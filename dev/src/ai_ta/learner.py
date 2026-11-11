"""Learner model: an append-only log of practice events, and state derived from it.

The log is the only source of truth. Mastery and review dates are recomputed from it,
so changing the scheduling or mastery rule never loses data (research/synthesis/T6.md).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from fsrs import Card, Rating, Scheduler

from . import config

EVENTS = config.LEARNER_DIR / "events.jsonl"
LABEL_SCORE = {"正確": 1.0, "部分正確": 0.5, "矛盾": 0.0, "離題": 0.0, "不知道": 0.0}
RECENT = 5  # attempts that count toward mastery


@dataclass(frozen=True)
class Event:
    knowledge_point: str   # heading chunk id of the note section
    location: str
    bloom: str
    question: str
    answer: str
    label: str
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass
class PointState:
    knowledge_point: str
    location: str
    attempts: int = 0
    labels: list[str] = field(default_factory=list)
    card: Card = field(default_factory=Card)

    @property
    def mastery(self) -> float:
        """Recency-weighted share of correct answers over the last few attempts."""
        recent = self.labels[-RECENT:]
        if not recent:
            return 0.0
        weights = range(1, len(recent) + 1)
        return sum(w * LABEL_SCORE.get(label, 0.0) for w, label in zip(weights, recent)) / sum(weights)

    @property
    def due(self) -> datetime:
        return self.card.due


def record(event: Event, path: Path = EVENTS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def load_events(path: Path = EVENTS) -> list[Event]:
    if not path.exists():
        return []
    return [Event(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def derive_state(events: list[Event]) -> dict[str, PointState]:
    # Fuzzing off, so replaying the same log always gives the same schedule.
    scheduler = Scheduler(enable_fuzzing=False)
    states: dict[str, PointState] = {}
    for event in sorted(events, key=lambda e: e.time):
        state = states.setdefault(event.knowledge_point, PointState(event.knowledge_point, event.location))
        rating = Rating.Good if event.label == "正確" else Rating.Again  # two levels only (architecture.md 4.4)
        state.card, _ = scheduler.review_card(state.card, rating, review_datetime=datetime.fromisoformat(event.time))
        state.attempts += 1
        state.labels.append(event.label)
    return states


def due_points(states: dict[str, PointState], now: datetime | None = None) -> list[PointState]:
    now = now or datetime.now(timezone.utc)
    return sorted((s for s in states.values() if s.due <= now), key=lambda s: s.due)


def weak_points(states: dict[str, PointState], threshold: float = 0.5, min_attempts: int = 2) -> list[PointState]:
    """The error notebook: points answered at least twice with low recent mastery."""
    weak = [s for s in states.values() if s.attempts >= min_attempts and s.mastery < threshold]
    return sorted(weak, key=lambda s: s.mastery)
