import pytest

from saemphysics.solvers.mechanics import (
    KinematicsResult,
    solve_constant_acceleration,
    verify_constant_acceleration,
)


def test_constant_acceleration_solver_returns_exact_results():
    result = solve_constant_acceleration(2, 3, 4)

    assert result.displacement_m == "32"
    assert result.final_velocity_m_s == "14"
    report = verify_constant_acceleration(result)
    assert report.status == "passed"
    assert all(check.passed for check in report.checks)


def test_solver_preserves_fractional_inputs_exactly():
    result = solve_constant_acceleration("1/2", "3/2", 2)

    assert result.displacement_m == "4"
    assert result.final_velocity_m_s == "7/2"


@pytest.mark.parametrize("time_s", [-1, "-1/2"])
def test_solver_rejects_negative_time(time_s):
    with pytest.raises(ValueError, match="non-negative"):
        solve_constant_acceleration(0, 1, time_s)


@pytest.mark.parametrize("value", [True, "not a number", "1/0", "oo"])
def test_solver_rejects_invalid_or_non_finite_inputs(value):
    with pytest.raises(ValueError):
        solve_constant_acceleration(value, 0, 1)


def test_verifier_rejects_a_corrupted_result():
    result = solve_constant_acceleration(2, 3, 4)
    corrupted = KinematicsResult(
        **{**result.__dict__, "displacement_m": "31"}
    )

    report = verify_constant_acceleration(corrupted)

    assert report.status == "failed"
    assert report.checks[0].passed
    assert not report.checks[1].passed
    assert report.checks[2].passed


def test_verifier_rejects_negative_elapsed_time():
    invalid = KinematicsResult(
        initial_velocity_m_s="0",
        acceleration_m_s2="1",
        time_s="-1",
        displacement_m="1/2",
        final_velocity_m_s="-1",
    )

    report = verify_constant_acceleration(invalid)

    assert report.status == "failed"
    assert not report.checks[0].passed
