# Results

## Data audit and legacy reproduction

The supplied series contained all 216 monthly timestamps from January 2008 through December 2025,
with no duplicated months, unexpected columns, nonnumeric values, or nonpositive observed targets.
The only missing target values were April–June 2020, leaving 213 observed target months. The mean
observed monthly total was 3,465,227 visitors (standard deviation 1,877,655; range 727,126 to
8,912,005). These descriptive values summarize a revised retrospective snapshot and do not imply
that the same vintage was available at historical forecast origins.

The legacy seasonal-naive calculation for January–December 2025 was exactly reproducible when the
complete 2024 target vector was treated as available at the 31 December 2024 origin. Across 12
months, MAE was 156,550, RMSE 184,753, MAPE 3.2796%, sMAPE 3.3456%, WAPE 2.9391%, and
R-squared was 0.991406. This favorable single-year score is an observation-availability reproduction,
not the confirmatory operational result, because complete 2024 issue-date availability at that
origin could not be verified.

## Fixed-origin 12-month operational forecasts

Seasonal naive had the lowest pooled MAE in the principal fixed-origin task (Table 1). Across 129
evaluable monthly forecasts from 11 annual origins, its MAE was 957,226, RMSE 1,448,293, sMAPE
30.006%, and WAPE 25.259%. The closest alternatives by MAE were robust STL–ARIMA (MAE 986,649;
−3.07% MAE skill), Theta (1,000,850; −4.56%), Holt–Winters (1,024,528; −7.03%), and the
three-season moving average (1,030,678; −7.67%). Thus, no evaluated fixed-origin alternative
improved on seasonal naive under the primary MAE criterion.

Table 1. Pooled full-support results for selected models in the two operational protocols.

| Protocol | Model | Evaluable months | MAE | RMSE | sMAPE (%) | WAPE (%) | MAE skill vs seasonal naive |
|---|---|---:|---:|---:|---:|---:|---:|
| Fixed-origin 12-month | Seasonal naive | 129 | 957,226 | 1,448,293 | 30.006 | 25.259 | 0.00% |
| Fixed-origin 12-month | Robust STL–ARIMA(1,1,1) | 129 | 986,649 | 1,398,498 | 29.450 | 26.035 | −3.07% |
| Fixed-origin 12-month | Theta | 129 | 1,000,850 | 1,500,206 | 30.069 | 26.410 | −4.56% |
| Fixed-origin 12-month | Holt–Winters | 129 | 1,024,528 | 1,353,406 | 30.045 | 27.035 | −7.03% |
| One-step | Ridge B0 | 129 | 825,882 | 1,331,875 | 28.822 | 21.793 | +7.86% |
| One-step | Seasonal naive | 129 | 896,358 | 1,402,065 | 28.289 | 23.652 | 0.00% |
| One-step | Histogram gradient boosting B0 | 129 | 917,923 | 1,247,967 | 25.195 | 24.222 | −2.41% |

Notes: B0 contains only release-delayed target history and deterministic calendar features. Skill
uses the same 129 target months for each listed candidate and seasonal naive. Protocols describe
different decision tasks and should not be compared as though they were interchangeable.

Rankings varied with the loss function. Holt–Winters and STL–ARIMA had lower RMSE than seasonal
naive despite worse MAE, showing that a single ordering does not characterize every aspect of the
error distribution. The closest fixed-origin MAE differences were not statistically distinguishable
from zero: STL–ARIMA minus seasonal-naive mean absolute loss was 29,423 (Diebold–Mariano
*p* = 0.746; 12-month moving-block bootstrap 95% interval −131,901 to 201,718), Theta was 43,624
(*p* = 0.449; −67,326 to 134,363), and Holt–Winters was 67,302 (*p* = 0.590; −176,969 to
252,085). These intervals do not rescue an accuracy-superiority claim; they instead indicate that
the sample does not precisely resolve the small differences among the leading fixed-origin models.

Seasonal naive's fixed-origin 95% interval covered 93.8% of evaluable outcomes, close to the nominal
rate, but its mean width was 6.82 million visitors. Theta covered 98.4% with an even wider mean
interval of 8.60 million. Holt–Winters (82.9% coverage) and STL–ARIMA (86.0%) were narrower but
undercovered. These results favor transparent reporting of both interval reliability and sharpness
rather than ranking intervals by coverage alone. The intervals were not post-hoc calibrated and
arose from different model-specific constructions, so the comparison is diagnostic rather than a
claim that all methods estimate the same probability distribution equally well.

The more flexible target-history models did not improve fixed-origin MAE. Extremely randomized
trees had MAE 1,194,032 (−24.74% skill), SARIMA 1,319,340 (−37.83%), histogram gradient boosting
1,356,010 (−41.66%), XGBoost 1,384,345 (−44.62%), and ridge 1,766,040 (−84.50%). Because all
12 months were generated recursively from a common year-end information set, these results expose
error propagation that a teacher-forced evaluation would conceal.

