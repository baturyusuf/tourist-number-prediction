# Forensic manuscript audit: `OzcanGuler-EvrimselHesaplama.docx`

Audit date: 11 August 2026
Source reviewed: `docs/source/OzcanGuler-EvrimselHesaplama.docx`
Source SHA-256: `67fb9c254c94091bcbce64001abad6aea01690dd1e76ef96ac61d75bfc4208a1`
Scope: scientific validity, time-series design, reproducibility, internal consistency, equations, tables, figures, citations, and rendered-document quality. The source DOCX was not modified.

## Overall decision

**Publication gate: fail — major scientific and editorial revision is required before the reported accuracy or substantive interpretations can be relied upon.**

The most consequential problems are:

1. The sample start date, split ratio, and stated 2025 test window cannot all be true.
2. The manuscript does not define whether the 2025 exercise is a fixed-origin 12-step forecast, rolling one-step evaluation, or an ex-post conditional prediction using realized 2025 inputs.
3. Realized future exogenous values and actual target lags may have entered the test forecasts. These are high-risk leakage paths that cannot be resolved without code and prediction-level artifacts.
4. Eight feature/lag configurations appear to be compared and the winner selected on the only reported 12-month test set, with no validation set or rolling-origin evaluation.
5. No seasonal-naive baseline is reported. The project brief reports a preliminary seasonal-naive MAPE of about 3.28%; if independently reproduced, it beats the manuscript's headline SARIMAX (4.01%) and lagged XGBoost (5.46%) results.
6. Pandemic shutdown months are replaced by linear interpolation, which manufactures a smooth counterfactual through an exceptional structural break.
7. SHAP values are treated as causal effects, hypothesis tests, evidence of asymmetry, and proof of a “perfect” leading indicator. None of those conclusions follows from the analysis shown.
8. Figures 8 and 9 are the same embedded PNG, while their captions are reversed relative to the surrounding model descriptions.
9. The method lacks the information needed to reproduce either model or any metric.
10. The literature audit found missing references, citation-year conflicts, one major source-description mismatch, and an official-statistics claim that is not supported as written.

### Evidence labels

- **Verified**: directly established from the DOCX, its OOXML structure, its Word-rendered pages, or the linked primary/publisher source.
- **High-risk; code required**: the manuscript exposes a plausible validity failure but does not provide enough implementation evidence for a definitive finding.
- **Not reproduced**: a concern from the review brief is not present in the current source/render.
- **Source verification required**: a factual or bibliographic claim is not supported by the source located, or the source itself needs further integrity checking.

## Audit evidence and render quality

| Item | Result |
|---|---|
| Render | Exported with Microsoft Word from a byte-identical temporary copy; 17 A4 portrait pages |
| Visual inspection | All 17 pages inspected at original rendered resolution |
| Visual integrity | No clipping, overlap, missing glyphs, or unreadable page was observed |
| Document structure | 208 top-level paragraphs, 2 tables, 9 drawing instances, 8 unique embedded PNG files |
| Equations | 24 `oMathPara` elements and 15 standalone `oMath` elements; notation/content defects remain despite technically renderable math |
| Images | All 9 drawing instances lack alternative text |
| Tables | Neither table marks its first row structurally as a repeating header row |
| Word fields | None: no automatic page numbers, caption numbering, cross-references, or table of contents |
| Revisions/comments | No tracked insertions/deletions/moves and no comments were found |
| Styles | Heading-like text and captions are largely Normal paragraphs with direct formatting; no heading hierarchy or Caption style is used |
| Front matter | No manuscript title on page 1 and no title in core document properties; no page numbers, headers, or footers |

The document is visually legible, but the layout is fragile. Table 1 starts at the bottom of page 11 with its header and one data row, then continues on page 12 without a repeated header. Long runs of blank paragraphs are used around the references rather than robust pagination, producing large unused areas on pages 15 and 17. References are crowded on page 16 while page 17 is only partly filled.

## Required-issue checklist

