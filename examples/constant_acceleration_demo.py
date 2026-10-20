"""A synthetic example showing the initial solve-and-verify vertical slice."""

from saemphysics.models import (
    QuestionRecord,
    RightsStatus,
    SolutionArtifact,
    SolutionStatus,
    SourceRecord,
    VerificationCheck,
)
from saemphysics.ir import SemanticIR, compile_request
from saemphysics.lesson import LessonAudience, compile_lesson
from saemphysics.runtime import execute_plan
from saemphysics.verification import publication_decision


def main() -> None:
    question = QuestionRecord(
        question_id="synthetic_cart_motion",
        exam="SaemPhysics synthetic demo",
        year=2026,
        subject="physics",
        topic="mechanics",
        subtopic="constant_acceleration",
        source=SourceRecord(
            document_id="synthetic_demo",
            rights_status=RightsStatus.ORIGINAL,
        ),
        question_text=(
            "A cart starts at 2 m/s and accelerates at 3 m/s^2 for 4 s. "
            "Find its displacement and final velocity."
        ),
        concepts=["constant acceleration", "kinematics"],
        teaching_plan={
            "intuition": (
                "A steady acceleration changes the cart's velocity by the same "
                "amount in each second."
            ),
            "visual_analogy": (
                "Show equal one-second intervals with a longer velocity arrow "
                "after each interval."
            ),
            "common_misconception": (
                "Acceleration changes velocity, while displacement accumulates "
                "the velocity over time."
            ),
            "exam_strategy": (
                "Use the constant-acceleration equations and check both requested "
                "quantities."
            ),
        },
    )
    semantic_ir = SemanticIR(
        operation="solve_constant_acceleration",
        question_id="synthetic_cart_motion",
        initial_velocity_m_s="2",
        acceleration_m_s2="3",
        time_s="4",
    )
    runtime_result = execute_plan(compile_request(semantic_ir))
    result = runtime_result.result
    report = runtime_result.verification
    question = question.model_copy(
        update={
            "solution": SolutionArtifact(
                status=SolutionStatus.VERIFIED,
                assumptions=["Motion is one-dimensional with constant acceleration."],
                derivation_steps=[
                    "Displacement: s = ut + 1/2 at^2 = 32 m.",
                    "Final velocity: v = u + at = 14 m/s.",
                ],
                symbolic_result="s = ut + 1/2 at^2; v = u + at",
                numerical_result=(
                    f"displacement={result.displacement_m} m; "
                    f"final_velocity={result.final_velocity_m_s} m/s"
                ),
                units="m, m/s",
                verification_checks=[
                    VerificationCheck(
                        name=check.name,
                        passed=check.passed,
                        details=check.details,
                    )
                    for check in report.checks
                ],
            )
        }
    )

    decision = publication_decision(question)
    lesson = compile_lesson(question, LessonAudience.GENERAL)
    print(f"Computed result: {question.solution.numerical_result}")
    print(f"Solver verification: {report.status}")
    print("Execution trace:")
    for event in runtime_result.trace:
        print(f"- {event.layer}: {event.event} ({event.details})")
    print(f"Publication allowed: {decision.publishable}")
    if decision.blockers:
        print("Publication blockers:")
        for blocker in decision.blockers:
            print(f"- {blocker}")
    print(
        f"Draft lesson: {lesson.lesson_id} "
        f"({len(lesson.scenes)} renderer-independent scenes)"
    )


if __name__ == "__main__":
    main()
