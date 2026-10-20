from dataclasses import asdict
from collections.abc import Callable
from typing import Literal

from pydantic import Field, model_validator

from saemphysics.ir import SemanticIR, compile_request
from saemphysics.lesson import compile_lesson, lesson_publication_decision
from saemphysics.models import QuestionRecord, SolutionStatus, StrictModel
from saemphysics.runtime import execute_plan


class StudentRequest(StrictModel):
    """One student-facing request routed to the capabilities available today."""

    intent: Literal[
        "solve",
        "practice",
        "submit_answer",
        "explain",
        "make_lesson",
        "start_test",
        "submit_test",
    ]
    question_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    question_ids: list[str] = Field(default_factory=list, min_length=0)
    question: QuestionRecord | None = None
    calculation: SemanticIR | None = None
    selected_option: str | None = Field(default=None, pattern=r"^[A-D]$")
    answers: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_intent_inputs(self):
        if self.intent in {"start_test", "submit_test"}:
            if self.question is not None or self.question_id is not None:
                raise ValueError(f"{self.intent} uses question_ids, not a single question")
            if self.calculation is not None or self.selected_option is not None:
                raise ValueError(f"{self.intent} cannot include single-question inputs")
            if not self.question_ids:
                raise ValueError(f"{self.intent} requires at least one question ID")
            if len(self.question_ids) != len(set(self.question_ids)):
                raise ValueError("question_ids must be unique")
            if self.intent == "start_test" and self.answers is not None:
                raise ValueError("start_test cannot include submitted answers")
            if self.intent == "submit_test":
                if self.answers is None:
                    raise ValueError("submit_test requires an answer for every question")
                if set(self.answers) != set(self.question_ids):
                    raise ValueError(
                        "submitted answer IDs must exactly match question_ids"
                    )
                if any(
                    answer not in {"A", "B", "C", "D"}
                    for answer in self.answers.values()
                ):
                    raise ValueError("test answers must be option keys A through D")
            return self

        if self.question_ids or self.answers is not None:
            raise ValueError(f"{self.intent} cannot include test inputs")

        if self.intent == "solve":
            if self.calculation is None:
                raise ValueError("solve requires a calculation request")
            if self.question_id is not None and (
                self.calculation.question_id != self.question_id
            ):
                raise ValueError("calculation and question IDs must match")
            if self.question is not None:
                if self.calculation.question_id != self.question.question_id:
                    raise ValueError("calculation and question IDs must match")
            if self.question_id is not None and self.question is not None:
                if self.question_id != self.question.question_id:
                    raise ValueError("question_id and question record IDs must match")
            if self.selected_option is not None:
                raise ValueError("solve cannot include a selected answer option")
            return self

        if self.calculation is not None:
            raise ValueError(f"{self.intent} cannot include a calculation request")
        if self.question is None and self.question_id is None:
            raise ValueError(f"{self.intent} requires a question record")
        if self.question is not None and self.question_id is not None:
            if self.question.question_id != self.question_id:
                raise ValueError("question_id and question record IDs must match")

        if self.intent == "submit_answer":
            if self.selected_option is None:
                raise ValueError("submit_answer requires a selected option")
            if self.question is not None and not any(
                option.key == self.selected_option for option in self.question.options
            ):
                raise ValueError("selected_option must match a question option")
        elif self.selected_option is not None:
            raise ValueError(f"{self.intent} cannot include a selected answer option")
        return self


class StudentResponse(StrictModel):
    intent: Literal[
        "solve",
        "practice",
        "submit_answer",
        "explain",
        "make_lesson",
        "start_test",
        "submit_test",
    ]
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


def process_student_request(
    request: StudentRequest,
    question_resolver: Callable[[str], QuestionRecord] | None = None,
) -> StudentResponse:
    """Route a student request through verified, explicitly supported workflows."""
    if request.intent in {"start_test", "submit_test"}:
        if question_resolver is None:
            raise ValueError(
                f"{request.intent} requires a validated question-corpus resolver"
            )
        questions = []
        for question_id in request.question_ids:
            question = question_resolver(question_id)
            if question.question_id != question_id:
                raise ValueError(
                    f"Question resolver returned a different question for {question_id!r}"
                )
            if not question.options:
                raise ValueError(
                    f"Question {question_id!r} has no multiple-choice options"
                )
            answer_keys = {option.key for option in question.options}
            if request.intent == "submit_test":
                answer = request.answers[question_id]
                if answer not in answer_keys:
                    raise ValueError(
                        f"Answer for {question_id!r} does not match an available option"
                    )
            questions.append(question)

        if request.intent == "start_test":
            return StudentResponse(
                intent=request.intent,
                status="ready",
                message="Test is ready. Submit one option key for each question.",
                artifact={
                    "question_ids": [question.question_id for question in questions],
                    "questions": [
                        {
                            "question_id": question.question_id,
                            "question_text": question.question_text,
                            "options": [
                                option.model_dump(mode="json")
                                for option in question.options
                            ],
                        }
                        for question in questions
                    ],
                },
                next_action="Submit answers with the same question IDs.",
            )

        if request.answers is None:
            raise ValueError("submit_test request is missing submitted answers")
        unkeyed = [
            question.question_id
            for question in questions
            if (question.official_answer or "").strip().upper()
            not in {option.key for option in question.options}
        ]
        if unkeyed:
            raise ValueError(
                "Cannot grade test; usable source-recorded answer keys are missing for: "
                + ", ".join(unkeyed)
            )
        results = [
            {
                "question_id": question.question_id,
                "selected_option": request.answers[question.question_id],
                "correct_option": question.official_answer.strip().upper(),
                "correct": (
                    request.answers[question.question_id]
                    == question.official_answer.strip().upper()
                ),
            }
            for question in questions
        ]
        correct_count = sum(result["correct"] for result in results)
        total = len(results)
        return StudentResponse(
            intent=request.intent,
            status="completed",
            message=f"Test graded: {correct_count} of {total} answers correct.",
            artifact={
                "correct_count": correct_count,
                "total": total,
                "percentage": round(correct_count * 100 / total, 1),
                "results": results,
            },
            next_action="Review each result; verified worked solutions are not available for every item yet.",
        )

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
        if request.question_id is None:
            raise ValueError(f"{request.intent} request is missing its question ID")
        if question_resolver is None:
            raise ValueError(
                "Selecting by question_id requires a validated question-corpus resolver"
            )
        question = question_resolver(request.question_id)
        if question.question_id != request.question_id:
            raise ValueError("Question resolver returned a different question ID")

    if request.intent == "submit_answer" and request.selected_option not in {
        option.key for option in question.options
    }:
        raise ValueError("selected_option must match a question option")

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
