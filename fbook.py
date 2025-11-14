import json
import sys
import glob
import time
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px

import dash
import dash_core_components as dcc
import dash_html_components as html

from PyInquirer import prompt  # type: ignore

import menus


BASE_DIR = Path(__file__).resolve().parent
MESSAGES_DIR = BASE_DIR / "messages"
INBOX_DIR = MESSAGES_DIR / "inbox"
AUTOFILL_PATH = MESSAGES_DIR / "autofill_information.json"


def file_to_list(file_name):
    """Read lines from a text file, stripping whitespace."""
    path = BASE_DIR / file_name
    result = []
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                result.append(line)
    return result


def recursive_lookup(key, data):
    """Find the first value for key in a nested dict structure."""
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            found = recursive_lookup(key, value)
            if found is not None:
                return found
    return None


def get_matchlist(guest_name):
    """
    Find all conversation folders in messages/inbox whose folder name
    contains the normalized guest_name.
    """
    normalized = guest_name.replace(" ", "").lower()
    pattern = str(INBOX_DIR / ("*%s_*" % normalized))
    matchlist = []

    for folder in glob.glob(pattern):
        msg_path = os.path.join(folder, "message_1.json")
        if not os.path.exists(msg_path):
            continue
        with open(msg_path, encoding="utf-8") as f:
            data = json.load(f)
        match_name = recursive_lookup("title", data)
        if not match_name:
            continue
        # crude heuristic to avoid huge noisy chats
        if len(match_name) <= 80:
            matchlist.append(match_name)

    matchlist = sorted(set(matchlist))
    matchlist.append("Quit")
    return matchlist


def get_autofill(value):
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
            entry = d_info[value]
            if isinstance(entry, list) and entry:
                return entry[0]
            if isinstance(entry, str) and entry:
                return entry
    return None


def analyze_name(user_name, match_name, path_pattern):
    """
    Scan all message_*.json files that match path_pattern and accumulate stats.
    """
    t0 = time.perf_counter()
    hour_count = defaultdict(int)    # type: Dict[int, int]
    month_count = defaultdict(int)   # type: Dict[str, int]
    day_count = defaultdict(int)     # type: Dict[str, int]
    day_name_count = defaultdict(int)  # type: Dict[str, int]

    my_message_count = 0
    other_message_count = 0
    first_date = None  # type: Optional[datetime]
    last_date = None   # type: Optional[datetime]

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

    print("\n%s's message count: %d" % (user_name, my_message_count))
    print("%s's message count: %d" % (match_name, other_message_count))
    if num_days:
        print(
            "Spanning %d days (%s – %s)"
            % (
                num_days,
                first_date.strftime("%A %B %d %Y") if first_date else "",
                last_date.strftime("%A %B %d %Y") if last_date else "",
            )
        )
    print("Processed data in %.2f seconds." % (time.perf_counter() - t0))

    return {
        "hour_count": dict(hour_count),
        "month_count": dict(month_count),
        "day_count": dict(day_count),
        "day_name_count": dict(day_name_count),
        "my_message_count": my_message_count,
        "other_message_count": other_message_count,
        "first_date": first_date,
        "last_date": last_date,
    }


def _set_zeroes(obj, fmt):
    """Fill missing dates in the dict with zeros for plotting continuity."""
    if not obj:
        return obj
    keys = list(obj.keys())
    try:
        start = datetime.strptime(min(keys), fmt).date()
        end = date.today()
    except ValueError:
        return obj

    freq = "D" if "%d" in fmt else "MS"
    for d in pd.date_range(start, end, freq=freq):
        key = d.strftime(fmt)
        if key not in obj:
            obj[key] = 0
    return obj


def _show_bar_chart(counts, x_label, y_label, title):
    df = pd.DataFrame.from_dict(counts, orient="index", columns=[y_label])
    df.index.name = x_label
    df = df.sort_index()
    fig = px.bar(df, labels={"index": x_label, y_label: y_label}, title=title)
    _run_dash_app(fig)


def show_monthly_graph(month_count, person_a, person_b):
    month_count = _set_zeroes(month_count, "%Y-%m")
    _show_bar_chart(
        month_count,
        x_label="Month",
        y_label="Message Count",
        title="Monthly message count between %s and %s" % (person_a, person_b),
    )


def show_daily_graph(day_count, person_a, person_b):
    day_count = _set_zeroes(day_count, "%Y-%m-%d")
    _show_bar_chart(
        day_count,
        x_label="Day",
        y_label="Message Count",
        title="Daily message count between %s and %s" % (person_a, person_b),
    )

    max_day = max(day_count, key=day_count.get)
    print("Highest day: %s with %d messages" % (max_day, day_count[max_day]))


def show_hourly_graph(hour_count, person_a, person_b):
    # Ensure we have keys 0–23
    for h in range(24):
        if h not in hour_count:
            hour_count[h] = 0
    counts = {"%02d:00" % h: hour_count[h] for h in range(24)}
    _show_bar_chart(
        counts,
        x_label="Hour of day",
        y_label="Message Count",
        title="Hourly message count between %s and %s" % (person_a, person_b),
    )


def get_common_words(path_pattern):
    dict_of_all_words = {}  # type: Dict[str, int]
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


def get_person_b():
    """
    Prompt for a search string, then prompt again with a disambiguated
    list of conversation titles. Returns the chosen title or None.
    """
    search_name_ans = prompt(menus.name_menu) or {}
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
    choose_name_ans = prompt(choose_name_menu) or {}
    choice = choose_name_ans.get("name_opt")
    if choice == "Quit":
        return None
    return choice


def _run_dash_app(fig):
    """Spin up a very simple Dash app to show a single figure."""
    app = dash.Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1(children="Messenger Analysis"),
            dcc.Graph(id="graph", figure=fig),
        ]
    )
    app.run_server(debug=True)


def main():
    person_a = get_autofill("FULL_NAME") or "You"

    header = "╔════════════════════╗"
    footer = "╚════════════════════╝"
    print(
        "\n\t%s\n\t Facebook Data Parser\n\t Welcome %s!\n\t%s\n"
        % (header, person_a, footer)
    )

    menu_ans = prompt(menus.entry_menu) or {}
    menu_choice = menu_ans.get("menu_opt", "")

    if "Quit" in menu_choice:
        print("Goodbye %s!" % person_a)
        sys.exit(0)

    person_b = get_person_b()
    if not person_b:
        print("No recipient selected. Exiting.")
        sys.exit(0)

    normalized_name = person_b.replace(" ", "").lower()
    path_pattern = str(
        INBOX_DIR / ("%s_*" % normalized_name) / "message_*.json"
    )

    if "Most common words" in menu_choice:
        print("Most common words between %s and %s" % (person_a, person_b))
        get_common_words(path_pattern)
        return

    stats = analyze_name(person_a, person_b, path_pattern)

    graph_ans = prompt(menus.graph_menu) or {}
    if not graph_ans.get("show_graphs"):
        return

    if "Monthly word count" in menu_choice:
        show_monthly_graph(stats["month_count"], person_a, person_b)
    elif "Hourly word count" in menu_choice:
        show_hourly_graph(stats["hour_count"], person_a, person_b)
    elif "Daily word count" in menu_choice:
        show_daily_graph(stats["day_count"], person_a, person_b)
    else:
        # fallback
        show_daily_graph(stats["day_count"], person_a, person_b)


if __name__ == "__main__":
    main()