| Concern from review brief | Finding | Location and evidence |
|---|---|---|
| January 2009 vs January 2008 | **Verified inconsistency** | Abstract and purpose, pp. 1–2: Jan 2009; Methodology and Data Collection, pp. 5 and 9: Jan 2008 |
| 9:1 split vs 12-month 2025 test | **Verified mathematical inconsistency** | Framework, p. 6: Training (90), Testing (10); p. 11: 9:1; p. 11: Jan–Dec 2025 test |
| PyTorch relevance | **Verified method/reporting problem** | p. 11 says the “model architecture” was built with PyTorch 2.6.0, but the reported models are XGBoost and SARIMAX; the actual XGBoost/statsmodels packages and versions are not reported |
| Blank input-variable labels | **Not reproduced** | The current Word render shows populated row labels in both tables, pp. 11–12. A blank cell at the far left of the second header row is a merged-header layout, not missing data |
| Missing R² headers | **Not reproduced** | R2/R² headers are visible for both model blocks in Tables 1 and 2, pp. 11–12. They should nevertheless be typeset consistently as `R²` and defined |
| Missing/malformed equations | **Verified** | p. 7 skips Equation 2, calls the penalty Equation 3, shows literal `\half`, misdescribes γ as L1, and has malformed objective punctuation; p. 8 omits `_s` and the exogenous term from SARIMAX notation |
| Figure numbering/captions | **Verified defects** | Figures 1–9 are sequential, but captions are manual, mixed-language, often scientifically underspecified, and Figures 8/9 are wrong/duplicated |
| XGBoost/SARIMAX prediction captions reversed | **Verified** | p. 14 text describes SARIMAX but Figure 8 caption says XGBoost; p. 15 text describes XGBoost but Figure 9 caption says SARIMAX |
| “Disscussion” | **Verified** | Heading on p. 14: “Disscussion and Conclusion” |
| Incomplete methodology | **Verified** | Missing source series identifiers, data vintages, transformations, alignment, hyperparameters, SARIMAX orders, tuning, seeds, forecasting protocol, diagnostics, and prediction artifacts |
| Future-exogenous leakage | **High-risk; code required** | Contemporaneous “raw” REER/HICP/Google Trends are used for a Jan–Dec 2025 exercise; the text never states how their future values were available at the Dec 2024 forecast origin |
| Target-lag teacher forcing | **High-risk; code required** | p. 7 explicitly adds tourist arrivals at t−1; no recursive/direct/rolling protocol says whether actual 2025 arrivals supplied subsequent 2025 predictions |
| Pandemic interpolation | **Verified method, unresolved impact** | p. 9: Apr–Jun 2020 are filled by time-based linear interpolation; no sensitivity or intervention treatment is reported |
| Seasonal-naive baseline absent | **Verified** | Neither tables nor narrative include a `y[t−12]` benchmark |
| Test-set selection | **Verified design omission; exact implementation requires code** | Eight input combinations and specific lag choices are compared on the only reported 2025 holdout; no validation/nested-selection stage is described |
| SHAP significance/causality | **Verified interpretive overreach** | pp. 13–15 infer “statistically significant” suppression, proof, effects, and drivers solely from SHAP plots |
| “Proves/confirms/perfect leading indicator” | **Verified** | p. 13 says “kusursuz bir öncü gösterge” and “ampirik olarak kanıtlar”; pp. 14–15 repeatedly use full confirmation/proof language |
| Unsupported asymmetry | **Verified** | Claimed in abstract, introduction, literature gap, and conclusion, but no asymmetric specification or test is presented |
| References/DOIs real and supportive | **Mixed** | Most identifiers resolve, but several years conflict, one citation is absent from the reference list, and material claims are misattributed or unsupported; see source audit below |
| Figures/tables referenced | **Mixed** | Figures 1–9 are mentioned in text; Table 1 is explicitly introduced; Table 2 is not explicitly cited or discussed as Table 2 |
| Metrics reproducible | **No** | No code/data snapshot, predictions, exact split rows, parameters, random seed, or metric implementation is supplied |

## 1. Sample period, split, and forecast horizon

### 1.1 Contradictory start date — verified

- Page 1 abstract: **January 2009–December 2025**.
- Page 2 objective and page 5 literature-gap paragraph: **January 2009–December 2025**.
- Page 5 Methodology and page 9 Data Collection: **January 2008–December 2025**.

Those definitions imply different sample sizes before lag losses:

| Claimed period | Inclusive monthly observations | 2025 test observations | Implied train/test share if 2025 is the test |
|---|---:|---:|---:|
| Jan 2008–Dec 2025 | 216 | 12 | 94.44% / 5.56% |
| Jan 2009–Dec 2025 | 204 | 12 | 94.12% / 5.88% |

Neither is a 90%/10% split. A 10% terminal holdout would be about 22 months for the 2008 start or 20 months for the 2009 start. Lag construction can reduce the eligible row count further, so the manuscript must report the exact first/last timestamp and row count **after each transformation and lag**.

Required correction: choose and use one period everywhere; state exact training, validation, and test dates and counts; and distinguish the ratio before and after lag-induced row removal.

