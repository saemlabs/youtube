import pytest
from pydantic import ValidationError

from saemphysics.models import (
    AnswerOption,
    QuestionRecord,
    RightsStatus,
    SolutionArtifact,
    SolutionStatus,
    SourceRecord,
    VerificationCheck,
)
from saemphysics.verification import publication_decision


def make_question(**updates):
    fields = {
        "question_id": "synthetic_motion",
        "exam": "Synthetic demo",
        "year": 2026,
        "subject": "physics",
        "topic": "mechanics",
        "source": SourceRecord(
            document_id="synthetic_demo",
            rights_status=RightsStatus.ORIGINAL,
        ),
        "question_text": "An original synthetic test question.",
    }
    fields.update(updates)
    return QuestionRecord(**fields)


def test_question_record_keeps_official_and_computed_answers_separate():
    question = make_question(
        official_answer="C",
        solution=SolutionArtifact(
            numerical_result="14 m/s",
        ),
    )

    assert question.official_answer == "C"
    assert question.solution.numerical_result == "14 m/s"


def test_multiple_choice_answer_keys_and_options_are_consistent():
    with pytest.raises(ValidationError, match="option keys must be unique"):
        make_question(
            options=[
                AnswerOption(key="A", text="First"),
                AnswerOption(key="A", text="Duplicate"),
            ]
        )
    with pytest.raises(ValidationError, match="must match one"):
        make_question(
            options=[
                AnswerOption(key="A", text="First"),
                AnswerOption(key="B", text="Second"),
            ],
            official_answer="C",
        )


def test_publication_is_blocked_before_verification_and_review():
    decision = publication_decision(make_question())

    assert not decision.publishable
    assert any("not passed verification" in item for item in decision.blockers)
    assert any("human reviewer" in item for item in decision.blockers)


def test_failed_check_cannot_be_marked_verified():
    with pytest.raises(ValidationError, match="failed checks"):
        SolutionArtifact(
            status=SolutionStatus.VERIFIED,
            derivation_steps=["A derivation."],
            verification_checks=[
                VerificationCheck(
                    name="equation",
                    passed=False,
                    details="Residual is nonzero.",
                )
            ],
        )


def test_cleared_question_can_be_published_after_human_review():
    question = make_question(
        solution=SolutionArtifact(
            status=SolutionStatus.VERIFIED,
            derivation_steps=["Apply the constant-acceleration equations."],
            verification_checks=[
                VerificationCheck(
                    name="equation",
                    passed=True,
                    details="Both equation residuals are zero.",
                )
            ],
        ),
        review={"human_verified": True, "reviewer": "reviewer-1"},
    )

    assert publication_decision(question).publishable


@pytest.mark.parametrize(
    "rights_status",
    [RightsStatus.REVIEW_REQUIRED, RightsStatus.PERMISSION_REQUIRED],
)
def test_uncleared_source_rights_block_publication(rights_status):
    question = make_question(
        source=SourceRecord(document_id="source", rights_status=rights_status)
    )

    decision = publication_decision(question)

    assert not decision.publishable
    assert any("rights are not cleared" in item for item in decision.blockers)


def test_human_review_requires_a_reviewer_identity():
    with pytest.raises(ValidationError, match="identify its reviewer"):
        make_question(review={"human_verified": True})
