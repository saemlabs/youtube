import pytest

from saemphysics.solvers.mechanics import (
    KinematicsResult,
    VerificationReport,
    solve_constant_acceleration,
    verify_constant_acceleration,
)
from saemphysics.visuals.kinematics import ConstantAccelerationMotion


def make_verified_motion():
    result = solve_constant_acceleration("2", "3", "4")
    report = verify_constant_acceleration(result)
    return result, report


def test_preview_model_preserves_exact_motion_states():
    result, report = make_verified_motion()

    motion = ConstantAccelerationMotion.from_verified_result(result, report)

    assert motion.at("0").displacement_m == 0
    assert motion.at("2").displacement_m == 10
    assert motion.at("2").velocity_m_s == 8
    assert motion.at("4").displacement_m == 32
    assert motion.at("4").velocity_m_s == 14


def test_preview_model_rejects_failed_or_incomplete_verification():
    result, report = make_verified_motion()
    failed_report = VerificationReport(
        status="failed",
        checks=report.checks,
    )

    with pytest.raises(ValueError, match="passed verification"):
        ConstantAccelerationMotion.from_verified_result(result, failed_report)

    with pytest.raises(ValueError, match="all verification checks"):
        ConstantAccelerationMotion.from_verified_result(
            result,
            VerificationReport(
                status="passed",
                checks=(
                    *report.checks[:-1],
                    type(report.checks[-1])(
                        name=report.checks[-1].name,
                        passed=False,
                        details="not verified",
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="passed verification"):
        ConstantAccelerationMotion.from_verified_result(
            result,
            VerificationReport(status="passed", checks=()),
        )


@pytest.mark.parametrize("time_s", [-1, "5", "not-a-time", True, 0.5])
def test_preview_model_rejects_times_outside_verified_duration(time_s):
    result, report = make_verified_motion()
    motion = ConstantAccelerationMotion.from_verified_result(result, report)

    with pytest.raises(ValueError, match="within the verified motion duration"):
        motion.at(time_s)


def test_preview_model_uses_only_result_inputs_and_verification_gate():
    result, report = make_verified_motion()
    mismatched_result = KinematicsResult(
        initial_velocity_m_s=result.initial_velocity_m_s,
        acceleration_m_s2=result.acceleration_m_s2,
        time_s=result.time_s,
        displacement_m="31",
        final_velocity_m_s=result.final_velocity_m_s,
    )

    with pytest.raises(ValueError, match="does not match"):
        ConstantAccelerationMotion.from_verified_result(
            mismatched_result,
            report,
        )

    corrupted = KinematicsResult(
        initial_velocity_m_s="2",
        acceleration_m_s2="3",
        time_s="-1",
        displacement_m="1/2",
        final_velocity_m_s="-1",
    )

    with pytest.raises(ValueError, match="does not match"):
        ConstantAccelerationMotion.from_verified_result(corrupted, report)
