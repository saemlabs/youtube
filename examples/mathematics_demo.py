"""A small exact-math workflow connecting rates, accumulation, and operators."""

from saemphysics.maths import definite_integral, differentiate, solve_linear_system


def main() -> None:
    velocity = differentiate("2 + 3*t", variable="t")
    displacement = definite_integral("2 + 3*t", "0", "4", variable="t")
    linear_solution = solve_linear_system(
        coefficients=[["2", "1"], ["1", "-1"]],
        right_hand_side=["5", "1"],
    )

    print(f"Acceleration: d({velocity.expression})/dt = {velocity.derivative}")
    print(
        "Displacement from 0 s to 4 s: "
        f"{displacement.value} m "
        f"({len(displacement.checks)} checks passed)"
    )
    print(
        "Operator solve A*x=b: "
        f"x={linear_solution.solution}; determinant={linear_solution.determinant}"
    )


if __name__ == "__main__":
    main()
