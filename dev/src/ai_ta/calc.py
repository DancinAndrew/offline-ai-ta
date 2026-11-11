"""Safe arithmetic for calculation questions: the model writes the expression, Python computes it.

A 9B model doing multi-step arithmetic in its head makes mistakes, and in the first eval it
copied numbers from an unrelated passage instead (mb-17). Only numbers, + - * / **, and a few
math functions are allowed; anything else is rejected rather than executed.
"""

from __future__ import annotations

import ast
import math
import operator

FUNCTIONS = {
    "log": math.log, "ln": math.log, "log2": math.log2, "log10": math.log10,
    "sqrt": math.sqrt, "exp": math.exp, "abs": abs,
}
CONSTANTS = {"pi": math.pi, "e": math.e}
OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
MAX_EXPONENT = 100


class CalcError(ValueError):
    """The expression is not plain arithmetic, or it cannot be evaluated."""


def evaluate(expression: str) -> float:
    normalized = expression.replace("^", "**").replace("×", "*").replace("−", "-").replace("÷", "/")
    try:
        tree = ast.parse(normalized, mode="eval")
        return float(_eval(tree.body))
    except CalcError:
        raise
    except (SyntaxError, ZeroDivisionError, ValueError, OverflowError, TypeError) as exc:
        raise CalcError(f"cannot evaluate {expression!r}: {exc}") from exc


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise CalcError("exponent too large")
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval(node.operand))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS
            and not node.keywords):
        return FUNCTIONS[node.func.id](*(_eval(arg) for arg in node.args))
    if isinstance(node, ast.Name) and node.id in CONSTANTS:
        return CONSTANTS[node.id]
    raise CalcError(f"not allowed in a calculation: {type(node).__name__}")
