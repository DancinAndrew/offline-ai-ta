"""Paths and settings shared by the AI TA modules."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_ROOT = REPO_ROOT.parent

DATA_DIR = REPO_ROOT / "data"
KNOWLEDGE_MANIFEST = DATA_DIR / "knowledge" / "sources.json"
INDEX_DB = DATA_DIR / "index" / "index.sqlite"
LOG_DIR = DATA_DIR / "logs"
# Overridable so tests and trial runs do not write into my real practice history.
LEARNER_DIR = Path(os.environ.get("AI_TA_LEARNER_DIR", DATA_DIR / "learner"))

HARNESS_DIR = REPO_ROOT / "dev" / "harness"
EVAL_DIR = REPO_ROOT / "dev" / "eval"

OLLAMA_URL = os.environ.get("AI_TA_OLLAMA_URL", "http://localhost:11434")
GENERATION_MODEL = os.environ.get("AI_TA_MODEL", "qwen3.5:9b")

# Candidates compared in step 5; EMBEDDING_MODEL and RETRIEVAL_METHOD are the choice (decision 0005).
EMBEDDING_MODELS = ("bge-m3", "qwen3-embedding:0.6b", "embeddinggemma-2:270m")
EMBEDDING_MODEL = os.environ.get("AI_TA_EMBED_MODEL", "qwen3-embedding:0.6b")
RETRIEVAL_METHOD = "vector"
