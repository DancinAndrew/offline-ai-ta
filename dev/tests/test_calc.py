"""Tests for the safe calculator. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest

import math

from ai_ta.calc import MAX_STATEMENTS, CalcError, evaluate, run


class CalcTest(unittest.TestCase):
    def test_entropy_of_a_two_to_three_split(self):
        self.assertAlmostEqual(evaluate("-(2/5)*log2(2/5) - (3/5)*log2(3/5)"), 0.970951, places=6)

    def test_common_notation_is_accepted(self):
        self.assertAlmostEqual(evaluate("(3^3 + 4^3)^(1/3)"), 4.497941, places=6)
        self.assertAlmostEqual(evaluate("0.98 × 0.008 ÷ 0.0376"), 0.2085106, places=6)
        self.assertAlmostEqual(evaluate("log(8, 2)"), 3.0)

    def test_code_is_rejected(self):
        for expression in ("__import__('os').system('ls')", "open('x')", "(1).real", "[1, 2]", "True + 1"):
            with self.assertRaises(CalcError, msg=expression):
                evaluate(expression)

    def test_math_errors_become_calc_errors(self):
        for expression in ("1/0", "log2(0)", "sqrt(-1)", "10**1000"):
            with self.assertRaises(CalcError, msg=expression):
                evaluate(expression)


class ProgramTest(unittest.TestCase):
    """Straight-line programs: one `name = expression` per line (failures: sc-07, pr-p01, pr-p19, pr-p42)."""

    def test_named_steps_feed_later_steps(self):
        steps = run("a = 3*0.2; b = 7*0.1\na / (a + b)")
        self.assertEqual([s.name for s in steps], ["a", "b", ""])
        self.assertAlmostEqual(steps[-1].value, 0.6 / 1.3)
        self.assertEqual(steps[0].text(), "a = 3*0.2 = 0.6")

    def test_vectors_and_matrices(self):
        steps = run("x = [1, 2]; W = [[0.5, -1], [2, 0]]; h = relu(W @ x + [0.1, 0.1]); p = softmax(h); -ln(p[1])")
        self.assertEqual(steps[0].text(), "x = [1, 2]")  # given numbers are shown once, not twice
        self.assertEqual(steps[2].value, [0.0, 2.1])
        self.assertAlmostEqual(steps[-1].value, -math.log(math.exp(2.1) / (1 + math.exp(2.1))))

    def test_helper_functions(self):
        self.assertAlmostEqual(evaluate("dist([1, 1], [4, 5])"), 5.0)
        self.assertAlmostEqual(evaluate("max(1, 5, 3) + mean([1, 2, 3])"), 7.0)
        self.assertAlmostEqual(evaluate("ReLU(-2) + sigmoid(0)"), 0.5)
        self.assertAlmostEqual(evaluate("dot([1, 2], [3, 4]) + norm([3, 4])"), 16.0)

    def test_sum_and_transpose_follow_python(self):
        self.assertEqual(run("M = [[1, 2], [3, 4]]; sum(M)")[-1].value, [4.0, 6.0])  # column totals
        self.assertEqual(run("M = [[1, 2], [3, 4]]; sum(M.T)")[-1].value, [3.0, 7.0])  # row totals
        self.assertAlmostEqual(evaluate("sum(sum([[1, 2], [3, 4]]))"), 10.0)

    def test_print_is_tolerated(self):
        self.assertAlmostEqual(run("x = 2; print(x * 3)")[-1].value, 6.0)

    def test_anything_but_arithmetic_is_rejected_with_a_reason(self):
        for program, reason in (("for i in [1]: x = i", "迴圈"), ("if 1: x = 2", "if"), ("import os", "import"),
                                ("x = y + 1", "y 還沒定義"), ("log = 3", "換一個名稱"), ("a, b = 1, 2", "一個名稱"),
                                ("x = 1 < 2", "比大小"), ("softmax(v=[1])", "照順序"), ("x = [1]; x.real", "Attribute"),
                                ("'abc'", "文字"), ("relu", "relu(…)"), ("x = 2; y = x if x > 0 else 0", "relu(x)"),
                                ("v = [1, 2]; [exp(a) for a in v]", "整個向量"), ("v = [1, 2]; v[0] = 3", "某一格"),
                                ("P(A) = 0.5", "英文字母")):
            with self.assertRaises(CalcError, msg=program) as caught:
                run(program)
            self.assertIn(reason, str(caught.exception))

    def test_runaway_programs_are_rejected(self):
        for program in ("[" + ",".join(["1"] * 101) + "]", "\n".join(f"a{i} = {i}" for i in range(MAX_STATEMENTS + 1)),
                        "[1, 2] @ [[1, 2, 3]]", "[1, 2][5]", "exp(1000)"):
            with self.assertRaises(CalcError, msg=program[:30]):
                run(program)


if __name__ == "__main__":
    unittest.main()
