# DGTW-CS holdings research note (draft)

**Scope:** disclosed stock holdings only; this is neither whole-fund alpha nor a trading signal.
**Status:** AUDIT PASSED — human publication approval still required

## Quarterly characteristic-adjusted selection

| Return quarter | Disclosed weight | Covered weight | Coverage of disclosed | CS contribution |
| --- | ---: | ---: | ---: | ---: |
| 2025-03 | 100.00% | 90.00% | 90.00% | 5.1000% |
| 2025-06 | 100.00% | 90.00% | 90.00% | 3.4000% |

CS is the sum of disclosed holding weights × (stock forward return − matched characteristic-group return). Uncovered holdings are not renormalized.

## Quality and limitations

- Excluded holding-period observations: 2.
- Minimum coverage of disclosed weight: 90.00%.
- 2 holding-period rows excluded; consult exceptions.json
- Inputs are local and source-authorized as asserted in config; no external source was fetched by this run.
- Characteristic definitions, formation timing and returns must match the stated config. Missing values are not zero-imputed.
- A human analyst must review source rights, finance interpretation and publication.

## Audit trail

- Input manifest SHA-256: `700c65f49d935654ddf0b64f713fa6020939ac4d68701ba4aeebef00c4f00d1d`
- See `stock_rows.json`, `quarterly.json`, `exceptions.json`, and `audit.json` in this run directory.
