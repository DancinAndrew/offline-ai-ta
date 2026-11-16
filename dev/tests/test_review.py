"""Tests for the review session with fake model calls. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_ta import explain, learner, llm, practice, review
from ai_ta.ingest import Chunk
from ai_ta.retrieve import Hit

LONG = "決策樹的內容。" * 40


def chunk(name: str, text: str = LONG) -> Chunk:
    return Chunk(name, "heading", "note.md", ("Note", name), 2, 1, 0, 10, text, ())


class FakeRetriever:
    def __init__(self, names: list[str]):
        self.chunks = {i: chunk(name) for i, name in enumerate(names)}

    def search(self, query: str, k: int = 5, **kwargs) -> list[Hit]:
        return [Hit(c, 1.0) for c in self.chunks.values()][:k]


QUIZ = practice.QuizItem(bloom_level="理解", question="決策樹怎麼挑特徵？", reference_points=["挑增益最大的", "每個節點各自挑"],
                         hint="想想資訊增益")


def fake_grade(chunk, quiz, answer):
    if practice.is_give_up(answer):
        return practice.grade(chunk, quiz, answer)   # no model call for giving up
    label = "正確" if "增益" in answer else "矛盾"
    return practice.Grade(label=label, correct_parts=[], wrong_parts=[], feedback="回饋。")


def fake_explain(question, retriever, **kwargs):
    passages = [hit.chunk for hit in retriever.search(question, k=4)]
    return explain.ExplainResult(question, "說明 [1]。", passages, [], explain.check_citations("說明 [1]。", len(passages)),
                                 0, 0.0, 0.0)


def fake_classify(text, pending):
    if text.strip() in review.COMMANDS:
        return review.Intent(action=review.COMMANDS[text.strip()])
    if text.endswith("？"):
        return review.Intent(action="ask")
    return review.Intent(action="answer" if pending else "ask")


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.events = Path(self.tmp.name) / "events.jsonl"
        self.explained: list[str] = []

        def explain_and_note(question, retriever, **kwargs):
            self.explained.append(retriever.search(question, k=4)[0].chunk.chunk_id)
            return fake_explain(question, retriever, **kwargs)

        services = review.Services(classify=fake_classify, make_question=lambda c, b: QUIZ, grade=fake_grade,
                                   answer_question=explain_and_note)
        self.session = review.ReviewSession(FakeRetriever(["a", "b"]), events=self.events, services=services)

    def tearDown(self):
        self.tmp.cleanup()

    def test_opening_without_history_says_how_to_start(self):
        self.assertIn("還沒有練習紀錄", self.session.opening().markdown)

    def test_an_answer_is_graded_and_recorded_once(self):
        [question] = self.session.handle("開始")
        self.assertEqual(question.kind, "question")
        pending_id = self.session.pending.id
        [graded] = self.session.handle("挑增益最大的特徵")
        self.assertEqual(graded.kind, "grade")
        self.assertIn("**正確**", graded.markdown)
        self.assertEqual(len(learner.load_events(self.events)), 1)
        # The same submission again (a double click) records nothing.
        self.assertEqual(self.session.answer("挑增益最大的特徵", pending_id)[0].kind, "note")
        self.assertEqual(len(learner.load_events(self.events)), 1)

    def test_the_hint_is_given_once(self):
        self.session.handle("開始")
        self.assertEqual(self.session.handle("提示")[0].markdown, "提示：想想資訊增益")
        self.assertIn("只有一個", self.session.handle("提示")[0].markdown)

    def test_giving_up_records_dont_know(self):
        self.session.handle("開始")
        self.assertIn("**不知道**", self.session.handle("放棄")[0].markdown)
        self.assertEqual(learner.load_events(self.events)[0].label, "不知道")

    def test_a_weak_point_is_explained_another_way_once_then_rechecked(self):
        self.session.handle("開始")
        point = self.session.pending.chunk.chunk_id
        self.assertEqual([r.kind for r in self.session.handle("隨便猜")], ["grade"])   # one miss: not weak yet
        self.session.next_question(chunk=self.session.retriever.chunks[0 if point == "a" else 1])
        kinds = [r.kind for r in self.session.handle("又猜錯")]
        self.assertEqual(kinds, ["grade", "reexplain", "question"])
        self.assertEqual(self.explained, [point])     # the missed section is pinned first
        self.assertTrue(self.session.pending.recheck)
        self.assertEqual([r.kind for r in self.session.handle("還是錯")], ["grade"])   # not again this session

    def test_a_question_during_a_quiz_keeps_the_quiz_waiting(self):
        self.session.handle("開始")
        pending = self.session.pending
        replies = self.session.handle("Gini 是什麼？")
        self.assertEqual([r.kind for r in replies], ["answer", "note"])
        self.assertIn("**出處**", replies[0].markdown)
        self.assertIs(self.session.pending, pending)

    def test_progress_lists_practised_points(self):
        self.session.handle("開始")
        self.session.handle("挑增益最大的特徵")
        self.assertIn("| Note > ", self.session.handle("進度")[0].markdown)


class ClassifyTest(unittest.TestCase):
    def test_commands_and_short_give_ups_need_no_model(self):
        pending = review.Pending(chunk("a"), QUIZ)
        with patch.object(llm, "structured", side_effect=AssertionError("no model call expected")):
            self.assertEqual(review.classify("提示", pending).action, "hint")
            self.assertEqual(review.classify("我不會", pending).action, "give_up")
            self.assertEqual(review.classify("開始", None).action, "quiz")

    def test_answer_actions_without_a_question_become_questions(self):
        with patch.object(llm, "structured", return_value=(review.Intent(action="answer"), 0.1)):
            self.assertEqual(review.classify("決策樹怎麼切", None).action, "ask")

    def test_a_failed_classification_falls_back(self):
        failed = llm.StructuredOutputError("intent: invalid")
        with patch.object(llm, "structured", side_effect=failed):
            self.assertEqual(review.classify("挑增益最大的", review.Pending(chunk("a"), QUIZ)).action, "answer")
            self.assertEqual(review.classify("什麼是 Gini", None).action, "ask")


class GiveUpTest(unittest.TestCase):
    def test_only_short_answers_count_as_giving_up(self):
        for text in ("", "不知道", "我不會。", "放棄吧", "PASS"):
            self.assertTrue(practice.is_give_up(text), text)
        for text in ("這樣不會過擬合，因為有剪枝", "不知道對不對，但我覺得是挑增益最大的特徵"):
            self.assertFalse(practice.is_give_up(text), text)


class PinnedRetrieverTest(unittest.TestCase):
    def test_the_pinned_section_comes_first_once(self):
        base = FakeRetriever(["a", "b", "c"])
        pinned = review.PinnedRetriever(base, base.chunks[1])
        self.assertEqual([h.chunk.chunk_id for h in pinned.search("q", k=3)], ["b", "a", "c"])


if __name__ == "__main__":
    unittest.main()
