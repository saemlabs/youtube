from collections.abc import Sequence
from dataclasses import dataclass

import sympy as sp

from saemphysics.maths.expressions import parse_rational
from saemphysics.maths.verification import MathCheck


@dataclass(frozen=True)
class LinearSystemResult:
    solution: tuple[str, ...]
    determinant: str
    residuals: tuple[str, ...]
    checks: tuple[MathCheck, ...]


def _matrix_values(
    coefficients: Sequence[Sequence[int | float | str]],
) -> tuple[tuple[sp.Rational, ...], ...]:
    if isinstance(coefficients, (str, bytes)):
        raise ValueError("coefficients must be a non-empty square matrix")
    try:
        raw_rows = tuple(coefficients)
    except TypeError as error:
        raise ValueError("coefficients must be a non-empty square matrix") from error
    if any(isinstance(row, (str, bytes)) for row in raw_rows):
        raise ValueError("matrix rows must be sequences of scalar values")
    try:
        rows = tuple(tuple(row) for row in raw_rows)
    except TypeError as error:
        raise ValueError("matrix rows must be sequences of scalar values") from error
    if not rows or any(not row for row in rows):
        raise ValueError("coefficients must be a non-empty square matrix")
    if any(len(row) != len(rows) for row in rows):
        raise ValueError("coefficients must be square")
    return tuple(
        tuple(
            parse_rational(value, f"coefficients[{row_index}][{column_index}]")
            for column_index, value in enumerate(row)
        )
        for row_index, row in enumerate(rows)
    )


def solve_linear_system(
    coefficients: Sequence[Sequence[int | float | str]],
    right_hand_side: Sequence[int | float | str],
) -> LinearSystemResult:
    """Solve A x = b exactly, treating A as an operator on the input vector."""
    values = _matrix_values(coefficients)
    if isinstance(right_hand_side, (str, bytes)):
        raise ValueError("right_hand_side must have one entry per matrix row")
    try:
        raw_rhs = tuple(right_hand_side)
    except TypeError as error:
        raise ValueError(
            "right_hand_side must have one entry per matrix row"
        ) from error
    if len(raw_rhs) != len(values):
        raise ValueError("right_hand_side must have one entry per matrix row")

    matrix = sp.Matrix(values)
    vector = sp.Matrix(
        [
            parse_rational(value, f"right_hand_side[{index}]")
            for index, value in enumerate(raw_rhs)
        ]
    )
    determinant = matrix.det()
    if determinant == 0:
        raise ValueError("coefficient matrix is singular; no unique solution exists")

    solution = matrix.LUsolve(vector)
    residual = matrix * solution - vector
    residuals = tuple(sp.sstr(value) for value in residual)
    check = MathCheck(
        name="linear_system_residual",
        passed=all(value == 0 for value in residual),
        details=f"A*x - b = ({', '.join(residuals)})",
    )
    if not check.passed:
        raise RuntimeError("The computed solution failed residual verification")
    return LinearSystemResult(
        solution=tuple(sp.sstr(value) for value in solution),
        determinant=sp.sstr(determinant),
        residuals=residuals,
        checks=(check,),
    )
