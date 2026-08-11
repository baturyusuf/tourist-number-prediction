# Methods

## Study objective and estimand

This study evaluates forecasts of Türkiye's monthly total number of departing visitors. The
target combines foreign visitors and Turkish citizens resident abroad and includes overnight and
same-day visitors. It is therefore not a count of unique tourists, foreign-only arrivals, hotel
guests, or Ministry of Culture and Tourism border entries. The primary estimand is out-of-sample
forecast loss under information that could conservatively have been available at each forecast
origin. Predictive association, coefficient-based statistical association, and causal effects are
different estimands and are not inferred from forecast accuracy or feature importance.

## Data, provenance, and target integrity

The supplied monthly composite contains 216 consecutive reference months from January 2008
through December 2025. The source file is identified by SHA-256
`a7885fb0e1ed5de7d64ae180733effc0baebad1e4842ef6bca467466b5b538e5`. The visitor target has
213 observed values. April, May, and June 2020 remain missing because the definition-consistent
TÜİK Departing Visitor Survey did not produce Q2 2020 estimates. Those observations were excluded
from loss calculations. They were not set to zero and were not replaced by Ministry border-entry
counts, which measure a different construct. A separately named linear interpolation exists only
to reproduce legacy calculations and was not used in the confirmatory backtests.

After the models and evaluation rules were frozen, official TÜİK release 58142 supplied a
same-definition total of 9,258,129 departing visitors for 2026 Q1. Only the quarter total was
archived; independently verified monthly 2026 outcomes were not available. Run
`external_2026q1_20260811T171249Z_71f005f4` therefore sums each model's January–March forecasts and
scores one quarterly aggregate. The forecast origin is 31 December 2025, target history is limited
to September 2025 under the three-completed-month convention, and the 2026 outcome was not used for
tuning or model selection.

The same local composite includes (i) the Central Bank of the Republic of Türkiye's monthly
CPI-based real effective exchange-rate developed-country subindex, rebased to 2025 = 100; (ii)
Eurostat's annual percentage change in the euro-area HICP for passenger transport by air; and
(iii) a legacy search-interest series. The first two variables have verified definitions but no
archived extraction vintages in the supplied file. The search-interest series lacks its query or
topic, geography, category, search type, request window, extraction time, normalization design,
and vintage. None of these contemporaneous retrospective values entered the confirmatory ex-ante
models. The undocumented search series was rejected rather than treated as Google Trends evidence.

Two additional workbooks were audited before any attempted integration. A local Instagram
hashtag workbook was rejected because its three sheets duplicate the same 300,000 rows, cover only
approximately one year, lack a defensible unit of observation and Türkiye-specific travel-intent
measure, and do not match the cited Kaggle dataset. A local Global Terrorism Database workbook was
eligible only for licensed, noncommercial, common-sample association or robustness analysis through
2020. It was used in a separate aggregate retrospective sensitivity described below, not in the
confirmatory leaderboard. The absence of post-2020 GTD events was never encoded as zero security
risk.

## Forecast-origin information set

The retrospective target snapshot did not include historical issue dates. We therefore imposed a
prespecified conservative release convention: a target value was eligible only after three
complete calendar months had elapsed after its reference month. For a forecast of month *t* made
at the end of month *t−1*, the latest eligible target was consequently *t−4*. For example, the
forecast origin for January 2025 was 31 December 2024 and the target history available through that
origin ended in September 2024. Each fold records the origin, target-availability cutoff, and delay.
This convention is an operational sensitivity assumption, not a claim that every historical TÜİK
release followed an invariant three-month schedule.

Two forecast protocols were evaluated separately:

1. **Rolling one-step ex ante.** Each month *t* was forecast at the end of *t−1*, after which the
   origin advanced by one month. There were 132 scheduled origins from January 2015 through
   December 2025 and 129 evaluable outcomes after excluding the three missing Q2 2020 targets.
2. **Fixed-origin 12-month ex ante.** All monthly forecasts for a calendar year were issued at the
   end of the preceding year and held fixed. Eleven annual origins, covering 2015–2025, produced
   129 evaluable monthly outcomes. Realized targets within the forecast year were never used to
   update later horizons.
3. **External 2026-Q1 quarterly holdout.** Five previously specified univariate models issued
   January–March forecasts at the 31 December 2025 origin. Their monthly predictions were summed
   and compared once with the official quarter total. Because monthly official outcomes were not
   archived, the exercise does not estimate monthly 2026 MAE, RMSE, or forecast intervals.

