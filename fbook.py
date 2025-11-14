from __future__ import annotations

import json
import sys
import glob
import time
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from dash import Dash, dcc, html  # modern Dash import style
import plotly.express as px
from PyInquirer import prompt  # type: ignore

import menus


BASE_DIR = Path(__file__).resolve().parent
MESSAGES_DIR = BASE_DIR / "messages"
INBOX_DIR = MESSAGES_DIR / "inbox"
AUTOFILL_PATH = MESSAGES_DIR / "autofill_information.json"


def file_to_list(file_name: str) -> list[str]:
    """Read lines from a text file, stripping whitespace."""
    path = BASE_DIR / file_name
    result: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                result.append(line)
    return result


def recursive_lookup(key: str, data: dict) -> str | None:
    """Find the first value for key in a nested dict structure."""
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            found = recursive_lookup(key, value)
            if found is not None:
                return found
    return None


def get_matchlist(guest_name: str) -> list[str]:
    """
    Find all conversation folders in messages/inbox whose folder name
    contains the normalized guest_name.
    """
    normalized = guest_name.replace(" ", "").lower()
    pattern = str(INBOX_DIR / f"*{normalized}_*")
    matchlist: list[str] = []

    for folder in glob.glob(pattern):
        # Each conversation folder should contain message_1.json
        msg_path = os.path.join(folder, "message_1.json")
        if not os.path.exists(msg_path):
            continue
        with open(msg_path, encoding="utf-8") as f:
            data = json.load(f)
        match_name = recursive_lookup("title", data)
        if not match_name:
            continue
        # crude heuristic to avoid huge group chats
        if len(match_name) <= 20:
            matchlist.append(match_name)

    matchlist = sorted(set(matchlist))
    matchlist.append("Quit")
    return matchlist


def get_autofill(value: str) -> str | None:
    """
    Look up a value (e.g. FULL_NAME) from messages/autofill_information.json.
    Returns the first match or None.
    """
    if not AUTOFILL_PATH.exists():
        return None
    with AUTOFILL_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for d_info in data.values():
        if not isinstance(d_info, dict):
            continue
        if value in d_info and d_info[value]:
            # original code took the first element
            return d_info[value][0]
    return None


@dataclass
class MessageStats:
    hour_count: Dict[int, int]
    month_count: Dict[str, int]
    day_count: Dict[str, int]
    day_name_count: Dict[str, int]
    my_message_count: int
    other_message_count: int
    first_date: datetime | None
    last_date: datetime | None


def analyze_name(
    user_name: str, match_name: str, path_pattern: str
) -> MessageStats:
    """
    Scan all message_*.json files that match path_pattern and accumulate stats.
    """
    t0 = time.perf_counter()
    hour_count: Dict[int, int] = defaultdict(int)
    month_count: Dict[str, int] = defaultdict(int)
    day_count: Dict[str, int] = defaultdict(int)
    day_name_count: Dict[str, int] = defaultdict(int)

    my_message_count = 0
    other_message_count = 0
    first_date: datetime | None = None
    last_date: datetime | None = None

    for path in glob.glob(path_pattern):
        with open(path, encoding="utf-8") as json_file:
            data = json.load(json_file)

        for message in data.get("messages", []):
            ts = message.get("timestamp_ms")
            if ts is None:
                continue
            dt = datetime.fromtimestamp(ts / 1000.0)
            month = dt.strftime("%Y-%m")
            day = dt.strftime("%Y-%m-%d")
            day_name = dt.strftime("%A")
            hour = dt.hour

            hour_count[hour] += 1
            day_name_count[day_name] += 1
            day_count[day] += 1
            month_count[month] += 1

            if first_date is None or dt < first_date:
                first_date = dt
            if last_date is None or dt > last_date:
                last_date = dt

            sender = message.get("sender_name")
            if sender == user_name:
                my_message_count += 1
            elif sender == match_name:
                other_message_count += 1

    if first_date and last_date:
        num_days = (last_date - first_date).days
    else:
        num_days = 0

    print(f"\n{user_name}'s message count: {my_message_count}")
    print(f"{match_name}'s message count: {other_message_count}")
    if num_days:
        print(
            f"Spanning {num_days} days "
            f"({first_date:%A %B %d %Y} – {last_date:%A %B %d %Y})"
        )
    print(f"Processed data in {time.perf_counter() - t0:.2f} seconds.")

    return MessageStats(
        hour_count=hour_count,
        month_count=month_count,
        day_count=day_count,
        day_name_count=day_name_count,
        my_message_count=my_message_count,
        other_message_count=other_message_count,
        first_date=first_date,
        last_date=last_date,
    )


def _set_zeroes(obj: Dict[str, int], fmt: str) -> Dict[str, int]:
    """Fill missing dates in the dict with zeros for plotting continuity."""
    if not obj:
        return obj
    keys = list(obj.keys())
    # assume keys are date-like strings compatible with the given format
    try:
        start = datetime.strptime(min(keys), fmt).date()
        end = date.today()
    except ValueError:
        # if parsing fails, just return original
        return obj

    rng = pd.date_range(start, end, freq="D" if "%d" in fmt else "MS")
    for d in rng:
        key = d.strftime(fmt)
        obj.setdefault(key, 0)
    return obj


