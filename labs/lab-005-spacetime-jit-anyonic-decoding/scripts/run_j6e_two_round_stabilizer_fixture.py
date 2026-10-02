"""Exact L=2 D4 red-X/postflux stabilizer-sector fixture, without sampling."""

from __future__ import annotations

import hashlib
from itertools import product
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
LAB004 = ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts"
sys.path.insert(0, str(LAB004))

from d4_honeycomb import (  # noqa: E402
    BLUE, GREEN, generate_loop_constraints, paper_periodic_honeycomb,
)
from d4_matching import edge_chain_boundary  # noqa: E402
from d4_observation import evaluate_observation  # noqa: E402
from d4_postflux import (  # noqa: E402
    accumulate_postflux_constraints,
    infer_periodic_postflux_relations,
)


CONTRACT = LAB / "manifests/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json"
RESULT = LAB / "results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def full_first_support(lattice, physical):
    flux = edge_chain_boundary(lattice, physical)
    degrees = np.zeros(lattice.vertex_count, dtype=np.int64)
    for edge in np.flatnonzero(physical):
        for vertex in lattice.edge_vertices[edge]:
            degrees[int(vertex)] += 1
    internal = tuple(int(v) for v in np.flatnonzero(degrees == 2))
    rows = []
    for bits in product((0, 1), repeat=len(internal)):
        charge = np.zeros(lattice.vertex_count, dtype=np.int64)
        charge[list(internal)] = bits
        validation = evaluate_observation(
            lattice.edge_vertices, physical, flux, charge
        )
        assert validation.allowed and validation.internal_vertices == internal
        rows.append({
            "public": {"flux": flux.astype(int).tolist(), "charge": charge.tolist()},
            "first_probability": validation.probability,
        })
    assert sum(row["first_probability"] for row in rows) == 1.0
    return rows


def exact_postflux(lattice, physical, correction):
    relations = infer_periodic_postflux_relations(lattice, physical, correction)
    active = relations.active_vertices
    records = []
    components = None
    for bits in product((0, 1), repeat=len(active)):
        private_charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
        private_charge[list(active)] = bits
        check = accumulate_postflux_constraints(
            lattice.vertex_count, active, relations.entanglement_pairs, private_charge
        )
        components = check.components
        if check.allowed:
            charge = np.zeros(lattice.vertex_count, dtype=np.int64)
            charge[list(active)] = bits
            records.append({
                "charge": charge.tolist(),
                "vacuum": (1 - charge).tolist(),
            })
    assert components is not None and records
    assert all(
        sum(record["charge"][v] for v in component) % 2 == 0
        for component in components for record in records
    )
    # Exact orthogonal-projector algebra: P_r P_s = delta_{r,s} P_r.
    # This proves repeatability after the first postflux measurement, not a
    # physical joint law with the earlier pre-correction herald measurement.
    patterns = [tuple(record["charge"]) for record in records]
    assert len(set(patterns)) == len(records)
    repeat_kernel = [
        [int(first == second) for second in patterns] for first in patterns
    ]
    assert all(sum(row) == 1 for row in repeat_kernel)
    assert all(repeat_kernel[i][i] == 1 for i in range(len(records)))
    return {
        "private_active_vertices": list(active),
        "private_parity_components": [list(component) for component in components],
        "public_full_binary_records": records,
        "postflux_support_size": len(records),
        "round_2_ideal_repeat_kernel": repeat_kernel,
    }


