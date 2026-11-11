"""Evaluation helpers: load the question sets and score retrieval against gold sections."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from . import config, index
from .retrieve import Retriever

BASELINE_SET = config.EVAL_DIR / "midterm-baseline.jsonl"
BASELINE_ANSWERS = config.EVAL_DIR / "private" / "baseline-answers.jsonl"
RUNS_DIR = config.EVAL_DIR / "runs"


def git_version() -> str:
    """Short commit of the harness and code, with '-dirty' when there are uncommitted changes."""
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(config.REPO_ROOT), *args], capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    return commit + ("-dirty" if git("status", "--porcelain", "dev/") else "")


def run_path(kind: str, suffix: str = ".jsonl") -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return RUNS_DIR / f"{datetime.now():%Y-%m-%d-%H%M}-{kind}{suffix}"


def load_baseline_answers(path: Path = BASELINE_ANSWERS) -> dict[str, str]:
    """Answers the untuned model gave in the Ollama App, kept locally (dev/eval/private/)."""
    if not path.exists():
        return {}
    return {row["id"]: row["answer"] for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())}


def load_items(path: Path = BASELINE_SET) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def score_retrieval(conn: sqlite3.Connection, items: list[dict[str, Any]], *, chunking: str, method: str,
                    model: str, k: int = 5) -> RetrievalScore:
    retriever = Retriever(conn, chunking=chunking, model=model)
    spans = _gold_spans(conn)
    by_id = {item["id"]: item for item in items}
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
