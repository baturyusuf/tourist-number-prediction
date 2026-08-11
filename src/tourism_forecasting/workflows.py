"""Top-level workflows shared by command-line scripts and tests."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from tourism_forecasting.backtest import (
    backtest_baselines,
    backtest_tabular_fixed_origin,
    combine_outputs,
)
from tourism_forecasting.config import load_project_config
from tourism_forecasting.data import assert_monthly_continuity, load_core_data, sha256_file
from tourism_forecasting.features import FeatureSpec
from tourism_forecasting.paths import resolve_from_root
from tourism_forecasting.registry import (
    append_experiment,
    assert_clean_source_tree,
    current_git_sha,
    initialize_registry,
    new_experiment_id,
)
from tourism_forecasting.reporting import (
    build_core_audit_artifacts,
    leaderboard_markdown,
    write_backtest_artifacts,
)
from tourism_forecasting.reproduction import reproduce_2025_seasonal_naive
from tourism_forecasting.splits import annual_fixed_origin_folds, rolling_one_step_folds


def audit_workflow() -> list[Path]:
    config = load_project_config()
    frame, audit = load_core_data(config.section("data")["core_csv"])
    assert_monthly_continuity(frame)
    return build_core_audit_artifacts(frame, audit)


def reproduction_workflow() -> list[Path]:
    config = load_project_config()
    assert_clean_source_tree()
    metrics, _, _ = reproduce_2025_seasonal_naive()
    artifacts = [
        resolve_from_root("results/reproduction_metrics.csv"),
        resolve_from_root("results/reproduction_differences.csv"),
        resolve_from_root("results/reproduction_report.md"),
        resolve_from_root("results/forecasts/reproduction_2025_seasonal_naive.csv"),
    ]
    initialize_registry()
    row = metrics.iloc[0].to_dict()
    append_experiment(
        {
            "run_id": "legacy_2025_reproduction",
            "config_checksum": config.sha256,
            "data_checksum": row["data_sha256"],
            "target_definition": "departing_visitors_total_original_with_missing",
            "training_window": f"{row['train_start']}..{row['train_end']}",
            "validation_folds": ["legacy_2025"],
            "forecast_horizon": "1..12",
            "forecast_protocol": row["protocol"],
            "feature_block": "legacy_target_history_only",
            "exact_features": {"seasonal_lag_months": 12, "target_release_delay": "unverified"},
            "model": "seasonal_naive",
            "hyperparameters": {"seasonal_period": 12},
            "random_seed": None,
            "per_fold_metrics_path": "results/reproduction_metrics.csv",
            "aggregate_metrics": {
                key: row[key]
                for key in (
                    "n",
                    "mae",
                    "rmse",
                    "mape",
                    "smape",
                    "wape",
                    "mase",
                    "rmsse",
                    "r2",
                    "bias",
                )
            },
            "seasonal_naive_skill": 0.0,
            "runtime_seconds": None,
            "artifact_paths": [
                {
                    "path": path.relative_to(resolve_from_root(".")).as_posix(),
                    "sha256": sha256_file(path),
                }
                for path in artifacts
            ],
            "notes": (
                "Legacy observation-availability reproduction only; complete 2024 issue-date "
                "availability is unverified and this row is not an operational ex-ante result."
            ),
            "failure_reason": "",
        }
    )
    return artifacts


def backtest_workflow(*, include_ml: bool = True, tune_ml: bool = True) -> list[Path]:
    config = load_project_config()
    project = config.section("project")
    data_config = config.section("data")
    validation = config.section("validation")
    availability = config.section("availability_lags")
    feature_config = config.section("features")
    frame, audit = load_core_data(data_config["core_csv"])
    assert_monthly_continuity(frame)
    assert_clean_source_tree()
    target_delay = int(availability["target_publication_delay_months"])
    feature_spec = FeatureSpec(
        target_lags=tuple(int(value) for value in feature_config["target_lags"]),
        rolling_windows=tuple(int(value) for value in feature_config["rolling_windows"]),
        fourier_order=int(feature_config["fourier_order"]),
        seasonal_period=int(feature_config["seasonal_period"]),
        include_rolling_median=bool(feature_config["include_rolling_median"]),
        include_rolling_std=bool(feature_config["include_rolling_std"]),
        include_expanding_mean=bool(feature_config["include_expanding_mean"]),
        target_publication_delay_months=target_delay,
    )
    one_step = list(
        rolling_one_step_folds(
            frame["date"],
            first_forecast=validation["rolling_start"],
            last_forecast=validation["rolling_end"],
            minimum_train_months=int(validation["minimum_train_months"]),
        )
    )
    fixed = list(
        annual_fixed_origin_folds(
            frame["date"],
            first_year=int(validation["fixed_origin_first_year"]),
            last_year=int(validation["fixed_origin_last_year"]),
            minimum_train_months=int(validation["minimum_train_months"]),
        )
    )

    one_step_output = backtest_baselines(
        frame,
        one_step,
        model_names=[
            "naive_last",
            "seasonal_naive",
            "drift",
            "same_month_historical_mean",
            "seasonal_moving_average_3",
        ],
        target_publication_delay_months=target_delay,
    )
    fixed_output = backtest_baselines(
        frame,
        fixed,
        model_names=[
            "naive_last",
            "seasonal_naive",
            "drift",
            "same_month_historical_mean",
            "seasonal_moving_average_3",
            "ets_holt_winters",
            "theta",
            "sarima",
            "dynamic_harmonic_regression",
            "stl_arima",
        ],
        target_publication_delay_months=target_delay,
    )
    outputs = [one_step_output, fixed_output]
    if include_ml:
        outputs.append(
            backtest_tabular_fixed_origin(
                frame,
                one_step,
                model_names=("ridge", "hist_gradient_boosting"),
                feature_spec=feature_spec,
                seed=int(project["seed"]),
                tune=False,
                target_publication_delay_months=target_delay,
                parameter_grids=config.section("models"),
            )
        )
        outputs.append(
            backtest_tabular_fixed_origin(
                frame,
                fixed,
                model_names=("ridge", "hist_gradient_boosting", "extra_trees", "xgboost"),
                feature_spec=feature_spec,
                seed=int(project["seed"]),
                tune=tune_ml,
                target_publication_delay_months=target_delay,
                parameter_grids=config.section("models"),
            )
        )
    combined = combine_outputs(*outputs)
    run_id = new_experiment_id("run")
    combined.forecasts.insert(0, "run_id", run_id)
    combined.fold_metrics.insert(0, "run_id", run_id)
    combined.leaderboard.insert(0, "run_id", run_id)
    run_results_dir = Path("results") / "runs" / run_id
    artifacts = write_backtest_artifacts(
        combined, prefix="rolling_origin", results_dir=run_results_dir
    )
    results = resolve_from_root("results")
    combined.fold_metrics.to_csv(results / "fold_metrics.csv", index=False)
    combined.leaderboard.to_csv(results / "leaderboard.csv", index=False)

    markdown = (
        """# Validated forecasting leaderboard

