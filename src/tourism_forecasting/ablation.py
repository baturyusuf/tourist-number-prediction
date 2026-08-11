"""Release-aware feature-block ablation on the retrospective core-data snapshot.

The local REER and HICP extraction vintages are not archived.  These experiments are therefore
kept in a separate snapshot-vintage sensitivity protocol and are not promoted into the
confirmatory ex-ante leaderboard.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tourism_forecasting.backtest import backtest_tabular_fixed_origin, combine_outputs
from tourism_forecasting.comparison import (
    diebold_mariano,
    moving_block_bootstrap_loss_difference,
)
from tourism_forecasting.config import load_project_config
from tourism_forecasting.data import assert_monthly_continuity, load_core_data, sha256_file
from tourism_forecasting.features import FeatureSpec
from tourism_forecasting.metrics import mae, relative_skill
from tourism_forecasting.paths import resolve_from_root
from tourism_forecasting.registry import (
    append_experiment,
    assert_clean_source_tree,
    new_experiment_id,
)
from tourism_forecasting.reporting import configure_plotting, save_figure, write_backtest_artifacts
from tourism_forecasting.splits import rolling_one_step_folds

PROTOCOL = "one_step_ex_ante_snapshot_vintage_sensitivity"
TARGET_DEFINITION = "departing_visitors_total_original_with_missing"


@dataclass(frozen=True)
class FeatureBlock:
    code: str
    label: str
    exogenous_lags: Mapping[str, int]
    interpretation: str


@dataclass(frozen=True)
class AblationArtifacts:
    run_id: str
    immutable_paths: tuple[Path, ...]
    publication_paths: tuple[Path, ...]


def _feature_blocks(availability: Mapping[str, object]) -> tuple[FeatureBlock, ...]:
    reer = "reer_cpi_developed_2025eq100"
    hicp = "ea_hicp_air_passenger_yoy_pct"
    reer_delay = int(availability[reer])
    hicp_delay = int(availability[hicp])
    return (
        FeatureBlock("B0", "Target history and calendar", {}, "reference block"),
        FeatureBlock(
            "B1",
            "B0 + REER",
            {reer: reer_delay},
            "lagged developed-country CPI-based REER level",
        ),
        FeatureBlock(
            "B2",
            "B0 + HICP",
            {hicp: hicp_delay},
            "lagged euro-area passenger-air annual HICP inflation",
        ),
        FeatureBlock(
            "B5",
            "B0 + macro/travel cost",
            {reer: reer_delay, hicp: hicp_delay},
            "joint lagged REER and HICP levels",
        ),
    )


def _block_from_model(model: str) -> str:
    marker = "_recursive_"
    if marker not in model:
        raise ValueError(f"Ablation model lacks a feature-block suffix: {model}")
    return model.rsplit(marker, 1)[1].upper()


def paired_block_comparisons(
    forecasts: pd.DataFrame,
    *,
    repetitions: int = 2_000,
    seed: int = 20250811,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare each accepted snapshot block with B0 on exact target months."""

    key = ["protocol", "fold_id", "date", "horizon"]
    b0_model = "ridge_recursive_b0"
    baseline = forecasts.loc[forecasts["model"] == b0_model, key + ["forecast"]].rename(
        columns={"forecast": "b0_forecast"}
    )
    if baseline.empty:
        raise ValueError("Ablation forecasts do not contain ridge_recursive_b0")
    comparison_records: list[dict[str, object]] = []
    regime_records: list[dict[str, object]] = []
    for model, candidate in forecasts.loc[forecasts["model"] != b0_model].groupby(
        "model", sort=True
    ):
        paired = candidate.merge(baseline, on=key, how="inner", validate="one_to_one")
        actual = pd.to_numeric(paired["actual"], errors="coerce")
        forecast = pd.to_numeric(paired["forecast"], errors="coerce")
        b0_forecast = pd.to_numeric(paired["b0_forecast"], errors="coerce")
        valid = actual.notna() & forecast.notna() & b0_forecast.notna()
        paired = paired.loc[valid].copy()
        y = actual.loc[valid].to_numpy(dtype=float)
        model_values = forecast.loc[valid].to_numpy(dtype=float)
        b0_values = b0_forecast.loc[valid].to_numpy(dtype=float)
        block = _block_from_model(str(model))
        for loss in ("absolute", "squared"):
            dm = diebold_mariano(
                y,
                model_values,
                b0_values,
                horizon=1,
                loss=loss,
                hac_lags=min(11, max(len(y) - 2, 0)),
            )
            bootstrap = moving_block_bootstrap_loss_difference(
                y,
                model_values,
                b0_values,
                loss=loss,
                block_length=12,
                repetitions=repetitions,
                seed=seed,
            )
            if loss == "absolute":
                model_loss = mae(y, model_values)
                b0_loss = mae(y, b0_values)
            else:
                model_loss = float(np.mean(np.square(y - model_values)))
                b0_loss = float(np.mean(np.square(y - b0_values)))
            comparison_records.append(
                {
                    "protocol": PROTOCOL,
                    "feature_block": block,
                    "model": model,
                    "benchmark_block": "B0",
                    "benchmark_model": b0_model,
                    "loss": loss,
                    "support": "exact_paired_target_months",
                    "observations": len(y),
                    "support_start": paired["date"].min(),
                    "support_end": paired["date"].max(),
                    "model_mean_loss": model_loss,
                    "b0_mean_loss": b0_loss,
                    "relative_skill_vs_b0": relative_skill(model_loss, b0_loss),
                    "mean_loss_difference_model_minus_b0": dm.mean_loss_difference,
                    "dm_statistic": dm.statistic,
                    "dm_two_sided_p_value": dm.p_value,
                    "dm_hac_lags": dm.hac_lags,
                    "moving_block_length": 12,
                    "moving_block_repetitions": repetitions,
                    "bootstrap_95_lower": bootstrap["lower"],
                    "bootstrap_95_upper": bootstrap["upper"],
                    "bootstrap_95_excludes_zero": (
                        bool(bootstrap["lower"] > 0 or bootstrap["upper"] < 0)
                        if np.isfinite(bootstrap["lower"]) and np.isfinite(bootstrap["upper"])
                        else pd.NA
                    ),
                    "direction_note": "negative loss difference favors feature block",
                }
            )
        for regime, group in paired.groupby("regime", sort=False):
            regime_y = group["actual"].to_numpy(dtype=float)
            regime_model = group["forecast"].to_numpy(dtype=float)
            regime_b0 = group["b0_forecast"].to_numpy(dtype=float)
            model_mae = mae(regime_y, regime_model)
            b0_mae = mae(regime_y, regime_b0)
            regime_records.append(
                {
                    "protocol": PROTOCOL,
                    "feature_block": block,
                    "regime": regime,
                    "observations": len(group),
                    "model_mae": model_mae,
                    "b0_mae": b0_mae,
                    "mae_skill_vs_b0": relative_skill(model_mae, b0_mae),
                }
            )
    comparisons = pd.DataFrame(comparison_records).sort_values(
        ["loss", "feature_block"], kind="mergesort"
    )
    regimes = pd.DataFrame(regime_records).sort_values(
        ["feature_block", "regime"], kind="mergesort"
    )
    return comparisons.reset_index(drop=True), regimes.reset_index(drop=True)


