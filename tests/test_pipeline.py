import pytest

from saemphysics.ir import SemanticIR, compile_request
from saemphysics.lesson import compile_lesson, lesson_publication_decision
from saemphysics.models import (
    QuestionRecord,
    RightsStatus,
    SolutionStatus,
    SourceRecord,
)
from saemphysics.pipeline import attach_verified_solution
from saemphysics.runtime import MathVerificationReport, execute_plan


def make_question(question_id="integral_motion"):
    return QuestionRecord(
        question_id=question_id,
        exam="Synthetic mathematics",
        year=2026,
        subject="mathematics",
        topic="calculus",
        source=SourceRecord(
            document_id="synthetic_integral",
            page=1,
            rights_status=RightsStatus.ORIGINAL,
        ),
        question_text="Find the exact accumulated change over the stated interval.",
    )


def test_verified_integral_flows_into_a_sourced_draft_lesson():
    question = make_question()
    execution = execute_plan(
        compile_request(
            SemanticIR(
                operation="definite_integral",
                question_id=question.question_id,
                expression="2 + 3*t",
                variable="t",
                lower_bound="0",
                upper_bound="4",
            )
        )
    )

    solved_question = attach_verified_solution(
        question,
        execution,
        derivation_steps=[
            "An antiderivative is 2*t + 3*t^2/2.",
            "Evaluate it at 4 and subtract its value at 0 to obtain 32.",
        ],
    )
    lesson = compile_lesson(solved_question)

    assert solved_question.solution.status == SolutionStatus.VERIFIED
    assert solved_question.solution.numerical_result == "32"
    assert all(check.passed for check in solved_question.solution.verification_checks)
    assert lesson.question_id == question.question_id
    assert all(scene.evidence for scene in lesson.scenes)
    assert not lesson.review.human_verified
    decision = lesson_publication_decision(lesson, solved_question)
    assert not decision.publishable
    assert any("human reviewer" in blocker for blocker in decision.blockers)


def test_solution_attachment_requires_explicit_derivation_and_matching_question():
    question = make_question()
    execution = execute_plan(
        compile_request(
            SemanticIR(
                operation="differentiate",
                question_id=question.question_id,
                expression="t**2",
                variable="t",
            )
        )
    )

    with pytest.raises(ValueError, match="different question"):
        attach_verified_solution(
            make_question("another_question"),
            execution,
            ["Differentiate t squared."],
        )
    with pytest.raises(ValueError, match="non-empty derivation"):
        attach_verified_solution(question, execution, [])


def test_failed_runtime_evidence_cannot_be_attached_to_a_question():
    question = make_question()
    execution = execute_plan(
        compile_request(
            SemanticIR(
                operation="differentiate",
                question_id=question.question_id,
                expression="t**2",
                variable="t",
            )
        )
    )
    failed_execution = execution.__class__(
        question_id=execution.question_id,
        result=execution.result,
        verification=MathVerificationReport(
            status="failed",
            checks=execution.verification.checks,
        ),
        trace=execution.trace,
    )

    with pytest.raises(ValueError, match="passed execution"):
        attach_verified_solution(
            question,
            failed_execution,
            ["Differentiate t squared."],
        )
