from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from saemphysics.maths.expressions import (
    parse_expression,
    parse_rational,
    parse_real_bound,
)
from saemphysics.models import StrictModel


class NumericMode(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"


class ExecutionStep(str, Enum):
    VALIDATE_EXACT_INPUTS = "validate_exact_inputs"
    SOLVE_CONSTANT_ACCELERATION = "solve_constant_acceleration"
    DIFFERENTIATE_EXPRESSION = "differentiate_expression"
    INTEGRATE_EXPRESSION = "integrate_expression"
    SOLVE_LINEAR_SYSTEM = "solve_linear_system"
    VERIFY_EQUATIONS = "verify_equations"
    VERIFY_MATHEMATICS = "verify_mathematics"
    ASSEMBLE_RESULT = "assemble_result"


class SemanticIR(StrictModel):
    """Machine-independent meaning of a verified mathematics request."""

    operation: Literal[
        "solve_constant_acceleration",
        "differentiate",
        "definite_integral",
        "solve_linear_system",
    ]
    question_id: str = Field(min_length=1)
    initial_velocity_m_s: str | None = None
    acceleration_m_s2: str | None = None
    time_s: str | None = None
    expression: str | None = None
    variable: str = "x"
    lower_bound: str | None = None
    upper_bound: str | None = None
    coefficients: list[list[str]] | None = None
    right_hand_side: list[str] | None = None
    numeric_mode: NumericMode = NumericMode.EXACT

    @model_validator(mode="after")
    def validate_operation_inputs(self):
        kinematics_fields = (
            self.initial_velocity_m_s,
            self.acceleration_m_s2,
            self.time_s,
        )
        calculus_fields = (
            self.expression,
            self.lower_bound,
            self.upper_bound,
        )

        if self.operation == "solve_constant_acceleration":
            if any(value is None for value in kinematics_fields):
                raise ValueError(
                    "Constant-acceleration requests require initial velocity, "
                    "acceleration, and time"
                )
            if any(value is not None for value in calculus_fields) or any(
                value is not None
                for value in (self.coefficients, self.right_hand_side)
            ):
                raise ValueError(
                    "Constant-acceleration requests cannot include unrelated inputs"
                )
            for name, value in zip(
                ("initial_velocity_m_s", "acceleration_m_s2", "time_s"),
                kinematics_fields,
            ):
                try:
                    parse_rational(value, name)
                except ValueError as error:
                    raise ValueError(
                        "Semantic IR inputs must be exact rational numbers"
                    ) from error
            if parse_rational(self.time_s, "time_s") < 0:
                raise ValueError("time_s must be non-negative")
            return self

        if any(value is not None for value in kinematics_fields):
            raise ValueError("Mathematics requests cannot include motion inputs")

        if self.operation in {"differentiate", "definite_integral"}:
            if self.expression is None:
                raise ValueError(f"{self.operation} requests require an expression")
            if self.coefficients is not None or self.right_hand_side is not None:
                raise ValueError(
                    "Calculus requests cannot include linear-system inputs"
                )
            parse_expression(self.expression, self.variable)
            if self.operation == "differentiate":
                if self.lower_bound is not None or self.upper_bound is not None:
                    raise ValueError(
                        "Differentiation requests cannot include integration bounds"
                    )
            else:
                if self.lower_bound is None or self.upper_bound is None:
                    raise ValueError(
                        "Definite integrals require lower and upper bounds"
                    )
                parse_real_bound(self.lower_bound, "lower_bound")
                parse_real_bound(self.upper_bound, "upper_bound")
            return self

        if self.operation == "solve_linear_system":
            if self.coefficients is None or self.right_hand_side is None:
                raise ValueError(
                    "Linear-system requests require coefficients and a right-hand side"
                )
            if any(value is not None for value in calculus_fields):
                raise ValueError(
                    "Linear-system requests cannot include calculus inputs"
                )
            row_count = len(self.coefficients)
            if row_count == 0 or any(
                len(row) != row_count for row in self.coefficients
            ):
                raise ValueError("coefficients must be a non-empty square matrix")
            if len(self.right_hand_side) != row_count:
                raise ValueError(
                    "right_hand_side must have one entry per matrix row"
                )
            for row_index, row in enumerate(self.coefficients):
                for column_index, value in enumerate(row):
                    parse_rational(
                        value,
                        f"coefficients[{row_index}][{column_index}]",
                    )
            for index, value in enumerate(self.right_hand_side):
                parse_rational(value, f"right_hand_side[{index}]")
            return self

        raise ValueError(f"Unsupported semantic operation: {self.operation}")


class ExecutionIR(StrictModel):
    """Backend-independent operations needed to fulfill a semantic request."""

    operation: Literal[
        "solve_constant_acceleration",
        "differentiate",
        "definite_integral",
        "solve_linear_system",
    ]
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
    CALL_DIFFERENTIATOR = "python.differentiate"
    CALL_DEFINITE_INTEGRATOR = "python.definite_integral"
    CALL_LINEAR_SYSTEM_SOLVER = "python.solve_linear_system"
    CALL_EQUATION_VERIFIER = "python.verify_constant_acceleration"
    CALL_MATHEMATICS_VERIFIER = "python.verify_mathematics"
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
    supported_operations=frozenset(
        {
            "solve_constant_acceleration",
            "differentiate",
            "definite_integral",
            "solve_linear_system",
        }
    ),
    supported_numeric_modes=frozenset({NumericMode.EXACT}),
)


