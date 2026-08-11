"""Leakage-safe feature construction with auditable source timestamps."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    target_lags: tuple[int, ...] = (1, 2, 3, 6, 12, 13, 18, 24)
    rolling_windows: tuple[int, ...] = (3, 6, 12, 24)
    fourier_order: int = 2
    seasonal_period: int = 12
    include_rolling_median: bool = True
    include_rolling_std: bool = True
    include_expanding_mean: bool = True
    # The supplied visitor target is published after its reference month.  The exact historical
    # release calendar is not archived, so the confirmatory operational backtest uses a
    # conservative three-completed-month delay.  Set this explicitly to zero only for the
    # separately labelled observation-availability sensitivity analysis.
    target_publication_delay_months: int = 3


def forecast_origins(dates: pd.Series | pd.DatetimeIndex) -> pd.Series:
    """Origin for a one-step forecast of each monthly timestamp."""

    values = pd.Series(pd.to_datetime(dates))
    return values - pd.Timedelta(days=1)


def add_calendar_features(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    fourier_order: int = 2,
    seasonal_period: int = 12,
) -> pd.DataFrame:
    result = frame.copy()
    date = pd.to_datetime(result[date_column])
    month = date.dt.month
    result["trend_index"] = np.arange(len(result), dtype=float)
    result["high_season"] = month.isin([5, 6, 7, 8, 9, 10]).astype(int)
    for month_number in range(2, 13):
        result[f"month_{month_number:02d}"] = (month == month_number).astype(int)
    index = np.arange(len(result), dtype=float)
    for order in range(1, fourier_order + 1):
        angle = 2 * np.pi * order * index / seasonal_period
        result[f"fourier_sin_{order}"] = np.sin(angle)
        result[f"fourier_cos_{order}"] = np.cos(angle)
    return result


def build_supervised_features(
    frame: pd.DataFrame,
    *,
    target_column: str = "target_original_with_missing",
    date_column: str = "date",
    exogenous_lags: Mapping[str, int] | None = None,
    spec: FeatureSpec | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Build one-step features and a same-shaped feature-availability ledger.

    Target rolling statistics are shifted by the logical lag plus the target-publication delay.
    ``exogenous_lags`` stores
    publication delay in completed months: a delay of one means the value for month t-2 is the
    latest conservatively available input at the end-of-t-1 origin. Calendar/Fourier values for
    the forecast month are known at the preceding month-end origin. Retrospective shock/regime
    labels are intentionally excluded from this ex-ante builder.
    """

    spec = spec or FeatureSpec()
    if spec.target_publication_delay_months < 0:
        raise ValueError("Target publication delay cannot be negative")
    exogenous_lags = exogenous_lags or {}
    ordered = frame.sort_values(date_column, kind="stable").reset_index(drop=True).copy()
    dates = pd.to_datetime(ordered[date_column])
    y = pd.to_numeric(ordered[target_column], errors="coerce").rename("target")
    origin = forecast_origins(dates)
    features = pd.DataFrame(index=ordered.index)
    availability = pd.DataFrame(index=ordered.index)

    target_delay = spec.target_publication_delay_months
    for logical_lag in spec.target_lags:
        effective_lag = logical_lag + target_delay
        name = (
            f"target_lag_{logical_lag}_publication_delay_{target_delay}_"
            f"effective_lag_{effective_lag}"
        )
        features[name] = y.shift(effective_lag)
        reference_month = dates.shift(effective_lag)
        availability[name] = reference_month + pd.offsets.MonthEnd(target_delay + 1)

    effective_recent_lag = target_delay + 1
    shifted = y.shift(effective_recent_lag)
    recent_reference_month = dates.shift(effective_recent_lag)
    recent_availability = recent_reference_month + pd.offsets.MonthEnd(target_delay + 1)
    for window in spec.rolling_windows:
        rolling = shifted.rolling(window=window, min_periods=window)
        base_name = f"target_available_roll_mean_{window}_delay_{target_delay}"
        features[base_name] = rolling.mean()
        availability[base_name] = recent_availability
        if spec.include_rolling_median:
            name = f"target_available_roll_median_{window}_delay_{target_delay}"
            features[name] = rolling.median()
            availability[name] = recent_availability
        if spec.include_rolling_std:
            name = f"target_available_roll_std_{window}_delay_{target_delay}"
            features[name] = rolling.std(ddof=0)
            availability[name] = recent_availability

    if spec.include_expanding_mean:
        name = f"target_available_expanding_mean_delay_{target_delay}"
        features[name] = shifted.expanding(min_periods=spec.seasonal_period).mean()
        availability[name] = recent_availability

    yoy_lag = effective_recent_lag + spec.seasonal_period
    yoy_name = f"target_available_yoy_change_delay_{target_delay}"
    features[yoy_name] = y.shift(effective_recent_lag) / y.shift(yoy_lag) - 1
    availability[yoy_name] = recent_availability
    difference_name = f"target_available_seasonal_difference_delay_{target_delay}"
    features[difference_name] = y.shift(effective_recent_lag) - y.shift(yoy_lag)
    availability[difference_name] = recent_availability

    calendar_source = pd.DataFrame({date_column: dates})
    calendar = add_calendar_features(
        calendar_source,
        date_column=date_column,
        fourier_order=spec.fourier_order,
        seasonal_period=spec.seasonal_period,
    ).drop(columns=[date_column])
    for column in calendar:
        features[column] = calendar[column]
        availability[column] = origin

    for source_column, publication_delay in exogenous_lags.items():
        if publication_delay < 0:
            raise ValueError(
                f"Publication delay cannot be negative: {source_column}={publication_delay}"
            )
        if source_column not in ordered:
            raise KeyError(f"Missing exogenous column: {source_column}")
        effective_lag = publication_delay + 1
        name = (
            f"{source_column}_publication_delay_{publication_delay}_"
            f"effective_lag_{effective_lag}"
        )
        features[name] = pd.to_numeric(ordered[source_column], errors="coerce").shift(effective_lag)
        reference_month = dates.shift(effective_lag)
        availability[name] = reference_month + pd.offsets.MonthEnd(publication_delay + 1)

    assert_no_lookahead(availability, origin)
    features.insert(0, "date", dates)
    availability.insert(0, "date", dates)
    return features, y, availability


def assert_no_lookahead(
    availability: pd.DataFrame,
    origins: pd.Series | pd.DatetimeIndex,
    *,
    ignore_columns: Sequence[str] = ("date",),
) -> None:
    """Fail if any feature value was not available by its forecast origin."""

    origin = pd.Series(pd.to_datetime(origins), index=availability.index)
    violations: list[str] = []
    for column in availability.columns:
        if column in ignore_columns:
            continue
        timestamps = pd.to_datetime(availability[column], errors="coerce")
        bad = timestamps.notna() & (timestamps > origin)
        if bad.any():
            examples = availability.index[bad].tolist()[:3]
            violations.append(f"{column}@rows{examples}")
    if violations:
        raise ValueError("Feature timestamp exceeds forecast origin: " + "; ".join(violations))


def training_ready(
    features: pd.DataFrame,
    target: pd.Series,
    required_columns: Sequence[str] | None = None,
) -> pd.Series:
    columns = (
        list(required_columns)
        if required_columns is not None
        else [column for column in features.columns if column != "date"]
    )
    return target.notna() & features[columns].notna().all(axis=1)