### 1.2 Forecasting task is undefined — publication blocker

The phrase “Ocak 2025'ten Aralık 2025'e kadar 12 ay boyunca ... tahmin” on page 11 permits at least three materially different experiments:

1. **Fixed-origin 12-step forecast**: train through Dec 2024 and forecast all 12 months without observing 2025 outcomes.
2. **Rolling one-step forecast**: update the information set each month and forecast the next month.
3. **Ex-post fitted/conditional prediction**: use realized 2025 regressors, and possibly realized lagged targets, to predict 2025.

These are not interchangeable. The manuscript must name the estimand and information set at every forecast origin. Until then, the headline MAPE values cannot be interpreted as genuine deployable forecast accuracy.

### 1.3 The “test” is retrospective

The data were accessed on 17 June 2026 (p. 9), after all 2025 target and exogenous observations were known. A 2025 holdout can still be a valid retrospective evaluation, but only if the training pipeline is frozen at a Dec 2024 information set, future values are not used, and feature/model choices are not made from 2025 results. None of those safeguards is documented.

## 2. Data definition and preprocessing

### 2.1 Target series is not identifiable enough to reproduce

The manuscript says only that monthly “international tourist”/visitor counts came from TÜİK. It does not provide:

- the TÜİK table or series code and a stable download link;
- whether the measure is arrivals, border entries, departing visitors, accommodated guests, or unique persons;
- whether Turkish citizens resident abroad are included;
- “foreign visitor” versus “international visitor” definitions;
- geography/border-gate scope, revisions, units, and seasonal-adjustment status;
- the exact raw values or a checksum.

The target definition matters because the cited TÜİK tourism-income release reports **departing visitors**, whereas a demand model may use border-arrival or accommodation statistics. The manuscript must establish that the modeled series and the economic interpretation refer to the same population.

### 2.2 Pandemic interpolation is scientifically unsafe as the sole treatment — verified

Page 9 replaces April, May, and June 2020 with time-based linear interpolation. These months coincide with border closures and an unprecedented collapse in international mobility. A smooth line between adjacent months can create arrivals that were not observed and can distort:

- seasonal patterns and autoregressive coefficients;
- the t−1 target feature and all later lagged features;
- model tuning and SHAP attributions;
- error estimates around structural breaks.

Required correction: recover the official observations and metadata first. If values are genuinely unavailable rather than zero/suppressed, preserve that distinction; pre-register a defensible treatment; model the intervention/structural break; and report sensitivity analyses for at least (a) official values, (b) missing-window exclusion, and (c) a pandemic/intervention treatment. Do not treat linear interpolation as ground truth.

### 2.3 Google Trends construction is not reproducible

Page 9 lists five query strings but omits every parameter needed to regenerate the series:

- search **term** versus Google **topic**;
- geography, category, search property/type, language, and time zone;
- extraction date and exact requested window;
- weekly-to-monthly aggregation rule;
- whether queries were downloaded jointly or separately and how 0–100 scales were combined;
- repeated-download or anchor-term normalization;
- treatment of partial months, zeros, revisions, and query sampling;
- whether the series was available in real time at each forecast origin.

Google Trends is normalized relative to the query window and can vary across downloads. A frozen raw export, acquisition script, and provenance manifest are necessary.

### 2.4 REER definition and naming conflict

Page 10 provides only “TCMB EVDS,” with no EVDS series code, base, weighting system, frequency, seasonal adjustment, direction of the index, vintage, or release lag. Figure 4 calls it a “foreign exchange rate price index,” while later SHAP text calls the feature `ReelUsd_Lag3`. A real effective exchange-rate index is not the same thing as a real USD bilateral rate. The variable must be named and interpreted consistently.

### 2.5 HICP is internally ambiguous

The manuscript alternates among:

- an HICP **index**;
- monthly **change** in the price level;
- monthly **inflation**;
- a “fluctuation rate.”

Figure 5 includes negative values while its y-axis says “Price index.” A price-level index should not be negative; a monthly rate of change can be. The exact Eurostat series code, COICOP/service scope, geography, unit (`index`, `m/m %`, or `y/y %`), seasonal adjustment, transformation, release lag, and vintage must be provided. The claim that most foreign visitors originate in the Euro Area also needs a cited composition table rather than an unsupported premise.

### 2.6 Undisclosed model features

