"""Typed access to the single TOML configuration used by every workflow."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tourism_forecasting.data import sha256_file
from tourism_forecasting.paths import resolve_from_root


@dataclass(frozen=True)
class ProjectConfig:
    path: Path
    values: dict[str, Any]
    sha256: str

    def section(self, name: str) -> dict[str, Any]:
        value = self.values.get(name)
        if not isinstance(value, dict):
            raise KeyError(f"Missing configuration section: {name}")
        return value


def load_project_config(path: str | Path = "configs/default.toml") -> ProjectConfig:
    source = resolve_from_root(path)
    with source.open("rb") as handle:
        values = tomllib.load(handle)
    return ProjectConfig(source, values, sha256_file(source))
