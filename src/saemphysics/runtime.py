from dataclasses import dataclass
import json
from pathlib import Path
import subprocess

from saemphysics.ir import (
    CompiledPlan,
    compile_request,
)
from saemphysics.maths import (
    DefiniteIntegralResult,
    DerivativeResult,
    LinearSystemResult,
    definite_integral,
    differentiate,
    solve_linear_system,
)
from saemphysics.maths.verification import MathCheck
from saemphysics.solvers.mechanics import (
    KinematicsResult,
    VerificationReport,
    solve_constant_acceleration,
    verify_constant_acceleration,
)


@dataclass(frozen=True)
class TraceEvent:
    layer: str
    event: str
    details: str


@dataclass(frozen=True)
class MathVerificationReport:
    status: str
    checks: tuple[MathCheck, ...]


@dataclass(frozen=True)
class RuntimeResult:
    question_id: str
    result: (
        KinematicsResult
        | DerivativeResult
        | DefiniteIntegralResult
        | LinearSystemResult
    )
    verification: VerificationReport | MathVerificationReport
    trace: tuple[TraceEvent, ...]


class NativeBackendError(RuntimeError):
    """A configured native capability failed to satisfy its result contract."""


def _execute_native_kinematics(
    executable: str | Path,
    initial_velocity_m_s: str,
    acceleration_m_s2: str,
    time_s: str,
) -> KinematicsResult:
    try:
        completed = subprocess.run(
            [
                str(executable),
                "--core-v1",
                "solve_constant_acceleration",
                initial_velocity_m_s,
                acceleration_m_s2,
                time_s,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NativeBackendError(
            f"Native kinematics capability could not run: {error}"
        ) from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit status {completed.returncode}"
        raise NativeBackendError(f"Native kinematics capability failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
        expected_checks = [
            "input_bounds",
            "displacement_equation",
            "velocity_equation",
        ]
        if not isinstance(payload, dict):
            raise ValueError("Native core response must be a JSON object")
        if set(payload) != {
            "protocol",
            "capability",
            "status",
            "result",
            "checks",
        }:
            raise ValueError("Native core response has unsupported or missing fields")
        if (
            payload.get("protocol") != "saemphysics.capability.v1"
            or payload.get("capability") != "solve_constant_acceleration"
            or payload.get("status") != "completed"
        ):
            raise ValueError("Native core response has an unsupported protocol or status")
        checks = payload.get("checks")
        if (
            not isinstance(checks, list)
            or [check.get("name") for check in checks if isinstance(check, dict)]
            != expected_checks
            or len(checks) != len(expected_checks)
            or any(
                not isinstance(check, dict)
                or set(check) != {"name", "passed"}
                or check.get("passed") is not True
                for check in checks
            )
        ):
            raise ValueError("Native core response must pass all required checks")
        expected_fields = {
            "initial_velocity_m_s",
            "acceleration_m_s2",
            "time_s",
            "displacement_m",
            "final_velocity_m_s",
        }
        result_payload = payload.get("result")
        if (
            not isinstance(result_payload, dict)
            or set(result_payload) != expected_fields
        ):
            raise ValueError(
                "Native core result must contain exactly the five motion fields"
            )
        if any(not isinstance(value, str) for value in result_payload.values()):
            raise ValueError("Native motion result fields must be exact strings")
        return KinematicsResult(**result_payload)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise NativeBackendError(
            f"Native kinematics capability returned invalid JSON: {error}"
        ) from error


def _execute_native_linear_system(
    executable: str | Path,
    coefficients: list[list[str]],
    right_hand_side: list[str],
) -> LinearSystemResult:
    size = len(coefficients)
    arguments = [
        str(executable),
        "--core-v1",
        "solve_linear_system",
        str(size),
        *(value for row in coefficients for value in row),
        *right_hand_side,
    ]
    try:
        completed = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NativeBackendError(
            f"Native linear-system capability could not run: {error}"
        ) from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit status {completed.returncode}"
        raise NativeBackendError(
            f"Native linear-system capability failed: {detail}"
        )
    try:
        payload = json.loads(completed.stdout)
        if not isinstance(payload, dict) or set(payload) != {
            "protocol",
            "capability",
            "status",
            "result",
            "checks",
        }:
            raise ValueError("Native core response has unsupported or missing fields")
        if (
            payload.get("protocol") != "saemphysics.capability.v1"
            or payload.get("capability") != "solve_linear_system"
            or payload.get("status") != "completed"
        ):
            raise ValueError("Native core response has an unsupported protocol or status")
        result_payload = payload.get("result")
        expected_result_fields = {"solution", "determinant", "residuals"}
        if (
            not isinstance(result_payload, dict)
            or set(result_payload) != expected_result_fields
        ):
            raise ValueError("Native linear-system result has unsupported or missing fields")
        solution = result_payload.get("solution")
        residuals = result_payload.get("residuals")
        determinant = result_payload.get("determinant")
        if (
            not isinstance(solution, list)
            or len(solution) != size
            or not all(isinstance(value, str) for value in solution)
            or not isinstance(residuals, list)
            or len(residuals) != size
            or not all(isinstance(value, str) for value in residuals)
            or not isinstance(determinant, str)
        ):
            raise ValueError("Native linear-system results must be exact strings")
        details = f"A*x - b = ({', '.join(residuals)})"
        checks = payload.get("checks")
        if (
            not isinstance(checks, list)
            or len(checks) != 1
            or not isinstance(checks[0], dict)
            or set(checks[0]) != {"name", "passed", "details"}
            or checks[0].get("name") != "linear_system_residual"
            or checks[0].get("passed") is not True
            or checks[0].get("details") != details
        ):
            raise ValueError("Native core response must pass its residual check")
        return LinearSystemResult(
            solution=tuple(solution),
            determinant=determinant,
            residuals=tuple(residuals),
            checks=(MathCheck(
                name="linear_system_residual",
                passed=True,
                details=details,
            ),),
        )
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise NativeBackendError(
            f"Native linear-system capability returned invalid JSON: {error}"
        ) from error


def _execute_math_request(plan: CompiledPlan):
    request = plan.semantic_ir
    if request.operation == "differentiate":
        if request.expression is None:
            raise ValueError("Differentiation request is missing its expression")
        result = differentiate(request.expression, request.variable)
    elif request.operation == "definite_integral":
        if (
            request.expression is None
            or request.lower_bound is None
            or request.upper_bound is None
        ):
            raise ValueError("Definite-integral request is missing required inputs")
        result = definite_integral(
            request.expression,
            request.lower_bound,
            request.upper_bound,
            request.variable,
        )
    elif request.operation == "solve_linear_system":
        if request.coefficients is None or request.right_hand_side is None:
            raise ValueError("Linear-system request is missing required inputs")
        result = solve_linear_system(
            request.coefficients,
            request.right_hand_side,
        )
    else:
        raise ValueError(f"Unsupported mathematics operation: {request.operation}")

    verification = MathVerificationReport(
        status="passed" if all(check.passed for check in result.checks) else "failed",
        checks=result.checks,
    )
    return result, verification


def execute_plan(
    plan: CompiledPlan,
    native_kinematics_executable: str | Path | None = None,
) -> RuntimeResult:
    """Execute a validated prototype plan and retain a layer-by-layer trace."""
    expected = compile_request(plan.semantic_ir)
    if plan.execution_ir != expected.execution_ir:
        raise ValueError("Execution IR does not match the semantic request")
    if plan.machine_ir != expected.machine_ir:
        raise ValueError("Machine IR does not match the execution plan")

    request = plan.semantic_ir
    trace = [
        TraceEvent(
            layer="semantic_ir",
            event=request.operation,
            details=f"Question {request.question_id}; arithmetic={request.numeric_mode.value}",
        ),
        TraceEvent(
            layer="execution_ir",
            event="planned",
            details=", ".join(step.value for step in plan.execution_ir.steps),
        ),
        TraceEvent(
            layer="machine_ir",
            event="lowered",
            details=(
                f"Backend profile {plan.machine_ir.profile_id}; "
                f"{len(plan.machine_ir.instructions)} declared operations"
            ),
        ),
    ]
    native_result: KinematicsResult | None = None
    native_math_result: LinearSystemResult | None = None

    if request.operation == "solve_constant_acceleration":
        if (
            request.initial_velocity_m_s is None
            or request.acceleration_m_s2 is None
            or request.time_s is None
        ):
            raise ValueError("Motion request is missing required inputs")
        python_reference = solve_constant_acceleration(
            request.initial_velocity_m_s,
            request.acceleration_m_s2,
            request.time_s,
        )
        if native_kinematics_executable is None:
            result = python_reference
        else:
            native_result = _execute_native_kinematics(
                native_kinematics_executable,
                request.initial_velocity_m_s,
                request.acceleration_m_s2,
                request.time_s,
            )
            if native_result != python_reference:
                raise NativeBackendError(
                    "Native kinematics result does not match the canonical Python result"
                )
            result = native_result
        verification: VerificationReport | MathVerificationReport = (
            verify_constant_acceleration(result)
        )
    elif (
        request.operation == "solve_linear_system"
        and native_kinematics_executable is not None
    ):
        if request.coefficients is None or request.right_hand_side is None:
            raise ValueError("Linear-system request is missing required inputs")
        python_reference = solve_linear_system(
            request.coefficients,
            request.right_hand_side,
        )
        native_math_result = _execute_native_linear_system(
            native_kinematics_executable,
            request.coefficients,
            request.right_hand_side,
        )
        if native_math_result != python_reference:
            raise NativeBackendError(
                "Native linear-system result does not match the canonical Python result"
            )
        result = native_math_result
        verification = MathVerificationReport(
            status="passed" if all(check.passed for check in result.checks) else "failed",
            checks=result.checks,
        )
    else:
        result, verification = _execute_math_request(plan)

    trace.append(
        TraceEvent(
            layer="runtime",
            event=(
                "native_kinematics_cross_checked"
                if native_result is not None
                else "native_linear_system_cross_checked"
                if native_math_result is not None
                else request.operation
            ),
            details=(
                "Executed the configured native capability and cross-checked its exact result "
                "against the canonical Python solver after validating the v1 core envelope."
                if native_result is not None
                else "Executed the configured native capability and cross-checked its exact result "
                "against the canonical Python solver after validating the v1 core envelope."
                if native_math_result is not None
                else f"Executed the {request.numeric_mode.value} Python math backend."
            ),
        )
    )
    trace.append(
        TraceEvent(
            layer="verification",
            event=verification.status,
            details=(
                f"{len(verification.checks)} verification checks: "
                + ", ".join(check.name for check in verification.checks)
            ),
        )
    )
    if verification.status != "passed":
        raise RuntimeError("Solver result failed independent verification")

    return RuntimeResult(
        question_id=request.question_id,
        result=result,
        verification=verification,
        trace=tuple(trace),
    )
