from enum import Enum
from fractions import Fraction
from typing import Literal

from pydantic import Field, field_validator

from saemphysics.models import StrictModel


class NumericMode(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"


class ExecutionStep(str, Enum):
    VALIDATE_EXACT_INPUTS = "validate_exact_inputs"
    SOLVE_CONSTANT_ACCELERATION = "solve_constant_acceleration"
    VERIFY_EQUATIONS = "verify_equations"
    ASSEMBLE_RESULT = "assemble_result"


class SemanticIR(StrictModel):
    """Machine-independent meaning of a constant-acceleration request."""

    operation: Literal["solve_constant_acceleration"]
    question_id: str = Field(min_length=1)
    initial_velocity_m_s: str
    acceleration_m_s2: str
    time_s: str
    numeric_mode: NumericMode = NumericMode.EXACT

    @field_validator(
        "initial_velocity_m_s",
        "acceleration_m_s2",
        "time_s",
    )
    @classmethod
    def require_exact_rational(cls, value: str) -> str:
        try:
            Fraction(value)
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError("Semantic IR inputs must be exact rational numbers") from error
        return value


class ExecutionIR(StrictModel):
    """Backend-independent operations needed to fulfill a semantic request."""

    operation: Literal["solve_constant_acceleration"]
    question_id: str
    numeric_mode: NumericMode
    steps: tuple[ExecutionStep, ...]


class MachineCapabilities(StrictModel):
    """Declared backend capabilities; this is not hardware discovery."""

    profile_id: str = Field(min_length=1)
    supported_operations: frozenset[str]
    supported_numeric_modes: frozenset[NumericMode]


class MachineInstruction(str, Enum):
    VALIDATE_RATIONAL_INPUTS = "python.validate_rational_inputs"
    CALL_KINEMATICS_SOLVER = "python.solve_constant_acceleration"
    CALL_EQUATION_VERIFIER = "python.verify_constant_acceleration"
    RETURN_VERIFIED_RESULT = "python.return_verified_result"


class MachineIR(StrictModel):
    """Prototype Python-backend lowering, not native CPU instructions."""

    profile_id: str
    question_id: str
    instructions: tuple[MachineInstruction, ...]


class CompiledPlan(StrictModel):
    semantic_ir: SemanticIR
    execution_ir: ExecutionIR
    machine_ir: MachineIR


class CapabilityError(ValueError):
    """Raised when a declared backend cannot honor a request."""


DEFAULT_MACHINE_CAPABILITIES = MachineCapabilities(
    profile_id="python-symbolic",
    supported_operations=frozenset({"solve_constant_acceleration"}),
    supported_numeric_modes=frozenset({NumericMode.EXACT}),
)


_EXECUTION_TO_MACHINE = {
    ExecutionStep.VALIDATE_EXACT_INPUTS: MachineInstruction.VALIDATE_RATIONAL_INPUTS,
    ExecutionStep.SOLVE_CONSTANT_ACCELERATION: MachineInstruction.CALL_KINEMATICS_SOLVER,
    ExecutionStep.VERIFY_EQUATIONS: MachineInstruction.CALL_EQUATION_VERIFIER,
    ExecutionStep.ASSEMBLE_RESULT: MachineInstruction.RETURN_VERIFIED_RESULT,
}

_KINEMATICS_STEPS = (
    ExecutionStep.VALIDATE_EXACT_INPUTS,
    ExecutionStep.SOLVE_CONSTANT_ACCELERATION,
    ExecutionStep.VERIFY_EQUATIONS,
    ExecutionStep.ASSEMBLE_RESULT,
)


def compile_request(
    semantic_ir: SemanticIR,
    capabilities: MachineCapabilities = DEFAULT_MACHINE_CAPABILITIES,
) -> CompiledPlan:
    """Plan and lower a semantic operation against explicit capabilities."""
    if capabilities.profile_id != DEFAULT_MACHINE_CAPABILITIES.profile_id:
        raise CapabilityError(
            f"Backend profile {capabilities.profile_id!r} has no registered executor"
        )
    if semantic_ir.operation not in capabilities.supported_operations:
        raise CapabilityError(
            f"Backend {capabilities.profile_id!r} does not support "
            f"{semantic_ir.operation!r}"
        )
    if semantic_ir.numeric_mode != NumericMode.EXACT:
        raise CapabilityError(
            f"{semantic_ir.numeric_mode.value!r} execution is not implemented"
        )
    if semantic_ir.numeric_mode not in capabilities.supported_numeric_modes:
        raise CapabilityError(
            f"Backend {capabilities.profile_id!r} does not support "
            f"{semantic_ir.numeric_mode.value!r} arithmetic"
        )

    execution_ir = ExecutionIR(
        operation=semantic_ir.operation,
        question_id=semantic_ir.question_id,
        numeric_mode=semantic_ir.numeric_mode,
        steps=_KINEMATICS_STEPS,
    )
    machine_ir = MachineIR(
        profile_id=capabilities.profile_id,
        question_id=semantic_ir.question_id,
        instructions=tuple(_EXECUTION_TO_MACHINE[step] for step in execution_ir.steps),
    )
    return CompiledPlan(
        semantic_ir=semantic_ir,
        execution_ir=execution_ir,
        machine_ir=machine_ir,
    )
