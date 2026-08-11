from pathlib import Path

import pandas as pd
import pytest

from tourism_forecasting.data import assert_monthly_continuity, load_core_data


def test_strict_date_parsing_and_target_variants(tmp_path: Path) -> None:
    source = tmp_path / "core.csv"
    source.write_text(
        "Yil-Ay,Ziyaretci,USD,HICP,TREND\n"
        "2020-3,100,120,1.0,50\n"
        "2020-4,,121,1.1,40\n"
        "2020-5,,122,1.2,30\n"
        "2020-6,,123,1.3,20\n"
        "2020-7,60,124,1.4,25\n",
        encoding="utf-8",
    )
    frame, audit = load_core_data(source)
    assert audit.path == "core.csv"
    assert not Path(audit.path).is_absolute()
    assert audit.missing_target == 3
    assert audit.missing_months == 0
    assert frame["target_original_with_missing"].isna().sum() == 3
    assert frame["target_official"].isna().sum() == 3
    assert frame["target_interpolated_legacy"].notna().all()
    assert frame.loc[1:3, "pandemic_shutdown"].all()


def test_malformed_month_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("Yil-Ay,Ziyaretci,USD,HICP,TREND\n2020-13,1,1,1,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed monthly date"):
        load_core_data(source)


def test_monthly_continuity_detects_gap() -> None:
    frame = pd.DataFrame({"date": pd.to_datetime(["2020-01-01", "2020-03-01"])})
    with pytest.raises(ValueError, match="missing=.*2020-02"):
        assert_monthly_continuity(frame)


def test_supplied_core_integration_if_present() -> None:
    path = Path("data/raw/turizm_kisi_Reel_HICP_Trend.csv")
    if not path.exists():
        pytest.skip("private core CSV not available")
    frame, audit = load_core_data(path)
    assert (audit.row_count, audit.column_count) == (216, 5)
    assert (audit.start, audit.end) == ("2008-01", "2025-12")
    assert audit.sha256 == "a7885fb0e1ed5de7d64ae180733effc0baebad1e4842ef6bca467466b5b538e5"
    assert audit.path == "data/raw/turizm_kisi_Reel_HICP_Trend.csv"
    assert audit.missing_target_dates == "2020-04, 2020-05, 2020-06"
    assert_monthly_continuity(frame)
