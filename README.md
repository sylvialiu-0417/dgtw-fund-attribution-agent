# DGTW Fund Attribution Agent

**Student:** 刘思颖 (Liu Siying), 26210660035  
**Course:** AI Coding in Finance, Fall 2026  
**Repository:** https://github.com/sylvialiu-0417/dgtw-fund-attribution-agent

A persistent, auditable workflow for a buy-side fund analyst who repeatedly receives holdings, stock characteristics, CSMAR-style 5×5×5 breakpoints, and characteristic-benchmark returns. It classifies each stock deterministically, computes disclosed-holdings characteristic-adjusted selection (CS), audits coverage and data quality, and produces a **draft** research report. It is not a trading system or a measure of whole-fund alpha.

## What is in this repository

- `docs/design.md`: annotated architecture, finance methodology, control gates, recovery, evaluation, and limitations.
- `docs/agent-prompts.md` and `docs/verification.md`: Codex handoff prompts and observed verification/recovery evidence.
- `docs/data-contract.md`: canonical inputs, units, temporal alignment, and source approvals.
- `src/dgtw_agent/`: input adapters, classification/calculation engine, persistent harness, independent audit, report and CLI.
- `.agents/skills/`: Codex intake, grouping, attribution and audit workflows.
- `examples/`: **synthetic**, shareable inputs and a demonstrative output. No licensed or private data.
- `tests/` and `evals/`: unit/integration tests, fixed regression baseline and interruption-recovery evidence.
- `scripts/package_submission.py`: checks the full Git history for common secret patterns and packages the existing repository, including `.git/`.
- `docs/build-log.md`: development and verification record. Git commits are the authoritative history.

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python examples/generate_synthetic.py
python -m dgtw_agent run --input-dir examples/synthetic --config examples/synthetic/config.json --runs-dir /tmp/dgtw-runs
python -m unittest discover -s tests -v
python evals/run_evals.py
```

The run command prints the run directory containing `state.json`, checkpoint files, a stock-level audit trail, quarterly CS, exceptions, and `report.md`. `--stop-after grouped` intentionally interrupts; `resume --run-dir PATH` continues after verifying input hashes. `python -m dgtw_agent --help` lists all commands.

The shareable fixture has an explicit forward-return convention and documented characteristic definition. Real uploads require a signed-off `config.json`: the provided teaching workbooks **do not by themselves establish** that raw B/M equals the industry-adjusted characteristic used by CSMAR groups, or that reported stock returns follow rather than coincide with the disclosed quarter-end holdings. The workflow therefore blocks certification until those facts are resolved. See `docs/data-contract.md`.

To backfill a source-missing characteristic, add `--supplements-csv PATH` with the provenance fields in `docs/data-contract.md`; this creates a fresh run. The example `examples/synthetic/supplements.csv` raises coverage from 90% to 100%. Missing returns and structural unavailability are never silently imputed.

## AI role and my contribution

Codex is the research assistant: it interprets unfamiliar columns, checks provenance and methodology, triages missing data, reviews exceptions, and writes a constrained narrative using the project skills. The harness controls stage execution and recovery; Python owns all classifications, arithmetic and hard audit checks. I selected the DGTW-CS question from my earlier investment coursework, specified the finance boundaries and acceptance criteria, reviewed the sample input limitations, and developed this auditable workflow with Codex. AI-generated explanations are not accepted as independent numerical evidence.

## Submission

Use the local ZIP named `26210660035-刘思颖-final-project.zip`, produced from the existing folder **including `.git/`** after the final commit. Do not use GitHub “Download ZIP” or `git archive`. The ZIP and full history should be scanned for secrets and private data before LMS upload.

```bash
python scripts/package_submission.py
```

