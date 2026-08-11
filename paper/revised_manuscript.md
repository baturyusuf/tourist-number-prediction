# When Complexity Does Not Beat Seasonality: Release-Aware Monthly Tourism-Demand Forecasting for Türkiye

## Abstract

Tourism-demand models can appear more accurate when they use weak benchmarks, retrospective
covariates, or realized targets from inside a forecast horizon. We re-evaluate monthly forecasts
of Türkiye's total departing visitors under information constraints designed to approximate an
operational setting. The supplied series covers January 2008–December 2025 (216 months); April–June
2020 remain missing because the definition-consistent survey produced no Q2 estimate. Because a
historical target issue-date archive was unavailable, confirmatory backtests impose a conservative
three-completed-month publication delay. We compare expanding-window rolling one-step forecasts
with fixed-origin 12-month forecasts and require the latter to generate each annual path without
teacher forcing. Seasonal naive is the mandatory benchmark. Across 129 evaluable fixed-origin
months from 11 annual origins, seasonal naive had the lowest mean absolute error (MAE 957,226;
RMSE 1,448,293; sMAPE 30.006%). The closest model, robust STL–ARIMA, had MAE 986,649 (−3.07%
skill), and its loss difference was uncertain. Ridge regression using release-delayed target
history and calendar features had a lower pooled one-step MAE than seasonal naive (825,882 versus
896,358; +7.86% skill), but the Diebold–Mariano test did not reject equal accuracy
(*p* = 0.635), the moving-block bootstrap interval crossed zero, and the ordering reversed during
2023–2025 normalization. In separate retrospective sensitivities, lagged REER/HICP blocks added no
MAE value, while an aggregate GTD block improved MAE by 5.10%–7.68% across nine definitions but
worsened RMSE by 1.63%–3.45%. Three high-severity lag associations had raw *p* < 0.05, but none
survived family-wide Benjamini–Hochberg adjustment. Unknown historical vintages make these results
noncausal and nondeployable. On a locked official 2026-Q1 quarter-total holdout, seasonal naive was
best of five (absolute error 136,977; APE 1.479532%). This one quarterly outcome was not used for
tuning and does not provide monthly 2026 accuracy. The findings show that release timing,
recursive evaluation, multiplicity, and outcome granularity must be treated as core elements of
forecast design.

**Keywords:** tourism demand; time-series forecasting; rolling origin; seasonal naive; data
leakage; Türkiye; predictive uncertainty

## 1. Introduction

Monthly tourism demand combines strong seasonality with trend, policy changes, economic
conditions, and rare disruptions. This structure encourages increasingly elaborate models, yet it
also creates several routes to optimistic evaluation. A model may be compared with a weak
nonseasonal benchmark, tuned on the final test period, supplied with covariate values that were not
known at the forecast origin, or allowed to use realized targets from inside a multi-month forecast
window. Under those conditions, a low reported error need not describe deployable forecasting
performance.

Türkiye is a demanding case because tourism volumes are highly seasonal and the COVID-19 period
contains both a structural shock and a survey gap. The target studied here is the monthly total of
departing visitors measured by the Turkish Statistical Institute (TÜİK): foreign visitors plus
Turkish citizens resident abroad, including overnight and same-day visitors. This definition is
broader than foreign-only arrivals and different from hotel stays or Ministry border-entry counts.
Replacing missing survey estimates with a different series would therefore change the estimand.

The original study materials also contained economic and digital candidates. Their presence in a
retrospective spreadsheet does not establish that the values, definitions, or vintages were known
at earlier forecast origins. This study consequently treats data provenance and source timing as
part of model specification. It separates operational ex-ante forecasts from observation-
availability reproductions and conditional exercises, and it separates predictive accuracy from
statistical or causal interpretation.

Four questions organize the analysis:

1. Can any evaluated model improve MAE over seasonal naive when a full 12-month path is issued at
   the preceding year-end?
