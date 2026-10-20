import pytest
from pydantic import ValidationError

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.ir import SemanticIR
from saemphysics.lesson import SceneRole
from saemphysics.models import (
    AnswerOption,
    QuestionRecord,
    RightsStatus,
    SolutionArtifact,
    SolutionStatus,
    SourceRecord,
    VerificationCheck,
)


def make_question(*, verified=False, official_answer="B"):
    solution = SolutionArtifact()
    if verified:
        solution = SolutionArtifact(
            status=SolutionStatus.VERIFIED,
            assumptions=["Acceleration is constant."],
            derivation_steps=[
                "Use s = ut + 1/2 at^2.",
                "Substitute the given values to obtain 28 m.",
            ],
            symbolic_result="s = ut + 1/2 at^2",
            numerical_result="28",
            units="m",
            verification_checks=[
                VerificationCheck(
                    name="displacement_equation",
                    passed=True,
                    details="The equation residual is zero.",
                )
            ],
        )
    return QuestionRecord(
        question_id="central-cart-question",
        exam="Synthetic demo",
        year=2026,
        subject="physics",
        topic="mechanics",
        source=SourceRecord(
            document_id="synthetic-central-demo",
            page=1,
            rights_status=RightsStatus.ORIGINAL,
        ),
        question_text="A cart moves under constant acceleration. Find its displacement.",
        options=[
            AnswerOption(key="A", text="20 m"),
            AnswerOption(key="B", text="28 m"),
        ],
        official_answer=official_answer,
        solution=solution,
    )


def test_central_solve_routes_calculation_to_verified_runtime():
    question = make_question()
    request = StudentRequest(
        intent="solve",
        question=question,
        calculation=SemanticIR(
            operation="solve_constant_acceleration",
            question_id=question.question_id,
            initial_velocity_m_s="3",
            acceleration_m_s2="2",
            time_s="4",
        ),
    )

    response = process_student_request(request)

    assert response.status == "completed"
    assert response.artifact["result"]["displacement_m"] == "28"
    assert response.verification["status"] == "passed"
    assert len(response.trace) == 5


def test_central_rejects_calculation_for_a_different_question():
    with pytest.raises(ValidationError, match="IDs must match"):
        StudentRequest(
            intent="solve",
            question=make_question(),
            calculation=SemanticIR(
                operation="differentiate",
                question_id="other-question",
                expression="x**2",
            ),
        )


def test_practice_hides_answer_key_until_submission():
    question = make_question()
    response = process_student_request(
        StudentRequest(intent="practice", question=question)
    )

    assert response.status == "ready"
    assert response.artifact["question_id"] == question.question_id
    assert "official_answer" not in response.artifact
    assert "correct_option" not in response.artifact


def test_practice_resolves_question_by_id_without_embedding_record():
    question = make_question()
    request = StudentRequest(
        intent="practice",
        question_id=question.question_id,
    )

    response = process_student_request(
        request,
        question_resolver=lambda question_id: question,
    )

    assert response.status == "ready"
    assert response.artifact["question_id"] == question.question_id


def test_id_selection_requires_a_resolver_and_checks_resolved_id():
    request = StudentRequest(
        intent="practice",
        question_id="central-cart-question",
    )

    with pytest.raises(ValueError, match="requires a validated question-corpus resolver"):
        process_student_request(request)
    with pytest.raises(ValueError, match="different question ID"):
        process_student_request(
            request,
            question_resolver=lambda question_id: make_question(
                verified=False
            ).model_copy(update={"question_id": "another-question"}),
        )


def test_id_based_answer_submission_checks_resolved_options():
    question = make_question()
    request = StudentRequest(
        intent="submit_answer",
        question_id=question.question_id,
        selected_option="D",
    )

    with pytest.raises(ValueError, match="must match a question option"):
        process_student_request(
            request,
            question_resolver=lambda question_id: question,
        )


def test_start_test_withholds_answer_keys():
    question = make_question()
    response = process_student_request(
        StudentRequest(
            intent="start_test",
            question_ids=[question.question_id],
        ),
        question_resolver=lambda question_id: question,
    )

    assert response.status == "ready"
    assert response.artifact["question_ids"] == [question.question_id]
    assert "official_answer" not in response.artifact["questions"][0]


def test_submit_test_returns_score_and_per_question_feedback():
    question = make_question(verified=True)
    response = process_student_request(
        StudentRequest(
            intent="submit_test",
            question_ids=[question.question_id],
            answers={question.question_id: "B"},
        ),
        question_resolver=lambda question_id: question,
    )

    assert response.status == "completed"
    assert response.artifact["correct_count"] == 1
    assert response.artifact["total"] == 1
    assert response.artifact["percentage"] == 100
    assert response.artifact["results"] == [
        {
            "question_id": question.question_id,
            "selected_option": "B",
            "correct_option": "B",
            "correct": True,
        }
    ]


def test_submit_test_blocks_if_any_answer_key_is_missing():
    question = make_question(official_answer=None)
    request = StudentRequest(
        intent="submit_test",
        question_ids=[question.question_id],
        answers={question.question_id: "A"},
    )

    with pytest.raises(ValueError, match="answer keys are missing"):
        process_student_request(
            request,
            question_resolver=lambda question_id: question,
        )


def test_test_score_percentage_preserves_partial_scores():
    question = make_question(verified=False)
    second = question.model_copy(update={"question_id": "second-question"})
    third = question.model_copy(update={"question_id": "third-question"})
    questions = {
        question.question_id: question,
        second.question_id: second,
        third.question_id: third,
    }
    response = process_student_request(
        StudentRequest(
            intent="submit_test",
            question_ids=list(questions),
            answers={
                question.question_id: "B",
                second.question_id: "A",
                third.question_id: "A",
            },
        ),
        question_resolver=questions.__getitem__,
    )

    assert response.artifact["correct_count"] == 1
    assert response.artifact["percentage"] == 33.3


def test_submission_grades_against_key_and_reveals_only_verified_work():
    question = make_question(verified=True)
    response = process_student_request(
        StudentRequest(
            intent="submit_answer",
            question=question,
            selected_option="B",
        )
    )

    assert response.status == "correct"
    assert response.artifact["correct_option"] == "B"
    assert len(response.artifact["derivation_steps"]) == 2


def test_submission_without_official_key_is_blocked_not_guessed():
    question = make_question(official_answer=None)
    response = process_student_request(
        StudentRequest(
            intent="submit_answer",
            question=question,
            selected_option="A",
        )
    )

    assert response.status == "blocked"
    assert response.artifact is None
    assert "official answer key" in response.message


def test_explanation_waits_for_passing_solution_evidence():
    pending = process_student_request(
        StudentRequest(intent="explain", question=make_question())
    )
    verified = process_student_request(
        StudentRequest(intent="explain", question=make_question(verified=True))
    )

    assert pending.status == "blocked"
    assert verified.status == "draft"
    assert verified.artifact["derivation_steps"]
    assert verified.verification["status"] == "passed"


def test_lesson_intent_returns_plan_without_claiming_video_or_publication():
    response = process_student_request(
        StudentRequest(intent="make_lesson", question=make_question(verified=True))
    )
    lesson = response.artifact["lesson"]

    assert response.status == "draft"
    assert lesson["scenes"][0]["role"] == SceneRole.CENTRAL_QUESTION.value
    assert lesson["scenes"][-1]["role"] == SceneRole.RECAP.value
    assert response.artifact["publication"]["publishable"] is False
    assert "does not render" in response.message
