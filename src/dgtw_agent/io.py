"""Read canonical CSV or bilingual teaching workbooks without changing originals."""

import csv
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


def load_excel_pair(holdings_path, benchmark_path):
    try:
        from openpyxl import load_workbook
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

