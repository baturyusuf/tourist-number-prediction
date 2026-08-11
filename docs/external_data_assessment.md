# External data suitability assessment

Audit date: **2026-08-11**. No external feature is accepted merely because a file or URL was
supplied. Raw rows and restricted narratives are not reproduced here.

## Decision summary

| Candidate | Decision | Binding reason |
|---|---|---|
| Local `trending_hashtags.xlsx` | **Reject** for the proposed country-specific travel-intent question | One year, triplicated sheets, undefined observation unit, no Türkiye-specific travel tags, unverified `top_country`, provenance mismatch, likely synthetic-generation indicators |
| Global Terrorism Database | **Conditionally accept** for licensed 2008–2020 tourism-overlap association/robustness work | Coverage ends in 2020, extensive structured missing/sentinel values, collection-method changes, and EULA forbids redistribution |
| Supplied legacy `TREND` | **Reject** from confirmatory models | Query/topic, geography, category, search type, request window, normalization, extraction timestamp, and vintage are unknown |
| New country-specific Google Trends panel | **Candidate; not yet accepted** | Relative normalization, topic/term/geography, repeated-download stability, and forecast-origin availability require a reproducible extraction protocol |
| Official monthly arrivals by nationality | **High-priority definition-different panel candidate** | Useful as a source-market covariate or separate target, but not a replacement for departing visitors; historical completeness still requires verification |
| Wikimedia pageviews | **Candidate robustness proxy** | Destination mapping, source-market interpretation, and timing/availability need assessment |
| GTTAC GRID | **Conditional terrorism-specific bridge** | Overlap permits comparison, but definitions, casualty estimation, reporting latency, and redistribution terms differ from GTD |
| ACLED | **Separate political-disorder robustness feature only** | It is not a terrorism continuation and Türkiye coverage has material source-revision breaks |
| UCDP GED/Candidate | **Accept as a separately named security proxy** | CC BY 4.0 and current, but measures organized lethal violence rather than terrorism |

## Instagram/trending-hashtag workbook

### Actual local schema and coverage

- File: `data/kaggle/trending_hashtags.xlsx`; SHA-256
  `d6230b265bd4a058c636a0a2c0b8a7b36343cb96cdb03333440669f96b1c0f5e`.
- Three visible sheets (`trending_hashtags`, `Sayfa1`, `Sayfa2`), each 300,000 data rows plus
  header and six columns: `date`, `hashtag`, `mentions`, `estimated_reach`,
  `sentiment_score`, `top_country`.
- All three sheets contain the same 300,000 rows in the same order. Concatenating them would add
  600,000 exact duplicate copies.
- Coverage is 2024-05-28 through 2025-05-27 (365 dates), only about 12 monthly observations and
  only the end of the 2008–2025 tourism period.
- One row per sheet (date 2024-11-15) lacks all five non-date fields. There are 62 hashtags and 20
  country labels. The proposed `(date, hashtag)` and `(date, hashtag, top_country)` keys are highly
  non-unique, so the unit of observation is undefined.
- Hashtag strings do exist, contrary to the preliminary expectation in the project brief, but the
  only travel-oriented labels are generic `#Travel` and `#TravelTuesday`. No Türkiye, Turkey,
  Antalya, destination-holiday, or localized travel hashtag was found.
- `top_country` has no documented meaning and cannot be assumed to be post country, user country,
  source market, country-specific volume, or rank.

### Provenance and reliability

The user-specified Kaggle page currently describes one `Instagram_Analytics.csv` with 29,999
posts, 23 columns, November 2024–November 2025, and CC BY 4.0. The local workbook instead has
300,000 unique rows, six columns, May 2024–May 2025, plus two exact sheet copies. With no embedded
source/license or transformation record, the page's provenance and license cannot be transferred
to this local workbook. The accessible uploader metadata identifies version 3, updated
2026-01-13, but supplies no source accounts, collection method, official API/export evidence,
sampling frame, consent basis, validation, or real-versus-synthetic disclosure:
https://www.kaggle.com/datasets/kundanbedmutha/instagram-analytics-dataset and
https://www.kaggle.com/api/v1/datasets/view/kundanbedmutha/instagram-analytics-dataset. The
uploader-selected CC BY 4.0 label is not proof of chain of title to platform content.

The following are synthetic-generation indicators, not proof: nearly uniform hashtag/country/date
selection; sentiment discretized to two decimals across `[-1,1]`; mention counts spanning a fixed
range; reach tightly related to mentions through a bounded multiplier; pervasive repetition of
date-hashtag combinations; triplicated sheets; and the same incomplete row on all sheets.

### Forecast suitability and final decision

The file lacks verified source-country semantics, Türkiye-specific travel intent, trend rank,
country-specific historical volume, a defensible observation unit, collection method, time zone,
source URL, extraction timestamp, forecast-origin availability, and adequate multi-year depth.
It is therefore **rejected** for “Do travel hashtags trending in Germany, Russia, or the United
Kingdom predict arrivals in Türkiye?” It will not enter B3/B6/B7. Hashtag identities or geography
will not be manufactured, and no Instagram scraping or personal-data collection will be attempted.
Meta's current terms prohibit automated collection without express written permission and prohibit
unauthorized automated access or bypassing controls:
https://www.facebook.com/legal/automated_data_collection_terms and
https://www.facebook.com/terms.

