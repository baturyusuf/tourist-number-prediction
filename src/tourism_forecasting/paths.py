"""Repository path helpers that do not depend on the current working directory."""

from __future__ import annotations

from pathlib import Path


def repository_root() -> Path:
    """Return the checkout root for an editable/source installation."""

    return Path(__file__).resolve().parents[2]


def resolve_from_root(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repository_root() / candidate
