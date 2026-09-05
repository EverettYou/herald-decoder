#!/usr/bin/env python3
"""Run the R6AF structural preflight without allocating production samples."""

from __future__ import annotations

import argparse
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import (
    decode_public_postflux_charges,
    public_postflux_charge_record,
    score_public_postflux_charge_action,
)
from d4_honeycomb import paper_periodic_honeycomb
from d4_matching import published_herald_weights, syndrome_only_weights
from d4_pipeline import decode_physical_error, sample_postflux_charge_outcomes
from d4_postflux import (
    accumulate_postflux_constraints,
    infer_periodic_postflux_relations,
)
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = LAB_DIR / "results/r6af-two-stage-public-charge-preflight-2026-09-01.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing prerequisite: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _arm(lattice, physical, first_charge, mode: str, second_seed: int) -> dict:
    weights = (
        syndrome_only_weights(lattice)
        if mode == "O0"
        else published_herald_weights(lattice, first_charge)
    )
    flux = decode_and_score_flux_recovery(lattice, physical, weights)
    if flux.logical_error:
        return {
            "mode": mode,
            "status": "flux_union_logical_failure",
            "correction_edges": [int(x) for x in np.flatnonzero(flux.correction)],
            "union_logical_error": True,
        }
    relations = infer_periodic_postflux_relations(lattice, physical, flux.correction)
    internal_second = sample_postflux_charge_outcomes(
        lattice.vertex_count, relations, seed=second_seed
    )
    public_second = public_postflux_charge_record(internal_second)
    support = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        internal_second,
    )
    charge_action = decode_public_postflux_charges(lattice, public_second)
    charge = score_public_postflux_charge_action(
        lattice,
        relations,
        public_second,
        charge_action,
        flux_components_homologically_trivial=True,
    )
    return {
        "mode": mode,
        "status": "decoded",
        "correction_edges": [int(x) for x in np.flatnonzero(flux.correction)],
        "union_logical_error": bool(flux.logical_error),
        "active_vertices": list(relations.active_vertices),
        "relation_pairs": [list(pair) for pair in relations.entanglement_pairs],
        "internal_second_record": [int(x) for x in internal_second],
        "public_second_record": [int(x) for x in public_second],
        "internal_second_record_has_inactive_sentinel": bool(
            np.any(internal_second == -1)
        ),
        "own_action_conditioned_support_allowed": bool(support.allowed),
        "charge_logical_error": bool(charge.logical_error),
        "public_charge_corrections": {
            "blue": [int(x) for x in np.flatnonzero(charge_action.blue.correction)],
            "green": [int(x) for x in np.flatnonzero(charge_action.green.correction)],
        },
        "final_boolean_union_loss": bool(flux.logical_error or charge.logical_error),
    }


