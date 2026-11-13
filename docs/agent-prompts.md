# Reusable Codex prompts and bounded handoffs

Project skills live in `.agents/skills/` as documented for [project-scoped Codex skills](https://developers.openai.com/api/reference/cli). The deterministic CLI needs no API key or Codex CLI installation. Codex is invoked interactively only for judgment tasks; every numerical decision remains in the engine.

## 1. New disclosure intake

> Use `dgtw-intake`. Inspect only the files I provide, map them to `docs/data-contract.md`, and show the proposed column mapping, units, return interval, B/M definition, source rights and unresolved items. Do not run a certified attribution until I approve those items. Never look up or upload licensed benchmark data without authorization.

**Handoff:** approved config and source paths, or `AWAITING_INPUT` with exact gaps.

## 2. Grouping exception triage

> Use `dgtw-grouping`. Read the current run's `groups.json` and `input.json`; summarize counts and affected disclosed weight by reason and quarter. Identify which missing values can be supplemented from the same authorized definition. Do not infer or fill values. Produce a proposed `supplements.csv` schema for my review, not new numbers.

**Handoff:** reason-coded exceptions or a new, user-supplied supplement file; correction starts a new run.

## 3. Attribution memo

> Use `dgtw-attribution`. Only if `audit.json` passes, write a concise investment-research note from `stock_rows.json` and `quarterly.json`. State coverage, large contributions, data cutoff and limits. Do not call this whole-fund alpha. Cite the run ID and distinguish calculation from inference.

**Handoff:** draft, not externally published. Human analyst approves publication.

## 4. Independent critique

> Use `dgtw-audit` as a separate review pass. Check manifest hashes, timing, exclusions, a sample of benchmark joins and arithmetic, coverage, and every claim in the draft. Do not accept the producer's explanation as proof. Return PASS or FAIL with concrete evidence; at most two revision cycles.

**Handoff:** Critic verdict. Hard programmatic audit failure always overrides prose.

