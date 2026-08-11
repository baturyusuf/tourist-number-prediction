"""Publication tables and figures from an immutable rolling-origin forecast run.

Descriptive metrics use each model's full evaluable support.  Model comparisons
use only observations paired with the seasonal-naive benchmark, keeping the two
estimands deliberately separate.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from tourism_forecasting.comparison import (
    diebold_mariano,
    moving_block_bootstrap_loss_difference,
)
from tourism_forecasting.metrics import (
    bias,
    interval_coverage,
    mae,
    mape,
    r2,
    relative_skill,
    rmse,
    smape,
    wape,
    winkler_score,
)
from tourism_forecasting.paths import resolve_from_root
from tourism_forecasting.reporting import configure_plotting, normalize_svg

BENCHMARK_MODEL = "seasonal_naive"
FORECAST_FILENAME = "rolling_origin_forecasts.csv"
SOURCE_NOTE = (
    "Source: immutable rolling-origin forecast run; calculations by the reproducible " "pipeline."
)

PROTOCOL_LABELS = {
    "fixed_origin_12m_ex_ante": "Fixed-origin 12-month ex ante",
    "one_step_ex_ante": "One-step ex ante",
}
MODEL_LABELS = {
    "seasonal_naive": "Seasonal naive",
    "same_month_mean": "Same-month mean",
    "seasonal_moving_average_3": "Seasonal moving average (3 years)",
    "ets_holt_winters": "ETS / Holt-Winters",
    "theta": "Theta",
    "stl_arima_111": "STL + ARIMA(1,1,1)",
    "ridge_recursive_b0": "Ridge (B0, recursive)",
    "hist_gradient_boosting_recursive_b0": "Histogram boosting (B0, recursive)",
}
REGIME_LABELS = {
    "pre_pandemic": "Pre-pandemic",
    "pandemic_shock": "Pandemic shock",
    "recovery": "Recovery",
    "normalization": "Normalization",
}

REQUIRED_COLUMNS = {
    "fold_id",
    "protocol",
    "model",
    "date",
    "horizon",
    "actual",
    "forecast",
    "year",
    "month",
    "regime",
}


@dataclass(frozen=True)
class PublicationArtifacts:
    """Paths and model shortlist produced by :func:`build_publication_artifacts`."""

    forecast_path: Path
    tables: tuple[Path, ...]
    figures: tuple[Path, ...]
    shortlist: tuple[str, ...]


def locate_latest_immutable_forecasts(results_root: str | Path = "results") -> Path:
    """Return the latest registry-verified forecast, with a filesystem fallback.

    A clean-source registry row and its recorded SHA-256 take priority, so merely touching or
    copying an older run cannot redirect publication outputs. Mutable compatibility aliases under
    ``results/forecasts`` are never searched. The modification-time fallback exists only for
    isolated/synthetic runs without a registry.
    """

    root = resolve_from_root(results_root)
    registry_path = root / "experiment_registry.csv"
    if registry_path.is_file():
        registry = pd.read_csv(registry_path, dtype="string", keep_default_na=False)
        if {"timestamp_utc", "run_id", "source_state", "artifact_paths"}.issubset(registry):
            ordered = registry.sort_values("timestamp_utc", ascending=False, kind="mergesort")
            seen_runs: set[str] = set()
            for row in ordered.to_dict(orient="records"):
                run_id = str(row["run_id"])
                if not run_id or run_id in seen_runs:
                    continue
                seen_runs.add(run_id)
                try:
                    source_state = json.loads(str(row["source_state"]))
                    artifacts = json.loads(str(row["artifact_paths"]))
                except (json.JSONDecodeError, TypeError):
                    continue
                if source_state.get("dirty") is not False:
                    continue
                for artifact in artifacts:
                    relative = Path(str(artifact.get("path", "")))
                    if relative.name != FORECAST_FILENAME or "runs" not in relative.parts:
                        continue
                    candidate = root.parent / relative
                    if not candidate.is_file() or candidate.parent.parent.name != run_id:
                        continue
                    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                    if digest == artifact.get("sha256"):
                        return candidate
    candidates = [
        path for path in root.glob(f"runs/*/forecasts/{FORECAST_FILENAME}") if path.is_file()
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No immutable forecast run found below {root / 'runs'}; run the backtest first"
        )
    return max(
        candidates,
        key=lambda path: (path.stat().st_mtime_ns, path.parent.parent.name),
    )


def _as_boolean(series: pd.Series, *, column: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    normalized = series.astype("string").str.strip().str.lower()
    unknown = normalized.notna() & ~normalized.isin({"true", "false", "1", "0"})
    if unknown.any():
        values = sorted(normalized.loc[unknown].dropna().unique().tolist())
        raise ValueError(f"Unrecognized boolean values in {column}: {values}")
    return normalized.map({"true": True, "1": True, "false": False, "0": False}).fillna(False)


def load_forecasts(
    forecast_path: str | Path | None = None,
    *,
    results_root: str | Path = "results",
) -> tuple[pd.DataFrame, Path]:
    """Load and validate an explicit or latest immutable forecast file."""

    path = (
        locate_latest_immutable_forecasts(results_root)
        if forecast_path is None
        else resolve_from_root(forecast_path)
    )
    if not path.is_file():
        raise FileNotFoundError(f"Forecast file does not exist: {path}")
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Forecast file is missing required columns: {missing}")
    if frame.empty:
        raise ValueError("Forecast file is empty")

    frame = frame.copy()
    inferred_run_id = (
        path.parent.parent.name
        if path.name == FORECAST_FILENAME
        and path.parent.name == "forecasts"
        and path.parent.parent.parent.name == "runs"
        else "not_recorded"
    )
    if "run_id" not in frame:
        frame.insert(0, "run_id", inferred_run_id)
    run_ids = frame["run_id"].dropna().astype(str).unique()
    if len(run_ids) != 1:
        raise ValueError("A publication forecast file must contain exactly one run_id")
    if "runs" in path.parts and inferred_run_id != "not_recorded" and run_ids[0] != inferred_run_id:
        raise ValueError(
            f"Forecast run_id {run_ids[0]!r} does not match immutable directory {inferred_run_id!r}"
        )
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in ("horizon", "actual", "forecast", "year", "month"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[["horizon", "year", "month"]].isna().any().any():
        raise ValueError("horizon, year, and month must be numeric and non-missing")
    if (frame["horizon"] < 1).any():
        raise ValueError("Forecast horizons must be positive")
    if (~frame["month"].between(1, 12)).any():
        raise ValueError("Calendar months must be between 1 and 12")
    if not (frame["date"].dt.year == frame["year"]).all():
        raise ValueError("year does not agree with date")
    if not (frame["date"].dt.month == frame["month"]).all():
        raise ValueError("month does not agree with date")

    for column in ("lower_95", "upper_95", "seasonal_naive_forecast"):
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    finite_interval = frame["lower_95"].notna() & frame["upper_95"].notna()
    if (frame.loc[finite_interval, "lower_95"] > frame.loc[finite_interval, "upper_95"]).any():
        raise ValueError("At least one lower_95 value exceeds upper_95")

    derived_full = frame["actual"].notna() & frame["forecast"].notna()
    frame["full_evaluable"] = (
        _as_boolean(frame["full_evaluable"], column="full_evaluable")
        if "full_evaluable" in frame
        else derived_full
    )
    frame["full_evaluable"] &= derived_full
    if "comparable_to_seasonal_naive" in frame:
        frame["comparable_to_seasonal_naive"] = _as_boolean(
            frame["comparable_to_seasonal_naive"],
            column="comparable_to_seasonal_naive",
        )

    key = ["fold_id", "protocol", "model", "date", "horizon"]
    duplicate = frame.duplicated(key, keep=False)
    if duplicate.any():
        example = frame.loc[duplicate, key].iloc[0].to_dict()
        raise ValueError(f"Duplicate forecast row for key: {example}")
    actual_counts = frame.groupby(["protocol", "fold_id", "date"], dropna=False)["actual"].nunique(
        dropna=True
    )
    if (actual_counts > 1).any():
        raise ValueError("Actual values disagree across models for the same forecast target")

    order = ["protocol", "model", "date", "horizon", "fold_id"]
    return frame.sort_values(order, kind="mergesort").reset_index(drop=True), path


def _full_support(group: pd.DataFrame) -> pd.DataFrame:
    actual = pd.to_numeric(group["actual"], errors="coerce")
    forecast = pd.to_numeric(group["forecast"], errors="coerce")
    mask = group["full_evaluable"].astype(bool) & actual.notna() & forecast.notna()
    return group.loc[mask].copy()


def _metric_record(group: pd.DataFrame) -> dict[str, object]:
    supported = _full_support(group)
    actual = supported["actual"].to_numpy(dtype=float)
    forecast = supported["forecast"].to_numpy(dtype=float)
    lower = supported["lower_95"].to_numpy(dtype=float)
    upper = supported["upper_95"].to_numpy(dtype=float)
    interval_mask = np.isfinite(actual) & np.isfinite(lower) & np.isfinite(upper)
    widths = upper[interval_mask] - lower[interval_mask]
    return {
        "support": "model_full_evaluable_support",
        "observations": int(len(supported)),
        "unique_target_months": int(supported["date"].nunique()),
        "folds": int(supported["fold_id"].nunique()),
        "support_start": supported["date"].min().date() if len(supported) else "",
        "support_end": supported["date"].max().date() if len(supported) else "",
        "mae": mae(actual, forecast),
        "rmse": rmse(actual, forecast),
        "mape_pct": mape(actual, forecast),
        "smape_pct": smape(actual, forecast),
        "wape_pct": wape(actual, forecast),
        "bias_forecast_minus_actual": bias(actual, forecast),
        "r2": r2(actual, forecast),
        "interval_95_observations": int(interval_mask.sum()),
        "interval_95_coverage": interval_coverage(actual, lower, upper),
        "interval_95_mean_width": float(np.mean(widths)) if len(widths) else np.nan,
        "interval_95_median_width": float(np.median(widths)) if len(widths) else np.nan,
        "interval_95_winkler": winkler_score(actual, lower, upper, alpha=0.05),
    }


def pooled_metrics(
    forecasts: pd.DataFrame,
    *,
    dimension: str | None = None,
) -> pd.DataFrame:
    """Compute pooled metrics on each model's complete evaluable support."""

    if dimension is not None and dimension not in {"horizon", "month", "regime", "year"}:
        raise ValueError("dimension must be horizon, month, regime, year, or None")
    grouping = ["run_id", "protocol", "model", *([dimension] if dimension else [])]
    records: list[dict[str, object]] = []
    grouper: str | list[str] = grouping[0] if len(grouping) == 1 else grouping
    for keys, group in forecasts.groupby(grouper, sort=True, dropna=False):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        record = dict(zip(grouping, key_values, strict=True))
        record.update(_metric_record(group))
        records.append(record)
    return pd.DataFrame(records).sort_values(grouping, kind="mergesort").reset_index(drop=True)