2. Does monthly one-step updating change the ranking?
3. Are numerical gains stable across the pandemic shock, recovery, and recent normalization?
4. Which proposed external inputs satisfy the minimum provenance, coverage, licensing, and
   forecast-origin-availability requirements for confirmatory use?

The contribution is a reproducible negative result with practical implications. Seasonal naive
remains best by MAE for the primary fixed-origin task. A one-step ridge model is numerically better
in the pooled sample but not statistically distinguishable from the benchmark and not stable in
the recent period. These findings replace claims of complex-model superiority with a narrower,
evidence-bounded account of what the available series can support.

## 2. Data and provenance

### 2.1 Target series

The local composite contains 216 consecutive monthly timestamps from January 2008 through
December 2025 and is identified by SHA-256
`a7885fb0e1ed5de7d64ae180733effc0baebad1e4842ef6bca467466b5b538e5`. The target has 213
observed values. April, May, and June 2020 are missing because the definition-consistent TÜİK
Departing Visitor Survey did not produce Q2 2020 estimates. These months remain missing in the
primary series and are excluded from loss. They are neither interpreted as zero traffic nor
replaced by a definition-different border-entry series.

The observed target mean is 3,465,227 visitors per month, with standard deviation 1,877,655 and a
range from 727,126 to 8,912,005. These statistics describe the supplied retrospective snapshot;
they do not establish which vintage was historically available.

After all model rules were frozen, official TÜİK release 58142 provided a same-definition total of
9,258,129 departing visitors for 2026 Q1. Only the quarterly total was archived. It was used as one
external aggregate holdout and was not appended to the monthly training panel or used for tuning.

### 2.2 Economic and digital candidates

The spreadsheet field originally labeled `USD` is the Central Bank of the Republic of Türkiye
CPI-based real effective exchange-rate developed-country subindex, rebased to 2025 = 100. A higher
value denotes real appreciation, not a higher nominal USD/TRY rate. The HICP field is Eurostat's
annual percentage change for euro-area passenger transport by air, not a general price index. Their
definitions are verified, but the supplied historical extraction vintages are not.

The legacy search-interest series lacks a query or topic, geography, category, search type,
request window, extraction timestamp, normalization method, and vintage. It was rejected from
confirmatory models. A separate Instagram workbook was also rejected: its three sheets repeat the
same 300,000 rows, cover approximately one year, lack a defensible unit of observation and a
Türkiye-specific travel-intent measure, and do not match the cited Kaggle dataset.

A local Global Terrorism Database workbook was identified with near certainty from its schema and
coverage. Its use is governed by the START license, its complete distribution ends in 2020, and it
contains collection-method changes and structured missingness. It was therefore eligible only for
licensed 2008–2020 common-sample association or robustness analysis. A separate aggregate
retrospective GTD sensitivity was completed, but GTD did not enter the confirmatory leaderboard and
post-2020 months were not filled with zero events.

## 3. Methods

### 3.1 Information set and forecast protocols

The retrospective target file had no historical issue-date archive. We imposed a prespecified
conservative convention under which a target value became eligible only after three complete
calendar months. At the end of month *t−1*, the latest target for forecasting month *t* was thus
*t−4*. At the 31 December 2024 origin for January 2025, for example, eligible target history ended
in September 2024. This is an explicit operational sensitivity assumption rather than an assertion
that every historical TÜİK release followed a fixed lag.

The rolling one-step protocol forecast each month from January 2015 through December 2025 at the
end of the preceding month. It contained 132 scheduled origins and 129 evaluable targets after the
three missing Q2 2020 outcomes were excluded. The fixed-origin protocol issued all 12 monthly
forecasts for each year 2015–2025 at the end of the preceding year. Its 11 annual origins also
yielded 129 evaluable outcomes. A fixed-origin model could not consume realized targets from inside
the forecast year.

