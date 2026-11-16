"""A review session: practice due and weak points, re-explain repeated misses, answer questions on the way.

The program runs the session; the model only decides what one free-form message is (decision 0007).
Each reply is Markdown, so the terminal and the web page show the same thing.
"""

from __future__ import annotations

import random
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from . import explain, learner, llm, practice
from .explain import harness_text
from .ingest import Chunk, PageLink
from .retrieve import Hit, Retriever

Action = Literal["answer", "hint", "give_up", "ask", "quiz", "progress", "search"]
MIN_QUIZ_SECTION_CHARS = 200
LIST_LIMIT = 5
COMMANDS: dict[str, Action] = {"開始": "quiz", "出題": "quiz", "下一題": "quiz", "換一題": "quiz", "提示": "hint",
                               "放棄": "give_up", "看答案": "give_up", "進度": "progress"}
END_WORDS = ("結束", "exit", "quit")


class Intent(BaseModel):
    action: Action
    topic: str = ""


@dataclass
class Pending:
    """A question waiting for an answer. Its id makes a second submission of the same answer a no-op."""
    chunk: Chunk
    quiz: practice.QuizItem
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    hinted: bool = False
    recheck: bool = False   # asked right after a re-explanation


@dataclass(frozen=True)
class Reply:
    kind: Literal["opening", "question", "hint", "grade", "reexplain", "answer", "progress", "search", "note"]
    markdown: str


def classify(text: str, pending: Pending | None) -> Intent:
    """One structured call; obvious commands are read by the program first."""
    stripped = text.strip()
    if stripped in COMMANDS:
        return Intent(action=COMMANDS[stripped])
    if pending and practice.is_give_up(stripped):
        return Intent(action="give_up")
    waiting = f"目前等作答的題目：{pending.quiz.question}" if pending else "目前沒有題目在等作答。"
    messages = [{"role": "system", "content": harness_text("skills/intent/SKILL.md")},
                {"role": "user", "content": f"{waiting}\n\n使用者的訊息：{stripped}"}]
    try:
        intent, _ = llm.structured(messages, Intent, temperature=0.0, purpose="intent", num_predict=200)
    except llm.StructuredOutputError:
        intent = Intent(action="answer" if pending else "ask")
    if not pending and intent.action in ("answer", "hint", "give_up"):
        return Intent(action="ask")
    return intent


class PinnedRetriever:
    """Puts one section first, then the usual results: a re-explanation must stay on the missed point."""

    def __init__(self, base: Retriever, chunk: Chunk):
        self.base, self.chunk = base, chunk
        self.chunks = base.chunks

    def search(self, query: str, k: int = 5, **kwargs) -> list[Hit]:
        rest = [h for h in self.base.search(query, k=k + 1, **kwargs) if h.chunk.chunk_id != self.chunk.chunk_id]
        return [Hit(self.chunk, 1.0)] + rest[:k - 1]


LinkBuilder = Callable[[PageLink], str]


def pages_markdown(chunk: Chunk, link: LinkBuilder | None) -> str:
    """The slide pages of a section: plain labels in the terminal, links that open the PDF page on the web."""
    first: dict[str, PageLink] = {}
    for page in chunk.page_links:
        first.setdefault(page.label, page)
    if not first:
        return ""
    shown = [f"[{label}]({link(page)})" if link else label for label, page in first.items()]
    return "（" + "、".join(shown) + "）"


def sources_markdown(result: explain.ExplainResult, link: LinkBuilder | None = None) -> str:
    lines = [f"[{n}] {result.passages[n - 1].location}{pages_markdown(result.passages[n - 1], link)}"
             for n in result.check.cited if 1 <= n <= len(result.passages)]
    return ("\n\n**出處**\n" + "\n".join(f"- {line}" for line in lines)) if lines else ""


@dataclass
class Services:
    """The model-backed steps, replaceable in tests."""
    classify: Callable[[str, Pending | None], Intent] = classify
    make_question: Callable[[Chunk, str], practice.QuizItem] = practice.make_question
    grade: Callable[[Chunk, practice.QuizItem, str], practice.Grade] = practice.grade
    answer_question: Callable[..., explain.ExplainResult] = explain.answer