def _summary_table(
    leaderboard: pd.DataFrame,
    blocks: tuple[FeatureBlock, ...],
) -> pd.DataFrame:
    metadata = {block.code: block for block in blocks}
    records: list[dict[str, object]] = []
    for row in leaderboard.to_dict(orient="records"):
        block = _block_from_model(str(row["model"]))
        definition = metadata[block]
        records.append(
            {
                "run_id": row["run_id"],
                "protocol": row["protocol"],
                "feature_block": block,
                "feature_block_label": definition.label,
                "model": row["model"],
                "exogenous_lags_completed_months": json.dumps(
                    definition.exogenous_lags, sort_keys=True, separators=(",", ":")
                ),
                "vintage_status": "retrospective snapshot; historical extraction vintage unknown",
                "observations": row["pooled_full_n"],
                "mae": row["pooled_full_mae"],
                "rmse": row["pooled_full_rmse"],
                "smape_pct": row["pooled_full_smape"],
                "wape_pct": row["pooled_full_wape"],
                "seasonal_naive_mae_on_paired_support": row["pooled_paired_seasonal_naive_mae"],
                "mae_skill_vs_seasonal_naive": row["pooled_paired_mae_skill_vs_seasonal_naive"],
                "interpretation": definition.interpretation,
            }
        )
    return (
        pd.DataFrame(records).sort_values("feature_block", kind="mergesort").reset_index(drop=True)
    )