Meta Content Library/API is a lawful access path for qualified public-interest researchers and
offers public creator/business-account content and engagement measures. It is access-controlled,
has secure-environment/deletion requirements, and is not a country-specific search-intent measure:
https://about.fb.com/news/2023/11/new-tools-to-support-independent-research/ and
https://www.icpsr.umich.edu/sites/somar/meta-content-library.

## Global Terrorism Database

### Actual schema, coverage, and provenance

- File: `data/kaggle/global_terrorism.xlsx`; SHA-256
  `4f372d996ba31365f69a13b15a1e72507c7d8b65faad430e9343b44a538c2b07`.
- One `Data` sheet with 209,706 event rows and 135 columns (A–EE).
- Shape, coverage, schema, and 2022 metadata identify it with near certainty as the renamed START
  `globalterrorismdb_0522dist.xlsx` distribution. This is an inference because the local filename
  and embedded package do not provide an unbroken acquisition chain. The official full download
  ends in 2020; START lists January-June 2021 as a separate partial file, not a complete 2021
  extension: https://www.start.umd.edu/download-global-terrorism-database.
- Event coverage is 1970–2020; incident-level 1993 is absent. There are 20 rows with month `0` and
  891 with day `0` (unknown). Dates must be constructed from explicit `iyear`/`imonth`/`iday`, not
  inferred solely from `eventid`.
- Türkiye/Turkey has 4,485 events overall and 1,777 during the tourism-overlap sample 2008–2020;
  167 Türkiye rows lack at least one coordinate. Primary target codes include 17 Tourist, 38
  Airports/Aircraft, and 152 Transportation events.
- No duplicate `eventid` was found. Globally, latitude/longitude are missing for about 2.24%,
  `nkill` for 12,527 events, and `nwound` for 19,936 events. Many secondary fields exceed 90%
  missingness. Coded values such as `-9` and `-99` mean structured unknown/not-applicable states
  and must be decoded rather than treated as zero or literal counts.

### License and redistribution

The official START terms grant non-commercial research/analysis use under a revocable,
non-exclusive, non-transferable agreement and prohibit public posting/display/distribution of the
raw data, codebook, and auxiliary materials without permission. Commercial use requires another
agreement. The repository may publish code, checksums, acquisition instructions, documented
transformations, and aggregate analyses—not event-level extracts or the codebook. The Kaggle
mirror reports an unknown license and is not treated as licensing authority.

Required citation:

> START (National Consortium for the Study of Terrorism and Responses to Terrorism). (2022).
> Global Terrorism Database, 1970–2020 [data file]. https://www.start.umd.edu/data-tools/GTD

Copyright notice: `Copyright University of Maryland 2022.` Official terms:
https://www.start.umd.edu/gtd-terms. Official FAQ: https://www.start.umd.edu/gtd-faqs. START permits
publication of noncommercial analysis/visualization but does not clearly classify a redistributable
monthly aggregate feature table. The conservative repository rule is therefore not to redistribute
derived GTD data without written permission.

### Methodology discontinuities

GTD was collected concurrently through 1997, retrospectively for 1998-2007, and concurrently again
after 2008. START identifies breaks at 1998-01-01, 2008-04-01, and 2012-01-01; `doubtterr` is
systematically available only after 1997. Failed attacks are included, foiled plots are excluded,
and GTD concerns non-state terrorism reported in open sources. Official guidance:
https://www.start.umd.edu/gtd-faqs and https://www.start.umd.edu/using-gtd.

### Accepted scope and transformation rules

GTD is conditionally accepted only for:

- the 2008–2020 tourism-overlap sample, with methodology-break controls or restrictions;
- robustness comparisons with/without security features;
- lagged historical association analyses; and
- prespecified broad/strict/success/severity/spatial sensitivity variants.

The pipeline skips unknown month `0`, retains missing casualties as unknown (with missingness
counts), reports coordinate-missing sensitivity, uses documented tourism-center coordinates, and
includes April 2008/January 2012 source-method indicators or sample restrictions. Strict/broad
definitions vary `doubtterr`, GTD criteria, success, casualty severity, and spatial thresholds. It
does not fill 2021–2025 with zero, treats the partial 2021 file separately if licensed, and does not
imply uniform collection coverage.

## Post-2020 security alternatives

### GTTAC Global Record of Incident Database

GRID is the closest terrorism-specific bridge. It was created under a US State Department contract
in 2018 and provides an overlap period for comparison with GTD. Its open-source methodology,
casualty rules, and reporting completeness differ from START; GTTAC notes that contemporaneous
reports can take three to six months to stabilize. Portal and methodology:
https://gttac.com/data/ and https://gttac.com/methodology/. Codebook:
https://gttac.com/wp-content/uploads/2023/11/2023_GRID_Codebook_V2.pdf.

