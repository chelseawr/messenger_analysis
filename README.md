This is an AI-assisted restructured version of my 2022 messenger analysis tool, packaged as an installable Python module with a simple CLI entry point.

## Requirements

- Python 3.12+
- A Facebook export unzipped so that a `messages/` directory exists
  (the one that contains `inbox/` and `autofill_information.json`).

## Layout

- `src/messenger_analysis/`
  - `config.py` – configuration and export root handling
  - `data_loader.py` – loading and iterating Messenger JSON data
  - `metrics.py` – core statistics and word-frequency helpers
  - `plots.py` – Plotly/Dash plotting helpers
  - `cli.py` – CLI entry point (no PyInquirer; uses argparse + input)
- `tests/`
  - `test_imports.py` – simple smoke test

## Installation (editable)

```bash
python -m venv .venv
# On Windows Git Bash:
source .venv/Scripts/activate
# On cmd.exe:
#   .venv\Scripts\activate
# On PowerShell:
#   .venv\Scripts\Activate.ps1

pip install -e .
```

## Usage

From the project root (where `pyproject.toml` lives) and with your
Facebook export unzipped so that `./messages` exists:

```bash
messenger-analysis
```

This will:

1. Attempt to read your name from `messages/autofill_information.json`.
2. Prompt you to select a conversation (with optional fuzzy fragment).
3. Prompt for a metric if you didn't provide one:
   - `monthly`
   - `daily`
   - `hourly`
   - `words`
4. For `words`, print the most common words in that conversation.
5. For other metrics, print counts and (unless `--no-graphs`) open a
   small Dash app to display the chart.

You can also use it non-interactively, for example:

```bash
messenger-analysis --export-root "D:/exports/facebook"           --person "alice"           --metric daily
```

This will skip prompts where possible.
```
