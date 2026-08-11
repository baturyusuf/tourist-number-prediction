# Reproduction report

## Reproduced benchmark

The supplied core CSV has SHA-256 `a7885fb0e1ed5de7d64ae180733effc0baebad1e4842ef6bca467466b5b538e5`. Training ends in December 2024 and the
forecast for each month of 2025 is the observed target exactly 12 months earlier. No realized
2025 target or exogenous value is consumed.

This legacy calculation assumes the complete 2024 target vector was available at the
31 December 2024 origin. Because a historical issue-date archive was not supplied, it is an
observation-availability reproduction, not the confirmatory operational ex-ante protocol.

| Metric | Reproduced value |
|---|---:|
| RMSE | 184,753.215374 |
| MAE | 156,550.416667 |
| MAPE | 3.27963777% |
| sMAPE | 3.34558651% |
| WAPE | 2.93912942% |
| MASE | 0.24666279 |
| RMSSE | 0.16584641 |
| R² | 0.9914064091 |
| Bias (forecast - actual) | -140,384.083333 |

The preliminary RMSE, MAE, MAPE, and R² are reproduced to the stated rounding precision.
This is a single favorable legacy year and is not evidence that a model is generally superior.

## Manuscript model reconstruction status

The reported SARIMAX and XGBoost scores remain unverified until the manuscript's blank feature
labels, exact orders/hyperparameters, preprocessing fit scope, lag-selection process, teacher
forcing behavior, and future-exogenous use are reconstructed. The pipeline records that gap
rather than selecting configurations on 2025 until the reported values appear.
