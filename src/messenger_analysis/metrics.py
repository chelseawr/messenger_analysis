from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from .data_loader import Message


@dataclass
class ConversationStats:
    hour_count: Dict[int, int]
    day_count: Dict[str, int]
    month_count: Dict[str, int]
    day_name_count: Dict[str, int]
    my_message_count: int
    other_message_count: int
    first_date: datetime | None
    last_date: datetime | None


def compute_basic_stats(messages: Iterable[Message], user_name: str, other_name: str) -> ConversationStats:
    hour_count: Dict[int, int] = defaultdict(int)
    day_count: Dict[str, int] = defaultdict(int)
    month_count: Dict[str, int] = defaultdict(int)
    day_name_count: Dict[str, int] = defaultdict(int)

    my_messages = 0
    other_messages = 0
    first_date: datetime | None = None
    last_date: datetime | None = None

    for msg in messages:
        dt = msg.timestamp
        hour = dt.hour
        day = dt.strftime("%Y-%m-%d")
        month = dt.strftime("%Y-%m")
        day_name = dt.strftime("%A")

        hour_count[hour] += 1
        day_count[day] += 1
        month_count[month] += 1
        day_name_count[day_name] += 1

        if first_date is None or dt < first_date:
            first_date = dt
        if last_date is None or dt > last_date:
            last_date = dt

        if msg.sender == user_name:
            my_messages += 1
        elif msg.sender == other_name:
            other_messages += 1

    return ConversationStats(
        hour_count=dict(hour_count),
        day_count=dict(day_count),
        month_count=dict(month_count),
        day_name_count=dict(day_name_count),
        my_message_count=my_messages,
        other_message_count=other_messages,
        first_date=first_date,
        last_date=last_date,
    )


def most_common_words(messages: Iterable[Message], stopwords: List[str], limit: int = 50) -> List[Tuple[str, int]]:
    stop = {w.lower() for w in stopwords}
    counter: Counter[str] = Counter()

    for msg in messages:
        if not msg.content:
            continue
        for raw in msg.content.split():
            w = raw.lower()
            if not w.isalpha():
                continue
            if w in stop:
                continue
            counter[w] += 1

    return counter.most_common(limit)