The external quarterly holdout used the frozen 31 December 2025 origin and target history only
through September 2025. Five previously specified univariate models forecast January–March 2026;
their predictions were summed and compared with the official Q1 total. Monthly official outcomes
were not independently archived, so no monthly 2026 error metric or interval coverage was inferred.

An additional 2025 calculation used observation-availability to reproduce a legacy seasonal-naive
result. It assumed the full 2024 vector was available on 31 December 2024. Because that condition
could not be verified from issue dates, it was reported separately and did not select a model.

### 3.2 Models and feature construction

Seasonal naive was the mandatory reference. It forecast a target month from the corresponding
month one year earlier. When the conservative release mask made that reference unavailable, the
model recursively projected it from the preceding season without changing the source target.
Other simple baselines were the last available observation, drift, same-month historical mean, and
a three-season moving average.

The fixed-origin comparison added additive damped-trend/additive-seasonal Holt–Winters, seasonal
Theta, SARIMA(1,1,1)(1,1,1)[12] with a constant, dynamic harmonic regression with two Fourier
pairs and ARIMA(1,1,1) errors, and robust STL with an ARIMA(1,1,1) remainder. Where a statistical
model required complete training input, missing training targets received an explicit model-
internal seasonal fill; the stored raw target was not overwritten.

The B0 machine-learning feature block used only release-delayed target history and deterministic
calendar information. It included logical target lags 1, 2, 3, 6, 12, 13, 18, and 24 months;
rolling means, medians, and standard deviations over 3, 6, 12, and 24 months; an expanding mean;
year-over-year change; seasonal difference; linear trend; month indicators; a high-season flag;
and two Fourier pairs. The three-month target delay was applied before target-history features were
constructed. Ridge used training-fold median imputation and robust scaling. Histogram gradient
boosting, extremely randomized trees, and XGBoost used training-fold median imputation.

One-step ridge and histogram gradient boosting used prespecified first-grid configurations rather
than choosing settings on outer outcomes; ridge used penalty 0.1. Fixed-origin machine-learning
hyperparameters were selected within each outer training window on up to three previous annual
fixed-origin folds. Inner and outer annual paths were recursive. Seeds and candidate grids were
frozen in configuration.

No deep-learning model was fitted because 216 national monthly observations did not justify the
additional capacity. No realized future or contemporaneous REER, HICP, search, social-media, or
security values entered the confirmatory ex-ante leaderboard.

### 3.3 Snapshot-vintage and GTD sensitivities

The clean snapshot run `ablation_20260811T165312Z_69334f2b` compared ridge B0 against B1 (B0 plus
REER), B2 (B0 plus passenger-air HICP inflation), and B5 (B0 plus both) on the same 129 one-step
outcomes from 2015–2025. Each external input was assigned a one-completed-month publication delay,
making *t−2* the latest value at the end-of-*t−1* origin. Ridge penalty 0.1, target-history
features, and preprocessing were held constant. Absolute- and squared-loss comparisons used the
same Newey–West Diebold–Mariano and 2,000-repetition, 12-month moving-block procedures as the main
comparison. Because historical extraction vintages are unknown, this was a retrospective snapshot
sensitivity, not a real-time forecast experiment.

The clean licensed-data run `gtd_20260811T172334Z_6527a1fb` retained only aggregate outputs over
the 2008–2020 overlap. Nine prespecified incident definitions varied strictness, success,
coordinate availability, proximity, and severity. High severity meant `nkill + nwound >= 10` only
when both casualty fields were observed; partial records remained unknown rather than zero.

The 100-km sensitivity used haversine distance from five manually prespecified WGS84 approximate
city centers: Istanbul (41.0082, 28.9784), Antalya (36.8969, 30.7133), Muğla (37.2153, 28.3636),
İzmir (38.4237, 27.1428), and Nevşehir/Cappadocia (38.6244, 34.7239). These points are not
administrative boundaries or comprehensive national tourism geography.

