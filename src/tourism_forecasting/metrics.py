"""Forecast metrics with explicit scaling and shock-month safeguards."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def _paired(actual: Iterable[float], forecast: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(list(actual), dtype=float)
    yhat = np.asarray(list(forecast), dtype=float)
    if y.shape != yhat.shape:
        raise ValueError(f"Shape mismatch: actual={y.shape}, forecast={yhat.shape}")
    mask = np.isfinite(y) & np.isfinite(yhat)
    if not mask.any():
        return np.array([], dtype=float), np.array([], dtype=float)
    return y[mask], yhat[mask]


def mae(actual: Iterable[float], forecast: Iterable[float]) -> float:
    y, yhat = _paired(actual, forecast)
    return float(np.mean(np.abs(y - yhat))) if len(y) else np.nan


def rmse(actual: Iterable[float], forecast: Iterable[float]) -> float:
    y, yhat = _paired(actual, forecast)
    return float(np.sqrt(np.mean(np.square(y - yhat)))) if len(y) else np.nan


def mape(actual: Iterable[float], forecast: Iterable[float]) -> float:
    """MAPE in percent, excluding undefined zero-actual observations."""

    y, yhat = _paired(actual, forecast)
    nonzero = y != 0
    if not nonzero.any():
        return np.nan
    return float(np.mean(np.abs((y[nonzero] - yhat[nonzero]) / y[nonzero])) * 100)


def smape(actual: Iterable[float], forecast: Iterable[float]) -> float:
    """Symmetric MAPE in percent using the standard 200*|e|/(|y|+|f|) form."""

    y, yhat = _paired(actual, forecast)
    denominator = np.abs(y) + np.abs(yhat)
    defined = denominator > 0
    if not defined.any():
        return np.nan
    return float(np.mean(200 * np.abs(y[defined] - yhat[defined]) / denominator[defined]))


def wape(actual: Iterable[float], forecast: Iterable[float]) -> float:
    """Weighted absolute percentage error in percent."""

    y, yhat = _paired(actual, forecast)
    denominator = np.sum(np.abs(y))
    return float(100 * np.sum(np.abs(y - yhat)) / denominator) if denominator else np.nan


def bias(actual: Iterable[float], forecast: Iterable[float]) -> float:
    """Mean forecast error, defined as forecast minus actual."""

    y, yhat = _paired(actual, forecast)
    return float(np.mean(yhat - y)) if len(y) else np.nan


def r2(actual: Iterable[float], forecast: Iterable[float]) -> float:
    y, yhat = _paired(actual, forecast)
    if len(y) < 2:
        return np.nan
    denominator = np.sum(np.square(y - np.mean(y)))
    return float(1 - np.sum(np.square(y - yhat)) / denominator) if denominator else np.nan


def _seasonal_scale(training: Iterable[float], seasonal_period: int, squared: bool) -> float:
    y = np.asarray(list(training), dtype=float)
    if seasonal_period < 1 or len(y) <= seasonal_period:
        return np.nan
    difference = y[seasonal_period:] - y[:-seasonal_period]
    difference = difference[np.isfinite(difference)]
    if not len(difference):
        return np.nan
    return float(np.mean(np.square(difference) if squared else np.abs(difference)))


def mase(
    actual: Iterable[float],
    forecast: Iterable[float],
    training: Iterable[float],
    seasonal_period: int = 12,
) -> float:
    scale = _seasonal_scale(training, seasonal_period, squared=False)
    numerator = mae(actual, forecast)
    return float(numerator / scale) if np.isfinite(scale) and scale > 0 else np.nan


def rmsse(
    actual: Iterable[float],
    forecast: Iterable[float],
    training: Iterable[float],
    seasonal_period: int = 12,
) -> float:
    scale = _seasonal_scale(training, seasonal_period, squared=True)
    numerator = rmse(actual, forecast)
    return float(numerator / np.sqrt(scale)) if np.isfinite(scale) and scale > 0 else np.nan


def interval_coverage(
    actual: Iterable[float], lower: Iterable[float], upper: Iterable[float]
) -> float:
    y = np.asarray(list(actual), dtype=float)
    lo = np.asarray(list(lower), dtype=float)
    hi = np.asarray(list(upper), dtype=float)
    if not (y.shape == lo.shape == hi.shape):
        raise ValueError("Interval arrays must have the same shape")
    valid = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    return (
        float(np.mean((y[valid] >= lo[valid]) & (y[valid] <= hi[valid]))) if valid.any() else np.nan
    )


def winkler_score(
    actual: Iterable[float],
    lower: Iterable[float],
    upper: Iterable[float],
    alpha: float = 0.05,
) -> float:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    y = np.asarray(list(actual), dtype=float)
    lo = np.asarray(list(lower), dtype=float)
    hi = np.asarray(list(upper), dtype=float)
    valid = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    y, lo, hi = y[valid], lo[valid], hi[valid]
    if not len(y):
        return np.nan
    score = hi - lo
    score = score + (2 / alpha) * (lo - y) * (y < lo)
    score = score + (2 / alpha) * (y - hi) * (y > hi)
    return float(np.mean(score))


def metric_bundle(
    actual: Iterable[float],
    forecast: Iterable[float],
    training: Iterable[float],
    seasonal_period: int = 12,
) -> dict[str, float]:
    y = list(actual)
    yhat = list(forecast)
    return {
        "n": float(len(_paired(y, yhat)[0])),
        "mae": mae(y, yhat),
        "rmse": rmse(y, yhat),
        "mape": mape(y, yhat),
        "smape": smape(y, yhat),
        "wape": wape(y, yhat),
        "mase": mase(y, yhat, training, seasonal_period),
        "rmsse": rmsse(y, yhat, training, seasonal_period),
        "r2": r2(y, yhat),
        "bias": bias(y, yhat),
    }


def relative_skill(model_loss: float, baseline_loss: float) -> float:
    """Return 1 - model/baseline; positive values indicate improvement."""

    if not np.isfinite(model_loss) or not np.isfinite(baseline_loss) or baseline_loss == 0:
        return np.nan
    return float(1 - model_loss / baseline_loss)