class ReviewSession:
    def __init__(self, retriever: Retriever, *, events: Path = learner.EVENTS, services: Services | None = None,
                 link: LinkBuilder | None = None):
        self.retriever = retriever
        self.events = events
        self.services = services or Services()
        self.link = link
        self.pending: Pending | None = None
        self.topic: str | None = None        # the topic the user asked for, kept for the next questions
        self.reexplained: set[str] = set()   # once per point per session
        self.missed: set[str] = set()        # points answered wrong in this session

    # --- state -----------------------------------------------------------------------------------------
    def states(self) -> dict[str, learner.PointState]:
        return learner.derive_state(learner.load_events(self.events))

    def opening(self) -> Reply:
        states = self.states()
        due, weak = learner.due_points(states), learner.weak_points(states)
        lines = ["**今天的複習**"]
        if not states:
            lines.append("還沒有練習紀錄。說一個想練的主題（例如「決策樹」），或輸入「開始」隨機出題。")
        else:
            lines.append(f"- 到期 {len(due)} 個、常錯 {len(weak)} 個。")
            lines += [f"  - 到期：{s.location}" for s in due[:LIST_LIMIT]]
            lines += [f"  - 常錯：{s.location}（掌握度 {s.mastery:.0%}）" for s in weak[:LIST_LIMIT]]
            lines.append("輸入「開始」照建議練習，或說想練的主題。隨時可以直接問問題。")
        return Reply("opening", "\n".join(lines))

    def status(self) -> str:
        states = self.states()
        due, weak = learner.due_points(states), learner.weak_points(states)
        lines = [f"**到期** {len(due)}　**常錯** {len(weak)}"]
        lines += [f"- 常錯：{s.location.split(' > ')[-1]}（{s.mastery:.0%}）" for s in weak[:LIST_LIMIT]]
        if self.topic:
            lines.append(f"\n**目前主題**：{self.topic}")
        if self.pending:
            lines.append(f"\n**等你作答**：{self.pending.quiz.question}")
        return "\n".join(lines)

    # --- dispatch --------------------------------------------------------------------------------------
    def handle(self, text: str) -> list[Reply]:
        if not text.strip():
            return []
        intent = self.services.classify(text, self.pending)
        if intent.action == "answer":
            return self.answer(text)
        if intent.action == "hint":
            return self.hint()
        if intent.action == "give_up":
            return self.give_up()
        if intent.action == "quiz":
            # A named topic sticks for the next questions; 「開始」 goes back to the schedule's suggestions.
            if intent.topic:
                self.topic = intent.topic
            elif text.strip() == "開始":
                self.topic = None
            return self.next_question(self.topic)
        if intent.action == "progress":
            return [self.progress()]
        if intent.action == "search":
            return [self.search(text)]
        return self.ask(text)

    # --- practice --------------------------------------------------------------------------------------
    def pick_point(self, topic: str | None) -> Chunk | None:
        states = self.states()
        by_id = {c.chunk_id: c for c in self.retriever.chunks.values()}
        # A point missed in this session comes back once the schedule says it is due (about a minute after
        # a miss), even when a topic is set; a second miss is what triggers the re-explanation.
        for state in learner.due_points(states):
            if state.knowledge_point in self.missed and state.knowledge_point in by_id:
                return by_id[state.knowledge_point]
        if topic:
            candidates = [h.chunk for h in self.retriever.search(topic, k=8)
                          if len(h.chunk.text) >= MIN_QUIZ_SECTION_CHARS]
            # The relevant section practiced least often.
            return min(candidates, key=lambda c: states[c.chunk_id].attempts if c.chunk_id in states else 0,
                       default=None)
        for state in learner.due_points(states) + learner.weak_points(states):
            if state.knowledge_point in by_id:
                return by_id[state.knowledge_point]
        fresh = [c for c in by_id.values() if c.chunk_id not in states and len(c.text) >= MIN_QUIZ_SECTION_CHARS]
        return random.choice(fresh) if fresh else None

    def next_question(self, topic: str | None = None, chunk: Chunk | None = None, recheck: bool = False) -> list[Reply]:
        chunk = chunk or self.pick_point(topic)
        if chunk is None:
            return [Reply("note", f"找不到和「{topic}」相關、內容夠長的筆記段落。" if topic else "目前沒有可以出題的段落。")]
        states = self.states()
        attempts = states[chunk.chunk_id].attempts if chunk.chunk_id in states else 0
        quiz = self.services.make_question(chunk, practice.bloom_for(attempts))
        self.pending = Pending(chunk, quiz, recheck=recheck)
        lead = "**再確認一題**" if recheck else f"**練習（{quiz.bloom_level}）**"
        return [Reply("question", f"{lead}　_{chunk.location}_\n\n{quiz.question}\n\n"
                                  "（作答；輸入「提示」看提示，「放棄」看答案。）")]

    def hint(self) -> list[Reply]:
        if not self.pending:
            return [Reply("note", "目前沒有題目在等作答。")]
        if self.pending.hinted:
            return [Reply("hint", f"提示只有一個：{self.pending.quiz.hint}\n\n想不出來可以輸入「放棄」看答案。")]
        self.pending.hinted = True
        return [Reply("hint", f"提示：{self.pending.quiz.hint}")]

    def give_up(self) -> list[Reply]:
        return self.answer("放棄")

    def answer(self, text: str, pending_id: str | None = None) -> list[Reply]:
        pending = self.pending
        if pending is None or (pending_id is not None and pending_id != pending.id):
            return [Reply("note", "這題已經批改過了。")]
        self.pending = None   # cleared before grading, so a repeated submission cannot record twice
        result = self.services.grade(pending.chunk, pending.quiz, text)
        learner.record(learner.Event(pending.chunk.chunk_id, pending.chunk.location, pending.quiz.bloom_level,
                                     pending.quiz.question, text, result.label), self.events)
        state = self.states()[pending.chunk.chunk_id]
        if result.label != "正確":
            self.missed.add(pending.chunk.chunk_id)
        replies = [Reply("grade", grade_markdown(pending, result, state, self.link))]
        if self.needs_reexplain(state):
            replies += self.reexplain(pending)
        return replies

    def needs_reexplain(self, state: learner.PointState) -> bool:
        """A weak point (learner.weak_points' rule) is explained another way once per session."""
        weak = {s.knowledge_point for s in learner.weak_points({state.knowledge_point: state})}
        return state.knowledge_point in weak and state.knowledge_point not in self.reexplained

    def reexplain(self, pending: Pending) -> list[Reply]:
        self.reexplained.add(pending.chunk.chunk_id)
        topic = pending.chunk.location.split(" > ")[-1]
        points = "；".join(pending.quiz.reference_points)
        question = (f"我在「{topic}」一直答錯。請換一種方式重新講解：先用段落裡的例子或一個比喻說明，"
                    f"再對回筆記的說法。要講清楚的重點：{points}")
        result = self.services.answer_question(question, PinnedRetriever(self.retriever, pending.chunk))
        replies = [Reply("reexplain", f"**換個方式講：{topic}**\n\n{result.answer}{sources_markdown(result, self.link)}")]
        return replies + self.next_question(chunk=pending.chunk, recheck=True)

    # --- questions, progress, search -------------------------------------------------------------------
    def ask(self, text: str) -> list[Reply]:
        result = self.services.answer_question(text, self.retriever)
        replies = [Reply("answer", f"{result.answer}{sources_markdown(result, self.link)}")]
        if result.unresolved:
            replies.append(Reply("note", "回答裡的數字和程式計算結果對不上，請以出處 [1] 的程式計算結果為準。"))
        if self.pending:
            replies.append(Reply("note", f"剛才那題還在等你作答：{self.pending.quiz.question}"))
        return replies

    def progress(self) -> Reply:
        states = self.states()
        if not states:
            return Reply("progress", "還沒有練習紀錄。")
        weak = {s.knowledge_point for s in learner.weak_points(states)}
        rows = sorted(states.values(), key=lambda s: s.due)
        lines = ["| 知識點 | 練習次數 | 掌握度 | 下次複習 |", "|---|---:|---:|---|"]
        lines += [f"| {s.location}{'（常錯）' if s.knowledge_point in weak else ''} | {s.attempts} | "
                  f"{s.mastery:.0%} | {s.due.astimezone():%m/%d %H:%M} |" for s in rows]
        return Reply("progress", "\n".join(lines))

    def search(self, text: str) -> Reply:
        hits = self.retriever.search(text, k=5)
        lines = ["**筆記裡的相關段落**"]
        lines += [f"- {hit.chunk.location}{pages_markdown(hit.chunk, self.link)}" for hit in hits]
        return Reply("search", "\n".join(lines))


def grade_markdown(pending: Pending, result: practice.Grade, state: learner.PointState,
                   link: LinkBuilder | None = None) -> str:
    lines = [f"**{result.label}**"]
    lines += [f"- ✓ {part}" for part in result.correct_parts]
    lines += [f"- ✗ {part}" for part in result.wrong_parts]
    lines += ["", result.feedback, "", "**參考要點**"]
    lines += [f"- {point}" for point in pending.quiz.reference_points]
    lines += ["", f"_出處：{pending.chunk.location}{pages_markdown(pending.chunk, link)}；"
                  f"掌握度 {state.mastery:.0%}，下次複習 {state.due.astimezone():%m/%d %H:%M}_"]
    return "\n".join(lines)


def is_end(text: str) -> bool:
    return re.sub(r"\s", "", text).lower() in END_WORDS
