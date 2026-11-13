"""Fixed, versioned acceptance baseline; reject financial-output regressions."""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dgtw_agent.workflow import read_json, start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept-baseline", action="store_true", help="Requires human review and a new commit")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "examples" / "generate_synthetic.py")], check=True,
                   stdout=subprocess.DEVNULL)
    suite = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
    if suite.returncode:
        return suite.returncode
    source = ROOT / "examples" / "synthetic"
    with tempfile.TemporaryDirectory() as temp:
        run = start(source, source / "config.json", temp)
        state = read_json(run / "state.json")
        q = read_json(run / "quarterly.json")
        verdict = read_json(run / "audit.json")
    metrics = {"status": state["status"], "audit_passed": verdict["passed"],
               "quarters": len(q), "cs": [x["cs"] for x in q],
               "coverage": [x["coverage_of_disclosed"] for x in q],
               "excluded_rows": verdict["excluded_rows"]}
    baseline_path = ROOT / "evals" / "baseline.json"
    if args.accept_baseline:
        baseline_path.write_text(json.dumps(metrics, indent=2) + "\n")
        print("Baseline updated; review diff and commit deliberately.")
        return 0
    baseline = json.loads(baseline_path.read_text())
    for key in ("status", "audit_passed", "quarters", "excluded_rows"):
        if metrics[key] != baseline[key]:
            print(f"REGRESSION {key}: {metrics[key]} != {baseline[key]}", file=sys.stderr)
            return 2
    for key in ("cs", "coverage"):
        if len(metrics[key]) != len(baseline[key]) or any(not math.isclose(a, b, abs_tol=1e-12)
                                                      for a, b in zip(metrics[key], baseline[key])):
            print(f"REGRESSION {key}", file=sys.stderr)
            return 2
    print("EVAL PASS: fixed baseline, unit tests, audit and recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

