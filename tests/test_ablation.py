import numpy as np
import pandas as pd

from tourism_forecasting.ablation import paired_block_comparisons


def test_paired_block_comparison_is_deterministic_and_uses_exact_support() -> None:
    dates = pd.date_range("2022-01-01", periods=24, freq="MS")
    rows: list[dict[str, object]] = []
    for index, date in enumerate(dates):
        actual = 1_000.0 + index
        for model, error in (("ridge_recursive_b0", 100.0), ("ridge_recursive_b1", 25.0)):
            rows.append(
                {
                    "protocol": "one_step_ex_ante_snapshot_vintage_sensitivity",
                    "fold_id": f"fold_{index}",
                    "date": date,
                    "horizon": 1,
                    "model": model,
                    "actual": actual,
                    "forecast": actual + (-error if index % 2 else error),
                    "regime": "normalization",
                }
            )
    forecasts = pd.DataFrame(rows)
    comparisons, regimes = paired_block_comparisons(forecasts, repetitions=100, seed=7)
    absolute = comparisons.loc[comparisons["loss"] == "absolute"].iloc[0]
    assert absolute["observations"] == 24
    assert np.isclose(absolute["relative_skill_vs_b0"], 0.75)
    assert regimes.iloc[0]["observations"] == 24
    repeated, _ = paired_block_comparisons(forecasts, repetitions=100, seed=7)
    pd.testing.assert_frame_equal(comparisons, repeated)
