from dataclasses import asdict
from typing import Literal

from pydantic import Field, model_validator

from saemphysics.ir import SemanticIR, compile_request
from saemphysics.lesson import compile_lesson, lesson_publication_decision
from saemphysics.models import QuestionRecord, SolutionStatus, StrictModel
from saemphysics.runtime import execute_plan


class StudentRequest(StrictModel):
    """One student-facing request routed to the capabilities available today."""

    intent: Literal["solve", "practice", "submit_answer", "explain", "make_lesson"]
    question: QuestionRecord | None = None
    calculation: SemanticIR | None = None
    selected_option: str | None = Field(default=None, pattern=r"^[A-D]$")

    @model_validator(mode="after")
    def validate_intent_inputs(self):
        if self.intent == "solve":
            if self.calculation is None:
                raise ValueError("solve requires a calculation request")
            if self.question is not None:
                if self.calculation.question_id != self.question.question_id:
                    raise ValueError("calculation and question IDs must match")
            if self.selected_option is not None:
                raise ValueError("solve cannot include a selected answer option")
            return self

        if self.calculation is not None:
            raise ValueError(f"{self.intent} cannot include a calculation request")
        if self.question is None:
            raise ValueError(f"{self.intent} requires a question record")

        if self.intent == "submit_answer":
            if self.selected_option is None:
                raise ValueError("submit_answer requires a selected option")
            if not any(
                option.key == self.selected_option
                for option in self.question.options
            ):
                raise ValueError("selected_option must match a question option")
        elif self.selected_option is not None:
            raise ValueError(f"{self.intent} cannot include a selected answer option")
        return self


class StudentResponse(StrictModel):
    intent: Literal["solve", "practice", "submit_answer", "explain", "make_lesson"]
    status: Literal["completed", "ready", "draft", "correct", "incorrect", "blocked"]
    message: str
    artifact: dict[str, object] | None = None
    verification: dict[str, object] | None = None
    trace: list[dict[str, object]] = Field(default_factory=list)
    next_action: str | None = None


def _blocked(request: StudentRequest, message: str, next_action: str) -> StudentResponse:
    return StudentResponse(
        intent=request.intent,
        status="blocked",
        message=message,
        next_action=next_action,
    )


def _question_is_verified(question: QuestionRecord) -> bool:
    solution = question.solution
    return (
        solution.status == SolutionStatus.VERIFIED
        and bool(solution.derivation_steps)
        and bool(solution.verification_checks)
        and all(check.passed for check in solution.verification_checks)
    )


def process_student_request(request: StudentRequest) -> StudentResponse:
    """Route a student request through verified, explicitly supported workflows."""
    if request.intent == "solve":
        if request.calculation is None:
            raise ValueError("solve request is missing its calculation")
        execution = execute_plan(compile_request(request.calculation))
        return StudentResponse(
            intent=request.intent,
            status="completed",
            message="The exact calculation passed the configured verification checks.",
            artifact={
                "question_id": execution.question_id,
                "result": asdict(execution.result),
            },
            verification=asdict(execution.verification),
            trace=[asdict(event) for event in execution.trace],
        )

    question = request.question
    if question is None:
        raise ValueError(f"{request.intent} request is missing its question")

    if request.intent == "practice":
        return StudentResponse(
            intent=request.intent,
            status="ready",
            message="Question ready. The answer key is withheld until submission.",
            artifact={
                "question_id": question.question_id,
                "question_text": question.question_text,
                "options": [option.model_dump(mode="json") for option in question.options],
            },
            next_action=(
                "Submit one option key to receive feedback."
                if question.options
                else "This question has no multiple-choice options yet."
            ),
        )

    if request.intent == "submit_answer":
        if request.selected_option is None:
            raise ValueError("submit_answer request is missing its selected option")
        if not question.options:
            return _blocked(
                request,
                "This question has no answer options to grade.",
                "Add reviewed answer options or implement a reviewed free-response rubric.",
            )
        correct_key = (question.official_answer or "").strip().upper()
        if correct_key not in {option.key for option in question.options}:
            return _blocked(
                request,
                "A usable official answer key is not available for this question.",
                "Review and record the official answer with its source provenance.",
            )
        is_correct = request.selected_option == correct_key
        solution = question.solution
        artifact: dict[str, object] = {
            "question_id": question.question_id,
            "selected_option": request.selected_option,
            "correct_option": correct_key,
            "solution_status": solution.status.value,
        }
        if _question_is_verified(question):
            artifact["derivation_steps"] = solution.derivation_steps
            artifact["verification_checks"] = [
                check.model_dump(mode="json")
                for check in solution.verification_checks
            ]
        return StudentResponse(
            intent=request.intent,
            status="correct" if is_correct else "incorrect",
            message="Correct." if is_correct else "Not correct; compare with the answer shown.",
            artifact=artifact,
            next_action=(
                None
                if _question_is_verified(question)
                else "The answer key is available, but a verified explanation is not. "
                "Request solution review before presenting a worked explanation."
            ),
        )

    if request.intent == "explain":
        if not _question_is_verified(question):
            return _blocked(
                request,
                "A worked explanation requires a solution with passing verification evidence.",
                "Verify the solution and provide reviewed derivation steps first.",
            )
        return StudentResponse(
            intent=request.intent,
            status="draft",
            message=(
                "This explanation is assembled from the stored solution. "
                "Its wording still requires human teaching review."
            ),
            artifact={
                "question_id": question.question_id,
                "assumptions": question.solution.assumptions,
                "derivation_steps": question.solution.derivation_steps,
                "symbolic_result": question.solution.symbolic_result,
                "numerical_result": question.solution.numerical_result,
                "units": question.solution.units,
            },
            verification={
                "status": "passed",
                "checks": [
                    check.model_dump(mode="json")
                    for check in question.solution.verification_checks
                ],
            },
            next_action="Have a subject and teaching reviewer approve the explanation.",
        )

    if not _question_is_verified(question):
        return _blocked(
            request,
            "A lesson draft requires a solution with passing verification evidence.",
            "Verify the solution and provide reviewed derivation steps first.",
        )

    lesson = compile_lesson(question)
    publication = lesson_publication_decision(lesson, question)
    return StudentResponse(
        intent=request.intent,
        status="draft",
        message=(
            "A renderer-independent lesson draft is ready. This workflow does not "
            "render or publish a video."
        ),
        artifact={
            "lesson": lesson.model_dump(mode="json"),
            "publication": {
                "publishable": publication.publishable,
                "blockers": list(publication.blockers),
            },
        },
        next_action="Review the lesson and clear source rights before rendering or publication.",
    )
