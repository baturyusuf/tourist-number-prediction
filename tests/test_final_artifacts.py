import os
from pathlib import Path

import numpy as np
import pandas as pd

from tourism_forecasting.final_artifacts import (
    build_publication_artifacts,
    load_forecasts,
    locate_latest_immutable_forecasts,
    paired_loss_comparisons,
    pooled_metrics,
)


def _synthetic_forecasts(periods: int = 24) -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", periods=periods, freq="MS")
    records: list[dict[str, object]] = []
    for index, date in enumerate(dates):
        actual = 1_000.0 + 50 * date.month + 5 * index
        benchmark = actual + (-1 if index % 2 else 1) * 100
        for model, forecast, has_interval in (
            ("seasonal_naive", benchmark, True),
            ("better_model", actual + (-1 if index % 2 else 1) * 25, True),
            ("partial_model", actual + 40, False),
        ):
            missing = model == "partial_model" and index == 0
            value = np.nan if missing else forecast
            records.append(
                {
                    "run_id": "run_synthetic",
                    "fold_id": f"fold_{date.year}",
                    "protocol": "fixed_origin_12m_ex_ante",
                    "model": model,
                    "date": date,
                    "horizon": date.month,
                    "actual": actual,
                    "forecast": value,
                    "lower_95": value - 120 if has_interval and not missing else np.nan,
                    "upper_95": value + 120 if has_interval and not missing else np.nan,
                    "seasonal_naive_forecast": benchmark,
                    "year": date.year,
                    "month": date.month,
                    "regime": "recovery" if date.year == 2022 else "normalization",
                    "full_evaluable": not missing,
                    "comparable_to_seasonal_naive": not missing,
                }
            )
    return pd.DataFrame(records)


def test_latest_forecast_locator_ignores_mutable_alias(tmp_path: Path) -> None:
    old = tmp_path / "runs" / "run_old" / "forecasts" / "rolling_origin_forecasts.csv"
    new = tmp_path / "runs" / "run_new" / "forecasts" / "rolling_origin_forecasts.csv"
    mutable = tmp_path / "forecasts" / "rolling_origin_forecasts.csv"
    for path in (old, new, mutable):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    os.utime(old, ns=(1_000_000_000, 1_000_000_000))
    os.utime(new, ns=(2_000_000_000, 2_000_000_000))
    os.utime(mutable, ns=(3_000_000_000, 3_000_000_000))
    assert locate_latest_immutable_forecasts(tmp_path) == new


def test_full_support_metrics_and_paired_comparisons() -> None:
    frame = _synthetic_forecasts()
    metrics = pooled_metrics(frame)
    partial = metrics.loc[metrics["model"] == "partial_model"].iloc[0]
    assert partial["observations"] == 23
    assert partial["support"] == "model_full_evaluable_support"

    comparisons = paired_loss_comparisons(frame, bootstrap_repetitions=100, seed=7)
    absolute = comparisons.loc[
        (comparisons["model"] == "better_model") & (comparisons["loss"] == "absolute")
    ].iloc[0]
    assert absolute["observations"] == 24
    assert absolute["dm_hac_lags"] == 11
    assert absolute["mean_loss_difference_model_minus_benchmark"] < 0
    assert np.isclose(absolute["relative_skill_vs_seasonal_naive"], 0.75)
    repeated = paired_loss_comparisons(frame, bootstrap_repetitions=100, seed=7)
    pd.testing.assert_frame_equal(comparisons, repeated)


def test_build_publication_artifacts_from_explicit_synthetic_file(tmp_path: Path) -> None:
    source = tmp_path / "runs" / "run_synthetic" / "forecasts" / "rolling_origin_forecasts.csv"
    source.parent.mkdir(parents=True)
    _synthetic_forecasts().to_csv(source, index=False)
    loaded, resolved = load_forecasts(source)
    assert resolved == source
    assert len(loaded) == 72

    artifacts = build_publication_artifacts(
        source,
        tables_dir=tmp_path / "tables",
        figures_dir=tmp_path / "figures",
        bootstrap_repetitions=50,
    )
    assert len(artifacts.tables) == 6
    assert len(artifacts.figures) == 10
    assert all(path.is_file() and path.stat().st_size > 0 for path in artifacts.tables)
    assert all(path.is_file() and path.stat().st_size > 0 for path in artifacts.figures)
    horizon = pd.read_csv(tmp_path / "tables" / "publication_metrics_by_horizon_full_support.csv")
    assert set(horizon["horizon"]) == set(range(1, 13))
