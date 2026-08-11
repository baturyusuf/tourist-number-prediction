# Türkiye Monthly Tourism-Demand Forecasting

This repository is a leakage-aware, reproducible re-evaluation of monthly international
tourism-demand forecasting for Türkiye. It separates ex-ante forecasts, conditional/ex-post
forecasts, predictive association, statistical association, and causal interpretation.

The supplied study has 216 monthly rows from January 2008 through December 2025 and three
missing target observations because TÜİK did not produce the corresponding Q2 2020 survey
estimates (April-June 2020). Raw inputs, the original manuscript, Kaggle workbooks, credentials,
and licensed GTD files are intentionally excluded from Git.

## Current scientific status

- The legacy 2025 seasonal-naive calculation is reproducible from the supplied CSV: RMSE
  184,753.22, MAE 156,550.42, MAPE 3.2796%, and R² 0.991406. It assumes the complete 2024
  target vector was available at the 31 December 2024 origin and scores all 12 months on full
  support (`n=12`), so it is an **observation-availability reproduction**, not a confirmatory
  operational backtest or a model-selection result.
- Confirmatory operational backtests use a conservative three-completed-month target-release
  assumption because no historical issue-date archive was supplied. At the end-of-month origin
  immediately before forecast month *t*, the latest usable target is therefore *t−4*. Zero-delay
  target history is allowed only in a separately labeled sensitivity analysis.
- Missing 2020 targets remain missing in the primary target. A separately named legacy
  interpolation is available only for sensitivity/reproduction work.
- Realized future exogenous variables are never used in the ex-ante leaderboard.
- The undocumented `TREND` series and local Instagram workbook are rejected from confirmatory
  feature blocks. GTD is restricted to licensed, noncommercial tourism-overlap analysis through
  2020 and is never extended with fabricated zeroes.
- In the primary fixed-origin 12-month protocol, seasonal naive has the lowest pooled MAE
  (957,226). In rolling one-step evaluation, ridge B0 lowers pooled MAE by 7.86% versus seasonal
  naive, but the paired uncertainty interval includes zero and the gain reverses in the 2023-2025
  normalization regime; it is not a robust overall winner.
- Snapshot-vintage ablations B1 (REER), B2 (HICP), and B5 (joint) all slightly worsen MAE versus B0
  (0.39%-1.15%), with bootstrap intervals spanning zero. They do not establish incremental
  exogenous value.
- A frozen, definition-consistent TÜİK quarterly holdout is now available for 2026-Q1. At the
  2025-12-31 origin with targets available through 2025-09, seasonal naive forecasts 9,121,152
  against the official 9,258,129 total: absolute error 136,977 and APE 1.4795%. This is one
  quarterly observation, not monthly validation or evidence of general superiority.
- The final GTD run (`gtd_20260811T172334Z_6527a1fb`, source `63a7b0a`) evaluates nine definitions,
  six lags, and a family-wide Benjamini-Hochberg correction. Three high-severity lag coefficients
  are nominally below 0.05, but none survives correction (minimum adjusted p-value 0.615394). GTD
  B4 variants improve MAE by 5.10%-7.68% while worsening RMSE by 1.63%-3.45%; final-snapshot
  vintages and 2020 coverage prevent operational claims.

See [PROGRESS.md](PROGRESS.md), [DECISIONS.md](DECISIONS.md), and
[docs/methodology.md](docs/methodology.md) for the audit trail.

## Data and evaluation semantics

The target is TÜİK's monthly total of departing visitors—foreign visitors plus Turkish citizens
resident abroad, including overnight and same-day visitors. April-June 2020 are structurally
missing because TÜİK did not produce the corresponding survey estimates. `USD` is actually the
TCMB developed-country CPI-based real effective exchange-rate index, and `HICP` is the Eurostat
euro-area annual inflation rate for passenger transport by air. Their exact local extraction
vintages remain unknown; the verified definitions and official sources are recorded in
[docs/data_sources.md](docs/data_sources.md).

Model accuracy is reported on **full support**: every date with an observed target and a model
forecast. Seasonal-naive skill is reported on **paired support**: the subset on which the same
model, target, and seasonal-naive comparator all exist. The release-aware seasonal-naive
implementation recursively projects an unavailable seasonal reference from earlier observed
seasons without altering the raw target, so the current validated run has 129 full and paired
forecast rows per model in both protocols. The distinction remains part of the metric contract for
models or future runs with different support. Pooled metrics weight forecast rows equally;
macro-fold metrics weight folds equally and are labeled separately.

## Reproduce

Python 3.11 is the reference runtime.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\reproduce.py
```

GNU Make users can run the equivalent `make setup`, `make test`, `make audit`,
`make backtest`, and `make reproduce` targets after setting `PYTHON` to the desired interpreter.
The frozen quarterly holdout is an explicit, registry-appending command:
`make external-validation-2026q1`; it is not invoked by routine `make reproduce`.
Authorized users who place the licensed GTD workbook at the documented private path can reproduce
the aggregate-only security sensitivity with `make gtd-robustness`; the command never writes an
event-level or monthly GTD derivative.

## Data placement

Place private inputs at the paths documented in [data/README.md](data/README.md). The pipeline
records hashes and metadata but does not publish raw values whose redistribution status is not
verified. Code is MIT-licensed; data and source documents retain their original terms.

The requested source-country arrivals/digital-intent panel remains unavailable: no accepted input
provides a historically aligned, forecast-origin-vintaged panel with compatible definitions.
