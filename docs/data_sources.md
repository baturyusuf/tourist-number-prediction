# Data sources and provenance register

Access date for the supplied local files and all official web sources cited below:
**2026-08-11**. A checksum identifies the exact local artifact; it does not establish authenticity,
provenance, or redistribution permission.

| Original filename | SHA-256 | Rows × columns / size | Coverage | Unit of observation | Source/license status | Redistribute? |
|---|---|---|---|---|---|---|
| `turizm_kisi_Reel_HICP_Trend.csv` | `a7885fb0e1ed5de7d64ae180733effc0baebad1e4842ef6bca467466b5b538e5` | 216 × 5; 6,824 bytes | 2008-01–2025-12; Türkiye national series | Month | User-supplied composite; target/REER/HICP definitions verified, but extraction vintages and `TREND` provenance remain unknown | No, as a composite, until every component's redistribution basis is verified |
| `OzcanGuler-EvrimselHesaplama.docx` | `67fb9c254c94091bcbce64001abad6aea01690dd1e76ef96ac61d75bfc4208a1` | 1,754,751 bytes | Study manuscript | Document | User-supplied private source | No |
| `trending_hashtags.xlsx` | `d6230b265bd4a058c636a0a2c0b8a7b36343cb96cdb03333440669f96b1c0f5e` | 3 × 300,000 rows × 6 columns; 39,685,918 bytes | 2024-05-28–2025-05-27; 20 unverified country labels | Undefined workbook row; all three sheets duplicate | Local provenance mismatches supplied Kaggle page; rejected | No |
| `global_terrorism.xlsx` | `4f372d996ba31365f69a13b15a1e72507c7d8b65faad430e9343b44a538c2b07` | 209,706 events × 135 columns; 104,455,519 bytes | 1970–2020, 204 countries/12 regions; 1993 absent | Terrorism event | Near-certain START 2022 GTD distribution; official EULA controls use | No |

## Transformation history

The raw files are immutable inputs. `src/tourism_forecasting/data.py` normalizes field names in
memory, strictly parses dates, constructs explicit target variants, and records audit metadata.
The primary target retains the three months lacking TÜİK Q2 survey estimates. The legacy
interpolated target is named and used only in reproduction/sensitivity work. Generated result
tables contain model outputs and aggregate metadata, not licensed GTD events.

For confirmatory operational backtests, the target is conservatively treated as available only
after three complete calendar months have elapsed after its reference month. Thus, at the
end-of-*t−1* origin for forecast month *t*, target history ends at *t−4*. This assumption is used
because the supplied retrospective snapshot has no historical issue-date archive; it is not an
assertion that every historical release followed exactly that lag. Zero-delay use is separately
labeled observation-availability sensitivity.

## Verified component identities

### Departing visitors target

The values match TÜİK's Departing Visitor Survey monthly total: foreign visitors plus Turkish
citizens resident abroad, including overnight and same-day visitors. It is not unique tourists,
foreign-only arrivals, hotel guests, or Ministry border entries. TÜİK's 2020 release explicitly
contains Q1, Q3, and Q4 but no Q2 survey estimate, so April-June remain structurally missing:
https://veriportali.tuik.gov.tr/en/press/37438. Ministry Q2 border-entry counts are a different
series and are not replacements. TÜİK has revised tourism statistics back to 2012; the supplied
snapshot's exact vintage is unknown and is preserved by hash. Current revision context:
https://veriportali.tuik.gov.tr/tr/press/58142. Official revision document:
https://veriportali.tuik.gov.tr/api/tr/data/downloads?p=12H3agc4gbYAQ4WuPHEEB9VRxgAeI1IvilC3TC8H6jOujJgFx5zix7GM4YGA2lkmbkIeyNI25a0xgygUQ24SDz0l3%2Fd13gDON5L9J5DPNzerSEnembSDivDXZk68X6Elt9k5tCzolBv7b8ciWecNng%3D%3D&t=r.
The Ministry's April-June 2020 border-entry values are documented only as a distinct sensitivity
series: https://yigm.ktb.gov.tr/Eklenti/81939%2C3103turizmistatistikleri2020-4pdf.pdf. TÜİK permits
reuse of its website, publication, and database data with attribution:
https://www.tuik.gov.tr/Kurumsal/Yasal_Uyari.

### Real effective exchange rate