_KINEMATICS_STEPS = (
    ExecutionStep.VALIDATE_EXACT_INPUTS,
    ExecutionStep.SOLVE_CONSTANT_ACCELERATION,
    ExecutionStep.VERIFY_EQUATIONS,
    ExecutionStep.ASSEMBLE_RESULT,
)

_OPERATION_STEPS = {
    "solve_constant_acceleration": _KINEMATICS_STEPS,
    "differentiate": (
        ExecutionStep.VALIDATE_EXACT_INPUTS,
        ExecutionStep.DIFFERENTIATE_EXPRESSION,
        ExecutionStep.VERIFY_MATHEMATICS,
        ExecutionStep.ASSEMBLE_RESULT,
    ),
    "definite_integral": (
        ExecutionStep.VALIDATE_EXACT_INPUTS,
        ExecutionStep.INTEGRATE_EXPRESSION,
        ExecutionStep.VERIFY_MATHEMATICS,
        ExecutionStep.ASSEMBLE_RESULT,
    ),
    "solve_linear_system": (
        ExecutionStep.VALIDATE_EXACT_INPUTS,
        ExecutionStep.SOLVE_LINEAR_SYSTEM,
        ExecutionStep.VERIFY_MATHEMATICS,
        ExecutionStep.ASSEMBLE_RESULT,
    ),
}
_EXECUTION_TO_MACHINE = {
    ExecutionStep.VALIDATE_EXACT_INPUTS: MachineInstruction.VALIDATE_RATIONAL_INPUTS,
    ExecutionStep.SOLVE_CONSTANT_ACCELERATION: MachineInstruction.CALL_KINEMATICS_SOLVER,
    ExecutionStep.DIFFERENTIATE_EXPRESSION: MachineInstruction.CALL_DIFFERENTIATOR,
    ExecutionStep.INTEGRATE_EXPRESSION: MachineInstruction.CALL_DEFINITE_INTEGRATOR,
    ExecutionStep.SOLVE_LINEAR_SYSTEM: MachineInstruction.CALL_LINEAR_SYSTEM_SOLVER,
    ExecutionStep.VERIFY_EQUATIONS: MachineInstruction.CALL_EQUATION_VERIFIER,
    ExecutionStep.VERIFY_MATHEMATICS: MachineInstruction.CALL_MATHEMATICS_VERIFIER,
    ExecutionStep.ASSEMBLE_RESULT: MachineInstruction.RETURN_VERIFIED_RESULT,
}


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
        steps=_OPERATION_STEPS[semantic_ir.operation],
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
