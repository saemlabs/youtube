import ast
import re

import sympy as sp


_MAX_EXPRESSION_LENGTH = 512
_MAX_EXPRESSION_NODES = 128
_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left**right,
}
_UNARY_OPERATORS = {
    ast.UAdd: lambda value: value,
    ast.USub: lambda value: -value,
}
_FUNCTIONS = {
    "cos": sp.cos,
    "exp": sp.exp,
    "log": sp.log,
    "sin": sp.sin,
    "sqrt": sp.sqrt,
    "tan": sp.tan,
}
_CONSTANTS = {"E": sp.E, "pi": sp.pi}


def _validate_name(name: str, field_name: str) -> None:
    if not isinstance(name, str) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) is None:
        raise ValueError(f"{field_name} must be a simple identifier")


def _build_expression(node: ast.AST) -> sp.Expr:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only integer and decimal numeric literals are supported")
        return sp.Rational(str(node.value))

    if isinstance(node, ast.Name):
        if node.id.startswith("_"):
            raise ValueError("Names beginning with underscores are not supported")
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        if node.id in _FUNCTIONS:
            raise ValueError(f"{node.id} must be called with one argument")
        return sp.Symbol(node.id)

    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("Only +, -, *, /, and ** operators are supported")
        left = _build_expression(node.left)
        right = _build_expression(node.right)
        if isinstance(node.op, ast.Pow) and (
            right.is_Integer is not True or abs(int(right)) > 32
        ):
            raise ValueError("Exponents must be integers between -32 and 32")
        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("Only unary + and - operators are supported")
        return operation(_build_expression(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise ValueError("Only approved mathematical functions are supported")
        if len(node.args) != 1 or node.keywords:
            raise ValueError("Mathematical functions require exactly one argument")
        return _FUNCTIONS[node.func.id](_build_expression(node.args[0]))

    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def parse_expression(expression: str, variable: str = "x") -> tuple[sp.Expr, sp.Symbol]:
    """Parse a deliberately small arithmetic grammar without evaluating Python."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must be a non-empty string")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("expression is too long")
    _validate_name(variable, "variable")
    if variable in _FUNCTIONS or variable in _CONSTANTS:
        raise ValueError("variable cannot shadow a built-in function or constant")

    try:
        syntax_tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("expression is not valid arithmetic syntax") from error
    if sum(1 for _ in ast.walk(syntax_tree)) > _MAX_EXPRESSION_NODES:
        raise ValueError("expression is too complex")

    parsed = _build_expression(syntax_tree.body)
    if parsed.has(sp.oo, -sp.oo, sp.zoo, sp.nan):
        raise ValueError("expression must not contain non-finite values")
    return parsed, sp.Symbol(variable)


def parse_rational(value: int | float | str, field_name: str) -> sp.Rational:
    """Convert a finite scalar to an exact SymPy rational."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field_name} must be a finite rational number")
    try:
        result = sp.Rational(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{field_name} must be a finite rational number") from error
    if result.is_finite is not True:
        raise ValueError(f"{field_name} must be a finite rational number")
    return result


def parse_real_bound(value: int | float | str, field_name: str) -> sp.Expr:
    """Parse an exact, finite real constant for a calculus interval endpoint."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field_name} must be an exact finite real number")
    expression, _ = parse_expression(str(value))
    if expression.free_symbols:
        raise ValueError(f"{field_name} must not contain variables")
    if expression.is_real is not True or expression.is_finite is not True:
        raise ValueError(f"{field_name} must be an exact finite real number")
    return expression