Figures 6 and 7 introduce `year`, `month`, `Trend_Lag6`, `HICP_Lag3`, and `ReelUsd_Lag3`, but the method never defines how year/month are encoded, how lags were selected, or how missing rows were handled. Treating month as an ordinal 1–12 variable is not cyclic; if that encoding was used, it should be justified or replaced with month indicators/Fourier terms. A numeric year feature can also dominate a short extrapolation without demonstrating a structural economic effect.

## 3. Leakage, selection bias, and validation

### 3.1 Future-exogenous leakage — high risk; inspect code and feature matrix

The “non-lag/raw” configurations include contemporaneous REER, HICP, and Google Trends while the paper calls the output a 2025 forecast. At a Dec 2024 fixed origin, those 2025 values are unknown. If realized 2025 values were supplied, the exercise is an **ex-post conditional forecast**, not an ex-ante forecast.

To resolve this, archive for every test month:

- forecast origin;
- target timestamp;
- each feature timestamp and publication timestamp;
- whether the feature is observed, forecast, scenario-supplied, or unavailable;
- the data vintage actually used.

Valid alternatives are: use only origin-available lags; separately forecast each exogenous variable without test leakage; or present explicitly labeled scenario/conditional forecasts. Report ex-ante and ex-post conditional results separately.

### 3.2 Target-lag teacher forcing — high risk; inspect code and predictions

Page 7 explicitly adds tourist arrivals at t−1 to XGBoost. For a fixed-origin 12-month forecast, actual February–December 2025 lagged arrivals are not known at the Dec 2024 origin. They must be recursively replaced by prior predictions, or the model must be trained as a direct multi-horizon model. If actual 2025 `y[t−1]` values were used, the exercise is rolling one-step evaluation/teacher forcing rather than a 12-step forecast.

Required evidence: per-row design matrices before model fitting; forecast loop; train/test assertions; and prediction files keyed by origin, horizon, and target date.

### 3.3 Test-set model selection — likely and methodologically unprotected

Tables 1 and 2 compare eight input combinations, and the lagged table fixes REER/HICP at 3 months and Google Trends at 6 months. The narrative then chooses the best-performing combination using the same 12-month 2025 period. No training-only validation, nested rolling-origin tuning, or pre-specified lag rationale is reported.

If feature sets or lags were chosen after seeing 2025 errors, 2025 is a validation set, not an untouched test set. A final test must then be held out or the reported uncertainty must account for selection. The recommended design is expanding-window rolling-origin validation inside pre-2025 data for lag/hyperparameter selection, followed by one frozen 2025 evaluation.

### 3.4 The evaluation has only one seasonal cycle

Twelve monthly test points provide little evidence about robustness across years, shocks, or revisions. R² on a single seasonal cycle can be high simply because both actuals and predictions share the annual pattern. Report rolling-origin results across multiple origins and horizons, uncertainty across origins, and errors by month/season and regime.

### 3.5 Missing baseline can reverse the conclusion

The study never compares against:

- seasonal naive: `ŷ[t] = y[t−12]`;
- last-value/random-walk naive;
- drift;
- a simple ETS/SARIMA benchmark selected without future information.

The project brief reports a preliminary seasonal-naive MAPE near **3.28%**. This value was not independently reproducible from the manuscript alone. If reproduced from the canonical data and identical 2025 evaluation window, it is lower than both headline values (SARIMAX 4.01%, lagged XGBoost 5.46%), so claims of high/superior performance would need to be withdrawn or qualified.

### 3.6 Required evaluation upgrade

At minimum, report MAE, RMSE, MAPE, sMAPE, WAPE, MASE, RMSSE, and signed bias against identical origins and horizons. Add prediction intervals with empirical coverage and width. Use a paired forecast-comparison procedure across sufficiently many rolling origins; with only 12 highly seasonal errors, strong significance claims are not credible.

## 4. Model specification and equations

### 4.1 XGBoost equations contain verified errors

On page 7:

- The objective is labeled Equation 1, but no equation number is printed alongside it.
- The next equation is called Equation 3; Equation 2 does not exist.
- The objective includes malformed/doubled punctuation/parentheses around the loss arguments.
- The regularization equation renders a literal `\half` rather than `1/2`.
- The displayed standard term is `γT + (1/2)λΣw²`. Here γ penalizes the number of leaves and λ is an L2 leaf-weight penalty. The text incorrectly calls γ and λ “respectively L1 and L2.” XGBoost's L1 leaf-weight penalty would normally be a separate α term.

A corrected form should be checked against the implementation, for example:

`L^(t) = Σ_i l(y_i, ŷ_i^(t−1) + f_t(x_i)) + Ω(f_t)`