def macro_fold_scaled_metrics(
    fold_metrics: pd.DataFrame,
    *,
    run_id: str,
) -> pd.DataFrame:
    """Summarize fold-specific MASE/RMSSE without inventing a pooled scale denominator."""

    required = {"protocol", "model", "fold_id", "full_n", "full_mase", "full_rmsse"}
    missing = sorted(required - set(fold_metrics.columns))
    if missing:
        return pd.DataFrame(
            [
                {
                    "run_id": run_id,
                    "status": "not_available",
                    "note": f"fold metrics missing required columns: {missing}",
                }
            ]
        )
    frame = fold_metrics.copy()
    for column in ("full_n", "full_mase", "full_rmsse"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.loc[frame["full_n"] > 0]
    records: list[dict[str, object]] = []
    for (protocol, model), group in frame.groupby(["protocol", "model"], sort=True):
        records.append(
            {
                "run_id": run_id,
                "protocol": protocol,
                "model": model,
                "support": "unweighted_macro_mean_of_fold_specific_scaled_errors",
                "folds": int(group["fold_id"].nunique()),
                "observations_across_folds": int(group["full_n"].sum()),
                "macro_fold_mase": float(group["full_mase"].mean()),
                "macro_fold_mase_median": float(group["full_mase"].median()),
                "macro_fold_rmsse": float(group["full_rmsse"].mean()),
                "macro_fold_rmsse_median": float(group["full_rmsse"].median()),
                "note": (
                    "Each fold uses its own in-sample seasonal scale; these values are not "
                    "pooled observation-weighted errors."
                ),
            }
        )
    return pd.DataFrame(records).sort_values(
        ["protocol", "macro_fold_mase", "model"], kind="mergesort"
    )


def publication_scope_status(
    *,
    run_id: str,
    external_2026_available: bool = False,
    evidence_run_ids: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Make completed, conditional, and unavailable publication outputs explicit."""

    linked_runs = dict(evidence_run_ids or {})

    rows = [
        (
            "dataset_and_missingness",
            "completed",
            "reports/tables/dataset_summary.csv; reports/tables/data_quality_summary.csv",
            "Audited supplied snapshot; the three Q2-2020 target months remain missing.",
        ),
        (
            "rolling_origin_model_comparison",
            "completed",
            "reports/tables/publication_metrics_overall_full_support.csv",
            "Fixed-origin and one-step ex-ante protocols are reported separately.",
        ),
        (
            "forecast_comparison_uncertainty",
            "completed",
            "reports/tables/publication_paired_comparisons_vs_seasonal_naive.csv",
            "Paired DM/HAC and moving-block bootstrap comparisons use seasonal-naive support.",
        ),
        (
            "scaled_error_summary",
            "completed",
            "reports/tables/publication_macro_fold_scaled_metrics.csv",
            "MASE and RMSSE use explicit unweighted macro means of fold-specific scales.",
        ),
        (
            "legacy_2025_reproduction",
            "completed_sensitivity",
            "results/reproduction_metrics.csv",
            (
                "Observation-availability legacy comparison; not the operational "
                "release-delay protocol."
            ),
        ),
        (
            "2026_external_validation",
            (
                "completed_at_quarterly_aggregate_only"
                if external_2026_available
                else "not_yet_generated"
            ),
            (
                "reports/tables/publication_2026q1_external_validation.csv"
                if external_2026_available
                else ""
            ),
            (
                "Same-definition official Q1 total; monthly 2026 accuracy is not inferred."
                if external_2026_available
                else "No frozen same-definition 2026 aggregate validation artifact was found."
            ),
        ),
        (
            "macroeconomic_ablation",
            "completed_snapshot_vintage_sensitivity",
            "reports/tables/model_ablation_snapshot_vintage.csv",
            (
                "REER/HICP issue-date vintages are unknown; this is not confirmatory "
                "operational evidence."
            ),
        ),
        (
            "gtd_common_sample",
            "completed_retrospective_sensitivity",
            "reports/tables/gtd_predictive_common_sample.csv",
            "Aggregate-only 2008-2020 licensed-data analysis; GTD issue dates are unavailable.",
        ),
        (
            "source_country_arrivals_and_digital_intent_panel",
            "not_estimable_from_available_inputs",
            "",
            (
                "No definition-consistent, archived country-month target and origin-vintage "
                "intent panel was available."
            ),
        ),
        (
            "conditional_or_ex_post_leaderboard",
            "not_run",
            "",
            (
                "No credible realized-future exogenous path was accepted; an empty track is "
                "not mixed with ex-ante results."
            ),
        ),
        (
            "shap_ale_or_pdp",
            "not_applicable_to_selected_evidence",
            "",
            (
                "No tree model established robust benchmark skill; post-hoc importance would "
                "not supply causal evidence."
            ),
        ),
        (
            "security_event_map",
            "not_published_by_license_design",
            "",
            (
                "The repository publishes aggregate GTD sensitivities, not event locations or "
                "reconstructable derivatives."
            ),
        ),
    ]
    return pd.DataFrame(
        [
            {
                "run_id": linked_runs.get(deliverable, run_id),
                "deliverable": deliverable,
                "status": status,
                "artifact": artifact,
                "evidence_boundary": boundary,
            }
            for deliverable, status, artifact, boundary in rows
        ]
    )


def _single_artifact_run_id(path: Path) -> str | None:
    """Return the sole run ID in an evidence table, failing on mixed provenance."""

    if not path.is_file():
        return None
    frame = pd.read_csv(path, usecols=["run_id"], dtype="string")
    values = frame["run_id"].dropna().unique().tolist()
    if len(values) != 1:
        raise ValueError(f"Expected exactly one run_id in {path}; found {values}")
    return str(values[0])


def _benchmark_for_group(group: pd.DataFrame, forecasts: pd.DataFrame) -> pd.Series:
    embedded = pd.to_numeric(group["seasonal_naive_forecast"], errors="coerce")
    if embedded.notna().any():
        return embedded

    benchmark = forecasts.loc[forecasts["model"] == BENCHMARK_MODEL].copy()
    key = ["protocol", "fold_id", "date", "horizon"]
    reference = benchmark[key + ["forecast"]].rename(columns={"forecast": "benchmark"})
    matched = group[key].merge(reference, on=key, how="left", validate="one_to_one")
    matched.index = group.index
    return pd.to_numeric(matched["benchmark"], errors="coerce")


def paired_loss_comparisons(
    forecasts: pd.DataFrame,
    *,
    bootstrap_repetitions: int = 2_000,
    seed: int = 20250811,
) -> pd.DataFrame:
    """Compare every model with seasonal naive on identical target observations.

    The monthly loss differential uses a Newey-West HAC variance with up to 11
    lags and a 12-month moving-block bootstrap.  The DM small-sample correction
    uses the largest forecast horizon represented by the protocol.
    """

    if bootstrap_repetitions < 1:
        raise ValueError("bootstrap_repetitions must be positive")
    records: list[dict[str, object]] = []
    candidates = forecasts.loc[forecasts["model"] != BENCHMARK_MODEL]
    for (run_id, protocol, model), group in candidates.groupby(
        ["run_id", "protocol", "model"], sort=True
    ):
        group = group.sort_values(["date", "horizon", "fold_id"], kind="mergesort").copy()
        benchmark = _benchmark_for_group(group, forecasts)
        actual = pd.to_numeric(group["actual"], errors="coerce")
        model_forecast = pd.to_numeric(group["forecast"], errors="coerce")
        paired = actual.notna() & model_forecast.notna() & benchmark.notna()
        if "comparable_to_seasonal_naive" in group:
            paired &= group["comparable_to_seasonal_naive"].astype(bool)
        paired_group = group.loc[paired]
        y = actual.loc[paired].to_numpy(dtype=float)
        model_values = model_forecast.loc[paired].to_numpy(dtype=float)
        benchmark_values = benchmark.loc[paired].to_numpy(dtype=float)
        maximum_horizon = int(paired_group["horizon"].max()) if len(paired_group) else 1
        hac_lags = min(11, max(len(paired_group) - 2, 0))
        for loss in ("absolute", "squared"):
            model_errors = y - model_values
            benchmark_errors = y - benchmark_values
            if loss == "absolute":
                model_losses = np.abs(model_errors)
                benchmark_losses = np.abs(benchmark_errors)
            else:
                model_losses = np.square(model_errors)
                benchmark_losses = np.square(benchmark_errors)
            model_mean = float(np.mean(model_losses)) if len(y) else np.nan
            benchmark_mean = float(np.mean(benchmark_losses)) if len(y) else np.nan
            dm = diebold_mariano(
                y,
                model_values,
                benchmark_values,
                horizon=maximum_horizon,
                loss=loss,
                hac_lags=hac_lags,
            )
            bootstrap = moving_block_bootstrap_loss_difference(
                y,
                model_values,
                benchmark_values,
                loss=loss,
                block_length=12,
                repetitions=bootstrap_repetitions,
                seed=seed,
            )
            records.append(
                {
                    "run_id": run_id,
                    "protocol": protocol,
                    "model": model,
                    "benchmark": BENCHMARK_MODEL,
                    "loss": loss,
                    "support": "paired_model_and_seasonal_naive_target_months",
                    "observations": int(len(y)),
                    "unique_target_months": int(paired_group["date"].nunique()),
                    "folds": int(paired_group["fold_id"].nunique()),
                    "support_start": (
                        paired_group["date"].min().date() if len(paired_group) else ""
                    ),
                    "support_end": (paired_group["date"].max().date() if len(paired_group) else ""),
                    "maximum_forecast_horizon": maximum_horizon,
                    "model_mean_loss": model_mean,
                    "benchmark_mean_loss": benchmark_mean,
                    "relative_skill_vs_seasonal_naive": relative_skill(model_mean, benchmark_mean),
                    "mean_loss_difference_model_minus_benchmark": dm.mean_loss_difference,
                    "dm_statistic": dm.statistic,
                    "dm_two_sided_p_value": dm.p_value,
                    "dm_hac_lags": dm.hac_lags,
                    "dm_reject_equal_accuracy_at_5pct": (
                        bool(dm.p_value < 0.05) if np.isfinite(dm.p_value) else pd.NA
                    ),
                    "moving_block_length": 12,
                    "moving_block_repetitions": bootstrap_repetitions,
                    "bootstrap_mean_loss_difference": bootstrap["mean"],
                    "bootstrap_95_lower": bootstrap["lower"],
                    "bootstrap_95_upper": bootstrap["upper"],
                    "bootstrap_95_excludes_zero": (
                        bool(bootstrap["lower"] > 0 or bootstrap["upper"] < 0)
                        if np.isfinite(bootstrap["lower"]) and np.isfinite(bootstrap["upper"])
                        else pd.NA
                    ),
                    "direction_note": "negative loss difference favors model",
                }
            )
    if not records:
        return pd.DataFrame()
    return (
        pd.DataFrame(records)
        .sort_values(["run_id", "protocol", "loss", "model"], kind="mergesort")
        .reset_index(drop=True)
    )


def select_shortlist(
    forecasts: pd.DataFrame,
    requested: Iterable[str] | None = None,
    *,
    nonbenchmark_per_protocol: int = 3,
) -> tuple[str, ...]:
    """Select seasonal naive plus the best full-support models per protocol."""

    available = set(forecasts["model"].dropna().astype(str))
    if requested is not None:
        selected = list(dict.fromkeys(str(model) for model in requested))
        unknown = sorted(set(selected) - available)
        if unknown:
            raise ValueError(f"Requested shortlist models not found: {unknown}")
        return tuple(selected)
    selected = [BENCHMARK_MODEL] if BENCHMARK_MODEL in available else []
    overall = pooled_metrics(forecasts)
    for _, group in overall.groupby("protocol", sort=True):
        ranked = group.loc[group["model"] != BENCHMARK_MODEL].sort_values(
            ["mae", "model"], kind="mergesort", na_position="last"
        )
        selected.extend(ranked["model"].head(nonbenchmark_per_protocol).tolist())
    return tuple(dict.fromkeys(selected))


def _model_colors(models: Sequence[str]) -> dict[str, object]:
    palette = plt.get_cmap("tab20").colors
    return {model: palette[index % len(palette)] for index, model in enumerate(models)}


def _protocol_label(protocol: object) -> str:
    value = str(protocol)
    return PROTOCOL_LABELS.get(value, value.replace("_", " ").title())


def _model_label(model: object) -> str:
    value = str(model)
    return MODEL_LABELS.get(value, value.replace("_", " ").title())


def _millions_formatter() -> FuncFormatter:
    return FuncFormatter(lambda value, _position: f"{value / 1_000_000:.1f}")


def _ranked_protocol_models(
    panel: pd.DataFrame,
    shortlist: Sequence[str],
    *,
    maximum_nonbenchmarks: int = 3,
) -> list[str]:
    """Return the benchmark and best shortlisted alternatives for one protocol."""

    candidates = panel.loc[panel["model"].isin(shortlist)].copy()
    records: list[tuple[str, float]] = []
    for model, group in candidates.groupby("model", sort=True):
        if {"actual", "forecast", "full_evaluable"}.issubset(group.columns):
            supported = _full_support(group)
            score = (
                mae(
                    supported["actual"].to_numpy(dtype=float),
                    supported["forecast"].to_numpy(dtype=float),
                )
                if len(supported)
                else np.nan
            )
        else:
            observations = pd.to_numeric(group["observations"], errors="coerce")
            group_mae = pd.to_numeric(group["mae"], errors="coerce")
            finite = observations.notna() & group_mae.notna() & (observations > 0)
            score = (
                float(np.average(group_mae.loc[finite], weights=observations.loc[finite]))
                if finite.any()
                else np.nan
            )
        records.append((str(model), score))
    alternatives = sorted(
        (
            (model, score)
            for model, score in records
            if model != BENCHMARK_MODEL and np.isfinite(score)
        ),
        key=lambda item: (item[1], item[0]),
    )
    selected = [BENCHMARK_MODEL] if any(model == BENCHMARK_MODEL for model, _ in records) else []
    selected.extend(model for model, _ in alternatives[:maximum_nonbenchmarks])
    return selected


def _save_publication_figure(fig: plt.Figure, stem: Path) -> tuple[Path, Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    png = stem.with_suffix(".png")
    svg = stem.with_suffix(".svg")
    fig.savefig(
        png,
        bbox_inches="tight",
        dpi=300,
        metadata={"Software": "tourism-forecasting"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "tourism-forecasting", "Date": None},
    )
    normalize_svg(svg)
    plt.close(fig)
    return png, svg


def _protocol_axes(protocols: Sequence[str], *, width: float = 10, height: float = 4.6):
    fig, axes = plt.subplots(
        len(protocols), 1, figsize=(width, height * len(protocols)), squeeze=False
    )
    return fig, axes[:, 0]


def _actual_vs_predicted_figure(
    forecasts: pd.DataFrame,
    shortlist: Sequence[str],
    destination: Path,
) -> tuple[Path, Path]:
    selected = forecasts.loc[forecasts["model"].isin(shortlist)].copy()
    protocols = sorted(selected["protocol"].unique())
    fig, axes = _protocol_axes(protocols, height=4.2)
    colors = _model_colors(shortlist)
    for axis, protocol in zip(axes, protocols, strict=True):
        panel = selected.loc[selected["protocol"] == protocol]
        panel_models = _ranked_protocol_models(panel, shortlist)
        actual = (
            panel.dropna(subset=["actual"])
            .sort_values(["date", "model"], kind="mergesort")
            .drop_duplicates("date")
        )
        axis.plot(
            actual["date"],
            actual["actual"],
            color="#111111",
            linewidth=1.8,
            label=f"actual (n={len(actual)})",
            zorder=5,
        )
        for model in panel_models:
            group = _full_support(panel.loc[panel["model"] == model]).sort_values("date")
            if group.empty:
                continue
            axis.plot(
                group["date"],
                group["forecast"],
                linewidth=1.0,
                alpha=0.9,
                color=colors[model],
                label=f"{_model_label(model)} (n={len(group)})",
            )
        axis.set_title(_protocol_label(protocol), loc="left")
        axis.set_ylabel("Monthly visitors (millions)")
        axis.yaxis.set_major_formatter(_millions_formatter())
        axis.legend(ncol=2, frameon=True)
    axes[-1].set_xlabel("Target month")
    fig.suptitle(
        "Actual and shortlisted forecasts\nModel-specific full evaluable support",
        x=0.01,
        ha="left",
    )
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    return _save_publication_figure(fig, destination / "publication_actual_vs_predicted")


def _error_dimension_figure(
    metrics: pd.DataFrame,
    *,
    dimension: str,
    shortlist: Sequence[str],
    destination: Path,
) -> tuple[Path, Path]:
    selected = metrics.loc[metrics["model"].isin(shortlist)].copy()
    protocols = sorted(selected["protocol"].unique())
    fig, axes = _protocol_axes(protocols, width=11.5, height=3.8)
    colors = _model_colors(shortlist)
    if dimension == "month":
        labels = [pd.Timestamp(2000, month, 1).strftime("%b") for month in range(1, 13)]
    else:
        labels = None
    for axis, protocol in zip(axes, protocols, strict=True):
        panel = selected.loc[selected["protocol"] == protocol]
        panel_models = _ranked_protocol_models(panel, shortlist)
        if dimension == "horizon" and panel[dimension].nunique() == 1:
            point = panel.loc[
                panel["model"].isin(panel_models) & panel["mae"].notna()
            ].drop_duplicates("model")
            point["_order"] = point["model"].map(
                {model: order for order, model in enumerate(panel_models)}
            )
            point = point.sort_values("_order", kind="mergesort")
            positions = np.arange(len(point))
            axis.bar(
                positions,
                point["mae"],
                color=[colors[model] for model in point["model"]],
            )
            axis.set_xticks(
                positions,
                [_model_label(model) for model in point["model"]],
                rotation=12,
                ha="right",
            )
            axis.set_title(f"{_protocol_label(protocol)} (horizon 1)", loc="left")
            axis.set_ylabel("MAE (millions of visitors)")
            axis.yaxis.set_major_formatter(_millions_formatter())
            continue
        for model in panel_models:
            group = panel.loc[panel["model"] == model].copy()
            if dimension == "regime":
                regime_order = {
                    "pre_pandemic": 0,
                    "pandemic_shock": 1,
                    "recovery": 2,
                    "normalization": 3,
                }
                group["_order"] = group[dimension].map(regime_order).fillna(99)
                group = group.sort_values(["_order", dimension], kind="mergesort")
            else:
                group = group.sort_values(dimension, kind="mergesort")
            if group.empty:
                continue
            axis.plot(
                group[dimension],
                group["mae"],
                marker="o",
                markersize=3,
                linewidth=1.2,
                color=colors[model],
                label=_model_label(model),
            )
        axis.set_title(_protocol_label(protocol), loc="left")
        axis.set_ylabel("MAE (millions of visitors)")
        axis.yaxis.set_major_formatter(_millions_formatter())
        if labels is not None:
            axis.set_xticks(range(1, 13), labels)
        elif dimension == "regime":
            ordered_labels = list(REGIME_LABELS)
            axis.set_xticks(ordered_labels, [REGIME_LABELS[label] for label in ordered_labels])
            axis.tick_params(axis="x", labelrotation=15)
        axis.legend(ncol=2, frameon=True)
    if dimension == "horizon" and (
        selected.loc[selected["protocol"] == protocols[-1], dimension].nunique() == 1
    ):
        axes[-1].set_xlabel("One-month-ahead model")
    else:
        axes[-1].set_xlabel(
            "Forecast horizon (months)" if dimension == "horizon" else dimension.title()
        )
    fig.suptitle(
        f"Forecast error by {dimension}\nModel-specific full evaluable support",
        x=0.01,
        ha="left",
    )
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    return _save_publication_figure(fig, destination / f"publication_mae_by_{dimension}")


def _error_over_time_figure(
    forecasts: pd.DataFrame,
    shortlist: Sequence[str],
    destination: Path,
) -> tuple[Path, Path]:
    selected = forecasts.loc[forecasts["model"].isin(shortlist)].copy()
    protocols = sorted(selected["protocol"].unique())
    fig, axes = _protocol_axes(protocols, width=11.5, height=3.9)
    colors = _model_colors(shortlist)
    for axis, protocol in zip(axes, protocols, strict=True):
        panel = selected.loc[selected["protocol"] == protocol]
        panel_models = _ranked_protocol_models(panel, shortlist)
        for model in panel_models:
            group = _full_support(panel.loc[panel["model"] == model]).sort_values("date")
            if group.empty:
                continue
            absolute_error = (group["forecast"] - group["actual"]).abs()
            rolling = absolute_error.rolling(12, min_periods=3).mean()
            axis.plot(
                group["date"],
                absolute_error,
                color=colors[model],
                alpha=0.12,
                linewidth=0.7,
            )
            axis.plot(
                group["date"],
                rolling,
                color=colors[model],
                linewidth=1.5,
                label=f"{_model_label(model)} (12-month mean)",
            )
        axis.set_title(_protocol_label(protocol), loc="left")
        axis.set_ylabel("Absolute error (millions of visitors)")
        axis.yaxis.set_major_formatter(_millions_formatter())
        axis.legend(ncol=2, frameon=True)
    axes[-1].set_xlabel("Target month")
    fig.suptitle(
        "Forecast error over time\n"
        "Faint lines are monthly errors; solid lines are trailing 12-month means",
        x=0.01,
        ha="left",
    )
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    return _save_publication_figure(fig, destination / "publication_absolute_error_over_time")


def _validation_design_figure(
    forecasts: pd.DataFrame,
    destination: Path,
) -> tuple[Path, Path]:
    columns = [
        "protocol",
        "fold_id",
        "forecast_origin",
        "date",
        "horizon",
        "actual",
        "target_available_through",
        "target_publication_delay_months",
    ]
    source = forecasts.copy()
    if "target_available_through" not in source:
        source["target_available_through"] = pd.NaT
    if "target_publication_delay_months" not in source:
        source["target_publication_delay_months"] = pd.NA
    if "forecast_origin" not in source:
        source["forecast_origin"] = pd.NaT
    design = source[columns].drop_duplicates(
        ["protocol", "fold_id", "date", "horizon"], keep="first"
    )
    design["target_available_through"] = pd.to_datetime(
        design["target_available_through"], errors="coerce"
    )
    design["forecast_origin"] = pd.to_datetime(design["forecast_origin"], errors="coerce")
    protocols = sorted(design["protocol"].unique())
    fig, axes = _protocol_axes(protocols, width=11.5, height=3.2)
    for axis, protocol in zip(axes, protocols, strict=True):
        panel = design.loc[design["protocol"] == protocol].sort_values("date")
        evaluable = panel["actual"].notna()
        axis.scatter(
            panel.loc[evaluable, "date"],
            panel.loc[evaluable, "horizon"],
            s=14,
            color="#3679a8",
            label=f"evaluable target (n={int(evaluable.sum())})",
        )
        if (~evaluable).any():
            axis.scatter(
                panel.loc[~evaluable, "date"],
                panel.loc[~evaluable, "horizon"],
                s=30,
                marker="x",
                color="#b2182b",
                label=f"missing target (n={int((~evaluable).sum())})",
            )
        origin_delay = (
            (panel["forecast_origin"].dt.year - panel["target_available_through"].dt.year)
            * 12
            + panel["forecast_origin"].dt.month
            - panel["target_available_through"].dt.month
        )
        delay_label = (
            int(origin_delay.dropna().median()) if origin_delay.notna().any() else None
        )
        if protocol == "fixed_origin_12m_ex_ante" and delay_label is not None:
            availability_label = (
                f"; at the December origin, target data end {delay_label} months earlier"
            )
        elif delay_label is not None:
            availability_label = f"; target history ends t-{delay_label + 1}"
        else:
            availability_label = ""
        axis.set_title(
            f"{_protocol_label(protocol)}{availability_label}",
            loc="left",
        )
        axis.set_ylabel("Forecast horizon (months)")
        axis.set_ylim(0.4, max(1.6, float(panel["horizon"].max()) + 0.6))
        axis.legend(ncol=2, frameon=True)
    axes[-1].set_xlabel("Forecast target month")
    fig.suptitle(
        "Rolling-origin validation design\n"
        "Each point is a prespecified fold target; protocols are not pooled",
        x=0.01,
        ha="left",
    )
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    return _save_publication_figure(fig, destination / "publication_validation_design")


def _interval_figure(
    overall: pd.DataFrame,
    *,
    shortlist: Sequence[str],
    destination: Path,
) -> tuple[Path, Path]:
    selected = overall.loc[
        overall["model"].isin(shortlist) & (overall["interval_95_observations"] > 0)
    ].copy()
    selected["label"] = selected.apply(
        lambda row: f"{_protocol_label(row['protocol'])} | {_model_label(row['model'])}", axis=1
    )
    selected = selected.sort_values(["protocol", "model"], kind="mergesort")
    fig, axes = plt.subplots(1, 2, figsize=(12, max(4.2, 0.42 * len(selected) + 1.8)))
    positions = np.arange(len(selected))
    axes[0].barh(positions, selected["interval_95_coverage"], color="#3679a8")
    axes[0].axvline(0.95, color="#b2182b", linestyle="--", linewidth=1, label="Nominal 95%")
    axes[0].set_xlim(0, 1.02)
    axes[0].set_yticks(positions, selected["label"])
    axes[0].set_xlabel("Empirical coverage")
    axes[0].set_title("95% interval coverage", loc="left")
    axes[0].legend(frameon=True)
    axes[1].barh(positions, selected["interval_95_mean_width"], color="#d28e47")
    axes[1].set_yticks(positions, [""] * len(selected))
    axes[1].set_xlabel("Mean interval width (millions of visitors)")
    axes[1].xaxis.set_major_formatter(_millions_formatter())
    axes[1].set_title("95% interval width", loc="left")
    fig.suptitle(
        "Prediction-interval diagnostics\nProtocol | model; model-specific full interval support",
        x=0.01,
        ha="left",
    )
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    return _save_publication_figure(fig, destination / "publication_interval_diagnostics")


def build_publication_artifacts(
    forecast_path: str | Path | None = None,
    *,
    results_root: str | Path = "results",
    tables_dir: str | Path = "reports/tables",
    figures_dir: str | Path = "reports/figures",
    shortlist: Iterable[str] | None = None,
    bootstrap_repetitions: int = 2_000,
    seed: int = 20250811,
) -> PublicationArtifacts:
    """Build deterministic publication outputs from one completed forecast run."""

    forecasts, source_path = load_forecasts(forecast_path, results_root=results_root)
    tables_destination = resolve_from_root(tables_dir)
    figures_destination = resolve_from_root(figures_dir)
    tables_destination.mkdir(parents=True, exist_ok=True)
    figures_destination.mkdir(parents=True, exist_ok=True)

    run_id = str(forecasts["run_id"].iloc[0])
    fold_metrics_path = source_path.parent.parent / "rolling_origin_fold_metrics.csv"
    fold_metrics = pd.read_csv(fold_metrics_path) if fold_metrics_path.is_file() else pd.DataFrame()
    external_table = tables_destination / "publication_2026q1_external_validation.csv"
    evidence_run_ids = {
        deliverable: linked_run
        for deliverable, linked_run in (
            ("legacy_2025_reproduction", "legacy_2025_reproduction"),
            (
                "2026_external_validation",
                _single_artifact_run_id(external_table),
            ),
            (
                "macroeconomic_ablation",
                _single_artifact_run_id(
                    tables_destination / "model_ablation_snapshot_vintage.csv"
                ),
            ),
            (
                "gtd_common_sample",
                _single_artifact_run_id(
                    tables_destination / "gtd_predictive_common_sample.csv"
                ),
            ),
        )
        if linked_run is not None
    }

    table_frames = {
        "publication_metrics_overall_full_support.csv": pooled_metrics(forecasts),
        **{
            f"publication_metrics_by_{dimension}_full_support.csv": pooled_metrics(
                forecasts, dimension=dimension
            )
            for dimension in ("horizon", "month", "regime", "year")
        },
        "publication_paired_comparisons_vs_seasonal_naive.csv": paired_loss_comparisons(
            forecasts,
            bootstrap_repetitions=bootstrap_repetitions,
            seed=seed,
        ),
        "publication_macro_fold_scaled_metrics.csv": macro_fold_scaled_metrics(
            fold_metrics,
            run_id=run_id,
        ),
        "publication_scope_status.csv": publication_scope_status(
            run_id=run_id,
            external_2026_available=external_table.is_file(),
            evidence_run_ids=evidence_run_ids,
        ),
    }
    table_paths: list[Path] = []
    for filename, frame in table_frames.items():
        path = tables_destination / filename
        frame.to_csv(path, index=False)
        table_paths.append(path)

    selected = select_shortlist(forecasts, shortlist)
    if not selected:
        raise ValueError("No models are available for publication figures")
    configure_plotting()
    figure_paths: list[Path] = []
    figure_paths.extend(_actual_vs_predicted_figure(forecasts, selected, figures_destination))
    figure_paths.extend(_validation_design_figure(forecasts, figures_destination))
    figure_paths.extend(_error_over_time_figure(forecasts, selected, figures_destination))
    for dimension in ("horizon", "month", "regime"):
        figure_paths.extend(
            _error_dimension_figure(
                table_frames[f"publication_metrics_by_{dimension}_full_support.csv"],
                dimension=dimension,
                shortlist=selected,
                destination=figures_destination,
            )
        )
    figure_paths.extend(
        _interval_figure(
            table_frames["publication_metrics_overall_full_support.csv"],
            shortlist=selected,
            destination=figures_destination,
        )
    )
    return PublicationArtifacts(
        forecast_path=source_path,
        tables=tuple(table_paths),
        figures=tuple(figure_paths),
        shortlist=selected,
    )
