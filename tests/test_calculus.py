import pytest

from saemphysics.maths.calculus import (
    definite_integral,
    differentiate,
    verify_derivative,
)


def test_differentiation_returns_exact_verified_derivative():
    result = differentiate("2 + 3*t", variable="t")

    assert result.derivative == "3"
    assert result.checks[0].passed


def test_differentiation_handles_chain_rule_and_trigonometric_functions():
    result = differentiate("sin(x**2)")

    assert result.derivative == "2*x*cos(x**2)"
    assert result.checks[0].passed


def test_derivative_verifier_rejects_a_wrong_candidate():
    check = verify_derivative("x**2", "x")

    assert not check.passed
    assert "residual" in check.details


def test_definite_integral_uses_exact_bounds_and_fundamental_theorem():
    result = definite_integral("2 + 3*t", "0", "4", variable="t")

    assert result.value == "32"
    assert {check.name for check in result.checks} == {
        "antiderivative",
        "fundamental_theorem",
        "definite_integral",
    }
    assert all(check.passed for check in result.checks)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo unsafe')",
        "x.real",
        "lambda: 1",
        "[x, 1]",
        "sin(x, x)",
        "x / 0",
        "x**100000000",
        "x**x",
    ],
)
def test_expression_parser_rejects_code_and_unsupported_syntax(expression):
    with pytest.raises(ValueError):
        differentiate(expression)


@pytest.mark.parametrize(
    ("expression", "lower", "upper"),
    [
        ("1/x", "-1", "1"),
        ("sqrt(x)", "-1", "1"),
    ],
)
def test_definite_integral_requires_continuity_on_interval(expression, lower, upper):
    with pytest.raises(ValueError, match="continuous"):
        definite_integral(expression, lower, upper)


def test_expression_parser_rejects_excessively_complex_input():
    expression = "+".join(["x"] * 130)

    with pytest.raises(ValueError, match="too complex"):
        differentiate(expression)


def test_definite_integral_respects_reversed_bounds():
    result = definite_integral("x", "1", "0")

    assert result.value == "-1/2"
    assert all(check.passed for check in result.checks)


def test_definite_integral_accepts_exact_transcendental_bounds():
    result = definite_integral("cos(x)", "0", "pi")

    assert result.value == "0"
    assert all(check.passed for check in result.checks)


@pytest.mark.parametrize("bound", ["y", "sqrt(-1)", "oo", True])
def test_definite_integral_rejects_variable_or_non_real_bounds(bound):
    with pytest.raises(ValueError, match="lower_bound"):
        definite_integral("x", bound, "1")