`Ω(f_t) = γT + (1/2)λΣ_j w_j²`

and, only if actually configured, an L1 term such as `αΣ_j |w_j|`.

The manuscript also lacks the canonical XGBoost citation, objective choice, booster, tree count, depth, learning rate, subsampling, column sampling, regularization values, early stopping, search space, selection criterion, and random seed.

### 4.2 SARIMAX section is generic rather than study-specific

Page 8 writes `SARIMAX(p,d,q)(P,D,Q)` but then defines `s`; the seasonal subscript `_s` is missing. More importantly, the notation omits the exogenous regression term despite the “X” being central to the paper.

The manuscript does not disclose:

- selected `(p,d,q) × (P,D,Q)_s` for any table row;
- deterministic terms, seasonal period, trend, and intercept handling;
- exogenous transformations and lag alignment;
- estimation method and optimizer;
- stationarity/invertibility constraints;
- ADF/KPSS results, ACF/PACF evidence, AIC/BIC search results;
- coefficient estimates, standard errors, confidence intervals, or collinearity checks;
- residual ACF, Ljung–Box, heteroskedasticity, normality, and stability diagnostics;
- forecast intervals and how future exogenous values were supplied.

Generic statements that these checks are “usually” performed are not evidence that they were performed here.

### 4.3 PyTorch statement is unexplained and the operative packages are omitted

Page 11 says the architecture was developed with PyTorch 2.6.0. Standard Python implementations would ordinarily use the `xgboost` package for XGBoost and a time-series/econometrics package such as `statsmodels` for SARIMAX. PyTorch is not inherently required for either reported model. The manuscript does not name or version the libraries that must have produced the models.

This is either an irrelevant boilerplate claim or evidence of an undisclosed custom implementation. The code and exact package lockfile are required. If PyTorch was used only for an abandoned model, remove it.

## 5. Tables and metrics

### 5.1 Table labels and R² headers — current render

Contrary to the preliminary concern, both tables visibly contain:

- populated input-variable row labels (`VH`, `VH + VR`, etc.); and
- R2/R² columns for both XGBoost and SARIMAX.

The first cell on the second header tier is blank because “Input Variable” spans the header structure. This is not missing row data. These concerns should be rechecked after any future edit, but they are not defects in the audited version.

Remaining presentation issues include “Reel efective” (misspelling), mixed math/plain formatting, captions in English within a Turkish manuscript, undefined lag notation inside row cells, and no structural repeat-header marking.

### 5.2 Narrative claim that every added variable improves both models is false

Page 11 states that adding each explanatory-variable group produces a noticeable improvement for both models. The tables contradict that claim.

Examples:

- Table 1 SARIMAX baseline `VH`: MAPE 5.09%; adding `VR` gives 5.39% and adding `VR + VG` gives 5.32% — both worse.
- Table 2 XGBoost baseline `VH`: MAPE 10.94%; `VH + VR` gives 12.28%, `VH + VG` 12.23%, `VH + VR + VHI` 11.30%, and `VH + VR + VG` 15.32% — all worse.

The text must report heterogeneous gains/losses rather than universal improvement.

### 5.3 What the tables actually show

- Best Table 1 SARIMAX row: `VH + VG + VHI`, MAPE 4.01%, not the full four-variable row (4.09%).
- Best Table 2 SARIMAX row: full lagged row, MAPE 4.05%; thus lagging does not beat the non-lag SARIMAX minimum of 4.01%.
- Best Table 2 XGBoost row: full lagged row, MAPE 5.46%, compared with the XGBoost historical-only 10.94%.

These are descriptive results on the reported holdout, not proof of general superiority or variable “effectiveness,” especially if the same holdout selected the configuration.

### 5.4 Metrics cannot be recalculated from the manuscript

The document gives aggregate RMSE, MAE, MAPE, and R² only. It gives no monthly actual/predicted table, metric formulas, missing-value rules, units/rounding convention, sample count after lags, or implementation. The plots are not a numeric substitute. XGBoost stochastic controls are absent.

Required reproducibility artifact: one machine-readable file containing `model_id`, `forecast_origin`, `horizon`, `target_date`, `actual`, `prediction`, interval bounds, and all configuration identifiers. A separate script should recompute every table from that file.

## 6. SHAP, significance, causality, and asymmetry

### 6.1 SHAP explains a fitted prediction; it does not establish a causal effect

Pages 13–15 use SHAP output to claim that:

