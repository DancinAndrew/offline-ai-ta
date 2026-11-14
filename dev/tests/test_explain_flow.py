"""Tests for the explanation-mode helpers that do not need a model. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest

from ai_ta import calc
from ai_ta.explain import (MAX_CHECK_PASSAGES, REFUSAL, TRUNCATED, ClaimCheck, ClaimVerdict, calc_passage,
                           check_citations, compute, render_check, retrieve_for_claims)
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
        self.assertEqual(passage.text, "-(2/5)*log2(2/5) - (3/5)*log2(3/5) = 0.970951")
        self.assertEqual(passage.location, "程式計算結果")

    def test_calc_passage_lists_every_step(self):
        passage = calc_passage(calc.run("a = 0.3 * 0.5; b = 0.7 * 0.2; a / (a + b)"))
        self.assertEqual(passage.text.splitlines(), ["a = 0.3 * 0.5 = 0.15", "b = 0.7 * 0.2 = 0.14",
                                                     "a / (a + b) = 0.517241"])


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


if __name__ == "__main__":
    unittest.main()
