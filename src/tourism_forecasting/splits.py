"""Deterministic expanding-window split definitions for monthly forecasts."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ForecastFold:
    fold_id: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    horizon: int
    protocol: str

    def masks(self, dates: pd.Series) -> tuple[pd.Series, pd.Series]:
        values = pd.to_datetime(dates)
        train = values.between(self.train_start, self.train_end)
        test = values.between(self.test_start, self.test_end)
        if train.any() and test.any() and values[train].max() >= values[test].min():
            raise AssertionError(f"Fold {self.fold_id} has overlapping train/test periods")
        return train, test


def rolling_one_step_folds(
    dates: pd.Series,
    *,
    first_forecast: str | pd.Timestamp,
    last_forecast: str | pd.Timestamp | None = None,
    minimum_train_months: int = 60,
) -> Iterator[ForecastFold]:
    values = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values().unique()
    first = pd.Timestamp(first_forecast).to_period("M").to_timestamp()
    last = (
        pd.Timestamp(last_forecast).to_period("M").to_timestamp()
        if last_forecast is not None
        else values.max()
    )
    for test_date in values[(values >= first) & (values <= last)]:
        train_dates = values[values < test_date]
        if len(train_dates) < minimum_train_months:
            continue
        yield ForecastFold(
            fold_id=f"one_step_{test_date:%Y%m}",
            train_start=train_dates.min(),
            train_end=train_dates.max(),
            test_start=test_date,
            test_end=test_date,
            horizon=1,
            protocol="one_step_ex_ante",
        )


def annual_fixed_origin_folds(
    dates: pd.Series,
    *,
    first_year: int,
    last_year: int,
    minimum_train_months: int = 60,
) -> Iterator[ForecastFold]:
    """Yield January-origin, up-to-12-month expanding-window folds."""

    values = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values().unique()
    for year in range(first_year, last_year + 1):
        test_start = pd.Timestamp(year=year, month=1, day=1)
        eligible_test = values[
            (values >= test_start) & (values < test_start + pd.DateOffset(years=1))
        ]
        train_dates = values[values < test_start]
        if len(train_dates) < minimum_train_months or not len(eligible_test):
            continue
        yield ForecastFold(
            fold_id=f"fixed_12m_{year}",
            train_start=train_dates.min(),
            train_end=train_dates.max(),
            test_start=eligible_test.min(),
            test_end=eligible_test.max(),
            horizon=len(eligible_test),
            protocol="fixed_origin_12m_ex_ante",
        )


def assert_fold_integrity(fold: ForecastFold, dates: pd.Series) -> None:
    train, test = fold.masks(dates)
    if not train.any():
        raise AssertionError(f"Fold {fold.fold_id} has no training rows")
    if not test.any():
        raise AssertionError(f"Fold {fold.fold_id} has no test rows")
    if pd.to_datetime(dates[train]).max() >= pd.to_datetime(dates[test]).min():
        raise AssertionError(f"Fold {fold.fold_id} leaks test dates into training")
