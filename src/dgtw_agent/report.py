"""Restricted research memo from audited numbers only."""


def render(calculation, verdict, manifest):
    lines = ["# DGTW-CS holdings research note (draft)", "",
             "**Scope:** disclosed stock holdings only; this is neither whole-fund alpha nor a trading signal.",
             "**Status:** " + ("AUDIT PASSED — human publication approval still required" if verdict["passed"] else "BLOCKED — not for publication"),
             "", "## Quarterly characteristic-adjusted selection", "",
             "| Return quarter | Disclosed weight | Covered weight | Coverage of disclosed | CS contribution |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for q in calculation["quarterly"]:
        lines.append(f"| {q['return_period']} | {q['disclosed_weight']:.2%} | {q['covered_weight']:.2%} | {q['coverage_of_disclosed']:.2%} | {q['cs']:.4%} |")
    lines += ["", "CS is the sum of disclosed holding weights × (stock forward return − matched characteristic-group return). Uncovered holdings are not renormalized.", "",
              "## Quality and limitations", "",
              f"- Excluded holding-period observations: {verdict['excluded_rows']}.",
              f"- Minimum coverage of disclosed weight: {verdict['minimum_coverage']:.2%}."]
    for warning in verdict["warnings"]:
        lines.append(f"- {warning}")
    for error in verdict["errors"]:
        lines.append(f"- **BLOCKER:** {error}")
    lines += ["- Inputs are local and source-authorized as asserted in config; no external source was fetched by this run.",
              "- Characteristic definitions, formation timing and returns must match the stated config. Missing values are not zero-imputed.",
              "- A human analyst must review source rights, finance interpretation and publication.", "",
              "## Audit trail", "",
              f"- Input manifest SHA-256: `{manifest['manifest_sha256']}`",
              "- See `stock_rows.json`, `quarterly.json`, `exceptions.json`, and `audit.json` in this run directory.", ""]
    return "\n".join(lines)

