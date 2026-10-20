import pytest

from saemphysics.maths.linear_algebra import solve_linear_system


def test_linear_operator_solver_returns_exact_solution_and_zero_residual():
    result = solve_linear_system(
        coefficients=[["2", "1"], ["1", "-1"]],
        right_hand_side=["5", "1"],
    )

    assert result.solution == ("2", "1")
    assert result.determinant == "-3"
    assert result.residuals == ("0", "0")
    assert all(check.passed for check in result.checks)


def test_linear_solver_preserves_fractional_inputs():
    result = solve_linear_system(
        coefficients=[["1/2", "0"], ["0", "2"]],
        right_hand_side=["1", "1"],
    )

    assert result.solution == ("2", "1/2")


@pytest.mark.parametrize(
    ("coefficients", "right_hand_side", "message"),
    [
        ([], [], "non-empty"),
        ([[1, 2]], [1], "square"),
        ([[1, 0], [0, 1]], [1], "one entry per matrix row"),
        ([[1, 2], [2, 4]], [3, 6], "singular"),
        ([[1, 0], [0, 1]], [1, "1/0"], "finite rational"),
        (["12", "34"], [1, 2], "matrix rows"),
    ],
)
def test_linear_solver_rejects_invalid_or_underdetermined_systems(
    coefficients,
    right_hand_side,
    message,
):
    with pytest.raises(ValueError, match=message):
        solve_linear_system(coefficients, right_hand_side)
