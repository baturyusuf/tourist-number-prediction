"""Offline 2026-Q1 external validation against a frozen official quarter aggregate."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from tourism_forecasting.baselines import (
    ForecastResult,
    holt_winters,
    seasonal_moving_average,
    seasonal_naive,
    stl_arima,
    theta,
)
from tourism_forecasting.config import load_project_config
from tourism_forecasting.data import load_core_data, sha256_file
from tourism_forecasting.paths import repository_root, resolve_from_root
from tourism_forecasting.registry import (
    append_experiment,
    assert_clean_source_tree,
    new_experiment_id,
)

ORIGIN = pd.Timestamp("2025-12-31")
TARGET_AVAILABLE_THROUGH = pd.Timestamp("2025-09-01")
FORECAST_DATES = pd.date_range("2026-01-01", "2026-03-01", freq="MS")
TARGET_PUBLICATION_DELAY_MONTHS = 3


@dataclass(frozen=True)
class FrozenOfficialQuarterEvidence:
    release_id: int
    publisher: str
    release_title: str
    publication_date: str
    reference_period: str
    departing_visitors_total: int
    target_definition: str
    official_url: str
    accessed_on: str
    role: str


OFFICIAL_2026_Q1 = FrozenOfficialQuarterEvidence(
    release_id=58142,
    publisher="Türkiye İstatistik Kurumu (TÜİK)",
    release_title="Turizm İstatistikleri, I. Çeyrek: Ocak-Mart, 2026",
    publication_date="2026-04-30",
    reference_period="2026-Q1",
    departing_visitors_total=9_258_129,
    target_definition=(
        "Türkiye'den çıkış yapan toplam ziyaretçi: yabancı ziyaretçiler ile yurt dışında "
        "ikamet eden vatandaşlar; geceleyen ve günübirlik ziyaretçiler"
    ),
    official_url="https://veriportali.tuik.gov.tr/tr/press/58142",
    accessed_on="2026-08-11",
    role="external_validation_actual_quarter_total",
)

OFFICIAL_2025_Q1 = FrozenOfficialQuarterEvidence(
    release_id=54155,
    publisher="Türkiye İstatistik Kurumu (TÜİK)",
    release_title="Turizm İstatistikleri, I. Çeyrek: Ocak-Mart, 2025",
    publication_date="2025-04-30",
    reference_period="2025-Q1",
    departing_visitors_total=9_121_152,
    target_definition=OFFICIAL_2026_Q1.target_definition,
    official_url="https://veriportali.tuik.gov.tr/tr/press/54155",
    accessed_on="2026-08-11",
    role="same_definition_identity_check_against_supplied_monthly_sum",
)

MODEL_ORDER = (
    "seasonal_naive",
    "stl_arima",
    "theta",
    "ets_holt_winters",
    "seasonal_moving_average_3",
)


def frozen_evidence_payload() -> dict[str, object]:
    return {
        "evidence_version": "2026q1_v1",
        "actual_2026_q1": asdict(OFFICIAL_2026_Q1),
        "identity_check_2025_q1": asdict(OFFICIAL_2025_Q1),
        "reproduction": "frozen public aggregate; no network request required",
    }


def frozen_evidence_checksum() -> str:
    encoded = json.dumps(
        frozen_evidence_payload(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def release_aware_training_target(frame: pd.DataFrame) -> pd.Series:
    """Return target history as available at the 2025-12-31 fixed origin."""

    dates = pd.DatetimeIndex(pd.to_datetime(frame["date"]))
    target = pd.Series(
        pd.to_numeric(frame["target_original_with_missing"], errors="coerce").to_numpy(),
        index=dates,
        dtype=float,
    ).sort_index()
    target.loc[target.index > TARGET_AVAILABLE_THROUGH] = np.nan
    return target


def _forecast_model(name: str, training: pd.Series) -> ForecastResult:
    if name == "seasonal_naive":
        return seasonal_naive(training, FORECAST_DATES)
    if name == "stl_arima":
        return stl_arima(training, FORECAST_DATES)
    if name == "theta":
        return theta(training, FORECAST_DATES)
    if name == "ets_holt_winters":
        return holt_winters(training, FORECAST_DATES)
    if name == "seasonal_moving_average_3":
        return seasonal_moving_average(training, FORECAST_DATES, seasons=3)
    raise KeyError(f"Unsupported external-validation model: {name}")


def evaluate_2026q1_external_validation(
    frame: pd.DataFrame,
    *,
    run_id: str = "unregistered",
    model_names: tuple[str, ...] = MODEL_ORDER,
) -> pd.DataFrame:
    """Score quarter sums only; monthly official actuals are not reconstructed or scored."""

    supplied_q1_2025 = int(
        frame.loc[
            pd.to_datetime(frame["date"]).between("2025-01-01", "2025-03-01"),
            "target_original_with_missing",
        ].sum()
    )
    if supplied_q1_2025 != OFFICIAL_2025_Q1.departing_visitors_total:
        raise ValueError(
            "Supplied 2025-Q1 monthly target sum does not match frozen TÜİK release 54155: "
            f"{supplied_q1_2025} != {OFFICIAL_2025_Q1.departing_visitors_total}"
        )
    training = release_aware_training_target(frame)
    records: list[dict[str, object]] = []
    for name in model_names:
        result = _forecast_model(name, training)
        if not result.forecast.index.equals(FORECAST_DATES) or result.forecast.isna().any():
            raise RuntimeError(f"{name} did not produce complete January-March 2026 forecasts")
        quarter_forecast = float(result.forecast.sum())
        absolute_error = abs(quarter_forecast - OFFICIAL_2026_Q1.departing_visitors_total)
        records.append(
            {
                "run_id": run_id,
                "forecast_origin": ORIGIN.date().isoformat(),
                "target_available_through": TARGET_AVAILABLE_THROUGH.date().isoformat(),
                "target_publication_delay_months": TARGET_PUBLICATION_DELAY_MONTHS,
                "forecast_period": "2026-Q1",
                "actual_granularity": "official_quarter_total_only",
                "model": result.model,
                "quarter_forecast": quarter_forecast,
                "official_quarter_actual": OFFICIAL_2026_Q1.departing_visitors_total,
                "quarter_error_forecast_minus_actual": (
                    quarter_forecast - OFFICIAL_2026_Q1.departing_visitors_total
                ),
                "quarter_absolute_error": absolute_error,
                "quarter_absolute_percentage_error": (
                    100 * absolute_error / OFFICIAL_2026_Q1.departing_visitors_total
                ),
                "interval_status": (
                    "omitted: monthly forecast-error dependence is not identified for "
                    "quarter-interval aggregation"
                ),
                "notes": result.notes,
            }
        )
    output = pd.DataFrame(records)
    benchmark_error = output.loc[
        output["model"].eq("seasonal_naive"), "quarter_absolute_error"
    ]
    if len(benchmark_error) != 1 or float(benchmark_error.iloc[0]) == 0:
        output["quarter_absolute_error_skill_vs_seasonal_naive"] = np.nan
    else:
        output["quarter_absolute_error_skill_vs_seasonal_naive"] = 1 - (
            output["quarter_absolute_error"] / float(benchmark_error.iloc[0])
        )
    return output


def _path_label(path: Path) -> str:
    try:
        return path.relative_to(repository_root()).as_posix()
    except ValueError:
        return path.as_posix()


def _write_note(path: Path, results: pd.DataFrame, run_id: str) -> None:
    display = results[
        [
            "model",
            "quarter_forecast",
            "official_quarter_actual",
            "quarter_error_forecast_minus_actual",
            "quarter_absolute_error",
            "quarter_absolute_percentage_error",
            "quarter_absolute_error_skill_vs_seasonal_naive",
        ]
    ].copy()
    for column in (
        "quarter_forecast",
        "official_quarter_actual",
        "quarter_error_forecast_minus_actual",
        "quarter_absolute_error",
    ):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")
    display["quarter_absolute_percentage_error"] = display[
        "quarter_absolute_percentage_error"
    ].map(lambda value: f"{value:.3f}%")
    display["quarter_absolute_error_skill_vs_seasonal_naive"] = display[
        "quarter_absolute_error_skill_vs_seasonal_naive"
    ].map(lambda value: f"{value:.2%}" if pd.notna(value) else "NA")
    text = f"""# 2026-Q1 external validation

