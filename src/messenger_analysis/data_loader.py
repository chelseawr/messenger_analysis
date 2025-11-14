from __future__ import annotations

import glob
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .config import autofill_path, inbox_dir, get_export_root


@dataclass
class Message:
    timestamp: datetime
    sender: str
    conversation_title: str
    content: str | None = None


def load_autofill_name(key: str = "FULL_NAME") -> str | None:
    """Load a value (e.g. FULL_NAME) from autofill_information.json.

    Returns the first non-empty string found for that key, or None.
    """
    path = autofill_path()
    if not path.exists():
        return None

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    for d_info in data.values():
        if not isinstance(d_info, dict):
            continue
        value = d_info.get(key)
        if isinstance(value, list) and value:
            return value[0]
        if isinstance(value, str) and value:
            return value
    return None


def _recursive_lookup(key: str, data: dict) -> str | None:
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            found = _recursive_lookup(key, value)
            if found is not None:
                return found
    return None


def find_conversations_matching(name_fragment: str, max_title_len: int = 80) -> list[str]:
    """Return a sorted list of conversation titles matching a search string.

    The search is done against the folder name and the JSON `title` field.
    """
    inbox_root = inbox_dir()
    if not inbox_root.exists():
        return []

    normalized = name_fragment.replace(" ", "").lower()
    pattern = str(inbox_root / f"*{normalized}_*")
    matches: list[str] = []

    for folder in glob.glob(pattern):
        message_file = Path(folder) / "message_1.json"
        if not message_file.exists():
            continue
        with message_file.open(encoding="utf-8") as f:
            data = json.load(f)
        title = _recursive_lookup("title", data)
        if not title:
            continue
        if len(title) <= max_title_len:
            matches.append(title)

    return sorted(set(matches))


def iter_messages_for_conversation(title: str) -> Iterable[Message]:
    """Yield Message objects for all messages in a given conversation title.

    This uses the folder naming convention from Facebook exports, where
    the folder names include a normalised form of the title.
    """
    inbox_root = inbox_dir()
    normalized = title.replace(" ", "").lower()
    pattern = str(inbox_root / f"{normalized}_*" / "message_*.json")

    for path_str in glob.glob(pattern):
        path = Path(path_str)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        conv_title = data.get("title", title)

        for msg in data.get("messages", []):
            ts = msg.get("timestamp_ms")
            sender = msg.get("sender_name")
            if ts is None or not sender:
                continue

            dt = datetime.fromtimestamp(ts / 1000.0)
            content = msg.get("content")
            yield Message(
                timestamp=dt,
                sender=sender,
                conversation_title=conv_title,
                content=content if isinstance(content, str) else None,
            )
