"""Regularized and tree-model candidates with time-ordered tuning only."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin, clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import ParameterGrid, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from tourism_forecasting.data import assert_monthly_continuity
from tourism_forecasting.features import FeatureSpec, build_supervised_features


@dataclass(frozen=True)
class ModelSpec:
    name: str
    estimator: RegressorMixin
    parameter_grid: Mapping[str, Sequence[Any]]
    scale_target: bool = False


@dataclass(frozen=True)
class FittedTabularModel:
    name: str
    estimator: RegressorMixin
    feature_columns: tuple[str, ...]
    parameters: dict[str, Any]
    validation_mae: float


@dataclass(frozen=True)
class RecursiveTuningResult:
    parameters: dict[str, Any]
    validation_mae: float
    validation_origins: tuple[str, ...]


def candidate_specs(
    seed: int = 20250811,
    include_xgboost: bool = True,
    parameter_grids: Mapping[str, Mapping[str, Sequence[Any]]] | None = None,
) -> dict[str, ModelSpec]:
    specs: dict[str, ModelSpec] = {
        "ridge": ModelSpec(
            "ridge",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scale", RobustScaler()),
                    ("model", Ridge()),
                ]
            ),
            {"model__alpha": [0.1, 1.0, 10.0, 100.0]},
        ),
        "elastic_net": ModelSpec(
            "elastic_net",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scale", RobustScaler()),
                    ("model", ElasticNet(max_iter=20_000, random_state=seed)),
                ]
            ),
            {
                "model__alpha": [0.001, 0.01, 0.1, 1.0],
                "model__l1_ratio": [0.1, 0.5, 0.9],
            },
            scale_target=True,
        ),
        "hist_gradient_boosting": ModelSpec(
            "hist_gradient_boosting",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            loss="squared_error", random_state=seed, early_stopping=False
                        ),
                    ),
                ]
            ),
            {
                "model__learning_rate": [0.03, 0.07],
                "model__max_leaf_nodes": [7, 15],
                "model__l2_regularization": [1.0, 10.0],
                "model__max_iter": [200],
            },
        ),
        "random_forest": ModelSpec(
            "random_forest",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=400,
                            random_state=seed,
                            n_jobs=1,
                            max_features=0.7,
                        ),
                    ),
                ]
            ),
            {
                "model__max_depth": [4, 7, None],
                "model__min_samples_leaf": [2, 4, 8],
            },
        ),
        "extra_trees": ModelSpec(
            "extra_trees",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        ExtraTreesRegressor(
                            n_estimators=400,
                            random_state=seed,
                            n_jobs=1,
                            max_features=0.8,
                        ),
                    ),
                ]
            ),
            {
                "model__max_depth": [5, 9, None],
                "model__min_samples_leaf": [2, 4, 8],
            },
        ),
    }
    if include_xgboost:
        try:
            from xgboost import XGBRegressor

            specs["xgboost"] = ModelSpec(
                "xgboost",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        (
                            "model",
                            XGBRegressor(
                                objective="reg:squarederror",
                                n_estimators=400,
                                random_state=seed,
                                n_jobs=1,
                                tree_method="hist",
                            ),
                        ),
                    ]
                ),
                {
                    "model__learning_rate": [0.02, 0.05],
                    "model__max_depth": [2, 3],
                    "model__min_child_weight": [3, 8],
                    "model__subsample": [0.8],
                    "model__colsample_bytree": [0.8],
                    "model__reg_lambda": [10.0, 30.0],
                },
            )
        except ImportError:
            pass
    if parameter_grids:
        unknown = sorted(set(parameter_grids) - set(specs))
        if unknown:
            raise ValueError(f"Configuration contains unknown model grids: {unknown}")
        specs = {
            name: ModelSpec(
                spec.name,
                spec.estimator,
                parameter_grids.get(name, spec.parameter_grid),
                spec.scale_target,
            )
            for name, spec in specs.items()
        }
    return specs


def _wrap_target(estimator: RegressorMixin, scale_target: bool) -> RegressorMixin:
    if not scale_target:
        return estimator
    return TransformedTargetRegressor(
        regressor=estimator,
        transformer=RobustScaler(),
        check_inverse=False,
    )


def tune_time_ordered(
    spec: ModelSpec,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    n_splits: int = 4,
) -> tuple[dict[str, Any], float]:
    """Select parameters on the supplied training window using ordered inner folds."""

    X = np.asarray(features, dtype=float)
    y = np.asarray(target, dtype=float)
    if len(y) < max(36, n_splits + 2):
        raise ValueError("Insufficient observations for nested time-series tuning")
    splitter = TimeSeriesSplit(n_splits=n_splits)
    best_parameters: dict[str, Any] | None = None
    best_score = np.inf
    for parameters in ParameterGrid(dict(spec.parameter_grid)):
        fold_scores: list[float] = []
        for train_index, validation_index in splitter.split(X):
            estimator = _wrap_target(
                clone(spec.estimator).set_params(**parameters), spec.scale_target
            )
            estimator.fit(X[train_index], y[train_index])
            prediction = estimator.predict(X[validation_index])
            fold_scores.append(float(mean_absolute_error(y[validation_index], prediction)))
        score = float(np.mean(fold_scores))
        if score < best_score:
            best_score = score
            best_parameters = dict(parameters)
    if best_parameters is None:  # pragma: no cover - ParameterGrid is non-empty by construction
        raise RuntimeError("No valid parameter configuration")
    return best_parameters, best_score


def fit_tabular_model(
    spec: ModelSpec,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    feature_columns: Sequence[str] | None = None,
    tune: bool = True,
    parameters: Mapping[str, Any] | None = None,
) -> FittedTabularModel:
    columns = tuple(feature_columns or [column for column in features if column != "date"])
    valid_target = pd.to_numeric(target, errors="coerce").notna()
    X = features.loc[valid_target, columns]
    y = pd.to_numeric(target.loc[valid_target], errors="coerce")
    if tune and parameters is not None:
        raise ValueError("Specify either tune=True or explicit parameters, not both")
    if tune:
        selected_parameters, score = tune_time_ordered(spec, X, y)
    elif parameters is not None:
        selected_parameters = dict(parameters)
        score = np.nan
    else:
        selected_parameters = {key: list(values)[0] for key, values in spec.parameter_grid.items()}
        score = np.nan
    estimator = _wrap_target(
        clone(spec.estimator).set_params(**selected_parameters), spec.scale_target
    )
    estimator.fit(X, y)
    return FittedTabularModel(spec.name, estimator, columns, selected_parameters, score)


def recursive_target_history_forecast(
    model: FittedTabularModel,
    history: pd.DataFrame,
    forecast_dates: pd.DatetimeIndex,
    *,
    target_column: str = "target_original_with_missing",
    date_column: str = "date",
    feature_spec: FeatureSpec | None = None,
    exogenous_lags: Mapping[str, int] | None = None,
) -> pd.Series:
    """Recursive forecast using target history and release-safe lagged exogenous inputs.

    Future exogenous values are never inserted. Consequently, a forecast is produced only while
    every requested lag can be sourced from rows already present at the forecast origin. The
    primary use for exogenous blocks is the rolling one-step snapshot-vintage sensitivity.
    """

    working = history.sort_values(date_column, kind="stable").copy()
    assert_monthly_continuity(working, date_column)
    ordered_forecast_dates = pd.DatetimeIndex(forecast_dates).sort_values()
    if ordered_forecast_dates.has_duplicates:
        raise ValueError("Forecast dates contain duplicates")
    if len(ordered_forecast_dates):
        expected = pd.date_range(
            pd.to_datetime(working[date_column]).max() + pd.offsets.MonthBegin(1),
            periods=len(ordered_forecast_dates),
            freq="MS",
        )
        if not ordered_forecast_dates.equals(expected):
            raise ValueError("Forecast dates must be contiguous months immediately after history")
    forecasts: list[float] = []
    for date in ordered_forecast_dates:
        if (pd.to_datetime(working[date_column]) >= date).any():
            working = working[pd.to_datetime(working[date_column]) < date].copy()
        future_row = {column: np.nan for column in working.columns}
        future_row[date_column] = date
        working = pd.concat([working, pd.DataFrame([future_row])], ignore_index=True)
        built, _, _ = build_supervised_features(
            working,
            target_column=target_column,
            date_column=date_column,
            exogenous_lags=exogenous_lags,
            spec=feature_spec,
        )
        row = built.loc[[built.index[-1]], model.feature_columns]
        value = max(0.0, float(model.estimator.predict(row)[0]))
        working.loc[working.index[-1], target_column] = value
        forecasts.append(value)
    return pd.Series(forecasts, index=ordered_forecast_dates)


def tune_recursive_fixed_origin(
    spec: ModelSpec,
    history: pd.DataFrame,
    *,
    target_column: str = "target_original_with_missing",
    date_column: str = "date",
    feature_spec: FeatureSpec | None = None,
    validation_years: int = 3,
    minimum_train_months: int = 60,
) -> RecursiveTuningResult:
    """Tune on inner annual fixed-origin folds using recursive predictions.

    Unlike ordinary ``TimeSeriesSplit`` scoring, no actual target from inside an inner validation
    year is used to construct a later lag in that year.
    """

    feature_spec = feature_spec or FeatureSpec()
    ordered = history.sort_values(date_column, kind="stable").reset_index(drop=True)
    assert_monthly_continuity(ordered, date_column)
    dates = pd.to_datetime(ordered[date_column])
    last_year = int(dates.max().year)
    candidate_years = range(last_year - validation_years + 1, last_year + 1)
    folds: list[tuple[pd.DataFrame, pd.DatetimeIndex, pd.Series, str]] = []
    for year in candidate_years:
        origin = pd.Timestamp(year=year, month=1, day=1)
        inner_history = ordered[dates < origin].copy()
        validation_mask = dates.between(origin, origin + pd.DateOffset(months=11))
        validation_dates = pd.DatetimeIndex(dates[validation_mask])
        actual = pd.Series(
            ordered.loc[validation_mask, target_column].to_numpy(dtype=float),
            index=validation_dates,
        )
        if len(inner_history) < minimum_train_months or not len(validation_dates):
            continue
        available_through = origin - pd.DateOffset(
            months=feature_spec.target_publication_delay_months + 1
        )
        unavailable = pd.to_datetime(inner_history[date_column]) > available_through
        inner_history.loc[unavailable, target_column] = np.nan
        folds.append((inner_history, validation_dates, actual, f"inner_fixed_{year}"))
    if not folds:
        raise ValueError("Insufficient history for recursive nested tuning")

    cached_features = []
    for inner_history, validation_dates, actual, fold_id in folds:
        features, target, _ = build_supervised_features(
            inner_history,
            target_column=target_column,
            date_column=date_column,
            spec=feature_spec,
        )
        cached_features.append((inner_history, validation_dates, actual, fold_id, features, target))

    best_parameters: dict[str, Any] | None = None
    best_score = np.inf
    for parameters in ParameterGrid(dict(spec.parameter_grid)):
        errors: list[float] = []
        for inner_history, validation_dates, actual, _, features, target in cached_features:
            fitted = fit_tabular_model(
                spec,
                features,
                target,
                tune=False,
                parameters=parameters,
            )
            prediction = recursive_target_history_forecast(
                fitted,
                inner_history,
                validation_dates,
                target_column=target_column,
                date_column=date_column,
                feature_spec=feature_spec,
            )
            valid = actual.notna() & prediction.notna()
            errors.extend(np.abs(actual[valid] - prediction[valid]).tolist())
        if not errors:
            continue
        score = float(np.mean(errors))
        if score < best_score:
            best_score = score
            best_parameters = dict(parameters)
    if best_parameters is None:
        raise RuntimeError("No recursive tuning configuration produced a valid prediction")
    return RecursiveTuningResult(
        parameters=best_parameters,
        validation_mae=best_score,
        validation_origins=tuple(item[3] for item in cached_features),
    )
