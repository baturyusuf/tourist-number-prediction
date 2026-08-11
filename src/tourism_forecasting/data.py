"""Core-data ingestion and audit utilities.

The loader is deliberately conservative: source columns are retained, semantic aliases are
marked as candidates until provenance is verified, and missing pandemic targets are not filled
in the primary analysis series.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from tourism_forecasting.paths import repository_root, resolve_from_root

DATE_PATTERN = re.compile(r"^\d{4}-(?:[1-9]|1[0-2])$")
SOURCE_TO_INTERNAL = {
    "Yil-Ay": "date",
    "Ziyaretci": "departing_visitors_total_original_with_missing",
    "USD": "reer_cpi_developed_2025eq100",
    "HICP": "ea_hicp_air_passenger_yoy_pct",
    "TREND": "search_interest_legacy_unverified",
}


@dataclass(frozen=True)
class CoreDataAudit:
    path: str
    sha256: str
    byte_count: int
    encoding: str
    delimiter: str
    row_count: int
    column_count: int
    start: str
    end: str
    expected_months: int
    missing_months: int
    duplicate_dates: int
    missing_target: int
    missing_target_dates: str
    non_numeric_values: int
    non_positive_targets: int
    unexpected_columns: str

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([{"check": key, "value": value} for key, value in asdict(self).items()])


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _logical_source_path(path: Path) -> str:
    """Return a portable provenance label without exposing a workstation path."""

    try:
        return path.resolve().relative_to(repository_root().resolve()).as_posix()
    except ValueError:
        return path.name


def _decode_csv(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8 with BOM"
    try:
        return raw.decode("ascii"), "ASCII (UTF-8 compatible; no BOM)"
    except UnicodeDecodeError:
        pass
    for encoding in ("utf-8", "cp1254"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1"), "latin-1"


def _detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def _strict_month_parse(values: pd.Series) -> pd.Series:
    raw = values.astype("string").str.strip()
    malformed = ~raw.fillna("").map(lambda value: bool(DATE_PATTERN.fullmatch(value)))
    if malformed.any():
        examples = raw[malformed].head(5).tolist()
        raise ValueError(f"Malformed monthly date values: {examples}")
    return pd.to_datetime(raw, format="%Y-%m", errors="raise")


def _numeric(series: pd.Series) -> tuple[pd.Series, int]:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce"), 0
    cleaned = series.astype("string").str.strip().str.replace(" ", "", regex=False)
    # A lone comma is treated as a decimal mark only when no dot is present.
    comma_decimal = cleaned.str.contains(",", na=False, regex=False) & ~cleaned.str.contains(
        ".", na=False, regex=False
    )
    cleaned.loc[comma_decimal] = cleaned.loc[comma_decimal].str.replace(",", ".", regex=False)
    parsed = pd.to_numeric(cleaned, errors="coerce")
    non_numeric = int((series.notna() & parsed.isna()).sum())
    return parsed, non_numeric


def load_core_data(
    path: str | Path = "data/raw/turizm_kisi_Reel_HICP_Trend.csv",
    *,
    official_replacements: Mapping[str | pd.Timestamp, float] | None = None,
) -> tuple[pd.DataFrame, CoreDataAudit]:
    """Load, normalize, and audit the supplied monthly CSV without overwriting it.

    ``official_replacements`` is intentionally explicit. It may be supplied only after a
    definition-consistent official series has been documented; absent that evidence, the
    three shutdown months remain missing.
    """

    source_path = resolve_from_root(path)
    raw = source_path.read_bytes()
    text, encoding = _decode_csv(raw)
    delimiter = _detect_delimiter(text)
    source = pd.read_csv(io.StringIO(text), sep=delimiter)
    source.columns = [str(column).strip() for column in source.columns]

    missing_required = sorted(set(SOURCE_TO_INTERNAL) - set(source.columns))
    if missing_required:
        raise ValueError(f"Core CSV is missing required columns: {missing_required}")

    df = source.rename(columns=SOURCE_TO_INTERNAL).copy()
    df["date"] = _strict_month_parse(df["date"])
    numeric_columns = [
        "departing_visitors_total_original_with_missing",
        "reer_cpi_developed_2025eq100",
        "ea_hicp_air_passenger_yoy_pct",
        "search_interest_legacy_unverified",
    ]
    non_numeric_values = 0
    for column in numeric_columns:
        df[column], invalid = _numeric(df[column])
        non_numeric_values += invalid

    df = df.sort_values("date", kind="stable").reset_index(drop=True)
    # Stable generic aliases keep modeling code configurable while the verified semantic fields
    # remain explicit in exported metadata and the data dictionary.
    df["target_original_with_missing"] = df["departing_visitors_total_original_with_missing"]
    df["reer_candidate"] = df["reer_cpi_developed_2025eq100"]
    df["hicp_candidate"] = df["ea_hicp_air_passenger_yoy_pct"]
    df["search_interest_candidate"] = df["search_interest_legacy_unverified"]
    expected = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
    observed = pd.DatetimeIndex(df["date"])
    missing_dates = expected.difference(observed)

    df["target_official"] = df["target_original_with_missing"]
    if official_replacements:
        normalized_replacements = {
            pd.Timestamp(date).to_period("M").to_timestamp(): float(value)
            for date, value in official_replacements.items()
        }
        for date, value in normalized_replacements.items():
            mask = df["date"].eq(date)
            if not mask.any():
                raise ValueError(
                    f"Official replacement date is not in the core series: {date:%Y-%m}"
                )
            df.loc[mask, "target_official"] = value

    # Kept solely to reconstruct the manuscript's legacy treatment. Never the default target.
    df["target_interpolated_legacy"] = df["target_original_with_missing"].interpolate(
        method="linear", limit_area="inside"
    )
    df["is_target_observed"] = df["target_original_with_missing"].notna()
    df["pandemic_shutdown"] = df["date"].between("2020-04-01", "2020-06-01")
    df["pandemic_period"] = df["date"].between("2020-03-01", "2022-03-01")
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["trend_index"] = np.arange(len(df), dtype=int)

    missing_target_dates = df.loc[df["target_original_with_missing"].isna(), "date"].dt.strftime(
        "%Y-%m"
    )
    unexpected = sorted(set(source.columns) - set(SOURCE_TO_INTERNAL))
    audit = CoreDataAudit(
        path=_logical_source_path(source_path),
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
        encoding=encoding,
        delimiter=repr(delimiter),
        row_count=len(df),
        column_count=len(source.columns),
        start=df["date"].min().strftime("%Y-%m"),
        end=df["date"].max().strftime("%Y-%m"),
        expected_months=len(expected),
        missing_months=len(missing_dates),
        duplicate_dates=int(df["date"].duplicated(keep=False).sum()),
        missing_target=int(df["target_original_with_missing"].isna().sum()),
        missing_target_dates=", ".join(missing_target_dates),
        non_numeric_values=non_numeric_values,
        non_positive_targets=int((df["target_original_with_missing"].dropna() <= 0).sum()),
        unexpected_columns=", ".join(unexpected),
    )
    return df, audit


def assert_monthly_continuity(df: pd.DataFrame, date_column: str = "date") -> None:
    dates = pd.DatetimeIndex(df[date_column]).sort_values()
    if dates.has_duplicates:
        raise ValueError("Duplicate monthly dates detected")
    expected = pd.date_range(dates.min(), dates.max(), freq="MS")
    if not dates.equals(expected):
        missing = expected.difference(dates).strftime("%Y-%m").tolist()
        raise ValueError(f"Monthly continuity failure; missing={missing}")