- Google Trends is a “perfect leading indicator” that is empirically proven;
- HICP shocks suppress demand at a “statistically significant” level;
- lagged variables affect actual arrivals after specific planning delays;
- two models provide complete methodological confirmation;
- the results prove asymmetric effects.

Ordinary SHAP values allocate a model prediction relative to a chosen background distribution. They do not, by themselves, provide causal identification, p-values, confidence intervals, Granger-causality evidence, or out-of-sample proof of a stable lead time. Correlated, lagged time-series features further complicate attribution.

The manuscript's own Li et al. citation explicitly states that conventional SHAP is limited in determining direction and statistical significance and introduces an enhanced Shapley-regression method for that purpose. The current manuscript reports no such extension, so its significance language conflicts with its cited methodological rationale.

### 6.2 SARIMAX interpretation needs statistical outputs, not SHAP alone

For a linear SARIMAX specification, the primary evidence should include coefficients, standard errors/confidence intervals, diagnostics, and—where relevant—dynamic multipliers or intervention effects. If SHAP is retained, state:

- explainer class and version;
- background/reference data and whether it is training-only;
- correlation/feature-dependence assumption;
- link/output scale;
- sample count and aggregation;
- handling of autoregressive state and time dependence.

The current plots appear consistent with only the 12 test months, but the sample count is not stated. A beeswarm with roughly one point per month is not a basis for “perfect” or “statistically significant” claims.

### 6.3 Asymmetry is not tested

The paper repeatedly invokes “asymmetric” effects/performance but provides no:

- positive-versus-negative shock decomposition;
- threshold or regime-switching term;
- interaction/partial-response analysis;
- quantile model;
- formal symmetry test or uncertainty interval.

A conventional linear SARIMAX coefficient is symmetric unless the model explicitly separates positive and negative changes or regimes. XGBoost's nonlinearity does not automatically demonstrate asymmetry. The asymmetry claim should be removed or tested with a clearly specified design.

### 6.4 Required language downgrades

Replace causal/proof language with model-bounded statements unless a causal design is added. Examples:

- “kusursuz bir öncü gösterge ... ampirik olarak kanıtlar” → “this fitted model assigned the largest positive attribution to the 6-month-lag Trends feature on the reported test observations.”
- “istatistiksel olarak anlamlı düzeyde baskıladığını doğrulamaktadır” → “higher feature values were associated with negative model attributions; no significance or causal test was conducted.”
- “tam bir metodolojik mutabakat” → “the two fitted explanations produced a similar ranking on this dataset.”
- “matematiksel güvenceyi doğrulamaktadır” → “SARIMAX had lower reported errors than XGBoost in the historical-only configuration.”

## 7. Figures, captions, tables, and document design

| Item | Page | Audit finding |
|---|---:|---|
| Figure 1 | 6 | Legible framework, but “Training (90)”/“Testing (10)” conflicts with the 12-month 2025 holdout; values lack `%` or counts |
| Figure 2 | 9 | No informative title inside plot, y-axis label/units, source, missing-data/interpolation note, or pandemic annotation; scientific notation `1e6` is unexplained |
| Figure 3 | 9 | No query-construction/source note; aggregated Trends measure is not defined |
| Figure 4 | 10 | “Reel Effective” is misspelled in plot title; caption calls REER a generic foreign-exchange price index; base/index direction/source absent |
| Figure 5 | 10–11 | Caption says fluctuation rate while axis says price index; negative values make the underlying unit ambiguous; caption is stranded on the next page |
| Figure 6 | 13 | SHAP methodology/background/sample count absent; year/month features were not defined in Methods |
| Figure 7 | 13–14 | Same SHAP-method omissions; ordinary SHAP is overinterpreted as significance and causal isolation |
| Figure 8 | 14 | Surrounding text says SARIMAX 4.01%, caption says XGBoost |
| Figure 9 | 15 | Surrounding text says lagged XGBoost 5.46%, caption says SARIMAX |
| Figures 8 and 9 | 14–15 | **Same embedded file** (`media/image8.png`, SHA-256 `005fc004cbfb1bfe125ed756b7d83d5e32fa10175a9b9021fc3133af503a6e58`); at least one figure is necessarily wrong, and the generic plot itself does not identify a model |
| Table 1 | 11–12 | Splits after its first data row and does not repeat the header; narrative overstates universal improvement |
| Table 2 | 12 | Not explicitly cited as Table 2 in the prose; lag labels rely on the caption rather than unambiguous row names |

All Figure numbers 1–9 are present and mentioned in the text, but the references are typed manually rather than linked fields. Table 1 is explicitly introduced; Table 2 is not. No figures contain alt text, and no figure/table caption uses Word's Caption style.

