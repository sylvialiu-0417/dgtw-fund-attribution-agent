import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dgtw_agent.engine import DataError, calculate, classify_one, group_holdings, validate
from dgtw_agent.io import load_csv_bundle
from dgtw_agent.workflow import advance, read_json, start


class DGTWTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "examples" / "generate_synthetic.py")], check=True,
                       stdout=subprocess.DEVNULL)
        cls.input_dir = ROOT / "examples" / "synthetic"
        cls.config = json.loads((cls.input_dir / "config.json").read_text())

    def data(self):
        return validate(load_csv_bundle(self.input_dir), self.config)

    def test_grouping_and_expected_cs(self):
        data = self.data()
        grouped = group_holdings(data, self.config)
        self.assertEqual((grouped[0]["size_group"], grouped[0]["bm_group"], grouped[0]["mom_group"]), (1, 2, 1))
        self.assertEqual((grouped[1]["size_group"], grouped[1]["bm_group"], grouped[1]["mom_group"]), (3, 4, 3))
        self.assertEqual(grouped[2]["reason"], "MISSING_MOM")
        result = calculate(grouped, data)
        self.assertAlmostEqual(result["quarterly"][0]["cs"], 0.5 * (0.12 - 0.018) + 0.4 * (0.03 - 0.030))
        self.assertAlmostEqual(result["quarterly"][1]["cs"], 0.5 * (0.04 - 0.028) + 0.4 * (0.11 - 0.040))
        self.assertAlmostEqual(result["quarterly"][0]["coverage_of_disclosed"], 0.9)

    def test_boundary_equality_and_nonmonotone(self):
        data = self.data()
        feature = {"size": 400_000_000_000, "bm": 0.6, "mom": 0.0}
        result = classify_one(feature, data["breakpoints"], "adjusted")
        self.assertEqual((result["size_group"], result["bm_group"], result["mom_group"]), (2, 3, 3))
        broken = copy.deepcopy(data["breakpoints"])
        for row in broken:
            if row["size_group"] == 2 and row["bm_group"] == 2:
                row["adj_bm_max"] = -9
        self.assertEqual(classify_one(feature, broken, "adjusted")["reason"], "NON_MONOTONE_BREAKPOINT")

    def test_missing_not_zero_imputed(self):
        data = self.data()
        data["holdings"][0]["stock_return"] = None
        result = calculate(group_holdings(data, self.config), data)
        self.assertEqual(result["stock_rows"][0]["reason"], "MISSING_STOCK_RETURN")
        self.assertAlmostEqual(result["quarterly"][0]["covered_weight"], 0.4)

    def test_duplicate_and_future_leakage(self):
        raw = load_csv_bundle(self.input_dir)
        raw["features"].append(copy.deepcopy(raw["features"][0]))
        with self.assertRaises(DataError):
            validate(raw, self.config)
        raw = load_csv_bundle(self.input_dir)
        raw["holdings"][0]["holding_date"] = "2025-03-31"
        self.assertTrue(any("not prior" in issue for issue in validate(raw, self.config)["issues"]))

    def test_recovery_and_hash_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            path = start(self.input_dir, self.input_dir / "config.json", temp, stop_after="grouped")
            self.assertEqual(read_json(path / "state.json")["status"], "INTERRUPTED")
            first_hash = read_json(path / "state.json")["checkpoints"]["groups.json"]
            advance(path)
            state = read_json(path / "state.json")
            self.assertEqual(state["status"], "COMPLETE")
            self.assertEqual(state["checkpoints"]["groups.json"], first_hash)
            self.assertEqual(state["attempts"]["grouped"], 1)
            (path / "groups.json").write_text("[]")
            with self.assertRaises(DataError):
                advance(path)

    def test_source_mutation_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            import shutil
            copied = Path(temp) / "input"
            shutil.copytree(self.input_dir, copied)
            path = start(copied, copied / "config.json", Path(temp) / "runs", stop_after="validated")
            with (copied / "holdings.csv").open("a") as handle:
                handle.write("\n")
            with self.assertRaises(DataError):
                advance(path)

    def test_authorized_supplement_creates_complete_new_run(self):
        with tempfile.TemporaryDirectory() as temp:
            path = start(self.input_dir, self.input_dir / "config.json", temp,
                         supplements_csv=self.input_dir / "supplements.csv")
            self.assertEqual(read_json(path / "state.json")["status"], "COMPLETE")
            self.assertEqual(read_json(path / "input.json")["source_missing"]["feature_mom"], 0)
            self.assertEqual(len(read_json(path / "input.json")["supplements_applied"]), 1)
            self.assertAlmostEqual(read_json(path / "quarterly.json")[0]["coverage_of_disclosed"], 1.0)


if __name__ == "__main__":
    unittest.main()

