"""Explanation mode: retrieve note sections first, then answer with numbered citations.

The model never calls a tool here. The program retrieves the passages, so the model
only has to write a short answer that cites them.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from . import config, llm
from .ingest import Chunk
from .retrieve import Hit, Retriever
from .textutil import clean_text

CITATION = re.compile(r"\[(\d+)\]")
REFUSAL = "筆記裡沒有提到"

# A fixed seed makes eval runs repeatable, so a change in results comes from a change in the harness.
OPTIONS = {"temperature": 0.3, "top_p": 0.8, "top_k": 20, "presence_penalty": 0.0, "num_predict": 800, "seed": 7}


def harness_text(*names: str) -> str:
    return "\n\n".join((config.HARNESS_DIR / name).read_text(encoding="utf-8").strip() for name in names)


def system_prompt() -> str:
    # Fixed order and content, so Ollama can reuse the cached prompt prefix across questions.
    return harness_text("systemprompt.md", "guardrails.md", "skills/explain/SKILL.md")


def passages_block(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{n}] {c.location}\n{clean_text(c.text)}" for n, c in enumerate(chunks, start=1))


@dataclass(frozen=True)
class CitationCheck:
    cited: tuple[int, ...]
    invalid: tuple[int, ...]
    refused: bool

    @property
    def ok(self) -> bool:
        return not self.invalid and (bool(self.cited) or self.refused)


def check_citations(answer: str, passage_count: int) -> CitationCheck:
    numbers = [int(n) for n in CITATION.findall(answer)]
    cited = tuple(sorted(set(numbers)))
    invalid = tuple(n for n in cited if not 1 <= n <= passage_count)
    return CitationCheck(cited, invalid, REFUSAL in answer)


@dataclass
class ExplainResult:
    question: str
    answer: str
    hits: list[Hit]
    check: CitationCheck
    retries: int
    retrieval_seconds: float
    generation_seconds: float
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    attempts: list[str] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        return self.retrieval_seconds + self.generation_seconds

    def cited_chunks(self) -> list[Chunk]:
        return [self.hits[n - 1].chunk for n in self.check.cited if 1 <= n <= len(self.hits)]


def answer(question: str, retriever: Retriever, *, k: int = 4, history: list[dict[str, str]] | None = None,
           retrieval_query: str | None = None) -> ExplainResult:
    started = time.perf_counter()
    hits = retriever.search(retrieval_query or question, k=k)
    retrieval_seconds = time.perf_counter() - started

    chunks = [hit.chunk for hit in hits]
    messages = [{"role": "system", "content": system_prompt()}, *(history or [])]
    messages.append({"role": "user", "content": f"筆記段落：\n\n{passages_block(chunks)}\n\n問題：{question}"})

    attempts: list[str] = []
    generation_seconds = 0.0
    prompt_tokens = output_tokens = None
    for attempt in range(2):
        result = llm.chat(messages, options=OPTIONS, purpose="explain")
        generation_seconds += result.wall_seconds
        prompt_tokens, output_tokens = result.prompt_tokens, result.output_tokens
        attempts.append(result.content)
        check = check_citations(result.content, len(chunks))
        if check.ok:
            break
        messages += [
            {"role": "assistant", "content": result.content},
            {"role": "user", "content": f"這個回答缺少段落編號，或用了不存在的編號。請重寫：每句句尾標 [1]–[{len(chunks)}]；"
                                        f"段落裡沒有答案就寫「{REFUSAL}」。"},
        ]
    return ExplainResult(question, attempts[-1], hits, check, len(attempts) - 1, retrieval_seconds,
                         generation_seconds, prompt_tokens, output_tokens, attempts)


def sources(result: ExplainResult) -> list[str]:
    lines = []
    for n in result.check.cited:
        if not 1 <= n <= len(result.hits):
            continue
        chunk = result.hits[n - 1].chunk
        pages = "、".join(dict.fromkeys(link.label for link in chunk.page_links))
        lines.append(f"[{n}] {chunk.location}" + (f"（{pages}）" if pages else ""))
    return lines
