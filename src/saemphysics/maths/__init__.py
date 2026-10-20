"""Exact calculus and linear-algebra tools for verified lessons."""

from saemphysics.maths.calculus import (
    DefiniteIntegralResult,
    DerivativeResult,
    definite_integral,
    differentiate,
    verify_derivative,
)
from saemphysics.maths.linear_algebra import (
    LinearSystemResult,
    solve_linear_system,
)

__all__ = [
    "DefiniteIntegralResult",
    "DerivativeResult",
    "LinearSystemResult",
    "definite_integral",
    "differentiate",
    "solve_linear_system",
    "verify_derivative",
]
