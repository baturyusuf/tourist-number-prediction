"""Aggregate-only GTD robustness, association, and pseudo-real-time forecast analysis."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from tourism_forecasting.config import load_project_config
from tourism_forecasting.data import load_core_data, sha256_file
from tourism_forecasting.gtd import (
    TOURISM_CENTERS,
    aggregate_gtd_monthly,
    haversine_km,
    read_gtd,
)
from tourism_forecasting.paths import resolve_from_root
from tourism_forecasting.registry import (
    append_experiment,
    assert_clean_source_tree,
    new_experiment_id,
)
from tourism_forecasting.reporting import configure_plotting, save_figure

ANALYSIS_START = pd.Timestamp("2008-01-01")
ANALYSIS_END = pd.Timestamp("2020-12-01")
FORECAST_START = pd.Timestamp("2015-01-01")
TARGET_DELAY_MONTHS = 3
RANDOM_SEED = 20250811


def _numeric(events: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(events.get(column, pd.Series(np.nan, index=events.index)), errors="coerce")


def gtd_definition_subsets(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return prespecified event-definition sensitivities without exporting their rows."""

    doubt = _numeric(events, "doubtterr")
    success = _numeric(events, "success")
    criteria = pd.concat([_numeric(events, f"crit{number}") for number in (1, 2, 3)], axis=1)
    latitude = _numeric(events, "latitude")
    longitude = _numeric(events, "longitude")
    coordinate_known = latitude.notna() & longitude.notna()
    distances = np.column_stack(
        [
            haversine_km(latitude, longitude, center_latitude, center_longitude)
            for center_latitude, center_longitude in TOURISM_CENTERS.values()
        ]
    )
    nearest_distance = np.where(np.isnan(distances), np.inf, distances).min(axis=1)
    near_tourism_center = coordinate_known & (nearest_distance <= 100)
    strict = doubt.eq(0) & criteria.eq(1).all(axis=1)
    return {
        "broad_all_gtd": events,
        "doubtterr_zero": events.loc[doubt.eq(0)],
        "strict_all_criteria_doubtterr_zero": events.loc[strict],
        "successful_only": events.loc[success.eq(1)],
        "known_coordinates_only": events.loc[coordinate_known],
        "strict_known_coordinates": events.loc[strict & coordinate_known],
        "within_100km_tourism_centers": events.loc[near_tourism_center],
        "strict_within_100km_tourism_centers": events.loc[strict & near_tourism_center],
    }


