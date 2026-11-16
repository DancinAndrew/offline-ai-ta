"""Practice mode: quiz first, then grade against reference points from the notes."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

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


def _passage(chunk: Chunk) -> str:
    return f"[1] {chunk.location}\n{clean_text(chunk.text)}"


def bloom_for(attempts: int) -> str:
    """Start with understanding, then move to application and analysis."""
    return BLOOM_LEVELS[attempts % 3]


def make_question(chunk: Chunk, bloom: str) -> QuizItem:
    system = harness_text("systemprompt.md", "skills/quiz/SKILL.md")
    user = f"筆記段落：\n\n{_passage(chunk)}\n\n請出一題「{bloom}」層級的回想題。"
    quiz, _ = llm.structured([{"role": "system", "content": system}, {"role": "user", "content": user}],
                             QuizItem, temperature=0.4, purpose="quiz")
    return quiz


GIVE_UP_MAX_CHARS = 6


def is_give_up(answer: str) -> bool:
    """An empty or very short answer such as 「不知道」「我不會」「放棄」.

    A real answer that happens to contain 「不會」 (「這樣不會過擬合」) is not giving up; the old substring test
    graded such answers 不知道 without reading them.
    """
    text = re.sub(r"[\s。，、！？!?.…~～]", "", answer).lower()
    return not text or (len(text) <= GIVE_UP_MAX_CHARS and any(word in text for word in GIVE_UP_WORDS))


def grade(chunk: Chunk, quiz: QuizItem, answer: str) -> Grade:
    if is_give_up(answer):
        return Grade(label="不知道", correct_parts=[], wrong_parts=[], feedback="先看參考要點，下次再試一次。")
    system = harness_text("skills/grade/SKILL.md")
    points = "\n".join(f"- {p}" for p in quiz.reference_points)
    user = (f"筆記段落：\n\n{_passage(chunk)}\n\n題目：{quiz.question}\n\n參考要點：\n{points}\n\n"
            f"使用者的作答：{answer}")
    result, _ = llm.structured([{"role": "system", "content": system}, {"role": "user", "content": user}],
                               Grade, temperature=0.0, purpose="grade")
    return result