Run `{run_id}` freezes the official TÜİK 2026-Q1 departing-visitors total of
**{OFFICIAL_2026_Q1.departing_visitors_total:,}** from release
[{OFFICIAL_2026_Q1.release_id}]({OFFICIAL_2026_Q1.official_url}), published
{OFFICIAL_2026_Q1.publication_date}. Release
[{OFFICIAL_2025_Q1.release_id}]({OFFICIAL_2025_Q1.official_url}) reports
{OFFICIAL_2025_Q1.departing_visitors_total:,} for 2025-Q1, exactly matching the supplied January-
March monthly sum and supporting the definition bridge. Both pages were accessed
{OFFICIAL_2026_Q1.accessed_on}; reproduction uses the frozen evidence embedded in source and makes
no network request.

Forecasts use a fixed 2025-12-31 origin and targets available only through 2025-09 under the
three-completed-month delay sensitivity. January-March predictions are summed and compared with the
official quarter total. Monthly official actuals were not independently archived, so no monthly
MAE, RMSE, R², or reconstructed monthly accuracy is reported. Quarter intervals are omitted because
the dependence needed to aggregate monthly forecast uncertainty was not identified.

{display.to_markdown(index=False)}
"""
    path.write_text(text, encoding="utf-8", newline="\n")


def build_2026q1_external_validation_artifacts(
    *,
    core_path: str | Path = "data/raw/turizm_kisi_Reel_HICP_Trend.csv",
    config_path: str | Path = "configs/default.toml",
    table_path: str | Path = "reports/tables/publication_2026q1_external_validation.csv",
    note_path: str | Path = "docs/external_validation_2026q1.md",
    runs_dir: str | Path = "results/runs",
    registry_path: str | Path = "results/experiment_registry.csv",
) -> list[Path]:
    """Build immutable quarter-level artifacts and append one registry row per model."""

    assert_clean_source_tree()
    started = perf_counter()
    run_id = new_experiment_id("external_2026q1")
    config = load_project_config(config_path)
    frame, audit = load_core_data(core_path)
    results = evaluate_2026q1_external_validation(frame, run_id=run_id)

    table = resolve_from_root(table_path)
    note = resolve_from_root(note_path)
    run_root = resolve_from_root(runs_dir) / run_id / "external_validation_2026q1"
    for directory in (table.parent, note.parent, run_root):
        directory.mkdir(parents=True, exist_ok=True)
    results.to_csv(table, index=False)
    _write_note(note, results, run_id)

    immutable_paths: list[Path] = []
    for artifact in (table, note):
        destination = run_root / artifact.name
        shutil.copyfile(artifact, destination)
        immutable_paths.append(destination)
    artifact_records = [
        {"path": _path_label(path), "sha256": sha256_file(path)} for path in immutable_paths
    ]
    data_checksums = {
        "core_csv": audit.sha256,
        "frozen_official_evidence": frozen_evidence_checksum(),
    }
    runtime = perf_counter() - started
    for row in results.to_dict(orient="records"):
        append_experiment(
            {
                "run_id": run_id,
                "config_checksum": config.sha256,
                "data_checksum": data_checksums,
                "target_definition": "departing_visitors_total_original_with_missing",
                "training_window": "2008-01..2025-09 available targets",
                "validation_folds": ["external_2026q1_official_quarter_total"],
                "forecast_horizon": "3_months_aggregated_to_quarter",
                "forecast_protocol": "external_validation_2026q1_quarter_total",
                "feature_block": "B0_univariate",
                "exact_features": {
                    "forecast_origin": ORIGIN.date().isoformat(),
                    "target_available_through": TARGET_AVAILABLE_THROUGH.date().isoformat(),
                    "actual_granularity": "quarter_total_only",
                },
                "model": row["model"],
                "hyperparameters": {"selection": "frozen shortlist; no 2026 outcome tuning"},
                "random_seed": None,
                "per_fold_metrics_path": "",
                "aggregate_metrics": {
                    "quarter_forecast": row["quarter_forecast"],
                    "official_quarter_actual": row["official_quarter_actual"],
                    "quarter_error_forecast_minus_actual": row[
                        "quarter_error_forecast_minus_actual"
                    ],
                    "quarter_absolute_error": row["quarter_absolute_error"],
                    "quarter_absolute_percentage_error": row[
                        "quarter_absolute_percentage_error"
                    ],
                    "quarter_absolute_error_skill_vs_seasonal_naive": row[
                        "quarter_absolute_error_skill_vs_seasonal_naive"
                    ],
                },
                "seasonal_naive_skill": row[
                    "quarter_absolute_error_skill_vs_seasonal_naive"
                ],
                "runtime_seconds": runtime,
                "artifact_paths": artifact_records,
                "notes": (
                    "Official quarter-total external validation; monthly actual accuracy and "
                    "aggregate intervals intentionally not reported."
                ),
                "failure_reason": "",
            },
            registry_path,
        )
    return [table, note, *immutable_paths, resolve_from_root(registry_path)]
