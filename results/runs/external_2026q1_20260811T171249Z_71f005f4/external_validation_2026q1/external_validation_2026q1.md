# 2026-Q1 external validation

Run `external_2026q1_20260811T171249Z_71f005f4` freezes the official TÜİK 2026-Q1 departing-visitors total of
**9,258,129** from release
[58142](https://veriportali.tuik.gov.tr/tr/press/58142), published
2026-04-30. Release
[54155](https://veriportali.tuik.gov.tr/tr/press/54155) reports
9,121,152 for 2025-Q1, exactly matching the supplied January-
March monthly sum and supporting the definition bridge. Both pages were accessed
2026-08-11; reproduction uses the frozen evidence embedded in source and makes
no network request.

Forecasts use a fixed 2025-12-31 origin and targets available only through 2025-09 under the
three-completed-month delay sensitivity. January-March predictions are summed and compared with the
official quarter total. Monthly official actuals were not independently archived, so no monthly
MAE, RMSE, R², or reconstructed monthly accuracy is reported. Quarter intervals are omitted because
the dependence needed to aggregate monthly forecast uncertainty was not identified.

| model                     | quarter_forecast   | official_quarter_actual   | quarter_error_forecast_minus_actual   | quarter_absolute_error   | quarter_absolute_percentage_error   | quarter_absolute_error_skill_vs_seasonal_naive   |
|:--------------------------|:-------------------|:--------------------------|:--------------------------------------|:-------------------------|:------------------------------------|:-------------------------------------------------|
| seasonal_naive            | 9,121,152          | 9,258,129                 | -136,977                              | 136,977                  | 1.480%                              | 0.00%                                            |
| stl_arima_111             | 9,655,879          | 9,258,129                 | 397,750                               | 397,750                  | 4.296%                              | -190.38%                                         |
| theta                     | 9,091,752          | 9,258,129                 | -166,377                              | 166,377                  | 1.797%                              | -21.46%                                          |
| ets_holt_winters          | 9,742,985          | 9,258,129                 | 484,856                               | 484,856                  | 5.237%                              | -253.97%                                         |
| seasonal_moving_average_3 | 8,770,936          | 9,258,129                 | -487,193                              | 487,193                  | 5.262%                              | -255.68%                                         |
