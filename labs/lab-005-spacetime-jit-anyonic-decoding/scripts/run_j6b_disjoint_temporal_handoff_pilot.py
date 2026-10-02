"""One-shot J6B preflight and separately armed matched-history production.

Default execution is deterministic only.  Production requires a passed
preflight bound to this runner and the immutable J6B contract.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import sysconfig
import time
from typing import Any

import numba
import numpy as np
import pymatching
import scipy


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
MANIFEST = LAB / "manifests/j6b-disjoint-temporal-handoff-pilot-2026-09-23.json"
PREFLIGHT = LAB / "results/j6b-disjoint-temporal-handoff-preflight-2026-09-23.json"
ROWS = LAB / "results/j6b-disjoint-temporal-handoff-rows-2026-09-23.jsonl"
ANALYSIS = LAB / "results/j6b-disjoint-temporal-handoff-analysis-2026-09-23.json"
SCHEDULES = ("immediate", "fixed_delay_1", "jit_lyons_brown", "offline_full_history")
MODES = ("syndrome_only", "heralded")
TESTS = (
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_j6a_causal_handoff.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_j6b_r0_temporal_ledger.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_integrated_history.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e1b_report_distribution_is_normalized_and_has_correct_perfect_limit",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py::test_e2a_rejects_wrong_action_binding_and_noncharge_reports",
    "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_charge.py::test_public_charge_action_uses_full_binary_record_only",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def versions() -> dict[str, str]:
    return {
        "python": ".".join(str(x) for x in sys.version_info[:3]),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "numba": numba.__version__, "pymatching": pymatching.__version__,
    }


def provenance(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    checks: list[dict[str, Any]] = []

    def check(path: Path, expected: str, required_status: str | None = None) -> None:
        actual = digest(path) if path.is_file() else None
        status = json.loads(path.read_text()).get("status") if required_status and path.is_file() else None
        passed = actual == expected and (required_status is None or status == required_status)
        checks.append({"path": str(path.relative_to(ROOT)), "expected_sha256": expected,
                       "actual_sha256": actual, "required_status": required_status,
                       "actual_status": status, "passed": passed})

    for spec in manifest["dependencies"].values():
        check(LAB / spec["path"], spec["sha256"], spec["required_status"])
    for relative, expected in manifest["frozen_source_sha256"].items():
        check(LAB / relative, expected)
    for name in ("raw_rows", "analysis"):
        spec = manifest["legacy_j6_quarantine"][name]
        check(LAB / spec["path"], spec["sha256"])
    return checks, all(item["passed"] for item in checks)


def geometry():
    from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox

    result = AbsorberGeometry()
    result.open(
        AbsorbingRegion("j6b-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 4)), 0),
        current_round=0,
    )
    return result


def deterministic_history(trial_id: str, odd_rounds: tuple[int, ...]):
    from d4_integrated_history import build_integrated_d4_history_from_draws
    from d4_spatial_policy import paper_periodic_honeycomb
    from generic_history import GenericNoiseParameters

    lattice = paper_periodic_honeycomb(2)
    readout_faults = np.zeros((5, lattice.vertex_count), dtype=bool)
    readout_faults[list(odd_rounds), 0] = True
    key = lambda tag: hashlib.sha256(f"{trial_id}:{tag}".encode("ascii")).hexdigest()
    return build_integrated_d4_history_from_draws(
        trial_id=trial_id, master_seed=1,
        parameters=GenericNoiseParameters(0, 0, 0, 0, 0),
        physical_key=key("physical"), first_observation_key=key("first"),
        second_exogenous_key=key("second"),
        transition_edge_faults=np.zeros((4, lattice.edge_count), dtype=bool),
        syndrome_measurement_faults=readout_faults,
        herald_uniforms=np.full((5, lattice.vertex_count), 0.5),
        first_observation_seeds=(10, 11, 12, 13, 14),
    )


def deterministic_matrix() -> tuple[list[dict[str, Any]], int, int]:
    from d4_integrated_history import evaluate_history_matrix
    from d4_spatial_policy import paper_periodic_honeycomb
    from generic_history import herald_confusion_matrix, GenericNoiseParameters

    lattice = paper_periodic_honeycomb(2)
    positions = tuple((site,) for site in range(lattice.vertex_count))
    cases = (("zero", ()), ("odd_then_even", (1,)), ("persistent_odd", (1, 2)))
    results = []
    arms = 0
    for name, odd_rounds in cases:
        history = deterministic_history(f"j6b-preflight-{name}", odd_rounds)
        first = evaluate_history_matrix(history, check_positions=positions, geometry=geometry())
        second = evaluate_history_matrix(history, check_positions=positions, geometry=geometry())
        arms += len(first) + len(second)
        public = history.public_transcript()
        public_keys = set(public)
        passed = bool(
            first == second and len(first) == 8
            and {(row.mode, row.branch) for row in first} == {(m, b) for m in MODES for b in SCHEDULES}
            and all(row.denominator_included for row in first)
            and all((row.status != "failed_closed") or row.logical_failure for row in first)
            and public_keys == {"trial_id", "history_digest", "syndrome_readout", "syndrome_detectors", "herald_readout"}
            and len({history.physical_key, history.first_observation_key, history.second_exogenous_key}) == 3
            and (name != "zero" or all(row.status == "scored" and not row.logical_failure for row in first))
        )
        results.append({"fixture": name, "passed": passed, "rows": len(first),
                        "failed_closed": sum(row.status == "failed_closed" for row in first),
                        "logical_failures": sum(row.logical_failure for row in first),
                        "replay_equal": first == second})
    for cell in json.loads(MANIFEST.read_text())["matched_design"]["cells"]:
        p = cell["rates"]
        matrix = herald_confusion_matrix(GenericNoiseParameters(
            p["p_data"], p["p_syndrome"], p["p_fp"], p["p_fn"], p["p_confuse"]
        ))
        results.append({"fixture": f"{cell['id']}:channel_normalization",
                        "passed": bool(np.all(matrix >= 0) and np.allclose(matrix.sum(axis=1), 1)),
                        "rows": 0})
    return results, len(cases), arms


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def run_preflight() -> dict[str, Any]:
    started = time.monotonic()
    manifest = json.loads(MANIFEST.read_text())
    checks, provenance_ok = provenance(manifest)
    runtime = versions()
    runtime_ok = all(runtime.get(name) == expected for name, expected in manifest["runtime"].items()
                     if name in runtime)
    outputs_absent = not ROWS.exists() and not ANALYSIS.exists()
    gate_rows: list[dict[str, Any]] = []
    fixture_rows: list[dict[str, Any]] = []
    synthetic_histories = arm_evaluations = 0
    if provenance_ok and runtime_ok and outputs_absent:
        pytest = shutil.which("pytest")
        if pytest is None:
            gate_rows.append({"gate": "public_path_and_model_fixtures", "passed": False,
                              "returncode": None, "output": "Existing pytest executable is unavailable"})
        else:
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = "0"
            env["PYTHONPATH"] = os.pathsep.join(
                filter(None, (sysconfig.get_paths()["purelib"], env.get("PYTHONPATH")))
            )
            try:
                completed = subprocess.run(
                    [pytest, "-q", "-x", *TESTS],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120, check=False,
                )
                gate_rows.append({"gate": "public_path_and_model_fixtures", "passed": completed.returncode == 0,
                                  "returncode": completed.returncode, "output": (completed.stdout + completed.stderr).strip()})
                if completed.returncode == 0:
                    fixture_rows, synthetic_histories, arm_evaluations = deterministic_matrix()
            except (AssertionError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                gate_rows.append({"gate": "public_path_and_model_fixtures", "passed": False,
                                  "returncode": None, "output": f"{type(error).__name__}:{error}"})
    outputs_absent_after = not ROWS.exists() and not ANALYSIS.exists()
    budget = manifest["compute_budget"]["preflight"]
    budget_ok = synthetic_histories <= budget["max_deterministic_synthetic_histories"] and arm_evaluations <= budget["max_arm_evaluations"]
    elapsed = time.monotonic() - started
    passed = bool(provenance_ok and runtime_ok and outputs_absent and outputs_absent_after and gate_rows
                  and all(row["passed"] for row in gate_rows)
                  and fixture_rows and all(row["passed"] for row in fixture_rows)
                  and budget_ok and elapsed < 600 and rss_bytes() < 2 * 1024**3)
    result = {
        "schema_version": 1, "phase": "J6B deterministic preflight",
        "status": "passed" if passed else "censored", "production_armed": passed,
        "manifest": str(MANIFEST.relative_to(ROOT)), "manifest_sha256": digest(MANIFEST),
        "runner_sha256": digest(Path(__file__)), "runtime": runtime,
        "runtime_passed": runtime_ok, "provenance": checks, "provenance_passed": provenance_ok,
        "public_path_gate": gate_rows, "deterministic_matrix": fixture_rows,
        "forbidden_outputs_absent": outputs_absent and outputs_absent_after,
        "counters": {"synthetic_histories": synthetic_histories,
                     "synthetic_arm_evaluations": arm_evaluations,
                     "production_histories": 0, "production_arm_evaluations": 0,
                     "bootstrap_replicates": 0},
        "resource_use": {"wall_seconds": round(elapsed, 5), "peak_rss_bytes": rss_bytes()},
        "budget_passed": budget_ok,
        "claim_boundary": "Deterministic public-interface verification only; no schedule-risk or fault-tolerance evidence.",
        "next_action": "Run the separately gated fixed cohort once" if passed else "Stop: repair failed preflight gates without generating the cohort",
    }
    atomic_json(PREFLIGHT, result)
    print(json.dumps({"status": result["status"], "preflight": str(PREFLIGHT),
                      "counters": result["counters"]}))
    return result


def run_production() -> dict[str, Any]:
    """Execute exactly the registered cohort; stop before any bootstrap."""

    if ROWS.exists() or ANALYSIS.exists():
        raise SystemExit("J6B outputs already exist; refusing to resample")
    if not PREFLIGHT.is_file():
        raise SystemExit("J6B preflight result is absent")
    manifest = json.loads(MANIFEST.read_text())
    preflight = json.loads(PREFLIGHT.read_text())
    checks, provenance_ok = provenance(manifest)
    runtime = versions()
    runtime_ok = all(runtime.get(name) == expected for name, expected in manifest["runtime"].items()
                     if name in runtime)
    release = bool(
        provenance_ok and runtime_ok and preflight.get("status") == "passed"
        and preflight.get("production_armed") is True
        and preflight.get("manifest_sha256") == digest(MANIFEST)
        and preflight.get("runner_sha256") == digest(Path(__file__))
        and preflight.get("forbidden_outputs_absent") is True
    )
    if not release:
        raise SystemExit("J6B production release gate is not satisfied")

    from d4_integrated_history import evaluate_history_matrix, generate_integrated_d4_history
    from d4_spatial_policy import paper_periodic_honeycomb
    from e1_schedule_integration import run_e1_policy_matrix
    from generic_history import GenericNoiseParameters

    lattice = paper_periodic_honeycomb(2)
    positions = tuple((site,) for site in range(lattice.vertex_count))
    started_wall, started_cpu = time.monotonic(), time.process_time()
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    failures: list[str] = []
    cap_failure: str | None = None
    for cell_index, cell in enumerate(manifest["matched_design"]["cells"]):
        p = cell["rates"]
        parameters = GenericNoiseParameters(p["p_data"], p["p_syndrome"], p["p_fp"],
                                            p["p_fn"], p["p_confuse"])
        for history_index in range(cell["histories"]):
            if time.process_time() - started_cpu >= 60 * manifest["compute_budget"]["hard_caps"]["cpu_minutes"]:
                cap_failure = "cpu_minute_cap_exceeded"
                break
            if rss_bytes() >= 2 * 1024**3:
                cap_failure = "resident_memory_cap_exceeded"
                break
            master_seed = 923_240_000 + 100_000 * cell_index + history_index
            trial_id = f"j6b-{cell['id']}-{history_index:04d}"
            history = generate_integrated_d4_history(
                trial_id=trial_id, master_seed=master_seed, parameters=parameters
            )
            replay = generate_integrated_d4_history(
                trial_id=trial_id, master_seed=master_seed, parameters=parameters
            )
            replay_ok = bool(
                history.history_digest == replay.history_digest
                and history.private_physical_digest == replay.private_physical_digest
                and (history.physical_key, history.first_observation_key, history.second_exogenous_key)
                == (replay.physical_key, replay.first_observation_key, replay.second_exogenous_key)
            )
            if not replay_ok:
                failures.append(f"{trial_id}:history_replay")
            if len({history.physical_key, history.first_observation_key,
                    history.second_exogenous_key}) != 3:
                failures.append(f"{trial_id}:exogenous_key_collision")
            evaluated = evaluate_history_matrix(history, check_positions=positions,
                                                geometry=geometry())
            if len(evaluated) != 8 or {(row.mode, row.branch) for row in evaluated} != {
                (mode, branch) for mode in MODES for branch in SCHEDULES
            }:
                failures.append(f"{trial_id}:arm_matrix")
            # Reconstruct only the public schedule transcript for a mechanism
            # diagnostic.  It is never used to choose histories or tune rates.
            resolved: dict[str, bool] = {}
            try:
                matrix = run_e1_policy_matrix(
                    trial_id=trial_id, record=history.record, check_positions=positions,
                    geometry=geometry(), size=2,
                )
                for mode_run in matrix.modes:
                    for branch in SCHEDULES:
                        calls = sorted(
                            (item for item in mode_run.invocations if item.branch == branch),
                            key=lambda item: item.report.round,
                        )
                        deferred = False
                        success = False
                        for item in calls:
                            if item.flux_action.status == "defer_temporal_boundary":
                                deferred = True
                            elif deferred and item.flux_action.status == "action":
                                success = True
                        resolved[f"{mode_run.mode}/{branch}"] = success
            except (AssertionError, RuntimeError, ValueError) as error:
                failures.append(f"{trial_id}:public_schedule_diagnostic:{type(error).__name__}")
            detectors = int(history.record.syndrome_detectors.sum())
            heralds = int((history.public_herald_readout != "none").sum())
            summaries.append({"trial_id": trial_id, "cell_id": cell["id"],
                              "master_seed": master_seed, "history_digest": history.history_digest,
                              "physical_key": history.physical_key,
                              "first_observation_key": history.first_observation_key,
                              "second_exogenous_key": history.second_exogenous_key,
                              "detector_event_count": detectors, "herald_event_count": heralds,
                              "resolved_by_arm": resolved, "history_replay_passed": replay_ok})
            for evaluation in evaluated:
                payload = asdict(evaluation)
                payload.update({"cell_id": cell["id"], "cell_index": cell_index,
                                "history_index": history_index, "master_seed": master_seed,
                                "history_digest": history.history_digest,
                                "physical_key": history.physical_key,
                                "first_observation_key": history.first_observation_key,
                                "second_exogenous_key": history.second_exogenous_key,
                                "detector_event_count": detectors, "herald_event_count": heralds,
                                "resolved_prior_handoff": resolved.get(f"{evaluation.mode}/{evaluation.branch}", False)})
                rows.append(payload)
                if not evaluation.denominator_included or (evaluation.status == "failed_closed" and not evaluation.logical_failure):
                    failures.append(f"{trial_id}:unconditional_loss")
        if cap_failure:
            break

    design = manifest["matched_design"]
    if len(summaries) != design["total_histories"]:
        failures.append("history_count")
    if len(rows) != design["total_arm_evaluations"]:
        failures.append("arm_count")
    if len({(row["trial_id"], row["mode"], row["branch"]) for row in rows}) != len(rows):
        failures.append("duplicate_arm_key")
    zero_rows = [row for row in rows if row["cell_id"] == "zero_control"]
    if len(zero_rows) != 128 or any(row["logical_failure"] or row["status"] != "scored" for row in zero_rows):
        failures.append("zero_control_logical_failure")
    if any(row["detector_event_count"] or row["herald_event_count"] for row in zero_rows):
        failures.append("zero_control_public_event")

    event_gates: dict[str, Any] = {}
    stochastic_ids = {cell["id"] for cell in design["cells"][1:]}
    for cell_id in stochastic_ids:
        cell_summaries = [row for row in summaries if row["cell_id"] == cell_id]
        nonempty = sum(row["detector_event_count"] > 0 for row in cell_summaries)
        real_action = {
            f"{mode}/{branch}": sum(
                row["unique_commit_count"] > 0
                for row in rows if row["cell_id"] == cell_id
                and row["mode"] == mode and row["branch"] == branch
            ) for mode in MODES for branch in SCHEDULES[:3]
        }
        passed = nonempty >= 16 and all(value >= 8 for value in real_action.values())
        event_gates[cell_id] = {"nonempty_detector_histories": nonempty,
                                "real_action_histories_per_online_arm": real_action,
                                "passed": passed}
        if not passed:
            failures.append(f"{cell_id}:event_resolution_gate")
    resolved_by_mode = {
        mode: sum(any(summary["resolved_by_arm"].get(f"{mode}/{branch}", False)
                      for branch in SCHEDULES[:3])
                  for summary in summaries if summary["cell_id"] in stochastic_ids)
        for mode in MODES
    }
    if any(count < 8 for count in resolved_by_mode.values()):
        failures.append("resolved_handoff_gate")
    failed_closed = {
        cell["id"]: {
            "count": sum(row["status"] == "failed_closed" for row in rows if row["cell_id"] == cell["id"]),
            "reasons": sorted({row["failure_reason"] for row in rows
                               if row["cell_id"] == cell["id"] and row["failure_reason"]}),
        } for cell in design["cells"]
    }
    path_tmp = ROWS.with_suffix(ROWS.suffix + ".tmp")
    path_tmp.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    os.replace(path_tmp, ROWS)
    if ROWS.stat().st_size >= 50 * 1024**2:
        failures.append("output_size_cap")
    status = "production_integrity_passed_bootstrap_pending" if not failures and not cap_failure else "censored"
    result = {
        "schema_version": 1, "phase": "J6B production integrity", "status": status,
        "manifest": str(MANIFEST.relative_to(ROOT)), "manifest_sha256": digest(MANIFEST),
        "runner_sha256": digest(Path(__file__)), "preflight_sha256": digest(PREFLIGHT),
        "production_release_passed": release, "provenance_passed": provenance_ok,
        "provenance": checks, "runtime": runtime,
        "integrity_passed": status != "censored", "integrity_failures": sorted(set(failures)),
        "cap_failure": cap_failure, "event_gates": event_gates,
        "resolved_handoff_histories_by_mode": resolved_by_mode,
        "failed_closed_rows": failed_closed,
        "counters": {"production_histories_generated": len(summaries),
                     "production_arm_evaluations": len(rows), "bootstrap_replicates": 0},
        "resource_use": {"wall_seconds": round(time.monotonic() - started_wall, 5),
                         "cpu_seconds": round(time.process_time() - started_cpu, 5),
                         "peak_rss_bytes": rss_bytes(), "raw_rows_bytes": ROWS.stat().st_size},
        "raw_rows": str(ROWS.relative_to(ROOT)), "raw_rows_sha256": digest(ROWS),
        "claim_boundary": "Integrity-only finite pilot; no paired risk or schedule advantage inferred before registered uncertainty analysis.",
        "next_action": "Run the registered whole-history paired analysis once" if status != "censored" else "Stop censored; no bootstrap or risk interpretation",
    }
    atomic_json(ANALYSIS, result)
    print(json.dumps({"status": status, "integrity_failures": result["integrity_failures"],
                      "counters": result["counters"]}))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    outcome = run_production() if args.production else run_preflight()
    if outcome["status"] == "censored":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