Fold-scaled errors gave a deliberately separate macro-fold view. Fixed-origin seasonal naive had
mean fold MASE 2.723 and RMSSE 2.060. Holt–Winters had the lowest mean MASE among the leading
models (2.702), while Holt–Winters and Theta had mean RMSSE 1.981 and 2.022, respectively. These
small ordering changes do not overturn the pooled-MAE conclusion; they show why the fold-specific
scale and aggregation rule must be stated. In the one-step task, ridge mean fold MASE was 2.259
versus 2.417 for seasonal naive, and mean fold RMSSE was 1.400 versus 1.479.

## Rolling one-step operational forecasts

Ridge B0 had the lowest pooled one-step MAE, 825,882, compared with 896,358 for seasonal naive, a
numerical MAE skill of 7.86%. Its RMSE was 1,331,875 and WAPE 21.793%. Histogram gradient boosting
did not improve MAE (917,923; −2.41% skill), although it had the lowest RMSE (1,247,967) and sMAPE
(25.195%) among the three leading one-step models. Again, the ordering depended on the chosen loss.

The ridge MAE difference was not robust evidence of higher accuracy. Its mean absolute-loss
difference from seasonal naive was −70,476 visitors, but the two-sided Diebold–Mariano test did not
reject equal predictive accuracy (*p* = 0.635). The 2,000-repetition, 12-month moving-block bootstrap
95% interval was −415,885 to 169,478 and crossed zero. Squared-loss skill was 9.76%, but its
Diebold–Mariano result was also nonsignificant (*p* = 0.805) and the bootstrap interval crossed zero.
The correct interpretation is therefore a numerical pooled gain, not a stable or statistically
established win.

## Regime dependence

The pooled ridge advantage was concentrated in disrupted periods (Table 2). Before the pandemic,
ridge had higher MAE than seasonal naive (595,329 versus 531,550). During the seven evaluable
pandemic-shock months, ridge had lower MAE (1,864,740 versus 3,383,076), and during the 24-month
recovery it also had lower MAE (1,271,284 versus 1,927,107). The ordering reversed sharply during
the 36-month 2023–2025 normalization period: ridge MAE was 724,011, more than twice seasonal
naive's 353,945.

Table 2. One-step MAE by descriptive regime.

| Regime | Evaluable months | Ridge B0 MAE | Seasonal-naive MAE | Lower MAE |
|---|---:|---:|---:|---|
| Pre-pandemic | 62 | 595,329 | 531,550 | Seasonal naive |
| Pandemic shock | 7 | 1,864,740 | 3,383,076 | Ridge B0 |
| Recovery | 24 | 1,271,284 | 1,927,107 | Ridge B0 |
| Normalization | 36 | 724,011 | 353,945 | Seasonal naive |

The year-by-year pattern was consistent with this regime diagnosis. Ridge improved on seasonal
naive in 2018–2022 but was worse in 2015–2017 and every year from 2023 through 2025. In the
operational one-step 2025 fold, ridge MAE was 563,901 versus 156,550 for seasonal
naive. The favorable pooled ridge average therefore does not generalize to the recent normalized
period and should not be extrapolated as a permanent structural advantage.

## Snapshot-vintage macro/travel-cost ablation

The separate one-step snapshot sensitivity found no incremental MAE value from the lagged economic
blocks (Table 3). Relative to ridge B0 MAE of 825,882, B1 (REER) increased MAE by 3,194 to 829,077,
B2 (HICP) increased it by 6,338 to 832,221, and B5 (both) increased it by 9,515 to 835,398.
Incremental MAE skill was therefore −0.39%, −0.77%, and −1.15%, respectively. The absolute-loss
Diebold–Mariano tests did not reject equal accuracy, and every 12-month moving-block interval
crossed zero. The squared-loss point estimates favored the added blocks because their RMSE values
were lower, but all three squared-loss bootstrap intervals also crossed zero. Thus B1, B2, and B5
added no supported MAE value on this snapshot.

Table 3. One-step ridge snapshot-vintage feature-block comparison with B0.

| Block | Added input | MAE | Incremental MAE skill vs B0 | Mean absolute-loss difference | DM *p* | Bootstrap 95% interval |
|---|---|---:|---:|---:|---:|---:|
| B1 | REER | 829,077 | −0.39% | 3,194 | 0.889 | [−37,625, 53,342] |
| B2 | Passenger-air HICP inflation | 832,221 | −0.77% | 6,338 | 0.483 | [−9,515, 25,371] |
| B5 | REER and HICP | 835,398 | −1.15% | 9,515 | 0.658 | [−26,947, 56,623] |

Notes: B0 MAE was 825,882 on the identical 129 target months. Negative skill and positive loss
difference favor B0. Inputs were lagged under stated release assumptions, but their historical
extraction vintages are unknown; the results are retrospective snapshot sensitivities, not
confirmatory operational tests.

