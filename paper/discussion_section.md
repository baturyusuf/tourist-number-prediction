# Discussion

## Principal finding

The central result is negative in the scientifically useful sense: added model complexity did not
improve the primary fixed-origin 12-month MAE over a release-aware seasonal-naive benchmark.
Seasonal naive remained first by MAE across 129 evaluable months from 11 annual origins. Robust
STL–ARIMA, Theta, and Holt–Winters were close enough that uncertainty intervals included zero loss
difference, but their point estimates were worse. The machine-learning candidates deteriorated
more substantially when required to generate a full year recursively without within-year actuals.

This result revises the study's contribution. The evidence does not support a claim that XGBoost,
SARIMAX, search data, or SHAP produced a superior operational forecasting system. Instead, it shows
how seasonal persistence, release timing, and the forecast protocol can dominate apparent gains in
a short monthly tourism series. A strong simple benchmark is not merely a hurdle; it is an estimate
of how much of the target's predictability arises from recurring seasonality.

## Why the one-step ridge result is not a general win

Ridge B0 reduced pooled one-step MAE by 7.86% relative to seasonal naive, but three pieces of
evidence argue against presenting that number as a stable improvement. First, neither the
autocorrelation-aware Diebold–Mariano test nor the 12-month moving-block bootstrap excluded equal
accuracy. Second, ridge was worse before the pandemic in aggregate and more than twice as inaccurate
as seasonal naive during 2023–2025 normalization. Third, its pooled gain was generated mainly by
the pandemic shock and recovery, when last year's seasonal level became an unusually poor guide.

This regime dependence has operational implications. A forecaster might use ridge as one member of
a monitored ensemble or as a shock-robust challenger, but these results do not justify replacing
seasonal naive unconditionally. Any switching or weighting rule would itself require a prespecified,
forward-looking regime signal and new out-of-sample validation. The retrospective regime labels in
this study describe errors; they were not available features and must not be converted after the
fact into a claim of deployable model selection.

## Forecast protocol and availability are substantive design choices

The legacy 2025 seasonal-naive score was excellent, but it assumed that the full 2024 target vector
was available at the 31 December 2024 forecast origin. Under the conservative three-completed-month
release convention, September 2024 was the latest eligible target. The difference between the
legacy reproduction and the confirmatory backtest is therefore not a software discrepancy; it is a
difference in the information set.

Likewise, one-step and fixed-origin forecasts should not be merged into a single ranking. A rolling
one-step system can revise its model every month, whereas a fixed-origin system commits to a full
annual path. Recursive fixed-origin evaluation exposed error accumulation in target-history
machine-learning models. Evaluations that insert realized within-year targets into later lags would
answer an easier, partly retrospective question and could materially overstate annual forecasting
performance.

## Interpretation of external variables

No causal conclusion about exchange rates, airfare inflation, digital interest, or terrorism
follows from these forecasts. The snapshot-vintage ablation added lagged REER, HICP, and their joint
block to one-step ridge B0, but all three increased MAE and all absolute- and squared-loss block
bootstrap intervals crossed zero. The lower RMSE point estimates for the added blocks do not
override their lack of MAE value or repair unknown historical extraction vintages. A model using
these retrospectively revised values estimates performance under a snapshot information set, not
necessarily the information available in real time. Future paths also must be forecast,
scenario-specified, or restricted to publication-lagged values; using realized future values would
create a conditional or ex-post exercise.

The legacy search series was excluded because its query construction and normalization cannot be
recovered. The Instagram workbook was excluded because its provenance, structure, geographic
meaning, and time coverage do not support the proposed Türkiye travel-intent measure.

The expanded licensed GTD sensitivity produced a deliberately mixed result. B4 reduced MAE by
5.10%–7.68% across all nine security definitions, and every absolute-loss block-bootstrap interval
was below zero. However, B4 worsened RMSE by 1.63%–3.45%. The high-severity complete-case definition
had the largest MAE skill, but high severity was a prespecified `nkill + nwound >= 10` rule applied
only when both casualty fields were observed.

Association results further limit interpretation. Across nine definitions and lags 0, 1, 2, 3, 6,
and 12, three high-severity coefficients had raw nominal *p* < 0.05, but none survived family-wide
Benjamini–Hochberg adjustment; the minimum adjusted *p* was 0.615394. The forecast result therefore
cannot be converted into a claim that terrorism suppresses tourism at a particular lag, that
incident data have causal effects, or that B4 is universally more accurate.

