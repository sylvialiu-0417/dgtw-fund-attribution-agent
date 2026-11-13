"""Read canonical CSV or bilingual teaching workbooks without changing originals."""

import csv
from datetime import date, datetime, time
from pathlib import Path


TABLES = ("holdings", "features", "breakpoints", "benchmark_returns")


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_csv_bundle(directory):
    directory = Path(directory)
    missing = [name for name in TABLES if not (directory / f"{name}.csv").is_file()]
    if missing:
        raise ValueError(f"Missing canonical tables: {', '.join(missing)}")
    return {name: _csv(directory / f"{name}.csv") for name in TABLES}


def apply_supplements(raw, path):
    """Backfill only genuinely missing stock-year features with provenance."""
    from .engine import DataError, code, integer, number

    supplements = _csv(Path(path))
    features = {(code(r["code"]), integer(r["formation_year"], "formation_year")): r
                for r in raw["features"]}
    used = set()
    applied = []
    for row in supplements:
        key = (code(row.get("code")), integer(row.get("formation_year"), "formation_year"))
        metric = str(row.get("metric", "")).strip().lower()
        if metric not in ("size", "bm", "mom"):
            raise DataError(f"Invalid supplemental metric: {metric}")
        if (key, metric) in used:
            raise DataError(f"Duplicate supplement: {key} {metric}")
        used.add((key, metric))
        if key not in features:
            raise DataError(f"Supplement lacks original stock-year row: {key}")
        if features[key].get(metric) not in (None, "", "#N/A"):
            raise DataError(f"Supplement would overwrite nonmissing source value: {key} {metric}")
        for field in ("source", "source_definition", "extracted_at"):
            if not str(row.get(field, "")).strip():
                raise DataError(f"Supplement lacks provenance field {field}: {key} {metric}")
        value = number(row.get("value"), f"supplement {metric}")
        features[key][metric] = value
        applied.append({"code": key[0], "formation_year": key[1], "metric": metric,
                        "source": row["source"], "source_definition": row["source_definition"],
                        "extracted_at": row["extracted_at"]})
    raw["supplements_applied"] = applied
    return raw


def load_excel_pair(holdings_path, benchmark_path):
    try:
        from openpyxl import load_workbook
        from openpyxl.utils.datetime import to_excel
    except ImportError as exc:
        raise RuntimeError("Install the openpyxl dependency to read Excel inputs") from exc

    def sheets(path):
        book = load_workbook(path, read_only=True, data_only=True)
        out = []
        for sheet in book:
            rows = sheet.iter_rows(values_only=True)
            header = next(rows, None)
            if header:
                out.append((sheet.title, [str(x).strip() if x is not None else "" for x in header], list(rows)))
        book.close()
        return out

    source = sheets(holdings_path) + sheets(benchmark_path)
    found = {}
    for title, header, rows in source:
        names = set(header)
        if {"time", "code", "weight", "return"} <= names:
            kind = "holdings"
            mapping = {"holding_date": "time", "return_period": "date", "code": "code", "weight": "weight", "stock_return": "return"}
        elif {"code", "year", "市值", "账面市值比", "股票动量"} <= names:
            kind = "features"
            mapping = {"code": "code", "formation_year": "year", "size": "市值", "bm": "账面市值比", "mom": "股票动量"}
        elif {"TradingYear", "MarketValue", "BooktoMarket", "Momentum", "IsNotBSE"} <= names:
            kind = "breakpoints"
            mapping = {"year": "TradingYear", "size_group": "MarketValue", "bm_group": "BooktoMarket", "mom_group": "Momentum", "is_not_bse": "IsNotBSE", "size_max": "MarketValueMax", "adj_bm_max": "AdjbtmMax", "raw_bm_max": "BtmMax", "mom_max": "MomMax"}
        elif {"时间", "市值分类标识", "账面市值比分类标识", "股票动量分类标识", "基准"} <= names:
            kind = "benchmark_returns"
            mapping = {"return_period": "时间", "size_group": "市值分类标识", "bm_group": "账面市值比分类标识", "mom_group": "股票动量分类标识", "benchmark_return": "基准"}
        else:
            continue
        if kind in found:
            raise ValueError(f"Ambiguous duplicate {kind} tables; inspect workbook sheets")
        indices = {dst: header.index(src) for dst, src in mapping.items()}
        records = []
        for row in rows:
            item = {dst: (row[pos] if pos < len(row) else None) for dst, pos in indices.items()}
            if kind == "holdings" and isinstance(item["stock_return"], (date, datetime, time)):
                # Some uploaded return cells have an Excel date number format. Recover the
                # underlying serial for diagnosis, but force analyst review in validate().
                item["stock_return"] = to_excel(item["stock_return"])
                item["_excel_return_date_coercion"] = True
            if kind == "breakpoints":
                try:
                    int(item["year"])
                except (TypeError, ValueError):
                    continue  # CSMAR metadata lines, not observations
            if all(value is None for value in item.values()):
                continue
            records.append(item)
        found[kind] = records
    missing = set(TABLES) - set(found)
    if missing:
        raise ValueError(f"Could not identify tables: {', '.join(sorted(missing))}; provide canonical CSV")
    return found

