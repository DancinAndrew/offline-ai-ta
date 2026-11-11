"""Explanation mode: route the question, retrieve note sections, answer with numbered citations.

The model never calls a tool. The program runs the steps: a short routing call says what kind
of question it is, Python computes any arithmetic, the program retrieves the passages, and the
model only writes a short answer that cites them.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from . import calc, config, llm
from .ingest import Chunk
from .retrieve import Hit, Retriever
from .textutil import clean_text

CITATION = re.compile(r"\[(\d+)\]")
REFUSAL = "筆記裡沒有提到"

# A fixed seed makes eval runs repeatable, so a change in results comes from a change in the harness.
OPTIONS = {"temperature": 0.3, "top_p": 0.8, "top_k": 20, "presence_penalty": 0.0, "num_predict": 800, "seed": 7}

QuestionType = Literal["concept", "comparison", "check-understanding", "calculation", "formula", "fact"]


class Route(BaseModel):
    type: QuestionType
    claims: list[str] = Field(default_factory=list)
    expression: str = ""


def harness_text(*names: str) -> str:
    return "\n\n".join((config.HARNESS_DIR / name).read_text(encoding="utf-8").strip() for name in names)


def system_prompt() -> str:
    # Fixed order and content, so Ollama can reuse the cached prompt prefix across questions.
    return harness_text("systemprompt.md", "guardrails.md", "skills/explain/SKILL.md")


def passages_block(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{n}] {c.location}\n{clean_text(c.text)}" for n, c in enumerate(chunks, start=1))


def route(question: str) -> tuple[Route | None, float]:
    """Classify the question; on invalid output, fall back to no routing."""
    messages = [{"role": "system", "content": harness_text("skills/route/SKILL.md")},
                {"role": "user", "content": question}]
    try:
        return llm.structured(messages, Route, temperature=0.0, purpose="route", num_predict=400)
    except llm.StructuredOutputError:
        return None, 0.0


def calc_passage(expression: str, value: float) -> Chunk:
    return Chunk("calc", "calc", "", ("程式計算結果",), 0, 1, 0, 0, f"{expression} = {value:.6g}", ())


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
    passages: list[Chunk]          # numbered [1], [2], ... as shown to the model
    hits: list[Hit]                # what retrieval returned
    check: CitationCheck
    retries: int
    retrieval_seconds: float
    generation_seconds: float
    route: Route | None = None
    route_seconds: float = 0.0
    calc_value: float | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    attempts: list[str] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        return self.route_seconds + self.retrieval_seconds + self.generation_seconds


def answer(question: str, retriever: Retriever, *, k: int = 4, history: list[dict[str, str]] | None = None,
           retrieval_query: str | None = None, use_router: bool = True) -> ExplainResult:
    routed, route_seconds = route(question) if use_router else (None, 0.0)

    passages: list[Chunk] = []
    calc_value = None
    if routed and routed.type == "calculation" and routed.expression.strip():
        try:
            calc_value = calc.evaluate(routed.expression)
            passages.append(calc_passage(routed.expression.strip(), calc_value))
        except calc.CalcError:
            pass

    started = time.perf_counter()
    hits = retriever.search(retrieval_query or question, k=k)
    retrieval_seconds = time.perf_counter() - started
    passages += [hit.chunk for hit in hits]

    messages = [{"role": "system", "content": system_prompt()}, *(history or [])]
    messages.append({"role": "user", "content": f"筆記段落：\n\n{passages_block(passages)}\n\n問題：{question}"})

    attempts: list[str] = []
    generation_seconds = 0.0
    prompt_tokens = output_tokens = None
    for _ in range(2):
        result = llm.chat(messages, options=OPTIONS, purpose="explain")
        generation_seconds += result.wall_seconds
        prompt_tokens, output_tokens = result.prompt_tokens, result.output_tokens
        attempts.append(result.content)
        check = check_citations(result.content, len(passages))
        if check.ok:
            break
        messages += [
            {"role": "assistant", "content": result.content},
            {"role": "user", "content": f"這個回答缺少段落編號，或用了不存在的編號。請重寫：每句句尾標 [1]–[{len(passages)}]；"
                                        f"段落裡沒有答案就寫「{REFUSAL}」。"},
        ]
    return ExplainResult(question, attempts[-1], passages, hits, check, len(attempts) - 1, retrieval_seconds,
                         generation_seconds, routed, route_seconds, calc_value, prompt_tokens, output_tokens,
                         attempts)


def sources(result: ExplainResult) -> list[str]:
    lines = []
    for n in result.check.cited:
        if not 1 <= n <= len(result.passages):
            continue
        chunk = result.passages[n - 1]
        pages = "、".join(dict.fromkeys(link.label for link in chunk.page_links))
        lines.append(f"[{n}] {chunk.location}" + (f"（{pages}）" if pages else ""))
    return lines
