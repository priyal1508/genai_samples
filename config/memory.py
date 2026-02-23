"""Lightweight persistent memory — stores user preferences as JSON."""

import json
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
_MEMORY_FILE = _MEMORY_DIR / "preferences.json"


def _ensure_dir() -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_memory() -> dict:
    """Load saved user preferences from disk. Returns empty dict if none exist."""
    if _MEMORY_FILE.exists():
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    return {}


def save_memory(data: dict) -> None:
    """Persist user preferences to disk (merges with existing)."""
    _ensure_dir()
    existing = load_memory()
    existing.update(data)
    _MEMORY_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def format_memory_context(data: dict) -> str:
    """Format stored preferences as a string to inject into the planner prompt."""
    if not data:
        return ""
    lines = ["## Remembered User Preferences (from previous sessions)"]
    for key, value in data.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)
