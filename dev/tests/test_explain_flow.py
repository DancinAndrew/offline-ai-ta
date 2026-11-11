"""Tests for the explanation-mode helpers that do not need a model. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest

from ai_ta.explain import (REFUSAL, ClaimCheck, ClaimVerdict, calc_passage, check_citations, render_check,
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
        self.assertEqual([h.chunk.chunk_id for h in hits], ["a", "b", "c", "d"])

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
        passage = calc_passage("-(2/5)*log2(2/5) - (3/5)*log2(3/5)", 0.9709505944546686)
        self.assertEqual(passage.text, "-(2/5)*log2(2/5) - (3/5)*log2(3/5) = 0.970951")
        self.assertEqual(passage.location, "程式計算結果")


if __name__ == "__main__":
    unittest.main()
