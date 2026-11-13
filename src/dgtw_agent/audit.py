"""Independent hard checks: no narrative can override a failed verdict."""

from collections import defaultdict
from math import isclose

from .engine import group_holdings


def audit(data, grouped, calculation, config):
    errors = []
    warnings = []
    expected_groups = group_holdings(data, config)
    if len(expected_groups) != len(grouped):
        errors.append("Grouping row count changed")
    else:
        for expected, actual in zip(expected_groups, grouped):
            for key in ("code", "return_period", "formation_year", "status", "reason",
                        "size_group", "bm_group", "mom_group"):
                if expected.get(key) != actual.get(key):
                    errors.append(f"Grouping mismatch for {expected['code']} {expected['return_period']}: {key}")
                    break
    benchmark = {(r["return_period"], r["size_group"], r["bm_group"], r["mom_group"]): r["benchmark_return"]
                 for r in data["benchmark_returns"]}
    sums = defaultdict(lambda: {"weight": 0.0, "covered": 0.0, "cs": 0.0})
    for row in calculation["stock_rows"]:
        period = row["return_period"]
        sums[period]["weight"] += row["weight"]
        if row["status"] == "CLASSIFIED":
            key = (period, row["size_group"], row["bm_group"], row["mom_group"])
            expected_return = benchmark.get(key)
            if expected_return is None or row.get("stock_return") is None:
                errors.append(f"Classified row has missing return: {period} {row['code']}")
                continue
            expected_contribution = row["weight"] * (row["stock_return"] - expected_return)
            if not isclose(row.get("benchmark_return", float("nan")), expected_return, abs_tol=1e-12):
                errors.append(f"Wrong benchmark: {period} {row['code']}")
            if not isclose(row.get("contribution", float("nan")), expected_contribution, abs_tol=1e-12):
                errors.append(f"Wrong contribution: {period} {row['code']}")
            sums[period]["covered"] += row["weight"]
            sums[period]["cs"] += expected_contribution
        elif not row.get("reason"):
            errors.append(f"Excluded row lacks reason: {period} {row['code']}")
    qmap = {q["return_period"]: q for q in calculation["quarterly"]}
    if set(qmap) != set(sums):
        errors.append("Quarter list does not match stock rows")
    for period, expected in sums.items():
        actual = qmap.get(period)
        if not actual:
            continue
        for key, report_key in (("weight", "disclosed_weight"), ("covered", "covered_weight"), ("cs", "cs")):
            if not isclose(expected[key], actual[report_key], abs_tol=1e-12):
                errors.append(f"Quarter reconciliation failed: {period} {report_key}")
        coverage = expected["covered"] / expected["weight"]
        if not isclose(coverage, actual["coverage_of_disclosed"], abs_tol=1e-12):
            errors.append(f"Coverage mismatch: {period}")
        if coverage < float(config["coverage_threshold"]):
            errors.append(f"Below coverage floor: {period} {coverage:.1%}")
        if expected["weight"] < 0.999:
            warnings.append(f"Partial disclosed portfolio in {period}: {expected['weight']:.1%} of fund weight")
    exceptions = [r for r in calculation["stock_rows"] if r["status"] != "CLASSIFIED"]
    if exceptions:
        warnings.append(f"{len(exceptions)} holding-period rows excluded; consult exceptions.json")
    return {"passed": not errors, "errors": sorted(set(errors)), "warnings": sorted(set(warnings)),
            "excluded_rows": len(exceptions), "quarters": len(qmap),
            "minimum_coverage": min((q["coverage_of_disclosed"] for q in qmap.values()), default=0)}