Descriptive regressions related `log1p` visitors to incident counts in separate models at lags 0,
1, 2, 3, 6, and 12, controlling for calendar month, trend, and GTD method breaks at April 2008 and
January 2012, with 12-lag HAC standard errors. Benjamini–Hochberg adjustment covered the entire
family of 54 definition-by-lag tests.

The GTD predictive sensitivity compared prespecified ridge B0 and B4 (`alpha=10`) over 69 identical
one-step outcomes from 2015–2020. Both used visitor targets only through *t−4*; B4 added a
three-month incident sum ending at *t−4* under an assumed three-completed-month security delay.
Absolute-loss uncertainty used 2,000 moving-block repetitions with 12-month blocks. The final GTD
snapshot has no verified historical issue dates, so this aggregate exercise is not an operational
vintage test.

### 3.4 Metrics and inference

All folds were expanding-window and time ordered. Standalone metrics used every observed target
and model forecast (**full support**). Relative skill used only dates shared by the candidate,
seasonal naive, and the target (**paired support**):

\[
\operatorname{skill}(m,b)=1-\frac{L_m}{L_b}.
\]

Positive skill favors the candidate. Pooled metrics weight each forecast row equally. The primary
accuracy measure is MAE, supported by RMSE, sMAPE, WAPE, MASE, RMSSE, bias, and secondary MAPE
and R-squared. For available 95% prediction intervals, coverage, width, and Winkler score were
computed.

MASE and RMSSE used each fold's own in-sample seasonal scale and are therefore reported as
unweighted macro-fold means and medians, not with an invented common pooled denominator. Pooled
MAE, RMSE, sMAPE, and WAPE remain the observation-weighted headline summaries. Prediction
intervals were model-specific: simple baselines, Holt–Winters, and STL used residual-normal
approximations (with horizon widening where specified), whereas Theta and fitted state-space ARIMA
models used model-provided intervals. No post-hoc calibration was applied, so coverage comparisons
are retrospective diagnostics under different assumptions.

Candidate-versus-benchmark comparisons used two-sided Diebold–Mariano tests with Newey–West
variance and 11 lags. A 2,000-repetition moving-block bootstrap with 12-month blocks estimated a
95% interval for mean loss difference. Regime summaries—pre-pandemic, pandemic shock, recovery,
and normalization—were descriptive and were not ex-ante predictors.

## 4. Results

### 4.1 Legacy reproduction

Treating the complete 2024 vector as available at the 31 December 2024 origin exactly reproduced
the 2025 seasonal-naive metrics: MAE 156,550, RMSE 184,753, MAPE 3.2796%, sMAPE 3.3456%, WAPE
2.9391%, and R-squared 0.991406. This is a favorable one-year observation-availability result, not
confirmatory evidence of operational performance.

### 4.2 Fixed-origin 12-month forecasts

Seasonal naive had the lowest pooled fixed-origin MAE: 957,226 over 129 evaluable months (Table 1).
Its RMSE was 1,448,293, sMAPE 30.006%, and WAPE 25.259%. Robust STL–ARIMA was the nearest
alternative by MAE at 986,649 (−3.07% skill), followed by Theta at 1,000,850 (−4.56%),
Holt–Winters at 1,024,528 (−7.03%), and the three-season moving average at 1,030,678 (−7.67%).
None improved the primary MAE criterion.

**Table 1. Selected pooled full-support forecast results.**

| Protocol | Model | Months | MAE | RMSE | sMAPE (%) | WAPE (%) | MAE skill |
|---|---|---:|---:|---:|---:|---:|---:|
| Fixed-origin 12-month | Seasonal naive | 129 | 957,226 | 1,448,293 | 30.006 | 25.259 | 0.00% |
| Fixed-origin 12-month | Robust STL–ARIMA | 129 | 986,649 | 1,398,498 | 29.450 | 26.035 | −3.07% |
| Fixed-origin 12-month | Theta | 129 | 1,000,850 | 1,500,206 | 30.069 | 26.410 | −4.56% |
| Fixed-origin 12-month | Holt–Winters | 129 | 1,024,528 | 1,353,406 | 30.045 | 27.035 | −7.03% |
| One-step | Ridge B0 | 129 | 825,882 | 1,331,875 | 28.822 | 21.793 | +7.86% |
| One-step | Seasonal naive | 129 | 896,358 | 1,402,065 | 28.289 | 23.652 | 0.00% |
| One-step | Histogram gradient boosting B0 | 129 | 917,923 | 1,247,967 | 25.195 | 24.222 | −2.41% |

