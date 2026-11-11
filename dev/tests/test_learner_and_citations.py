"""Tests for the learner model, citation checks, and give-up detection. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_ta import learner
from ai_ta.explain import check_citations
from ai_ta.practice import bloom_for, is_give_up


def event(point: str, label: str, minutes: int) -> learner.Event:
    time = (datetime(2026, 11, 11, tzinfo=timezone.utc) + timedelta(minutes=minutes)).isoformat()
    return learner.Event(point, point, "理解", "q", "a", label, time=time)


class LearnerTest(unittest.TestCase):
    def test_replaying_the_log_is_deterministic(self):
        events = [event("p1", "正確", 0), event("p1", "正確", 30), event("p2", "矛盾", 5)]
        first, second = learner.derive_state(events), learner.derive_state(list(reversed(events)))
        self.assertEqual(first["p1"].due, second["p1"].due)
        self.assertEqual(first["p1"].attempts, 2)

    def test_mastery_weights_recent_attempts_more(self):
        improving = learner.derive_state([event("p", "矛盾", 0), event("p", "正確", 10)])["p"]
        declining = learner.derive_state([event("p", "正確", 0), event("p", "矛盾", 10)])["p"]
        self.assertGreater(improving.mastery, declining.mastery)

    def test_weak_points_need_repeated_low_scores(self):
        states = learner.derive_state([event("a", "矛盾", 0), event("a", "不知道", 10), event("b", "矛盾", 0)])
        self.assertEqual([s.knowledge_point for s in learner.weak_points(states)], ["a"])

    def test_wrong_answers_come_back_sooner_than_right_ones(self):
        states = learner.derive_state([event("right", "正確", 0), event("wrong", "矛盾", 0)])
        self.assertLess(states["wrong"].due, states["right"].due)

    def test_events_round_trip_through_the_log_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            learner.record(event("p", "正確", 0), path)
            self.assertEqual(learner.load_events(path)[0].label, "正確")


class CitationTest(unittest.TestCase):
    def test_valid_citations(self):
        check = check_citations("熵是 0.971 [1]。增益最大 [2][3]。", passage_count=4)
        self.assertEqual(check.cited, (1, 2, 3))
        self.assertTrue(check.ok)

    def test_out_of_range_citation_is_invalid(self):
        self.assertFalse(check_citations("見 [5]。", passage_count=4).ok)

    def test_answer_without_citations_needs_an_explicit_refusal(self):
        self.assertFalse(check_citations("熵是 0.971。", passage_count=4).ok)
        self.assertTrue(check_citations("筆記裡沒有提到這個。", passage_count=4).ok)


class PracticeHelpersTest(unittest.TestCase):
    def test_give_up_detection(self):
        self.assertTrue(is_give_up("我不知道"))
        self.assertTrue(is_give_up("   "))
        self.assertFalse(is_give_up("熵越大越混"))

    def test_bloom_levels_rotate(self):
        self.assertEqual([bloom_for(n) for n in range(4)], ["理解", "應用", "分析", "理解"])


if __name__ == "__main__":
    unittest.main()
