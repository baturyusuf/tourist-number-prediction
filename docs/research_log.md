# Research log

## 2026-08-11 — repository intake and protocol freeze

- Confirmed the existing remote and preserved the initial commit/history.
- Created `codex/tourism-forecasting` from `main` as required.
- Located all four supplied inputs and recorded SHA-256 checksums.
- Protected raw, private, credential, GTD, and large intermediate paths before staging anything.
- Verified the core CSV has 216 continuous monthly rows (2008-01–2025-12), five columns, and only
  three missing target cells (2020-04 through 2020-06).
- Exactly reproduced the preliminary 2025 seasonal-naive metrics on full support (`n=12`). This
  calculation assumes the complete 2024 target vector at the 31 December 2024 origin and is frozen
  as a **legacy observation-availability reproduction**, not release-aware operational validation
  or a model-selection result.
- Predefined expanding rolling one-step and annual fixed-origin protocols, strong baseline set,
  primary metrics, and seasonal-naive skill before tuning models.
- Because no historical target issue-date archive was supplied, froze a conservative
  three-completed-month target-release assumption for confirmatory operational backtests. At the
  end-of-*t−1* origin for month *t*, target history ends at *t−4*; zero delay is a separately
  labeled observation-availability sensitivity.
- Froze metric support semantics: pooled full-support metrics score every evaluable model forecast;
  pooled paired metrics and seasonal-naive skill use the exact matched model/baseline rows. Macro
  fold means are labeled separately. The release-aware seasonal-naive model recursively projects
  an unavailable reference from earlier observed seasons without changing the raw Q2 2020 gaps;
  the current validated run therefore retains 129 paired rows per model and protocol.

## 2026-08-11 — official-source provenance and external-data gate

- Verified the target as TÜİK total departing visitors and confirmed that the official 2020
  release excludes Q2 survey estimates: https://veriportali.tuik.gov.tr/en/press/37438. Ministry
  Q2 border-arrival counts are definition-different and were not substituted.
- Identified `USD` as TCMB's developed-country CPI-based REER, 2025=100, and `HICP` as Eurostat
  euro-area passenger-air-transport annual HICP inflation. Definitions are verified, while the
  supplied composite's exact extraction vintages and the exact native EVDS item remain unknown.
- Rejected the supplied `TREND` from confirmatory models because its query, geography, request
  window, normalization, extraction timestamp, and vintage are absent. Google Trends' official
  normalization documentation is https://support.google.com/trends/answer/4365533?hl=en-GB.
- Rejected the local Instagram workbook. It does not match the supplied Kaggle page, has no
  reliable chain of provenance or country semantics, and cannot inherit the uploader-declared
  license. Meta's no-unauthorized-automation terms were recorded; no scraping was performed.
- Conditionally restricted GTD to licensed, noncommercial 2008-2020 tourism-overlap analysis. Raw
  data/codebook are not redistributed, 2021-2025 are not zero-filled, and the official 1998-01,
  2008-04, and 2012-01 collection breaks must be modeled or restricted. Official terms:
  https://www.start.umd.edu/gtd-terms.
- Recorded GTTAC GRID, ACLED, and UCDP as non-interchangeable post-2020 security alternatives and
  Google Ads/Wikimedia/GDELT as differently scoped digital-attention alternatives. None is silently
  spliced into an existing variable.
- Confirmed the initial evidence cutoff: the supplied monthly target ends at 2025-12. This was
  later extended only by the frozen official 2026-Q1 aggregate described below; no monthly 2026
  actual vector was inferred.

## 2026-08-11 — final model, ablation, and GTD evidence

- Registered the clean primary run and retained seasonal naive as the fixed-origin MAE benchmark.
  Rolling one-step ridge B0 has 7.86% pooled MAE skill, but paired uncertainty includes zero and the
  gain reverses during normalization; it is not a stable overall winner.
- Completed snapshot-vintage B1/B2/B5 ablations. Each slightly worsens MAE versus B0 and each
  block-bootstrap interval spans zero; no incremental REER/HICP value is claimed.
- Registered GTD run `gtd_20260811T172334Z_6527a1fb` at source SHA `63a7b0a`. It covers nine
  definitions and lags 0, 1, 2, 3, 6, and 12. Three high-severity lag coefficients have nominal
  p<0.05, but none survives family-wide BH adjustment (minimum adjusted p=0.615394).
- All nine GTD B4 variants improve MAE by 5.10%-7.68% with block-bootstrap absolute-loss intervals
  below zero, while RMSE worsens by 1.63%-3.45%. Results remain retrospective snapshot
  sensitivities rather than operational forecasts.
- Spatial distances use haversine calculations from manually curated WGS84 points for Istanbul,
  Antalya, Muğla, İzmir, and Nevşehir/Cappadocia. The points are neither authoritative boundaries
  nor complete tourism geography.
- Required GTD citation: START (National Consortium for the Study of Terrorism and Responses to
  Terrorism). (2022). *Global Terrorism Database, 1970–2020* [data file].
  https://www.start.umd.edu/data-tools/GTD. Copyright University of Maryland 2022.

## 2026-08-11 — frozen official 2026-Q1 holdout

- Froze TÜİK releases 58142 (2026-Q1 actual 9,258,129) and 54155 (2025-Q1 total 9,121,152, exactly
  matching the supplied January-March sum) with release/access metadata and evidence checksums.
- Registered `external_2026q1_20260811T171249Z_71f005f4`: origin 2025-12-31, target available
  through 2025-09, and no tuning on 2026 outcomes.
- Seasonal naive forecasts 9,121,152, for signed error −136,977, absolute error 136,977, and APE
  1.4795%; it has the lowest quarter absolute error among the frozen shortlist.
- Scoring is quarter-only. Monthly MAE/RMSE/R² and a quarter interval are withheld because monthly
  actuals and a defensible error-dependence model were not independently archived.
- The local Instagram workbook and undocumented `TREND` remain rejected. The requested
  source-country panel remains unavailable because no accepted aligned origin-vintage source was
  obtained.

Open items are maintained in `PROGRESS.md`; methodological choices and rejected alternatives are
maintained in `DECISIONS.md`.
