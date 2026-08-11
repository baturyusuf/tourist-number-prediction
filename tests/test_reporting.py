from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from tourism_forecasting.data import sha256_file
from tourism_forecasting.reporting import configure_plotting, leaderboard_markdown, save_figure


def _plot() -> plt.Figure:
    figure, axis = plt.subplots(figsize=(3, 2))
    axis.plot([1, 2, 3], [3, 1, 2], label="series")
    axis.legend()
    return figure


def test_svg_generation_is_deterministic(tmp_path: Path) -> None:
    configure_plotting()
    _, first_svg = save_figure(_plot(), tmp_path / "first")
    first = sha256_file(first_svg)
    _, second_svg = save_figure(_plot(), tmp_path / "second")
    second = sha256_file(second_svg)
    assert first == second


def test_leaderboard_markdown_exposes_full_and_paired_support() -> None:
    leaderboard = pd.DataFrame(
        [
            {
                "protocol": "fixed_origin_12m_ex_ante",
                "model": "seasonal_naive",
                "folds": 2,
                "pooled_full_n": 20,
                "pooled_full_mae": 10.0,
                "pooled_paired_n": 18,
                "pooled_paired_mae": 11.0,
                "pooled_paired_seasonal_naive_mae": 11.0,
                "pooled_paired_mae_skill_vs_seasonal_naive": 0.0,
            }
        ]
    )
    markdown = leaderboard_markdown(leaderboard)
    assert "pooled_full_n" in markdown
    assert "pooled_paired_n" in markdown
    assert "pooled_paired_mae_skill_vs_seasonal_naive" in markdown
