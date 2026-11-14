"""Explanation mode: route the question, retrieve note sections, answer with numbered citations.

The model never calls a tool. The program runs the steps: a short routing call says what kind
of question it is, the program retrieves the passages, a calculation question gets its own step
where the model writes the arithmetic and Python computes it (a rejected program goes back once
with the error), and the model only writes a short answer that cites the passages.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
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


# Calculation programs: deterministic, and capped so a runaway answer is cut off early.
CALC_OPTIONS = {"temperature": 0.0, "top_p": 0.8, "top_k": 20, "num_predict": 400, "seed": 7}
FENCE = re.compile(r"^\s*```[A-Za-z]*\s*\n|\n\s*```\s*$")
TRUNCATED = "計算太長，超過長度上限被截斷"


@dataclass(frozen=True)
class Calculation:
    program: str               # what ran, or the last attempt
    steps: list[calc.Step]     # empty when the calculator could not run it
    error: str | None
    rewrites: int              # 1 when the first program was rejected and rewritten
    seconds: float             # time spent writing the program(s)

    @property
    def value(self) -> float | None:
        """The last result when it is a single number."""
        last = self.steps[-1].value if self.steps else None
        return last if isinstance(last, float) else None


ProgramWriter = Callable[[list[dict[str, str]]], tuple[str, float, bool]]


def write_program(messages: list[dict[str, str]]) -> tuple[str, float, bool]:
    """The program text, the seconds it took, and whether it hit the token limit."""
    result = llm.chat(messages, options=CALC_OPTIONS, purpose="calc")
    truncated = result.output_tokens is not None and result.output_tokens >= CALC_OPTIONS["num_predict"]
    return FENCE.sub("", result.content).strip(), result.wall_seconds, truncated


def compute(question: str, passages: list[Chunk], write: ProgramWriter = write_program) -> Calculation:
    """The model writes the arithmetic, Python runs it; a fixable error goes back once for a rewrite.

    Its own step, so the routing call stays short; in the routing JSON, long programs were cut off
    and took the whole routing down with them (sc-07), and the notes' formulas were not in view.
    """
    messages = [{"role": "system", "content": harness_text("skills/calc/SKILL.md")},
                {"role": "user", "content": f"筆記段落：\n\n{passages_block(passages)}\n\n題目：{question}"}]
    seconds, error, program, attempt = 0.0, "", "", 0
    for attempt in range(2):
        program, took, truncated = write(messages)
        seconds += took
        try:
            return Calculation(program, calc.run(program), None, attempt, seconds)
        except calc.CalcError as exc:
            error, rewritable = (TRUNCATED, False) if truncated else (str(exc), exc.rewritable)
        if not rewritable:
            break
        messages += [{"role": "assistant", "content": program},
                     {"role": "user", "content": f"計算器算不出來：{error}\n請照規則重寫整段計算，只輸出計算。"}]
    return Calculation(program, [], error, attempt, seconds)


def calc_passage(steps: list[calc.Step]) -> Chunk:
    text = "\n".join(step.text() for step in steps)
    return Chunk("calc", "calc", "", ("程式計算結果",), 0, 1, 0, 0, text, ())


class ClaimVerdict(BaseModel):
    claim: str
    verdict: Literal["正確", "需要修正", "錯誤", "筆記沒寫"]
    evidence: list[int] = Field(default_factory=list)
    correction: str = ""


class ClaimCheck(BaseModel):
    claims: list[ClaimVerdict]
    summary: str


MAX_CHECK_PASSAGES = 6


def retrieve_for_claims(retriever: Retriever, query: str, claims: list[str], k: int) -> list[Hit]:
    """Passages for the claim check, shared out so the question's own hits cannot crowd the claims out.

    Order: each claim's best passage, the question's two best, each claim's next passage, then the
    rest of the question's. Filling with the question's hits first dropped gold sections at the cap
    (16 of 19 kept on the dev claim-check questions; change 7).
    """
    question = retriever.search(query, k=k)
    per_claim = [retriever.search(claim, k=3) for claim in claims]
    chosen: dict[str, Hit] = {}

    def take(hit: Hit | None) -> None:
        if hit is not None and len(chosen) < MAX_CHECK_PASSAGES:
            chosen.setdefault(hit.chunk.chunk_id, hit)

    def next_new(hits: list[Hit]) -> Hit | None:
        return next((hit for hit in hits if hit.chunk.chunk_id not in chosen), None)

    for hits in per_claim:
        take(next_new(hits))
    for hit in question[:2]:
        take(hit)
    for hits in per_claim:
        take(next_new(hits))
    for hit in question[2:]:
        take(hit)
    return list(chosen.values())


def check_claims(question: str, claims: list[str], passages: list[Chunk]) -> tuple[ClaimCheck, float]:
    """Judge each claim in its own structured call, before any answer is written (failure: mb-08, mb-16)."""
    numbered = "\n".join(f"{n}. {claim}" for n, claim in enumerate(claims, start=1))
    user = f"筆記段落：\n\n{passages_block(passages)}\n\n使用者的主張：\n{numbered}\n\n使用者的原話：{question}"
    messages = [{"role": "system", "content": harness_text("skills/check/SKILL.md")}, {"role": "user", "content": user}]
    return llm.structured(messages, ClaimCheck, temperature=0.0, purpose="check", num_predict=1200)


def render_check(result: ClaimCheck, passage_count: int) -> str:
    lines = [result.summary.strip(), ""]
    for c in result.claims:
        cite = "".join(f"[{n}]" for n in c.evidence if 1 <= n <= passage_count)
        if c.verdict == "正確":
            lines.append(f"- 對：{c.claim} {cite}".rstrip())
        elif c.verdict == "筆記沒寫":
            lines.append(f"- {REFUSAL}：{c.claim}")
        else:
            lines.append(f"- {c.verdict}：{c.claim} → {c.correction} {cite}".rstrip())
    return "\n".join(lines).strip()


@dataclass(frozen=True)
class CitationCheck:
    cited: tuple[int, ...]
    invalid: tuple[int, ...]
    refused: bool

    @property
    def ok(self) -> bool:
        return not self.invalid and (bool(self.cited) or self.refused)


SENTENCE_END = re.compile(r"[。\n]")


def is_refusal(answer: str) -> bool:
    """A refusal says so up front (guardrail 3); a later remark about a detail the notes leave out is not one."""
    return REFUSAL in SENTENCE_END.split(answer.strip(), maxsplit=1)[0]


def check_citations(answer: str, passage_count: int) -> CitationCheck:
    numbers = [int(n) for n in CITATION.findall(answer)]
    cited = tuple(sorted(set(numbers)))
    invalid = tuple(n for n in cited if not 1 <= n <= passage_count)
    return CitationCheck(cited, invalid, is_refusal(answer))


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
    calculation: Calculation | None = None
    claim_check: ClaimCheck | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    attempts: list[str] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        calc_seconds = self.calculation.seconds if self.calculation else 0.0
        return self.route_seconds + calc_seconds + self.retrieval_seconds + self.generation_seconds


def answer(question: str, retriever: Retriever, *, k: int = 4, history: list[dict[str, str]] | None = None,
           retrieval_query: str | None = None, use_router: bool = True) -> ExplainResult:
    routed, route_seconds = route(question) if use_router else (None, 0.0)

    if routed and routed.type == "check-understanding" and routed.claims:
        started = time.perf_counter()
        hits = retrieve_for_claims(retriever, retrieval_query or question, routed.claims, k)
        retrieval_seconds = time.perf_counter() - started
        passages = [hit.chunk for hit in hits]
        try:
            judged, seconds = check_claims(question, routed.claims, passages)
            text = render_check(judged, len(passages))
            return ExplainResult(question, text, passages, hits, check_citations(text, len(passages)), 0,
                                 retrieval_seconds, seconds, routed, route_seconds, claim_check=judged)
        except llm.StructuredOutputError:
            pass  # fall back to a normal explanation below

    started = time.perf_counter()
    hits = retriever.search(retrieval_query or question, k=k)
    retrieval_seconds = time.perf_counter() - started

    passages: list[Chunk] = []
    calculation = None
    # A question without any digit has nothing to compute; the calc step would invent numbers (mb-19).
    if routed and routed.type == "calculation" and any(ch.isdigit() for ch in question):
        calculation = compute(question, [hit.chunk for hit in hits])
        if calculation.steps:
            passages.append(calc_passage(calculation.steps))
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
                         generation_seconds, route=routed, route_seconds=route_seconds, calculation=calculation,
                         prompt_tokens=prompt_tokens, output_tokens=output_tokens, attempts=attempts)


def sources(result: ExplainResult) -> list[str]:
    lines = []
    for n in result.check.cited:
        if not 1 <= n <= len(result.passages):
            continue
        chunk = result.passages[n - 1]
        pages = "、".join(dict.fromkeys(link.label for link in chunk.page_links))
        lines.append(f"[{n}] {chunk.location}" + (f"（{pages}）" if pages else ""))
    return lines
