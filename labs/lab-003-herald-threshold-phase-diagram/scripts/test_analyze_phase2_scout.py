from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_phase2_scout.py")
SPEC = importlib.util.spec_from_file_location("analyze_phase2_scout", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)


def synthetic_manifest() -> dict:
    return {
        "campaign": "phase2-q-skeleton-discovery-2026-08-27",
        "q_values": [step / 20 for step in range(21)],
        "lattices": ["square", "honeycomb"],
        "sizes": [5, 7],
        "seeds": [520001, 520002, 520003, 520004, 520005],
        "shots_per_seed": 200,
        "p_grid": {"square": [0.1, 0.2, 0.3], "honeycomb": [0.1, 0.2, 0.3]},
    }


def synthetic_payload(*, lattice: str = "square", q: float = 0.5) -> dict:
    manifest = synthetic_manifest()
    # One stable crossing: delta L5-L7 is negative at p=.1 and positive above.
    counts_by_size = {5: [20, 60, 80], 7: [40, 40, 60]}
    per_seed = []
    summaries = []
    for size in manifest["sizes"]:
        for p_offset, p in enumerate(manifest["p_grid"][lattice]):
            per_seed_count = counts_by_size[size][p_offset]
            for seed in manifest["seeds"]:
                per_seed.append({
                    "lattice": lattice,
                    "L": size,
                    "p": p,
                    "q": q,
                    "seed": seed,
                    "shots": 200,
                    "logical_errors": per_seed_count,
                })
            errors = 5 * per_seed_count
            summaries.append({
                "lattice": lattice,
                "L": size,
                "edges": 1,
                "detectors": 1,
                "p": p,
                "q": q,
                "decoder": "herald_damping_bp_llr_mwpm",
                "shots": 1000,
                "logical_errors": errors,
                "logical_error_rate": errors / 1000,
                "logical_error_ci95": [0.0, 1.0],
                "bp_convergence_rate": 1.0,
                "mean_bp_iterations": 1.0,
                "mean_bp_max_message_delta": 0.0,
                "mean_decode_ms": 1.0,
            })
    payload = {
        "schema_version": 1,
        "campaign": manifest["campaign"],
        "lattice": lattice,
        "q": q,
        "p_grid": manifest["p_grid"][lattice],
        "sizes": manifest["sizes"],
        "seeds": manifest["seeds"],
        "shots_per_seed": 200,
        "decoder": dict(analysis.DECODER),
        "sampling": analysis.expected_sampling(lattice),
        "total_shots_per_cell": 1000,
        "runtime": {
            "python_executable": "/registered/python",
            "python_version": "3.13.2",
            "numpy_version": "1.26.4",
            "numba_version": "0.65.0",
            "scipy_version": "1.16.0",
            "pymatching_version": "2.4.0",
            "numba_available": True,
        },
        "source_hashes": {key: "a" * 64 for key in analysis.SOURCE_FILES},
        "per_seed": per_seed,
        "summaries": summaries,
        "raw_records": {
            "path": "results/not-read-in-this-test.jsonl.gz",
            "format": "gzip_json_lines",
            "records": 6000,
            "sha256": "b" * 64,
        },
    }
    payload["config_sha256"] = analysis.config_sha256(payload)
    return payload