The leading fixed-origin MAE differences were imprecise. STL–ARIMA minus seasonal-naive mean
absolute loss was 29,423 (Diebold–Mariano *p* = 0.746; bootstrap 95% interval −131,901 to
201,718). The corresponding differences were 43,624 for Theta (*p* = 0.449; −67,326 to 134,363)
and 67,302 for Holt–Winters (*p* = 0.590; −176,969 to 252,085). These results do not establish
equivalence; they show that the sample does not resolve the relatively small differences precisely.

Rankings were loss-dependent. Holt–Winters and STL–ARIMA had lower RMSE than seasonal naive even
though their MAE was worse. The machine-learning fixed-origin results were less competitive:
extremely randomized trees had MAE 1,194,032, histogram gradient boosting 1,356,010, XGBoost
1,384,345, and ridge 1,766,040. Recursive annual forecasting exposed error propagation that would
be hidden by teacher forcing.

Seasonal naive's fixed-origin 95% interval coverage was 93.8% with mean width 6.82 million. Theta
covered 98.4% but had mean width 8.60 million. STL–ARIMA (86.0%) and Holt–Winters (82.9%) were
narrower and undercovered, illustrating the trade-off between calibration and sharpness.

On the separate macro-fold scaled-error summary, fixed-origin seasonal naive had mean MASE 2.723
and RMSSE 2.060. Holt–Winters had mean MASE 2.702 and RMSSE 1.981, while Theta had mean RMSSE
2.022. In the one-step task, ridge mean MASE/RMSSE were 2.259/1.400 versus 2.417/1.479 for seasonal
naive. These aggregation-dependent ordering changes reinforce the need to report the weighting and
scale convention alongside every metric.

### 4.3 One-step forecasts and regime dependence

Ridge B0 had pooled one-step MAE 825,882 versus 896,358 for seasonal naive, a numerical improvement
of 7.86%. The mean absolute-loss difference was −70,476, but the Diebold–Mariano test did not reject
equal accuracy (*p* = 0.635); the 12-month block-bootstrap 95% interval, −415,885 to 169,478,
included zero. Squared-loss skill was 9.76%, but its test was also nonsignificant (*p* = 0.805) and
its bootstrap interval crossed zero. Histogram gradient boosting had worse MAE than seasonal naive
but lower RMSE and sMAPE, again showing sensitivity to loss choice.

Ridge's pooled advantage was concentrated in disrupted periods. Before the pandemic, ridge MAE was
595,329 versus 531,550 for seasonal naive. During the seven evaluable pandemic-shock months, the
comparison was 1,864,740 versus 3,383,076; during the 24-month recovery it was 1,271,284 versus
1,927,107. During the 36-month 2023–2025 normalization period, ridge was markedly worse: 724,011
versus 353,945. In 2025 alone, ridge MAE was 563,901 versus 156,550. The lower pooled ridge MAE is
therefore not a stable recent-period advantage.

### 4.4 Snapshot-vintage feature ablation

B1, B2, and B5 added no MAE value to one-step ridge B0 (Table 2). B0 MAE was 825,882. B1 increased
MAE by 3,194, B2 by 6,338, and B5 by 9,515; incremental skills were −0.39%, −0.77%, and −1.15%.
All absolute-loss and squared-loss moving-block intervals crossed zero. Although the added blocks
had lower RMSE point estimates, neither that loss-specific ranking nor the lag assumption recovers
the missing historical extraction vintages.