`USD` is the TCMB CPI-based real effective exchange-rate developed-country subindex, currently
2025=100, monthly and non-seasonally adjusted—not nominal USD/TRY. A rise denotes real appreciation
of the lira and a relative increase in Turkish prices. Official table:
https://tcmb.gov.tr/wps/wcm/connect/23c10aa7-4937-400d-9770-31a81b960907/CPI.pdf?CACHEID=ROOTWORKSPACE-23c10aa7-4937-400d-9770-31a81b960907-oMVLvJL&MOD=AJPERES.
The public category is https://evds3.tcmb.gov.tr/tumSeriler/2504/bie_rktufey. The index was rebased
in February 2026 and historical partner/input revisions occur, so one official vintage must be
re-fetched as a whole; the supplied snapshot is not patched. Exact EVDS item code/vintage remains
open. TCMB metadata:
https://www.tcmb.gov.tr/wps/wcm/connect/65b5812f-f1cd-4cb9-8ca6-a978c77f74f4/REERMetadata_2026.pdf?CACHEID=ROOTWORKSPACE-65b5812f-f1cd-4cb9-8ca6-a978c77f74f4-pMEqFZu&MOD=AJPERES.
Methodological/rebasing changes are documented at
https://www.tcmb.gov.tr/wps/wcm/connect/1b2d355e-ac1e-43ac-ac22-57e94e5b5398/REER_MethodologicalChanges2025.pdf?CACHEID=ROOTWORKSPACE-1b2d355e-ac1e-43ac-ac22-57e94e5b5398-pjgKnyR&MOD=AJPERES.
EVDS permits third-party use/publication with attribution, subject to its current terms and
commercial-product provisions:
https://evds3.tcmb.gov.tr/igmevdsms-dis/documents/showDocument?docId=18.

### Euro-area airfare inflation

`HICP` exactly matches archived Eurostat dataset `prc_hicp_manr`, unit `RCH_A` (annual percentage
change), COICOP `CP0733` (passenger transport by air), geography `EA` (changing-composition euro
area), monthly. Exact API query:
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?lang=en&geo=EA&unit=RCH_A&coicop=CP0733.
From January 2026, the corresponding current source is `prc_hicp_minr` with COICOP 2018. This is a
limited euro-area air-travel-cost proxy, not an HICP index or broad inflation measure, and receives
at least a one-month publication lag. Current-series query:
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?lang=en&geo=EA&unit=RCH_A&coicop18=CP0733.
Archived and current observations must be compared and then fetched as one documented vintage,
not spliced opportunistically. Eurostat states that detailed HICP breakdowns are normally released
around the middle of the following month and may be revised:
https://ec.europa.eu/eurostat/web/hicp/information-data.
Eurostat permits commercial and noncommercial reuse with attribution and disclosure of
modifications, subject to identified third-party exceptions:
https://ec.europa.eu/eurostat/help/copyright-notice.

### Legacy search interest

The `TREND` query/topic, geography, category, search type, request window, extraction timestamp,
anchor, normalization, and vintage are absent. It remains available only for legacy reproduction
and is rejected from confirmatory feature blocks unless provenance is recovered. Google Trends
normalizes each request relative to its own geography/time maximum and may sample/add noise, so a
retrospective full-period extraction cannot be treated as the values archived at earlier forecast
origins. Official FAQ: https://support.google.com/trends/answer/4365533?hl=en-GB.
Terms and topics are different query objects:
https://support.google.com/trends/answer/17309543. CSV export/citation guidance is at
https://support.google.com/trends/answer/4365538?hl=en. The official API remains alpha/limited
access and exposes only a rolling 1,800-day history, so it cannot reconstruct a consistent
2008-2025 origin-vintage panel today: https://developers.google.com/search/apis/trends and
https://developers.google.com/search/blog/2025/07/trends-api.

## Restricted or rejected external inputs

The Kaggle page supplied for the Instagram candidate declares CC BY 4.0 for a 29,999-row,
23-column dataset updated in January 2026:
https://www.kaggle.com/datasets/kundanbedmutha/instagram-analytics-dataset and
https://www.kaggle.com/api/v1/datasets/view/kundanbedmutha/instagram-analytics-dataset. It does not
match the local six-column workbook, and an uploader-selected license neither transfers to that
different file nor proves rights in underlying platform content. Meta prohibits automated data
collection without express written permission and prohibits unauthorized automated access:
https://www.facebook.com/legal/automated_data_collection_terms and
https://www.facebook.com/terms. The local workbook is rejected and is not redistributed.

The local terrorism workbook is treated as the START GTD 1970-2020 distribution only with
near-certain schema-based identification; its acquisition filename/vintage chain remains
incomplete. START's EULA limits use to noncommercial research/analysis, prohibits scraping and raw
redistribution, and requires citation: https://www.start.umd.edu/gtd-terms. The full official file
ends in 2020, with January-June 2021 offered separately:
https://www.start.umd.edu/download-global-terrorism-database. Raw events, codebook, and auxiliary
materials remain outside Git.
