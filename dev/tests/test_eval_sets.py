"""The eval sets stay consistent, and the test split stays held out (decision 0006)."""

import unittest
from pathlib import Path

from ai_ta import cli, evaluate, index
from ai_ta.ingest import Chunk

TYPES = {"concept", "comparison", "check-understanding", "follow-up", "calculation", "formula", "fact"}
LABELS = {"正確", "部分正確", "矛盾", "離題", "不知道"}


class EvalSetTests(unittest.TestCase):
    def setUp(self):
        self.items = evaluate.load_items(split="all")  # practice is skipped when its local file is missing

    def test_every_item_is_complete_and_ids_are_unique(self):
        ids = [item["id"] for item in self.items]
        self.assertEqual(len(ids), len(set(ids)))
        for item in self.items:
            with self.subTest(item=item["id"]):
                self.assertIn(item["split"], ("dev", "test"))
                self.assertIn(item["type"], TYPES)
                self.assertTrue(item["question_as_asked"].strip())
                self.assertTrue(item["gold_sections"])
                self.assertTrue(item["reference_points"])
                if item.get("follow_up_of"):
                    self.assertIn(item["follow_up_of"], ids)

    def test_items_sit_in_the_file_of_their_set(self):
        for name in evaluate.EVAL_SETS:
            for item in evaluate.load_set(name):
                self.assertEqual(item["set"], name, item["id"])

    def test_questions_used_for_tuning_are_never_test(self):
        self.assertTrue(all(item["split"] == "dev" for item in evaluate.load_set("midterm-baseline")))

    def test_other_sets_put_every_third_item_in_dev(self):
        for name in ("self-check", "traps", "practice"):
            for i, item in enumerate(evaluate.load_set(name)):
                self.assertEqual(item["split"], "dev" if i % 3 == 0 else "test", item["id"])

    def test_trap_items_carry_point_by_point_verdicts(self):
        for item in evaluate.load_set("traps"):
            self.assertTrue(item["misconceptions"], item["id"])
            self.assertIn(item["grading_label"], LABELS)

    def test_only_sets_under_private_count_as_private(self):
        self.assertTrue(evaluate.is_private({"set": "practice"}))
        for name in ("midterm-baseline", "self-check", "traps"):
            self.assertFalse(evaluate.is_private({"set": name}))

    def test_loading_defaults_to_dev(self):
        self.assertTrue(all(item["split"] == "dev" for item in evaluate.load_items()))
        self.assertTrue(all(item["split"] == "test" for item in evaluate.load_items(split="test")))
        with self.assertRaises(ValueError):
            evaluate.load_items(split="validation")

    def test_cli_refuses_the_test_split_without_the_flag(self):
        for split in ("test", "all"):
            args = cli.build_parser().parse_args(["eval-retrieval", "--split", split])
            with self.assertRaises(SystemExit):
                cli._eval_items(args)

    def test_gold_sections_missing_from_the_index_are_reported(self):
        conn = index.connect(Path(":memory:"))
        index.rebuild(conn, [Chunk("note.md#A", "heading", "note.md", ("Note", "A"), 2, 1, 0, 10, "text", ())])
        items = [{"id": "q1", "gold_sections": ["note.md#A"]},
                 {"id": "q2", "gold_sections": ["note.md#A", "note.md#Renamed"]}]
        self.assertEqual(evaluate.missing_gold(conn, items), {"q2": ["note.md#Renamed"]})


if __name__ == "__main__":
    unittest.main()