Seasonal naive is the mandatory reference. Positive skill means lower loss than seasonal naive.
Protocols are separate; values from incompatible tasks must not be compared as one competition.
`pooled_full_*` reports every evaluable model target. `pooled_paired_*` and skill use the exact
model/seasonal-naive common support. Macro-fold quantities remain in the CSV artifact.

"""
        + leaderboard_markdown(combined.leaderboard)
        + "\n"
    )
    resolve_from_root("LEADERBOARD.md").write_text(markdown, encoding="utf-8")

    initialize_registry()
    baseline_configurations: dict[str, dict[str, object]] = {
        "naive_last": {"rule": "last available observed target"},
        "seasonal_naive": {
            "seasonal_period": 12,
            "unavailable_reference_policy": "recursive preceding-season projection",
        },
        "drift": {"rule": "last available level plus calendar-month drift"},
        "same_month_historical_mean": {"calendar_month_climatology": True},
        "seasonal_moving_average_3": {"seasonal_period": 12, "prior_seasons": 3},
        "ets_holt_winters": {
            "trend": "additive_damped",
            "seasonal": "additive",
            "seasonal_period": 12,
        },
        "theta": {"seasonal_period": 12, "deseasonalize": True},
        "sarima_111_111_12": {
            "order": [1, 1, 1],
            "seasonal_order": [1, 1, 1, 12],
            "trend": "constant",
        },
        "dynamic_harmonic_arima_k2": {
            "arima_order": [1, 1, 1],
            "fourier_order": 2,
            "seasonal_period": 12,
        },
        "stl_arima_111": {
            "decomposition": "robust_STL",
            "seasonal_period": 12,
            "remainder_order": [1, 1, 1],
        },
    }
    for (protocol, model), group in combined.fold_metrics.groupby(
        ["protocol", "model"], dropna=False
    ):
        failure_reason = " | ".join(
            sorted(set(group.get("failure_reason", pd.Series(dtype="string")).dropna().astype(str)))
        )
        aggregate = (
            combined.leaderboard[
                (combined.leaderboard["protocol"] == protocol)
                & (combined.leaderboard["model"] == model)
            ]
            .drop(columns=["protocol", "model"], errors="ignore")
            .to_dict(orient="records")
        )
        is_tabular = str(model).endswith("_recursive_b0")
        base_model = str(model).removesuffix("_recursive_b0")
        fold_notes = sorted(set(group.get("notes", pd.Series(dtype="string")).dropna().astype(str)))
        if is_tabular:
            exact_features: object = asdict(feature_spec)
            hyperparameters: object = {
                "candidate_grid": config.section("models").get(base_model, {}),
                "fold_notes": fold_notes,
            }
            feature_block = "B0_target_history_calendar"
            random_seed: int | None = int(project["seed"])
        else:
            exact_features = {"target_history": True, "calendar_index": "model_internal"}
            hyperparameters = {
                "configuration": baseline_configurations.get(str(model), {}),
                "fold_notes": fold_notes,
            }
            feature_block = "B0_univariate_target_history"
            random_seed = None
        append_experiment(
            {
                "data_checksum": audit.sha256,
                "run_id": run_id,
                "config_checksum": config.sha256,
                "target_definition": "departing_visitors_total_original_with_missing",
                "training_window": f"{group['train_start'].min()}..{group['train_end'].max()}",
                "validation_folds": group["fold_id"].dropna().tolist(),
                "forecast_horizon": "1" if protocol == "one_step_ex_ante" else "1..12",
                "forecast_protocol": protocol,
                "feature_block": feature_block,
                "exact_features": exact_features,
                "model": model,
                "hyperparameters": hyperparameters,
                "random_seed": random_seed,
                "per_fold_metrics_path": artifacts[0]
                .relative_to(resolve_from_root("."))
                .as_posix(),
                "aggregate_metrics": aggregate[0] if aggregate else {},
                "seasonal_naive_skill": (
                    float(aggregate[0]["pooled_paired_mae_skill_vs_seasonal_naive"])
                    if aggregate
                    and pd.notna(aggregate[0].get("pooled_paired_mae_skill_vs_seasonal_naive"))
                    else None
                ),
                "runtime_seconds": float(group["runtime_seconds"].sum()),
                "artifact_paths": [
                    {
                        "path": path.relative_to(resolve_from_root(".")).as_posix(),
                        "sha256": sha256_file(path),
                    }
                    for path in artifacts
                ],
                "notes": (
                    f"run_id={run_id}; git_sha={current_git_sha()}; all outer folds retained; "
                    "no random split or final-test tuning"
                ),
                "failure_reason": failure_reason,
            }
        )
    return artifacts + [results / "fold_metrics.csv", results / "leaderboard.csv"]


def reproduce_workflow(*, include_ml: bool = True) -> list[Path]:
    artifacts = []
    artifacts.extend(audit_workflow())
    artifacts.extend(reproduction_workflow())
    artifacts.extend(backtest_workflow(include_ml=include_ml))
    return artifacts