GRID's living-database terms require attribution and an access date, prohibit scraping and direct
raw-data access for others, and prohibit creating a substitute/competing database:
https://gttac.com/use-and-citation-policy/. Before use, verify Türkiye completeness, the portal's
actual terminal month, release lag, and permission for the intended derived outputs. Do not splice
GRID counts onto GTD without overlap validation and explicit source/method indicators.

### ACLED

ACLED covers Türkiye from January 2016 to the present but measures political violence,
demonstrations, and disorder rather than terrorism:
https://acleddata.com/methodology/countrytime-period-coverage. Its July 2025 EULA provides a
noncommercial, nontransferable license; externally shared outputs must be transformative and
non-reconstructable, and raw sharing/scraping are prohibited. AI/ML use remains subject to license,
attribution, and access controls: https://acleddata.com/eula.

A March 2025 integration of Turkish sources added nearly 3,000 demonstration events from January
2023 onward—more than 30%—with back-coding planned. This is a material source/revision break:
https://acleddata.com/update-log/data-update-incorporation-data-new-sources-acleds-turkey-dataset.
ACLED may enter only as a separately defined political-disorder robustness feature.

### UCDP GED and Candidate Events

UCDP GED version 26.1 covers individual events through 2025; the Candidate dataset is updated
monthly and, on the audit date, extended through June 2026. UCDP distributes its datasets under
CC BY 4.0, permitting reuse and redistribution with attribution:
https://ucdp.uu.se/downloads/. The API is documented at https://ucdp.uu.se/apidocs/.

UCDP does not classify terrorism. State-based, non-state, and one-sided violence overlap only
partially with terrorist violence:
https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/frequently-asked-questions.
It is the strongest open and reproducible current security proxy, but it is not appended to GTD or
renamed terrorism. Candidate releases must be archived by vintage for release-aware forecasting.

## Digital-intent and source-market alternatives

### Google Trends

The supplied `TREND` column is rejected from confirmatory models because its query/topic,
geography, category, search type, request window, extraction timestamp, anchor, normalization, and
vintage are absent. It may remain only for legacy reproduction.

Google states that Trends uses sampled, anonymized, categorized, aggregated searches. Each value is
divided by total searches for its geography/time and scaled 0-100 to the maximum share within that
request; low volume may appear as zero and statistical noise is added:
https://support.google.com/trends/answer/4365533?hl=en-GB. Terms and topics are different objects:
https://support.google.com/trends/answer/17309543. CSV export and attribution guidance:
https://support.google.com/trends/answer/4365538?hl=en.

A new panel must freeze term/topic IDs, language, country, category, search type, extraction
timestamp/window, anchor/overlap method, and repeated pulls. Independent 0-100 windows cannot be
concatenated naively. A retrospective full-period extraction can be rescaled by later observations
and cannot be treated as the exact values available at historical forecast origins. Full month *t*
is unavailable at the end-of-*t−1* origin.

The official API remains alpha/limited access. It offers consistent scaling across API requests but
only a rolling 1,800-day history and data through approximately two days earlier, so it cannot
rebuild 2008-2025 today: https://developers.google.com/search/apis/trends and
https://developers.google.com/search/blog/2025/07/trends-api. The BigQuery dataset contains only
leading overall/rising searches over a rolling five-year window, not arbitrary keyword histories:
https://support.google.com/trends/answer/12764470?hl=en.

### Google Ads search volume

Keyword Planner/API can generate geographically and linguistically filtered Google Search
historical metrics, but monthly volumes cover approximately the preceding 12 months and are
rounded/approximate. It is suitable only for prospective recent monitoring, with every snapshot
dated and retained—not for a 2008-2025 backfill:
https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics,
https://support.google.com/google-ads/answer/3022575, and
https://support.google.com/google-ads/answer/6325025.

### Wikimedia pageviews

Wikimedia's per-article API begins in July 2015; best-effort dumps extend to December 2007. The
analytics datasets are CC0. Pre-May 2015 data differ in mobile coverage and automated-traffic
filtering. Per-article views are available by language project, not arbitrary article-by-viewer
country; country endpoints provide project-wide/top-page aggregates. A language edition is at most
a weak source-market proxy:
https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html,
https://dumps.wikimedia.org/other/analytics/, and
https://dumps.wikimedia.org/other/pageviews/readme.html.

### GDELT and official nationality panels

GDELT may support a media-attention covariate, not search intent or a validated continuation of a
security-event series. GDELT 2.0 begins in February 2015, and historical-system methodology differs.
Its data page calls the database free/open but is less explicit than a formal downstream license,
so raw article-derived content is not redistributed without further review:
https://www.gdeltproject.org/data.html.

Official nationality-by-month arrivals remain a high-priority source-market panel candidate, but
they must retain their own border-arrival definition and cannot silently replace the TÜİK departing
visitor target.

## Evidence cutoff

The core target ends in December 2025. Although some external sources publish 2026 observations,
they are not 2026 target outcomes and do not create an external-validation sample. No 2026 tourism
forecast accuracy or validation result is claimed or fabricated.
