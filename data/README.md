# Data access, placement, and redistribution

The code repository does not redistribute raw datasets or the original manuscript. Place local
inputs at the paths below. The pipeline records SHA-256 checksums so results can be tied to an
exact local copy without publishing its contents.

| Local path | Role | Redistribution |
|---|---|---|
| `data/raw/turizm_kisi_Reel_HICP_Trend.csv` | Core monthly study data | Not established; excluded from Git |
| `docs/source/OzcanGuler-EvrimselHesaplama.docx` | Original manuscript | Private source document; excluded from Git |
| `data/kaggle/trending_hashtags.xlsx` | Candidate Instagram dataset | Subject to source license; excluded from Git |
| `data/kaggle/global_terrorism.xlsx` | Licensed GTD candidate | Prohibited here; excluded from Git |

Generated `data/interim/` and `data/processed/` records are also excluded by default because they
may permit reconstruction of restricted inputs. Aggregated non-sensitive result tables live under
`reports/tables/` and `results/`.

Never place Kaggle credentials, cookies, API tokens, GTD codebooks, or licensed auxiliary files in
the repository. Acquisition and source documentation are maintained in
`docs/data_sources.md` and `docs/external_data_assessment.md`.
