"""Read the course notes in the knowledge manifest and cut them into chunks.

Two chunkings are produced so they can be compared on the eval set:

- ``heading``: one chunk per smallest heading section (H1-H6), long sections split
  at paragraph boundaries. This follows the structure of the notes.
- ``fixed``: windows of about 512 tokens over the same text, ignoring headings.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import config
from .textutil import PAGE_LINK, clean_text

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")

MAX_SECTION_CHARS = 3000   # longer sections are split into parts
PART_TARGET_CHARS = 2500
FIXED_WINDOW_CHARS = 850   # about 512 tokens at 1.66 characters per token
FIXED_STEP_CHARS = 700     # 150 characters of overlap


class ManifestError(ValueError):
    """The knowledge manifest is missing or malformed."""


@dataclass(frozen=True)
class Manifest:
    include: tuple[str, ...]
    exclude_files: tuple[str, ...]
    exclude_heading_keywords: tuple[str, ...]


@dataclass(frozen=True)
class PageLink:
    pdf: str      # vault-relative path of the slide PDF
    page: int
    label: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    chunking: str                 # "heading" or "fixed"
    file: str                     # vault-relative path of the note
    heading_path: tuple[str, ...]  # note title first
    level: int                    # heading level of the section, 0 before any heading
    part: int                     # 1-based part number when a section was split
    start: int                    # character offsets in the note file
    end: int
    text: str                     # raw Markdown with LaTeX kept
    page_links: tuple[PageLink, ...]

    @property
    def location(self) -> str:
        return " > ".join(self.heading_path)

    def embedding_text(self) -> str:
        return f"{self.location}\n{clean_text(self.text)}"


def load_manifest(path: Path = config.KNOWLEDGE_MANIFEST) -> Manifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Manifest(
            include=tuple(data["include"]),
            exclude_files=tuple(data.get("exclude_files", ())),
            exclude_heading_keywords=tuple(data.get("exclude_heading_keywords", ())),
        )
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise ManifestError(f"cannot read knowledge manifest {path}: {exc}") from exc


def source_files(manifest: Manifest, vault_root: Path = config.VAULT_ROOT) -> list[Path]:
    included = {p for pattern in manifest.include for p in vault_root.glob(pattern) if p.is_file()}
    excluded = {p for pattern in manifest.exclude_files for p in vault_root.glob(pattern)}
    return sorted(included - excluded)


def body_start(text: str) -> int:
    """Offset where the note body begins, after YAML frontmatter if present."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return end + len("\n---\n")
    return 0


def page_links(markdown: str) -> tuple[PageLink, ...]:
    return tuple(
        PageLink(pdf=m.group(1), page=int(m.group(2)), label=m.group(3) or f"p.{m.group(2)}")
        for m in PAGE_LINK.finditer(markdown)
    )


def _sections(text: str, default_title: str) -> list[tuple[tuple[str, ...], int, int, int]]:
    """(heading path, level, start, end) for every heading section, code fences respected."""
    sections = []
    title = default_title
    stack: list[tuple[int, str]] = []
    path: tuple[str, ...] = (title,)
    level = 0
    start = offset = body_start(text)
    in_fence = False
    for line in text[offset:].splitlines(keepends=True):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := HEADING.match(line.rstrip("\n"))):
            sections.append((path, level, start, offset))
            level, name = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title, stack = name, []
            else:
                stack = [(lvl, n) for lvl, n in stack if lvl < level] + [(level, name)]
            path = (title,) + tuple(n for _, n in stack)
            start = offset
        offset += len(line)
    sections.append((path, level, start, offset))
    return sections


def _parts(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split a long section at blank lines outside code fences."""
    if end - start <= MAX_SECTION_CHARS:
        return [(start, end)]
    cuts: list[int] = []
    pos, in_fence = start, False
    for line in text[start:end].splitlines(keepends=True):
        if FENCE.match(line):
            in_fence = not in_fence
        pos += len(line)
        if not in_fence and not line.strip():
            cuts.append(pos)
    parts, part_start, last_cut = [], start, start
    for cut in cuts + [end]:
        if cut - part_start > PART_TARGET_CHARS and last_cut > part_start:
            parts.append((part_start, last_cut))
            part_start = last_cut
        last_cut = cut
    parts.append((part_start, end))
    return [(a, b) for a, b in parts if text[a:b].strip()]


def _has_body(raw: str) -> bool:
    lines = raw.splitlines()
    if lines and HEADING.match(lines[0]):
        lines = lines[1:]
    return any(line.strip() for line in lines)


def heading_chunks(rel_path: str, text: str, exclude_keywords: tuple[str, ...] = ()) -> list[Chunk]:
    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    for path, level, start, end in _sections(text, Path(rel_path).stem):
        if any(k in name for name in path[1:] for k in exclude_keywords):
            continue
        if not _has_body(text[start:end]):
            continue
        spans = _parts(text, start, end)
        for part, (a, b) in enumerate(spans, start=1):
            base = f"{rel_path}#{' > '.join(path[1:]) or '（開頭）'}"
            if len(spans) > 1:
                base += f" ({part}/{len(spans)})"
            seen[base] = seen.get(base, 0) + 1
            chunk_id = base if seen[base] == 1 else f"{base} ~{seen[base]}"
            raw = text[a:b]
            chunks.append(Chunk(chunk_id, "heading", rel_path, path, level, part, a, b, raw, page_links(raw)))
    return chunks


def fixed_chunks(rel_path: str, text: str, sections: list[Chunk]) -> list[Chunk]:
    """Fixed windows over the text covered by ``sections`` (same content, no headings)."""
    segments: list[tuple[int, int, int]] = []  # (offset in joined text, file start, file end)
    joined = ""
    for s in sorted(sections, key=lambda c: c.start):
        segments.append((len(joined), s.start, s.end))
        joined += text[s.start : s.end]

    def to_file(pos: int) -> int:
        for joined_start, file_start, file_end in reversed(segments):
            if pos >= joined_start:
                return min(file_start + (pos - joined_start), file_end)
        return segments[0][1]

    def section_at(file_pos: int) -> Chunk:
        for s in sections:
            if s.start <= file_pos < s.end:
                return s
        return sections[-1]

    chunks: list[Chunk] = []
    i = 0
    while segments and i < len(joined):
        window = joined[i : i + FIXED_WINDOW_CHARS]
        if window.strip():
            a, b = to_file(i), to_file(i + len(window) - 1) + 1
            owner = section_at(a)
            chunks.append(Chunk(f"{rel_path}@{a}", "fixed", rel_path, owner.heading_path, owner.level,
                                1, a, b, window, page_links(window)))
        if i + FIXED_WINDOW_CHARS >= len(joined):
            break
        i += FIXED_STEP_CHARS
    return chunks


def load_chunks(manifest: Manifest, vault_root: Path = config.VAULT_ROOT) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in source_files(manifest, vault_root):
        rel_path = path.relative_to(vault_root).as_posix()
        text = path.read_text(encoding="utf-8")
        sections = heading_chunks(rel_path, text, manifest.exclude_heading_keywords)
        chunks.extend(sections)
        if sections:
            chunks.extend(fixed_chunks(rel_path, text, sections))
    return chunks
