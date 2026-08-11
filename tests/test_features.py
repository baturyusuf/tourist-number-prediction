import numpy as np
import pandas as pd
import pytest

from tourism_forecasting.features import (
    FeatureSpec,
    assert_no_lookahead,
    build_supervised_features,
    forecast_origins,
)


def _frame(periods: int = 36) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2018-01-01", periods=periods, freq="MS"),
            "target_original_with_missing": np.arange(1, periods + 1, dtype=float),
            "reer_candidate": np.arange(101, 101 + periods, dtype=float),
        }
    )


def test_lags_and_rolls_use_only_prior_targets() -> None:
    frame = _frame()
    features, target, availability = build_supervised_features(
        frame,
        spec=FeatureSpec(
            target_lags=(1, 12),
            rolling_windows=(3,),
            fourier_order=1,
            target_publication_delay_months=0,
        ),
    )
    row = 15
    lag_1 = "target_lag_1_publication_delay_0_effective_lag_1"
    lag_12 = "target_lag_12_publication_delay_0_effective_lag_12"
    roll = "target_available_roll_mean_3_delay_0"
    assert features.loc[row, lag_1] == target.loc[row - 1]
    assert features.loc[row, lag_12] == target.loc[row - 12]
    assert features.loc[row, roll] == target.loc[row - 3 : row - 1].mean()
    assert availability.loc[row, roll] == frame.loc[row - 1, "date"] + pd.offsets.MonthEnd(1)
    assert availability.loc[row, roll] == forecast_origins(frame["date"]).loc[row]


def test_conservative_target_publication_delay_is_enforced() -> None:
    frame = _frame()
    features, target, availability = build_supervised_features(
        frame,
        spec=FeatureSpec(
            target_lags=(1,),
            rolling_windows=(3,),
            fourier_order=1,
            target_publication_delay_months=3,
        ),
    )
    row = 15
    lag = "target_lag_1_publication_delay_3_effective_lag_4"
    roll = "target_available_roll_mean_3_delay_3"
    assert features.loc[row, lag] == target.loc[row - 4]
    assert features.loc[row, roll] == target.loc[row - 6 : row - 4].mean()
    assert availability.loc[row, lag] == forecast_origins(frame["date"]).loc[row]


def test_exogenous_publication_lag_is_enforced() -> None:
    frame = _frame()
    features, _, _ = build_supervised_features(
        frame,
        exogenous_lags={"reer_candidate": 1},
        spec=FeatureSpec(
            target_lags=(1,),
            rolling_windows=(3,),
            fourier_order=1,
            target_publication_delay_months=0,
        ),
    )
    column = "reer_candidate_publication_delay_1_effective_lag_2"
    assert features.loc[4, column] == frame.loc[2, "reer_candidate"]
    zero_delay, _, _ = build_supervised_features(
        frame,
        exogenous_lags={"reer_candidate": 0},
        spec=FeatureSpec(
            target_lags=(1,),
            rolling_windows=(3,),
            fourier_order=1,
            target_publication_delay_months=0,
        ),
    )
    assert (
        zero_delay.loc[4, "reer_candidate_publication_delay_0_effective_lag_1"]
        == frame.loc[3, "reer_candidate"]
    )
    with pytest.raises(ValueError, match="Publication delay cannot be negative"):
        build_supervised_features(
            frame,
            exogenous_lags={"reer_candidate": -1},
            spec=FeatureSpec(
                target_lags=(1,),
                rolling_windows=(3,),
                fourier_order=1,
                target_publication_delay_months=0,
            ),
        )


def test_retrospective_pandemic_labels_are_not_ex_ante_features() -> None:
    features, _, availability = build_supervised_features(
        _frame(60),
        spec=FeatureSpec(target_lags=(1, 12), rolling_windows=(3,), fourier_order=1),
    )
    assert "pandemic_shutdown" not in features
    assert "pandemic_recovery" not in features
    assert "pandemic_shutdown" not in availability


def test_explicit_leakage_guard_fails() -> None:
    dates = pd.Series(pd.date_range("2020-01-01", periods=4, freq="MS"))
    origins = forecast_origins(dates)
    ledger = pd.DataFrame({"bad": dates})
    with pytest.raises(ValueError, match="bad"):
        assert_no_lookahead(ledger, origins)
