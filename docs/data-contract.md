# Input contract and real-data gate

## Canonical CSV bundle

Place four UTF-8 files and `config.json` in one input directory. The CLI also accepts two Excel workbooks with equivalent sheets; it maps known bilingual aliases and stops if a required table/column is ambiguous.

| Table | Required fields | Key |
| --- | --- | --- |
| `holdings.csv` | `holding_date,return_period,code,weight,stock_return` | `return_period,code` |
| `features.csv` | `code,formation_year,size,bm,mom` | `code,formation_year` |
| `breakpoints.csv` | `year,size_group,bm_group,mom_group,is_not_bse,size_max,adj_bm_max,raw_bm_max,mom_max` | `year,groups,is_not_bse` |
| `benchmark_returns.csv` | `return_period,size_group,bm_group,mom_group,benchmark_return` | `return_period,groups` |

`code` is a six-character string retaining leading zeroes. Dates use ISO `YYYY-MM-DD`; return periods use quarter-end `YYYY-MM`. Weights and returns are fractions, not percentages. Size is CNY market capitalization, B/M and momentum are ratios. The example generator documents every synthetic value. A live config must explicitly approve source rights, units, B/M basis and timing. The reporting threshold is a floor for **disclosed-weight coverage**; it does not convert partial holdings into a complete fund performance measure.

## CSMAR teaching workbooks: unresolved fields

The user-supplied workbook contains 379 holdings, 879 stock-year feature rows, 24 × 125 group-period returns and 2018–2024 breakpoints. The feature table has 103 missing momentum values and one missing B/M; one holding return is `#N/A`. These are source-table counts, not the affected holdings count. Source backfills must be same security, formation year, definition and currency; they create a new immutable run. If the metric is structurally unavailable, classify it as `UNCLASSIFIABLE` and disclose its weight.

The breakpoint table contains both `AdjbtmMax` and `BtmMax`; the provided stock-feature header says only `账面市值比`. It does **not** prove the feature is industry-adjusted. Raw-B/M maxima are non-monotone in 8 of 35 year–size slices in the uploaded file, another reason not to assume they are valid group cutoffs. The original DGTW benchmark construction describes industry-adjusted B/M; CSMAR's own data dictionary and source fields must be checked before publishing an attribution conclusion. The holding date and stock return appear to share a quarter; a quarter-end disclosure cannot establish the return earned after that date. The source return interval or lagged holdings must be supplied. Until both are resolved, run only an input diagnostic, not a certified CS report.

## Required config keys

`source_authorized`, `metric_definition_confirmed`, `bm_basis` (`adjusted` or `raw`), `return_timing` (`forward` only for certification), `formation_rule` (`june`), `breakpoint_is_not_bse` (0 or 1), `coverage_threshold` (0–1), `max_rows`, `weight_unit`, `return_unit`, and `size_unit`.

