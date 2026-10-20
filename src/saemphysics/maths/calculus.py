from dataclasses import dataclass

import sympy as sp

from saemphysics.maths.expressions import parse_expression, parse_real_bound
from saemphysics.maths.verification import MathCheck


@dataclass(frozen=True)
class DerivativeResult:
    expression: str
    variable: str
    derivative: str
    checks: tuple[MathCheck, ...]


@dataclass(frozen=True)
class DefiniteIntegralResult:
    expression: str
    variable: str
    lower_bound: str
    upper_bound: str
    value: str
    checks: tuple[MathCheck, ...]


def verify_derivative(
    expression: str,
    candidate: str,
    variable: str = "x",
) -> MathCheck:
    """Compare a proposed derivative with the exact symbolic derivative."""
    source, symbol = parse_expression(expression, variable)
    proposed, _ = parse_expression(candidate, variable)
    residual = sp.simplify(proposed - sp.diff(source, symbol))
    passed = residual == 0
    return MathCheck(
        name="symbolic_derivative",
        passed=passed,
        details=f"Derivative residual: {sp.sstr(residual)}",
    )


def differentiate(expression: str, variable: str = "x") -> DerivativeResult:
    """Differentiate a supported expression and retain an explicit check."""
    source, symbol = parse_expression(expression, variable)
    derivative = sp.simplify(sp.diff(source, symbol))
    if derivative.has(sp.Derivative):
        raise ValueError("The derivative could not be evaluated symbolically")

    check = verify_derivative(expression, sp.sstr(derivative), variable)
    if not check.passed:
        raise RuntimeError("The computed derivative failed symbolic verification")
    return DerivativeResult(
        expression=sp.sstr(source),
        variable=variable,
        derivative=sp.sstr(derivative),
        checks=(check,),
    )


def _continuous_on_interval(
    expression: sp.Expr,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
) -> bool:
    try:
        domain = sp.calculus.util.continuous_domain(
            expression,
            variable,
            sp.S.Reals,
        )
    except NotImplementedError as error:
        raise ValueError(
            "Continuity could not be established for the requested integral"
        ) from error
    interval = sp.Interval(sp.Min(lower, upper), sp.Max(lower, upper))
    return interval.is_subset(domain) is True


def _verify_definite_integral(
    expression: sp.Expr,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
    candidate: sp.Expr,
) -> tuple[MathCheck, ...]:
    direct = sp.integrate(expression, (variable, lower, upper))
    antiderivative = sp.integrate(expression, variable)
    if direct.has(sp.Integral) or antiderivative.has(sp.Integral):
        raise ValueError("The requested integral could not be evaluated exactly")
    if direct.is_finite is not True:
        raise ValueError("The requested integral is not verified as finite")

    derivative_residual = sp.simplify(sp.diff(antiderivative, variable) - expression)
    fundamental_theorem_residual = sp.simplify(
        antiderivative.subs(variable, upper)
        - antiderivative.subs(variable, lower)
        - candidate
    )
    direct_residual = sp.simplify(candidate - direct)
    checks = (
        MathCheck(
            name="antiderivative",
            passed=derivative_residual == 0,
            details=f"Derivative residual: {sp.sstr(derivative_residual)}",
        ),
        MathCheck(
            name="fundamental_theorem",
            passed=fundamental_theorem_residual == 0,
            details=(
                "Endpoint-evaluation residual: "
                f"{sp.sstr(fundamental_theorem_residual)}"
            ),
        ),
        MathCheck(
            name="definite_integral",
            passed=direct_residual == 0,
            details=f"Integral residual: {sp.sstr(direct_residual)}",
        ),
    )
    if not all(check.passed for check in checks):
        raise RuntimeError("The computed integral failed symbolic verification")
    return checks


def definite_integral(
    expression: str,
    lower_bound: int | float | str,
    upper_bound: int | float | str,
    variable: str = "x",
) -> DefiniteIntegralResult:
    """Compute a finite exact definite integral over a continuous interval."""
    source, symbol = parse_expression(expression, variable)
    lower = parse_real_bound(lower_bound, "lower_bound")
    upper = parse_real_bound(upper_bound, "upper_bound")
    if not _continuous_on_interval(source, symbol, lower, upper):
        raise ValueError(
            "The integrand must be established as continuous on the closed interval"
        )

    value = sp.integrate(source, (symbol, lower, upper))
    if value.has(sp.Integral) or value.is_finite is not True:
        raise ValueError("The requested integral could not be evaluated exactly")
    checks = _verify_definite_integral(source, symbol, lower, upper, value)
    return DefiniteIntegralResult(
        expression=sp.sstr(source),
        variable=variable,
        lower_bound=sp.sstr(lower),
        upper_bound=sp.sstr(upper),
        value=sp.sstr(value),
        checks=checks,
    )
