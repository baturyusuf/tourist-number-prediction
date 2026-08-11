"""Backtesting engines that keep protocols and forecast origins explicit."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from tourism_forecasting.baselines import BASELINE_MODELS, ForecastResult, seasonal_naive
from tourism_forecasting.data import assert_monthly_continuity
from tourism_forecasting.features import FeatureSpec, build_supervised_features
from tourism_forecasting.metrics import (
    interval_coverage,
    metric_bundle,
    relative_skill,
    winkler_score,
)
from tourism_forecasting.models import (
    candidate_specs,
    fit_tabular_model,
    recursive_target_history_forecast,
    tune_recursive_fixed_origin,
)
from tourism_forecasting.splits import ForecastFold


@dataclass(frozen=True)
class BacktestOutput:
    forecasts: pd.DataFrame
    fold_metrics: pd.DataFrame
    leaderboard: pd.DataFrame


def _regime(date: pd.Timestamp) -> str:
    if pd.Timestamp("2020-03-01") <= date <= pd.Timestamp("2020-12-01"):
        return "pandemic_shock"
    if pd.Timestamp("2021-01-01") <= date <= pd.Timestamp("2022-12-01"):
        return "recovery"
    if date >= pd.Timestamp("2023-01-01"):
        return "normalization"
    return "pre_pandemic"


def _prefixed(metrics: dict[str, float], prefix: str) -> dict[str, float]:
    return {f"{prefix}{key}": value for key, value in metrics.items()}


def _available_training_target(
    target: pd.Series,
    fold: ForecastFold,
    publication_delay_months: int,
) -> tuple[pd.Series, pd.Timestamp]:
    """Mask targets that would not have been issued by the fold's forecast origin."""

    if publication_delay_months < 0:
        raise ValueError("Target publication delay cannot be negative")
    available_through = fold.test_start - pd.DateOffset(months=publication_delay_months + 1)
    result = target.copy()
    result.loc[result.index > available_through] = np.nan
    return result, available_through


