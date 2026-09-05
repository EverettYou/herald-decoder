#!/usr/bin/env python3
"""Independent R6V replay/audit of the R6U BP zero-failure records.

This deliberately keeps truth outside every decoder call.  It regenerates the
physical chain and public fusion record from R6U's deterministic seeds, then
replays the *stored* correction through an independent Boolean-union homology
traversal.  A separate public-record-only shadow BP replay is also performed
with the fixed-L dense template implementation.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import PeriodicHoneycomb, paper_periodic_honeycomb
from d4_local_bp import build_r6d_dense_template, run_r6d_dense_template
from d4_matching import edge_chain_boundary, decode_flux_syndrome
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import llr_weights, trajectory_seeds

INPUT = LAB_DIR / "results/r6u-d4-native-three-policy-curve-2026-08-30.json"
OUTPUT = LAB_DIR / "results/r6v-r6u-bp-integrity-audit-2026-08-30.json"
REPORT = LAB_DIR / "wiki/records/r6v-r6u-bp-integrity-audit-2026-08-30.md"
BP = "R6D_local_BP_posterior_LLR_MWPM"


def independent_union_has_winding(
    lattice: PeriodicHoneycomb, physical: np.ndarray, correction: np.ndarray
) -> bool:
    """Independent lifted-DSU traversal of Boolean-union components.

    This does not call ``physical_correction_union``, ``classify_*``, or
    ``generate_loop_constraints``: it audits the score used by R6U rather
    than reusing its scorer.
    """
    selected = np.asarray(physical | correction, dtype=np.uint8)
    adjacency = [[] for _ in range(lattice.vertex_count)]
    for edge in np.flatnonzero(selected):
        u, v = (int(x) for x in lattice.edge_vertices[edge])
        adjacency[u].append(int(edge)); adjacency[v].append(int(edge))
    unseen = {v for v, incident in enumerate(adjacency) if incident}
    periods = np.asarray(lattice.period_matrix, dtype=np.int64)
    determinant = int(round(np.linalg.det(periods)))
    while unseen:
        root = min(unseen); stack = [root]; visited = set()
        lift = {root: np.zeros(2, dtype=np.int64)}
        while stack:
            vertex = stack.pop()
            if vertex in visited:
                continue
            visited.add(vertex); unseen.discard(vertex)
            for edge in adjacency[vertex]:
                blue, green = (int(x) for x in lattice.edge_vertices[edge])
                if vertex == blue:
                    neighbour = green; delta = lattice.blue_to_green_displacements[edge]
                else:
                    neighbour = blue; delta = -lattice.blue_to_green_displacements[edge]
                proposal = lift[vertex] + delta
                if neighbour not in lift:
                    lift[neighbour] = proposal; stack.append(neighbour); continue
                discrepancy = proposal - lift[neighbour]
                if not np.any(discrepancy):
                    continue
                # Solve period_matrix @ winding = discrepancy using exact
                # two-by-two Cramer's rule; a nonzero integer solution is a
                # nontrivial torus winding.
                a, b = (int(x) for x in periods[0]); c, d = (int(x) for x in periods[1])
                numerators = (d * int(discrepancy[0]) - b * int(discrepancy[1]),
                              -c * int(discrepancy[0]) + a * int(discrepancy[1]))
                if determinant <= 0 or any(n % determinant for n in numerators):
                    raise AssertionError("non-periodic lift discrepancy")
                if any(n // determinant for n in numerators):
                    return True
    return False


def dense_shadow_correction(template, public: PublicD4Observation, config: dict) -> tuple[np.ndarray, dict]:
    """Decode solely from the public D4 record; physical truth is absent."""
    bp = run_r6d_dense_template(
        template, public,
        old_message_weight=float(config["old_message_weight"]),
        max_iterations=int(config["max_iterations"]),
        tolerance=float(config["tolerance"]),
    )
    decoded = decode_flux_syndrome(template.lattice, public.flux_syndrome,
                                   llr_weights(bp.marginals[: template.lattice.edge_count, 1]))
    return decoded.correction, {"converged": bool(bp.converged), "iterations": int(bp.iterations),
                                "max_message_delta": float(bp.max_message_delta)}


def static_truth_boundary_audit() -> dict:
    """Verify the production BP helper creates its decoder input before scoring."""
    path = Path(__file__).resolve().parent / "run_r6n_default_flux_policy_comparison.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "decode_bp_policy")
    calls = [ast.unparse(node.func) for node in ast.walk(func) if isinstance(node, ast.Call)]
    return {
        "source": path.name,
        "bp_graph_input_constructed_as_public_observation": "PublicD4Observation" in calls,
        "bp_graph_constructed": "build_r6d_factor_graph" in calls,
        "truth_referenced_score_call_present": "decode_and_score_flux_recovery" in calls,
        "interpretation": "The implementation builds BP from public syndrome/charge; physical truth is passed only to the subsequent scorer. The dynamic shadow replay separately enforces this boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shadow-limit", type=int, default=0,
                        help="Optional public-only dense-BP replays; scorer replay always covers every row.")
    args = parser.parse_args()
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    scope = payload["scope"]; config = scope["bp_defaults"]
    rows = [r for r in payload["rows"] if r["status"] == "nonterminal" and not r["policies"][BP]["flux_union_logical_failure"]]
    # Dense shadow replays are a supplementary decoder-boundary diagnostic.
    # The mandatory all-row integrity replay below uses the stored corrections,
    # regenerated inputs, and an independent scorer; it is deliberately cheap
    # enough to run before any threshold allocation.
    shadow_rows = {(int(r["size"]), float(r["p_X"]), int(r["trajectory_index"]))
                   for r in rows[: max(0, args.shadow_limit)]}
    templates = {(size, p): build_r6d_dense_template(paper_periodic_honeycomb(size), error_rate=p)
                 for size, p, _ in shadow_rows}
    audits=[]; counts=Counter()
    for row in rows:
        size, p, index = int(row["size"]), float(row["p_X"]), int(row["trajectory_index"])
        lattice = paper_periodic_honeycomb(size)
        physical_seed, observation_seed = trajectory_seeds(int(scope["seed_salt"]), size, p, index)
        physical = (np.random.default_rng(physical_seed).random(lattice.edge_count) < p).astype(np.uint8)
        observation = observation_from_error_edges(lattice, physical, seed=observation_seed)
        if observation.status != "sampled" or observation.charge_outcomes is None:
            raise AssertionError("R6U zero-failure row did not regenerate as public sampled record")
        public = PublicD4Observation(tuple(int(x) for x in edge_chain_boundary(lattice, physical)),
                                     tuple(int(x) for x in observation.charge_outcomes))
        stored = row["policies"][BP]
        correction = np.zeros(lattice.edge_count, dtype=np.uint8)
        correction[np.asarray(stored["correction_edges"], dtype=int)] = 1
        if not np.array_equal(edge_chain_boundary(lattice, correction), np.asarray(public.flux_syndrome, dtype=np.uint8)):
            raise AssertionError("stored BP correction does not reproduce public syndrome")
        independent_failure = independent_union_has_winding(lattice, physical, correction)
        if independent_failure != bool(stored["flux_union_logical_failure"]):
            raise AssertionError("independent Boolean-union scorer disagrees with R6U")
        shadow_matches = None; bp = None
        if (size, p, index) in shadow_rows:
            shadow, bp = dense_shadow_correction(templates[(size, p)], public, config)
            shadow_matches = bool(np.array_equal(shadow, correction))
            counts["shadow_correction_matches"] += int(shadow_matches)
            counts["shadow_correction_mismatches"] += int(not shadow_matches)
            counts["shadow_converged"] += int(bp["converged"])
            counts["shadow_nonconverged"] += int(not bp["converged"])
        audits.append({"size": size, "p_X": p, "trajectory_index": index,
                       "physical_seed": physical_seed, "observation_seed": observation_seed,
                       "physical_error_edges": [int(x) for x in np.flatnonzero(physical)],
                       "public_observation": {"flux_syndrome": list(public.flux_syndrome), "charge_outcomes": list(public.charge_outcomes)},
                       "stored_bp_correction_edges": list(stored["correction_edges"]),
                       "stored_failure": bool(stored["flux_union_logical_failure"]),
                       "independent_boolean_union_failure": independent_failure,
                       "public_only_dense_shadow_correction_matches_stored": shadow_matches,
                       "shadow_bp": bp})
    result = {"schema_version": 1, "status": "completed_r6u_bp_zero_failure_integrity_audit",
              "generated_at": datetime.now(timezone.utc).isoformat(), "input": INPUT.name,
              "scope": {"zero_failure_rows_replayed": len(rows), "all_r6u_nonterminal_rows": sum(r["status"] == "nonterminal" for r in payload["rows"])},
              "acceptance": {"provenance_regenerated": len(audits) == len(rows), "all_stored_corrections_match_public_syndrome": True,
                             "independent_boolean_union_scorer_matches": True,
                             "public_only_shadow_replay_exact_matches": (counts["shadow_correction_mismatches"] == 0 if shadow_rows else None)},
              "shadow_summary": dict(counts), "truth_leakage_boundary": static_truth_boundary_audit(), "rows": audits,
              "claim_boundary": "This audits R6U provenance, scorer, and decoder input boundary. It neither validates BP convergence nor establishes an LER curve or threshold."}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text("\n".join([
        "# R6V R6U BP zero-failure integrity audit", "",
        f"Replayed {len(rows)} of {sum(r['status'] == 'nonterminal' for r in payload['rows'])} R6U nonterminal records: every row reported BP flux-union failure=false.",
        "", "## Gates", "",
        f"- Provenance regenerated from deterministic physical and observation seeds: {result['acceptance']['provenance_regenerated']}.",
        "- Every stored BP correction reproduces its regenerated public flux syndrome: true.",
        "- Independent lifted Boolean-union homology scorer agrees with every stored score: true.",
        f"- Public-record-only dense BP shadow replays requested: {len(shadow_rows)}; matches: {counts['shadow_correction_matches']}; mismatches: {counts['shadow_correction_mismatches']}.",
        f"- Shadow BP convergence: {counts['shadow_converged']} converged; {counts['shadow_nonconverged']} finite nonconverged final iterates.",
        "", "## Interpretation", "",
        "The pilot's zero BP failures are not explained by a missing truth/provenance record, syndrome-invalid correction, or a scorer disagreement. This does not validate the apparent BP advantage: high nonconvergence and the pilot's 25 histories/cell still require the R6V convergence-sensitivity gate before threshold sampling.",
    ]) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "report": str(REPORT), "rows": len(rows), "shadow": dict(counts)}))


if __name__ == "__main__":
    main()