def _show_bar_chart(
    counts: Dict, x_label: str, y_label: str, title: str
) -> None:
    df = pd.DataFrame.from_dict(counts, orient="index", columns=[y_label])
    df.index.name = x_label
    df = df.sort_index()
    fig = px.bar(df, labels={"index": x_label, y_label: y_label}, title=title)
    _run_dash_app(fig)


def show_monthly_graph(
    month_count: Dict[str, int], person_a: str, person_b: str
) -> None:
    month_count = _set_zeroes(month_count, "%Y-%m")
    _show_bar_chart(
        month_count,
        x_label="Month",
        y_label="Message Count",
        title=f"Monthly message count between {person_a} and {person_b}",
    )


def show_daily_graph(
    day_count: Dict[str, int], person_a: str, person_b: str
) -> None:
    day_count = _set_zeroes(day_count, "%Y-%m-%d")
    _show_bar_chart(
        day_count,
        x_label="Day",
        y_label="Message Count",
        title=f"Daily message count between {person_a} and {person_b}",
    )

    max_day = max(day_count, key=day_count.get)
    print(f"Highest day: {max_day} with {day_count[max_day]} messages")


def show_hourly_graph(
    hour_count: Dict[int, int], person_a: str, person_b: str
) -> None:
    # Ensure we have keys 0–23
    for h in range(24):
        hour_count.setdefault(h, 0)
    # convert to string labels
    counts = {f"{h:02d}:00": c for h, c in hour_count.items()}
    _show_bar_chart(
        counts,
        x_label="Hour of day",
        y_label="Message Count",
        title=f"Hourly message count between {person_a} and {person_b}",
    )


def get_common_words(path_pattern: str) -> None:
    dict_of_all_words: Dict[str, int] = {}
    common_word_list = set(file_to_list("common_words.txt"))

    for path in glob.glob(path_pattern):
        with open(path, encoding="utf-8") as json_file:
            data = json.load(json_file)
        for message in data.get("messages", []):
            content = message.get("content")
            if not isinstance(content, str):
                continue
            for word in content.split():
                w = word.lower()
                if w in common_word_list:
                    continue
                if not w.isalpha():
                    continue
                dict_of_all_words[w] = dict_of_all_words.get(w, 0) + 1

    sorted_words = sorted(
        dict_of_all_words, key=dict_of_all_words.get, reverse=True
    )
    print("\nMost common words sent:")
    print(sorted_words[:50])


def get_person_b() -> str | None:
    """
    Prompt for a search string, then prompt again with a disambiguated
    list of conversation titles. Returns the chosen title or None.
    """
    search_name_ans = prompt(menus.name_menu)
    name_input = search_name_ans.get("name_input")
    if not name_input:
        return None

    matchlist = get_matchlist(name_input)
    if not matchlist:
        print("No conversations matched that input.")
        return None

    choose_name_menu = {
        "type": "list",
        "name": "name_opt",
        "message": "Choose a conversation:",
        "choices": matchlist,
    }
    choose_name_ans = prompt(choose_name_menu)
    choice = choose_name_ans.get("name_opt")
    if choice == "Quit":
        return None
    return choice


def _run_dash_app(fig) -> None:
    """Spin up a very simple Dash app to show a single figure."""
    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="Messenger Analysis"),
            dcc.Graph(id="graph", figure=fig),
        ]
    )
    app.run_server(debug=True)


def main() -> None:
    person_a = get_autofill("FULL_NAME") or "You"

    header = "╔════════════════════╗"
    footer = "╚════════════════════╝"
    print(
        f"\n\t{header}\n\t Facebook Data Parser"
        f"\n\t Welcome {person_a}!\n\t{footer}\n"
    )

    menu_ans = prompt(menus.entry_menu)
    menu_choice = menu_ans.get("menu_opt", "")

    if "Quit" in menu_choice:
        print(f"Goodbye {person_a}!")
        sys.exit(0)

    person_b = get_person_b()
    if not person_b:
        print("No recipient selected. Exiting.")
        sys.exit(0)

    # facebook uses folder names like "<normalized_name>_randomid"
    normalized_name = person_b.replace(" ", "").lower()
    path_pattern = str(INBOX_DIR / f"{normalized_name}_*" / "message_*.json")

    if "Most common words" in menu_choice:
        print(f"Most common words between {person_a} and {person_b}")
        get_common_words(path_pattern)
        return

    if any(
        choice in menu_choice
        for choice in ("word count", "Monthly", "Hourly", "Daily", "Day of week")
    ):
        stats = analyze_name(person_a, person_b, path_pattern)
        graph_ans = prompt(menus.graph_menu)
        if not graph_ans.get("show_graphs"):
            return

        if "Monthly word count" in menu_choice:
            show_monthly_graph(stats.month_count, person_a, person_b)
        elif "Hourly word count" in menu_choice:
            show_hourly_graph(stats.hour_count, person_a, person_b)
        elif "Daily word count" in menu_choice:
            show_daily_graph(stats.day_count, person_a, person_b)
        else:
            # simple fallback – you could add a real "day of week" chart here
            show_daily_graph(stats.day_count, person_a, person_b)


if __name__ == "__main__":
    main()
