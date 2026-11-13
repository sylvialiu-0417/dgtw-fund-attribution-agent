"""Deterministic validation, hierarchical grouping and CS arithmetic."""

from collections import defaultdict
from datetime import date, datetime
from math import isclose, isfinite


class DataError(ValueError):
    pass


def code(value):
    if value is None:
        raise DataError("Missing security code")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    if not text.isdigit() or len(text) > 6:
        raise DataError(f"Invalid six-digit security code: {text!r}")
    return text.zfill(6)


def number(value, label, allow_missing=False):
    if value in (None, "", "#N/A", "#VALUE!", "#DIV/0!"):
        if allow_missing:
            return None
        raise DataError(f"Missing {label}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataError(f"Invalid {label}: {value!r}") from exc
    if not isfinite(result):
        raise DataError(f"Nonfinite {label}")
    return result


def integer(value, label):
    result = number(value, label)
    if not result.is_integer():
        raise DataError(f"Noninteger {label}: {value}")
    return int(result)


def period(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")
    text = str(value).strip()[:7]
    try:
        year, month = map(int, text.split("-"))
        if month not in (3, 6, 9, 12):
            raise ValueError
        return f"{year:04d}-{month:02d}"
    except (TypeError, ValueError) as exc:
        raise DataError(f"Expected quarter-end YYYY-MM, got {value!r}") from exc


def holding_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value).strip()[:10]).isoformat()
    except ValueError as exc:
        raise DataError(f"Invalid holding_date: {value!r}") from exc


def formation_year(return_period):
    year, month = map(int, return_period.split("-"))
    return year if month >= 7 else year - 1


def quarter_start(return_period):
    year, month = map(int, return_period.split("-"))
    return date(year, month - 2, 1)


def validate(raw, config):
    required = ("source_authorized", "metric_definition_confirmed", "bm_basis", "return_timing", "formation_rule", "breakpoint_is_not_bse", "coverage_threshold", "max_rows", "weight_unit", "return_unit", "size_unit")
    missing_config = [key for key in required if key not in config]
    if missing_config:
        raise DataError(f"Missing config keys: {', '.join(missing_config)}")
    if config["bm_basis"] not in ("adjusted", "raw"):
        raise DataError("bm_basis must be adjusted or raw")
    if config["breakpoint_is_not_bse"] not in (0, 1):
        raise DataError("breakpoint_is_not_bse must be 0 or 1")
    if not 0 <= float(config["coverage_threshold"]) <= 1:
        raise DataError("coverage_threshold outside 0..1")
    if sum(len(rows) for rows in raw.values()) > int(config["max_rows"]):
        raise DataError("Input exceeds max_rows")
    issues = []
    for key, message in (("source_authorized", "Source rights not approved"), ("metric_definition_confirmed", "B/M and momentum definitions not confirmed")):
        if config[key] is not True:
            issues.append(message)
    if config["return_timing"] != "forward":
        issues.append("Return timing not confirmed as forward from holdings")
    if config["formation_rule"] != "june":
        issues.append("Only annual June formation rule is implemented")
    if (config["weight_unit"], config["return_unit"], config["size_unit"]) != ("fraction", "fraction", "CNY"):
        issues.append("Input units must be fraction/fraction/CNY; convert before run")

    holdings = []
    seen = set()
    for row in raw["holdings"]:
        p = period(row["return_period"])
        d = holding_date(row["holding_date"])
        c = code(row["code"])
        key = (p, c)
        if key in seen:
            raise DataError(f"Duplicate holding key {key}")
        seen.add(key)
        w = number(row["weight"], "weight")
        if not 0 < w <= 1:
            raise DataError(f"Invalid weight for {key}: {w}")
        if date.fromisoformat(d) >= quarter_start(p):
            issues.append(f"Holding {c} dated {d} is not prior to return quarter {p}")
        holdings.append({"holding_date": d, "return_period": p, "code": c, "weight": w,
                         "stock_return": number(row["stock_return"], "stock_return", allow_missing=True)})

    features = []
    seen = set()
    for row in raw["features"]:
        c = code(row["code"])
        y = integer(row["formation_year"], "formation_year")
        if (c, y) in seen:
            raise DataError(f"Duplicate feature key {(c, y)}")
        seen.add((c, y))
        features.append({"code": c, "formation_year": y,
                         "size": number(row["size"], "size", allow_missing=True),
                         "bm": number(row["bm"], "bm", allow_missing=True),
                         "mom": number(row["mom"], "mom", allow_missing=True)})

    breakpoints = []
    seen = set()
    for row in raw["breakpoints"]:
        r = {key: integer(row[key], key) for key in ("year", "size_group", "bm_group", "mom_group", "is_not_bse")}
        if any(r[g] not in range(1, 6) for g in ("size_group", "bm_group", "mom_group")):
            raise DataError("Group ID outside 1..5")
        key = tuple(r[k] for k in ("year", "size_group", "bm_group", "mom_group", "is_not_bse"))
        if key in seen:
            raise DataError(f"Duplicate breakpoint key {key}")
        seen.add(key)
        for name in ("size_max", "adj_bm_max", "raw_bm_max", "mom_max"):
            r[name] = number(row[name], name, allow_missing=True)
        breakpoints.append(r)

    benchmarks = []
    seen = set()
    for row in raw["benchmark_returns"]:
        r = {"return_period": period(row["return_period"])}
        for name in ("size_group", "bm_group", "mom_group"):
            r[name] = integer(row[name], name)
        key = tuple(r[k] for k in ("return_period", "size_group", "bm_group", "mom_group"))
        if key in seen:
            raise DataError(f"Duplicate benchmark key {key}")
        seen.add(key)
        r["benchmark_return"] = number(row["benchmark_return"], "benchmark_return", allow_missing=True)
        benchmarks.append(r)

    totals = defaultdict(float)
    for row in holdings:
        totals[row["return_period"]] += row["weight"]
    for p, total in totals.items():
        if total > 1.000001:
            issues.append(f"Disclosed weight exceeds 100% in {p}: {total:.6f}")
    return {"holdings": holdings, "features": features, "breakpoints": breakpoints,
            "benchmark_returns": benchmarks, "issues": sorted(set(issues)),
            "source_missing": {"feature_mom": sum(r["mom"] is None for r in features),
                               "feature_bm": sum(r["bm"] is None for r in features),
                               "holding_return": sum(r["stock_return"] is None for r in holdings)}}


