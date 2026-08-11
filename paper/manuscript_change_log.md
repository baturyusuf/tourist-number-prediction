# Manuscript change log

This log records substantive changes between the supplied private manuscript and the revised
repository manuscript. The source `.docx` was audited but not modified or redistributed. Page
references below refer to the 17-page rendered source audit documented in
`docs/manuscript_audit.md`.

| Area | Source-manuscript issue | Revision | Evidence status |
|---|---|---|---|
| Title and scope | No title appeared on page 1; the contribution implied complex-model superiority | Added a title centered on release-aware evaluation and the finding that complexity does not beat seasonality in the primary task | Supported by immutable run `run_20260811T162732Z_6bbfe89e` |
| Target | Target was ambiguously described as international tourist arrivals and conflicted on start year | Defined the target as TÜİK total departing visitors: foreign visitors plus Turkish citizens resident abroad, overnight and same-day; fixed coverage at 2008-01–2025-12 | Verified against the supplied values and official target definition |
| Q2 2020 | Missing target months were not transparently handled | Retained April–June 2020 as missing, excluded them from loss, and prohibited replacement by definition-different Ministry border counts | Verified; no definition-consistent TÜİK Q2 estimate identified |
| Forecast protocol | “90/10” language conflicted with the 2025 split; one-step, annual, and conditional tasks were not separated | Defined rolling one-step, fixed-origin 12-month, observation-availability reproduction, and conditional/ex-post protocols separately | Implemented in code and fold metadata |
| Release timing | The source assumed retrospective target values were usable without issue-date evidence | Added a conservative three-completed-month target-release convention; each fold records origin and cutoff | Explicit assumption; historical issue-date archive unavailable |
| Leakage | Future exogenous availability and within-year target use were unresolved | Confirmatory leaderboard uses no realized future exogenous path; fixed-origin machine-learning models forecast recursively without teacher forcing | Tested and recorded in run artifacts |
| Baselines | Seasonal naive was not treated as the mandatory benchmark | Promoted seasonal naive to the reference for every compatible comparison; added multiple simple and statistical baselines | Complete |
| Model specification | SARIMAX/XGBoost equations, features, tuning, and preprocessing were incomplete or inconsistent | Replaced unreconstructable claims with fully specified baseline/statistical/B0 model families, frozen grids, fold-local preprocessing, and nested recursive tuning where used | Complete for new study; original scores remain unverified |
| Legacy 2025 metrics | Favorable 2025 seasonal-naive result risked being interpreted as operational validation | Reproduced the exact metrics but labeled the calculation observation-availability because complete 2024 issue-date availability at 31 December 2024 is unverified | Reproduced; not confirmatory |
| Accuracy claims | The source described complex models as superior without a strong, leakage-aware rolling evaluation | Reported seasonal naive as lowest-MAE fixed-origin model; described one-step ridge only as a non-robust numerical pooled gain | Supported by registered forecasts and comparison tables |
| Uncertainty | No autocorrelation-aware paired forecast comparison accompanied small error differences | Added paired-support Diebold–Mariano tests with Newey–West variance and 12-month moving-block bootstrap intervals | Complete, 2,000 bootstrap repetitions |
| Regimes | Pandemic and asymmetry language lacked an explicit test | Added descriptive pre-pandemic, pandemic-shock, recovery, and normalization error summaries; removed asymmetry claims | Descriptive only; not a causal or formal regime-switching model |
| SHAP | Ordinary SHAP plots were interpreted as significance, causal direction, lead time, and “perfect” evidence | Removed SHAP-based significance and causal claims; no SHAP result is reported in the revised manuscript | Unsupported original inference removed |
| REER | `USD` was treated as a nominal exchange-rate measure | Corrected it to the TCMB CPI-based real effective exchange-rate developed-country subindex, 2025 = 100, with direction stated | Definition verified; local vintage unknown |
| HICP | HICP was described inconsistently as an index, rate, or general inflation measure | Corrected it to euro-area annual HICP inflation for passenger transport by air | Definition verified; local vintage unknown |
| Macro/travel-cost ablation | Economic feature value was asserted without a reproducible block comparison | Added clean snapshot-vintage B1/B2/B5 comparisons against ridge B0; every added block worsened MAE and every absolute- and squared-loss interval crossed zero | Completed in `ablation_20260811T165312Z_69334f2b`; sensitivity only because historical extraction vintages are unknown |
| Search data | An undocumented `TREND` column supported strong leading-indicator claims | Rejected the series from confirmatory models because query design, geography, normalization, timestamp, and vintage are absent | Excluded |
| Instagram | A large workbook was proposed as external validation | Rejected it because of triplicated sheets, one-year coverage, undefined observation unit, lack of Türkiye-specific travel intent, and provenance mismatch | Excluded |
| Security | Terrorism data risked being extended beyond its coverage, spatially overgeneralized, or interpreted causally | Completed licensed aggregate-only 2008–2020 sensitivity with nine definitions, six prespecified lags, family-wide Benjamini–Hochberg adjustment, no post-2020 zeros, and no event-level outputs | Run `gtd_20260811T172334Z_6527a1fb`: B4 MAE skill 5.10%–7.68% with all nine absolute-loss intervals below zero, but RMSE worsened 1.63%–3.45%; three raw high-severity lag tests had *p* < 0.05 and none survived BH adjustment |
| Security definitions | Casualty completeness and the meaning of “near tourism centers” were underspecified | Defined high severity as `nkill + nwound >= 10` only when both are observed; named five manually prespecified WGS84 city centers and haversine 100-km sensitivity | Partial casualty values remain unknown; city points are not administrative boundaries or comprehensive national geography |
| Causality | Predictive outputs were used to assert causal effects and policy mechanisms | Separated forecasting, predictive association, statistical association, and causal identification; all causal claims removed | Complete |
| 2026 | Later-dated context risked implying monthly 2026 validation without an official outcome | Added locked external run `external_2026q1_20260811T171249Z_71f005f4` using the official same-definition Q1 total; seasonal naive was best of five with absolute error 136,977 and APE 1.479532% | Quarterly aggregate only; no 2026 tuning, monthly accuracy, interval, or significance claim |
| Figures and tables | Duplicate/mislabeled SHAP figures and conflicting captions undermined the results | Replaced the evidentiary layer with reproducible forecast, ablation, and aggregate GTD figures plus machine-readable tables | Generated from immutable or clean-run records; no restricted event rows exported |
| Reproducibility | Predictions, folds, configurations, source hashes, and environment were missing | Added immutable run directories, registry rows, artifact hashes, exact fold-level forecasts, frozen configuration and dependency lock, and automated tests | Confirmatory, ablation, final GTD, and quarterly 2026 runs recorded |
| Limitations | The source lacked a dedicated limitations section | Added limitations covering sample size, survey gap, release assumption, vintages, missing source-country panel, multiplicity, and quarterly-only 2026 evidence | Complete |
| Data/code statement | No data/code availability, funding, conflict, or contribution statement was present | Added a data/code statement and an author-completion note for contributions, funding, and competing interests | Author metadata and declarations still require confirmation |
| References | Several in-text/reference years, source descriptions, and factual claims did not match | Removed unsupported GDP-share and mismatched literature claims; added the required START 2022 GTD dataset citation and `Copyright University of Maryland 2022.` notice | A journal-formatted literature review may be added only after source-by-source verification |

## Claims explicitly withdrawn

The revised manuscript does not repeat the following source-manuscript claims:

- that Google Trends is a “perfect” or empirically proven leading indicator;
- that ordinary SHAP demonstrates statistical significance, causal direction, or a fixed planning
  delay;
- that SARIMAX and XGBoost provide complete methodological confirmation;
- that asymmetric effects have been demonstrated;
- that the reported complex models beat a release-aware seasonal-naive benchmark;
- that a tourism contribution of 4.66% of GDP is established by the cited TÜİK releases;
- that one 2026 quarterly total establishes monthly or general model validation.

## Remaining author actions before submission

1. Select a target journal and apply its reference, word-count, heading, and disclosure format.
2. Supply verified author names, affiliations, contributions, funding, acknowledgments, and
   competing-interest declarations.
3. Decide whether the private raw composite can be deposited under an appropriate data-use basis
   or whether only code, hashes, and generated aggregates may be shared.
4. Retain the GTD result as aggregate retrospective sensitivity unless prospective operational
   vintages or an auditable replacement source are obtained; do not publish event-level rows.
5. Preserve the no-tuning holdout rule when adding later official 2026 quarters or monthly outcomes;
   do not reconstruct monthly accuracy from a quarter total.
