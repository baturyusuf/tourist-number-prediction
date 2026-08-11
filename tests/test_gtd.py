import numpy as np
import pandas as pd

from tourism_forecasting.gtd import aggregate_gtd_monthly, haversine_km


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
        }
    )
    monthly, _ = aggregate_gtd_monthly(events)
    row = monthly.iloc[0]
    assert pd.isna(row["severity_known"])
    assert row["events_partial_unknown_severity"] == 2
    assert row["events_unknown_success"] == 2
    assert row["successful_incidents"] == 0
    assert row["tourism_transport_targets"] == 1
    assert row["events_missing_coordinates"] == 1
