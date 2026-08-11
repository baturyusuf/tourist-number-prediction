"""License-safe GTD transformations; raw GTD data are never written by this module."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from tourism_forecasting.paths import resolve_from_root

TOURISM_CENTERS: Mapping[str, tuple[float, float]] = {
    "Istanbul": (41.0082, 28.9784),
    "Antalya": (36.8969, 30.7133),
    "Mugla": (37.2153, 28.3636),
    "Izmir": (38.4237, 27.1428),
    "Nevsehir_Cappadocia": (38.6244, 34.7239),
}

GTD_ANALYSIS_COLUMNS: tuple[str, ...] = (
    "iyear",
    "imonth",
    "country_txt",
    "crit1",
    "crit2",
    "crit3",
    "doubtterr",
    "success",
    "nkill",
    "nwound",
    "latitude",
    "longitude",
    "targtype1_txt",
    "targsubtype1_txt",
)


@dataclass(frozen=True)
class GTDAggregationMetadata:
    source_path: str
    input_rows: int
    turkey_rows: int
    skipped_unknown_month: int
    first_month: str
    last_month: str
    strict_definition: bool


def haversine_km(
    latitude_1: float | np.ndarray,
    longitude_1: float | np.ndarray,
    latitude_2: float | np.ndarray,
    longitude_2: float | np.ndarray,
) -> np.ndarray:
    lat1, lon1, lat2, lon2 = map(
        np.radians,
        [latitude_1, longitude_1, latitude_2, longitude_2],
    )
    delta_latitude = lat2 - lat1
    delta_longitude = lon2 - lon1
    a = (
        np.sin(delta_latitude / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(delta_longitude / 2) ** 2
    )
    return 6_371.0088 * 2 * np.arcsin(np.sqrt(a))


def read_gtd(path: str | Path = "data/kaggle/global_terrorism.xlsx") -> pd.DataFrame:
    """Read only fields required by the aggregate robustness analysis.

    Excluding identifiers, narratives, actor names, and source citations reduces memory use and
    makes accidental propagation of licensed event-level content structurally less likely.
    """

    source = resolve_from_root(path)
    if source.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(source, usecols=list(GTD_ANALYSIS_COLUMNS))
    return pd.read_csv(source, usecols=list(GTD_ANALYSIS_COLUMNS), low_memory=False)


def aggregate_gtd_monthly(
    events: pd.DataFrame,
    *,
    country_names: tuple[str, ...] = ("Turkey", "Türkiye", "Turkiye"),
    strict_definition: bool = False,
) -> tuple[pd.DataFrame, GTDAggregationMetadata]:
    required = {"iyear", "imonth", "country_txt"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"GTD input is missing required columns: {missing}")
    selected = events[events["country_txt"].isin(country_names)].copy()
    unknown_month = pd.to_numeric(selected["imonth"], errors="coerce").fillna(0).eq(0)
    skipped_unknown_month = int(unknown_month.sum())
    selected = selected.loc[~unknown_month].copy()
    if strict_definition and "doubtterr" in selected:
        selected = selected[pd.to_numeric(selected["doubtterr"], errors="coerce").fillna(1).eq(0)]

    selected["date"] = pd.to_datetime(
        {
            "year": pd.to_numeric(selected["iyear"], errors="coerce"),
            "month": pd.to_numeric(selected["imonth"], errors="coerce"),
            "day": 1,
        },
        errors="coerce",
    )
    selected = selected[selected["date"].notna()].copy()
    for column in ("nkill", "nwound"):
        if column not in selected:
            selected[column] = np.nan
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
        # GTD special negative codes and missing values mean unknown, not zero.
        selected.loc[selected[column] < 0, column] = np.nan
    selected["fatalities"] = selected["nkill"].clip(lower=0)
    selected["injuries"] = selected["nwound"].clip(lower=0)
    selected["fatalities_missing"] = selected["fatalities"].isna().astype(int)
    selected["injuries_missing"] = selected["injuries"].isna().astype(int)
    all_casualties_known = selected[["fatalities", "injuries"]].notna().all(axis=1)
    selected["severity"] = (
        selected["fatalities"].fillna(0) + 0.25 * selected["injuries"].fillna(0)
    ).where(all_casualties_known)
    selected["severity_partial_unknown"] = (~all_casualties_known).astype(int)
    success = (
        selected["success"] if "success" in selected else pd.Series(np.nan, index=selected.index)
    )
    success_numeric = pd.to_numeric(success, errors="coerce")
    selected["success_numeric"] = success_numeric.eq(1).astype(int)
    selected["success_unknown"] = (~success_numeric.isin([0, 1])).astype(int)
    target_type = selected.get("targtype1_txt", pd.Series("", index=selected.index)).astype(
        "string"
    )
    target_subtype = selected.get("targsubtype1_txt", pd.Series("", index=selected.index)).astype(
        "string"
    )
    target_text = target_type.fillna("") + " " + target_subtype.fillna("")
    selected["tourism_transport_target"] = target_text.str.contains(
        "Tourist|Transportation|Airport|Hotel|Resort|Lodging",
        case=False,
        regex=True,
        na=False,
    ).astype(int)
    selected["hotel_resort_target"] = (
        target_subtype.fillna("")
        .str.contains(
            "Hotel|Resort|Lodging",
            case=False,
            regex=True,
            na=False,
        )
        .astype(int)
    )

    latitude_source = (
        selected["latitude"] if "latitude" in selected else pd.Series(np.nan, index=selected.index)
    )
    longitude_source = (
        selected["longitude"]
        if "longitude" in selected
        else pd.Series(np.nan, index=selected.index)
    )
    latitude = pd.to_numeric(latitude_source, errors="coerce")
    longitude = pd.to_numeric(longitude_source, errors="coerce")
    distances = []
    for center_latitude, center_longitude in TOURISM_CENTERS.values():
        distances.append(haversine_km(latitude, longitude, center_latitude, center_longitude))
    coordinate_missing = latitude.isna() | longitude.isna()
    selected["nearest_tourism_center_km"] = np.nan
    distance_matrix = np.column_stack(distances)
    selected.loc[~coordinate_missing, "nearest_tourism_center_km"] = np.nanmin(
        distance_matrix[~coordinate_missing.to_numpy()], axis=1
    )
    selected["coordinate_missing"] = coordinate_missing.astype(int)
    within_100 = selected["nearest_tourism_center_km"].le(100).astype("Int64")
    within_100.loc[selected["coordinate_missing"].eq(1)] = pd.NA
    selected["within_100km_tourism_center"] = within_100

    monthly = selected.groupby("date", as_index=False).agg(
        incidents=("date", "size"),
        successful_incidents=("success_numeric", "sum"),
        events_unknown_success=("success_unknown", "sum"),
        fatalities_known=("fatalities", lambda values: values.sum(min_count=1)),
        injuries_known=("injuries", lambda values: values.sum(min_count=1)),
        events_missing_fatalities=("fatalities_missing", "sum"),
        events_missing_injuries=("injuries_missing", "sum"),
        severity_known=("severity", lambda values: values.sum(min_count=1)),
        events_partial_unknown_severity=("severity_partial_unknown", "sum"),
        tourism_transport_targets=("tourism_transport_target", "sum"),
        hotel_resort_targets=("hotel_resort_target", "sum"),
        incidents_within_100km_known=(
            "within_100km_tourism_center",
            lambda values: values.sum(min_count=1),
        ),
        events_missing_coordinates=("coordinate_missing", "sum"),
    )
    if monthly.empty:
        raise ValueError("No Türkiye events remain after documented filters")
    full_index = pd.date_range(monthly["date"].min(), monthly["date"].max(), freq="MS")
    monthly = (
        monthly.set_index("date")
        .reindex(full_index, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )
    for window in (3, 6, 12):
        monthly[f"incidents_roll_{window}_through_t"] = (
            monthly["incidents"].rolling(window, min_periods=1).sum()
        )
        monthly[f"severity_known_roll_{window}_through_t"] = (
            monthly["severity_known"].rolling(window, min_periods=1).sum()
        )
        monthly[f"incidents_roll_{window}_lag1"] = monthly[
            f"incidents_roll_{window}_through_t"
        ].shift(1)
        monthly[f"severity_known_roll_{window}_lag1"] = monthly[
            f"severity_known_roll_{window}_through_t"
        ].shift(1)
    monthly["source_method_break_post_1998_01"] = monthly["date"].ge("1998-01-01").astype(int)
    monthly["source_method_break_post_2008_04"] = monthly["date"].ge("2008-04-01").astype(int)
    monthly["source_method_break_post_2012_01"] = monthly["date"].ge("2012-01-01").astype(int)
    metadata = GTDAggregationMetadata(
        source_path="in-memory licensed GTD input",
        input_rows=len(events),
        turkey_rows=len(selected),
        skipped_unknown_month=skipped_unknown_month,
        first_month=monthly["date"].min().strftime("%Y-%m"),
        last_month=monthly["date"].max().strftime("%Y-%m"),
        strict_definition=strict_definition,
    )
    return monthly, metadata
