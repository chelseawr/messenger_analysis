from __future__ import annotations

from pathlib import Path


# Default path to the root of a Facebook export (where `messages/` lives)
DEFAULT_EXPORT_ROOT: Path = Path(".").resolve()

# Folder containing all message threads, relative to export root
INBOX_DIR_REL = Path("messages") / "inbox"

# Path to autofill information file, relative to export root
AUTOFILL_REL = Path("messages") / "autofill_information.json"


def set_export_root(path: str | Path) -> None:
    """Override the default export root at runtime."""
    global DEFAULT_EXPORT_ROOT
    DEFAULT_EXPORT_ROOT = Path(path).resolve()


def get_export_root() -> Path:
    """Return the path to the export root."""
    return DEFAULT_EXPORT_ROOT


def inbox_dir() -> Path:
    return get_export_root() / INBOX_DIR_REL


def autofill_path() -> Path:
    return get_export_root() / AUTOFILL_REL
