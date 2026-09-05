import copy
import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load(filename, name):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit = load("audit_phase_b4_new_output.py", "phase_b4_audit_test")
analyze = load("analyze_phase_b4_frontier.py", "phase_b4_analyze_test")
render = load("render_phase_b4_merged_map.py", "phase_b4_render_test")
submit = load("submit_phase_b4_frontier.py", "phase_b4_submit_gate_test")


class PhaseB4GateTests(unittest.TestCase):
    def test_completion_audit_checks_all_3000_syndrome_faithful_rows(self):
        manifest = json.loads(submit.DEFAULT_MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "raw.jsonl.gz"
            with gzip.open(raw, "wt", encoding="utf-8") as handle:
                for index in range(3000):
                    handle.write(json.dumps({"campaign": manifest["campaign"], "q": 0.05, "p": 0.20, "L": [7, 9, 11][index % 3], "seed": manifest["new_seeds"][index % 5], "syndrome_faithful": True}) + "\n")
            payload = {"campaign": manifest["campaign"], "lattice": "honeycomb", "q": 0.05, "p_grid": [0.20], "sizes": [7, 9, 11], "seeds": manifest["new_seeds"], "decoder": manifest["decoder"], "source_hashes": manifest["required_source_hashes"], "source_stability": {"start_equals_end": True}, "raw_records": {"records": 3000, "sha256": audit.sha256(raw)}, "syndrome_fidelity": {"all_faithful": True}}
            self.assertEqual(audit.audit_pair(manifest, payload, raw), (3000, 3000))

    def test_pooled_analyzer_uses_exactly_base_plus_fresh_counts(self):
        base = {"summaries": [{"q": 0.05, "p": 0.20, "L": size, "logical_errors": errors, "shots": 1000} for size, errors in [(7, 300), (9, 320), (11, 340)]]}
        fresh = {"summaries": [{"q": 0.05, "p": 0.20, "L": size, "logical_errors": errors, "shots": 1000} for size, errors in [(7, 310), (9, 330), (11, 350)]]}
        row = analyze.analyze_counts(base, fresh)
        self.assertEqual(row["logical_errors"], [610, 650, 690])
        self.assertEqual(row["shots"], [2000, 2000, 2000])

    def test_renderer_updates_exactly_one_payload_and_preserves_230(self):
        base = json.loads(render.DEFAULT_BASE.read_text())
        target = next(cell for row in base["analyses"] if row["q"] == 0.05 for cell in row["cells"] if cell["p"] == 0.20)
        row = {"q": 0.05, "p": 0.20, "pooling_kind": "new_independent_shots", "sizes": [7, 9, 11], "logical_errors": [600, 650, 700], "shots": [2000, 2000, 2000], "classification": "unresolved", "jeffreys_classification": "unresolved", "uniform_prior_sensitivity": {"classification": "unresolved"}}
        merged, changes = render.merged_analyses(base, {"analyses": [row]})
        self.assertEqual(len(changes), 1)
        unchanged = 0
        for before_row, after_row in zip(base["analyses"], merged):
            for before, after in zip(before_row["cells"], after_row["cells"]):
                if (before_row["q"], before["p"]) != (0.05, 0.20):
                    self.assertEqual(before, after)
                    unchanged += 1
        self.assertEqual(unchanged, 230)
        self.assertEqual(target["classification"], "unresolved")

    def test_preflight_rejects_source_hash_drift(self):
        manifest = json.loads(submit.DEFAULT_MANIFEST.read_text())
        drifted = copy.deepcopy(manifest)
        drifted["required_source_hashes"]["runner"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            jobs = submit.expand_jobs(drifted, project_root=Path(temporary), lab_dir=Path(temporary) / "lab")
        with self.assertRaisesRegex(ValueError, "source hash drift"):
            submit.validate(submit.DEFAULT_MANIFEST, drifted, jobs)


if __name__ == "__main__":
    unittest.main()
