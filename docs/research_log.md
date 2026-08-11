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
  fold means are labeled separately. Missing April-June 2020 targets consequently remove
  April-June 2021 only from lag-12 paired comparisons, not from another model's full support.

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
- Confirmed the evidence cutoff: the supplied target ends at 2025-12. No 2026 target validation,
  error metric, significance claim, or external-validation result was calculated or inferred.

Open items are maintained in `PROGRESS.md`; methodological choices and rejected alternatives are
maintained in `DECISIONS.md`.
