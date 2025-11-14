

def is_input_valid(value):
    """Basic validation for name input."""
    return bool(value) and value.replace(" ", "").isalpha()


def search_filter(value):
    """Normalize name for searching."""
    return value.replace(" ", "").lower()


graph_menu = {
    "type": "confirm",
    "name": "show_graphs",
    "message": "Show graph?",
    "default": False,
}

name_menu = {
    "type": "input",
    "name": "name_input",
    "message": "Who would you like to search for?",
    "validate": is_input_valid,
    "filter": search_filter,
}

entry_menu = {
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
