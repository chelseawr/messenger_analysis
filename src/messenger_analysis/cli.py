from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .data_loader import (
    find_conversations_matching,
    iter_messages_for_conversation,
    load_autofill_name,
)
from .metrics import compute_basic_stats, most_common_words
from .plots import daily_figure, hourly_figure, monthly_figure, run_single_figure_app


def _load_common_words_list() -> list[str]:
    """Load stopwords from a local common_words.txt if present."""
    path = Path("common_words.txt")
    if not path.exists():
        return []
    words: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                words.append(line)
    return words


def _interactive_choice(prompt_text: str, choices: list[str]) -> str:
    print(prompt_text)
    for idx, name in enumerate(choices, start=1):
        print(f"  {idx}. {name}")
    while True:
        raw = input("Enter number: ").strip()
        if not raw.isdigit():
            print("Please enter a number.")
            continue
        i = int(raw)
        if 1 <= i <= len(choices):
            return choices[i - 1]
        print("Out of range, try again.")


def _select_conversation(fragment: str | None = None) -> str | None:
    if not fragment:
        fragment = input("Who would you like to search for? ").strip()
        if not fragment:
            return None

    matches = find_conversations_matching(fragment)
    if not matches:
        print("No conversations matched that input.")
        return None

    if len(matches) == 1:
        print(f"Using only match: {matches[0]}")
        return matches[0]

    matches_with_quit = matches + ["Quit"]
    choice = _interactive_choice("Choose a conversation:", matches_with_quit)
    if choice == "Quit":
        return None
    return choice


def run(
    export_root: str | None,
    person_b_fragment: str | None,
    metric: str | None,
    no_graphs: bool,
) -> None:
    if export_root:
        config.set_export_root(export_root)

    person_a = load_autofill_name() or "You"

    header = "╔════════════════════╗"
    footer = "╚════════════════════╝"
    print(
        f"\n\t{header}\n\t Facebook Messenger Analysis"
        f"\n\t Welcome {person_a}!\n\t{footer}\n"
    )

    conv_title = _select_conversation(person_b_fragment)
    if not conv_title:
        print("No conversation selected. Exiting.")
        sys.exit(1)

    messages = list(iter_messages_for_conversation(conv_title))

    # Default metric if not provided
    if metric is None:
        metric = _interactive_choice(
            "Pick a metric:",
            [
                "monthly",
                "daily",
                "hourly",
                "words",
                "quit",
            ],
        )
        if metric == "quit":
            print("Goodbye!")
            sys.exit(0)

    metric = metric.lower()

    if metric == "words":
        stopwords = _load_common_words_list()
        common = most_common_words(messages, stopwords, limit=50)
        print(f"Most common words in conversation '{conv_title}':")
        for word, count in common:
            print(f"{word}: {count}")
        return

    # Stats-based metrics
    stats = compute_basic_stats(messages, person_a, conv_title)
    print(f"\n{person_a}'s message count: {stats.my_message_count}")
    print(f"{conv_title}'s message count: {stats.other_message_count}")
    if stats.first_date and stats.last_date:
        span = (stats.last_date - stats.first_date).days
        print(
            "Spanning {span} days ({start} – {end})".format(
                span=span,
                start=stats.first_date.strftime("%A %B %d %Y"),
                end=stats.last_date.strftime("%A %B %d %Y"),
            )
        )

    if no_graphs:
        return

    if metric == "monthly":
        fig = monthly_figure(stats, person_a, conv_title)
    elif metric == "hourly":
        fig = hourly_figure(stats, person_a, conv_title)
    else:
        # default to daily
        fig = daily_figure(stats, person_a, conv_title)

    run_single_figure_app(fig)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Facebook Messenger exports.",
    )
    parser.add_argument(
        "--export-root",
        help="Path to the root of the Facebook export (where `messages/` lives). Defaults to CWD.",
    )
    parser.add_argument(
        "--person",
        dest="person_fragment",
        help="Fragment of the other person's name for conversation selection.",
    )
    parser.add_argument(
        "--metric",
        choices=["monthly", "daily", "hourly", "words"],
        help="Metric to display. If omitted, you'll be prompted.",
    )
    parser.add_argument(
        "--no-graphs",
        action="store_true",
        help="Don't start Dash; just print stats or words.",
    )

    args = parser.parse_args(argv)

    run(
        export_root=args.export_root,
        person_b_fragment=args.person_fragment,
        metric=args.metric,
        no_graphs=args.no_graphs,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
