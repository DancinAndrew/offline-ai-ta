"""Text helpers: Obsidian Markdown cleanup and CJK-aware keyword tokens."""

from __future__ import annotations

import re

PAGE_LINK = re.compile(r"\[\[([^\]|#]+?\.pdf)#page=(\d+)(?:\|([^\]]*))?\]\]")
EMBED = re.compile(r"!\[\[[^\]]*\]\]")
WIKI_LINK = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
CALLOUT_MARK = re.compile(r"\[!\w+\][+-]?\s*")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
QUOTE_PREFIX = re.compile(r"^\s*(?:>\s?)+")

# ASCII words, or runs of CJK ideographs.
TOKEN = re.compile(r"[a-z0-9_]+|[㐀-䶿一-鿿]+")


def clean_text(markdown: str) -> str:
    """Strip Obsidian syntax that adds noise to search; keep LaTeX and wording."""
    text = HTML_COMMENT.sub("", markdown)
    text = EMBED.sub("", text)
    text = PAGE_LINK.sub(lambda m: m.group(3) or f"p.{m.group(2)}", text)
    text = WIKI_LINK.sub(lambda m: m.group(2) or m.group(1).split("/")[-1], text)
    lines = []
    for line in text.splitlines():
        line = QUOTE_PREFIX.sub("", line)
        line = CALLOUT_MARK.sub("", line)
        lines.append(line.replace("==", "").rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def keyword_tokens(text: str) -> list[str]:
    """Lowercased ASCII words plus overlapping CJK bigrams.

    Chinese has no spaces, so a run like 資訊增益 becomes 資訊 訊增 增益; this lets
    two-character terms such as 先驗 or 剪枝 match, which trigram matching cannot.
    """
    tokens: list[str] = []
    for run in TOKEN.findall(text.lower()):
        if run.isascii():
            tokens.append(run)
        elif len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens
