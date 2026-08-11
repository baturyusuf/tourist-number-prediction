"""One-time schema migration that preserves and invalidates preliminary experiment rows."""

from __future__ import annotations

import ast
import json

import pandas as pd

from tourism_forecasting.registry import REGISTRY_COLUMNS, initialize_registry


def migrate() -> int:
    path = initialize_registry()
    frame = pd.read_csv(path, dtype="string", keep_default_na=False)
    preliminary = frame["run_id"].eq("")
    marker = (
        "provisional_pre_milestone_run; Git SHA references the intake commit; "
        "mutable artifacts were superseded"
    )
    failure = "provenance_incomplete_pre_milestone"
    for index in frame.index[preliminary]:
        notes = frame.at[index, "notes"]
        if marker not in notes:
            frame.at[index, "notes"] = f"{notes}; {marker}".strip("; ")
        reasons = frame.at[index, "failure_reason"]
        if failure not in reasons:
            frame.at[index, "failure_reason"] = f"{reasons} | {failure}".strip(" |")
        package_versions = frame.at[index, "package_versions"]
        if package_versions.startswith("{") and "'" in package_versions:
            frame.at[index, "package_versions"] = json.dumps(
                ast.literal_eval(package_versions), sort_keys=True, separators=(",", ":")
            )
    temporary = path.with_suffix(".tmp")
    frame[REGISTRY_COLUMNS].to_csv(temporary, index=False)
    temporary.replace(path)
    return int(preliminary.sum())


if __name__ == "__main__":
    print(f"invalidated_preliminary_rows={migrate()}")
