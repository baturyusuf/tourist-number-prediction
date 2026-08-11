import json
import subprocess
from pathlib import Path

import pandas as pd

from tourism_forecasting.registry import REGISTRY_COLUMNS, append_experiment, initialize_registry


def test_registry_schema_and_append(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    initialize_registry(path)
    experiment_id = append_experiment(
        {
            "model": "seasonal_naive",
            "forecast_protocol": "one_step_ex_ante",
            "data_checksum": "abc",
        },
        path,
    )
    frame = pd.read_csv(path)
    assert list(frame.columns) == REGISTRY_COLUMNS
    assert frame.loc[0, "experiment_id"] == experiment_id
    assert json.loads(frame.loc[0, "package_versions"])["python"]
    assert isinstance(json.loads(frame.loc[0, "source_state"])["dirty"], bool)


def test_restricted_paths_are_git_ignored() -> None:
    restricted = [
        "data/kaggle/global_terrorism.xlsx",
        "data/kaggle/kaggle.json",
        "data/raw/private.csv",
        "docs/source/private_manuscript.docx",
        ".env",
    ]
    for path in restricted:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path], check=False, capture_output=True
        )
        assert result.returncode == 0, path


def test_license_safe_gtd_aggregate_tables_are_not_hidden_by_gitignore() -> None:
    allowed = [
        "reports/tables/gtd_definition_sensitivity_summary.csv",
        (
            "results/runs/gtd_example/gtd_aggregate/"
            "gtd_predictive_common_sample.csv"
        ),
    ]
    for path in allowed:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path], check=False, capture_output=True
        )
        assert result.returncode == 1, path
    prohibited_near_miss = "reports/tables/gtd_event_rows.csv"
    result = subprocess.run(
        ["git", "check-ignore", "-q", prohibited_near_miss],
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, prohibited_near_miss