More fundamentally, the GTD exercise covers only 2008–2020, evaluates 69 forecast outcomes, and
uses a final retrospective workbook without operational issue vintages. The assumed security delay
does not reconstruct what analysts knew at each historical origin. The result is useful as an
aggregate robustness signal that may motivate prospective data collection; it is not deployable
evidence and cannot establish post-2020 forecast value. GTD still cannot be extended beyond
coverage by writing zeros.

The official 2026-Q1 holdout provides a narrow prospective check. Seasonal naive was best among
five locked models, with quarter-total absolute error 136,977 and APE 1.479532%. That observation
is consistent with its fixed-origin historical ranking, but one quarterly total cannot establish a
new general performance distribution. The outcome was not used for tuning, monthly official
actuals were not archived, and neither monthly accuracy nor quarter-level significance can be
inferred.

These exclusions are findings, not empty cells to be filled. They prevent unverifiable inputs from
creating an illusion of richer evidence.

## Practical implications

For annual operational planning, seasonal naive is the appropriate default among the evaluated
models because it had the lowest fixed-origin MAE, is easy to audit, and makes its dependence on
prior seasonal levels explicit. Its prediction intervals were reasonably calibrated but wide,
which signals that point forecasts should be accompanied by uncertainty bands and scenario stress
tests. Organizations should monitor forecast errors by horizon, calendar month, and regime rather
than relying on one aggregate statistic. Seasonal naive's leading 2026-Q1 quarterly result is
encouraging but does not remove that monitoring requirement.

For monthly updating, ridge B0 is a useful challenger rather than a demonstrated replacement. A
practical governance rule is to retain both forecasts, publish their disagreement, and require
prospective evidence before changing the production default. Model selection should use a loss
function tied to the planning decision: MAE favors typical absolute deviations, whereas RMSE places
more weight on large misses. The differing RMSE and MAE rankings in this study show why that choice
must be specified before seeing test results.

## Limitations

The study has six important limitations. First, it analyzes one national monthly aggregate with 216
timestamps, only 213 of which have observed targets. Effective sample size is smaller because of
seasonality and serial dependence. Second, the pandemic created both structural disruption and a
three-month survey gap; no definition-consistent Q2 2020 replacement was found. Third, historical
target issue dates were unavailable, so the three-month release delay is a conservative convention
rather than a reconstructed vintage calendar. Fourth, the supplied component snapshots do not
document every extraction vintage, and confirmatory exogenous-feature value was therefore not
estimated. Fifth, the study has no source-country panel, which limits both statistical power and
the ability to represent heterogeneous travel drivers. Sixth, 2026 evidence consists of one
official quarter total; monthly outcomes and later quarters remain unavailable.

The reported uncertainty procedures also have limited power with 129 evaluable months and major
structural breaks. Failure to reject equal accuracy is not proof that models are identical. It means
the available data do not support a sufficiently precise superiority statement. Similarly, regime
comparisons are descriptive and should not be interpreted as estimated treatment effects.

## Future research

A stronger next study should freeze source vintages before outcomes are observed, archive actual
publication timestamps, and evaluate the already specified pipeline prospectively. A harmonized
source-country panel could increase the number of useful cross-sectional observations, provided the
target definition remains distinct from the national departing-visitor total. Official monthly
arrivals by nationality, carefully versioned Google Trends requests, and Wikimedia pageviews are
candidate covariates only after their semantics, normalization, release timing, and licenses pass
the same data gate.

Security research should next prospectively validate the completed licensed GTD common-sample
sensitivity using archived release vintages or a source with auditable operational timestamps. Any
bridge to a newer security source must validate overlap definitions rather than splice incompatible
series. The economic ablation likewise requires frozen REER and HICP vintages before it can become
an operational test. Future 2026 work should preserve the current no-tuning holdout rule and add
monthly or later-quarter outcomes only as official same-definition releases become available.

## Conclusion

Under a conservative release-aware evaluation, seasonal naive was the strongest fixed-origin
12-month forecaster by MAE. Ridge produced a lower pooled one-step MAE, but the difference was
uncertain and reversed in the recent normalization period. The defensible conclusion is therefore
not that a complex model has solved Türkiye tourism forecasting. It is that honest availability,
strong seasonal benchmarks, recursive evaluation, and regime-aware uncertainty materially change
what the evidence can support. The B1/B2/B5 ablation added no MAE value; the GTD B4 sensitivity
showed a loss-dependent MAE signal on a restricted retrospective sample, not causal or deployable
security evidence. Seasonal naive also had the smallest error on the single official 2026-Q1 total,
which is supportive holdout evidence but not monthly validation or a basis for significance.
