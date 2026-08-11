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
- The supplied target ends in December 2025. No 2026 target observations or 2026 external
  validation results are claimed.

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
model, target, and seasonal-naive comparator all exist. This matters because missing April-June
2020 targets also make lag-12 seasonal-naive forecasts unavailable for April-June 2021, even when
another model can forecast those months. Pooled metrics concatenate eligible forecast rows and
weight observations equally; macro-fold metrics average fold scores and are labeled separately.

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

## Data placement

Place private inputs at the paths documented in [data/README.md](data/README.md). The pipeline
records hashes and metadata but does not publish raw values whose redistribution status is not
verified. Code is MIT-licensed; data and source documents retain their original terms.
