"""Small client for the local Ollama HTTP API, with a call log."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from pydantic import BaseModel, ValidationError

from . import config

CALL_LOG = config.LOG_DIR / "llm-calls.jsonl"


class OllamaError(RuntimeError):
    """Ollama returned an error or could not be reached."""


class StructuredOutputError(RuntimeError):
    """The model did not return output matching the schema, even after a retry."""


@dataclass(frozen=True)
class ChatResult:
    content: str
    thinking: str
    wall_seconds: float
    prompt_tokens: int | None
    output_tokens: int | None


def _post(path: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    try:
        response = requests.post(f"{config.OLLAMA_URL}{path}", json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise OllamaError(f"cannot reach Ollama at {config.OLLAMA_URL}: {exc}") from exc
    if response.status_code != 200:
        raise OllamaError(f"{path} returned {response.status_code}: {response.text[:300]}")
    return response.json()


def embed(texts: list[str], model: str, *, batch_size: int = 16, timeout: float = 600) -> list[list[float]]:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        data = _post("/api/embed", {"model": model, "input": texts[i : i + batch_size]}, timeout)
        vectors.extend(data["embeddings"])
    return vectors


def chat(
    messages: list[dict[str, str]],
    *,
    model: str = config.GENERATION_MODEL,
    think: bool = False,
    fmt: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
    timeout: float = 600,
    purpose: str = "",
) -> ChatResult:
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False, "think": think}
    if fmt is not None:
        payload["format"] = fmt
    if options:
        payload["options"] = options
    started = time.perf_counter()
    data = _post("/api/chat", payload, timeout)
    wall = time.perf_counter() - started
    message = data.get("message", {})
    result = ChatResult(
        content=message.get("content", ""),
        thinking=message.get("thinking", "") or "",
        wall_seconds=wall,
        prompt_tokens=data.get("prompt_eval_count"),
        output_tokens=data.get("eval_count"),
    )
    _log({"purpose": purpose, "model": model, "think": think, "options": options or {},
          "format": fmt is not None, "messages": messages, "content": result.content,
          "thinking": result.thinking, "wall_seconds": round(wall, 2),
          "prompt_tokens": result.prompt_tokens, "output_tokens": result.output_tokens})
    return result


def structured(messages: list[dict[str, str]], schema: type[BaseModel], *, temperature: float = 0.0,
               purpose: str = "", num_predict: int = 900) -> tuple[BaseModel, float]:
    """Ask for JSON matching ``schema`` (Ollama ``format``), validate it, retry once.

    Returns the parsed object and the seconds spent in the model.
    """
    options = {"temperature": temperature, "top_p": 0.8, "top_k": 20, "presence_penalty": 0.0,
               "num_predict": num_predict, "seed": 7}
    seconds, last_error = 0.0, ""
    for _ in range(2):
        result = chat(messages, fmt=schema.model_json_schema(), options=options, purpose=purpose)
        seconds += result.wall_seconds
        try:
            return schema.model_validate_json(result.content), seconds
        except ValidationError as exc:
            last_error = str(exc)
    raise StructuredOutputError(f"{purpose}: invalid output after a retry: {last_error[:300]}")


def _log(record: dict[str, Any]) -> None:
    CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    with CALL_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