The protocols answer different operational questions and were not pooled into one ranking. A
third calculation reproduced a previously reported 2025 seasonal-naive result under
observation-availability: it assumes the complete 2024 vector was usable on 31 December 2024.
Because that issue-date condition was not verified, the reproduction was not included as
confirmatory operational evidence.

## Candidate models

Seasonal naive, which forecasts each month from its value one year earlier, was the mandatory
reference. Under the conservative release mask, an unavailable seasonal reference was projected
recursively from the preceding season inside the model; the raw target was not altered. Additional
simple benchmarks were the last available observation, drift, same-calendar-month historical
mean, and a three-season moving average.

The fixed-origin comparison also included additive damped-trend/additive-seasonal Holt–Winters,
Theta with seasonal adjustment, SARIMA(1,1,1)(1,1,1)[12] with a constant, dynamic harmonic
regression using two Fourier pairs and ARIMA(1,1,1) errors, and robust STL decomposition with an
ARIMA(1,1,1) remainder. Statistical models requiring a complete training vector used an explicit
model-internal seasonal fill for missing training targets; this did not change the stored source
series.

The target-history/calendar feature block, denoted B0, contained target lags 1, 2, 3, 6, 12, 13,
18, and 24 months, with the three-month target-publication delay applied before feature
construction; 3-, 6-, 12-, and 24-month rolling means, medians, and standard deviations; an
expanding mean; year-over-year change and seasonal difference; a linear time index; month
indicators; a high-season indicator; and two Fourier pairs. Ridge regression, histogram gradient
boosting, extremely randomized trees, and XGBoost were evaluated on this block where specified.
Median imputation and, for ridge, robust scaling were estimated within each training fold. Random
seeds and parameter grids were frozen in the project configuration.

The one-step ridge and histogram-gradient-boosting configurations were prespecified from the first
configuration in their frozen grids rather than selected on the outer test observations. The
one-step ridge penalty was 0.1. For fixed-origin machine-learning models, hyperparameters were
selected separately inside each outer training window using up to three earlier annual
fixed-origin validation folds. Inner forecasts were recursive, so actual values from an inner
validation year never became predictors for its later months. The fitted fixed-origin models then
generated the full 12-month outer path recursively from their own predictions. This design avoids
teacher forcing.

No deep neural network was fitted. With only 216 national monthly rows and major structural shock
behavior, such models would add capacity without a correspondingly large independent sample. No
contemporaneous or realized future exchange-rate, airfare-inflation, search, or security path was
used in the confirmatory ex-ante leaderboard. Separate snapshot-vintage and GTD common-sample
sensitivities were kept outside that ranking because their historical operational vintages are
unknown.

## Retrospective snapshot-vintage feature ablation

Run `ablation_20260811T165312Z_69334f2b` compared one-step ridge B0 with three added feature blocks
on the same 129 evaluable months from 2015–2025: B1 added REER, B2 added euro-area passenger-air
HICP inflation, and B5 added both. Each external series was assigned a one-completed-month
publication delay, so at the end-of-*t−1* origin the most recent candidate input was its value for
*t−2*. The models used the prespecified ridge penalty 0.1, identical target-history/calendar
features, training-only preprocessing, and exact paired target months. Because the supplied REER
and HICP extraction vintages were not archived, this design evaluates a lagged retrospective
snapshot, not a reconstructed real-time information set.

Each block was compared with B0 using absolute and squared loss, an 11-lag Newey–West
Diebold–Mariano statistic, and a 2,000-repetition moving-block bootstrap with 12-month blocks. B3
(digital intent) was not estimable because the legacy search series lacks provenance; B6 and B7
were not estimable because no accepted historically aligned digital panel or full multisource
sample existed.

## Aggregate GTD sensitivity

Run `gtd_20260811T172334Z_6527a1fb` used selected fields from the licensed GTD workbook in memory
and wrote only aggregate outputs. The analysis was restricted to January 2008–December 2020 and
never extended security counts beyond coverage. Nine prespecified definitions varied whether
events were broad, non-doubtful, strict, successful, coordinate-known, or within 100 km of a
prespecified tourism center. The ninth classified high-severity incidents only when both casualty
fields were observed and `nkill + nwound >= 10`; partial records remained unknown rather than zero.

The 100-km sensitivity used five manually prespecified WGS84 approximate city-center points:
Istanbul (41.0082, 28.9784), Antalya (36.8969, 30.7133), Muğla (37.2153, 28.3636), İzmir
(38.4237, 27.1428), and Nevşehir/Cappadocia (38.6244, 34.7239). Great-circle distance was calculated
with the haversine formula. These points are neither administrative boundaries nor comprehensive
national tourism geography; the radius analysis is only a spatial sensitivity.

