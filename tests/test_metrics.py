import numpy as np

from tourism_forecasting.metrics import (
    interval_coverage,
    mae,
    mape,
    mase,
    relative_skill,
    rmse,
    rmsse,
    smape,
    wape,
    winkler_score,
)


def test_metric_values() -> None:
    actual = [100.0, 200.0]
    forecast = [90.0, 220.0]
    training = np.arange(1.0, 27.0)
    assert mae(actual, forecast) == 15.0
    assert np.isclose(rmse(actual, forecast), np.sqrt(250))
    assert np.isclose(mape(actual, forecast), 10.0)
    assert np.isclose(wape(actual, forecast), 10.0)
    assert 0 < smape(actual, forecast) < 20
    assert np.isclose(mase(actual, forecast, training, 12), 15 / 12)
    assert np.isclose(rmsse(actual, forecast, training, 12), np.sqrt(250) / 12)
    assert np.isclose(relative_skill(8, 10), 0.2)


def test_interval_metrics() -> None:
    actual = [1.0, 2.0, 5.0]
    lower = [0.0, 1.0, 2.0]
    upper = [2.0, 3.0, 4.0]
    assert np.isclose(interval_coverage(actual, lower, upper), 2 / 3)
    assert winkler_score(actual, lower, upper, alpha=0.05) > 2
