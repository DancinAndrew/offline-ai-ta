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

    def test_confusion_matrix_helpers(self):
        steps = run("M = [[4, 1], [2, 3]]; diag(M); rowsum(M); colsum(M); diag(M) / rowsum(M)")
        self.assertEqual([s.value for s in steps[1:4]], [[4.0, 3.0], [5.0, 5.0], [6.0, 4.0]])
        self.assertEqual(steps[-1].value, [0.8, 0.6])  # recall when rows are the true classes
        with self.assertRaises(CalcError) as caught:
            run("diag([1, 2])")
        self.assertIn("矩陣", str(caught.exception))

    def test_bernoulli_uses_one_minus_p_for_every_no(self):
        steps = run("x = [1, 0]; p = [0.6, 0.2]; f = bernoulli(x, p); prod(f)")
        self.assertEqual(steps[2].text(), "f = bernoulli(x, p) = bernoulli([1, 0], [0.6, 0.2]) = [0.6, 0.8]")
        self.assertAlmostEqual(steps[-1].value, 0.6 * 0.8)
        self.assertAlmostEqual(evaluate("prod(bernoulli([0, 0], [0.8, 0.3]))"), 0.2 * 0.7)

    def test_bernoulli_rejects_mismatched_or_invalid_input(self):
        for program, reason in (("x = [0, 0]; bernoulli(x, 0.8)", "一樣長"), ("bernoulli([1, 2], [0.5, 0.5])", "1（是）"),
                                ("bernoulli([1, 0], [0.5, 1.5])", "0 到 1")):
            with self.assertRaises(CalcError, msg=program) as caught:
                run(program)
            self.assertIn(reason, str(caught.exception))
            self.assertTrue(caught.exception.rewritable)

    def test_a_name_may_match_a_function(self):
        steps = run("M = [[1, 2], [3, 4]]\ndiag = diag(M)\nlog = 3\nsum(diag) + log + log2(diag(M)[1])")
        self.assertEqual(steps[1].text(), "diag = diag(M) = [1, 4]")
        self.assertAlmostEqual(steps[-1].value, 5 + 3 + 2)

    def test_earlier_values_are_filled_into_each_step(self):
        steps = run("prior = 0.45\nf = [0.9, 0.3, 0.4]\nscore = prior * prod(f)")
        self.assertEqual(steps[-1].text(), "score = prior * prod(f) = 0.45 * prod([0.9, 0.3, 0.4]) = 0.0486")
        self.assertEqual(run("a = -2\nb = a ** 2")[-1].text(), "b = a ** 2 = (-2) ** 2 = 4")
        self.assertEqual(run("v = [10, 8, 7]\nv[0] / sum(v)")[-1].text(), "v[0] / sum(v) = 10 / sum([10, 8, 7]) = 0.4")

    def test_long_vectors_matrices_and_plain_copies_are_not_filled(self):
        self.assertEqual(run("v = [1, 2, 3, 4, 5]\ns = sum(v)")[-1].text(), "s = sum(v) = 15")
        self.assertEqual(run("M = [[1, 2], [3, 4]]\nt = rowsum(M)")[-1].text(), "t = rowsum(M) = [3, 7]")
        self.assertEqual(run("a = 2\nb = a")[-1].text(), "b = a = 2")

    def test_dist_gives_one_distance_per_row(self):
        self.assertEqual(run("X = [[0, 2], [3, 1]]; dist(X, [0, 1])")[-1].value, [1.0, 3.0])
        self.assertAlmostEqual(evaluate("dist(3, 5)"), 2.0)

    def test_a_failure_keeps_the_lines_that_ran_before_it(self):
        with self.assertRaises(CalcError) as caught:
            run("a = 2\nb = a * 3\nc = b if b > 1 else 0")
        self.assertEqual([s.name for s in caught.exception.steps], ["a", "b"])
        with self.assertRaises(CalcError) as caught:
            run("a = 2\nb = a / 0")
        self.assertEqual([s.name for s in caught.exception.steps], ["a"])

    def test_rows_columns_and_ranges(self):
        self.assertEqual(run("M = [[1, 2], [3, 4]]; M[:, 0]")[-1].value, [1.0, 3.0])
        self.assertEqual(run("M = [[1, 2], [3, 4]]; M[1, :]")[-1].value, [3.0, 4.0])
        self.assertEqual(run("v = [1, 2, 3, 4]; v[1:3]")[-1].value, [2.0, 3.0])

    def test_print_is_tolerated(self):
        self.assertAlmostEqual(run("x = 2; print(x * 3)")[-1].value, 6.0)

    def test_anything_but_arithmetic_is_rejected_with_a_reason(self):
        for program, reason in (("for i in [1]: x = i", "迴圈"), ("if 1: x = 2", "if"), ("import os", "import"),
                                ("x = y + 1", "y 還沒定義"), ("a, b = 1, 2", "一個名稱"),
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
