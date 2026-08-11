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

The support distinction is material: missing target observations in April-June 2020 also remove
April-June 2021 from a lag-12 seasonal-naive comparator, although another model may still produce
valid forecasts for those months. Restricting all standalone model metrics to seasonal-naive
support would discard those otherwise evaluable forecasts. A standalone full-support
seasonal-naive result and `pooled_paired_seasonal_naive_*` are therefore different estimands and
may have different observation counts, date ranges, and values; the latter can also vary by model
when model forecast support differs.

Where intervals exist, empirical coverage, mean width, and Winkler score are reported. Shortlisted
model comparisons use autocorrelation-aware Diebold-Mariano tests and moving-block bootstrap
intervals; small numerical differences are not called meaningful without uncertainty evidence.

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

## Evidence boundary

The supplied target ends in December 2025. No definition-consistent 2026 target vintage was
supplied or incorporated, so the repository does not claim an untouched 2026 validation, 2026
forecast accuracy, or statistical significance based on 2026 outcomes. Such validation remains
future work contingent on an official release and a frozen pre-outcome pipeline.
