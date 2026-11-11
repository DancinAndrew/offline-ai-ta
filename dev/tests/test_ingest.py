"""Tests for note chunking and keyword tokens. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import unittest

from ai_ta import ingest
from ai_ta.retrieve import reciprocal_rank_fusion
from ai_ta.textutil import clean_text, keyword_tokens

NOTE = """---
title: test
note_style: reading-v3
---
# 機器學習 Week6：Classification

> [!abstract] 一分鐘看完
> 這堂課講分類。

## 決策樹

決策樹用問題把資料切開。

### 怎麼決定先問哪個問題？

用資訊增益，見 [[Week6/課程 PPT/2. Classification.pdf#page=25|分類講義 p.25]]。

```python
# 這不是標題
print("entropy")
```

> [!tip] 這節記住
> 資訊增益越大越好。

## 自我檢查

> [!question]- 熵是什麼？
> 不確定性。
"""


class HeadingChunksTest(unittest.TestCase):
    def setUp(self):
        self.chunks = ingest.heading_chunks("Week6/note.md", NOTE, ("自我檢查",))

    def test_frontmatter_is_skipped_and_title_comes_from_h1(self):
        first = self.chunks[0]
        self.assertEqual(first.heading_path, ("機器學習 Week6：Classification",))
        self.assertNotIn("note_style", first.text)

    def test_one_chunk_per_smallest_heading_section(self):
        locations = [c.location for c in self.chunks]
        self.assertEqual(locations, [
            "機器學習 Week6：Classification",
            "機器學習 Week6：Classification > 決策樹",
            "機器學習 Week6：Classification > 決策樹 > 怎麼決定先問哪個問題？",
        ])

    def test_hash_comments_inside_code_fences_are_not_headings(self):
        last = self.chunks[-1]
        self.assertIn("# 這不是標題", last.text)
        self.assertIn("這節記住", last.text)

    def test_excluded_heading_keywords_drop_the_section(self):
        self.assertFalse(any("自我檢查" in c.location for c in self.chunks))

    def test_page_links_are_extracted(self):
        links = self.chunks[-1].page_links
        self.assertEqual(len(links), 1)
        self.assertEqual((links[0].pdf, links[0].page, links[0].label),
                         ("Week6/課程 PPT/2. Classification.pdf", 25, "分類講義 p.25"))

    def test_offsets_point_back_into_the_file(self):
        for c in self.chunks:
            self.assertEqual(NOTE[c.start:c.end], c.text)

    def test_long_sections_are_split_into_parts(self):
        long_note = "# T\n\n## Long\n\n" + "\n\n".join("段落" * 200 for _ in range(10))
        parts = ingest.heading_chunks("x.md", long_note)
        long_parts = [c for c in parts if c.heading_path[-1] == "Long"]
        self.assertGreater(len(long_parts), 1)
        self.assertTrue(all(len(c.text) <= ingest.MAX_SECTION_CHARS for c in long_parts))
        self.assertEqual(len({c.chunk_id for c in long_parts}), len(long_parts))


class FixedChunksTest(unittest.TestCase):
    def test_windows_cover_the_sections_and_map_to_file_offsets(self):
        long_note = "# T\n\n## A\n\n" + "甲" * 2000 + "\n\n## 自我檢查\n\n不要\n\n## B\n\n" + "乙" * 900
        sections = ingest.heading_chunks("x.md", long_note, ("自我檢查",))
        windows = ingest.fixed_chunks("x.md", long_note, sections)
        self.assertGreaterEqual(len(windows), 4)
        self.assertTrue(all(c.chunking == "fixed" for c in windows))
        self.assertFalse(any("不要" in c.text for c in windows))
        self.assertTrue(all(0 <= c.start < c.end <= len(long_note) for c in windows))


class TextTest(unittest.TestCase):
    def test_keyword_tokens_use_cjk_bigrams_and_ascii_words(self):
        self.assertEqual(keyword_tokens("資訊增益 and Gini"), ["資訊", "訊增", "增益", "and", "gini"])

    def test_clean_text_keeps_latex_and_link_labels(self):
        cleaned = clean_text("> [!tip] 這節記住\n> ==$H(S)$== 見 [[a.pdf#page=3|講義 p.3]]")
        self.assertEqual(cleaned, "這節記住\n$H(S)$ 見 講義 p.3")

    def test_reciprocal_rank_fusion_rewards_agreement(self):
        fused = reciprocal_rank_fusion([[(1, 0.9), (2, 0.8)], [(2, 5.0), (3, 4.0)]])
        self.assertEqual(fused[0][0], 2)


if __name__ == "__main__":
    unittest.main()
