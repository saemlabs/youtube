from collections.abc import Sequence

from saemphysics.maths import (
    DefiniteIntegralResult,
    DerivativeResult,
    LinearSystemResult,
)
from saemphysics.models import (
    QuestionRecord,
    SolutionArtifact,
    SolutionStatus,
    VerificationCheck,
)
from saemphysics.runtime import RuntimeResult
from saemphysics.solvers.mechanics import KinematicsResult


def attach_verified_solution(
    question: QuestionRecord,
    execution: RuntimeResult,
    derivation_steps: Sequence[str],
    assumptions: Sequence[str] = (),
) -> QuestionRecord:
    """Attach checked computation while requiring a supplied human-readable derivation."""
    if execution.question_id != question.question_id:
        raise ValueError("The execution result belongs to a different question")
    if execution.verification.status != "passed":
        raise ValueError("Only a passed execution result can be attached")
    if not execution.verification.checks or not all(
        check.passed for check in execution.verification.checks
    ):
        raise ValueError("The execution result must contain passing checks")

    steps = list(derivation_steps)
    if not steps or any(
        not isinstance(step, str) or not step.strip() for step in steps
    ):
        raise ValueError("Provide at least one non-empty derivation step")

    result = execution.result
    if isinstance(result, KinematicsResult):
        symbolic_result = "s = ut + 1/2 at^2; v = u + at"
        numerical_result = (
            f"displacement={result.displacement_m} m; "
            f"final_velocity={result.final_velocity_m_s} m/s"
        )
        units = "m, m/s"
    elif isinstance(result, DerivativeResult):
        symbolic_result = f"d({result.expression})/d{result.variable}"
        numerical_result = result.derivative
        units = None
    elif isinstance(result, DefiniteIntegralResult):
        symbolic_result = (
            f"integral[{result.lower_bound}, {result.upper_bound}] "
            f"{result.expression} d{result.variable}"
        )
        numerical_result = result.value
        units = None
    elif isinstance(result, LinearSystemResult):
        symbolic_result = "A*x = b"
        numerical_result = f"x = ({', '.join(result.solution)})"
        units = None
    else:
        raise TypeError(f"Unsupported execution result type: {type(result).__name__}")

    solution = SolutionArtifact(
        status=SolutionStatus.VERIFIED,
        assumptions=list(assumptions),
        derivation_steps=steps,
        symbolic_result=symbolic_result,
        numerical_result=numerical_result,
        units=units,
        verification_checks=[
            VerificationCheck(
                name=check.name,
                passed=check.passed,
                details=check.details,
            )
            for check in execution.verification.checks
        ],
    )
    return question.model_copy(update={"solution": solution})
