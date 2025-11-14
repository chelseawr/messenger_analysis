from __future__ import annotations

from typing import Any, Dict


def is_input_valid(value: str) -> bool:
    # keep behavior close to original, but fix "is not 0" bug
    return bool(value) and value.replace(" ", "").isalpha()


def search_filter(value: str) -> str:
    return value.replace(" ", "").lower()


graph_menu: Dict[str, Any] = {
    "type": "confirm",
    "name": "show_graphs",
    "message": "Show graph?",
    "default": False,
}

name_menu: Dict[str, Any] = {
    "type": "input",
    "name": "name_input",
    "message": "Who would you like to search for?",
    "validate": is_input_valid,
    "filter": search_filter,
}

entry_menu: Dict[str, Any] = {
    "type": "list",
    "name": "menu_opt",
    "message": "Pick a menu option",
    "choices": [
        {"name": "Monthly word count"},
        {"name": "Daily word count"},
        {"name": "Hourly word count"},
        {"name": "Day of week word count"},
        {"name": "Most common words"},
        {"name": "Quit"},
    ],
}