## Aggregate GTD common-sample sensitivity

Clean aggregate run `gtd_20260811T172334Z_6527a1fb` contained 1,777 broad-definition incidents
across 156 months from 2008–2020. Nine definitions were evaluated at prespecified incident lags 0,
1, 2, 3, 6, and 12,
creating one family of 54 association tests. Three unadjusted high-severity results were nominally
below 0.05: lag 1 (*p* = 0.013041), lag 6 (0.031822), and lag 2 (0.049795). None survived
family-wide Benjamini–Hochberg adjustment; the minimum adjusted *p*-value was 0.615394. The
high-severity definition required `nkill + nwound >= 10` with both casualty fields observed. These
are descriptive, noncausal associations, and the multiplicity-adjusted evidence does not support a
lag-specific security claim.

In the separate 69-month 2015–2020 one-step predictive sensitivity, adding the availability-lagged
B4 incident block reduced MAE under all nine security definitions (Table 4). MAE skill over the
common-sample B0 model ranged from 5.10% to 7.68%, and every 12-month moving-block absolute-loss
interval was entirely below zero. The same B4 models worsened RMSE by 1.63%–3.45%. The apparent
benefit is therefore loss-dependent even within the restricted overlap sample.

Table 4. Aggregate GTD B4 sensitivity by security definition.

| Security definition | B4 MAE | MAE skill vs B0 | RMSE change vs B0 | Absolute-loss bootstrap 95% interval |
|---|---:|---:|---:|---:|
| Broad GTD | 844,672 | 6.12% | +2.41% | [−176,550, −11,975] |
| `doubtterr == 0` | 841,890 | 6.43% | +2.22% | [−179,024, −14,312] |
| Strict criteria and `doubtterr == 0` | 841,676 | 6.46% | +2.22% | [−179,458, −14,324] |
| Successful only | 840,658 | 6.57% | +2.45% | [−180,318, −17,508] |
| Known coordinates only | 843,736 | 6.23% | +2.42% | [−179,137, −11,462] |
| Strict with known coordinates | 840,947 | 6.54% | +2.23% | [−182,032, −13,363] |
| Within 100 km of five city centers | 847,791 | 5.78% | +3.45% | [−174,322, −5,346] |
| Strict within 100 km | 853,909 | 5.10% | +3.30% | [−158,625, −2,111] |
| High severity, complete case | 830,674 | 7.68% | +1.63% | [−181,387, −37,129] |

Notes: B0 MAE and RMSE were 899,756.684 and 1,365,442 on the identical 69 outcomes. The best
high-severity B4 values were MAE 830,673.869, skill 7.6779%, RMSE 1,387,763, and RMSE skill
−1.6347%; its unrounded absolute-loss interval was [−181,386.586, −37,128.985]. Positive RMSE
change denotes deterioration. The final GTD workbook has no historical issue-date archive; both
the three-completed-month reporting delay and retrospective event definitions are sensitivity
assumptions. Only aggregate results were retained. These findings are not causal, do not establish
operational vintage performance, and are not evidence for deploying a security-driven forecaster.

## Evidence boundary after the sensitivities

The confirmatory fixed-origin and one-step leaderboards remain target-history/calendar analyses.
The B1/B2/B5 and GTD B4 results do not change the primary conclusion because they are separate
retrospective-vintage sensitivities. The legacy search series remains undocumented, and the local
Instagram workbook remains rejected.

## Official 2026-Q1 quarterly external holdout

External run `external_2026q1_20260811T171249Z_71f005f4` evaluated an official same-definition Q1
total of 9,258,129 departing visitors. Seasonal naive forecast
9,121,152 at the frozen 31 December 2025 origin, an error of −136,977, absolute error 136,977, and
absolute percentage error 1.479532%. It had the smallest quarter-total absolute error among all
five locked models (Table 5). Theta was second at 166,377.332, followed by STL–ARIMA at
397,750.359, Holt–Winters at 484,856.153, and the three-season moving average at 487,193.

Table 5. Official 2026-Q1 quarter-total external holdout.

| Model | Q1 forecast | Official Q1 actual | Absolute error | Absolute percentage error |
|---|---:|---:|---:|---:|
| Seasonal naive | 9,121,152 | 9,258,129 | 136,977 | 1.479532% |
| Theta | 9,091,751.668 | 9,258,129 | 166,377.332 | 1.797095% |
| Robust STL–ARIMA | 9,655,879.359 | 9,258,129 | 397,750.359 | 4.296228% |
| Holt–Winters | 9,742,985.153 | 9,258,129 | 484,856.153 | 5.237086% |
| Three-season moving average | 8,770,936 | 9,258,129 | 487,193 | 5.262327% |

This is one official quarterly aggregate, not three verified monthly outcomes. No 2026 observation
was used for tuning. Monthly 2026 MAE, RMSE, R-squared, and interval coverage were not estimated,
and no significance claim can be made from one quarter.