def aggregate_definition_sensitivities(
    events: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Aggregate each definition monthly and return only non-granular summary statistics."""

    analysis_index = pd.date_range(ANALYSIS_START, ANALYSIS_END, freq="MS")
    monthly_by_definition: dict[str, pd.DataFrame] = {}
    summary_records: list[dict[str, object]] = []
    for name, subset in gtd_definition_subsets(events).items():
        monthly, metadata = aggregate_gtd_monthly(subset)
        monthly = monthly.set_index("date").reindex(analysis_index)
        # Zero means no event only inside verified GTD coverage. Missing event attributes
        # remain NaN.
        count_columns = [
            "incidents",
            "successful_incidents",
            "events_unknown_success",
            "events_missing_fatalities",
            "events_missing_injuries",
            "events_partial_unknown_severity",
            "tourism_transport_targets",
            "hotel_resort_targets",
            "events_missing_coordinates",
            "incidents_within_100km_known",
        ]
        monthly[count_columns] = monthly[count_columns].fillna(0)
        monthly = monthly.rename_axis("date").reset_index()
        monthly["source_method_break_post_2008_04"] = monthly["date"].ge("2008-04-01").astype(int)
        monthly["source_method_break_post_2012_01"] = monthly["date"].ge("2012-01-01").astype(int)
        monthly_by_definition[name] = monthly
        incidents = float(monthly["incidents"].sum())
        incomplete = float(monthly["events_partial_unknown_severity"].sum())
        coordinate_missing = float(monthly["events_missing_coordinates"].sum())
        summary_records.append(
            {
                "definition": name,
                "period_start": "2008-01",
                "period_end": "2020-12",
                "months": len(monthly),
                "incidents": int(incidents),
                "active_months": int(monthly["incidents"].gt(0).sum()),
                "successful_incidents": int(monthly["successful_incidents"].sum()),
                "events_unknown_success": int(monthly["events_unknown_success"].sum()),
                "tourism_transport_targets": int(monthly["tourism_transport_targets"].sum()),
                "hotel_resort_targets": int(monthly["hotel_resort_targets"].sum()),
                "complete_case_severity_sum": float(monthly["severity_known"].sum(min_count=1)),
                "events_incomplete_severity": int(incomplete),
                "complete_case_severity_event_share": (
                    (incidents - incomplete) / incidents if incidents else np.nan
                ),
                "events_missing_coordinates": int(coordinate_missing),
                "incidents_within_100km_known": int(monthly["incidents_within_100km_known"].sum()),
                "known_coordinate_event_share": (
                    (incidents - coordinate_missing) / incidents if incidents else np.nan
                ),
                "unknown_month_events_excluded": metadata.skipped_unknown_month,
                "guardrail": (
                    "aggregate descriptive sensitivity; unknown attributes are not recoded as zero"
                ),
            }
        )
    return monthly_by_definition, pd.DataFrame(summary_records)


def _availability_lagged_risk(monthly: pd.DataFrame, delay_months: int) -> pd.Series:
    # At the end of t-1, a three-completed-month delay permits values only through t-4.
    return (
        monthly.set_index("date")["incidents"]
        .rolling(3, min_periods=3)
        .sum()
        .shift(delay_months + 1)
    )


def association_sensitivity(
    core: pd.DataFrame,
    monthly_by_definition: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Estimate contemporaneous non-causal associations with GTD method-break controls."""

    target = core.set_index("date")["target_original_with_missing"].loc[ANALYSIS_START:ANALYSIS_END]
    records: list[dict[str, object]] = []
    for definition, monthly in monthly_by_definition.items():
        risk = monthly.set_index("date")["incidents"].rename("monthly_incidents")
        data = pd.concat([target.rename("target"), risk], axis=1).dropna()
        data["log_target"] = np.log1p(data["target"])
        data["trend_years"] = np.arange(len(data), dtype=float) / 12
        data["post_2008_04"] = (data.index >= pd.Timestamp("2008-04-01")).astype(float)
        data["post_2012_01"] = (data.index >= pd.Timestamp("2012-01-01")).astype(float)
        month_dummies = pd.get_dummies(
            data.index.month, prefix="month", drop_first=True, dtype=float
        )
        month_dummies.index = data.index
        design = pd.concat(
            [
                data[["monthly_incidents", "trend_years", "post_2008_04", "post_2012_01"]],
                month_dummies,
            ],
            axis=1,
        )
        fitted = sm.OLS(data["log_target"], sm.add_constant(design), missing="drop").fit(
            cov_type="HAC", cov_kwds={"maxlags": 12}
        )
        coefficient = float(fitted.params["monthly_incidents"])
        interval = fitted.conf_int().loc["monthly_incidents"]
        records.append(
            {
                "definition": definition,
                "outcome": "log1p_monthly_departing_visitors",
                "security_term": "contemporaneous_monthly_incidents",
                "target_months": len(data),
                "coefficient_log_points_per_incident": coefficient,
                "hac_standard_error": float(fitted.bse["monthly_incidents"]),
                "hac_p_value": float(fitted.pvalues["monthly_incidents"]),
                "hac_95_ci_lower": float(interval.iloc[0]),
                "hac_95_ci_upper": float(interval.iloc[1]),
                "approx_percent_difference_per_incident": 100 * np.expm1(coefficient),
                "controls": (
                    "calendar-month indicators; linear trend; GTD method breaks 2008-04 and 2012-01"
                ),
                "interpretation": "descriptive association only; not causal evidence",
            }
        )
    return pd.DataFrame(records)


def _base_forecast_features(target: pd.Series) -> pd.DataFrame:
    features = pd.DataFrame(index=target.index)
    for lag in (4, 6, 12, 13, 18, 24):
        features[f"target_lag_{lag}"] = target.shift(lag)
    features["target_roll3_available"] = target.rolling(3, min_periods=1).mean().shift(4)
    features["target_roll12_available"] = target.rolling(12, min_periods=3).mean().shift(4)
    month = features.index.month
    features["month_sin"] = np.sin(2 * np.pi * month / 12)
    features["month_cos"] = np.cos(2 * np.pi * month / 12)
    features["trend_years"] = np.arange(len(features), dtype=float) / 12
    return features


def _forecast_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    denominator = (np.abs(actual) + np.abs(predicted)) / 2
    smape = np.mean(np.divide(np.abs(actual - predicted), denominator, where=denominator != 0))
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "smape_percent": float(100 * smape),
    }


