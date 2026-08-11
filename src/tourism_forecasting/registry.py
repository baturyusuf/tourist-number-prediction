"""Append-only, machine-readable experiment registry."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pandas as pd

from tourism_forecasting.paths import repository_root, resolve_from_root

REGISTRY_COLUMNS = [
    "experiment_id",
    "timestamp_utc",
    "git_sha",
    "source_state",
    "run_id",
    "config_checksum",
    "data_checksum",
    "target_definition",
    "training_window",
    "validation_folds",
    "forecast_horizon",
    "forecast_protocol",
    "feature_block",
    "exact_features",
    "model",
    "hyperparameters",
    "random_seed",
    "package_versions",
    "per_fold_metrics_path",
    "aggregate_metrics",
    "seasonal_naive_skill",
    "runtime_seconds",
    "artifact_paths",
    "notes",
    "failure_reason",
]


def current_git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository_root(), text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def current_source_state() -> dict[str, Any]:
    """Fingerprint source/config changes while excluding generated research artifacts."""

    scoped = [
        "src",
        "scripts",
        "configs",
        "tests",
        "pyproject.toml",
        "requirements.lock",
        "Makefile",
    ]
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--binary", "HEAD", "--", *scoped],
            cwd=repository_root(),
        )
        untracked_text = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "--", *scoped],
            cwd=repository_root(),
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {"available": False, "dirty": None}
    untracked = sorted(line for line in untracked_text.splitlines() if line)
    digest = hashlib.sha256()
    digest.update(diff)
    for relative in untracked:
        path = repository_root() / relative
        digest.update(relative.encode("utf-8"))
        if path.is_file():
            digest.update(path.read_bytes())
    return {
        "available": True,
        "dirty": bool(diff or untracked),
        "diff_sha256": digest.hexdigest(),
        "untracked_source_files": untracked,
    }


def assert_clean_source_tree() -> None:
    state = current_source_state()
    if not state.get("available"):
        raise RuntimeError("Cannot verify the Git source tree")
    if state.get("dirty"):
        raise RuntimeError(
            "Source/config tree is dirty; commit implementation changes before a valid run"
        )


def package_versions(packages: tuple[str, ...] = ()) -> dict[str, str]:
    selected = packages or (
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "statsmodels",
        "xgboost",
    )
    result = {"python": platform.python_version()}
    for package in selected:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not-installed"
    return result


def new_experiment_id(prefix: str = "exp") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}"


def _serialize(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, str | int | float | bool):
        return value
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def append_experiment(
    record: Mapping[str, Any],
    path: str | Path = "results/experiment_registry.csv",
) -> str:
    destination = resolve_from_root(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    experiment_id = str(record.get("experiment_id") or new_experiment_id())
    raw_record: dict[str, Any] = {column: "" for column in REGISTRY_COLUMNS}
    raw_record.update(
        {
            "experiment_id": experiment_id,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "git_sha": current_git_sha(),
            "source_state": current_source_state(),
            "package_versions": package_versions(),
        }
    )
    unknown = sorted(set(record) - set(REGISTRY_COLUMNS))
    if unknown:
        raise ValueError(f"Unknown experiment-registry columns: {unknown}")
    raw_record.update(record)
    normalized = {column: _serialize(raw_record[column]) for column in REGISTRY_COLUMNS}
    new_row = pd.DataFrame([normalized], columns=REGISTRY_COLUMNS)
    initialize_registry(destination)
    if destination.exists() and destination.stat().st_size:
        existing = pd.read_csv(destination, dtype="string", keep_default_na=False)
        if list(existing.columns) != REGISTRY_COLUMNS:
            raise ValueError("Experiment registry schema does not match the current contract")
        if experiment_id in set(existing["experiment_id"]):
            raise ValueError(f"Duplicate experiment_id: {experiment_id}")
        combined = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
    else:
        combined = new_row
    temporary = destination.with_suffix(".tmp")
    combined.to_csv(temporary, index=False)
    temporary.replace(destination)
    return experiment_id


def initialize_registry(path: str | Path = "results/experiment_registry.csv") -> Path:
    destination = resolve_from_root(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        pd.DataFrame(columns=REGISTRY_COLUMNS).to_csv(destination, index=False)
    elif destination.stat().st_size:
        existing = pd.read_csv(destination, dtype="string", keep_default_na=False)
        unknown = sorted(set(existing.columns) - set(REGISTRY_COLUMNS))
        if unknown:
            raise ValueError(f"Experiment registry contains unknown columns: {unknown}")
        if list(existing.columns) != REGISTRY_COLUMNS:
            for column in REGISTRY_COLUMNS:
                if column not in existing:
                    existing[column] = ""
            temporary = destination.with_suffix(".tmp")
            existing[REGISTRY_COLUMNS].to_csv(temporary, index=False)
            temporary.replace(destination)
    return destination
