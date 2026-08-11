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
