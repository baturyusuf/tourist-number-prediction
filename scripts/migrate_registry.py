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
        "mutable artifacts were superseded and their stale references were cleared"
    )
    failure = "provenance_incomplete_pre_milestone"
    for index in frame.index[preliminary]:
        notes = frame.at[index, "notes"]
        if marker not in notes:
            frame.at[index, "notes"] = f"{notes}; {marker}".strip("; ")
        reasons = frame.at[index, "failure_reason"]
        if failure not in reasons:
            frame.at[index, "failure_reason"] = f"{reasons} | {failure}".strip(" |")
        # These preliminary rows pointed at shared compatibility files that were overwritten by
        # later runs. Preserve the rows and their recorded metrics, but never imply that a mutable
        # path still reproduces them.
        frame.at[index, "per_fold_metrics_path"] = ""
        frame.at[index, "artifact_paths"] = "[]"
        package_versions = frame.at[index, "package_versions"]
        if package_versions.startswith("{") and "'" in package_versions:
            frame.at[index, "package_versions"] = json.dumps(
                ast.literal_eval(package_versions), sort_keys=True, separators=(",", ":")
            )
    invalid_gtd_reasons = {
        "gtd_20260811T165245Z_85f099db": (
            "superseded_gtd_generator_wording_error",
            "Run invalidated before publication: generated method note contradicted its "
            "recorded bootstrap interval; corrected clean-source rerun retained separately",
        ),
        "gtd_20260811T171305Z_f6039b77": (
            "superseded_publication_figure_layout",
            "Run invalidated before publication: generated aggregate figures had overlapping "
            "source notes; corrected clean-source rerun retained separately",
        ),
        "gtd_20260811T171833Z_a4e00dcf": (
            "superseded_publication_figure_layout_engine",
            "Run invalidated before publication: the global constrained-layout engine rejected "
            "the reserved footer space; corrected clean-source rerun retained separately",
        ),
        "gtd_20260811T172103Z_857bb696": (
            "superseded_publication_figure_layout_engine",
            "Run invalidated before publication: disabling the layout engine after figure "
            "creation restored the global constrained engine; corrected clean-source rerun "
            "retained separately",
        ),
    }
    invalid_gtd = frame["run_id"].isin(invalid_gtd_reasons)
    for index in frame.index[invalid_gtd]:
        invalid_gtd_failure, invalid_gtd_marker = invalid_gtd_reasons[
            frame.at[index, "run_id"]
        ]
        notes = frame.at[index, "notes"]
        if invalid_gtd_marker not in notes:
            frame.at[index, "notes"] = f"{notes}; {invalid_gtd_marker}".strip("; ")
        reasons = frame.at[index, "failure_reason"]
        if invalid_gtd_failure not in reasons:
            frame.at[index, "failure_reason"] = (
                f"{reasons} | {invalid_gtd_failure}".strip(" |")
            )
        frame.at[index, "artifact_paths"] = "[]"
    temporary = path.with_suffix(".tmp")
    frame[REGISTRY_COLUMNS].to_csv(temporary, index=False)
    temporary.replace(path)
    return int(preliminary.sum() + invalid_gtd.sum())


if __name__ == "__main__":
    print(f"migrated_or_invalidated_rows={migrate()}")
