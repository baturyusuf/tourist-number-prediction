"""Reproduce claims that can be identified unambiguously from supplied evidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tourism_forecasting.data import load_core_data
from tourism_forecasting.metrics import metric_bundle
from tourism_forecasting.paths import resolve_from_root

LEGACY_EXPECTED = {
    "rmse": 184_753.0,
    "mae": 156_550.0,
    "mape": 3.28,
    "r2": 0.9914,
}
LEGACY_ROUNDING_TOLERANCE = {
    "rmse": 0.5,
    "mae": 0.5,
    "mape": 0.005,
    "r2": 0.00005,
}


def reproduce_2025_seasonal_naive(
    *,
    output_dir: str | Path = "results",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame, audit = load_core_data()
    frame = frame.set_index("date")
    test = frame.loc["2025-01-01":"2025-12-01", "target_original_with_missing"]
    forecast = frame["target_original_with_missing"].shift(12).reindex(test.index)
    training = frame.loc[:"2024-12-01", "target_original_with_missing"]
    metrics = metric_bundle(test, forecast, training, seasonal_period=12)
    metric_row = {
        "experiment_id": "repro_legacy_2025_seasonal_naive",
        "protocol": "legacy_2025_observation_availability_fixed_origin",
        "model": "seasonal_naive",
        "target_definition": "target_original_with_missing",
        "train_start": training.index.min().strftime("%Y-%m"),
        "train_end": training.index.max().strftime("%Y-%m"),
        "test_start": test.index.min().strftime("%Y-%m"),
        "test_end": test.index.max().strftime("%Y-%m"),
        "data_sha256": audit.sha256,
        **metrics,
    }
    metrics_frame = pd.DataFrame([metric_row])
    forecasts = pd.DataFrame(
        {
            "date": test.index.strftime("%Y-%m-%d"),
            "actual": test.to_numpy(),
            "forecast": forecast.to_numpy(),
            "error": forecast.to_numpy() - test.to_numpy(),
            "absolute_percentage_error": (forecast.to_numpy() - test.to_numpy()).__abs__()
            / test.to_numpy()
            * 100,
        }
    )
    differences = pd.DataFrame(
        [
            {
                "claim": f"seasonal_naive_2025_{metric}",
                "reported_or_preliminary": expected,
                "reproduced": metrics[metric],
                "absolute_difference": metrics[metric] - expected,
                "status": (
                    "reproduced_with_rounding"
                    if abs(metrics[metric] - expected) <= LEGACY_ROUNDING_TOLERANCE[metric]
                    else "not_reproduced_at_reported_precision"
                ),
            }
            for metric, expected in LEGACY_EXPECTED.items()
        ]
        + [
            {
                "claim": "manuscript_best_sarimax_mape",
                "reported_or_preliminary": 4.01,
                "reproduced": pd.NA,
                "absolute_difference": pd.NA,
                "status": "pending_exact_configuration_reconstruction",
            },
            {
                "claim": "manuscript_lagged_xgboost_mape",
                "reported_or_preliminary": 5.46,
                "reproduced": pd.NA,
                "absolute_difference": pd.NA,
                "status": "pending_exact_configuration_reconstruction",
            },
        ]
    )
    destination = resolve_from_root(output_dir)
    (destination / "forecasts").mkdir(parents=True, exist_ok=True)
    metrics_frame.to_csv(destination / "reproduction_metrics.csv", index=False)
    forecasts.to_csv(
        destination / "forecasts" / "reproduction_2025_seasonal_naive.csv", index=False
    )
    differences.to_csv(destination / "reproduction_differences.csv", index=False)

    report = f"""# Reproduction report

## Reproduced benchmark

The supplied core CSV has SHA-256 `{audit.sha256}`. Training ends in December 2024 and the
forecast for each month of 2025 is the observed target exactly 12 months earlier. No realized
2025 target or exogenous value is consumed.

This legacy calculation assumes the complete 2024 target vector was available at the
31 December 2024 origin. Because a historical issue-date archive was not supplied, it is an
observation-availability reproduction, not the confirmatory operational ex-ante protocol.

| Metric | Reproduced value |
|---|---:|
| RMSE | {metrics['rmse']:,.6f} |
| MAE | {metrics['mae']:,.6f} |
| MAPE | {metrics['mape']:.8f}% |
| sMAPE | {metrics['smape']:.8f}% |
| WAPE | {metrics['wape']:.8f}% |
| MASE | {metrics['mase']:.8f} |
| RMSSE | {metrics['rmsse']:.8f} |
| R² | {metrics['r2']:.10f} |
| Bias (forecast - actual) | {metrics['bias']:,.6f} |

The preliminary RMSE, MAE, MAPE, and R² are reproduced to the stated rounding precision.
This is a single favorable legacy year and is not evidence that a model is generally superior.

## Manuscript model reconstruction status

The reported SARIMAX and XGBoost scores remain unverified until the manuscript's blank feature
labels, exact orders/hyperparameters, preprocessing fit scope, lag-selection process, teacher
forcing behavior, and future-exogenous use are reconstructed. The pipeline records that gap
rather than selecting configurations on 2025 until the reported values appear.
"""
    (destination / "reproduction_report.md").write_text(report, encoding="utf-8")
    return metrics_frame, forecasts, differences