**Table 2. Ridge snapshot-vintage feature-block comparison with B0.**

| Block | Added input | MAE | MAE skill vs B0 | Absolute-loss difference | DM *p* | Bootstrap 95% interval |
|---|---|---:|---:|---:|---:|---:|
| B1 | REER | 829,077 | −0.39% | 3,194 | 0.889 | [−37,625, 53,342] |
| B2 | Passenger-air HICP inflation | 832,221 | −0.77% | 6,338 | 0.483 | [−9,515, 25,371] |
| B5 | REER and HICP | 835,398 | −1.15% | 9,515 | 0.658 | [−26,947, 56,623] |

### 4.5 Aggregate GTD sensitivity

The broad GTD definition contained 1,777 incidents over 156 months from 2008–2020. Nine definitions
at lags 0, 1, 2, 3, 6, and 12 formed 54 association tests. High-severity lags 1, 6, and 2 had raw
nominal *p*-values 0.013041, 0.031822, and 0.049795, respectively. None survived family-wide
Benjamini–Hochberg adjustment; the minimum adjusted *p* was 0.615394. These results do not support a
lag-specific or causal security claim.

Adding B4 reduced MAE in every 69-month common-sample forecast comparison (Table 3). MAE skill over
B0 ranged from 5.10% to 7.68%, and all nine absolute-loss block-bootstrap intervals were entirely
below zero. However, every B4 definition worsened RMSE, by 1.63%–3.45%. The signal is consequently
loss-dependent.

**Table 3. Aggregate GTD B4 common-sample sensitivity.**

| Security definition | B4 MAE | MAE skill | RMSE change | Absolute-loss bootstrap 95% interval |
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

B0 MAE and RMSE on this restricted sample were 899,756.684 and 1,365,442. The best high-severity B4
had MAE 830,673.869, skill 7.6779%, RMSE 1,387,763, RMSE skill −1.6347%, and unrounded
absolute-loss interval [−181,386.586, −37,128.985]. The GTD workbook is a final retrospective
snapshot, not a historical vintage archive. The aggregate-only B4 result does not establish causal
impact, operational vintage performance, post-2020 value, or a deployable security-driven forecast.

### 4.6 Official 2026-Q1 quarterly holdout

The official same-definition Q1 total was 9,258,129. Seasonal naive forecast 9,121,152 at the
frozen 31 December 2025 origin, giving error −136,977, absolute error 136,977, and APE 1.479532%.
This was the smallest absolute error among five locked models. Theta's absolute error was
166,377.332, STL–ARIMA's 397,750.359, Holt–Winters' 484,856.153, and the three-season moving
average's 487,193.

**Table 4. Official 2026-Q1 quarter-total holdout.**

| Model | Quarter forecast | Official actual | Absolute error | APE |
|---|---:|---:|---:|---:|
| Seasonal naive | 9,121,152 | 9,258,129 | 136,977 | 1.479532% |
| Theta | 9,091,751.668 | 9,258,129 | 166,377.332 | 1.797095% |
| Robust STL–ARIMA | 9,655,879.359 | 9,258,129 | 397,750.359 | 4.296228% |
| Holt–Winters | 9,742,985.153 | 9,258,129 | 484,856.153 | 5.237086% |
| Three-season moving average | 8,770,936 | 9,258,129 | 487,193 | 5.262327% |

This is one quarterly official outcome, not monthly validation. The 2026 value was not used for
tuning, monthly official actuals were not archived, and no interval or significance claim follows
from one quarter.

### 4.7 Evidence boundary

The external sensitivities remain separate from the confirmatory target-history/calendar
leaderboard and do not alter its fixed-origin conclusion. The legacy search series is still
undocumented, and the Instagram workbook remains rejected. The monthly modeling snapshot ends in
December 2025; 2026 evidence is limited to the single official Q1 aggregate described above.

## 5. Discussion

