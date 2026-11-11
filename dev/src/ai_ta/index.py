"""SQLite store for chunks, a CJK-bigram keyword index, and embeddings.

Vectors are cached by a hash of the text they embed, so rebuilding the index after a
note or manifest change only embeds chunks whose text actually changed.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

import numpy as np

from . import config, llm
from .ingest import Chunk, PageLink
from .textutil import keyword_tokens

CHUNK_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT UNIQUE NOT NULL,
    chunking TEXT NOT NULL,
    file TEXT NOT NULL,
    heading_path TEXT NOT NULL,
    level INTEGER NOT NULL,
    part INTEGER NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    text TEXT NOT NULL,
    page_links TEXT NOT NULL,
    embed_key TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(tokens, tokenize = 'unicode61');
"""
VECTOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS vectors (
    embed_key TEXT NOT NULL,
    model TEXT NOT NULL,
    vector BLOB NOT NULL,
    PRIMARY KEY (embed_key, model)
);
"""

# Prompt formats the embedding models were trained with. Models not listed embed raw text.
QUERY_TEMPLATES = {
    "qwen3-embedding:0.6b": (
        "Instruct: Given a student's question about machine learning course notes, "
        "retrieve the note section that answers it\nQuery: {query}"
    ),
    "embeddinggemma-2:270m": "task: search result | query: {query}",
}
DOCUMENT_TEMPLATES = {
    "embeddinggemma-2:270m": "title: {title} | text: {text}",
}


def embed_key(chunk: Chunk) -> str:
    return hashlib.sha1(chunk.embedding_text().encode("utf-8")).hexdigest()


def connect(path: Path = config.INDEX_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(VECTOR_SCHEMA)
    _migrate_v1(conn)
    conn.executescript(CHUNK_SCHEMA)
    return conn


def _migrate_v1(conn: sqlite3.Connection) -> None:
    """Move vectors from the first schema (keyed by chunk row id) into the text-keyed cache."""
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "embeddings" not in tables:
        return
    rows = conn.execute(
        "SELECT c.chunk_id, c.chunking, c.file, c.heading_path, c.level, c.part, c.start_offset, c.end_offset,"
        " c.text, c.page_links, e.model, e.vector FROM embeddings e JOIN chunks c ON c.id = e.chunk").fetchall()
    for r in rows:
        chunk = Chunk(r[0], r[1], r[2], tuple(json.loads(r[3])), r[4], r[5], r[6], r[7], r[8], ())
        conn.execute("INSERT OR IGNORE INTO vectors (embed_key, model, vector) VALUES (?, ?, ?)",
                     (embed_key(chunk), r[10], r[11]))
    conn.executescript("DROP TABLE embeddings; DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS chunks_fts;")
    conn.commit()


def rebuild(conn: sqlite3.Connection, chunks: Iterable[Chunk]) -> int:
    """Replace all chunks and keyword tokens. Cached vectors are kept and reused by text."""
    conn.executescript("DELETE FROM chunks_fts; DELETE FROM chunks;")
    count = 0
    for chunk in chunks:
        cur = conn.execute(
            "INSERT INTO chunks (chunk_id, chunking, file, heading_path, level, part, start_offset,"
            " end_offset, text, page_links, embed_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chunk.chunk_id, chunk.chunking, chunk.file, json.dumps(chunk.heading_path, ensure_ascii=False),
             chunk.level, chunk.part, chunk.start, chunk.end, chunk.text,
             json.dumps([link.__dict__ for link in chunk.page_links], ensure_ascii=False), embed_key(chunk)),
        )
        conn.execute("INSERT INTO chunks_fts (rowid, tokens) VALUES (?, ?)",
                     (cur.lastrowid, " ".join(keyword_tokens(chunk.embedding_text()))))
        count += 1
    conn.commit()
    return count


def load_chunks(conn: sqlite3.Connection, chunking: str) -> dict[int, Chunk]:
    rows = conn.execute(
        "SELECT id, chunk_id, chunking, file, heading_path, level, part, start_offset, end_offset, text,"
        " page_links FROM chunks WHERE chunking = ? ORDER BY id", (chunking,)).fetchall()
    return {
        row[0]: Chunk(row[1], row[2], row[3], tuple(json.loads(row[4])), row[5], row[6], row[7], row[8], row[9],
                      tuple(PageLink(**link) for link in json.loads(row[10])))
        for row in rows
    }


def document_text(model: str, chunk: Chunk) -> str:
    template = DOCUMENT_TEMPLATES.get(model)
    text = chunk.embedding_text()
    return template.format(title=chunk.location, text=text) if template else text


def query_text(model: str, query: str) -> str:
    template = QUERY_TEMPLATES.get(model)
    return template.format(query=query) if template else query


def embed_chunks(conn: sqlite3.Connection, model: str, chunking: str) -> int:
    """Embed chunks whose text has no cached vector for ``model``; returns how many were embedded."""
    chunks = load_chunks(conn, chunking)
    keys = dict(conn.execute("SELECT id, embed_key FROM chunks WHERE chunking = ?", (chunking,)).fetchall())
    cached = {row[0] for row in conn.execute("SELECT embed_key FROM vectors WHERE model = ?", (model,))}
    todo: dict[str, Chunk] = {}
    for cid, chunk in chunks.items():
        if keys[cid] not in cached:
            todo.setdefault(keys[cid], chunk)
    vectors = llm.embed([document_text(model, c) for c in todo.values()], model)
    conn.executemany("INSERT OR REPLACE INTO vectors (embed_key, model, vector) VALUES (?, ?, ?)",
                     [(key, model, np.asarray(v, dtype=np.float32).tobytes()) for key, v in zip(todo, vectors)])
    conn.commit()
    return len(todo)


def load_matrix(conn: sqlite3.Connection, model: str, chunking: str) -> tuple[list[int], np.ndarray]:
    rows = conn.execute(
        "SELECT c.id, v.vector FROM chunks c JOIN vectors v ON v.embed_key = c.embed_key AND v.model = ?"
        " WHERE c.chunking = ? ORDER BY c.id", (model, chunking)).fetchall()
    total = conn.execute("SELECT count(*) FROM chunks WHERE chunking = ?", (chunking,)).fetchone()[0]
    if not rows or len(rows) < total:
        raise LookupError(f"{total - len(rows)} of {total} {chunking!r} chunks have no {model!r} vector;"
                          " run the embed command")
    ids = [row[0] for row in rows]
    matrix = np.vstack([np.frombuffer(row[1], dtype=np.float32) for row in rows])
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return ids, matrix
