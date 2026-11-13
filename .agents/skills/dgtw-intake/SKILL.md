---
name: dgtw-intake
description: Map unfamiliar fund holdings and benchmark files to the DGTW input contract, flagging finance-method ambiguities before computation.
---

# Intake and source approval

Use when a new local disclosure or source extract arrives. Read `docs/data-contract.md`, inspect only the supplied sheets/headers and sample values, and propose a canonical mapping with units, source rights, date conventions and feature definitions. Do not infer that a field named `bm` is industry-adjusted; do not equate a quarter-end holding with prior-period exposure. Ask the analyst to approve unresolved meanings. Save approved mapping/config outside the private source files, then run the deterministic CLI. Never fetch a paid benchmark or reveal/upload raw data without explicit rights.

