import pandas as pd

from tourism_forecasting.splits import annual_fixed_origin_folds, rolling_one_step_folds


def test_rolling_split_boundaries() -> None:
    dates = pd.Series(pd.date_range("2008-01-01", "2016-12-01", freq="MS"))
    folds = list(
        rolling_one_step_folds(
            dates, first_forecast="2015-01", last_forecast="2015-03", minimum_train_months=60
        )
    )
    assert len(folds) == 3
    assert folds[0].train_end == pd.Timestamp("2014-12-01")
    assert folds[0].test_start == pd.Timestamp("2015-01-01")
    assert folds[0].horizon == 1


def test_fixed_origin_has_no_teacher_forcing_boundary() -> None:
    dates = pd.Series(pd.date_range("2008-01-01", "2016-12-01", freq="MS"))
    fold = list(annual_fixed_origin_folds(dates, first_year=2016, last_year=2016))[0]
    assert fold.train_end == pd.Timestamp("2015-12-01")
    assert fold.test_start == pd.Timestamp("2016-01-01")
    assert fold.test_end == pd.Timestamp("2016-12-01")
    assert fold.horizon == 12
