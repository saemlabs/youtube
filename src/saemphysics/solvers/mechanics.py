from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class KinematicsResult:
    initial_velocity_m_s: str
    acceleration_m_s2: str
    time_s: str
    displacement_m: str
    final_velocity_m_s: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: tuple[CheckResult, ...]


def _rational(value: int | float | str, name: str) -> sp.Rational:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = sp.Rational(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not result.is_finite:
        raise ValueError(f"{name} must be a finite number")
    return result


def solve_constant_acceleration(
    initial_velocity_m_s: int | float | str,
    acceleration_m_s2: int | float | str,
    time_s: int | float | str,
) -> KinematicsResult:
    """Solve one-dimensional motion with constant acceleration in SI units."""
    u = _rational(initial_velocity_m_s, "initial_velocity_m_s")
    a = _rational(acceleration_m_s2, "acceleration_m_s2")
    t = _rational(time_s, "time_s")
    if t < 0:
        raise ValueError("time_s must be non-negative")

    displacement = u * t + a * t**2 / 2
    final_velocity = u + a * t
    return KinematicsResult(
        initial_velocity_m_s=sp.sstr(u),
        acceleration_m_s2=sp.sstr(a),
        time_s=sp.sstr(t),
        displacement_m=sp.sstr(displacement),
        final_velocity_m_s=sp.sstr(final_velocity),
    )


def verify_constant_acceleration(result: KinematicsResult) -> VerificationReport:
    """Check that a result satisfies both constant-acceleration equations."""
    u = _rational(result.initial_velocity_m_s, "initial_velocity_m_s")
    a = _rational(result.acceleration_m_s2, "acceleration_m_s2")
    t = _rational(result.time_s, "time_s")
    displacement = _rational(result.displacement_m, "displacement_m")
    final_velocity = _rational(result.final_velocity_m_s, "final_velocity_m_s")

    displacement_residual = sp.simplify(displacement - (u * t + a * t**2 / 2))
    velocity_residual = sp.simplify(final_velocity - (u + a * t))
    checks = (
        CheckResult(
            name="non_negative_time",
            passed=bool(t >= 0),
            details=f"Elapsed time is {sp.sstr(t)} s",
        ),
        CheckResult(
            name="constant_acceleration_displacement",
            passed=bool(displacement_residual == 0),
            details=f"Equation residual: {sp.sstr(displacement_residual)} m",
        ),
        CheckResult(
            name="constant_acceleration_velocity",
            passed=bool(velocity_residual == 0),
            details=f"Equation residual: {sp.sstr(velocity_residual)} m/s",
        ),
    )
    return VerificationReport(
        status="passed" if all(check.passed for check in checks) else "failed",
        checks=checks,
    )
