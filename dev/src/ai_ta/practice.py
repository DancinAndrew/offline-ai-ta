"""Practice mode: quiz first, then grade against reference points from the notes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from . import llm
from .explain import harness_text
from .ingest import Chunk
from .textutil import clean_text

BLOOM_LEVELS = ("理解", "應用", "分析", "記憶")
GIVE_UP_WORDS = ("不知道", "不會", "放棄", "pass")


class QuizItem(BaseModel):
    bloom_level: Literal["記憶", "理解", "應用", "分析"]
    question: str = Field(min_length=5)
    reference_points: list[str] = Field(min_length=2, max_length=4)
    hint: str


class Grade(BaseModel):
    label: Literal["正確", "部分正確", "矛盾", "離題", "不知道"]
    correct_parts: list[str]
    wrong_parts: list[str]
    feedback: str


class PracticeError(RuntimeError):
    """The model did not return a valid structured answer after retrying."""


def _passage(chunk: Chunk) -> str:
    return f"[1] {chunk.location}\n{clean_text(chunk.text)}"


def _structured(messages: list[dict[str, str]], schema: type[BaseModel], *, temperature: float,
                purpose: str) -> BaseModel:
    options = {"temperature": temperature, "top_p": 0.8, "top_k": 20, "presence_penalty": 0.0, "num_predict": 900}
    last_error = ""
    for _ in range(2):
        result = llm.chat(messages, fmt=schema.model_json_schema(), options=options, purpose=purpose)
        try:
            return schema.model_validate_json(result.content)
        except ValidationError as exc:
            last_error = str(exc)
    raise PracticeError(f"{purpose}: invalid output after a retry: {last_error[:300]}")


def bloom_for(attempts: int) -> str:
    """Start with understanding, then move to application and analysis."""
    return BLOOM_LEVELS[attempts % 3]


def make_question(chunk: Chunk, bloom: str) -> QuizItem:
    system = harness_text("systemprompt.md", "skills/quiz/SKILL.md")
    user = f"筆記段落：\n\n{_passage(chunk)}\n\n請出一題「{bloom}」層級的回想題。"
    return _structured([{"role": "system", "content": system}, {"role": "user", "content": user}],
                       QuizItem, temperature=0.4, purpose="quiz")


def is_give_up(answer: str) -> bool:
    text = answer.strip().lower()
    return not text or any(word in text for word in GIVE_UP_WORDS)


def grade(chunk: Chunk, quiz: QuizItem, answer: str) -> Grade:
    if is_give_up(answer):
        return Grade(label="不知道", correct_parts=[], wrong_parts=[], feedback="先看參考要點，下次再試一次。")
    system = harness_text("skills/grade/SKILL.md")
    points = "\n".join(f"- {p}" for p in quiz.reference_points)
    user = (f"筆記段落：\n\n{_passage(chunk)}\n\n題目：{quiz.question}\n\n參考要點：\n{points}\n\n"
            f"使用者的作答：{answer}")
    return _structured([{"role": "system", "content": system}, {"role": "user", "content": user}],
                       Grade, temperature=0.0, purpose="grade")
