import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import tourism_forecasting.external_validation_2026q1 as external
from tourism_forecasting.registry import REGISTRY_COLUMNS


def _frame() -> pd.DataFrame:
    dates = pd.date_range("2008-01-01", "2025-12-01", freq="MS")
    target = 1_000_000 + 100_000 * np.sin(2 * np.pi * (dates.month - 1) / 12)
    frame = pd.DataFrame(
        {
            "date": dates,
            "target_original_with_missing": target,
        }
    )
    frame.loc[frame["date"].eq("2025-01-01"), "target_original_with_missing"] = 3_000_000
    frame.loc[frame["date"].eq("2025-02-01"), "target_original_with_missing"] = 3_000_000
    frame.loc[frame["date"].eq("2025-03-01"), "target_original_with_missing"] = 3_121_152
    return frame


def _write_core_csv(path: Path) -> None:
    frame = _frame()
    source = pd.DataFrame(
        {
            "Yil-Ay": frame["date"].map(lambda date: f"{date.year}-{date.month}"),
            "Ziyaretci": frame["target_original_with_missing"],
            "USD": 100.0,
            "HICP": 2.0,
            "TREND": 50.0,
        }
    )
    source.to_csv(path, index=False)


def test_release_cutoff_masks_october_through_december_2025() -> None:
    assert external.OFFICIAL_2026_Q1.official_url == (
        "https://veriportali.tuik.gov.tr/tr/press/58142"
    )
    assert external.OFFICIAL_2025_Q1.official_url == (
        "https://veriportali.tuik.gov.tr/tr/press/54155"
    )
    assert external.OFFICIAL_2026_Q1.publication_date == "2026-04-30"
    assert external.OFFICIAL_2026_Q1.departing_visitors_total == 9_258_129
    training = external.release_aware_training_target(_frame())
    assert training.loc["2025-09-01"] == _frame().set_index("date").loc[
        "2025-09-01", "target_original_with_missing"
    ]
    assert training.loc["2025-10-01":"2025-12-01"].isna().all()


def test_seasonal_naive_q1_forecast_matches_official_2025_q1_identity() -> None:
    result = external.evaluate_2026q1_external_validation(
        _frame(), model_names=("seasonal_naive",)
    )
    assert result.loc[0, "quarter_forecast"] == 9_121_152
    assert result.loc[0, "official_quarter_actual"] == 9_258_129
    assert result.loc[0, "quarter_error_forecast_minus_actual"] == -136_977
    assert result.loc[0, "quarter_absolute_error_skill_vs_seasonal_naive"] == 0


def test_external_validation_never_fabricates_monthly_accuracy() -> None:
    result = external.evaluate_2026q1_external_validation(
        _frame(), model_names=("seasonal_naive",)
    )
    forbidden = {"date", "month", "mae", "rmse", "r2", "mape", "monthly_actual"}
    assert forbidden.isdisjoint(result.columns)
    assert set(result["actual_granularity"]) == {"official_quarter_total_only"}
    assert result["interval_status"].str.startswith("omitted").all()


def test_external_validation_builds_hashed_immutable_registry_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    core = tmp_path / "core.csv"
    config = tmp_path / "config.toml"
    table = tmp_path / "reports" / "publication_2026q1_external_validation.csv"
    note = tmp_path / "docs" / "external_validation_2026q1.md"
    runs = tmp_path / "runs"
    registry = tmp_path / "registry.csv"
    _write_core_csv(core)
    config.write_text("[project]\nseed = 1\n", encoding="utf-8")
    monkeypatch.setattr(external, "assert_clean_source_tree", lambda: None)

    artifacts = external.build_2026q1_external_validation_artifacts(
        core_path=core,
        config_path=config,
        table_path=table,
        note_path=note,
        runs_dir=runs,
        registry_path=registry,
    )
    assert all(path.exists() for path in artifacts)
    rows = pd.read_csv(registry, dtype=str, keep_default_na=False)
    assert list(rows.columns) == REGISTRY_COLUMNS
    assert len(rows) == len(external.MODEL_ORDER)
    assert rows["run_id"].nunique() == 1
    assert rows["forecast_protocol"].eq("external_validation_2026q1_quarter_total").all()
    assert rows["failure_reason"].eq("").all()
    registered = json.loads(rows.loc[0, "artifact_paths"])
    assert len(registered) == 2
    for record in registered:
        path = Path(record["path"])
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    metrics = json.loads(rows.loc[0, "aggregate_metrics"])
    assert set(metrics) == {
        "official_quarter_actual",
        "quarter_absolute_error",
        "quarter_absolute_error_skill_vs_seasonal_naive",
        "quarter_absolute_percentage_error",
        "quarter_error_forecast_minus_actual",
        "quarter_forecast",
    }
    assert "monthly" not in json.dumps(metrics).lower()
