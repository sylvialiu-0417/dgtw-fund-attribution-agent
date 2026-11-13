"""Persistent, hash-checked harness with resumable stage checkpoints."""

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .audit import audit
from .engine import DataError, calculate, group_holdings, validate
from .io import apply_supplements, load_csv_bundle, load_excel_pair
from .report import render


STAGES = ("validated", "grouped", "calculated", "audited", "reported")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(value)
        temporary = handle.name
    os.replace(temporary, path)


def _manifest(source_paths, config_path):
    paths = [str(Path(p).resolve()) for p in [*source_paths, config_path]]
    files = {p: sha(p) for p in sorted(paths)}
    content = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"files": files, "manifest_sha256": hashlib.sha256(content).hexdigest(),
            "engine_version": __version__, "created_at_utc": datetime.now(timezone.utc).isoformat()}


def _verify(run_dir, state):
    manifest = read_json(run_dir / "manifest.json")
    for path, expected in manifest["files"].items():
        if not Path(path).is_file() or sha(path) != expected:
            raise DataError(f"Input changed or missing: {path}; start a new run")
    if manifest["engine_version"] != __version__:
        raise DataError("Engine version changed; start a new run rather than mixing checkpoints")
    for file, expected in state["checkpoints"].items():
        if not (run_dir / file).is_file() or sha(run_dir / file) != expected:
            raise DataError(f"Checkpoint changed or missing: {file}")
    return manifest


def start(input_dir, config_path, runs_dir, holdings_xlsx=None, benchmark_xlsx=None, stop_after=None,
          supplements_csv=None):
    if stop_after and stop_after not in STAGES:
        raise ValueError("Invalid stop-after stage")
    input_dir = Path(input_dir).resolve() if input_dir else None
    config_path = Path(config_path).resolve()
    if holdings_xlsx or benchmark_xlsx:
        if not (holdings_xlsx and benchmark_xlsx):
            raise DataError("Both Excel workbooks are required")
        source_paths = [Path(holdings_xlsx).resolve(), Path(benchmark_xlsx).resolve()]
        source = {"kind": "excel", "paths": [str(p) for p in source_paths]}
    else:
        if input_dir is None:
            raise DataError("Provide --input-dir or both Excel workbooks")
        source_paths = [input_dir / f"{name}.csv" for name in ("holdings", "features", "breakpoints", "benchmark_returns")]
        source = {"kind": "csv", "path": str(input_dir)}
    if supplements_csv:
        source["supplements_csv"] = str(Path(supplements_csv).resolve())
        source_paths.append(Path(supplements_csv).resolve())
    for path in [*source_paths, config_path]:
        if not path.is_file():
            raise DataError(f"Missing input file: {path}")
    run_dir = Path(runs_dir).resolve() / uuid.uuid4().hex
    run_dir.mkdir(parents=True)
    manifest = _manifest(source_paths, config_path)
    write_json(run_dir / "manifest.json", manifest)
    state = {"run_id": run_dir.name, "status": "RUNNING", "completed": [], "checkpoints": {},
             "source": source, "config_path": str(config_path), "attempts": {}, "last_error": None}
    write_json(run_dir / "state.json", state)
    advance(run_dir, stop_after=stop_after)
    return run_dir


def _checkpoint(run_dir, state, stage, files):
    for name in files:
        state["checkpoints"][name] = sha(run_dir / name)
    state["completed"].append(stage)
    state["status"] = "RUNNING"
    state["last_error"] = None
    write_json(run_dir / "state.json", state)


def advance(run_dir, stop_after=None):
    run_dir = Path(run_dir).resolve()
    state = read_json(run_dir / "state.json")
    manifest = _verify(run_dir, state)
    if state["status"] == "BLOCKED":
        raise DataError("This run is blocked; correct source/config in a new run")
    if state["status"] == "COMPLETE":
        return run_dir
    config = read_json(state["config_path"])
    for stage in STAGES:
        if stage in state["completed"]:
            continue
        state["attempts"][stage] = state["attempts"].get(stage, 0) + 1
        if state["attempts"][stage] > 2:
            state["status"] = "BLOCKED"
            state["last_error"] = f"Retry limit exceeded in {stage}"
            write_json(run_dir / "state.json", state)
            raise DataError(state["last_error"])
        write_json(run_dir / "state.json", state)
        try:
            if stage == "validated":
                source = state["source"]
                raw = load_csv_bundle(source["path"]) if source["kind"] == "csv" else load_excel_pair(*source["paths"])
                if source.get("supplements_csv"):
                    raw = apply_supplements(raw, source["supplements_csv"])
                data = validate(raw, config)
                write_json(run_dir / "input.json", data)
                _checkpoint(run_dir, state, stage, ["input.json"])
                if data["issues"]:
                    state["status"] = "BLOCKED"
                    state["last_error"] = "; ".join(data["issues"][:10])
                    write_json(run_dir / "state.json", state)
                    return run_dir
            elif stage == "grouped":
                data = read_json(run_dir / "input.json")
                write_json(run_dir / "groups.json", group_holdings(data, config))
                _checkpoint(run_dir, state, stage, ["groups.json"])
            elif stage == "calculated":
                data = read_json(run_dir / "input.json")
                grouped = read_json(run_dir / "groups.json")
                result = calculate(grouped, data)
                write_json(run_dir / "stock_rows.json", result["stock_rows"])
                write_json(run_dir / "quarterly.json", result["quarterly"])
                write_json(run_dir / "exceptions.json", [r for r in result["stock_rows"] if r["status"] != "CLASSIFIED"])
                _checkpoint(run_dir, state, stage, ["stock_rows.json", "quarterly.json", "exceptions.json"])
            elif stage == "audited":
                data = read_json(run_dir / "input.json")
                grouped = read_json(run_dir / "groups.json")
                result = {"stock_rows": read_json(run_dir / "stock_rows.json"),
                          "quarterly": read_json(run_dir / "quarterly.json")}
                verdict = audit(data, grouped, result, config)
                write_json(run_dir / "audit.json", verdict)
                _checkpoint(run_dir, state, stage, ["audit.json"])
                if not verdict["passed"]:
                    state["status"] = "BLOCKED"
                    state["last_error"] = "; ".join(verdict["errors"][:10])
                    write_json(run_dir / "state.json", state)
                    return run_dir
            elif stage == "reported":
                result = {"stock_rows": read_json(run_dir / "stock_rows.json"),
                          "quarterly": read_json(run_dir / "quarterly.json")}
                verdict = read_json(run_dir / "audit.json")
                write_text(run_dir / "report.md", render(result, verdict, manifest))
                _checkpoint(run_dir, state, stage, ["report.md"])
        except (DataError, ValueError, KeyError) as exc:
            state["status"] = "BLOCKED"
            state["last_error"] = str(exc)
            write_json(run_dir / "state.json", state)
            raise
        except OSError as exc:
            state["status"] = "RETRYABLE" if state["attempts"][stage] < 2 else "BLOCKED"
            state["last_error"] = str(exc)
            write_json(run_dir / "state.json", state)
            raise
        if stage == stop_after:
            state["status"] = "INTERRUPTED"
            write_json(run_dir / "state.json", state)
            return run_dir
    state["status"] = "COMPLETE"
    write_json(run_dir / "state.json", state)
    return run_dir