Additional editorial defects:

- No manuscript title on page 1; title metadata is blank.
- No page numbers.
- “Disscussion and Conclusion” is misspelled.
- “4.1.Data Collection” lacks a space.
- Headings and captions alternate between English and Turkish without a clear journal language policy.
- `XGBOOST`, `XGBoost`, Google Trend/Trends, REER/`ReelUsd`, HICP index/inflation/rate, and `R2`/`R²` are inconsistent.
- The Introduction promises policy recommendations, but the conclusion supplies future model ideas rather than concrete policy recommendations and contains no limitations subsection.
- No data/code availability, funding, conflict-of-interest, author-contribution, or reproducibility statement is present.

## 8. Reference and factual-claim audit

The checks below verify identifier resolution and whether the located source supports the manuscript's specific use. A real DOI is not sufficient if the cited paper does not say what the manuscript attributes to it.

| Manuscript source/claim | Verification | Finding |
|---|---|---|
| [TÜİK release 54158](https://veriportali.tuik.gov.tr/en/press/54158) | **Supported in part** | Reports that 2025 tourism income rose 6.8% to USD 65,230,749,000. It does not report a tourism value-added share of GDP |
| [TÜİK release 54162](https://veriportali.tuik.gov.tr/en/press/54162) | **Claim mismatch** | Reports 2025 GDP growth of 3.6% and **4.6% growth** in the combined trade, transport, accommodation, and food-services branch. It does not report “tourism contributed 4.66% of GDP” |
| “Tourism contributed 4.66% of GDP” (p. 1) | **Source verification required** | Neither cited TÜİK release states this. It may be an author-calculated tourism-receipts/GDP ratio, which is not the same as tourism value added/contribution. If retained, show formula, denominator, currency conversion, source values, and label it accurately |
| [Presidency/Orient tourism record page](https://www.iletisim.gov.tr/turkce/dis_basinda_turkiye/detay/turkiyenin-turizm-rekoru-2025-sonunda-gelirler-65-milyar-dolara-ulasti-orient) | **Broadly supportive** | Supports the ranking/income narrative, but it is a government press-monitoring item; use the underlying UN Tourism/TÜİK primary source for rankings and definitions |
| `C. Li vd. (2022)` (p. 1) | **Missing reference** | Cited in text but absent from the bibliography. Add the complete source and verify that it supports the operational-decision claim |
| [Ölmez 2025](https://doi.org/10.34232/pjess.1836417) | **Real; construct mismatch** | The paper concerns nominal exchange rate and net tourism income. It is not direct support for an exact TCMB REER feature predicting international arrivals |
| [Hou & Wang](https://doi.org/10.3390/systems14020146) | **Real; year mismatch** | Published in 2026 and does use multi-source VSN–xLSTM plus SHAP. The manuscript cites Hou & Wang (2025) in text but lists 2026 |
| [Zheng et al.](https://doi.org/10.1080/13683500.2025.2554872) | **Supported** | Uses a VMD–MSSA–KELM framework with historical demand, weather, Google/YouTube search data and SHAP; the broad description is supported |
| [Agan Celik et al.](https://doi.org/10.1108/JHTT-08-2025-0686) | **Real; year mismatch** | Bibliography gives 2026 while in-text citations say 2025. Core Istanbul/XGBoost/driver/SHAP description is broadly supported |
| [Li et al.](https://doi.org/10.1080/13683500.2025.2466801) | **Supported but contradicts current inference** | The paper says ordinary SHAP is limited in identifying direction and statistical significance and proposes enhanced Shapley regression. The manuscript nevertheless infers significance from ordinary SHAP |
| [Kardeş & Öngen Bilir](https://doi.org/10.54452/jrb.1395182) | **Supported** | Bibliographic record and comparison of SVR, ridge, and multiple linear regression align with the manuscript |
| [Renhua / IEEE Access](https://doi.org/10.1109/ACCESS.2025.3632219) | **DOI resolves; source integrity review required** | The accessible accepted-version text contains unusual internal inconsistencies, including an old volume header, unrelated datasets/tasks, and percentage claims that do not transparently reconcile with displayed errors. This is not an allegation of misconduct, but the final Version of Record and the exact 15–25% calculation should be verified before relying on it |
| [Ünal](https://izlik.org/JA78AL78NZ) | **Real; year mismatch** | Reference is 2024, while page 4 cites Ünal (2023); the Safranbolu NARX topic is supported |
| [Mahmud et al.](https://doi.org/10.32996/jcsts.2025.7.2.2) | **Real; broad support only** | Supports a general ML-versus-traditional forecasting narrative, not direct evidence about Türkiye's monthly international arrivals |
| [Bozkurt et al.](https://doi.org/10.17123/atad.1087573) | **Supported** | Supports the Türkiye Box–Jenkins/SARIMA literature claim |
| [Erdoğan et al.](https://doi.org/10.31590/ejosat.983323) | **Supported** | Supports the comparison and the reported ANN advantage for German visitors |
| [Ouassou & Taya](https://doi.org/10.3390/forecast4020024) | **Partly overstated** | Reports lower errors for LSTM–AR, but the manuscript's phrase “statistically significant” is not backed by a reported formal forecast-comparison test in that paper |
| [Zhang et al.](https://doi.org/10.3390/su17052210) | **Major source-description mismatch** | The actual paper is a **BiLSTM–Transformer** study implemented in TensorFlow. The publisher page contains no CNN, GRU, Bayesian optimization, or SHAP methodology matching the manuscript's CNN–GRU–Attention/Bayesian/SHAP description |
| [Kurtulay & Kızılırmak](https://doi.org/10.54493/jgttr.1408566) | **Supported at a broad level** | Bibliographic record and general tourism-demand model-comparison claim align |

Reference-list corrections also required:

- Disambiguate the two corporate-author TÜİK 2026 entries as 2026a/2026b in both text and references.
- Reconcile every in-text year with the reference list (Hou & Wang, Agan Celik et al., Ünal).
- Add foundational references for XGBoost, SHAP, SARIMAX/Box–Jenkins or the chosen software implementation, Google Trends methodology, TCMB EVDS, Eurostat HICP, and the exact TÜİK target series.
- Apply one journal reference style consistently; current entries mix APA-like, IEEE-like, raw URLs, `DOI:`, and access-address formats.

## 9. Reproducibility verdict and minimum evidence package

**The reported metrics are not reproducible from the manuscript.** Reproduction requires, at minimum:

1. Immutable raw data files and a provenance manifest with source URLs/series codes, extraction timestamps, vintages, units, licenses, and hashes.
2. A canonical monthly merged panel and a data dictionary.
3. Code for pandemic handling, Google Trends normalization, date alignment, transformations, and lags.
4. Explicit leakage assertions showing that every feature timestamp/publication date precedes its forecast origin.
5. Exact train/validation/test timestamps and row counts for every configuration.
6. Frozen dependency versions, including the actual XGBoost and SARIMAX libraries.
7. Complete model configurations, hyperparameter search spaces, selected values, seeds, and training logs.
8. Forecast-origin/horizon keyed predictions for every model and baseline.
9. A single metrics implementation that regenerates both tables.
10. SARIMAX coefficients/diagnostics/intervals and SHAP explainer/background metadata.

Until these artifacts are available, the numerical results should be labeled **reported, not independently verified**.

## 10. Publication-blocking corrections in recommended order

1. Freeze the target definition, correct the 2008/2009 contradiction, and publish exact data provenance.
2. Define the forecasting task and information set; audit future-exogenous and target-lag leakage from code and matrices.
3. Rebuild evaluation with training-only tuning, expanding-window rolling origins, simple baselines, and uncertainty.
4. Recover or defensibly handle 2020 shutdown observations and run sensitivity analyses.
5. Recompute all predictions/metrics; if seasonal naive remains better, rewrite the contribution around interpretation or conditional scenarios rather than superior accuracy.
6. Replace causal/significance/asymmetry claims with model-bounded language or add appropriate identification and inference.
7. Provide actual XGBoost/SARIMAX specifications, repair equations, and remove/explain PyTorch.
8. Replace Figures 8/9 with distinct, labeled, reproducible plots and correct every caption/source/axis.
9. Repair the citation mismatches, missing `C. Li et al. (2022)` entry, and unsupported 4.66% GDP claim.
10. Add a real title, limitations, data/code availability, policy implications if promised, page numbers, styles, accessible figures, and robust caption/cross-reference fields.

## Verified non-issues and boundaries

- The current document does **not** show blank table input labels.
- The current document does **not** omit the R²/R2 table headers.
- Figure numbering is continuous from 1 through 9.
- The rendered pages have no detected clipping, overlap, or missing glyphs.
- No tracked changes or comments are present.
- Leakage, teacher forcing, exact metric correctness, and the project brief's 3.28% seasonal-naive value require the underlying code/data to settle definitively; they are not claimed as proven solely from this DOCX audit.
