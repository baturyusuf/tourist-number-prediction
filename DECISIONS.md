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
macro-fold-weighted quantities are named separately. Lag-12 support disappears for April-June 2021
after the Q2 2020 target gap, but other models can still forecast those months.

## D009 - registry artifacts are immutable and preliminary rows remain visible

Every new run writes to `results/runs/<run_id>/`, records artifact hashes, the committed Git SHA,
configuration checksum, package versions, and source-tree state. The 28 pre-milestone rows are
preserved but explicitly marked `provenance_incomplete_pre_milestone`; their mutable aliases and
intake-commit SHA cannot substantiate current claims.

## D010 - no 2026 validation is inferred

The target ends at 2025-12. Later-dated external covariates do not create realized tourism
outcomes. Any 2026 forecast remains prospective and unscored until a definition-consistent
official target vintage is released and frozen.
