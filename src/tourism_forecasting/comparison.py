"""Forecast-comparison procedures with autocorrelation-aware uncertainty."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class DMResult:
    statistic: float
    p_value: float
    mean_loss_difference: float
    observations: int
    hac_lags: int
    loss: str


def _loss(error: np.ndarray, loss: str) -> np.ndarray:
    if loss == "absolute":
        return np.abs(error)
    if loss == "squared":
        return np.square(error)
    raise ValueError("loss must be 'absolute' or 'squared'")


def _newey_west_long_run_variance(values: np.ndarray, lags: int) -> float:
    centered = values - np.mean(values)
    n = len(centered)
    variance = float(np.dot(centered, centered) / n)
    for lag in range(1, min(lags, n - 1) + 1):
        covariance = float(np.dot(centered[lag:], centered[:-lag]) / n)
        weight = 1 - lag / (lags + 1)
        variance += 2 * weight * covariance
    return max(variance, 0.0)


def diebold_mariano(
    actual: np.ndarray,
    model_forecast: np.ndarray,
    benchmark_forecast: np.ndarray,
    *,
    horizon: int = 1,
    loss: str = "absolute",
    hac_lags: int | None = None,
) -> DMResult:
    """Two-sided DM test; negative mean loss difference favors ``model_forecast``."""

    y = np.asarray(actual, dtype=float)
    model = np.asarray(model_forecast, dtype=float)
    benchmark = np.asarray(benchmark_forecast, dtype=float)
    if not (y.shape == model.shape == benchmark.shape):
        raise ValueError("actual and forecast arrays must have identical shapes")
    valid = np.isfinite(y) & np.isfinite(model) & np.isfinite(benchmark)
    y, model, benchmark = y[valid], model[valid], benchmark[valid]
    differential = _loss(y - model, loss) - _loss(y - benchmark, loss)
    n = len(differential)
    if n < 8:
        return DMResult(np.nan, np.nan, float(np.mean(differential)) if n else np.nan, n, 0, loss)
    lags = max(horizon - 1, 0) if hac_lags is None else max(hac_lags, 0)
    long_run_variance = _newey_west_long_run_variance(differential, lags)
    if long_run_variance <= 0:
        statistic = np.nan
        p_value = np.nan
    else:
        statistic = float(np.mean(differential) / np.sqrt(long_run_variance / n))
        # Harvey-Leybourne-Newbold small-sample correction.
        correction_term = (n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n
        statistic *= float(np.sqrt(max(correction_term, 0)))
        p_value = float(2 * stats.t.sf(abs(statistic), df=n - 1))
    return DMResult(statistic, p_value, float(np.mean(differential)), n, lags, loss)


def moving_block_bootstrap_loss_difference(
    actual: np.ndarray,
    model_forecast: np.ndarray,
    benchmark_forecast: np.ndarray,
    *,
    loss: str = "absolute",
    block_length: int = 12,
    repetitions: int = 2_000,
    seed: int = 20250811,
) -> dict[str, float]:
    y = np.asarray(actual, dtype=float)
    model = np.asarray(model_forecast, dtype=float)
    benchmark = np.asarray(benchmark_forecast, dtype=float)
    valid = np.isfinite(y) & np.isfinite(model) & np.isfinite(benchmark)
    differential = _loss(y[valid] - model[valid], loss) - _loss(y[valid] - benchmark[valid], loss)
    n = len(differential)
    if n < max(8, block_length):
        return {
            "mean": float(np.mean(differential)) if n else np.nan,
            "lower": np.nan,
            "upper": np.nan,
        }
    generator = np.random.default_rng(seed)
    starts = np.arange(n - block_length + 1)
    draws = np.empty(repetitions, dtype=float)
    blocks_needed = int(np.ceil(n / block_length))
    for repetition in range(repetitions):
        sampled_starts = generator.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate(
            [differential[start : start + block_length] for start in sampled_starts]
        )[:n]
        draws[repetition] = np.mean(sample)
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return {
        "mean": float(np.mean(differential)),
        "lower": float(lower),
        "upper": float(upper),
    }