def run():
    start = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    pinned = contract["upstream"]
    paths = {
        "j6d_result": LAB / "results/j6d-projector-state-sufficiency-2026-09-24.json",
        "d4_honeycomb": LAB004 / "d4_honeycomb.py",
        "d4_matching": LAB004 / "d4_matching.py",
        "d4_postflux": LAB004 / "d4_postflux.py",
        "d4_observation": LAB004 / "d4_observation.py",
    }
    hashes = {key: sha(path) == pinned[f"{key}_sha256"] for key, path in paths.items()}
    if not all(hashes.values()):
        raise ValueError(f"pinned source mismatch: {hashes}")
    upstream = json.loads(paths["j6d_result"].read_text())
    if upstream.get("status") != "passed_source_sufficiency_audit_only":
        raise ValueError("J6D is not accepted")
    lattice = paper_periodic_honeycomb(2)
    assert (lattice.vertex_count, lattice.edge_count) == (24, 36)
    candidate = None
    for center in range(lattice.vertex_count):
        if int(lattice.vertex_colors[center]) != GREEN:
            continue
        incident = sorted(
            int(edge) for edge, endpoints in enumerate(lattice.edge_vertices)
            if center in endpoints
        )
        for left, right in product(incident, repeat=2):
            if left >= right:
                continue
            endpoints = sorted(
                ({int(v) for v in lattice.edge_vertices[left]} |
                 {int(v) for v in lattice.edge_vertices[right]}) - {center}
            )
            if len(endpoints) == 2 and all(int(lattice.vertex_colors[v]) == BLUE for v in endpoints):
                candidate = (center, left, right, endpoints)
                break
        if candidate is not None:
            break
    assert candidate is not None
    center, first_edge, second_edge, endpoints = candidate
    cases = {}
    for name, edges in (
        ("zero", ()), ("single_edge", (first_edge,)),
        ("two_edge_path", (first_edge, second_edge)),
    ):
        physical = np.zeros(lattice.edge_count, dtype=np.uint8)
        physical[list(edges)] = 1
        topology = generate_loop_constraints(lattice, physical)
        assert all(component.homologically_trivial for component in topology.components)
        first = full_first_support(lattice, physical)
        branches = {}
        for action in ("defer", "matching_red_x"):
            correction = np.zeros(lattice.edge_count, dtype=np.uint8)
            if action == "matching_red_x":
                correction[list(edges)] = 1
            residual = physical ^ correction
            flux = edge_chain_boundary(lattice, residual)
            postflux = (
                exact_postflux(lattice, physical, correction)
                if action == "matching_red_x" and edges else None
            )
            branches[action] = {
                "public_action_edges": list(int(i) for i in np.flatnonzero(correction)),
                "private_residual_flux": flux.astype(int).tolist(),
                "postflux_e2": postflux,
            }
            if action == "defer":
                assert postflux is None and np.array_equal(residual, physical)
            else:
                assert not np.any(residual) and not np.any(flux)
        cases[name] = {
            "private_physical_edges": list(edges),
            "first_public_full_binary_support": first,
            "branches": branches,
        }
    two = cases["two_edge_path"]["branches"]["matching_red_x"]["postflux_e2"]
    assert two is not None
    assert sorted(map(len, two["private_parity_components"])) == [1, 2]
    assert two["postflux_support_size"] == 2
    assert all(row["charge"][center] == 0 for row in two["public_full_binary_records"])
    assert len(cases["two_edge_path"]["first_public_full_binary_support"]) == 2
    one = cases["single_edge"]["branches"]["matching_red_x"]["postflux_e2"]
    assert one is not None and one["postflux_support_size"] == 1
    assert time.monotonic() - start < contract["budget"]["max_cpu_seconds"]
    return {
        "schema_version": 1,
        "id": contract["id"],
        "status": "passed_source_bounded_stabilizer_sector_only",
        "contract_sha256": sha(CONTRACT),
        "upstream_hash_checks": hashes,
        "geometry": {"size": 2, "vertices": 24, "edges": 36,
                     "selected_green_center": center,
                     "selected_two_edge_path": [first_edge, second_edge],
                     "selected_blue_endpoints": endpoints},
        "exact_cases": cases,
        "interpretation": {
            "established": "Exact red-X flux-chain action limits, postflux same-color parity support, and ideal unchanged-projector repeatability on the L=2 geometry.",
            "unresolved": "The joint distribution of first herald outcome and post-correction charge outcome, action-conditioned hidden state under arbitrary new faults, and a full D4 density-channel law are not fixed by this fixture.",
            "next_gate": "Derive an explicit first-measurement/correction/postflux conditional instrument on this geometry, including density or stabilizer-state update, before reducing to a numeric cross-round kernel or integrating the five-round caller."
        },
        "stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "cpu_seconds": round(time.monotonic() - start, 6),
    }


if __name__ == "__main__":
    RESULT.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n")