def _moving_block_interval(
    differences: np.ndarray,
    *,
    block_length: int = 12,
    repetitions: int = 2_000,
    seed: int = RANDOM_SEED,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(differences, dtype=float)
    starts = np.arange(max(1, len(values) - block_length + 1))
    means = np.empty(repetitions)
    for repetition in range(repetitions):
        sample: list[float] = []
        while len(sample) < len(values):
            start = int(rng.choice(starts))
            sample.extend(values[start : start + block_length])
        means[repetition] = np.mean(sample[: len(values)])
    lower, upper = np.quantile(means, [0.025, 0.975])
    return float(lower), float(upper)


def predictive_value_sensitivity(
    core: pd.DataFrame,
    monthly_by_definition: Mapping[str, pd.DataFrame],
    *,
    delay_months: int = TARGET_DELAY_MONTHS,
) -> pd.DataFrame:
    """Compare B4 to B0 on identical one-step observations without exporting forecasts.

    GTD reporting vintages were not supplied. The delay is therefore a conservative timing
    sensitivity applied equally to outcomes and security counts, not a verified release calendar.
    """

    target = core.set_index("date")["target_original_with_missing"].loc[ANALYSIS_START:ANALYSIS_END]
    base_features = _base_forecast_features(target)
    forecast_dates = target.loc[FORECAST_START:ANALYSIS_END].dropna().index
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", RobustScaler()),
            ("ridge", Ridge(alpha=10.0)),
        ]
    )
    records: list[dict[str, object]] = []
    for definition, monthly in monthly_by_definition.items():
        security = _availability_lagged_risk(monthly, delay_months).rename("security_roll3")
        combined = base_features.join(security)
        predictions: dict[str, list[float]] = {"b0": [], "b4": []}
        actuals: list[float] = []
        for date in forecast_dates:
            available_through = date - pd.DateOffset(months=delay_months + 1)
            training_mask = (
                (combined.index <= available_through)
                & target.notna()
                & combined["security_roll3"].notna()
            )
            training_dates = combined.index[training_mask]
            if len(training_dates) < 48 or pd.isna(combined.loc[date, "security_roll3"]):
                continue
            b0_columns = list(base_features.columns)
            b4_columns = [*b0_columns, "security_roll3"]
            for key, columns in (("b0", b0_columns), ("b4", b4_columns)):
                fitted = clone(model)
                fitted.fit(combined.loc[training_dates, columns], target.loc[training_dates])
                predictions[key].append(float(fitted.predict(combined.loc[[date], columns])[0]))
            actuals.append(float(target.loc[date]))
        actual_array = np.asarray(actuals)
        b0 = np.asarray(predictions["b0"])
        b4 = np.asarray(predictions["b4"])
        b0_metrics = _forecast_metrics(actual_array, b0)
        b4_metrics = _forecast_metrics(actual_array, b4)
        absolute_loss_difference = np.abs(actual_array - b4) - np.abs(actual_array - b0)
        lower, upper = _moving_block_interval(absolute_loss_difference)
        records.append(
            {
                "security_definition": definition,
                "protocol": "rolling_one_step_common_sample",
                "forecast_start": forecast_dates.min().strftime("%Y-%m"),
                "forecast_end": forecast_dates.max().strftime("%Y-%m"),
                "evaluated_months": len(actual_array),
                "target_publication_delay_months_assumed": delay_months,
                "security_reporting_delay_months_assumed": delay_months,
                "b0_mae": b0_metrics["mae"],
                "b4_mae": b4_metrics["mae"],
                "b4_mae_skill_vs_b0": 1 - b4_metrics["mae"] / b0_metrics["mae"],
                "b0_rmse": b0_metrics["rmse"],
                "b4_rmse": b4_metrics["rmse"],
                "b4_rmse_skill_vs_b0": 1 - b4_metrics["rmse"] / b0_metrics["rmse"],
                "b0_smape_percent": b0_metrics["smape_percent"],
                "b4_smape_percent": b4_metrics["smape_percent"],
                "mean_absolute_loss_difference_b4_minus_b0": float(absolute_loss_difference.mean()),
                "block_bootstrap_95_ci_lower": lower,
                "block_bootstrap_95_ci_upper": upper,
                "block_length_months": 12,
                "model": "ridge_alpha_10_prespecified",
                "interpretation": (
                    "retrospective snapshot timing sensitivity; not an operational vintage test"
                ),
            }
        )
    return pd.DataFrame(records)


