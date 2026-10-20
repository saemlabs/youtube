from dataclasses import asdict
from datetime import date

from pydantic import Field

from saemphysics.central import StudentRequest, StudentResponse, process_student_request
from saemphysics.ir import SemanticIR, compile_request
from saemphysics.models import QuestionRecord, RightsStatus, SourceRecord, StrictModel
from saemphysics.pipeline import attach_verified_solution
from saemphysics.runtime import execute_plan


class TeacherLessonInput(StrictModel):
    question_text: str = Field(min_length=10, max_length=2000)
    initial_velocity_m_s: str = Field(min_length=1, max_length=64)
    acceleration_m_s2: str = Field(min_length=1, max_length=64)
    time_s: str = Field(min_length=1, max_length=64)
    intuition: str | None = Field(default=None, max_length=500)
    common_misconception: str | None = Field(default=None, max_length=500)


def create_teacher_lesson_draft(
    request: TeacherLessonInput,
) -> StudentResponse:
    """Verify one teacher-entered motion example and compile its lesson draft."""
    question_id = "teacher-draft-constant-acceleration"
    calculation = SemanticIR(
        operation="solve_constant_acceleration",
        question_id=question_id,
        initial_velocity_m_s=request.initial_velocity_m_s,
        acceleration_m_s2=request.acceleration_m_s2,
        time_s=request.time_s,
    )
    execution = execute_plan(compile_request(calculation))

    question = QuestionRecord(
        question_id=question_id,
        exam="Teacher-created lesson draft",
        year=date.today().year,
        subject="physics",
        topic="Mechanics",
        subtopic="constant_acceleration",
        source=SourceRecord(
            document_id="teacher-composed-draft",
            rights_status=RightsStatus.REVIEW_REQUIRED,
        ),
        question_text=request.question_text,
        concepts=["constant_acceleration", "displacement", "final_velocity"],
        teaching_plan={
            "intuition": request.intuition,
            "common_misconception": request.common_misconception,
        },
    )
    verified_question = attach_verified_solution(
        question,
        execution,
        derivation_steps=[
            (
                "Displacement: s = ut + 1/2 at^2 = "
                f"({request.initial_velocity_m_s})({request.time_s}) + "
                f"1/2({request.acceleration_m_s2})({request.time_s})^2 = "
                f"{execution.result.displacement_m} m."
            ),
            (
                "Final velocity: v = u + at = "
                f"({request.initial_velocity_m_s}) + "
                f"({request.acceleration_m_s2})({request.time_s}) = "
                f"{execution.result.final_velocity_m_s} m/s."
            ),
        ],
        assumptions=["Motion is one-dimensional with constant acceleration."],
    )
    response = process_student_request(
        StudentRequest(intent="make_lesson", question=verified_question)
    )
    artifact = {
        **(response.artifact or {}),
        "calculation_inputs": {
            "initial_velocity_m_s": request.initial_velocity_m_s,
            "acceleration_m_s2": request.acceleration_m_s2,
            "time_s": request.time_s,
        },
    }
    return response.model_copy(
        update={
            "artifact": artifact,
            "verification": asdict(execution.verification),
            "trace": [asdict(event) for event in execution.trace],
        }
    )