def _evaluate_result(
    result: ForecastResult,
    actual: pd.Series,
    training: pd.Series,
    fold: ForecastFold,
    seasonal_reference: ForecastResult,
    runtime_seconds: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    aligned_actual = actual.reindex(result.forecast.index)
    seasonal_forecast = seasonal_reference.forecast.reindex(result.forecast.index)
    full_support = aligned_actual.notna() & result.forecast.notna()
    comparable = full_support & seasonal_forecast.notna()
    full_metrics = metric_bundle(
        aligned_actual.where(full_support),
        result.forecast.where(full_support),
        training,
        seasonal_period=12,
    )
    paired_metrics = metric_bundle(
        aligned_actual.where(comparable),
        result.forecast.where(comparable),
        training,
        seasonal_period=12,
    )
    seasonal_metrics = metric_bundle(
        aligned_actual.where(comparable), seasonal_forecast.where(comparable), training, 12
    )
    record: dict[str, object] = {
        "fold_id": fold.fold_id,
        "protocol": fold.protocol,
        "model": result.model,
        "train_start": fold.train_start.strftime("%Y-%m"),
        "train_end": fold.train_end.strftime("%Y-%m"),
        "test_start": fold.test_start.strftime("%Y-%m"),
        "test_end": fold.test_end.strftime("%Y-%m"),
        "runtime_seconds": runtime_seconds,
        "notes": result.notes,
        **_prefixed(full_metrics, "full_"),
        **_prefixed(paired_metrics, "paired_"),
        **_prefixed(seasonal_metrics, "paired_seasonal_naive_"),
        "paired_mae_skill_vs_seasonal_naive": relative_skill(
            paired_metrics["mae"], seasonal_metrics["mae"]
        ),
        "paired_rmse_skill_vs_seasonal_naive": relative_skill(
            paired_metrics["rmse"], seasonal_metrics["rmse"]
        ),
    }
    if result.lower is not None and result.upper is not None:
        lower = result.lower.reindex(result.forecast.index)
        upper = result.upper.reindex(result.forecast.index)
        record["full_interval_95_coverage"] = interval_coverage(
            aligned_actual.where(full_support),
            lower.where(full_support),
            upper.where(full_support),
        )
        record["full_interval_95_mean_width"] = float((upper - lower).where(full_support).mean())
        record["full_interval_95_winkler"] = winkler_score(
            aligned_actual.where(full_support),
            lower.where(full_support),
            upper.where(full_support),
            0.05,
        )
        record["paired_interval_95_coverage"] = interval_coverage(
            aligned_actual.where(comparable),
            lower.where(comparable),
            upper.where(comparable),
        )
        record["paired_interval_95_mean_width"] = float((upper - lower).where(comparable).mean())
        record["paired_interval_95_winkler"] = winkler_score(
            aligned_actual.where(comparable),
            lower.where(comparable),
            upper.where(comparable),
            0.05,
        )
    else:
        lower = pd.Series(np.nan, index=result.forecast.index)
        upper = pd.Series(np.nan, index=result.forecast.index)
        for support in ("full", "paired"):
            record[f"{support}_interval_95_coverage"] = np.nan
            record[f"{support}_interval_95_mean_width"] = np.nan
            record[f"{support}_interval_95_winkler"] = np.nan

    forecasts: list[dict[str, object]] = []
    for horizon, date in enumerate(result.forecast.index, start=1):
        forecasts.append(
            {
                "fold_id": fold.fold_id,
                "protocol": fold.protocol,
                "model": result.model,
                "date": date.strftime("%Y-%m-%d"),
                "horizon": horizon,
                "actual": aligned_actual.loc[date],
                "forecast": result.forecast.loc[date],
                "lower_95": lower.loc[date],
                "upper_95": upper.loc[date],
                "seasonal_naive_forecast": seasonal_forecast.loc[date],
                "error": result.forecast.loc[date] - aligned_actual.loc[date],
                "absolute_error": abs(result.forecast.loc[date] - aligned_actual.loc[date]),
                "year": date.year,
                "month": date.month,
                "regime": _regime(date),
                "full_evaluable": bool(full_support.loc[date]),
                "comparable_to_seasonal_naive": bool(comparable.loc[date]),
            }
        )
    return forecasts, record


def _leaderboard(fold_metrics: pd.DataFrame, forecasts: pd.DataFrame) -> pd.DataFrame:
    """Build explicitly weighted macro-fold and pooled-observation summaries."""

    if fold_metrics.empty or forecasts.empty:
        return pd.DataFrame()

    numeric_columns = [
        column
        for column in fold_metrics.select_dtypes(include="number").columns
        if column != "runtime_seconds"
    ]
    macro = fold_metrics.groupby(["protocol", "model"], as_index=False)[numeric_columns].mean()
    macro = macro.rename(columns={column: f"macro_fold_{column}" for column in numeric_columns})
    counts = fold_metrics.groupby(["protocol", "model"], as_index=False).agg(
        folds=("fold_id", "nunique"), runtime_seconds=("runtime_seconds", "sum")
    )
    result = macro.merge(counts, on=["protocol", "model"])

    pooled_records: list[dict[str, object]] = []
    for (protocol, model), group in forecasts.groupby(["protocol", "model"], sort=False):
        actual = pd.to_numeric(group["actual"], errors="coerce")
        prediction = pd.to_numeric(group["forecast"], errors="coerce")
        seasonal = pd.to_numeric(group["seasonal_naive_forecast"], errors="coerce")
        full = group["full_evaluable"].astype(bool)
        paired = group["comparable_to_seasonal_naive"].astype(bool)
        full_bundle = metric_bundle(actual.where(full), prediction.where(full), [], 12)
        paired_bundle = metric_bundle(actual.where(paired), prediction.where(paired), [], 12)
        seasonal_bundle = metric_bundle(actual.where(paired), seasonal.where(paired), [], 12)
        record: dict[str, object] = {"protocol": protocol, "model": model}
        for prefix, bundle in (
            ("pooled_full_", full_bundle),
            ("pooled_paired_", paired_bundle),
            ("pooled_paired_seasonal_naive_", seasonal_bundle),
        ):
            for key, value in bundle.items():
                if key not in {"mase", "rmsse"}:
                    record[f"{prefix}{key}"] = value
        record["pooled_paired_mae_skill_vs_seasonal_naive"] = relative_skill(
            paired_bundle["mae"], seasonal_bundle["mae"]
        )
        record["pooled_paired_rmse_skill_vs_seasonal_naive"] = relative_skill(
            paired_bundle["rmse"], seasonal_bundle["rmse"]
        )
        lower = pd.to_numeric(group["lower_95"], errors="coerce")
        upper = pd.to_numeric(group["upper_95"], errors="coerce")
        for label, support in (("full", full), ("paired", paired)):
            record[f"pooled_{label}_interval_95_coverage"] = interval_coverage(
                actual.where(support), lower.where(support), upper.where(support)
            )
            record[f"pooled_{label}_interval_95_mean_width"] = float(
                (upper - lower).where(support).mean()
            )
            record[f"pooled_{label}_interval_95_winkler"] = winkler_score(
                actual.where(support), lower.where(support), upper.where(support), 0.05
            )
        pooled_records.append(record)
    result = result.merge(pd.DataFrame(pooled_records), on=["protocol", "model"])
    return result.sort_values(
        ["protocol", "pooled_paired_mae_skill_vs_seasonal_naive", "pooled_paired_mae"],
        ascending=[True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def backtest_baselines(
    frame: pd.DataFrame,
    folds: Iterable[ForecastFold],
    *,
    target_column: str = "target_original_with_missing",
    model_names: Iterable[str] | None = None,
    target_publication_delay_months: int = 3,
) -> BacktestOutput:
    assert_monthly_continuity(frame)
    dates = pd.to_datetime(frame["date"])
    target = pd.Series(frame[target_column].to_numpy(dtype=float), index=dates)
    models = list(model_names or BASELINE_MODELS)
    forecast_records: list[dict[str, object]] = []
    fold_records: list[dict[str, object]] = []
    for fold in folds:
        train_mask, test_mask = fold.masks(dates)
        training, available_through = _available_training_target(
            target.loc[dates[train_mask]], fold, target_publication_delay_months
        )
        actual = target.loc[dates[test_mask]]
        test_dates = pd.DatetimeIndex(dates[test_mask])
        reference = seasonal_naive(training, test_dates)
        for name in models:
            if name not in BASELINE_MODELS:
                raise KeyError(f"Unknown baseline model: {name}")
            started = perf_counter()
            try:
                result = BASELINE_MODELS[name](training, test_dates)
                runtime = perf_counter() - started
                forecasts, metrics = _evaluate_result(
                    result, actual, training, fold, reference, runtime
                )
                for forecast_record in forecasts:
                    forecast_record["forecast_origin"] = (
                        fold.test_start - pd.Timedelta(days=1)
                    ).date()
                    forecast_record["target_available_through"] = available_through.date()
                    forecast_record["target_publication_delay_months"] = (
                        target_publication_delay_months
                    )
                metrics["forecast_origin"] = (fold.test_start - pd.Timedelta(days=1)).date()
                metrics["target_available_through"] = available_through.date()
                metrics["target_publication_delay_months"] = target_publication_delay_months
                forecast_records.extend(forecasts)
                fold_records.append(metrics)
            except Exception as exc:  # retained as a negative/failed experiment
                fold_records.append(
                    {
                        "fold_id": fold.fold_id,
                        "protocol": fold.protocol,
                        "model": name,
                        "train_start": fold.train_start.strftime("%Y-%m"),
                        "train_end": fold.train_end.strftime("%Y-%m"),
                        "test_start": fold.test_start.strftime("%Y-%m"),
                        "test_end": fold.test_end.strftime("%Y-%m"),
                        "runtime_seconds": perf_counter() - started,
                        "forecast_origin": (fold.test_start - pd.Timedelta(days=1)).date(),
                        "target_available_through": available_through.date(),
                        "target_publication_delay_months": target_publication_delay_months,
                        "full_n": 0.0,
                        "paired_n": 0.0,
                        "failure_reason": f"{type(exc).__name__}: {exc}",
                    }
                )
    forecasts = pd.DataFrame(forecast_records)
    metrics = pd.DataFrame(fold_records)
    return BacktestOutput(forecasts, metrics, _leaderboard(metrics, forecasts))


def backtest_tabular_fixed_origin(
    frame: pd.DataFrame,
    folds: Iterable[ForecastFold],
    *,
    model_names: Iterable[str] = ("ridge", "hist_gradient_boosting", "extra_trees", "xgboost"),
    target_column: str = "target_original_with_missing",
    feature_spec: FeatureSpec | None = None,
    seed: int = 20250811,
    tune: bool = True,
    target_publication_delay_months: int = 3,
    parameter_grids: Mapping[str, Mapping[str, Sequence[object]]] | None = None,
    exogenous_lags: Mapping[str, int] | None = None,
    feature_block: str = "b0",
) -> BacktestOutput:
    """Evaluate recursive models; realized test targets/exogenous values are not consumed."""

    assert_monthly_continuity(frame)
    dates = pd.to_datetime(frame["date"])
    target = pd.Series(frame[target_column].to_numpy(dtype=float), index=dates)
    resolved_feature_spec = feature_spec or FeatureSpec(
        target_publication_delay_months=target_publication_delay_months
    )
    if resolved_feature_spec.target_publication_delay_months != target_publication_delay_months:
        raise ValueError("Feature and fold target-publication delays disagree")
    resolved_exogenous_lags = dict(exogenous_lags or {})
    normalized_block = feature_block.strip().lower()
    if not normalized_block or not normalized_block.replace("_", "").isalnum():
        raise ValueError("feature_block must be a non-empty alphanumeric label")
    if tune and resolved_exogenous_lags:
        raise ValueError(
            "Exogenous snapshot-vintage blocks must use pre-specified parameters; recursive "
            "12-month inner tuning would require unavailable future exogenous paths"
        )
    specs = candidate_specs(seed=seed, include_xgboost=True, parameter_grids=parameter_grids)
    forecast_records: list[dict[str, object]] = []
    fold_records: list[dict[str, object]] = []
    for fold in folds:
        train_mask, test_mask = fold.masks(dates)
        history = frame.loc[train_mask].copy()
        test_dates = pd.DatetimeIndex(dates[test_mask])
        training, available_through = _available_training_target(
            target.loc[dates[train_mask]], fold, target_publication_delay_months
        )
        unavailable = pd.to_datetime(history["date"]) > available_through
        history.loc[unavailable, target_column] = np.nan
        actual = target.loc[dates[test_mask]]
        reference = seasonal_naive(training, test_dates)
        built, y, _ = build_supervised_features(
            history,
            target_column=target_column,
            exogenous_lags=resolved_exogenous_lags,
            spec=resolved_feature_spec,
        )
        for name in model_names:
            started = perf_counter()
            try:
                if name not in specs:
                    raise RuntimeError(f"Model dependency unavailable or model unknown: {name}")
                if tune:
                    tuning = tune_recursive_fixed_origin(
                        specs[name],
                        history,
                        target_column=target_column,
                        feature_spec=resolved_feature_spec,
                    )
                    fitted = fit_tabular_model(
                        specs[name],
                        built,
                        y,
                        tune=False,
                        parameters=tuning.parameters,
                    )
                    validation_note = (
                        f"nested recursive validation MAE={tuning.validation_mae:.6g}; "
                        f"origins={tuning.validation_origins}"
                    )
                else:
                    fitted = fit_tabular_model(specs[name], built, y, tune=False)
                    validation_note = "pre-specified first grid configuration; no tuning"
                point = recursive_target_history_forecast(
                    fitted,
                    history,
                    test_dates,
                    target_column=target_column,
                    feature_spec=resolved_feature_spec,
                    exogenous_lags=resolved_exogenous_lags,
                )
                result = ForecastResult(
                    model=f"{name}_recursive_{normalized_block}",
                    forecast=point,
                    notes=(f"{validation_note}; parameters={fitted.parameters}"),
                )
                forecasts, metrics = _evaluate_result(
                    result, actual, training, fold, reference, perf_counter() - started
                )
                for forecast_record in forecasts:
                    forecast_record["forecast_origin"] = (
                        fold.test_start - pd.Timedelta(days=1)
                    ).date()
                    forecast_record["target_available_through"] = available_through.date()
                    forecast_record["target_publication_delay_months"] = (
                        target_publication_delay_months
                    )
                metrics["forecast_origin"] = (fold.test_start - pd.Timedelta(days=1)).date()
                metrics["target_available_through"] = available_through.date()
                metrics["target_publication_delay_months"] = target_publication_delay_months
                forecast_records.extend(forecasts)
                fold_records.append(metrics)
            except Exception as exc:
                fold_records.append(
                    {
                        "fold_id": fold.fold_id,
                        "protocol": fold.protocol,
                        "model": f"{name}_recursive_{normalized_block}",
                        "train_start": fold.train_start.strftime("%Y-%m"),
                        "train_end": fold.train_end.strftime("%Y-%m"),
                        "test_start": fold.test_start.strftime("%Y-%m"),
                        "test_end": fold.test_end.strftime("%Y-%m"),
                        "runtime_seconds": perf_counter() - started,
                        "forecast_origin": (fold.test_start - pd.Timedelta(days=1)).date(),
                        "target_available_through": available_through.date(),
                        "target_publication_delay_months": target_publication_delay_months,
                        "full_n": 0.0,
                        "paired_n": 0.0,
                        "failure_reason": f"{type(exc).__name__}: {exc}",
                    }
                )
    forecasts = pd.DataFrame(forecast_records)
    metrics = pd.DataFrame(fold_records)
    return BacktestOutput(forecasts, metrics, _leaderboard(metrics, forecasts))


def combine_outputs(*outputs: BacktestOutput) -> BacktestOutput:
    forecasts = pd.concat([output.forecasts for output in outputs], ignore_index=True)
    metrics = pd.concat([output.fold_metrics for output in outputs], ignore_index=True)
    return BacktestOutput(forecasts, metrics, _leaderboard(metrics, forecasts))
