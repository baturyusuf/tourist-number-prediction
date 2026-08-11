# Data dictionary

This dictionary distinguishes source labels from verified semantics. Candidate aliases are used in
code to prevent a convenient filename or column name from becoming an unsupported data claim.

## Core monthly CSV

| Source field | Internal field | Type/unit | Current interpretation | Status |
|---|---|---|---|---|
| `Yil-Ay` | `date` | Month start, `YYYY-M` | Monthly reference period | Verified from values |
| `Ziyaretci` | `departing_visitors_total_original_with_missing` (`target_original_with_missing` modeling alias) | People/count | TÜİK monthly total departing visitors: foreign visitors plus Turkish citizens resident abroad; overnight and same-day visitors | Definition verified; extraction/revision vintage unknown |
| — | `target_official` | People/count | Same observed target snapshot plus only explicit definition-consistent official replacements | Q2 2020 remains missing; no definition-consistent monthly replacement was identified as of 2026-08-11 |
| — | `target_interpolated_legacy` | People/count | Linear interpolation retained only to reconstruct/sensitize the legacy study | Never the default target |
| `USD` | `reer_cpi_developed_2025eq100` | Index, 2025=100 | TCMB CPI-based REER developed-country subindex; monthly, non-seasonally adjusted; a rise means real lira appreciation/relative Turkish-price increase | Identity verified; exact EVDS item/extraction vintage pending |
| `HICP` | `ea_hicp_air_passenger_yoy_pct` | Annual percentage change | Eurostat euro-area HICP, passenger transport by air (`prc_hicp_manr`, `RCH_A`, `CP0733`, `EA`) | Identity verified; archived-to-current COICOP transition documented |
| `TREND` | `search_interest_legacy_unverified` | Relative index | Undocumented legacy search-interest composite | Rejected from confirmatory models unless query/geography/window/vintage are recovered |
| — | `is_target_observed` | Boolean | True only when the source target is present | Derived |
| — | `pandemic_shutdown` | Boolean | April-June 2020 survey-gap/intervention interval; it does not assert zero border traffic | Derived, prespecified |
| — | `pandemic_period` | Boolean | March 2020-March 2022 descriptive regime | Derived, prespecified |

The file has 216 continuous monthly rows from 2008-01 through 2025-12. The target is missing at
2020-04, 2020-05, and 2020-06 because TÜİK did not produce the survey estimate for 2020 Q2. Ministry
border-arrival counts are definition-inconsistent and are not substituted. No other source column
is missing.

## Forecast fields

| Field | Definition |
|---|---|
| `forecast_origin` | Issue date immediately before the test period; all inputs must have availability timestamps on or before it |
| `target_publication_delay_months` | Confirmatory operational assumption of three completed calendar months; zero is allowed only for a separately labeled observation-availability sensitivity |
| `target_available_through` | Latest target reference month admitted at the origin; for forecast month *t* under the three-month rule, this is *t−4* |
| `protocol` | Operational rolling one-step, operational fixed-origin 12-month, separately labeled observation-availability sensitivity, or conditional/ex-post task |
| `horizon` | Number of months from fixed origin; one for rolling one-step |
| `feature_block` | Prespecified B0-B7 feature group |
| `full_evaluable` | Target and evaluated model forecast are both present for the row |
| `comparable_to_seasonal_naive` | `full_evaluable` plus a present seasonal-naive forecast for the same row |
| `pooled_full_*` | Metric computed after concatenating all full-support forecast rows across folds; each observation receives equal weight |
| `pooled_paired_*` | Model metric on the pooled subset shared with seasonal naive |
| `pooled_paired_seasonal_naive_*` | Seasonal-naive metric on exactly the same pooled paired subset as the evaluated model |
| `pooled_full_n` | Number of full-support forecast rows in the pooled metric |
| `pooled_paired_n` | Number of exact model/baseline comparison rows in the pooled paired metric |
| `pooled_paired_mae_skill_vs_seasonal_naive` | `1 - pooled_paired_model_MAE / pooled_paired_seasonal_naive_MAE`; positive is better |
| `pooled_paired_rmse_skill_vs_seasonal_naive` | Equivalent paired-support calculation using RMSE |
| `macro_fold_*` | Unweighted mean of the named fold-level metric; folds, rather than forecast rows, receive equal weight |
| `bias` | Mean forecast minus actual; positive means over-forecasting |

The support labels prevent silent loss of valid model forecasts. The validated seasonal-naive
model recursively projects any unavailable seasonal reference from earlier observed seasons; it
does not fill or overwrite the raw target. Consequently, the current run has 129 full and paired
rows per model and protocol, while both support fields remain mandatory.

The standalone 2025 reproduction uses protocol label
`legacy_2025_observation_availability_fixed_origin`. It assumes the complete 2024 target vector is
available at the 31 December 2024 origin and must not be interpreted as the three-month-delay
confirmatory operational protocol.

## Aggregate external-validation fields

| Field | Definition |
|---|---|
| `forecast_period` | `2026-Q1`; January-March predictions are aggregated before scoring |
| `actual_granularity` | `official_quarter_total_only`; no monthly 2026 actual vector is inferred |
| `quarter_forecast` | Sum of the three monthly point forecasts |
| `official_quarter_actual` | TÜİK release 58142 total: 9,258,129 departing visitors |
| `quarter_error_forecast_minus_actual` | Signed quarter forecast minus official total |
| `quarter_absolute_error` | Absolute quarter-total error |
| `quarter_absolute_percentage_error` | `100 × quarter_absolute_error / official_quarter_actual` |
| `interval_status` | Omitted because defensible monthly-error dependence for aggregation is unavailable |

The monthly dictionary still contains no realized target after 2025-12. The only scored 2026
outcome is the frozen official Q1 aggregate, so monthly MAE/RMSE/R² remain unavailable.
