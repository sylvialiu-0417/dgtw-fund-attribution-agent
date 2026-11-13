# Verification and recovery evidence

Run `python evals/run_evals.py` after any financial-logic change. The accepted `evals/baseline.json` records two synthetic quarters, CS contributions 5.10% and 3.40%, 90% coverage of disclosed weight, two excluded stock-quarter rows, and a passed audit. This is a **synthetic numerical fixture**, not a statement about a real fund. `examples/expected-output/` is the shareable report and audit artifact; its manifest hash is path-specific and will differ on another machine.

Observed on 2026-11-13:

| Check | Result |
| --- | --- |
| Unit/integration tests | Eight passed (classification, exact boundaries, nonmonotone breakpoints, missing values, duplicate keys, future-data check, audit tampering, supplement, recovery and hash guards) |
| Fixed baseline | PASS, no numerical regression |
| Interrupted synthetic run | `--stop-after grouped` produced `INTERRUPTED`; `resume` reached `COMPLETE` without recomputing `grouped` (`attempts.grouped = 1`, same checkpoint SHA-256) |
| Changed input after checkpoint | Resume rejected with `Input changed or missing`; requires a new run |
| Tampered grouping checkpoint | Resume rejected with `Checkpoint changed or missing` |
| Unauthorized/incomplete real example | Diagnostic stopped at `validated` with `BLOCKED`, no certified CS report |

Private teaching-workbook diagnostic (aggregates only): 379 holdings over 24 quarters, 879 stock-year rows, 1,375 breakpoint rows and 3,000 group-return rows. There are 103 missing momentum features, one missing B/M, one missing holding return, 57 zero-weight holdings, nine date-formatted stock-return cells, and 379 same-quarter holding/return alignments. The source's raw B/M is not proven comparable to industry-adjusted group breakpoints. These are reasons to request source clarification or authorized backfill, not to announce a fund performance result. Neither source workbook nor private run artifacts are in Git.

**Change-control drill:** baseline metrics and tests are stored in Git. If a proposed change alters CS or coverage without approved methodology, the eval exits nonzero; reject the commit and restore the last accepted version with Git. If the change is intentional, independently review the economics and update `baseline.json` in a separate documented commit. Never alter a previous run's snapshots.

