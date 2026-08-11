# GTD aggregate robustness analysis

This licensed-data analysis uses only selected GTD fields in memory and writes no event-level or
monthly derivative. The source workbook SHA-256 is `4f372d996ba31365f69a13b15a1e72507c7d8b65faad430e9343b44a538c2b07`. Outputs are aggregate
definition summaries, model summaries, and aggregate figures; redistribution remains subject to the
GTD end-user license.

Required citation: START (National Consortium for the Study of Terrorism and Responses to Terrorism). (2022). Global Terrorism Database, 1970–2020 [data file]. https://www.start.umd.edu/data-tools/GTD

Copyright University of Maryland 2022.

## Coverage and coding

The common tourism overlap is January 2008 through December 2020; the series is not extended with
zeros after GTD coverage ends. The broad definition contains 1,777 incidents.
Unknown month is excluded, unknown success remains unknown, missing coordinates remain unknown, and
severity is summed only for events with both fatality and injury fields observed. The tables report
the incomplete-severity and missing-coordinate shares. Sensitivities cover `doubtterr == 0`, all
three GTD criteria plus `doubtterr == 0`, successful events, coordinate-known events, complete-case
casualty severity of at least 10 (`fatalities + injuries`), events within 100 km of a prespecified
tourism center, and strict intersections. The severity threshold is a prespecified robustness
definition, not tuned; partial casualty cases remain unknown and are never recoded to zero.
Hotel/resort targets are reported separately from the broader tourism and transport target flag.

The 100-km spatial sensitivity uses Istanbul (41.0082, 28.9784), Antalya (36.8969, 30.7133),
Muğla (37.2153, 28.3636), İzmir (38.4237, 27.1428), and Nevşehir/Cappadocia
(38.6244, 34.7239), with great-circle distance calculated by the haversine formula. These five
manually frozen WGS84 reference points are approximate city centers, not administrative boundaries
or a separately sourced coordinate product. They represent major tourism geographies but are not a
comprehensive map of Türkiye; events near other destinations can therefore be classified as outside
the radius.

## Association analysis

The descriptive regressions relate log monthly visitors to incident counts at prespecified lags of
0, 1, 2, 3, 6, and 12 months, one lag per regression. They include calendar-month indicators, a
linear trend, and GTD method indicators at April 2008 and January 2012. HAC standard errors use 12
lags. Benjamini-Hochberg adjusted p-values cover the full definition-by-lag family. These estimates
are associations, not causal effects; source construction, omitted shocks, simultaneity, and
measurement error preclude causal wording.

## Predictive-value sensitivity

The comparison uses rolling one-step forecasts from 2015 through 2020 on an identical common sample.
Both B0 and B4 use only visitor targets through `t-4`, corresponding to the project-wide assumption
of three completed months of publication delay. B4 also uses a three-month GTD incident sum through
`t-4`. The GTD workbook is a final retrospective snapshot, and no issue-date archive or verified GTD
release calendar was available; the security timing rule is deliberately labeled an assumption,
not a fact. Models are prespecified ridge regressions (`alpha=10`) and block-bootstrap intervals use
12-month blocks. No observation-level forecasts are written.

The largest point-estimate B4 MAE skill is 7.7% for
`high_severity_complete_case_ge10`; its block-bootstrap interval for B4 minus B0 absolute loss is
[-181,387, -37,129].
The MAE evidence is consistent across definitions: every block-bootstrap interval is below zero. RMSE worsens for every definition. The final retrospective GTD snapshot has no issue-date archive;
these sensitivities therefore do not establish an operational forecasting gain.

## Artifact boundary

- `gtd_definition_sensitivity_summary.csv`: aggregate coding and missingness sensitivity.
- `gtd_association_sensitivity.csv`: aggregate HAC coefficients only.
- `gtd_predictive_common_sample.csv`: aggregate common-sample error metrics only.
- `gtd_annual_security_sensitivity.(png|svg)`: annual broad/strict counts and coordinate coverage.
- `gtd_lag_association_sensitivity.(png|svg)`: aggregate lag-response estimates and 95% CIs.

No GTD event row, identifier, narrative, actor, source citation, codebook, or monthly derivative is
included in the repository.