def _choose_group(value, rows, group_key, bound_key):
    bounds = {}
    for group in range(1, 6):
        values = [row[bound_key] for row in rows if row[group_key] == group and row[bound_key] is not None]
        if not values:
            return None, None, "MISSING_BREAKPOINT"
        bounds[group] = max(values)
    ordered = [bounds[g] for g in (5, 4, 3, 2, 1)]
    if ordered != sorted(ordered) or len(set(ordered)) != 5:
        return None, bounds, "NON_MONOTONE_BREAKPOINT"
    for group in (5, 4, 3, 2, 1):
        if value <= bounds[group] or isclose(value, bounds[group], rel_tol=1e-14, abs_tol=1e-14):
            return group, bounds, None
    return None, bounds, "ABOVE_BREAKPOINT_RANGE"


def classify_one(feature, year_rows, bm_basis):
    for name in ("size", "bm", "mom"):
        if feature[name] is None:
            return {"status": "UNCLASSIFIABLE", "reason": f"MISSING_{name.upper()}"}
    if not year_rows:
        return {"status": "UNCLASSIFIABLE", "reason": "MISSING_BREAKPOINT_YEAR"}
    size_group, size_bounds, reason = _choose_group(feature["size"], year_rows, "size_group", "size_max")
    if reason:
        return {"status": "UNCLASSIFIABLE", "reason": reason, "stage": "size"}
    size_rows = [r for r in year_rows if r["size_group"] == size_group]
    bm_column = "adj_bm_max" if bm_basis == "adjusted" else "raw_bm_max"
    bm_group, bm_bounds, reason = _choose_group(feature["bm"], size_rows, "bm_group", bm_column)
    if reason:
        return {"status": "UNCLASSIFIABLE", "reason": reason, "stage": "bm"}
    bm_rows = [r for r in size_rows if r["bm_group"] == bm_group]
    mom_group, mom_bounds, reason = _choose_group(feature["mom"], bm_rows, "mom_group", "mom_max")
    if reason:
        return {"status": "UNCLASSIFIABLE", "reason": reason, "stage": "mom"}
    return {"status": "CLASSIFIED", "size_group": size_group, "bm_group": bm_group,
            "mom_group": mom_group, "boundaries": {"size": size_bounds[size_group],
                                                     "bm": bm_bounds[bm_group], "mom": mom_bounds[mom_group]}}


def group_holdings(data, config):
    features = {(r["code"], r["formation_year"]): r for r in data["features"]}
    breaks = defaultdict(list)
    for row in data["breakpoints"]:
        if row["is_not_bse"] == config["breakpoint_is_not_bse"]:
            breaks[row["year"]].append(row)
    result = []
    for holding in data["holdings"]:
        year = formation_year(holding["return_period"])
        feature = features.get((holding["code"], year))
        classification = ({"status": "UNCLASSIFIABLE", "reason": "MISSING_FEATURE_ROW"}
                          if feature is None else classify_one(feature, breaks[year], config["bm_basis"]))
        result.append({**holding, "formation_year": year, **classification})
    return result


def calculate(grouped, data):
    benchmark = {(r["return_period"], r["size_group"], r["bm_group"], r["mom_group"]): r["benchmark_return"]
                 for r in data["benchmark_returns"]}
    rows = []
    for row in grouped:
        out = dict(row)
        if out["status"] == "CLASSIFIED" and out["stock_return"] is None:
            out.update(status="EXCLUDED", reason="MISSING_STOCK_RETURN")
        if out["status"] == "CLASSIFIED":
            key = (out["return_period"], out["size_group"], out["bm_group"], out["mom_group"])
            group_return = benchmark.get(key)
            if group_return is None:
                out.update(status="EXCLUDED", reason="MISSING_BENCHMARK_RETURN")
            else:
                out["benchmark_return"] = group_return
                out["active_return"] = out["stock_return"] - group_return
                out["contribution"] = out["weight"] * out["active_return"]
        rows.append(out)
    quarterly = {}
    for row in rows:
        p = row["return_period"]
        q = quarterly.setdefault(p, {"return_period": p, "disclosed_weight": 0.0,
                                     "covered_weight": 0.0, "cs": 0.0, "holdings": 0, "covered_holdings": 0})
        q["disclosed_weight"] += row["weight"]
        q["holdings"] += 1
        if row["status"] == "CLASSIFIED":
            q["covered_weight"] += row["weight"]
            q["cs"] += row["contribution"]
            q["covered_holdings"] += 1
    for q in quarterly.values():
        q["coverage_of_disclosed"] = q["covered_weight"] / q["disclosed_weight"]
    return {"stock_rows": rows, "quarterly": [quarterly[p] for p in sorted(quarterly)]}

