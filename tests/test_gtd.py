import numpy as np
import pandas as pd

from tourism_forecasting.gtd import GTD_ANALYSIS_COLUMNS, aggregate_gtd_monthly, haversine_km
from tourism_forecasting.gtd_analysis import (
    aggregate_definition_sensitivities,
    association_sensitivity,
    gtd_definition_subsets,
    predictive_value_sensitivity,
)


def test_haversine_known_distance() -> None:
    assert np.isclose(float(haversine_km(0, 0, 0, 1)), 111.195, atol=0.1)


def test_gtd_monthly_aggregation_does_not_extend_post_coverage() -> None:
    events = pd.DataFrame(
        {
            "iyear": [2020, 2020, 2020, 2020],
            "imonth": [1, 1, 3, 0],
            "country_txt": ["Turkey"] * 4,
            "success": [1, 0, 1, 1],
            "doubtterr": [0, 0, 1, 0],
            "nkill": [1, 0, 2, 0],
            "nwound": [0, 4, 0, 0],
            "latitude": [41.0, 36.9, 39.0, 40.0],
            "longitude": [29.0, 30.7, 35.0, 30.0],
            "targtype1_txt": ["Tourists", "Business", "Transportation", "Unknown"],
        }
    )
    monthly, metadata = aggregate_gtd_monthly(events)
    assert monthly["date"].min() == pd.Timestamp("2020-01-01")
    assert monthly["date"].max() == pd.Timestamp("2020-03-01")
    assert list(monthly["incidents"]) == [2, 0, 1]
    assert metadata.skipped_unknown_month == 1


def test_gtd_partial_casualties_and_missing_success_remain_unknown() -> None:
    events = pd.DataFrame(
        {
            "iyear": [2020, 2020],
            "imonth": [1, 1],
            "country_txt": ["Turkey", "Turkey"],
            "nkill": [1, np.nan],
            "nwound": [np.nan, 4],
            "latitude": [41.0, np.nan],
            "longitude": [29.0, np.nan],
            "targtype1_txt": ["Hotel/Resort", "Business"],
            "targsubtype1_txt": ["Hotel/Resort", "Retail"],
        }
    )
    monthly, _ = aggregate_gtd_monthly(events)
    row = monthly.iloc[0]
    assert pd.isna(row["severity_known"])
    assert row["events_partial_unknown_severity"] == 2
    assert row["events_unknown_success"] == 2
    assert row["successful_incidents"] == 0
    assert row["tourism_transport_targets"] == 1
    assert row["hotel_resort_targets"] == 1
    assert row["events_missing_coordinates"] == 1


def test_gtd_reader_columns_exclude_event_level_content() -> None:
    assert "eventid" not in GTD_ANALYSIS_COLUMNS
    assert "summary" not in GTD_ANALYSIS_COLUMNS
    assert "gname" not in GTD_ANALYSIS_COLUMNS
    assert "scite1" not in GTD_ANALYSIS_COLUMNS


def test_gtd_definition_filters_preserve_unknowns() -> None:
    events = pd.DataFrame(
        {
            "doubtterr": [0, 1, np.nan],
            "success": [1, 0, np.nan],
            "crit1": [1, 1, 1],
            "crit2": [1, 1, 1],
            "crit3": [1, 0, 1],
            "latitude": [41.0, np.nan, 39.0],
            "longitude": [29.0, np.nan, np.nan],
        }
    )
    definitions = gtd_definition_subsets(events)
    assert len(definitions["broad_all_gtd"]) == 3
    assert len(definitions["doubtterr_zero"]) == 1
    assert len(definitions["strict_all_criteria_doubtterr_zero"]) == 1
    assert len(definitions["successful_only"]) == 1
    assert len(definitions["known_coordinates_only"]) == 1
    assert len(definitions["within_100km_tourism_centers"]) == 1


def test_gtd_aggregate_analysis_does_not_extend_after_2020() -> None:
    events = pd.DataFrame(
        {
            "iyear": [2008, 2020],
            "imonth": [1, 12],
            "country_txt": ["Turkey", "Turkey"],
            "crit1": [1, 1],
            "crit2": [1, 1],
            "crit3": [1, 1],
            "doubtterr": [0, 0],
            "success": [1, 1],
            "nkill": [1, np.nan],
            "nwound": [0, 1],
            "latitude": [41.0, np.nan],
            "longitude": [29.0, np.nan],
            "targtype1_txt": ["Tourists", "Business"],
            "targsubtype1_txt": ["Hotel/Resort", "Retail"],
        }
    )
    monthly, summary = aggregate_definition_sensitivities(events)
    broad = monthly["broad_all_gtd"]
    assert broad["date"].min() == pd.Timestamp("2008-01-01")
    assert broad["date"].max() == pd.Timestamp("2020-12-01")
    assert summary.loc[summary["definition"].eq("broad_all_gtd"), "incidents"].item() == 2


def test_gtd_association_includes_both_method_break_controls() -> None:
    dates = pd.date_range("2008-01-01", "2020-12-01", freq="MS")
    core = pd.DataFrame(
        {
            "date": dates,
            "target_original_with_missing": 1_000 + np.arange(len(dates)) * 5,
        }
    )
    monthly = pd.DataFrame({"date": dates, "incidents": np.arange(len(dates)) % 7})
    result = association_sensitivity(core, {"synthetic": monthly})
    assert len(result) == 1
    assert "2008-04" in result.loc[0, "controls"]
    assert "2012-01" in result.loc[0, "controls"]
    assert result.loc[0, "interpretation"] == "descriptive association only; not causal evidence"


def test_gtd_predictive_output_is_aggregate_common_sample() -> None:
    dates = pd.date_range("2008-01-01", "2020-12-01", freq="MS")
    target = 1_000 + np.arange(len(dates)) * 5 + 50 * np.sin(2 * np.pi * dates.month / 12)
    core = pd.DataFrame({"date": dates, "target_original_with_missing": target})
    monthly = pd.DataFrame({"date": dates, "incidents": np.arange(len(dates)) % 7})
    result = predictive_value_sensitivity(core, {"synthetic": monthly})
    assert result.loc[0, "protocol"] == "rolling_one_step_common_sample"
    assert result.loc[0, "evaluated_months"] == 72
    assert "date" not in result.columns
    assert "forecast" not in result.columns
