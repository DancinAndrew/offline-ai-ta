"""Tests for the safe calculator. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest

from ai_ta.calc import CalcError, evaluate


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


if __name__ == "__main__":
    unittest.main()
