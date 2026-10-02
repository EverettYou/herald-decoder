"""Post-hoc, registered replay of eight immutable J6B histories; no new seeds."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from d4_integrated_history import (
    evaluate_history_matrix,
    generate_integrated_d4_history,
    provide_action_conditioned_second_record,
)
from d4_matching import edge_chain_boundary
from d4_spatial_policy import D4TemporalBoundaryActionV1, paper_periodic_honeycomb
from e1_schedule_integration import run_e1_policy_matrix
from generic_history import GenericNoiseParameters
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6b-d3-selected-frozen-history-replay-2026-09-23.json"
RESULT = LAB / "results/j6b-d3-selected-frozen-history-replay-2026-09-23.json"
BRANCHES = ("immediate", "fixed_delay_1", "jit_lyons_brown", "offline_full_history")
MODES = ("syndrome_only", "heralded")
PRIVATE_PUBLIC_KEYS = {
    "physical_edge_states", "transition_edge_faults", "private_physical_digest",
    "active_vertices", "entanglement_pairs", "internal_second_record",
    "terminal_residual", "logical_failure", "physical_winding", "union_winding",
    "charge_winding", "_physical_edges", "_flux_correction_edges",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry() -> AbsorberGeometry:
    value = AbsorberGeometry()
    value.open(
        AbsorbingRegion(
            "j6b-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 4)), 0
        ),
        current_round=0,
    )
    return value


def public_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from public_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from public_keys(item)


def row_kind(row: dict) -> str | None:
    if row["status"] == "scored" and row["logical_failure"] and row["terminal_residual"]:
        count = row["unique_commit_count"]
        return "residual_no_commit" if count == 0 else "residual_one_commit" if count == 1 else "residual_multi_commit"
    if row["status"] == "scored" and not row["logical_failure"] and not row["terminal_residual"]:
        return "scored_success_control"
    return None


def freeze_rows(contract: dict):
    rows = [json.loads(line) for line in (LAB / contract["frozen_inputs"]["j6b_rows"]["path"]).read_text().splitlines()]
    if len(rows) != 2176:
        raise AssertionError("frozen raw row count changed")
    by_key = {(row["trial_id"], row["mode"], row["branch"]): row for row in rows}
    if len(by_key) != len(rows):
        raise AssertionError("duplicate frozen arm key")
    for case in contract["frozen_selection"]["case_order"]:
        candidates = sorted(
            (row for row in rows if row["cell_id"] == case["cell_id"]
             and row["mode"] == "syndrome_only" and row["branch"] == "jit_lyons_brown"
             and row_kind(row) == case["stratum"]),
            key=lambda row: row["history_index"],
        )
        if not candidates or candidates[0]["history_index"] != case["history_index"] or candidates[0]["trial_id"] != case["trial_id"]:
            raise AssertionError(f"frozen selection drift: {case['trial_id']}")
    return by_key


def trace_case(contract: dict, case: dict, frozen: dict):
    manifest = json.loads((LAB / contract["frozen_inputs"]["j6b_manifest"]["path"]).read_text())
    cells = manifest["matched_design"]["cells"]
    cell_index = next(i for i, cell in enumerate(cells) if cell["id"] == case["cell_id"])
    cell = cells[cell_index]
    seed = 923_240_000 + 100_000 * cell_index + case["history_index"]
    p = cell["rates"]
    parameters = GenericNoiseParameters(p["p_data"], p["p_syndrome"], p["p_fp"], p["p_fn"], p["p_confuse"])
    history = generate_integrated_d4_history(trial_id=case["trial_id"], master_seed=seed, parameters=parameters)
    lattice = paper_periodic_honeycomb(2)
    positions = tuple((site,) for site in range(lattice.vertex_count))
    expected = frozen[(case["trial_id"], "syndrome_only", "jit_lyons_brown")]
    for name in ("history_digest", "physical_key", "first_observation_key", "second_exogenous_key"):
        if getattr(history, name) != expected[name]:
            raise AssertionError(f"frozen history/key mismatch: {case['trial_id']}:{name}")
    if seed != expected["master_seed"] or cell_index != expected["cell_index"]:
        raise AssertionError("frozen seed/cell index mismatch")

    replay = evaluate_history_matrix(history, check_positions=positions, geometry=geometry())
    if len(replay) != 8:
        raise AssertionError("replay did not yield eight unconditional arms")
    for arm in replay:
        original = frozen[(case["trial_id"], arm.mode, arm.branch)]
        obtained = json.loads(json.dumps(asdict(arm)))
        if any(obtained[key] != original[key] for key in obtained):
            raise AssertionError(f"exact frozen arm replay mismatch: {case['trial_id']}:{arm.mode}/{arm.branch}")
        if not arm.denominator_included or (arm.status == "failed_closed" and not arm.logical_failure):
            raise AssertionError("unconditional denominator/loss changed")

    matrix = run_e1_policy_matrix(
        trial_id=history.trial_id, record=history.record,
        check_positions=positions, geometry=geometry(), size=2,
    )
    if matrix.history_digest != history.history_digest:
        raise AssertionError("public history digest mismatch")
    physical_boundaries = [edge_chain_boundary(lattice, state.astype(np.uint8)).astype(bool) for state in history.physical_edge_states]
    public_readouts = history.record.syndrome_readout.astype(bool)
    mismatch_rounds = [i for i in range(5) if not np.array_equal(physical_boundaries[i], public_readouts[i])]
    rounds = [{
        "round": i,
        "private_physical_edges": np.flatnonzero(history.physical_edge_states[i]).astype(int).tolist(),
        "private_physical_syndrome": np.flatnonzero(physical_boundaries[i]).astype(int).tolist(),
        "public_syndrome_readout": np.flatnonzero(public_readouts[i]).astype(int).tolist(),
        "public_detector_events_since_previous_round": [] if i == 0 else np.flatnonzero(history.record.syndrome_detectors[i-1]).astype(int).tolist(),
        "public_herald_sites": np.flatnonzero(history.public_herald_readout[i] != "none").astype(int).tolist(),
        "physical_transition_edges": [] if i == 0 else np.flatnonzero(history.transition_edge_faults[i-1]).astype(int).tolist(),
    } for i in range(5)]
    arms = []
    for mode_run in matrix.modes:
        if mode_run.mode not in MODES:
            raise AssertionError("unregistered mode")
        for branch in BRANCHES:
            original = frozen[(case["trial_id"], mode_run.mode, branch)]
            calls = [item for item in mode_run.invocations if item.branch == branch]
            if len(calls) != original["invocation_count"]:
                raise AssertionError("public invocation count mismatch")
            by_round = {}
            for item in calls:
                public = {"request": item.policy_request.to_dict(), "action": item.flux_action.to_dict()}
                if set(public_keys(public)) & PRIVATE_PUBLIC_KEYS:
                    raise AssertionError("private truth leaked into public request/action")
                by_round.setdefault(item.report.round, []).append(item)
            canonical = []
            for round_index, group in sorted(by_round.items()):
                if len({(item.flux_action.status, tuple(item.flux_action.correction_edges)) for item in group}) != 1:
                    raise AssertionError("same-round public action conflict")
                canonical.append(min(group, key=lambda item: item.schedule_request_digest))
            commit_calls = [item for item in canonical if not isinstance(item.flux_action, D4TemporalBoundaryActionV1)]
            if original["status"] == "scored" and [item.report.round for item in commit_calls] != original["commit_rounds"]:
                raise AssertionError("reconstructed physical commit ledger mismatch")
            completions = []
            for item in commit_calls:
                second = provide_action_conditioned_second_record(history, item)
                if second.flux_action_digest != item.flux_action.action_digest or second.decision_round != item.report.round:
                    raise AssertionError("unbound second public record")
                if set(public_keys(second.public_dict())) & PRIVATE_PUBLIC_KEYS or set(second.public_charge_action) != {"blue", "green"}:
                    raise AssertionError("second public record leaks relation or omits charge action")
                completions.append(second.public_completion_digest)
            if original["status"] == "scored" and completions != original["public_completion_digests"]:
                raise AssertionError("action-conditioned public completion replay mismatch")
            latest = np.zeros(lattice.edge_count, dtype=np.uint8)
            current_commit = None
            residual_by_round = []
            for round_index in range(5):
                for item in commit_calls:
                    if item.report.round == round_index:
                        latest[:] = 0
                        latest[list(item.flux_action.correction_edges)] = 1
                        current_commit = round_index
                residual = edge_chain_boundary(
                    lattice, history.physical_edge_states[round_index].astype(np.uint8) ^ latest
                )
                residual_by_round.append(np.flatnonzero(residual).astype(int).tolist())
            last_commit = None if not commit_calls else commit_calls[-1].report.round
            final_residual = bool(residual_by_round[-1])
            if original["status"] == "scored" and final_residual != original["terminal_residual"]:
                raise AssertionError("independent final residual/frame mismatch")
            later_physical = bool(last_commit is not None and np.any(history.transition_edge_faults[last_commit:]))
            mismatch_at_commit = bool(last_commit is not None and last_commit in mismatch_rounds)
            last_commit_residual = bool(last_commit is not None and residual_by_round[last_commit])
            arms.append({
                "mode": mode_run.mode, "branch": branch,
                "stored_status": original["status"], "stored_logical_failure": original["logical_failure"],
                "stored_terminal_residual": original["terminal_residual"],
                "last_commit_round": last_commit,
                "physical_transition_after_last_commit": later_physical,
                "private_public_readout_mismatch_at_last_commit": mismatch_at_commit,
                "residual_immediately_after_last_commit": last_commit_residual,
                "first_nonzero_residual_round": next((i for i, values in enumerate(residual_by_round) if values), None),
                "final_residual_endpoints": residual_by_round[-1],
                "residual_endpoints_by_round": residual_by_round,
                "public_invocations": [{
                    "round": item.report.round, "status": item.flux_action.status,
                    "schedule_request_digest": item.schedule_request_digest,
                    "public_report_digest": item.report.report_digest,
                    "public_action_digest": item.flux_action.action_digest,
                    "public_correction_edges": list(item.flux_action.correction_edges),
                } for item in canonical],
            })
    return {
        "trial_id": case["trial_id"], "cell_id": case["cell_id"], "stratum": case["stratum"],
        "master_seed": seed, "history_digest": history.history_digest,
        "first_private_public_readout_mismatch_round": None if not mismatch_rounds else mismatch_rounds[0],
        "rounds": rounds, "arms": arms,
    }


def main() -> int:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    result = {
        "contract_sha256": sha(CONTRACT), "status": "censored", "reason": None,
        "prior_censored_attempt": {
            "reason": "IndexError:index 4 is out of bounds for axis 0 with size 4",
            "stage": "diagnostic round-table construction before any case was accepted",
            "corrective_change": "Index four adjacent-round detector rows by readout round minus one; use the exact original J6B absorber region name. Frozen scientific inputs, selection, arm set and scorer unchanged.",
        },
        "new_stochastic_seeds": 0, "new_unique_production_histories": 0,
        "new_unique_production_arm_rows": 0, "new_bootstrap_replicates": 0,
        "selected_replayed_histories": 0, "selected_replayed_arm_rows": 0,
        "cases": [],
    }
    try:
        for item in contract["frozen_inputs"].values():
            if sha(LAB / item["path"]) != item["sha256"]:
                raise AssertionError(f"frozen input changed: {item['path']}")
        frozen = freeze_rows(contract)
        cases = [trace_case(contract, case, frozen) for case in contract["frozen_selection"]["case_order"]]
        if len(cases) != 8 or len({case["trial_id"] for case in cases}) != 8 or sum(len(case["arms"]) for case in cases) != 64:
            raise AssertionError("registered replay cap or branch coverage mismatch")
        for item in contract["frozen_inputs"].values():
            if sha(LAB / item["path"]) != item["sha256"]:
                raise AssertionError(f"frozen input changed after replay: {item['path']}")
        result["cases"] = cases
        result["selected_replayed_histories"] = len(cases)
        result["selected_replayed_arm_rows"] = sum(len(case["arms"]) for case in cases)
        result["status"] = "passed_selected_case_replay_only"
    except Exception as error:
        result["reason"] = f"{type(error).__name__}:{error}"
    result["elapsed_seconds"] = round(time.monotonic() - started, 4)
    result["claim_boundary"] = contract["claim_boundary"]
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if result["elapsed_seconds"] > contract["budget"]["max_wall_seconds"] or len(output.encode()) > contract["budget"]["max_result_mib"] * 1024**2:
        result.update({"status": "censored", "reason": "registered time/output cap exceeded", "cases": [], "selected_replayed_histories": 0, "selected_replayed_arm_rows": 0})
        output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    RESULT.write_text(output)
    print(json.dumps({"status": result["status"], "reason": result["reason"],
                      "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["status"] == "passed_selected_case_replay_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
