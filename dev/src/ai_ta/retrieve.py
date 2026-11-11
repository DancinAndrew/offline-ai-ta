"""Vector, keyword, and hybrid retrieval over the chunk index."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import numpy as np

from . import config, index, llm
from .ingest import Chunk
from .textutil import keyword_tokens

RRF_K = 60  # standard constant for reciprocal rank fusion


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Retriever:
    def __init__(self, conn: sqlite3.Connection, *, chunking: str = "heading",
                 model: str = config.EMBEDDING_MODEL) -> None:
        self.conn = conn
        self.chunking = chunking
        self.model = model
        self.chunks = index.load_chunks(conn, chunking)
        self._ids: list[int] | None = None
        self._matrix: np.ndarray | None = None

    def _vectors(self) -> tuple[list[int], np.ndarray]:
        if self._matrix is None:
            self._ids, self._matrix = index.load_matrix(self.conn, self.model, self.chunking)
        return self._ids, self._matrix

    def vector(self, query: str, k: int) -> list[tuple[int, float]]:
        ids, matrix = self._vectors()
        q = np.asarray(llm.embed([index.query_text(self.model, query)], self.model)[0], dtype=np.float32)
        scores = matrix @ (q / np.linalg.norm(q))
        order = np.argsort(-scores)[:k]
        return [(ids[i], float(scores[i])) for i in order]

    def keyword(self, query: str, k: int) -> list[tuple[int, float]]:
        tokens = sorted(set(keyword_tokens(query)))
        if not tokens:
            return []
        match = " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens)
        rows = self.conn.execute(
            "SELECT f.rowid, bm25(chunks_fts) AS s FROM chunks_fts f JOIN chunks c ON c.id = f.rowid"
            " WHERE chunks_fts MATCH ? AND c.chunking = ? ORDER BY s LIMIT ?",
            (match, self.chunking, k)).fetchall()
        return [(row[0], -row[1]) for row in rows]  # bm25() is lower-is-better

    def search(self, query: str, k: int = 5, method: str = config.RETRIEVAL_METHOD, pool: int = 30) -> list[Hit]:
        if method == "vector":
            ranked = self.vector(query, k)
        elif method == "keyword":
            ranked = self.keyword(query, k)
        elif method == "hybrid":
            ranked = reciprocal_rank_fusion([self.vector(query, pool), self.keyword(query, pool)])[:k]
        else:
            raise ValueError(f"unknown retrieval method {method!r}")
        return [Hit(self.chunks[cid], score) for cid, score in ranked]


def reciprocal_rank_fusion(rankings: list[list[tuple[int, float]]]) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, (cid, _) in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores.items(), key=lambda item: -item[1])
