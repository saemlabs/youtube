"""Run calculus and operator examples through the compiled math runtime."""

from saemphysics.ir import SemanticIR, compile_request
from saemphysics.runtime import execute_plan


def main() -> None:
    velocity = execute_plan(
        compile_request(
            SemanticIR(
                operation="differentiate",
                question_id="cart-acceleration",
                expression="2 + 3*t",
                variable="t",
            )
        )
    )
    displacement = execute_plan(
        compile_request(
            SemanticIR(
                operation="definite_integral",
                question_id="cart-displacement",
                expression="2 + 3*t",
                variable="t",
                lower_bound="0",
                upper_bound="4",
            )
        )
    )
    linear_solution = execute_plan(
        compile_request(
            SemanticIR(
                operation="solve_linear_system",
                question_id="linear-operator",
                coefficients=[["2", "1"], ["1", "-1"]],
                right_hand_side=["5", "1"],
            )
        )
    )

    print(
        "Acceleration: "
        f"d({velocity.result.expression})/dt = {velocity.result.derivative} "
        f"[{velocity.verification.status}]"
    )
    print(
        "Displacement from 0 s to 4 s: "
        f"{displacement.result.value} m "
        f"({displacement.verification.status}; "
        f"{len(displacement.verification.checks)} checks)"
    )
    print(
        "Operator solve A*x=b: "
        f"x={linear_solution.result.solution}; "
        f"determinant={linear_solution.result.determinant} "
        f"[{linear_solution.verification.status}]"
    )


if __name__ == "__main__":
    main()
