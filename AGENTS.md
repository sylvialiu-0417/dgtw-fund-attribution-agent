# Project instructions for Codex

- This is a finance research workflow, not a trading system. Never place orders or present disclosed-holdings CS as fund alpha.
- Read `docs/design.md` and the relevant skill before changing financial logic.
- Numerical DGTW classification and CS must be deterministic Python. LLMs may map ambiguous input, investigate exceptions, and draft commentary, but may not invent missing observations.
- Never commit real CSMAR data, fund/client files, credentials, or generated private runs. Use synthetic fixtures in Git.
- A change to financial logic requires tests, the fixed eval suite, and a baseline comparison before acceptance. Reject regressions and document rollback.
- Material methodology ambiguity (formation date, B/M definition, return interval) blocks a certified report; do not silently choose a value.
- Keep a meaningful Git commit per development phase and record observed evidence in `docs/build-log.md`.