def _scope_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("B0", "completed", "target history and calendar reference"),
            ("B1", "completed_sensitivity", "REER snapshot vintage is not archived"),
            ("B2", "completed_sensitivity", "HICP snapshot vintage is not archived"),
            (
                "B3",
                "not_estimable",
                "legacy digital-intent series lacks query and vintage provenance",
            ),
            ("B4", "separate_common_sample", "GTD ends in 2020 and is evaluated separately"),
            ("B5", "completed_sensitivity", "joint REER/HICP snapshot-vintage block"),
            ("B6", "not_estimable", "no accepted historically aligned digital-intent panel"),
            ("B7", "not_estimable", "accepted inputs do not share a comparable full sample"),
        ],
        columns=["feature_block", "status", "reason"],
    )


def _ablation_figure(comparisons: pd.DataFrame, destination: Path) -> tuple[Path, Path]:
    absolute = comparisons.loc[comparisons["loss"] == "absolute"].copy()
    absolute["improvement_pct"] = 100 * absolute["relative_skill_vs_b0"]
    absolute["lower_pct"] = -100 * absolute["bootstrap_95_upper"] / absolute["b0_mean_loss"]
    absolute["upper_pct"] = -100 * absolute["bootstrap_95_lower"] / absolute["b0_mean_loss"]
    absolute = absolute.sort_values("feature_block", kind="mergesort")
    configure_plotting()
    fig, axis = plt.subplots(figsize=(8.2, 4.8))
    positions = np.arange(len(absolute))
    values = absolute["improvement_pct"].to_numpy(dtype=float)
    lower = values - absolute["lower_pct"].to_numpy(dtype=float)
    upper = absolute["upper_pct"].to_numpy(dtype=float) - values
    axis.bar(positions, values, color="#3679a8", width=0.62)
    axis.errorbar(
        positions,
        values,
        yerr=np.vstack([lower, upper]),
        fmt="none",
        color="#222222",
        capsize=4,
        linewidth=1.1,
    )
    axis.axhline(0, color="#222222", linewidth=0.9)
    axis.set_xticks(positions, absolute["feature_block"])
    axis.set_ylabel("MAE improvement over B0 (%)")
    axis.set_xlabel("Feature block")
    axis.set_title(
        "Incremental one-step value of lagged macro/travel-cost inputs\n"
        "Retrospective snapshot-vintage sensitivity; 95% moving-block intervals",
        loc="left",
    )
    fig.text(
        0.01,
        -0.01,
        "Source: supplied core-data snapshot; rolling one-step calculations by the reproducible "
        "pipeline. Positive values favor the added block.",
        fontsize=8,
    )
    return save_figure(fig, destination / "ablation_incremental_mae_vs_b0")


