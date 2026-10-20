from dataclasses import dataclass
from fractions import Fraction

from saemphysics.solvers.mechanics import (
    KinematicsResult,
    VerificationReport,
    verify_constant_acceleration,
)


@dataclass(frozen=True)
class MotionState:
    time_s: Fraction
    displacement_m: Fraction
    velocity_m_s: Fraction


@dataclass(frozen=True)
class ConstantAccelerationMotion:
    """Exact, renderer-independent state for a verified motion preview."""

    initial_velocity_m_s: Fraction
    acceleration_m_s2: Fraction
    duration_s: Fraction

    @classmethod
    def from_verified_result(
        cls,
        result: KinematicsResult,
        verification: VerificationReport,
    ) -> "ConstantAccelerationMotion":
        if verification.status != "passed" or not verification.checks:
            raise ValueError("A motion preview requires a passed verification report")
        if not all(check.passed for check in verification.checks):
            raise ValueError("A motion preview requires all verification checks to pass")
        if verification != verify_constant_acceleration(result):
            raise ValueError(
                "The verification report does not match the supplied motion result"
            )

        duration = Fraction(result.time_s)
        if duration < 0:
            raise ValueError("A motion preview requires non-negative elapsed time")

        return cls(
            initial_velocity_m_s=Fraction(result.initial_velocity_m_s),
            acceleration_m_s2=Fraction(result.acceleration_m_s2),
            duration_s=duration,
        )

    def at(self, time_s: int | str | Fraction) -> MotionState:
        if isinstance(time_s, bool) or not isinstance(
            time_s,
            (int, str, Fraction),
        ):
            raise ValueError("time_s must be within the verified motion duration")
        try:
            elapsed = Fraction(time_s)
        except (TypeError, ValueError, ZeroDivisionError) as error:
            raise ValueError(
                "time_s must be within the verified motion duration"
            ) from error
        if elapsed < 0 or elapsed > self.duration_s:
            raise ValueError("time_s must be within the verified motion duration")

        displacement = (
            self.initial_velocity_m_s * elapsed
            + self.acceleration_m_s2 * elapsed**2 / 2
        )
        velocity = (
            self.initial_velocity_m_s + self.acceleration_m_s2 * elapsed
        )
        return MotionState(
            time_s=elapsed,
            displacement_m=displacement,
            velocity_m_s=velocity,
        )