The principal finding is that complexity did not improve the primary fixed-origin MAE over a strong
release-aware seasonal benchmark. This changes the interpretation of the project. The evidence
does not show that XGBoost, SARIMAX, search data, or SHAP produced a superior operational system.
It shows that recurring seasonality explains much of the predictable signal and that availability
and horizon design materially affect apparent accuracy.

The one-step ridge result is better understood as shock sensitivity than general superiority. It
helped during the pandemic and recovery but lost before the pandemic in aggregate and during the
recent normalization period. A monitored ridge forecast could serve as a challenger or ensemble
member, but any switching rule would require a forward-known regime signal and fresh validation.
Retrospective regime labels cannot be converted into an ex-ante deployment claim.

The sharp contrast between the legacy 2025 score and the conservative backtest emphasizes that the
information set is substantive. The legacy calculation assumes all 2024 targets were available at
the year-end origin; the operational convention allows data only through September. Similarly,
monthly updating and annual fixed-origin planning are different tasks. A method that works when
refitted every month need not remain accurate when it must generate a full annual path without
within-year outcomes.

The external-data results and exclusions are also informative. B1/B2/B5 had no incremental MAE
value, and all their absolute- and squared-loss intervals crossed zero. The GTD B4 result was more
consistent under MAE—5.10%–7.68% skill and nine intervals below zero—but uniformly worse under
RMSE. Three high-severity lags were nominally below 0.05, yet none of the 54 association tests
survived family-wide Benjamini–Hochberg correction. Forecast value under one loss does not establish
a lag-specific association, causal mechanism, or universally better model.

These sensitivities do not solve the vintage problem. REER, HICP, and GTD were final retrospective
snapshots, and the assigned delays were assumptions rather than reconstructed release calendars.
The GTD sample ended in 2020 and cannot be extended with zeros. The search series and Instagram
workbook remain rejected. This disciplined separation prevents exploratory aggregate signals from
becoming claims of deployable multisource validation.

The official 2026-Q1 result is a useful but narrow prospective check. Seasonal naive's absolute
quarter error of 136,977 was best among five locked models and accords with its historical
fixed-origin MAE ranking. Nevertheless, it is one quarterly total. It was not used for tuning, and
without archived monthly outcomes it cannot establish monthly 2026 performance or significance.

### 5.1 Practical implications

For annual planning, seasonal naive is the defensible default among the evaluated models because it
had the lowest fixed-origin MAE and is transparent. Its intervals are wide, so decisions should use
ranges and stress scenarios rather than point forecasts alone. Errors should be monitored by
horizon, month, and regime. The leading 2026-Q1 quarter result is encouraging but does not remove
that monitoring requirement.

For monthly updating, ridge B0 is a useful challenger, not a demonstrated replacement. Production
governance can retain both forecasts, track their disagreement, and require prospective evidence
before changing the default. Loss functions should be tied to decision costs before results are
seen; the differing MAE and RMSE rankings show that there is no universally best model here.

### 5.2 Limitations and future work

The analysis uses one national aggregate with only 216 months, a structural pandemic shock, and
three missing target values. Historical issue dates were not supplied, so the target, economic, and
security delays are sensitivity conventions rather than reconstructed vintage calendars. The GTD
predictive result uses only 69 outcomes through 2020 and is loss-dependent. The 2026 external check
contains one quarterly aggregate and no archived monthly outcomes. No source-country panel was
available, and uncertainty comparisons have limited power. Failure to reject equal accuracy is not
proof of model equivalence; an interval below zero in a retrospective sensitivity does not by
itself establish deployability.

Future work should freeze official source vintages before outcomes occur, archive release
timestamps, and test the pipeline prospectively. A harmonized source-country panel may increase
effective sample size if its distinct target definition is maintained. New search or pageview
features should be admitted only through reproducible, geography-specific extraction protocols.
The completed GTD common-sample result should next be tested prospectively with archived operational
timestamps; any bridge to a newer security source requires overlap-definition validation. REER and
HICP likewise require frozen vintages. Future 2026 work should preserve the no-tuning holdout rule
and add monthly or later-quarter evidence only as official same-definition releases become
available.

