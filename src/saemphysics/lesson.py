from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from saemphysics.models import (
    QuestionRecord,
    ReviewRecord,
    RightsStatus,
    SolutionStatus,
    SourceRecord,
    StrictModel,
)
from saemphysics.verification import publication_decision as question_publication_decision


class LessonAudience(str, Enum):
    GENERAL = "general"
    NEET = "neet"
    JEE_MAIN = "jee_main"
    JEE_ADVANCED = "jee_advanced"
    OLYMPIAD = "olympiad"


class SceneRole(str, Enum):
    CENTRAL_QUESTION = "central_question"
    INTUITION = "intuition"
    MODEL = "model"
    DERIVATION = "derivation"
    VERIFICATION = "verification"
    RECAP = "recap"


class EvidenceReference(StrictModel):
    question_id: str = Field(min_length=1)
    source_document_id: str = Field(min_length=1)
    field_path: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    question_number: str | None = None


class LessonScene(StrictModel):
    scene_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    role: SceneRole
    teaching_purpose: str = Field(min_length=1)
    narration_cue: str = Field(min_length=1)
    visual_action: str = Field(min_length=1)
    learner_inference: str = Field(min_length=1)
    equations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(min_length=1)


class LessonArtifact(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    lesson_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    question_id: str = Field(min_length=1)
    source: SourceRecord
    audience: LessonAudience
    learning_objective: str = Field(min_length=1)
    central_question: str = Field(min_length=1)
    scenes: list[LessonScene] = Field(min_length=4)
    review: ReviewRecord = Field(default_factory=ReviewRecord)

    @model_validator(mode="after")
    def validate_scene_sequence_and_provenance(self):
        scene_ids = [scene.scene_id for scene in self.scenes]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique within a lesson")

        roles = [scene.role for scene in self.scenes]
        required = (
            SceneRole.CENTRAL_QUESTION,
            SceneRole.INTUITION,
            SceneRole.DERIVATION,
            SceneRole.VERIFICATION,
            SceneRole.RECAP,
        )
        if any(role not in roles for role in required):
            raise ValueError("Lesson is missing a required teaching scene")
        if roles[0] != SceneRole.CENTRAL_QUESTION or roles[-1] != SceneRole.RECAP:
            raise ValueError("Lessons must begin with the question and end with a recap")
        derivation_positions = [
            index
            for index, role in enumerate(roles)
            if role == SceneRole.DERIVATION
        ]
        if not derivation_positions:
            raise ValueError("Lessons must include at least one derivation scene")
        first_derivation = derivation_positions[0]
        last_derivation = derivation_positions[-1]
        if roles.index(SceneRole.INTUITION) > first_derivation:
            raise ValueError("Intuition must precede the derivation")
        if roles.index(SceneRole.VERIFICATION) < last_derivation:
            raise ValueError("Verification must follow the derivation")
        if (
            SceneRole.MODEL in roles
            and roles.index(SceneRole.MODEL) > first_derivation
        ):
            raise ValueError("Model assumptions must precede the derivation")

        for scene in self.scenes:
            if any(
                reference.question_id != self.question_id
                or reference.source_document_id != self.source.document_id
                or reference.page != self.source.page
                or reference.question_number != self.source.question_number
                for reference in scene.evidence
            ):
                raise ValueError("Scene evidence must retain this lesson's source lineage")
        return self


@dataclass(frozen=True)
class LessonPublicationDecision:
    publishable: bool
    blockers: tuple[str, ...]


def _evidence(question: QuestionRecord, field_path: str) -> EvidenceReference:
    return EvidenceReference(
        question_id=question.question_id,
        source_document_id=question.source.document_id,
        field_path=field_path,
        page=question.source.page,
        question_number=question.source.question_number,
    )


def compile_lesson(
    question: QuestionRecord,
    audience: LessonAudience = LessonAudience.GENERAL,
) -> LessonArtifact:
    """Compile a renderer-independent draft using only a verified solution."""
    solution = question.solution
    if solution.status != SolutionStatus.VERIFIED:
        raise ValueError("A lesson can only be compiled from a verified solution")
    if not solution.verification_checks or not all(
        check.passed for check in solution.verification_checks
    ):
        raise ValueError("A lesson requires passing verification evidence")
    if not solution.derivation_steps:
        raise ValueError("A lesson requires at least one verified derivation step")

    result = solution.numerical_result or solution.symbolic_result
    if not result:
        raise ValueError("A lesson requires a symbolic or numerical result")

    scenes = [
        LessonScene(
            scene_id="central-question",
            role=SceneRole.CENTRAL_QUESTION,
            teaching_purpose="Make the problem and requested outcome clear.",
            narration_cue=question.question_text,
            visual_action="Show the problem context and mark the requested quantity.",
            learner_inference="Identify what is given and what must be found.",
            evidence=[_evidence(question, "question_text")],
        ),
        LessonScene(
            scene_id="intuition",
            role=SceneRole.INTUITION,
            teaching_purpose="Build a physical picture before using equations.",
            narration_cue=(
                question.teaching_plan.intuition
                or "Picture the physical situation before choosing a mathematical model."
            ),
            visual_action=(
                question.teaching_plan.visual_analogy
                or "Keep the objects and quantities named in the question visible."
            ),
            learner_inference=(
                question.teaching_plan.common_misconception
                or "The model should describe the stated physical situation."
            ),
            evidence=[_evidence(question, "question_text")],
        ),
    ]

    if solution.assumptions:
        scenes.append(
            LessonScene(
                scene_id="model-assumptions",
                role=SceneRole.MODEL,
                teaching_purpose="State the conditions under which the solution applies.",
                narration_cue="Use the model only under these stated assumptions.",
                visual_action="Display the assumptions beside the physical setup.",
                learner_inference="A result is valid only within its stated model.",
                assumptions=solution.assumptions,
                evidence=[
                    _evidence(question, f"solution.assumptions[{index}]")
                    for index in range(len(solution.assumptions))
                ],
            )
        )

    for index, step in enumerate(solution.derivation_steps):
        equations = []
        if index == 0 and solution.symbolic_result:
            equations.append(solution.symbolic_result)
        if index == len(solution.derivation_steps) - 1:
            equations.append(result)
            if solution.units and solution.numerical_result:
                equations.append(f"Units: {solution.units}")
        scenes.append(
            LessonScene(
                scene_id=f"derivation-{index + 1}",
                role=SceneRole.DERIVATION,
                teaching_purpose=f"Explain verified derivation step {index + 1}.",
                narration_cue=step,
                visual_action="Reveal this step after its inputs and reasoning are visible.",
                learner_inference="Connect this step to the preceding physical or mathematical idea.",
                equations=equations,
                evidence=[
                    _evidence(question, f"solution.derivation_steps[{index}]")
                ],
            )
        )

    scenes.append(
        LessonScene(
            scene_id="independent-checks",
            role=SceneRole.VERIFICATION,
            teaching_purpose="Show how the result was checked independently.",
            narration_cue="Compare the result with each recorded verification check.",
            visual_action="Show each check and its pass status next to the result.",
            learner_inference="A result should satisfy its equations and stated constraints.",
            evidence=[
                _evidence(question, f"solution.verification_checks[{index}]")
                for index in range(len(solution.verification_checks))
            ],
        )
    )
    scenes.append(
        LessonScene(
            scene_id="recap",
            role=SceneRole.RECAP,
            teaching_purpose="Restate the verified result and the idea used.",
            narration_cue=(
                question.teaching_plan.exam_strategy
                or f"The verified result is {result}."
            ),
            visual_action="Return to the original question and highlight its answer.",
            learner_inference="The answer follows from the stated model and checked derivation.",
            equations=[result],
            evidence=[
                _evidence(
                    question,
                    "solution.numerical_result"
                    if solution.numerical_result
                    else "solution.symbolic_result",
                )
            ],
        )
    )

    return LessonArtifact(
        lesson_id=f"{question.question_id}-{audience.value}-lesson",
        question_id=question.question_id,
        source=question.source,
        audience=audience,
        learning_objective=(
            f"Explain the verified {question.subtopic or question.topic} solution "
            "and identify the assumptions and checks that support it."
        ),
        central_question=question.question_text,
        scenes=scenes,
    )


def lesson_publication_decision(
    lesson: LessonArtifact, question: QuestionRecord
) -> LessonPublicationDecision:
    blockers = []
    if lesson.question_id != question.question_id:
        blockers.append("The lesson does not match the supplied question.")
    if lesson.source != question.source:
        blockers.append("The lesson source lineage does not match the question.")

    blockers.extend(question_publication_decision(question).blockers)
    if not lesson.review.human_verified:
        blockers.append("A human reviewer has not approved the lesson.")
    if lesson.source.rights_status not in {
        RightsStatus.ORIGINAL,
        RightsStatus.PUBLIC_DOMAIN,
        RightsStatus.LICENSED,
    }:
        blockers.append("Source rights are not cleared for publication.")

    return LessonPublicationDecision(
        publishable=not blockers,
        blockers=tuple(blockers),
    )