def _write_method_note(
    path: Path,
    summary: pd.DataFrame,
    association: pd.DataFrame,
    predictive: pd.DataFrame,
    source_sha256: str,
) -> None:
    broad = summary.loc[summary["definition"].eq("broad_all_gtd")].iloc[0]
    best = predictive.sort_values("b4_mae_skill_vs_b0", ascending=False).iloc[0]
    text = f"""# GTD aggregate robustness analysis

This licensed-data analysis uses only selected GTD fields in memory and writes no event-level or
monthly derivative. The source workbook SHA-256 is `{source_sha256}`. Outputs are aggregate
definition summaries, model summaries, and an annual figure; redistribution remains subject to the
GTD end-user license.

## Coverage and coding

The common tourism overlap is January 2008 through December 2020; the series is not extended with
zeros after GTD coverage ends. The broad definition contains {int(broad['incidents']):,} incidents.
Unknown month is excluded, unknown success remains unknown, missing coordinates remain unknown, and
severity is summed only for events with both fatality and injury fields observed. The tables report
the incomplete-severity and missing-coordinate shares. Sensitivities cover `doubtterr == 0`, all
three GTD criteria plus `doubtterr == 0`, successful events, coordinate-known events, events within
100 km of a prespecified tourism center, and strict intersections. Hotel/resort targets are reported
separately from the broader tourism and transport target flag.

## Association analysis

The descriptive regressions relate log monthly visitors to contemporaneous monthly incident counts.
They include calendar-month indicators, a linear trend, and GTD method indicators at April 2008 and
January 2012. HAC standard errors use 12 lags. These estimates are associations, not predictive or
causal effects; source construction, omitted shocks, simultaneity, and measurement error preclude
causal wording. Availability-lagged security features are used only in the predictive sensitivity.

## Predictive-value sensitivity

The comparison uses rolling one-step forecasts from 2015 through 2020 on an identical common sample.
Both B0 and B4 use only visitor targets through `t-4`, corresponding to the project-wide assumption
of three completed months of publication delay. B4 also uses a three-month GTD incident sum through
`t-4`. The GTD workbook is a final retrospective snapshot, and no issue-date archive or verified GTD
release calendar was available; the security timing rule is deliberately labeled an assumption,
not a fact. Models are prespecified ridge regressions (`alpha=10`) and block-bootstrap intervals use
12-month blocks. No observation-level forecasts are written.

The largest point-estimate B4 MAE skill is {best['b4_mae_skill_vs_b0']:.1%} for
`{best['security_definition']}`; its block-bootstrap interval for B4 minus B0 absolute loss is
[{best['block_bootstrap_95_ci_lower']:,.0f}, {best['block_bootstrap_95_ci_upper']:,.0f}]. A point
estimate is not treated as reliable incremental value when that interval crosses zero.

## Artifact boundary

- `gtd_definition_sensitivity_summary.csv`: aggregate coding and missingness sensitivity.
- `gtd_association_sensitivity.csv`: aggregate HAC coefficients only.
- `gtd_predictive_common_sample.csv`: aggregate common-sample error metrics only.
- `gtd_annual_security_sensitivity.(png|svg)`: annual broad/strict counts and coordinate coverage.

No GTD event row, identifier, narrative, actor, source citation, codebook, or monthly derivative is
included in the repository.
"""
    path.write_text(text, encoding="utf-8", newline="\n")


