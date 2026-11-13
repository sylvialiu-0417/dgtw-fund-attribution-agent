# Observed development log

- Phase 1: scoped a DGTW-CS research workflow, separate from trading and whole-fund alpha; defined source, timing and privacy gates.
- Phase 2 (`4e2c137`): implemented read-only Excel/canonical CSV adapters, deterministic hierarchical classification, and synthetic source data.
- Phase 3 (`eeb8763`): added atomic checkpoints, input hash guard, resume, independent arithmetic audit, report generation, and four project-scoped Codex skills.
- Phase 4 (`51f389a`): added optional provenance-checked source supplementation, exact-boundary and recovery tests, fixed eval baseline and shareable report. The first test run found floating-point boundary and expected-group mistakes; both were corrected before acceptance.
- Phase 5: private diagnostic of the uploaded teaching workbooks blocked certification, identifying same-quarter holding/return alignment, unclear B/M definition, 57 zero-weight rows and nine Excel date-formatted return cells in addition to the stated missing features. No real source data was committed. See `docs/verification.md` for aggregate evidence.