def run_snapshot_vintage_ablation(
    *,
    bootstrap_repetitions: int = 2_000,
) -> AblationArtifacts:
    """Run B0/B1/B2/B5 Ridge comparisons under a separate sensitivity protocol."""

    config = load_project_config()
    project = config.section("project")
    validation = config.section("validation")
    availability = config.section("availability_lags")
    feature_config = config.section("features")
    frame, audit = load_core_data(config.section("data")["core_csv"])
    assert_monthly_continuity(frame)
    assert_clean_source_tree()
    target_delay = int(availability["target_publication_delay_months"])
    spec = FeatureSpec(
        target_lags=tuple(int(value) for value in feature_config["target_lags"]),
        rolling_windows=tuple(int(value) for value in feature_config["rolling_windows"]),
        fourier_order=int(feature_config["fourier_order"]),
        seasonal_period=int(feature_config["seasonal_period"]),
        include_rolling_median=bool(feature_config["include_rolling_median"]),
        include_rolling_std=bool(feature_config["include_rolling_std"]),
        include_expanding_mean=bool(feature_config["include_expanding_mean"]),
        target_publication_delay_months=target_delay,
    )
    base_folds = rolling_one_step_folds(
        frame["date"],
        first_forecast=validation["rolling_start"],
        last_forecast=validation["rolling_end"],
        minimum_train_months=int(validation["minimum_train_months"]),
    )
    folds = [replace(fold, protocol=PROTOCOL) for fold in base_folds]
    blocks = _feature_blocks(availability)
    outputs = [
        backtest_tabular_fixed_origin(
            frame,
            folds,
            model_names=("ridge",),
            feature_spec=spec,
            seed=int(project["seed"]),
            tune=False,
            target_publication_delay_months=target_delay,
            parameter_grids=config.section("models"),
            exogenous_lags=block.exogenous_lags,
            feature_block=block.code,
        )
        for block in blocks
    ]
    combined = combine_outputs(*outputs)
    run_id = new_experiment_id("ablation")
    for table in (combined.forecasts, combined.fold_metrics, combined.leaderboard):
        table.insert(0, "run_id", run_id)

    run_dir = Path("results") / "runs" / run_id
    immutable_paths = write_backtest_artifacts(combined, prefix="ablation", results_dir=run_dir)
    comparisons, regimes = paired_block_comparisons(
        combined.forecasts,
        repetitions=bootstrap_repetitions,
        seed=int(project["seed"]),
    )
    comparisons.insert(0, "run_id", run_id)
    regimes.insert(0, "run_id", run_id)
    summary = _summary_table(combined.leaderboard, blocks)
    scope = _scope_status()

    immutable_tables = resolve_from_root(run_dir / "tables")
    immutable_tables.mkdir(parents=True, exist_ok=True)
    table_frames = {
        "model_ablation_snapshot_vintage.csv": summary,
        "feature_block_contribution_snapshot_vintage.csv": comparisons,
        "ablation_by_regime_snapshot_vintage.csv": regimes,
        "feature_block_scope_status.csv": scope,
    }
    for filename, table in table_frames.items():
        path = immutable_tables / filename
        table.to_csv(path, index=False)
        immutable_paths.append(path)
    figure_paths = _ablation_figure(comparisons, resolve_from_root(run_dir / "figures"))
    immutable_paths.extend(figure_paths)

    publication_tables = resolve_from_root("reports/tables")
    publication_figures = resolve_from_root("reports/figures")
    publication_tables.mkdir(parents=True, exist_ok=True)
    publication_figures.mkdir(parents=True, exist_ok=True)
    publication_paths: list[Path] = []
    for filename, table in table_frames.items():
        path = publication_tables / filename
        table.to_csv(path, index=False)
        publication_paths.append(path)
    for source in figure_paths:
        destination = publication_figures / source.name
        shutil.copyfile(source, destination)
        publication_paths.append(destination)

    artifact_records = [
        {
            "path": path.relative_to(resolve_from_root(".")).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in immutable_paths
    ]
    block_lookup = {block.code: block for block in blocks}
    for row in combined.leaderboard.to_dict(orient="records"):
        block_code = _block_from_model(str(row["model"]))
        block = block_lookup[block_code]
        append_experiment(
            {
                "run_id": run_id,
                "config_checksum": config.sha256,
                "data_checksum": audit.sha256,
                "target_definition": TARGET_DEFINITION,
                "training_window": (
                    f"{combined.fold_metrics['train_start'].min()}.."
                    f"{combined.fold_metrics['train_end'].max()}"
                ),
                "validation_folds": combined.fold_metrics.loc[
                    combined.fold_metrics["model"] == row["model"], "fold_id"
                ].tolist(),
                "forecast_horizon": "1",
                "forecast_protocol": PROTOCOL,
                "feature_block": block_code,
                "exact_features": {
                    "base": asdict(spec),
                    "exogenous_lags_completed_months": dict(block.exogenous_lags),
                },
                "model": row["model"],
                "hyperparameters": {
                    "selection": "first pre-specified Ridge grid value; no block-wise tuning",
                    "candidate_grid": config.section("models")["ridge"],
                },
                "random_seed": int(project["seed"]),
                "per_fold_metrics_path": immutable_paths[0]
                .relative_to(resolve_from_root("."))
                .as_posix(),
                "aggregate_metrics": {
                    key: value
                    for key, value in row.items()
                    if key not in {"run_id", "protocol", "model"}
                },
                "seasonal_naive_skill": row["pooled_paired_mae_skill_vs_seasonal_naive"],
                "runtime_seconds": float(
                    combined.fold_metrics.loc[
                        combined.fold_metrics["model"] == row["model"], "runtime_seconds"
                    ].sum()
                ),
                "artifact_paths": artifact_records,
                "notes": (
                    "Retrospective snapshot-vintage sensitivity only: official semantics are "
                    "verified, but the local REER/HICP extraction vintages and revision paths "
                    "are unknown. Lagged levels only; no future exogenous values consumed."
                ),
                "failure_reason": "",
            }
        )
    return AblationArtifacts(
        run_id=run_id,
        immutable_paths=tuple(immutable_paths),
        publication_paths=tuple(publication_paths),
    )
