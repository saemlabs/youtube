import pytest
from pydantic import ValidationError

from saemphysics.lesson import (
    EvidenceReference,
    LessonAudience,
    LessonArtifact,
    SceneRole,
    compile_lesson,
    lesson_publication_decision,
)
from saemphysics.models import (
    QuestionRecord,
    RightsStatus,
    ReviewRecord,
    SolutionArtifact,
    SolutionStatus,
    SourceRecord,
    VerificationCheck,
)


def make_question(**updates):
    fields = {
        "question_id": "synthetic_cart_motion",
        "exam": "Synthetic demo",
        "year": 2026,
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "constant_acceleration",
        "source": SourceRecord(
            document_id="synthetic_demo",
            page=1,
            question_number="1",
            rights_status=RightsStatus.ORIGINAL,
        ),
        "question_text": (
            "A cart starts at 2 m/s and accelerates at 3 m/s^2 for 4 s. "
            "Find its displacement and final velocity."
        ),
        "solution": SolutionArtifact(
            status=SolutionStatus.VERIFIED,
            assumptions=["Motion is one-dimensional with constant acceleration."],
            derivation_steps=[
                "Displacement: s = ut + 1/2 at^2 = 32 m.",
                "Final velocity: v = u + at = 14 m/s.",
            ],
            symbolic_result="s = ut + 1/2 at^2; v = u + at",
            numerical_result="displacement=32 m; final_velocity=14 m/s",
            units="m, m/s",
            verification_checks=[
                VerificationCheck(
                    name="displacement",
                    passed=True,
                    details="Displacement equation residual is zero.",
                ),
                VerificationCheck(
                    name="velocity",
                    passed=True,
                    details="Velocity equation residual is zero.",
                ),
            ],
        ),
    }
    fields.update(updates)
    return QuestionRecord(**fields)


def test_compiles_renderer_independent_lesson_with_source_evidence():
    question = make_question()

    lesson = compile_lesson(question, LessonAudience.JEE_MAIN)

    assert lesson.schema_version == "1.0"
    assert lesson.audience == LessonAudience.JEE_MAIN
    assert lesson.scenes[0].role == SceneRole.CENTRAL_QUESTION
    assert lesson.scenes[-1].role == SceneRole.RECAP
    assert all(scene.evidence for scene in lesson.scenes)
    assert all(
        reference.question_id == question.question_id
        and reference.source_document_id == question.source.document_id
        and reference.page == question.source.page
        for scene in lesson.scenes
        for reference in scene.evidence
    )
    assert any(scene.role == SceneRole.MODEL for scene in lesson.scenes)
    assert sum(scene.role == SceneRole.DERIVATION for scene in lesson.scenes) == 2


def test_lesson_artifact_round_trips_as_versioned_json():
    lesson = compile_lesson(make_question(), LessonAudience.JEE_MAIN)

    restored = LessonArtifact.model_validate_json(lesson.model_dump_json())

    assert restored == lesson


def test_compiler_rejects_unverified_solutions():
    question = make_question(solution=SolutionArtifact())

    with pytest.raises(ValueError, match="verified solution"):
        compile_lesson(question)


def test_compiler_rejects_failed_verification_evidence():
    question = make_question()
    corrupted_solution = question.solution.model_copy(
        update={
            "verification_checks": [
                VerificationCheck(
                    name="equation",
                    passed=False,
                    details="Residual is nonzero.",
                )
            ]
        }
    )
    corrupted_question = question.model_copy(
        update={"solution": corrupted_solution}
    )

    with pytest.raises(ValueError, match="passing verification"):
        compile_lesson(corrupted_question)


def test_scene_evidence_cannot_point_to_a_different_source():
    question = make_question()
    lesson = compile_lesson(question)
    central = lesson.scenes[0].model_copy(
        update={
            "evidence": [
                EvidenceReference(
                    question_id=question.question_id,
                    source_document_id="unrelated-document",
                    field_path="question_text",
                )
            ]
        }
    )
    altered_scenes = [central, *lesson.scenes[1:]]

    with pytest.raises(ValidationError, match="source lineage"):
        LessonArtifact(
            **{
                **lesson.model_dump(),
                "scenes": [scene.model_dump() for scene in altered_scenes],
            }
        )


def test_scene_order_keeps_verification_after_derivation():
    lesson = compile_lesson(make_question())
    scenes = list(lesson.scenes)
    verification = next(
        scene for scene in scenes if scene.role == SceneRole.VERIFICATION
    )
    scenes.remove(verification)
    scenes.insert(2, verification)

    with pytest.raises(ValidationError, match="follow the derivation"):
        LessonArtifact(
            **{
                **lesson.model_dump(),
                "scenes": [scene.model_dump() for scene in scenes],
            }
        )


def test_draft_lesson_is_not_publishable_without_question_and_lesson_review():
    question = make_question()
    lesson = compile_lesson(question)

    decision = lesson_publication_decision(lesson, question)

    assert not decision.publishable
    assert any("lesson" in blocker for blocker in decision.blockers)
    assert any("question" in blocker for blocker in decision.blockers)


def test_lesson_approval_does_not_bypass_source_rights_or_question_review():
    question = make_question(
        source=SourceRecord(
            document_id="source-needs-review",
            rights_status=RightsStatus.REVIEW_REQUIRED,
        ),
        review=ReviewRecord(human_verified=True, reviewer="reviewer-1"),
    )
    lesson = compile_lesson(question).model_copy(
        update={
            "review": ReviewRecord(human_verified=True, reviewer="reviewer-2")
        }
    )

    decision = lesson_publication_decision(lesson, question)

    assert not decision.publishable
    assert any("rights" in blocker for blocker in decision.blockers)
