"""Deterministic research tables, figures, and Markdown summaries."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tourism_forecasting.backtest import BacktestOutput
from tourism_forecasting.data import CoreDataAudit
from tourism_forecasting.paths import resolve_from_root

SOURCE_NOTE = "Source: supplied project CSV; calculations by the reproducible pipeline."


def configure_plotting() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.constrained_layout.use": True,
            "svg.fonttype": "none",
            "svg.hashsalt": "tourism-forecasting",
        }
    )


def save_figure(fig: plt.Figure, stem: str | Path) -> tuple[Path, Path]:
    destination = resolve_from_root(stem)
    destination.parent.mkdir(parents=True, exist_ok=True)
    png = destination.with_suffix(".png")
    svg = destination.with_suffix(".svg")
    fig.savefig(png, bbox_inches="tight", dpi=300, metadata={"Software": "tourism-forecasting"})
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "tourism-forecasting", "Date": None},
    )
    normalize_svg(svg)
    plt.close(fig)
    return png, svg


def normalize_svg(path: str | Path) -> Path:
    """Remove backend-inserted trailing spaces while preserving deterministic SVG content."""

    destination = Path(path)
    text = destination.read_text(encoding="utf-8")
    destination.write_text(
        "\n".join(line.rstrip() for line in text.splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def build_core_audit_artifacts(
    frame: pd.DataFrame,
    audit: CoreDataAudit,
    *,
    tables_dir: str | Path = "reports/tables",
    figures_dir: str | Path = "reports/figures",
) -> list[Path]:
    configure_plotting()
    tables = resolve_from_root(tables_dir)
    figures = resolve_from_root(figures_dir)
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    quality_path = tables / "data_quality_summary.csv"
    audit.to_frame().to_csv(quality_path, index=False)
    artifacts.append(quality_path)

    summary = pd.DataFrame(
        {
            "variable": [
                "departing_visitors_total_original_with_missing",
                "reer_cpi_developed_2025eq100",
                "ea_hicp_air_passenger_yoy_pct",
                "search_interest_legacy_unverified",
            ],
        }
    )
    numeric = frame[summary["variable"].tolist()].describe(percentiles=[0.25, 0.5, 0.75]).T
    numeric.insert(0, "variable", numeric.index)
    numeric = numeric.reset_index(drop=True)
    numeric["missing"] = [int(frame[column].isna().sum()) for column in numeric["variable"]]
    summary_path = tables / "dataset_summary.csv"
    numeric.to_csv(summary_path, index=False)
    artifacts.append(summary_path)

    correlation_records: list[dict[str, object]] = []
    target_column = "target_original_with_missing"
    candidates = [
        "reer_cpi_developed_2025eq100",
        "ea_hicp_air_passenger_yoy_pct",
        "search_interest_legacy_unverified",
    ]
    transformations = {
        "level": lambda values: values,
        "first_difference": lambda values: values.diff(),
        "seasonal_difference_12": lambda values: values.diff(12),
    }
    for transformation, function in transformations.items():
        transformed_target = function(frame[target_column])
        for candidate in candidates:
            transformed_candidate = function(frame[candidate])
            paired = pd.concat([transformed_target, transformed_candidate], axis=1).dropna()
            correlation_records.append(
                {
                    "target": target_column,
                    "candidate": candidate,
                    "transformation": transformation,
                    "paired_observations": len(paired),
                    "pearson_correlation": (
                        float(paired.iloc[:, 0].corr(paired.iloc[:, 1]))
                        if len(paired) >= 3
                        else np.nan
                    ),
                    "interpretation_guardrail": (
                        "descriptive only; not predictive, inferential, or causal evidence"
                    ),
                }
            )
    correlation_path = tables / "correlation_sensitivity.csv"
    pd.DataFrame(correlation_records).to_csv(correlation_path, index=False)
    artifacts.append(correlation_path)

    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    series = [
        (
            "departing_visitors_total_original_with_missing",
            "TÜİK total departing visitors",
            "People",
        ),
        (
            "reer_cpi_developed_2025eq100",
            "TCMB CPI REER: developed-country subindex",
            "2025=100",
        ),
        (
            "ea_hicp_air_passenger_yoy_pct",
            "Euro-area passenger-air-transport HICP",
            "YoY change (%)",
        ),
        (
            "search_interest_legacy_unverified",
            "Legacy search-interest composite (unverified provenance)",
            "Relative index",
        ),
    ]
    for axis, (column, title, unit) in zip(axes, series, strict=True):
        axis.plot(frame["date"], frame[column], color="#1f5a94", linewidth=1.2)
        axis.set_title(title, loc="left")
        axis.set_ylabel(unit)
    axes[-1].set_xlabel("Month")
    fig.suptitle("Core monthly series, 2008-2025", fontsize=14, x=0.01, ha="left")
    fig.text(0.01, -0.01, SOURCE_NOTE, fontsize=8)
    artifacts.extend(save_figure(fig, figures / "core_series_overview"))

    missing = (
        frame[
            [
                "departing_visitors_total_original_with_missing",
                "reer_cpi_developed_2025eq100",
                "ea_hicp_air_passenger_yoy_pct",
                "search_interest_legacy_unverified",
            ]
        ]
        .isna()
        .T
    )
    fig, axis = plt.subplots(figsize=(10, 2.8))
    sns.heatmap(missing, cmap=["#f5f5f5", "#b2182b"], cbar=False, yticklabels=True, ax=axis)
    tick_positions = np.linspace(0, len(frame) - 1, 10, dtype=int)
    axis.set_xticks(tick_positions + 0.5)
    axis.set_xticklabels(
        frame.loc[tick_positions, "date"].dt.strftime("%Y-%m"), rotation=45, ha="right"
    )
    axis.set_title("Missingness by variable (red = missing)", loc="left")
    axis.set_xlabel("Month")
    axis.set_ylabel("")
    fig.text(0.01, -0.05, SOURCE_NOTE, fontsize=8)
    artifacts.extend(save_figure(fig, figures / "missingness"))

    observed = frame.dropna(subset=["target_original_with_missing"]).copy()
    observed["month_name"] = observed["date"].dt.strftime("%b")
    order = [pd.Timestamp(2000, month, 1).strftime("%b") for month in range(1, 13)]
    fig, axis = plt.subplots(figsize=(10, 4.8))
    sns.boxplot(
        data=observed,
        x="month_name",
        y="target_original_with_missing",
        order=order,
        color="#86b3d1",
        fliersize=2,
        ax=axis,
    )
    axis.set_title("Seasonal distribution of monthly visitor counts", loc="left")
    axis.set_xlabel("Calendar month")
    axis.set_ylabel("Visitors (people)")
    fig.text(0.01, -0.02, SOURCE_NOTE + " Missing targets excluded.", fontsize=8)
    artifacts.extend(save_figure(fig, figures / "seasonality"))

    target = frame.set_index("date")["target_original_with_missing"]
    yoy = target.pct_change(12, fill_method=None) * 100
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    axes[0].plot(target.index, target, color="#1f5a94", linewidth=1.2)
    axes[0].set_ylabel("Visitors")
    axes[0].set_title("Observed level and year-over-year change", loc="left")
    axes[1].plot(yoy.index, yoy, color="#b04a3f", linewidth=1.0)
    axes[1].axhline(0, color="#666666", linewidth=0.8)
    axes[1].set_ylabel("YoY change (%)")
    axes[1].set_xlabel("Month")
    for axis in axes:
        axis.axvspan(
            pd.Timestamp("2020-03-01"), pd.Timestamp("2020-06-01"), color="#d73027", alpha=0.15
        )
        axis.axvline(pd.Timestamp("2016-07-01"), color="#777777", linestyle="--", linewidth=0.8)
    fig.text(
        0.01,
        -0.02,
        SOURCE_NOTE
        + " Shading/line mark prespecified events, not statistically estimated break dates.",
        fontsize=8,
    )
    artifacts.extend(save_figure(fig, figures / "structural_breaks"))
    return artifacts


def write_backtest_artifacts(
    output: BacktestOutput,
    *,
    prefix: str,
    results_dir: str | Path = "results",
) -> list[Path]:
    destination = resolve_from_root(results_dir)
    (destination / "forecasts").mkdir(parents=True, exist_ok=True)
    artifacts = [
        destination / f"{prefix}_fold_metrics.csv",
        destination / f"{prefix}_leaderboard.csv",
        destination / "forecasts" / f"{prefix}_forecasts.csv",
    ]
    output.fold_metrics.to_csv(artifacts[0], index=False)
    output.leaderboard.to_csv(artifacts[1], index=False)
    output.forecasts.to_csv(artifacts[2], index=False)
    return artifacts


def leaderboard_markdown(leaderboard: pd.DataFrame) -> str:
    if leaderboard.empty:
        return "No successful experiments are available."
    display_columns = [
        column
        for column in [
            "protocol",
            "model",
            "folds",
            "observations",
            "mae",
            "rmse",
            "smape",
            "mase",
            "mae_skill_vs_seasonal_naive",
        ]
        if column in leaderboard
    ]
    display = leaderboard[display_columns].copy()
    for column in display.select_dtypes(include="number"):
        display[column] = display[column].map(
            lambda value: "" if pd.isna(value) else f"{value:.4f}"
        )
    return display.to_markdown(index=False)


def write_json(path: str | Path, payload: object) -> Path:
    destination = resolve_from_root(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return destination
