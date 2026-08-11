# Research decisions

## D001 - preserve source target missingness

The primary target remains missing for April-June 2020. Supervised loss and evaluation exclude
those observations. Linear interpolation exists only as `target_interpolated_legacy` for explicit
reproduction/sensitivity work. TÜİK did not produce the definition-consistent Q2 2020 survey
estimates; Ministry border counts are a different series and are not replacements.

## D002 - promote seasonal naive to mandatory benchmark

All compatible leaderboards report seasonal naive and relative skill. The 2025 benchmark is
reproduced but does not select models or lags. Monthly tourism is highly seasonal, and a weak
nonseasonal benchmark would exaggerate gains.

## D003 - separate forecast protocols

Rolling one-step, fixed-origin 12-month operational ex-ante, observation-availability sensitivity,
and conditional/ex-post forecasts are separate tasks. Realized targets within a 12-month forecast
year and realized future exogenous values are not allowed in the operational ex-ante task.

## D004 - retain verified semantics and unknown vintages

Official tables identify `USD` as `reer_cpi_developed_2025eq100` and `HICP` as
`ea_hicp_air_passenger_yoy_pct`. Their snapshot vintages remain unknown. `TREND` is retained as
`search_interest_legacy_unverified` but excluded from confirmatory blocks until its query,
geography, request window, normalization, and extraction vintage are recovered.

## D005 - quarantine external raw data

Instagram/GTD workbooks, GTD codebooks, and row-level derivatives remain outside Git. GTD is
restricted to licensed noncommercial overlap work. The local Instagram workbook is rejected: it
lacks Türkiye-specific travel tags, verified country semantics, reliable provenance, a defensible
unit of observation, and adequate history.

## D006 - conventional models precede deep learning

The 216-row national series is evaluated with statistical, regularized, tree, decomposition, and
hybrid candidates first. Deep learning is not a primary path without a materially larger panel.

## D007 - target issue dates use a conservative operational convention

No historical issue-date archive accompanied the retrospective target snapshot. Confirmatory
operational folds therefore impose a prespecified delay of three completed months: at the end of
`t-1`, the latest usable target is `t-4`. The exact cutoff is recorded per fold. The zero-delay
2025 seasonal-naive calculation is retained only as a legacy observation-availability
reproduction, not operational validation.

## D008 - full-support accuracy and pairwise skill are different estimands

Standalone accuracy uses every observed target/model forecast pair. Seasonal-naive skill uses the
exact rows shared by that model and the seasonal-naive comparator. Pooled observation-weighted and
macro-fold-weighted quantities are named separately. In the current implementation, an unavailable
lag-12 seasonal reference is recursively projected from earlier observed seasons inside the model;
the raw target remains missing and unchanged. The validated run therefore retains 129 paired rows
per model and protocol, while the general support distinction remains explicit for future runs.

## D009 - registry artifacts are immutable and preliminary rows remain visible

Every new run writes to `results/runs/<run_id>/`, records artifact hashes, the committed Git SHA,
configuration checksum, package versions, and source-tree state. The 28 pre-milestone rows are
preserved but explicitly marked `provenance_incomplete_pre_milestone`; their mutable aliases and
intake-commit SHA cannot substantiate current claims.

## D010 - 2026 validation is quarterly and frozen

TÜİK release 58142 supplies the definition-consistent 2026-Q1 departing-visitors total of
9,258,129; release 54155 reports 9,121,152 for 2025-Q1, exactly matching the supplied January-March
sum. Run `external_2026q1_20260811T171249Z_71f005f4` forecasts from 2025-12-31 using targets only
through 2025-09 and performs no 2026 outcome tuning. January-March predictions are summed and scored
only against the quarter total. Monthly MAE/RMSE/R² and aggregate intervals are withheld because
independently archived monthly actuals and defensible monthly-error dependence are unavailable.

## D011 - GTD evidence is aggregate, multiplicity-adjusted, and non-operational

Run `gtd_20260811T172334Z_6527a1fb` (source SHA `63a7b0a`) uses nine definitions and incident lags
0, 1, 2, 3, 6, and 12 with HAC inference and one Benjamini-Hochberg family of 54 tests. High-severity
lags 1, 2, and 6 have nominal p-values 0.013041, 0.049795, and 0.031822, respectively, but none is BH
significant (minimum adjusted p=0.615394). All nine B4 variants improve common-sample MAE by
5.10%-7.68% with block-bootstrap absolute-loss intervals below zero, while RMSE worsens by
1.63%-3.45%. This loss dependence, the
final retrospective snapshot, assumed reporting delay, and end-2020 coverage preclude an
operational or causal claim.

Spatial sensitivity uses manually curated WGS84 points for Istanbul, Antalya, Muğla, İzmir, and
Nevşehir/Cappadocia and haversine distance. These points are neither authoritative administrative
boundaries nor a complete representation of Türkiye's tourism geography. Raw GTD rows remain
restricted. Required citation: START (National Consortium for the Study of Terrorism and Responses
to Terrorism). (2022). *Global Terrorism Database, 1970–2020* [data file].
https://www.start.umd.edu/data-tools/GTD. Copyright University of Maryland 2022.

## D012 - snapshot macro blocks do not improve MAE

Run `ablation_20260811T165312Z_69334f2b` evaluates B1, B2, and B5 using lagged REER/HICP values from
a retrospective snapshot whose historical extraction vintage is unknown. Relative to ridge B0,
their paired MAE changes are −0.39%, −0.77%, and −1.15% skill, respectively, and all
block-bootstrap intervals include zero.
They remain labeled snapshot-vintage sensitivities rather than confirmatory feature gains.
