from dataclasses import dataclass

from saemphysics.ir import (
    CompiledPlan,
    ExecutionStep,
    MachineInstruction,
    compile_request,
)
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
class RuntimeResult:
    result: KinematicsResult
    verification: VerificationReport
    trace: tuple[TraceEvent, ...]


def execute_plan(plan: CompiledPlan) -> RuntimeResult:
    """Execute a validated prototype plan and retain a layer-by-layer trace."""
    expected = compile_request(plan.semantic_ir)
    if plan.execution_ir != expected.execution_ir:
        raise ValueError("Execution IR does not match the semantic request")
    if plan.machine_ir != expected.machine_ir:
        raise ValueError("Machine IR does not match the execution plan")

    instructions = plan.machine_ir.instructions
    required = (
        MachineInstruction.VALIDATE_RATIONAL_INPUTS,
        MachineInstruction.CALL_KINEMATICS_SOLVER,
        MachineInstruction.CALL_EQUATION_VERIFIER,
        MachineInstruction.RETURN_VERIFIED_RESULT,
    )
    if instructions != required:
        raise ValueError("Machine IR contains an unsupported instruction sequence")

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

    result = solve_constant_acceleration(
        request.initial_velocity_m_s,
        request.acceleration_m_s2,
        request.time_s,
    )
    trace.append(
        TraceEvent(
            layer="runtime",
            event=ExecutionStep.SOLVE_CONSTANT_ACCELERATION.value,
            details="Executed the deterministic SymPy-backed solver.",
        )
    )
    verification = verify_constant_acceleration(result)
    trace.append(
        TraceEvent(
            layer="verification",
            event=verification.status,
            details=f"{len(verification.checks)} verification checks",
        )
    )
    if verification.status != "passed":
        raise RuntimeError("Solver result failed independent verification")

    return RuntimeResult(
        result=result,
        verification=verification,
        trace=tuple(trace),
    )
