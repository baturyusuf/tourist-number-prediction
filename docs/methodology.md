# Methodology

## Research estimands are separated

1. **Forecasting performance** asks whether a model reduces out-of-sample loss.
2. **Predictive association** asks whether a feature block adds stable forecast information.
3. **Statistical association** concerns coefficients/tests under stated assumptions.
4. **Causal interpretation** requires an identification design and is not inferred from SHAP,
   correlations, Granger predictability, coefficients alone, or feature importance.

## Forecast protocols

- **Rolling one-step operational ex-ante:** predict month *t* at the end of *t−1*, then advance the
  origin. Target observations are restricted by the conservative release rule below; *t−1* is not
  assumed observable.
- **Fixed-origin 12-month operational ex-ante:** issue all 12 monthly forecasts at the end of the
  preceding year. Training may use only target observations available by that origin, and the
  forecast consumes neither realized within-year targets nor realized future exogenous values.
- **Observation-availability sensitivity:** assumes source observations are available once their
  reference month is present in the supplied retrospective file. This is useful for reproduction
  but is not labeled operational ex-ante.
- **Conditional/ex-post:** may consume realized future exogenous paths, but is stored and ranked
  separately and cannot be described as an ex-ante forecast.
- **Frozen 2026-Q1 external holdout:** fixes the origin at 2025-12-31, masks target history after
  2025-09 under the three-month rule, sums January-March forecasts, and scores them only against
  TÜİK's official quarter total. No 2026 outcome is used for model selection or tuning.

Folds are expanding-window and time ordered. Random splitting and shuffling are prohibited. Model
and feature selection use only inner time-series folds. The 2025 legacy period is reported after
the model design is fixed, not used as a tuning surface.

## Target release assumption

No historical issue-date archive accompanied the TÜİK monthly target snapshot. Confirmatory
operational backtests therefore impose a prespecified delay of **three completed calendar months**
after each target reference month. For a forecast of month *t* made at the end of *t−1*, the latest
eligible target is *t−4*. For example, at the 31 December 2024 origin for January 2025, September
2024 is the latest target conservatively treated as issued.

This is an explicit conservative assumption, not a claim about every historical TÜİK publication
date. Each fold records the forecast origin, assumed target-available-through month, and delay. A
zero-delay run must be labeled observation-availability sensitivity. The reproduced 2025
seasonal-naive result assumes the complete January-December 2024 vector at the 31 December 2024
origin and is therefore a **legacy observation-availability reproduction**, not the confirmatory
operational fixed-origin result.

## Missing targets and shocks

The April-June 2020 target values remain missing in the primary series and are excluded from loss.
Intervention/regime indicators describe the pandemic-era survey gap, travel disruption, and
recovery; they do not assert zero border traffic. A named linear interpolation is retained only for
reproduction and sensitivity analysis; it never silently overwrites the source. Models that
require complete training data must declare any model-internal fill in their result notes and be
compared against missing-aware alternatives.

## Metrics and uncertainty

Primary metrics are MASE, RMSSE, sMAPE, WAPE, MAE, and RMSE. MAPE and R² are secondary, especially
unreliable during very low-volume shock months.

- **Full-support metrics** use every row on which the target and evaluated model forecast are both
  present. These are the primary standalone operational-accuracy estimates.
- **Paired metrics** use only rows on which the target, evaluated model forecast, and seasonal-naive
  forecast are all present. Seasonal-naive MAE/RMSE and relative skill are computed on this exact
  same support: `1 - paired_model_loss / paired_seasonal_naive_loss`.
- **Pooled metrics** concatenate eligible predictions across folds and weight each forecast
  observation equally. They are the primary cross-fold summaries.
- **Macro-fold metrics** average fold-level scores and weight folds equally; they are labeled
  `macro_fold_*` because they can differ materially from pooled results when fold sizes differ.

The support distinction remains part of the metric contract. In the current validated run, the
seasonal-naive implementation recursively projects an unavailable lag-12 reference from earlier
observed seasons inside the model, without filling the raw April-June 2020 target. This preserves
129 full and paired forecast rows per model in both protocols. A future model or run can still have
different forecast support, so standalone `pooled_full_*` accuracy and model-specific
`pooled_paired_*` comparison statistics remain separately labeled.

Where intervals exist, empirical coverage, mean width, and Winkler score are reported. Interval
construction is model-specific: several simple baselines use a normal approximation based on
finite in-sample residual dispersion, while supported statistical models use their fitted-model
forecast intervals. These are uncalibrated retrospective diagnostics, not interchangeable
probabilistic forecasts. Shortlisted point-forecast comparisons use autocorrelation-aware
Diebold-Mariano tests and moving-block bootstrap intervals; small numerical differences are not
called meaningful without uncertainty evidence.

The 2026-Q1 holdout has one official quarter-total actual, not three independently archived monthly
actuals. It therefore reports quarter absolute error and APE only. Monthly MAE, RMSE, R², and a
quarter interval derived from unidentified monthly-error dependence are intentionally omitted.

## Feature availability

Every feature admitted to a confirmatory model must have a source-availability timestamp. The
leakage assertion fails if that timestamp is later than the forecast origin; candidates without an
auditable timestamp are excluded. Target lags and rolling features incorporate the three-month
publication delay before aggregation. Scaling, imputation, and tuning live inside training-only
pipelines. Fixed-origin B0 tree/linear models are recursive and consume their own prior forecasts.
Exogenous feature blocks are admitted only after publication lags and future-path generation are
documented. Contemporaneous realized REER, HICP, Trends, or security values are not ex-ante inputs.

## External data gate

Candidate data must pass schema, provenance, license, coverage, frequency, target-compatibility,
forecast-origin availability, and leakage checks before integration. GTD is restricted to its
licensed 2008-2020 tourism-overlap sample, with methodology-break controls, unless a documented
compatible bridge is validated; post-coverage months are never filled with zero. The unproven
`TREND` snapshot and Instagram workbook are excluded from confirmatory models. Rejected datasets
remain in the research record.

The final GTD association family contains nine prespecified definitions × lags 0, 1, 2, 3, 6, and
12, with HAC standard errors and Benjamini-Hochberg adjustment across all 54 tests. The 100-km
sensitivity uses manually curated WGS84 points for Istanbul, Antalya, Muğla, İzmir, and
Nevşehir/Cappadocia and haversine distance. Point locations are not authoritative administrative
boundaries and do not exhaust Türkiye's tourism geography. The complete-case high-severity
sensitivity requires `nkill + nwound >= 10`; partial casualties remain unknown. Predictive B4
comparisons use a retrospective final GTD snapshot and assumed reporting delay and are never called
operational or causal.

## Evidence boundary

The supplied monthly target ends in December 2025. TÜİK releases 58142 and 54155 provide
definition-consistent Q1 totals for 2026 and 2025; the latter exactly matches the supplied
January-March 2025 sum. Run `external_2026q1_20260811T171249Z_71f005f4` freezes those public
aggregates and evaluates a shortlist designed without 2026 outcomes. This is a valid quarterly
external holdout but not monthly validation, repeated-origin evidence, or a significance test.
The requested source-country panel remains unavailable because no accepted source supplies aligned
definitions and historical forecast-origin vintages.
