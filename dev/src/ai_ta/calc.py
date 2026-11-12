"""Safe calculator for calculation questions: the model writes the steps, Python computes them.

A 9B model doing multi-step arithmetic in its head makes mistakes, and in the first eval it
copied numbers from an unrelated passage instead (mb-17). The model writes a short straight-line
program, one ``name = expression`` per line (or separated by ``;``). Only numbers, vectors and
matrices written with [ ], arithmetic, and a short list of math functions are allowed. Anything
else is rejected rather than executed, with a message the model can act on when it rewrites the
program (decision: dev/harness/EXPERIENCE.md, change 4).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

import numpy as np

MAX_PROGRAM_CHARS = 3000
MAX_STATEMENTS = 40
MAX_LITERAL_NUMBERS = 100   # numbers in one [ ] literal
MAX_RESULT_SIZE = 10_000    # elements in any intermediate result
MAX_EXPONENT = 100

Value = Any  # a float, or a numpy array of floats while running


def _log(x: Value, base: Value | None = None) -> Value:
    return np.log(x) if base is None else np.log(x) / np.log(base)


def _softmax(v: Value) -> Value:
    v = np.asarray(v, dtype=float)
    z = np.exp(v - v.max())
    return z / z.sum()


def _reduce(fn, **kwargs):
    """sum([1, 2]) and max(1, 2) both work."""
    return lambda *args: fn(np.asarray(args[0] if len(args) == 1 else args, dtype=float), **kwargs)


FUNCTIONS = {
    "log": _log, "ln": np.log, "log2": np.log2, "log10": np.log10, "sqrt": np.sqrt, "exp": np.exp,
    "abs": np.abs, "sum": _reduce(np.sum, axis=0), "mean": _reduce(np.mean, axis=0), "max": _reduce(np.max),
    "min": _reduce(np.min), "dot": np.dot, "norm": np.linalg.norm,
    "dist": lambda a, b: np.linalg.norm(np.subtract(a, b)),
    "relu": lambda x: np.maximum(0.0, x), "sigmoid": lambda x: 1 / (1 + np.exp(-np.asarray(x, dtype=float))),
    "softmax": _softmax,
}
CONSTANTS = {"pi": float(np.pi), "e": float(np.e)}
BINARY = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply, ast.Div: np.divide,
          ast.Pow: np.power, ast.MatMult: np.matmul}
UNARY = {ast.USub: np.negative, ast.UAdd: np.positive}
NORMALIZE = str.maketrans({"^": "**", "×": "*", "−": "-", "÷": "/", "（": "(", "）": ")", "，": ",", "；": ";"})


class CalcError(ValueError):
    """The program is not plain arithmetic, or it cannot be evaluated."""


@dataclass(frozen=True)
class Step:
    name: str                 # empty for a bare expression
    expression: str
    value: float | list       # a number, or nested lists for vectors and matrices
    literal: bool = False     # the expression only writes down given numbers

    def text(self) -> str:
        shown = format_value(self.value)
        if not self.name:
            return f"{self.expression} = {shown}"
        return f"{self.name} = {shown}" if self.literal else f"{self.name} = {self.expression} = {shown}"


def format_value(value: float | list) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(format_value(v) for v in value) + "]"
    return f"{value:.6g}"


def run(program: str) -> list[Step]:
    """Run a straight-line program and return every step with its value."""
    text = program.translate(NORMALIZE).strip()
    if not text:
        raise CalcError("沒有算式")
    if len(text) > MAX_PROGRAM_CHARS:
        raise CalcError("算式太長，請只寫需要的步驟")
    try:
        tree = ast.parse(text, mode="exec")
    except SyntaxError as exc:
        raise CalcError(f"第 {exc.lineno} 行語法錯誤（{exc.msg}）。名稱只能用英文字母、數字和底線，一行寫一步") from exc
    if len(tree.body) > MAX_STATEMENTS:
        raise CalcError(f"步驟太多（最多 {MAX_STATEMENTS} 行）")
    env: dict[str, Value] = {}
    steps = []
    with np.errstate(divide="raise", over="raise", invalid="raise", under="ignore"):
        for statement in tree.body:
            try:
                steps.append(_run_statement(statement, text, env))
            except CalcError:
                raise
            except (ArithmeticError, ValueError, TypeError, IndexError, np.linalg.LinAlgError) as exc:
                raise CalcError(f"第 {statement.lineno} 行算不出來：{exc}") from exc
    return steps


def evaluate(expression: str) -> float:
    """A single expression whose result is one number."""
    steps = run(expression)
    if len(steps) != 1 or isinstance(steps[0].value, list):
        raise CalcError("結果不是單一數字")
    return steps[0].value


def _run_statement(node: ast.stmt, text: str, env: dict[str, Value]) -> Step:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name.lower() in FUNCTIONS or name in CONSTANTS:
            raise CalcError(f"第 {node.lineno} 行：{name} 是函式或常數的名稱，請換一個名稱")
        value = _check(_eval(node.value, env))
        env[name] = value
        return Step(name, ast.get_source_segment(text, node.value) or "", _plain(value), _is_literal(node.value))
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript):
        raise CalcError(f"第 {node.lineno} 行：不能改向量裡的某一格，請另外取一個名稱")
    if isinstance(node, ast.Assign):
        raise CalcError(f"第 {node.lineno} 行：一行只能指定一個名稱，例如「a = 1」換行再寫「b = 2」")
    if isinstance(node, ast.Expr):
        expr = node.value
        if (isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "print"
                and len(expr.args) == 1 and not expr.keywords):
            expr = expr.args[0]  # tolerated: print(x) shows x
        return Step("", ast.get_source_segment(text, expr) or "", _plain(_check(_eval(expr, env))))
    if isinstance(node, (ast.For, ast.While)):
        raise CalcError(f"第 {node.lineno} 行：不能用迴圈，請把每一步寫成一行「名稱 = 算式」")
    if isinstance(node, ast.If):
        raise CalcError(f"第 {node.lineno} 行：不能用 if，比較大小留給回答")
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        raise CalcError(f"第 {node.lineno} 行：不能 import，可以直接用 log、sqrt、softmax 這些函式")
    raise CalcError(f"第 {node.lineno} 行：只能寫「名稱 = 算式」，不能用 {type(node).__name__}")


def _is_literal(node: ast.expr) -> bool:
    """Numbers written down as given, such as 0.5, -2 or [[1, 2], [3, 4]]."""
    if isinstance(node, ast.UnaryOp):
        return _is_literal(node.operand)
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_is_literal(item) for item in node.elts)
    return isinstance(node, ast.Constant)


def _eval(node: ast.expr, env: dict[str, Value]) -> Value:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        raise CalcError("算式裡不能有文字，只能有數字")
    if isinstance(node, (ast.List, ast.Tuple)):
        array = np.array([_eval(item, env) for item in node.elts], dtype=float)
        if array.size > MAX_LITERAL_NUMBERS:
            raise CalcError(f"一個 [ ] 裡最多 {MAX_LITERAL_NUMBERS} 個數字")
        return array
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        if node.id.lower() in FUNCTIONS:
            raise CalcError(f"{node.id} 是函式，要寫成 {node.id}(…)")
        raise CalcError(f"{node.id} 還沒定義，請先寫一行「{node.id} = …」，題目給的數字要自己寫進去")
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        left, right = _eval(node.left, env), _eval(node.right, env)
        if isinstance(node.op, ast.Pow) and np.max(np.abs(right)) > MAX_EXPONENT:
            raise CalcError("次方太大")
        return BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](_eval(node.operand, env))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id.lower()
        if name not in FUNCTIONS:
            raise CalcError(f"不能用函式 {node.func.id}；可以用的函式：{'、'.join(FUNCTIONS)}")
        if node.keywords:
            raise CalcError(f"{node.func.id} 只能照順序給參數，不能寫 名稱=值")
        return FUNCTIONS[name](*(_eval(arg, env) for arg in node.args))
    if isinstance(node, ast.Subscript):
        return np.asarray(_eval(node.value, env))[_index(node.slice)]
    if isinstance(node, ast.Attribute) and node.attr == "T":
        return np.asarray(_eval(node.value, env)).T  # transpose, the one attribute programs commonly use
    if isinstance(node, ast.IfExp):
        raise CalcError("不能用「a if 條件 else b」；ReLU 請用 relu(x)，取較大的用 max(a, b)")
    if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
        raise CalcError("不能用 [… for …]；函式可以直接用在整個向量上，例如 exp(v)、relu(v)")
    if isinstance(node, ast.Compare):
        raise CalcError("不能比大小；把每個值算出來，判斷留給回答")
    raise CalcError(f"算式裡不能用 {type(node).__name__}；只能用數字、[ ]、+ - * / ** @ 和允許的函式")


def _index(node: ast.expr) -> int | tuple[int, ...]:
    """Only fixed whole-number positions, such as v[0], v[-1] or W[0, 1]."""
    if isinstance(node, ast.Tuple):
        return tuple(_index(item) for item in node.elts)  # type: ignore[misc]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_index(node.operand)  # type: ignore[operator]
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    raise CalcError("[ ] 裡的位置只能寫整數，例如 v[0]（從 0 開始數）")


def _check(value: Value) -> Value:
    array = np.asarray(value)
    if array.dtype.kind not in "fiu":
        raise CalcError("結果不是數字")
    if array.size > MAX_RESULT_SIZE:
        raise CalcError("結果太大")
    if not np.all(np.isfinite(array)):
        raise CalcError("結果不是有限的數字")
    return value


def _plain(value: Value) -> float | list:
    array = np.asarray(value, dtype=float)
    return float(array) if array.ndim == 0 else array.tolist()
