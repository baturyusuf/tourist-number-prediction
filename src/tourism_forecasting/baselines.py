"""Strong univariate baselines for fixed-origin and rolling one-step evaluation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastResult:
    model: str
    forecast: pd.Series
    lower: pd.Series | None = None
    upper: pd.Series | None = None
    notes: str = ""


def _series(training: pd.Series) -> pd.Series:
    result = pd.Series(training, copy=True, dtype=float)
    if not isinstance(result.index, pd.DatetimeIndex):
        raise TypeError("Training series must use a DatetimeIndex")
    result = result.sort_index()
    if result.index.has_duplicates:
        raise ValueError("Training series contains duplicate monthly timestamps")
    return result.asfreq("MS")


def _test_index(test_dates: pd.DatetimeIndex | pd.Series) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(test_dates)).sort_values()


def _interval_from_residuals(
    point: pd.Series,
    residuals: pd.Series,
    *,
    alpha: float = 0.05,
    horizon_scale: bool = True,
    horizon_steps: np.ndarray | None = None,
) -> tuple[pd.Series, pd.Series]:
    residuals = pd.Series(residuals, dtype=float).dropna()
    if len(residuals) < 3:
        empty = pd.Series(np.nan, index=point.index)
        return empty.copy(), empty.copy()
    z = NormalDist().inv_cdf(1 - alpha / 2)
    sigma = float(residuals.std(ddof=1))
    steps = horizon_steps if horizon_steps is not None else np.arange(1, len(point) + 1)
    if len(steps) != len(point):
        raise ValueError("Interval horizon steps must match the forecast length")
    scale = np.sqrt(steps) if horizon_scale else np.ones(len(point))
    width = z * sigma * scale
    return point - width, point + width


def _calendar_horizon_steps(last_observed: pd.Timestamp, index: pd.DatetimeIndex) -> np.ndarray:
    base = last_observed.to_period("M")
    return np.asarray([date.to_period("M").ordinal - base.ordinal for date in index], dtype=float)


def last_observation(training: pd.Series, test_dates: pd.DatetimeIndex) -> ForecastResult:
    train = _series(training).dropna()
    index = _test_index(test_dates)
    point = pd.Series(float(train.iloc[-1]), index=index, dtype=float)
    residuals = train.diff()
    lower, upper = _interval_from_residuals(
        point,
        residuals,
        horizon_steps=_calendar_horizon_steps(train.index[-1], index),
    )
    return ForecastResult("naive_last", point, lower, upper)


def seasonal_naive(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    seasonal_period: int = 12,
) -> ForecastResult:
    train = _series(training)
    index = _test_index(test_dates)
    history = train.copy()
    values: list[float] = []
    for date in index:
        reference = date - pd.DateOffset(months=seasonal_period)
        value = history.get(reference, np.nan)
        # For horizons longer than one season, recursively reuse the model forecast.
        values.append(float(value) if pd.notna(value) else np.nan)
        history.loc[date] = values[-1]
    point = pd.Series(values, index=index, dtype=float)
    residuals = train - train.shift(seasonal_period)
    lower, upper = _interval_from_residuals(point, residuals)
    return ForecastResult("seasonal_naive", point, lower, upper)


def drift(training: pd.Series, test_dates: pd.DatetimeIndex) -> ForecastResult:
    train = _series(training).dropna()
    index = _test_index(test_dates)
    slope = (float(train.iloc[-1]) - float(train.iloc[0])) / max(len(train) - 1, 1)
    horizon = _calendar_horizon_steps(train.index[-1], index)
    point = pd.Series(float(train.iloc[-1]) + horizon * slope, index=index)
    fitted = pd.Series(float(train.iloc[0]) + np.arange(len(train)) * slope, index=train.index)
    lower, upper = _interval_from_residuals(point, train - fitted, horizon_steps=horizon)
    return ForecastResult("drift", point, lower, upper)


def same_month_historical_mean(training: pd.Series, test_dates: pd.DatetimeIndex) -> ForecastResult:
    train = _series(training)
    index = _test_index(test_dates)
    climatology = train.groupby(train.index.month).mean()
    point = pd.Series([climatology.get(date.month, np.nan) for date in index], index=index)
    fitted = pd.Series(
        [climatology.get(date.month, np.nan) for date in train.index], index=train.index
    )
    lower, upper = _interval_from_residuals(point, train - fitted, horizon_scale=False)
    return ForecastResult("same_month_historical_mean", point, lower, upper)


def seasonal_moving_average(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    seasons: int = 3,
) -> ForecastResult:
    train = _series(training)
    index = _test_index(test_dates)
    values: list[float] = []
    for date in index:
        prior = (
            train[(train.index.month == date.month) & (train.index < date)].dropna().tail(seasons)
        )
        values.append(float(prior.mean()) if len(prior) else np.nan)
    point = pd.Series(values, index=index)
    fitted = pd.Series(index=train.index, dtype=float)
    for date in train.index:
        prior = (
            train[(train.index.month == date.month) & (train.index < date)].dropna().tail(seasons)
        )
        fitted.loc[date] = prior.mean() if len(prior) else np.nan
    lower, upper = _interval_from_residuals(point, train - fitted, horizon_scale=False)
    return ForecastResult(f"seasonal_moving_average_{seasons}", point, lower, upper)


def _explicit_internal_seasonal_fill(training: pd.Series, seasonal_period: int = 12) -> pd.Series:
    """Fill model-internal gaps explicitly; never exported as an observed target."""

    result = _series(training)
    for position in np.flatnonzero(result.isna().to_numpy()):
        candidates: list[float] = []
        for offset in (-seasonal_period, seasonal_period):
            other = position + offset
            if 0 <= other < len(result) and pd.notna(result.iloc[other]):
                candidates.append(float(result.iloc[other]))
        if candidates:
            result.iloc[position] = float(np.mean(candidates))
    return result.interpolate(limit_direction="both")


def holt_winters(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    seasonal_period: int = 12,
) -> ForecastResult:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    original = _series(training)
    filled = _explicit_internal_seasonal_fill(original, seasonal_period)
    model = ExponentialSmoothing(
        filled,
        trend="add",
        damped_trend=True,
        seasonal="add",
        seasonal_periods=seasonal_period,
        initialization_method="estimated",
    ).fit(optimized=True, use_brute=True, method="L-BFGS-B")
    index = _test_index(test_dates)
    point = pd.Series(np.asarray(model.forecast(len(index))), index=index)
    lower, upper = _interval_from_residuals(point, pd.Series(model.resid), horizon_scale=True)
    notes = []
    if original.isna().any():
        notes.append("model-internal seasonal fill for missing training targets")
    if not bool(model.mle_retvals.get("success", False)):
        notes.append("optimizer did not converge; result retained but not shortlisted")
    note = "; ".join(notes)
    return ForecastResult("ets_holt_winters", point, lower, upper, note)


def theta(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    seasonal_period: int = 12,
) -> ForecastResult:
    from statsmodels.tsa.forecasting.theta import ThetaModel

    original = _series(training)
    filled = _explicit_internal_seasonal_fill(original, seasonal_period)
    fitted = ThetaModel(filled, period=seasonal_period, deseasonalize=True).fit()
    index = _test_index(test_dates)
    point = pd.Series(np.asarray(fitted.forecast(len(index))), index=index)
    interval = fitted.prediction_intervals(len(index), alpha=0.05)
    lower = pd.Series(np.asarray(interval.iloc[:, 0]), index=index)
    upper = pd.Series(np.asarray(interval.iloc[:, 1]), index=index)
    note = (
        "model-internal seasonal fill for missing training targets" if original.isna().any() else ""
    )
    return ForecastResult("theta", point, lower, upper, note)


def sarima(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    order: tuple[int, int, int] = (1, 1, 1),
    seasonal_order: tuple[int, int, int, int] = (1, 1, 1, 12),
) -> ForecastResult:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    train = _series(training)
    fitted = SARIMAX(
        train,
        order=order,
        seasonal_order=seasonal_order,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False, maxiter=200)
    index = _test_index(test_dates)
    prediction = fitted.get_forecast(steps=len(index))
    point = pd.Series(np.asarray(prediction.predicted_mean), index=index)
    interval = np.asarray(prediction.conf_int(alpha=0.05))
    lower = pd.Series(interval[:, 0], index=index)
    upper = pd.Series(interval[:, 1], index=index)
    return ForecastResult("sarima_111_111_12", point, lower, upper)


def dynamic_harmonic_regression(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    fourier_order: int = 2,
    seasonal_period: int = 12,
) -> ForecastResult:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    train = _series(training)
    index = _test_index(test_dates)
    positions = np.arange(len(train) + len(index), dtype=float)

    def design(values: np.ndarray) -> np.ndarray:
        columns = [values]
        for order in range(1, fourier_order + 1):
            angle = 2 * np.pi * order * values / seasonal_period
            columns.extend([np.sin(angle), np.cos(angle)])
        return np.column_stack(columns)

    exog = design(positions)
    fitted = SARIMAX(
        train,
        exog=exog[: len(train)],
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False, maxiter=200)
    prediction = fitted.get_forecast(steps=len(index), exog=exog[len(train) :])
    point = pd.Series(np.asarray(prediction.predicted_mean), index=index)
    interval = np.asarray(prediction.conf_int(alpha=0.05))
    return ForecastResult(
        f"dynamic_harmonic_arima_k{fourier_order}",
        point,
        pd.Series(interval[:, 0], index=index),
        pd.Series(interval[:, 1], index=index),
    )


def stl_arima(
    training: pd.Series,
    test_dates: pd.DatetimeIndex,
    *,
    seasonal_period: int = 12,
) -> ForecastResult:
    """Robust STL decomposition with an ARIMA(1,1,1) remainder model."""

    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.forecasting.stl import STLForecast

    original = _series(training)
    filled = _explicit_internal_seasonal_fill(original, seasonal_period)
    fitted = STLForecast(
        filled,
        ARIMA,
        model_kwargs={"order": (1, 1, 1), "trend": "t"},
        period=seasonal_period,
        robust=True,
    ).fit()
    index = _test_index(test_dates)
    point = pd.Series(np.asarray(fitted.forecast(len(index))), index=index)
    residuals = filled - pd.Series(
        np.asarray(fitted.get_prediction().predicted_mean), index=filled.index
    )
    lower, upper = _interval_from_residuals(point, residuals, horizon_scale=True)
    note = "robust STL(12) + ARIMA(1,1,1) remainder"
    if original.isna().any():
        note += "; model-internal seasonal fill for missing training targets"
    return ForecastResult("stl_arima_111", point, lower, upper, note)


BASELINE_MODELS: dict[str, Callable[..., ForecastResult]] = {
    "naive_last": last_observation,
    "seasonal_naive": seasonal_naive,
    "drift": drift,
    "same_month_historical_mean": same_month_historical_mean,
    "seasonal_moving_average_3": seasonal_moving_average,
    "ets_holt_winters": holt_winters,
    "theta": theta,
    "sarima": sarima,
    "dynamic_harmonic_regression": dynamic_harmonic_regression,
    "stl_arima": stl_arima,
}
