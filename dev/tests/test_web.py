"""Tests for the web page's offline settings and links, without starting a server. Run from the repo root:

    PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
"""

import os
import unittest
from urllib.parse import unquote

from ai_ta import config, web
from ai_ta.ingest import Chunk, PageLink


class FakeRetriever:
    def __init__(self, chunks):
        self.chunks = dict(enumerate(chunks))


def chunk(*links: PageLink) -> Chunk:
    return Chunk("a", "heading", "note.md", ("Note", "a"), 2, 1, 0, 10, "text", links)


class WebTest(unittest.TestCase):
    def test_analytics_and_the_version_check_are_off(self):
        self.assertEqual(os.environ.get("GRADIO_ANALYTICS_ENABLED"), "False")

    def test_message_text_unwraps_gradio_message_parts(self):
        # What Gradio 6's Chatbot hands back for a typed 「放棄」.
        self.assertEqual(web.message_text([{"text": "放棄", "type": "text"}]), "放棄")
        self.assertEqual(web.message_text("放棄"), "放棄")
        self.assertEqual(web.message_text({"text": "提示", "type": "text"}), "提示")
        self.assertEqual(web.message_text([{"text": "a", "type": "text"}, {"path": "x.png", "type": "file"},
                                           {"text": "b", "type": "text"}]), "ab")

    def test_a_slide_link_opens_the_pdf_page(self):
        url = web.page_url(PageLink("Week5、6/課程PPT/1. Classification.pdf", 21, "分類講義 p.21"))
        self.assertTrue(url.startswith("/gradio_api/file="))
        self.assertTrue(url.endswith("#page=21"))
        self.assertEqual(unquote(url[len("/gradio_api/file="):-len("#page=21")]),
                         str(config.VAULT_ROOT / "Week5、6/課程PPT/1. Classification.pdf"))

    def test_only_the_slide_folders_are_served(self):
        retriever = FakeRetriever([chunk(PageLink("Week1/a.pdf", 1, "p.1"), PageLink("Week1/b.pdf", 2, "p.2")),
                                   chunk(PageLink("Week5、6/課程PPT/c.pdf", 3, "p.3"))])
        self.assertEqual(web.slide_folders(retriever),
                         sorted([str(config.VAULT_ROOT / "Week1"), str(config.VAULT_ROOT / "Week5、6/課程PPT")]))

    def test_the_page_builds_without_starting_a_server(self):
        demo = web.build(FakeRetriever([chunk()]))
        self.assertEqual(demo.title, "AI TA 複習")


if __name__ == "__main__":
    unittest.main()
