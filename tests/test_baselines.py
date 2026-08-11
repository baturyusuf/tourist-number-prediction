from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tourism_forecasting.backtest import backtest_baselines
from tourism_forecasting.baselines import drift, seasonal_naive, stl_arima, theta
from tourism_forecasting.data import load_core_data
from tourism_forecasting.metrics import metric_bundle
from tourism_forecasting.splits import ForecastFold


def test_seasonal_naive_fixed_origin_uses_prior_year_only() -> None:
    index = pd.date_range("2018-01-01", "2020-12-01", freq="MS")
    values = pd.Series(np.arange(len(index), dtype=float), index=index)
    result = seasonal_naive(values.loc[:"2019-12-01"], index[index.year == 2020])
    assert np.array_equal(
        result.forecast.to_numpy(), values.loc["2019-01-01":"2019-12-01"].to_numpy()
    )


def test_drift_horizon_counts_unpublished_target_gap() -> None:
    index = pd.date_range("2019-01-01", "2020-12-01", freq="MS")
    values = pd.Series(np.arange(len(index), dtype=float), index=index)
    values.loc["2020-10-01":] = np.nan
    result = drift(values, pd.DatetimeIndex(["2021-01-01"]))
    expected_slope = (20.0 - 0.0) / 20
    assert result.forecast.iloc[0] == 20.0 + 4 * expected_slope


def test_legacy_2025_reproduction_if_input_present() -> None:
    path = Path("data/raw/turizm_kisi_Reel_HICP_Trend.csv")
    if not path.exists():
        pytest.skip("private core CSV not available")
    frame, _ = load_core_data(path)
    target = frame.set_index("date")["target_original_with_missing"]
    actual = target.loc["2025-01-01":"2025-12-01"]
    forecast = seasonal_naive(target.loc[:"2024-12-01"], actual.index).forecast
    metrics = metric_bundle(actual, forecast, target.loc[:"2024-12-01"], 12)
    assert np.isclose(metrics["rmse"], 184753.21537368887)
    assert np.isclose(metrics["mae"], 156550.41666666666)
    assert np.isclose(metrics["mape"], 3.279637765784286)
    assert np.isclose(metrics["r2"], 0.9914064090666596)


def test_theta_produces_forecast_and_interval() -> None:
    index = pd.date_range("2010-01-01", periods=72, freq="MS")
    values = pd.Series(
        1_000 + 3 * np.arange(72) + 100 * np.sin(2 * np.pi * np.arange(72) / 12),
        index=index,
    )
    result = theta(values, pd.date_range("2016-01-01", periods=12, freq="MS"))
    assert result.forecast.notna().all()
    assert result.lower is not None and result.lower.notna().all()
    assert result.upper is not None and result.upper.notna().all()


def test_stl_arima_produces_forecast_and_interval() -> None:
    index = pd.date_range("2010-01-01", periods=84, freq="MS")
    values = pd.Series(
        1_000 + 3 * np.arange(84) + 100 * np.sin(2 * np.pi * np.arange(84) / 12),
        index=index,
    )
    result = stl_arima(values, pd.date_range("2017-01-01", periods=12, freq="MS"))
    assert result.forecast.notna().all()
    assert result.lower is not None and result.lower.notna().all()
    assert result.upper is not None and result.upper.notna().all()


def test_model_skill_uses_common_seasonal_naive_dates() -> None:
    dates = pd.date_range("2018-01-01", "2021-12-01", freq="MS")
    values = np.arange(len(dates), dtype=float) + 100
    values[(dates.year <= 2020) & dates.month.isin([4, 5, 6])] = np.nan
    frame = pd.DataFrame({"date": dates, "target_original_with_missing": values})
    fold = ForecastFold(
        "fixed_2021",
        dates.min(),
        pd.Timestamp("2020-12-01"),
        pd.Timestamp("2021-01-01"),
        pd.Timestamp("2021-12-01"),
        12,
        "fixed_origin_12m_ex_ante",
    )
    output = backtest_baselines(
        frame,
        [fold],
        model_names=["seasonal_naive", "naive_last"],
        target_publication_delay_months=0,
    )
    assert set(output.fold_metrics["paired_n"]) == {9.0}
    full_by_model = output.fold_metrics.set_index("model")["full_n"]
    assert full_by_model["seasonal_naive"] == 9.0
    assert full_by_model["naive_last"] == 12.0
    leaderboard = output.leaderboard.set_index("model")
    assert leaderboard.loc["naive_last", "pooled_full_n"] == 12.0
    assert leaderboard.loc["naive_last", "pooled_paired_n"] == 9.0


def test_seasonal_naive_recursively_projects_release_masked_tail() -> None:
    index = pd.date_range("2018-01-01", "2020-12-01", freq="MS")
    values = pd.Series(np.arange(len(index), dtype=float), index=index)
    values.loc["2020-10-01":] = np.nan
    result = seasonal_naive(values, pd.date_range("2021-01-01", periods=12, freq="MS"))
    assert result.forecast.notna().all()
    assert result.forecast.loc["2021-10-01"] == values.loc["2019-10-01"]
    assert "raw target unchanged" in result.notes


def test_backtest_fails_before_row_based_lags_when_month_is_missing() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2018-01-01", "2018-03-01"]),
            "target_original_with_missing": [100.0, 120.0],
        }
    )
    with pytest.raises(ValueError, match="Monthly continuity failure"):
        backtest_baselines(frame, [], model_names=["seasonal_naive"])
