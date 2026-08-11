# Validated forecasting leaderboard

Seasonal naive is the mandatory reference. Positive skill means lower loss than seasonal naive.
Protocols are separate; values from incompatible tasks must not be compared as one competition.
`pooled_full_*` reports every evaluable model target. `pooled_paired_*` and skill use the exact
model/seasonal-naive common support. Macro-fold quantities remain in the CSV artifact.

The primary conclusions from `run_20260811T162732Z_6bbfe89e` are unchanged: seasonal naive has the
lowest fixed-origin 12-month pooled MAE (957,226). Rolling one-step ridge B0 reports 7.86% pooled
MAE skill, but its paired uncertainty interval includes zero and performance is regime dependent.
Snapshot-vintage B1/B2/B5 ablations do
not improve MAE over B0 in `ablation_20260811T165312Z_69334f2b`, and all paired bootstrap
intervals span zero.

## Fixed-origin 12-month ex ante

Seasonal naive is the selected reference and lowest-MAE model: 957,226 over 129 evaluable targets
from 11 annual origins. No model establishes positive MAE skill in this operational protocol.
The complete model rows appear in the protocol-preserving table below.

## Rolling one-step ex ante

Ridge B0 has the lowest pooled MAE (825,882 versus 896,358 for seasonal naive), but its 7.86%
point skill is not robust to the paired forecast-comparison tests or the latest normalization
regime. It is therefore a qualified result, not a replacement for the mandatory benchmark.

## Conditional/ex-post

No conditional leaderboard is published. No accepted feature had a credible realized-future path
that could support this separate task, and conditional scores are never mixed into the ex-ante
table.

## Official 2026-Q1 quarterly holdout

Run `external_2026q1_20260811T171249Z_71f005f4` uses a 2025-12-31 origin, target availability
through 2025-09, and no 2026 tuning. Only the official quarter total is scored.

| model | Q1 forecast | official Q1 actual | signed error | absolute error | APE |
|---|---:|---:|---:|---:|---:|
| seasonal naive | 9,121,152 | 9,258,129 | −136,977 | 136,977 | 1.4795% |
| theta | 9,091,751.67 | 9,258,129 | −166,377.33 | 166,377.33 | 1.7971% |
| STL-ARIMA(1,1,1) | 9,655,879.36 | 9,258,129 | +397,750.36 | 397,750.36 | 4.2962% |
| ETS Holt-Winters | 9,742,985.15 | 9,258,129 | +484,856.15 | 484,856.15 | 5.2371% |
| seasonal moving average (3) | 8,770,936 | 9,258,129 | −487,193 | 487,193 | 5.2623% |

This single quarterly holdout supports only a narrow external check. Monthly actuals were not
independently archived, so monthly metrics and quarter intervals are not reported.

## GTD common-sample sensitivity

Final run `gtd_20260811T172334Z_6527a1fb` evaluates nine definitions on 69 common one-step months.
Every B4 variant improves MAE versus B0 by 5.10%-7.68%, with 12-month block-bootstrap absolute-loss
intervals below zero, but every variant worsens RMSE by 1.63%-3.45%. The best MAE point estimate is
the prespecified complete-case high-severity definition: B4 MAE 830,673.87 versus B0 899,756.68
(7.6779% skill), mean absolute-loss difference −69,082.81, 95% interval
[−181,386.59, −37,128.98], and B4 RMSE 1,387,763.30 versus B0 1,365,442.45 (−1.6347% skill).
Across nine definitions × six lags, high-severity lags 1, 2, and 6 have nominal p-values 0.013041,
0.049795, and 0.031822, but none survives the 54-test BH correction (minimum adjusted p=0.615394).
These are retrospective licensed sensitivities, not entries in the primary operational leaderboard.

## Source-country panel extension

Not estimable from the accepted inputs. A definition-consistent country-month arrival target and
historically archived, forecast-origin-vintaged digital-intent panel were unavailable; no blank or
fabricated leaderboard rows are reported.

## Complete ex-ante model table

The protocol column below keeps fixed-origin and rolling one-step results distinguishable. Values
across protocols are not ranked against one another.