class CrossingTests(unittest.TestCase):
    def test_all_sign_changes_are_preserved(self) -> None:
        crossings = analysis.curve_crossings(
            [0.1, 0.2, 0.3, 0.4],
            [-0.1, 0.1, -0.1, 0.1],
        )
        self.assertEqual(len(crossings), 3)
        self.assertTrue(all(item["kind"] == "sign_change" for item in crossings))
        self.assertTrue(all(item["boundary_candidate"] for item in crossings))
        for actual, expected in zip([item["estimate"] for item in crossings], [0.15, 0.25, 0.35]):
            self.assertAlmostEqual(actual, expected)

    def test_zero_run_is_retained_as_one_interval(self) -> None:
        crossings = analysis.curve_crossings([0.1, 0.2, 0.3, 0.4], [-0.1, 0.0, 0.0, 0.1])
        self.assertEqual(crossings, [{
            "kind": "zero_interval",
            "p_interval": [0.2, 0.3],
            "estimate": 0.25,
            "boundary_candidate": True,
        }])

    def test_low_p_zero_plateau_is_not_a_boundary_crossing(self) -> None:
        events = analysis.curve_crossings([0.1, 0.2, 0.3], [0.0, 0.0, 0.1])
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0]["boundary_candidate"])

    def test_seed_bootstrap_finite_classification(self) -> None:
        result = analysis.analyze_q(
            synthetic_payload(),
            synthetic_manifest(),
            bootstrap_replicates=200,
            bootstrap_seed=7,
        )
        self.assertEqual(result["classification"], "finite")
        crossings = result["adjacent_size_crossings"][0]["crossings"]
        self.assertEqual(len(crossings), 1)
        self.assertAlmostEqual(crossings[0]["estimate"], 0.15)
        for endpoint in crossings[0]["bootstrap"]["interval95"]:
            self.assertAlmostEqual(endpoint, 0.15)

    def test_manifest_confidence_level_controls_90_percent_intervals(self) -> None:
        manifest = synthetic_manifest()
        manifest["inference"] = {"confidence_level": 0.90}
        result = analysis.analyze_q(
            synthetic_payload(),
            manifest,
            bootstrap_replicates=200,
            bootstrap_seed=11,
        )
        crossing = result["adjacent_size_crossings"][0]["crossings"][0]
        self.assertEqual(result["confidence_level"], 0.90)
        self.assertIn("interval90", crossing["bootstrap"])
        self.assertIn("bootstrap_interval90", result["cells"][0]["adjacent_size_evidence"][0])
        self.assertIn("no_crossing_fraction", crossing["bootstrap"])
        self.assertIn("multiple_crossing_fraction", crossing["bootstrap"])

    def test_q_p_plot_renders(self) -> None:
        result = analysis.analyze_q(
            synthetic_payload(),
            synthetic_manifest(),
            bootstrap_replicates=100,
            bootstrap_seed=9,
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "phase-map.png"
            analysis.plot_lattice("square", [result], synthetic_manifest(), destination)
            self.assertGreater(destination.stat().st_size, 0)


class ValidationTests(unittest.TestCase):
    def test_explicit_high_q_refinement_manifest_allows_more_seed_clusters(self) -> None:
        manifest = synthetic_manifest()
        manifest.update({
            "q_grid_policy": "explicit",
            "q_values": [0.85, 0.9, 0.95],
            "lattices": ["honeycomb"],
            "seeds": list(range(571001, 571021)),
            "shots_per_seed": 200,
            "shots_per_cell": 4000,
            "expected_shards": 3,
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            loaded = analysis.load_manifest(path)
        self.assertEqual(loaded["q_values"], [0.85, 0.9, 0.95])
        self.assertEqual(len(loaded["seeds"]), 20)

    def test_full_skeleton_policy_rejects_partial_q_grid(self) -> None:
        manifest = synthetic_manifest()
        manifest["q_values"] = [0.9, 0.95]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(analysis.ValidationError, "full_skeleton"):
                analysis.load_manifest(path)

    def test_duplicate_per_seed_cell_is_rejected(self) -> None:
        payload = synthetic_payload()
        payload["per_seed"].append(dict(payload["per_seed"][0]))
        with self.assertRaisesRegex(analysis.ValidationError, "duplicate per-seed"):
            analysis._validate_rows(payload, synthetic_manifest())

    def test_config_hash_tampering_is_rejected(self) -> None:
        payload = synthetic_payload()
        payload["config_sha256"] = hashlib.sha256(b"wrong").hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "phase2-square-q050-discovery-1000-2026-08-27.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(analysis.ValidationError, "config SHA-256"):
                analysis.validate_shard(path, synthetic_manifest(), validate_raw=False)

    def test_discovery_requires_every_lattice_q_pair(self) -> None:
        manifest = synthetic_manifest()
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            for lattice in manifest["lattices"]:
                for q in manifest["q_values"]:
                    name = f"phase2-{lattice}-{analysis.q_tag(q)}-discovery-1000-2026-08-27.json"
                    (results / name).touch()
            discovered = analysis.discover_shards(results, manifest)
            self.assertEqual(len(discovered), 42)
            next(iter(discovered.values())).unlink()
            with self.assertRaisesRegex(analysis.ValidationError, "coverage mismatch"):
                analysis.discover_shards(results, manifest)

    def test_custom_manifest_discovers_only_unique_campaign_names(self) -> None:
        manifest = synthetic_manifest()
        manifest["lattices"] = ["honeycomb"]
        manifest["artifact_stem_template"] = "unit-{lattice}-{q_tag}"
        manifest["expected_shards"] = 21
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            for q in manifest["q_values"]:
                (results / f"unit-honeycomb-{analysis.q_tag(q)}.json").touch()
            (results / "phase2-square-q050-discovery-1000-2026-08-27.json").touch()
            discovered = analysis.discover_shards(results, manifest)
            self.assertEqual(len(discovered), 21)
            self.assertTrue(all(key[0] == "honeycomb" for key in discovered))

    def test_duplicate_raw_cell_is_rejected(self) -> None:
        manifest = synthetic_manifest()
        manifest["sizes"] = [5, 7]
        manifest["seeds"] = [1]
        manifest["shots_per_seed"] = 2
        manifest["p_grid"] = {"square": [0.1], "honeycomb": [0.1]}
        seed_rows = {(size, 0.1, 1): {"logical_errors": 0} for size in manifest["sizes"]}
        with tempfile.TemporaryDirectory() as directory:
            lab_dir = Path(directory)
            results = lab_dir / "results"
            results.mkdir()
            summary_path = results / "phase2-square-q050-discovery-1000-2026-08-27.json"
            raw_path = summary_path.with_name(f"{summary_path.stem}-raw.jsonl.gz")
            base = {
                "campaign": manifest["campaign"],
                "lattice": "square",
                "L": 5,
                "p": 0.1,
                "q": 0.5,
                "decoder": "herald_damping_bp_llr_mwpm",
                "seed": 1,
                "shot": 0,
                "observation_id": f"{manifest['campaign']}:square:L5:seed1:shot0",
                "logical_failure": False,
            }
            with gzip.open(raw_path, "wt", encoding="utf-8") as output:
                output.write(json.dumps(base) + "\n")
                output.write(json.dumps(base) + "\n")
            payload = {
                "lattice": "square",
                "q": 0.5,
                "raw_records": {
                    "path": f"results/{raw_path.name}",
                    "format": "gzip_json_lines",
                    "records": 2,
                    "sha256": analysis.sha256(raw_path),
                },
            }
            with self.assertRaisesRegex(analysis.ValidationError, "duplicate raw"):
                analysis._validate_raw(payload, summary_path, lab_dir, manifest, seed_rows)


if __name__ == "__main__":
    unittest.main()