def build_preflight() -> dict:
    manifest = _load(
        LAB_DIR
        / "manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json"
    )
    r6ac = _load(
        LAB_DIR / "manifests/r6ac-d4-sublattice-herald-model-audit-2026-08-31.json"
    )
    r6ae = _load(
        LAB_DIR / "manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json"
    )
    p4 = _load(
        LAB_DIR / "results/p4-lab003-d4-channel-equivalence-audit-2026-09-01.json"
    )
    prerequisites = {
        "manifest_registered": manifest.get("status")
        in {
            "registered_preflight_pending",
            "preflight_failed_public_charge_interface",
            "preflight_passed_pilot_pending",
            "preflight_passed_pilot_registration_pending",
            "pilot_registered_execution_pending",
            "pilot_completed_analyzed_no_refinement",
        },
        "corrected_signal_event_table_passed": r6ac.get(
            "signal_only_event_table_gate_passed"
        )
        is True,
        "r6ae_closed_at_cap": r6ae.get("status")
        == "completed_at_registered_cap_no_threshold",
        "p4_cross_lab_comparison_prohibited": p4.get("comparison_allowed") is False,
    }

    lattice = paper_periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[[2, 5, 8, 12, 17, 24, 30, 34]] = 1
    first_seed = 103
    second_seed = 12345
    first = observation_from_error_edges(lattice, physical, seed=first_seed)
    if first.charge_outcomes is None:
        raise RuntimeError("frozen nonwinding fixture lacks a first charge record")
    first_charge = np.asarray(first.charge_outcomes, dtype=np.int64)
    degrees = np.bincount(
        lattice.edge_vertices[physical.astype(bool)].ravel(),
        minlength=lattice.vertex_count,
    )
    arms = {
        mode: _arm(lattice, physical, first_charge, mode, second_seed)
        for mode in ("O0", "O2")
    }

    zero = np.zeros(lattice.edge_count, dtype=np.uint8)
    zero_first = observation_from_error_edges(lattice, zero, seed=first_seed)
    zero_charge = np.asarray(zero_first.charge_outcomes, dtype=np.int64)
    zero_arms = {
        mode: _arm(lattice, zero, zero_charge, mode, second_seed)
        for mode in ("O0", "O2")
    }
    public_transcript = decode_physical_error(
        lattice, zero, mode="heralded", seed=7
    ).public_transcript()
    transcript_text = json.dumps(public_transcript, sort_keys=True)

    full_binary_second = all(
        set(arm.get("public_second_record", ())) <= {0, 1}
        for arm in arms.values()
    )
    charge_signature = tuple(
        inspect.signature(decode_public_postflux_charges).parameters
    )
    hidden_relation_required = "relations" in charge_signature
    o0_public = np.asarray(arms["O0"]["public_second_record"], dtype=np.uint8)
    o0_action = decode_public_postflux_charges(lattice, o0_public)
    o0_weights = syndrome_only_weights(lattice)
    o2_weights = published_herald_weights(lattice, first_charge)
    o0_flux = decode_and_score_flux_recovery(lattice, physical, o0_weights)
    o2_flux = decode_and_score_flux_recovery(lattice, physical, o2_weights)
    o0_relations = infer_periodic_postflux_relations(
        lattice, physical, o0_flux.correction
    )
    o2_relations = infer_periodic_postflux_relations(
        lattice, physical, o2_flux.correction
    )
    wrong_action_support_rejected = False
    try:
        score_public_postflux_charge_action(
            lattice,
            o2_relations,
            o0_public,
            o0_action,
            flux_components_homologically_trivial=True,
        )
    except ValueError as error:
        wrong_action_support_rejected = "outside private support" in str(error)
    gates = {
        "prerequisites": all(prerequisites.values()),
        "first_record_signal_only": set(first_charge.tolist()) <= {0, 1},
        "first_record_has_positive_signal": bool(np.any(first_charge == 1)),
        "ambiguous_zero_present": bool(
            np.any((degrees == 2) & (first_charge == 0))
            and np.any((degrees != 2) & (first_charge == 0))
        ),
        "matched_first_history": True,
        "first_actions_disagree_on_frozen_fixture": arms["O0"].get(
            "correction_edges"
        )
        != arms["O2"].get("correction_edges"),
        "second_channel_is_action_conditioned": arms["O0"].get(
            "active_vertices"
        )
        != arms["O2"].get("active_vertices")
        or arms["O0"].get("relation_pairs") != arms["O2"].get("relation_pairs"),
        "same_second_exogenous_key_used": True,
        "own_support_valid": all(
            arm.get("own_action_conditioned_support_allowed", False)
            for arm in arms.values()
        ),
        "zero_fixture_decodes_without_loss": all(
            arm.get("status") == "decoded"
            and arm.get("final_boolean_union_loss") is False
            for arm in zero_arms.values()
        ),
        "full_binary_public_second_record": full_binary_second,
        "charge_action_excludes_hidden_relations": not hidden_relation_required,
        "wrong_action_support_rejected": wrong_action_support_rejected,
        "public_transcript_excludes_private_truth": not any(
            forbidden in transcript_text
            for forbidden in (
                "physical_error",
                "postflux_relations",
                "active_vertices",
                "effective_error",
                "logical_error",
            )
        ),
        "boolean_union_scorer_explicit": all(
            "final_boolean_union_loss" in arm for arm in arms.values()
        ),
    }
    failed = [name for name, passed in gates.items() if not passed]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failed else "failed_before_sampling",
        "production_sampling_authorized": False,
        "pilot_registration_authorized": not failed,
        "manifest": str(
            (
                LAB_DIR
                / "manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json"
            ).relative_to(LAB_DIR)
        ),
        "prerequisites": prerequisites,
        "fixture": {
            "lattice": "paper_periodic_honeycomb(2)",
            "physical_error_edges": [2, 5, 8, 12, 17, 24, 30, 34],
            "first_observation_seed": first_seed,
            "second_exogenous_seed": second_seed,
            "first_flux_vertices": list(first.flux_vertices),
            "first_signal_record": first_charge.tolist(),
            "physical_degrees": degrees.tolist(),
            "arms": arms,
        },
        "zero_fixture": zero_arms,
        "public_interface_audit": {
            "decode_public_postflux_charges_signature": charge_signature,
            "current_second_record_encoding": "full binary with zero outside hidden active support",
            "registered_public_encoding": "full binary vector with zero outside hidden active support",
            "private_truth_boundary": (
                "Action-conditioned relations and effective chains enter only the "
                "private support validator and logical scorer."
            ),
            "public_transcript_keys": sorted(public_transcript),
        },
        "gates": gates,
        "failed_gates": failed,
        "new_production_trajectories": 0,
        "next_action": (
            "Amend the manifest with the smallest paired O0/O2 finite-size pilot "
            "grid and uncertainty procedure before allocating histories."
        ),
        "claim_boundary": (
            "This structural preflight releases no LER, crossing, threshold, or "
            "cross-lab comparison. A failed public-information gate blocks sampling."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_preflight()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": payload["status"],
                "failed_gates": payload["failed_gates"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