| protocol                 | model                               |   folds |   pooled_full_n |   pooled_full_mae |   pooled_full_rmse |   pooled_full_smape |   pooled_paired_n |   pooled_paired_mae |   pooled_paired_seasonal_naive_mae |   pooled_paired_mae_skill_vs_seasonal_naive | pooled_full_interval_95_coverage   |
|:-------------------------|:------------------------------------|--------:|----------------:|------------------:|-------------------:|--------------------:|------------------:|--------------------:|-----------------------------------:|--------------------------------------------:|:-----------------------------------|
| fixed_origin_12m_ex_ante | seasonal_naive                      |      11 |             129 |  957226           |        1.44829e+06 |             30.0058 |               129 |    957226           |                             957226 |                                      0      | 0.9380                             |
| fixed_origin_12m_ex_ante | stl_arima_111                       |      11 |             129 |  986649           |        1.3985e+06  |             29.4496 |               129 |    986649           |                             957226 |                                     -0.0307 | 0.8605                             |
| fixed_origin_12m_ex_ante | theta                               |      11 |             129 |       1.00085e+06 |        1.50021e+06 |             30.0685 |               129 |         1.00085e+06 |                             957226 |                                     -0.0456 | 0.9845                             |
| fixed_origin_12m_ex_ante | ets_holt_winters                    |      11 |             129 |       1.02453e+06 |        1.35341e+06 |             30.0445 |               129 |         1.02453e+06 |                             957226 |                                     -0.0703 | 0.8295                             |
| fixed_origin_12m_ex_ante | seasonal_moving_average_3           |      11 |             129 |       1.03068e+06 |        1.37687e+06 |             29.8332 |               129 |         1.03068e+06 |                             957226 |                                     -0.0767 | 0.7287                             |
| fixed_origin_12m_ex_ante | dynamic_harmonic_arima_k2           |      11 |             129 |       1.07967e+06 |        1.50039e+06 |             40.5432 |               129 |         1.07967e+06 |                             957226 |                                     -0.1279 | 0.6899                             |
| fixed_origin_12m_ex_ante | same_month_historical_mean          |      11 |             129 |       1.1584e+06  |        1.42009e+06 |             34.6901 |               129 |         1.1584e+06  |                             957226 |                                     -0.2102 | 0.6434                             |
| fixed_origin_12m_ex_ante | extra_trees_recursive_b0            |      11 |             129 |       1.19403e+06 |        1.47606e+06 |             35.3196 |               129 |         1.19403e+06 |                             957226 |                                     -0.2474 |                                    |
| fixed_origin_12m_ex_ante | sarima_111_111_12                   |      11 |             129 |       1.31934e+06 |        1.85121e+06 |             51.897  |               129 |         1.31934e+06 |                             957226 |                                     -0.3783 | 0.7829                             |
| fixed_origin_12m_ex_ante | hist_gradient_boosting_recursive_b0 |      11 |             129 |       1.35601e+06 |        1.828e+06   |             38.8015 |               129 |         1.35601e+06 |                             957226 |                                     -0.4166 |                                    |
| fixed_origin_12m_ex_ante | xgboost_recursive_b0                |      11 |             129 |       1.38434e+06 |        1.88589e+06 |             38.4011 |               129 |         1.38434e+06 |                             957226 |                                     -0.4462 |                                    |
| fixed_origin_12m_ex_ante | ridge_recursive_b0                  |      11 |             129 |       1.76604e+06 |        3.36261e+06 |             44.7639 |               129 |         1.76604e+06 |                             957226 |                                     -0.845  |                                    |
| fixed_origin_12m_ex_ante | naive_last                          |      11 |             129 |       2.27916e+06 |        2.69513e+06 |             55.3924 |               129 |         2.27916e+06 |                             957226 |                                     -1.381  | 0.8915                             |
| fixed_origin_12m_ex_ante | drift                               |      11 |             129 |       2.46914e+06 |        2.91787e+06 |             58.0019 |               129 |         2.46914e+06 |                             957226 |                                     -1.5795 | 1.0000                             |
| one_step_ex_ante         | ridge_recursive_b0                  |     132 |             129 |  825882           |        1.33187e+06 |             28.8223 |               129 |    825882           |                             896358 |                                      0.0786 |                                    |
| one_step_ex_ante         | seasonal_naive                      |     132 |             129 |  896358           |        1.40207e+06 |             28.2888 |               129 |    896358           |                             896358 |                                      0      | 0.7752                             |
| one_step_ex_ante         | hist_gradient_boosting_recursive_b0 |     132 |             129 |  917923           |        1.24797e+06 |             25.1949 |               129 |    917923           |                             896358 |                                     -0.0241 |                                    |
| one_step_ex_ante         | seasonal_moving_average_3           |     132 |             129 |       1.00173e+06 |        1.35454e+06 |             28.9899 |               129 |         1.00173e+06 |                             896358 |                                     -0.1176 | 0.7364                             |
| one_step_ex_ante         | same_month_historical_mean          |     132 |             129 |       1.15228e+06 |        1.41016e+06 |             34.4402 |               129 |         1.15228e+06 |                             896358 |                                     -0.2855 | 0.6667                             |
| one_step_ex_ante         | naive_last                          |     132 |             129 |       2.42473e+06 |        2.86841e+06 |             63.7832 |               129 |         2.42473e+06 |                             896358 |                                     -1.7051 | 0.7597                             |
| one_step_ex_ante         | drift                               |     132 |             129 |       2.44918e+06 |        2.90823e+06 |             63.902  |               129 |         2.44918e+06 |                             896358 |                                     -1.7324 | 1.0000                             |
