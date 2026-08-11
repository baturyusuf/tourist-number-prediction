from pathlib import Path

import matplotlib.pyplot as plt

from tourism_forecasting.data import sha256_file
from tourism_forecasting.reporting import configure_plotting, save_figure


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
