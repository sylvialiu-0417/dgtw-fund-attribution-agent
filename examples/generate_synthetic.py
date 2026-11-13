"""Generate a small, fully shareable forward-return DGTW example."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "synthetic"
ROOT.mkdir(exist_ok=True)


def table(name, fields, records):
    with (ROOT / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


holdings = []
for holding_date, period, returns in [
    ("2024-12-31", "2025-03", (0.12, 0.03, 0.08)),
    ("2025-03-31", "2025-06", (0.04, 0.11, -0.02)),
]:
    for code, weight, stock_return in zip(("000001", "000002", "000003"), (0.5, 0.4, 0.1), returns):
        holdings.append(dict(holding_date=holding_date, return_period=period, code=code,
                             weight=weight, stock_return=stock_return))
table("holdings", ("holding_date", "return_period", "code", "weight", "stock_return"), holdings)

table("features", ("code", "formation_year", "size", "bm", "mom"), [
    dict(code="000001", formation_year=2024, size=450, bm=0.7, mom=0.35),
    dict(code="000002", formation_year=2024, size=250, bm=0.3, mom=-0.1),
    dict(code="000003", formation_year=2024, size=150, bm=0.5, mom=""),
])

breakpoints = []
for size_group in range(1, 6):
    for bm_group in range(1, 6):
        for mom_group in range(1, 6):
            breakpoints.append(dict(year=2024, size_group=size_group, bm_group=bm_group,
                                    mom_group=mom_group, is_not_bse=1,
                                    size_max=600 - 100 * size_group,
                                    adj_bm_max=1.2 - 0.2 * bm_group,
                                    raw_bm_max=1.2 - 0.2 * bm_group,
                                    mom_max=0.6 - 0.2 * mom_group))
table("breakpoints", ("year", "size_group", "bm_group", "mom_group", "is_not_bse",
                      "size_max", "adj_bm_max", "raw_bm_max", "mom_max"), breakpoints)

benchmark = []
for p in ("2025-03", "2025-06"):
    for s in range(1, 6):
        for b in range(1, 6):
            for m in range(1, 6):
                benchmark.append(dict(return_period=p, size_group=s, bm_group=b, mom_group=m,
                                      benchmark_return=round((0.01 if p == "2025-03" else 0.02) +
                                                             0.001 * s + 0.002 * b + 0.003 * m, 6)))
table("benchmark_returns", ("return_period", "size_group", "bm_group", "mom_group", "benchmark_return"), benchmark)

config = dict(source_authorized=True, metric_definition_confirmed=True, bm_basis="adjusted",
              return_timing="forward", formation_rule="june", breakpoint_is_not_bse=1,
              coverage_threshold=0.8, max_rows=10000, weight_unit="fraction",
              return_unit="fraction", size_unit="CNY")
(ROOT / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(ROOT)