## 6. Conclusion

Under conservative release-aware evaluation, seasonal naive was the strongest fixed-origin
12-month model by MAE. Ridge reduced pooled one-step MAE, but the difference was uncertain and
reversed in the recent normalization period. The defensible result is not that model complexity has
solved Türkiye tourism forecasting. It is that strong seasonal benchmarks, explicit availability,
recursive testing, and regime-aware uncertainty change what the data can support. B1/B2/B5 added
no MAE value. GTD B4 showed a retrospective, aggregate, loss-dependent MAE signal—not causal,
operational-vintage, or deployable security evidence. Seasonal naive also had the smallest error on
the official 2026-Q1 total, supportive evidence from one quarter rather than monthly validation.

## Data, code, and reproducibility statement

The code, frozen configuration, tests, aggregate tables, forecast records, and figures required to
recompute the reported results are maintained in this repository. Confirmatory forecasts correspond
to immutable run `run_20260811T162732Z_6bbfe89e`; snapshot ablation, final aggregate GTD, and
quarterly external results correspond to `ablation_20260811T165312Z_69334f2b`,
`gtd_20260811T172334Z_6527a1fb`, and `external_2026q1_20260811T171249Z_71f005f4`. Raw composite
data, the private source manuscript, the Instagram workbook, event-level GTD data, and monthly GTD
derivatives are not redistributed. Checksums and admissibility decisions allow authorized users to
verify local copies without publishing restricted rows.

## Ethics, funding, and competing interests

The study analyzes aggregate tourism and structured event data and does not involve human-subject
recruitment. No author-contribution statement, funding information, or competing-interest
declaration was supplied in the source materials; these statements must be completed by the
authors before journal submission. Model outputs are descriptive and predictive, not causal
estimates of policy or security effects.

## Source notes

- Turkish Statistical Institute, *Tourism Statistics, Quarter IV: October–December and Annual,
  2020*, including the absence of a Q2 survey estimate:
  <https://veriportali.tuik.gov.tr/en/press/37438>.
- Turkish Statistical Institute, official 2026-Q1 departing-visitors total and revision context:
  <https://veriportali.tuik.gov.tr/tr/press/58142>.
- Central Bank of the Republic of Türkiye, CPI-based real effective exchange-rate table:
  <https://tcmb.gov.tr/wps/wcm/connect/23c10aa7-4937-400d-9770-31a81b960907/CPI.pdf?CACHEID=ROOTWORKSPACE-23c10aa7-4937-400d-9770-31a81b960907-oMVLvJL&MOD=AJPERES>.
- Eurostat, archived annual HICP rate for euro-area passenger transport by air (`prc_hicp_manr`,
  `RCH_A`, `CP0733`, `EA`):
  <https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?lang=en&geo=EA&unit=RCH_A&coicop=CP0733>.
- Google Trends, normalization and interpretation guidance:
  <https://support.google.com/trends/answer/4365533?hl=en-GB>.
- START (National Consortium for the Study of Terrorism and Responses to Terrorism). (2022).
  *Global Terrorism Database, 1970–2020* [data file].
  <https://www.start.umd.edu/data-tools/GTD>. Copyright University of Maryland 2022.
- GTD terms of use: <https://www.start.umd.edu/gtd-terms>.

## Method references

- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business &
  Economic Statistics, 13*(3), 253–263. <https://doi.org/10.1080/07350015.1995.10524599>.
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy.
  *International Journal of Forecasting, 22*(4), 679–688.
  <https://doi.org/10.1016/j.ijforecast.2006.03.001>.
- Newey, W. K., & West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and
  autocorrelation consistent covariance matrix. *Econometrica, 55*(3), 703–708.
  <https://doi.org/10.2307/1913610>.
