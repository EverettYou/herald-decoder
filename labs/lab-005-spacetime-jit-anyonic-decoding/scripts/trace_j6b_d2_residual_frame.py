"""Registered five-history J6B-D2 deterministic public-interface trace."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from d4_integrated_history import (
    build_integrated_d4_history_from_draws,
    evaluate_schedule_arm,
    provide_action_conditioned_second_record,
)
from d4_matching import edge_chain_boundary
from d4_spatial_policy import D4TemporalBoundaryActionV1, paper_periodic_honeycomb
from e1_schedule_integration import run_e1_policy_matrix
from generic_history import GenericNoiseParameters
from lyons_absorber import AbsorberGeometry, AbsorbingRegion, SpacetimeBox


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json"
RESULT = LAB / "results/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json"
BRANCHES = ("immediate", "fixed_delay_1", "jit_lyons_brown", "offline_full_history")
MODES = ("syndrome_only", "heralded")
FORBIDDEN_PUBLIC_KEYS = {
    "physical_edge_states", "transition_edge_faults", "private_physical_digest",
    "active_vertices", "entanglement_pairs", "internal_second_record",
    "terminal_residual", "logical_failure", "physical_winding", "union_winding",
    "charge_winding", "_physical_edges", "_flux_correction_edges",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def geometry() -> AbsorberGeometry:
    region = AbsorberGeometry()
    region.open(
        AbsorbingRegion(
            "j6b-d2-boundary", "spatial_boundary", SpacetimeBox((1, 0), (1, 4)), 0
        ),
        current_round=0,
    )
    return region


def make_history(fixture: dict):
    lattice = paper_periodic_honeycomb(2)
    faults = np.zeros((4, lattice.edge_count), dtype=bool)
    readout = np.zeros((5, lattice.vertex_count), dtype=bool)
    for round_index, edge in fixture["transition_faults"]:
        faults[round_index, edge] = True
    for round_index, vertex in fixture["syndrome_readout_flips"]:
        readout[round_index, vertex] = True
    return build_integrated_d4_history_from_draws(
        trial_id="j6b-d2-fixed",
        master_seed=1,
        parameters=GenericNoiseParameters(0.0, 0.0, 0.0, 0.0, 0.0),
        physical_key=key("physical"),
        first_observation_key=key("first"),
        second_exogenous_key=key("second"),
        transition_edge_faults=faults,
        syndrome_measurement_faults=readout,
        herald_uniforms=np.full((5, lattice.vertex_count), 0.5),
        first_observation_seeds=(10, 11, 12, 13, 14),
    )


def public_keys(value):
    if isinstance(value, dict):
        for name, item in value.items():
            yield name
            yield from public_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from public_keys(item)


def trace_history(fixture: dict):
    history = make_history(fixture)
    lattice = paper_periodic_honeycomb(2)
    matrix = run_e1_policy_matrix(
        trial_id=history.trial_id,
        record=history.record,
        check_positions=tuple((site,) for site in range(lattice.vertex_count)),
        geometry=geometry(),
        size=2,
    )
    if matrix.history_digest != history.history_digest:
        raise AssertionError("public history digest mismatch")
    arms = []
    causal_prefixes = []
    for mode_run in matrix.modes:
        if mode_run.mode not in MODES:
            raise AssertionError("unregistered mode")
        for branch in BRANCHES:
            invocations = tuple(x for x in mode_run.invocations if x.branch == branch)
            row = evaluate_schedule_arm(
                history, mode=mode_run.mode, branch=branch, invocations=invocations
            )
            if not row.denominator_included or row.trial_id != history.trial_id:
                raise AssertionError("unconditional arm denominator or trial changed")
            by_round = {}
            for item in invocations:
                public = {"request": item.policy_request.to_dict(),
                          "action": item.flux_action.to_dict()}
                if set(public_keys(public)) & FORBIDDEN_PUBLIC_KEYS:
                    raise AssertionError("private field entered public request/action")
                if branch != "offline_full_history" and item.report.round <= 3:
                    causal_prefixes.append((mode_run.mode, branch, item.report.round,
                                            item.schedule_request_digest,
                                            item.report.report_digest,
                                            item.flux_action.action_digest))
                by_round.setdefault(item.report.round, []).append(item)
            commits = []
            for round_index, group in sorted(by_round.items()):
                status = {item.flux_action.status for item in group}
                if len(status) != 1:
                    raise AssertionError("conflicting same-round public actions")
                actions = {tuple(item.flux_action.correction_edges) for item in group}
                if len(actions) != 1:
                    raise AssertionError("conflicting same-round correction")
                if not isinstance(group[0].flux_action, D4TemporalBoundaryActionV1):
                    commits.append((round_index, group[0]))
                    completion = provide_action_conditioned_second_record(history, group[0])
                    if completion.flux_action_digest != group[0].flux_action.action_digest:
                        raise AssertionError("unbound second public record")
                    if set(public_keys(completion.public_dict())) & FORBIDDEN_PUBLIC_KEYS:
                        raise AssertionError("private field entered second public record")
                    if set(completion.public_charge_action) != {"blue", "green"}:
                        raise AssertionError("relation-free public charge action missing")
            if row.status == "scored":
                if row.unique_commit_count != len(commits) or row.commit_rounds != tuple(x[0] for x in commits):
                    raise AssertionError("physical commit ledger mismatch")
                correction = np.zeros(lattice.edge_count, dtype=np.uint8)
                if commits:
                    correction[list(commits[-1][1].flux_action.correction_edges)] = 1
                physical = history.physical_edge_states[-1].astype(np.uint8)
                oracle = bool(np.any(edge_chain_boundary(lattice, physical ^ correction)))
                if row.terminal_residual != oracle:
                    raise AssertionError("terminal residual disagrees with final physical XOR latest public frame")
                if row.logical_failure != bool(row.physical_winding or row.union_winding or row.charge_winding or oracle):
                    raise AssertionError("Boolean-union loss mismatch")
            elif row.status != "failed_closed" or not row.logical_failure:
                raise AssertionError("unknown or uncounted terminal outcome")
            arms.append({
                "mode": mode_run.mode, "branch": branch, "status": row.status,
                "logical_failure": row.logical_failure,
                "invocation_count": row.invocation_count,
                "commit_rounds": list(row.commit_rounds),
                "latest_public_correction_edges": list(commits[-1][1].flux_action.correction_edges) if commits else [],
                "physical_winding": row.physical_winding,
                "union_winding": row.union_winding,
                "charge_winding": row.charge_winding,
                "terminal_residual": row.terminal_residual,
                "failure_reason": row.failure_reason,
            })
    if len(arms) != 8 or len({(a["mode"], a["branch"]) for a in arms}) != 8:
        raise AssertionError("not exactly eight public arm rows")
    return {
        "fixture_id": fixture["id"], "visible_history_digest": history.history_digest,
        "final_physical_edges": np.flatnonzero(history.physical_edge_states[-1]).astype(int).tolist(),
        "causal_prefixes": sorted(causal_prefixes), "arms": arms,
    }


def main() -> int:
    started = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    result = {"contract_sha256": sha(CONTRACT), "status": "censored", "reason": None,
              "new_stochastic_histories": 0, "new_production_arm_evaluations": 0,
              "bootstrap_replicates": 0, "fixtures": []}
    try:
        for path, expected in contract["frozen_inputs"].items():
            if sha(LAB / path) != expected:
                raise AssertionError(f"frozen input changed: {path}")
        fixtures = [trace_history(fixture) for fixture in contract["fixture_matrix"]]
        replay = [trace_history(fixture) for fixture in contract["fixture_matrix"]]
        if fixtures != replay:
            raise AssertionError("full public arm matrix is not replay-identical")
        if fixtures[1]["causal_prefixes"] != fixtures[3]["causal_prefixes"]:
            raise AssertionError("late physical fault changed earlier causal decisions")
        if len(fixtures) != 5 or sum(len(x["arms"]) for x in fixtures) != 40:
            raise AssertionError("fixture or arm budget mismatch")
        for path, expected in contract["frozen_inputs"].items():
            if sha(LAB / path) != expected:
                raise AssertionError(f"frozen input changed after execution: {path}")
        result["fixtures"] = fixtures
        result["status"] = "passed_deterministic_interface_only"
    except Exception as error:
        result["reason"] = f"{type(error).__name__}:{error}"
    result["elapsed_seconds"] = round(time.monotonic() - started, 4)
    if result["elapsed_seconds"] > contract["budget"]["runtime_seconds_max"]:
        result["status"] = "censored"
        result["reason"] = "runtime cap exceeded"
    result["claim_boundary"] = (
        "Deterministic public/private interface consistency only; no J6B risk rescore, "
        "stochastic mechanism attribution, JIT benefit or threshold."
    )
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "reason": result["reason"],
                      "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["status"] == "passed_deterministic_interface_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
