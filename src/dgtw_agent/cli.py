"""Command-line entry point for research runs and recovery."""

import argparse
import json
import sys

from .workflow import advance, read_json, start


def main(argv=None):
    parser = argparse.ArgumentParser(prog="dgtw-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Create a new immutable run")
    run.add_argument("--input-dir")
    run.add_argument("--holdings-xlsx")
    run.add_argument("--benchmark-xlsx")
    run.add_argument("--config", required=True)
    run.add_argument("--runs-dir", required=True)
    run.add_argument("--stop-after", choices=("validated", "grouped", "calculated", "audited"))
    resume = sub.add_parser("resume", help="Resume an interrupted run after hash checks")
    resume.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            path = start(args.input_dir, args.config, args.runs_dir, args.holdings_xlsx,
                         args.benchmark_xlsx, args.stop_after)
        else:
            path = advance(args.run_dir)
        state = read_json(path / "state.json")
        print(json.dumps({"run_dir": str(path), "status": state["status"],
                          "completed": state["completed"], "last_error": state["last_error"]}, ensure_ascii=False))
        return 0 if state["status"] in ("COMPLETE", "INTERRUPTED") else 2
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

