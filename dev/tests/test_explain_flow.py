"""Tests for the explanation-mode helpers that do not need a model. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest
from unittest.mock import patch

from ai_ta import calc, explain, llm
from ai_ta.explain import (CALC_HEADER, MAX_CHECK_PASSAGES, PARTIAL_NOTE, REFUSAL, TRUNCATED, ClaimCheck, ClaimVerdict,
                           answer_prompt, calc_passage, calc_problems, check_citations, compute, render_check,
                           retrieve_for_claims)
from ai_ta.ingest import Chunk
from ai_ta.retrieve import Hit


def chunk(name: str) -> Chunk:
    return Chunk(name, "heading", "note.md", ("Note", name), 2, 1, 0, 10, name, ())


class FakeRetriever:
    """Returns fixed results per query so retrieval merging can be tested without embeddings."""

    def __init__(self, results: dict[str, list[str]]):
        self.results = results

    def search(self, query: str, k: int = 5) -> list[Hit]:
        return [Hit(chunk(name), 1.0) for name in self.results.get(query, [])][:k]


class CheckFlowTest(unittest.TestCase):
    def test_claims_get_their_own_passages_without_duplicates(self):
        retriever = FakeRetriever({"q": ["a", "b"], "claim 1": ["b", "c"], "claim 2": ["d", "a"]})
        hits = retrieve_for_claims(retriever, "q", ["claim 1", "claim 2"], k=4)
        self.assertEqual([h.chunk.chunk_id for h in hits], ["b", "d", "a", "c"])

    def test_the_question_cannot_crowd_out_the_claims(self):
        retriever = FakeRetriever({"q": ["q1", "q2", "q3", "q4"],
                                   **{f"claim {n}": [f"c{n}a", f"c{n}b"] for n in range(1, 5)}})
        hits = [h.chunk.chunk_id for h in retrieve_for_claims(retriever, "q", [f"claim {n}" for n in range(1, 5)], k=4)]
        self.assertEqual(len(hits), MAX_CHECK_PASSAGES)
        self.assertTrue(all(f"c{n}a" in hits for n in range(1, 5)))  # every claim keeps its best passage
        self.assertEqual(hits[4:], ["q1", "q2"])

    def test_rendered_check_lists_every_verdict_and_passes_the_citation_check(self):
        judged = ClaimCheck(summary="三點對，一點要改。", claims=[
            ClaimVerdict(claim="P(A) 是先驗", verdict="正確", evidence=[1]),
            ClaimVerdict(claim="P(B) 是新的條件", verdict="需要修正", evidence=[2], correction="P(B) 是證據機率"),
            ClaimVerdict(claim="和 KNN 一樣", verdict="筆記沒寫"),
            ClaimVerdict(claim="引用不存在的段落", verdict="正確", evidence=[9]),
        ])
        text = render_check(judged, passage_count=4)
        self.assertIn("- 對：P(A) 是先驗 [1]", text)
        self.assertIn("- 需要修正：P(B) 是新的條件 → P(B) 是證據機率 [2]", text)
        self.assertIn(f"- {REFUSAL}：和 KNN 一樣", text)
        self.assertNotIn("[9]", text)
        self.assertTrue(check_citations(text, 4).ok)

    def test_calc_passage_shows_the_expression_and_value(self):
        passage = calc_passage(calc.run("-(2/5)*log2(2/5) - (3/5)*log2(3/5)"))
        self.assertEqual(passage.text.splitlines(), [CALC_HEADER, "-(2/5)*log2(2/5) - (3/5)*log2(3/5) = 0.970951"])
        self.assertEqual(passage.location, "程式計算結果")

    def test_calc_passage_lists_every_step_with_its_numbers_filled_in(self):
        passage = calc_passage(calc.run("a = 0.3 * 0.5; b = 0.7 * 0.2; a / (a + b)"))
        self.assertEqual(passage.text.splitlines()[1:], ["a = 0.3 * 0.5 = 0.15", "b = 0.7 * 0.2 = 0.14",
                                                         "a / (a + b) = 0.15 / (0.15 + 0.14) = 0.517241"])


class FakeWriter:
    """Returns prepared programs in order and keeps the messages it was sent."""

    def __init__(self, *programs: tuple[str, bool]):
        self.programs = list(programs)
        self.sent: list[list[dict[str, str]]] = []

    def __call__(self, messages):
        self.sent.append(list(messages))
        program, truncated = self.programs.pop(0)
        return program, 2.0, truncated


class ComputeTest(unittest.TestCase):
    def test_a_valid_program_runs_without_a_rewrite(self):
        writer = FakeWriter(("a = 2\na * 3", False))
        result = compute("q", [chunk("formula")], write=writer)
        self.assertEqual((result.value, result.rewrites, result.error, result.seconds), (6.0, 0, None, 2.0))
        self.assertIn("formula", writer.sent[0][1]["content"])  # the notes are in view when writing

    def test_a_fixable_error_goes_back_once_with_the_error(self):
        writer = FakeWriter(("y * 3", False), ("y = 2; y * 3", False))
        result = compute("q", [], write=writer)
        self.assertIn("y 還沒定義", writer.sent[1][-1]["content"])
        self.assertEqual(writer.sent[1][-2], {"role": "assistant", "content": "y * 3"})
        self.assertEqual((result.value, result.rewrites, result.seconds), (6.0, 1, 4.0))

    def test_loops_decisions_and_cut_off_programs_are_not_rewritten(self):
        for program, truncated, reason in (("for i in [1]: x = i", False, "迴圈"), ("x = 1 if 2 > 1 else 0", False, "if"),
                                           ("a = (1 +", True, TRUNCATED)):
            writer = FakeWriter((program, truncated))
            result = compute("q", [], write=writer)
            self.assertEqual((len(writer.sent), result.rewrites, result.steps), (1, 0, []), program)
            self.assertIn(reason, result.error)

    def test_a_second_failure_is_reported_not_hidden(self):
        result = compute("q", [], write=FakeWriter(("y + 1", False), ("z + 1", False)))
        self.assertEqual((result.steps, result.rewrites), ([], 1))
        self.assertIn("z 還沒定義", result.error)

    def test_a_decision_keeps_the_steps_computed_before_it(self):
        writer = FakeWriter(("x = [1, 2]\nd = dist(x, [1, 1])\ng = 1 if d > 0 else 0", False))
        result = compute("q", [], write=writer)
        self.assertEqual(([s.name for s in result.steps], len(writer.sent)), (["x", "d"], 1))
        self.assertTrue(result.partial)
        self.assertIsNone(result.value)  # the last kept step is not the answer
        self.assertIn("if", result.error)

    def test_steps_that_only_copy_the_question_are_not_kept(self):
        result = compute("q", [], write=FakeWriter(("x = 2\ny = 1 if x > 0 else 0", False)))
        self.assertEqual((result.steps, result.partial), ([], False))

    def test_a_cut_off_program_keeps_its_finished_lines(self):
        result = compute("q", [], write=FakeWriter(("a = 2\nb = a * 3\nc = (b +", True)))
        self.assertEqual(([s.name for s in result.steps], result.error), (["a", "b"], TRUNCATED))
        self.assertTrue(result.partial)

    def test_calc_answers_flag_numbers_the_calculator_never_produced(self):
        passages = [calc_passage(calc.run("prior = 0.45\nf = [0.9, 0.3, 0.4]\nscore = prior * prod(f)\npost = score / 0.0717"))]
        question = "先驗 0.45，會軟的機率 0.9，算後驗。"
        self.assertEqual(calc_problems("分數是 0.0486，後驗約 0.678 [1]。先驗 0.45 [1]。", question, passages), [])
        found = calc_problems("分數是 0.1323，後驗約 0.852 [1]。", question, passages)
        self.assertEqual(len(found), 1)
        self.assertIn("0.1323、0.852", found[0])

    def test_the_first_sentence_must_not_borrow_another_examples_result(self):
        notes = Chunk("notes", "heading", "note.md", ("Note",), 2, 1, 0, 10, "變式的後驗約 0.269755。", ())
        passages = [calc_passage(calc.run("post = 0.054 / 0.152")), notes]
        found = calc_problems("流失後驗約 0.269755 [2]。", "q", passages)
        self.assertEqual(len(found), 1)
        self.assertIn("第一句的 0.269755", found[0])
        # Later sentences may quote the notes.
        self.assertEqual(calc_problems("流失後驗約 0.355 [1]。筆記的變式是 0.269755 [2]。", "q", passages), [])

    def test_a_calculator_result_stands_apart_from_the_notes(self):
        passages = [calc_passage(calc.run("a = 0.3 * 0.5")), chunk("notes")]
        prompt = answer_prompt(passages, "q")
        self.assertTrue(prompt.startswith("這一題的程式計算結果：\n\n[1] 程式計算結果\n"))
        self.assertIn("筆記段落：\n\n[2] Note > notes\nnotes", prompt)
        self.assertTrue(answer_prompt([chunk("notes")], "q").startswith("筆記段落：\n\n[1] "))

    def test_calc_answers_must_not_open_with_a_refusal(self):
        passages = [calc_passage(calc.run("a = 0.3 * 0.5"))]
        for answer in ("根據提供的筆記，無法直接回答此題的計算結果，因為 [1] 不同。", f"{REFUSAL}這兩個機率 [1]。"):
            self.assertIn("無法回答", calc_problems(answer, "q", passages)[0], answer)
        self.assertEqual(calc_problems("結果是 0.15 [1]。筆記沒有說無法計算的情況 [1]。", "q", passages), [])

    def test_a_partial_calc_passage_says_where_it_stopped(self):
        steps = calc.run("a = 2\nb = a * 3")
        self.assertEqual(calc_passage(steps, partial=True).text.splitlines()[-1], PARTIAL_NOTE)
        self.assertNotIn(PARTIAL_NOTE, calc_passage(steps).text)


class AnswerRetryTest(unittest.TestCase):
    """The answer loop with a fake model: how many attempts each kind of problem gets."""

    QUESTION = "0.3 乘以 0.5 是多少？"

    def answer(self, replies: list[str]) -> explain.ExplainResult:
        computed = explain.Calculation("a = 0.3 * 0.5", calc.run("a = 0.3 * 0.5"), None, 0, 1.0)
        queue = list(replies)

        def fake_chat(messages, options=None, purpose=""):
            return llm.ChatResult(queue.pop(0), "", 1.0, 10, 10)

        with patch.object(explain, "route", return_value=(explain.Route(type="calculation"), 0.1)), \
                patch.object(explain, "compute", return_value=computed), \
                patch.object(explain.llm, "chat", side_effect=fake_chat):
            return explain.answer(self.QUESTION, FakeRetriever({self.QUESTION: ["notes"]}))

    def test_a_good_answer_is_kept_at_once(self):
        result = self.answer(["結果是 0.15 [1]。"])
        self.assertEqual((result.retries, result.retry_reasons, result.unresolved), (0, [], []))

    def test_a_made_up_number_gets_up_to_two_retries(self):
        result = self.answer(["結果是 0.21 [1]。", "結果是 0.25 [1]。", "結果是 0.15 [1]。"])
        self.assertEqual((result.answer, result.retries, result.unresolved), ("結果是 0.15 [1]。", 2, []))
        self.assertIn("0.21", result.retry_reasons[0])

    def test_a_problem_left_after_two_retries_is_reported(self):
        result = self.answer(["結果是 0.21 [1]。"] * 3)
        self.assertEqual(result.retries, 2)
        self.assertIn("0.21", result.unresolved[0])

    def test_a_missing_citation_gets_one_retry(self):
        result = self.answer(["結果是 0.15。", "結果是 0.15。", "結果是 0.15 [1]。"])
        self.assertEqual((result.retries, result.retry_reasons), (1, ["citations"]))


if __name__ == "__main__":
    unittest.main()