def build_gtd_robustness_artifacts(
    *,
    gtd_path: str | Path = "data/kaggle/global_terrorism.xlsx",
    tables_dir: str | Path = "reports/tables",
    figures_dir: str | Path = "reports/figures",
    docs_dir: str | Path = "docs",
) -> list[Path]:
    """Run the aggregate analysis and write only license-safe outputs."""

    assert_clean_source_tree()
    started = perf_counter()
    run_id = new_experiment_id("gtd")
    config = load_project_config()
    source = resolve_from_root(gtd_path)
    events = read_gtd(source)
    core, core_audit = load_core_data()
    monthly_by_definition, summary = aggregate_definition_sensitivities(events)
    association = association_sensitivity(core, monthly_by_definition)
    predictive = predictive_value_sensitivity(core, monthly_by_definition)
    for frame in (summary, association, predictive):
        frame.insert(0, "run_id", run_id)

    tables = resolve_from_root(tables_dir)
    figures = resolve_from_root(figures_dir)
    docs = resolve_from_root(docs_dir)
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []
    for frame, name in (
        (summary, "gtd_definition_sensitivity_summary.csv"),
        (association, "gtd_association_sensitivity.csv"),
        (predictive, "gtd_predictive_common_sample.csv"),
    ):
        destination = tables / name
        frame.to_csv(destination, index=False)
        artifacts.append(destination)

    configure_plotting()
    broad = monthly_by_definition["broad_all_gtd"].copy()
    strict = monthly_by_definition["strict_all_criteria_doubtterr_zero"].copy()
    annual = (
        broad.assign(year=broad["date"].dt.year)
        .groupby("year", as_index=False)
        .agg(
            broad_incidents=("incidents", "sum"),
            missing_coordinates=("events_missing_coordinates", "sum"),
        )
    )
    annual_strict = (
        strict.assign(year=strict["date"].dt.year)
        .groupby("year", as_index=False)
        .agg(strict_incidents=("incidents", "sum"))
    )
    annual = annual.merge(annual_strict, on="year")
    annual["known_coordinate_share"] = 1 - annual["missing_coordinates"] / annual[
        "broad_incidents"
    ].replace(0, np.nan)
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(annual["year"], annual["broad_incidents"], marker="o", label="Broad GTD")
    axes[0].plot(
        annual["year"],
        annual["strict_incidents"],
        marker="o",
        label="All criteria and doubtterr=0",
    )
    axes[0].set_ylabel("Annual incidents")
    axes[0].set_title("Türkiye GTD definition and coordinate sensitivities, 2008-2020", loc="left")
    axes[0].legend(frameon=False)
    axes[1].plot(annual["year"], annual["known_coordinate_share"] * 100, marker="o")
    axes[1].set_ylabel("Known coordinates (%)")
    axes[1].set_xlabel("Year")
    axes[1].set_ylim(0, 105)
    fig.text(
        0.01,
        -0.01,
        "Source: licensed GTD 1970-2020 distribution; aggregate calculations only. "
        "No post-2020 zero fill.",
        fontsize=8,
    )
    artifacts.extend(save_figure(fig, figures / "gtd_annual_security_sensitivity"))

    method_note = docs / "gtd_robustness.md"
    _write_method_note(method_note, summary, association, predictive, sha256_file(source))
    artifacts.append(method_note)

    immutable_dir = resolve_from_root(Path("results") / "runs" / run_id / "gtd_aggregate")
    immutable_dir.mkdir(parents=True, exist_ok=True)
    immutable_paths: list[Path] = []
    for artifact in artifacts:
        destination = immutable_dir / artifact.name
        shutil.copyfile(artifact, destination)
        immutable_paths.append(destination)
    artifact_records = [
        {
            "path": path.relative_to(resolve_from_root(".")).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in immutable_paths
    ]
    data_checksums = {
        "core_csv": core_audit.sha256,
        "licensed_gtd_workbook": sha256_file(source),
    }
    evaluable_dates = core.loc[
        core["date"].between(FORECAST_START, ANALYSIS_END)
        & core["target_original_with_missing"].notna(),
        "date",
    ]
    fold_ids = [f"gtd_one_step_{date:%Y%m}" for date in evaluable_dates]
    runtime = perf_counter() - started
    append_experiment(
        {
            "run_id": run_id,
            "config_checksum": config.sha256,
            "data_checksum": data_checksums,
            "target_definition": "departing_visitors_total_original_with_missing",
            "training_window": "2008-01..2020-12",
            "validation_folds": ["descriptive monthly common-sample association"],
            "forecast_horizon": "not_applicable",
            "forecast_protocol": "statistical_association_hac_common_sample",
            "feature_block": "B4_security_risk",
            "exact_features": {
                "security": "contemporaneous monthly incident count",
                "sensitivities": association["definition"].tolist(),
                "controls": "month indicators, linear trend, 2008-04 and 2012-01 breaks",
            },
            "model": "ols_hac12_noncausal_association",
            "hyperparameters": {"hac_lags": 12},
            "random_seed": None,
            "per_fold_metrics_path": "",
            "aggregate_metrics": association.to_dict(orient="records"),
            "seasonal_naive_skill": None,
            "runtime_seconds": runtime,
            "artifact_paths": artifact_records,
            "notes": (
                "Aggregate-only licensed GTD association; no event rows or monthly derivative "
                "written; estimates are descriptive and non-causal."
            ),
            "failure_reason": "",
        }
    )
    for row in predictive.to_dict(orient="records"):
        append_experiment(
            {
                "run_id": run_id,
                "config_checksum": config.sha256,
                "data_checksum": data_checksums,
                "target_definition": "departing_visitors_total_original_with_missing",
                "training_window": "2008-01..2020-12",
                "validation_folds": fold_ids,
                "forecast_horizon": "1",
                "forecast_protocol": "gtd_common_sample_snapshot_vintage_sensitivity",
                "feature_block": "B4_security_risk",
                "exact_features": {
                    "definition": row["security_definition"],
                    "security_feature": "three-month incident sum available through t-4",
                    "target_features": "prespecified release-delayed B0",
                    "method_breaks_reported": ["2008-04", "2012-01"],
                },
                "model": f"ridge_alpha10_b4_{row['security_definition']}",
                "hyperparameters": {
                    "ridge_alpha": 10.0,
                    "selection": "prespecified; no common-sample outcome tuning",
                    "bootstrap_block_months": 12,
                    "bootstrap_repetitions": 2_000,
                },
                "random_seed": RANDOM_SEED,
                "per_fold_metrics_path": "",
                "aggregate_metrics": row,
                "seasonal_naive_skill": None,
                "runtime_seconds": runtime,
                "artifact_paths": artifact_records,
                "notes": (
                    "Aggregate-only B4-versus-B0 retrospective snapshot timing sensitivity; "
                    "no event/monthly derivative or observation forecasts written; GTD issue "
                    "dates are unavailable."
                ),
                "failure_reason": "",
            }
        )
    return [*artifacts, *immutable_paths, resolve_from_root("results/experiment_registry.csv")]
