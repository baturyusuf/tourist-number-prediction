import numpy as np
import pandas as pd
import pytest

from tourism_forecasting.features import FeatureSpec, build_supervised_features
from tourism_forecasting.models import (
    FittedTabularModel,
    candidate_specs,
    fit_tabular_model,
    recursive_target_history_forecast,
)


class _RecordingEstimator:
    def __init__(self) -> None:
        self.last_features: pd.DataFrame | None = None

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        self.last_features = features.copy()
        return np.array([123.0])


def test_train_only_preprocessing_and_recursive_forecast_ignore_future_actuals() -> None:
    dates = pd.date_range("2010-01-01", periods=96, freq="MS")
    target = 1_000 + 5 * np.arange(96) + 100 * np.sin(2 * np.pi * np.arange(96) / 12)
    frame = pd.DataFrame({"date": dates, "target_original_with_missing": target})
    history = frame.iloc[:84].copy()
    features, y, _ = build_supervised_features(
        history,
        spec=FeatureSpec(target_lags=(1, 12), rolling_windows=(3, 12), fourier_order=1),
    )
    model = fit_tabular_model(
        candidate_specs(include_xgboost=False)["ridge"], features, y, tune=False
    )
    first = recursive_target_history_forecast(
        model,
        history,
        pd.DatetimeIndex(frame.iloc[84:]["date"]),
        feature_spec=FeatureSpec(target_lags=(1, 12), rolling_windows=(3, 12), fourier_order=1),
    )
    altered = frame.copy()
    altered.loc[84:, "target_original_with_missing"] = 999_999_999
    second = recursive_target_history_forecast(
        model,
        altered.iloc[:84],
        pd.DatetimeIndex(altered.iloc[84:]["date"]),
        feature_spec=FeatureSpec(target_lags=(1, 12), rolling_windows=(3, 12), fourier_order=1),
    )
    assert np.allclose(first, second)


def test_recursive_forecast_rejects_sparse_forecast_dates() -> None:
    dates = pd.date_range("2010-01-01", periods=84, freq="MS")
    frame = pd.DataFrame(
        {"date": dates, "target_original_with_missing": np.arange(84, dtype=float) + 100}
    )
    spec = FeatureSpec(
        target_lags=(1, 12),
        rolling_windows=(3,),
        fourier_order=1,
        target_publication_delay_months=0,
    )
    features, target, _ = build_supervised_features(frame, spec=spec)
    model = fit_tabular_model(
        candidate_specs(include_xgboost=False)["ridge"], features, target, tune=False
    )
    with pytest.raises(ValueError, match="contiguous months"):
        recursive_target_history_forecast(
            model,
            frame,
            pd.DatetimeIndex(["2017-01-01", "2017-03-01"]),
            feature_spec=spec,
        )


def test_recursive_forecast_consumes_release_safe_lagged_exogenous_value() -> None:
    dates = pd.date_range("2010-01-01", periods=84, freq="MS")
    frame = pd.DataFrame(
        {
            "date": dates,
            "target_original_with_missing": np.arange(84, dtype=float) + 100,
            "macro": np.arange(84, dtype=float),
        }
    )
    estimator = _RecordingEstimator()
    model = FittedTabularModel(
        "recording",
        estimator,
        ("macro_publication_delay_1_effective_lag_2",),
        {},
        np.nan,
    )
    recursive_target_history_forecast(
        model,
        frame,
        pd.DatetimeIndex(["2017-01-01"]),
        feature_spec=FeatureSpec(
            target_lags=(1,),
            rolling_windows=(3,),
            fourier_order=1,
            target_publication_delay_months=0,
        ),
        exogenous_lags={"macro": 1},
    )
    assert estimator.last_features is not None
    assert estimator.last_features.iloc[0, 0] == 82.0
