"""Evaluation helpers: load the question sets and score retrieval against gold sections."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from . import config, index
from .retrieve import Retriever

PRIVATE_DIR = config.EVAL_DIR / "private"  # git-ignored
# Question sets (decision 0006). practice holds past exam questions, so it stays local and may be missing.
EVAL_SETS = {
    "midterm-baseline": config.EVAL_DIR / "midterm-baseline.jsonl",
    "self-check": config.EVAL_DIR / "self-check.jsonl",
    "traps": config.EVAL_DIR / "traps.jsonl",
    "practice": PRIVATE_DIR / "practice.jsonl",
}
SPLITS = ("dev", "test", "all")
BASELINE_ANSWERS = PRIVATE_DIR / "baseline-answers.jsonl"
RUNS_DIR = config.EVAL_DIR / "runs"


def git_version() -> str:
    """Short commit of the harness and code, with '-dirty' when there are uncommitted changes."""
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(config.REPO_ROOT), *args], capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    # Run outputs do not count as changes to the harness or code.
    dirty = git("status", "--porcelain", "--", "dev", ":(exclude)dev/eval/runs", ":(exclude)dev/eval/private")
    return commit + ("-dirty" if dirty else "")


def run_path(kind: str, suffix: str = ".jsonl") -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return RUNS_DIR / f"{datetime.now():%Y-%m-%d-%H%M}-{kind}{suffix}"


def load_baseline_answers(path: Path = BASELINE_ANSWERS) -> dict[str, str]:
    """Answers the untuned model gave in the Ollama App, kept locally (dev/eval/private/)."""
    if not path.exists():
        return {}
    return {row["id"]: row["answer"] for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())}


def load_set(name: str) -> list[dict[str, Any]]:
    """One question set; empty when its file is missing (practice on a fresh clone)."""
    path = EVAL_SETS[name]
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_private(item: dict[str, Any]) -> bool:
    """Answers to private questions restate them (past exam numbers), so their run records stay local too."""
    return PRIVATE_DIR in EVAL_SETS[item["set"]].parents


def load_items(sets: Iterable[str] = tuple(EVAL_SETS), split: str = "dev") -> list[dict[str, Any]]:
    """Questions of the given sets in one split. Development uses dev; test waits for step 7 (decision 0006)."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, not {split!r}")
    items = [item for name in sets for item in load_set(name)]
    return [item for item in items if split == "all" or item["split"] == split]


def question_text(item: dict[str, Any]) -> str:
    """The intended question: the restored version when formulas were lost."""
    return item.get("question_restored") or item["question_as_asked"]


def retrieval_query(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> str:
    """Follow-up questions are retrieved together with the questions they follow."""
    parts = [question_text(item)]
    parent = item.get("follow_up_of")
    while parent:
        parts.insert(0, question_text(by_id[parent]))
        parent = by_id[parent].get("follow_up_of")
    return "\n".join(parts)


@dataclass(frozen=True)
class RetrievalScore:
    chunking: str
    method: str
    model: str
    recall_at_k: float   # share of questions with at least one gold section in the top k
    mrr: float           # mean reciprocal rank of the first gold hit within the top k
    misses: tuple[str, ...]


def _gold_spans(conn: sqlite3.Connection) -> dict[str, tuple[str, int, int]]:
    return {c.chunk_id: (c.file, c.start, c.end) for c in index.load_chunks(conn, "heading").values()}


def missing_gold(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Gold sections that are no longer in the index, for example after a note heading was renamed."""
    known = _gold_spans(conn)
    missing = {item["id"]: [g for g in item["gold_sections"] if g not in known] for item in items}
    return {item_id: gold for item_id, gold in missing.items() if gold}


def score_retrieval(conn: sqlite3.Connection, items: list[dict[str, Any]], *, chunking: str, method: str,
                    model: str, k: int = 5, by_id: dict[str, dict[str, Any]] | None = None) -> RetrievalScore:
    """by_id must hold the turns that follow-up questions follow, when they are not among items."""
    retriever = Retriever(conn, chunking=chunking, model=model)
    spans = _gold_spans(conn)
    by_id = by_id or {item["id"]: item for item in items}
    hits, reciprocal, misses = 0, 0.0, []
    for item in items:
        gold = [spans[g] for g in item["gold_sections"]]
        results = retriever.search(retrieval_query(item, by_id), k=k, method=method)
        rank = next((r for r, hit in enumerate(results, start=1) if _matches(hit.chunk, item, gold)), None)
        if rank:
            hits += 1
            reciprocal += 1 / rank
        else:
            misses.append(item["id"])
    n = len(items)
    return RetrievalScore(chunking, method, model, hits / n, reciprocal / n, tuple(misses))


def _matches(chunk, item: dict[str, Any], gold: list[tuple[str, int, int]]) -> bool:
    if chunk.chunking == "heading":
        return chunk.chunk_id in item["gold_sections"]
    # A fixed window counts when it overlaps a gold section by a meaningful amount.
    return any(chunk.file == f and min(chunk.end, b) - max(chunk.start, a) >= 100 for f, a, b in gold)