The association sensitivity regressed `log1p` monthly departing visitors on incident counts in
separate models at lags 0, 1, 2, 3, 6, and 12 months. It included calendar-month indicators, a
linear trend, GTD method indicators at April 2008 and January 2012, and heteroskedasticity- and
autocorrelation-consistent standard errors with 12 lags. Benjamini–Hochberg adjustment covered the
entire family of 54 definition-by-lag tests. These regressions are descriptive associations, not
causal estimates.

The predictive sensitivity compared prespecified ridge B0 and B4 models (`alpha=10`) on 69
identical rolling one-step outcomes from January 2015–December 2020. Both models restricted target
history to *t−4*. B4 added a three-month incident-count sum ending at *t−4*, under an assumed
three-completed-month security-reporting delay. Absolute-loss uncertainty used a 2,000-repetition
moving-block bootstrap with 12-month blocks. The GTD file is a final retrospective snapshot with no
issue-date archive or verified historical release calendar. This is therefore an aggregate-only
timing sensitivity, not an operational vintage test or deployable security forecast.

## Validation, metrics, and uncertainty

All outer folds used an expanding window and preserved temporal order. Random splitting and
shuffling were prohibited. Forecast rows were keyed by run identifier, protocol, fold, origin,
horizon, target month, model, actual, prediction, interval bounds where available, and availability
metadata.

Standalone model accuracy used **full support**: every row on which the target and that model's
forecast were observed. Relative skill used **paired support**: only rows on which the target, the
candidate forecast, and the seasonal-naive forecast were all present. Skill was calculated as

\[
\operatorname{skill}(m,b)=1-\frac{L_m}{L_b},
\]

where `L_m` and `L_b` are losses for the candidate and benchmark on identical observations.
Positive values favor the candidate. Pooled metrics weighted each forecast observation equally;
macro-fold summaries, retained in machine-readable outputs, weighted folds equally. The principal
accuracy statistics were mean absolute error (MAE), root mean squared error (RMSE), symmetric mean
absolute percentage error (sMAPE), weighted absolute percentage error (WAPE), mean absolute scaled
error (MASE), and root mean squared scaled error (RMSSE). MAPE and R-squared were secondary because
percentage and variance-explained measures can be unstable in low-volume shock months.

MASE and RMSSE used the seasonal in-sample scale available within each outer fold. Because this
denominator changes as the expanding window advances, scaled errors are reported as explicitly
unweighted macro-fold means and medians rather than with a synthetic pooled denominator. Pooled
MAE, RMSE, sMAPE, and WAPE remain the observation-weighted headline summaries.

For models with 95% intervals, empirical coverage, mean and median width, and Winkler score were
reported. Interval construction was model-specific. Naive, seasonal-naive, drift, same-month,
moving-average, Holt–Winters, and STL forecasts used normal approximations based on finite
in-sample residual dispersion, with square-root horizon widening where specified; Theta and fitted
state-space ARIMA models used their model-provided intervals. No post-hoc coverage calibration was
applied. These intervals are therefore retrospective diagnostics under different assumptions, not
interchangeable probabilistic forecasts. Candidate-versus-seasonal-naive loss differences used
two-sided Diebold–Mariano tests
with Newey–West long-run variance and 11 lags, together with 2,000-repetition moving-block
bootstrap intervals using a 12-month block. A numerical ranking was not called a stable accuracy
improvement when the equal-accuracy test was not rejected and the bootstrap interval included
zero. Regime summaries were descriptive, using pre-pandemic (through February 2020), pandemic
shock (March–December 2020, excluding missing targets), recovery (2021–2022), and normalization
(2023–2025) periods; these labels were not supplied as ex-ante model features.

## Reproducibility and evidence boundary

The confirmatory results derive from immutable run `run_20260811T162732Z_6bbfe89e`; the snapshot
ablation, final GTD sensitivity, and quarterly external holdout derive from clean runs
`ablation_20260811T165312Z_69334f2b`, `gtd_20260811T172334Z_6527a1fb`, and
`external_2026q1_20260811T171249Z_71f005f4`, respectively. Each used the frozen configuration and a
clean committed source state.
Machine-readable forecasts, fold metrics, aggregate leaderboards, comparison tables, and figure
inputs are retained in the repository; dependency versions are locked. Raw restricted files and
the private source manuscript are excluded from version control.

The monthly modeling snapshot ends in December 2025. The external evidence adds one official
same-definition 2026-Q1 total, not monthly 2026 outcomes. The study therefore reports only
quarter-total absolute error and absolute percentage error for that single holdout. It makes no
claim about monthly 2026 accuracy, later 2026 quarters, prediction-interval coverage, or statistical
significance from one quarterly observation.
