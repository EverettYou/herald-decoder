#!/usr/bin/env python3
"""Run the registered matched default-cell three-policy D4 flux pilot.

The third policy deliberately transfers only the Lab 002 *posterior-LLR
matching principle*.  Its likelihood is the R6D D4 local factor graph, not the
phenomenological Lab 002 binary-herald model.  This is a first-stage-only
comparison: all policies see the same public first observation and physical
truth is used only after their corrections have been fixed for scoring.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import (
    build_r6d_dense_template,
    require_r6d_dense_backend,
    r6d_dense_backend_provenance,
    run_r6d_dense_template,
)
from d4_matching import edge_chain_boundary, published_herald_weights, syndrome_only_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6n-default-flux-policy-comparison-manifest-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6n-default-flux-policy-comparison-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6n-default-flux-policy-comparison-2026-08-29.md"


def trajectory_seeds(salt: int, size: int, error_rate: float, index: int) -> tuple[int, int]:
    sequence = np.random.SeedSequence([salt, size, int(round(10_000 * error_rate)), index])
    physical_seed, observation_seed = sequence.generate_state(2, dtype=np.uint32)
    return int(physical_seed), int(observation_seed)


def llr_weights(marginals: np.ndarray) -> np.ndarray:
    probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1.0 - 1e-12)
    weights = np.log((1.0 - probabilities) / probabilities)
    if not np.all(np.isfinite(weights)):
        raise ValueError("BP posterior LLR weights are not finite")
    return weights


def paired_summary(rows: list[dict], left: str, right: str) -> dict:
    paired = [
        row for row in rows
        if row["status"] == "nonterminal"
        and row["policies"].get(left, {}).get("status") == "decoded"
        and row["policies"].get(right, {}).get("status") == "decoded"
    ]
    counts: Counter[str] = Counter()
    for row in paired:
        left_failure = bool(row["policies"][left]["flux_union_logical_failure"])
        right_failure = bool(row["policies"][right]["flux_union_logical_failure"])
        if left_failure == right_failure:
            counts["tie"] += 1
        elif left_failure and not right_failure:
            counts["right_improves"] += 1
        else:
            counts["right_regresses"] += 1
    count = len(paired)
    return {
        "left": left,
        "right": right,
        "matched_nonterminal_count": count,
        "right_improves": int(counts["right_improves"]),
        "right_regresses": int(counts["right_regresses"]),
        "ties": int(counts["tie"]),
        "right_minus_left_flux_failure_rate": (
            float((counts["right_regresses"] - counts["right_improves"]) / count)
            if count else None
        ),
    }


def policy_summary(rows: list[dict], policy: str) -> dict:
    # A physical winding is already a logical failure in the paper's Appendix-C
    # score.  No decoder call is needed for that row, but it remains in the
    # unconditional LER denominator.  The older conditional field is retained
    # only for decoder-runtime diagnostics and must never be used as an LER.
    attempted = len(rows)
    terminal_failures = sum(row["status"] == "terminal_physical_winding" for row in rows)
    eligible = [row for row in rows if row["status"] == "nonterminal"]
    decoded = [row for row in eligible if row["policies"].get(policy, {}).get("status") == "decoded"]
    failures = sum(bool(row["policies"][policy]["flux_union_logical_failure"]) for row in decoded)
    wall_seconds = [float(row["policies"][policy]["wall_seconds"]) for row in decoded]
    summary = {
        "policy": policy,
        "attempted_records": attempted,
        "physical_winding_logical_failures": int(terminal_failures),
        "nonterminal_records": len(eligible),
        "decoded_records": len(decoded),
        "unavailable_records": len(eligible) - len(decoded),
        "flux_union_logical_failures": int(failures),
        "conditional_flux_failure_rate": float(failures / len(decoded)) if decoded else None,
        "paper_unconditional_flux_logical_failures": int(terminal_failures + failures),
        "paper_unconditional_flux_logical_error_rate": (
            float((terminal_failures + failures) / attempted) if attempted else None
        ),
        "mean_wall_seconds": float(np.mean(wall_seconds)) if wall_seconds else None,
        "median_wall_seconds": float(np.median(wall_seconds)) if wall_seconds else None,
    }
    if policy == "R6D_local_BP_posterior_LLR_MWPM":
        bp_rows = [row["policies"][policy]["bp"] for row in decoded]
        summary.update({
            "converged_records": sum(bool(row["converged"]) for row in bp_rows),
            "nonconverged_records": sum(not bool(row["converged"]) for row in bp_rows),
            "mean_iterations": float(np.mean([row["iterations"] for row in bp_rows])) if bp_rows else None,
            "maximum_final_message_delta": max((row["max_message_delta"] for row in bp_rows), default=None),
        })
    return summary


def decode_bp_policy(template, lattice, physical: np.ndarray, observation, config: dict) -> dict:
    public = PublicD4Observation(
        tuple(int(value) for value in edge_chain_boundary(lattice, physical)),
        tuple(int(value) for value in observation.charge_outcomes),
    )
    started = time.perf_counter()
    try:
        bp = run_r6d_dense_template(
            template,
            public,
            old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]),
            tolerance=float(config["tolerance"]),
        )
        recovery = decode_and_score_flux_recovery(
            lattice, physical, llr_weights(bp.marginals[: lattice.edge_count, 1])
        )
    except Exception as error:  # Preserve a strict unavailable result; never substitute another policy.
        return {
            "status": "unavailable",
            "reason": repr(error),
            "wall_seconds": time.perf_counter() - started,
            "backend_provenance": r6d_dense_backend_provenance(),
        }
    return {
        "status": "decoded",
        "flux_union_logical_failure": bool(recovery.logical_error),
        "objective_weight": float(recovery.objective_weight),
        "correction_edges": [int(edge) for edge in np.flatnonzero(recovery.correction)],
        "wall_seconds": time.perf_counter() - started,
        "bp": {
            "converged": bool(bp.converged),
            "iterations": int(bp.iterations),
            "max_message_delta": float(bp.max_message_delta),
        },
        "backend_provenance": r6d_dense_backend_provenance(),
    }


def decode_matching_policy(lattice, physical: np.ndarray, weights: np.ndarray) -> dict:
    started = time.perf_counter()
    recovery = decode_and_score_flux_recovery(lattice, physical, weights)
    return {
        "status": "decoded",
        "flux_union_logical_failure": bool(recovery.logical_error),
        "objective_weight": float(recovery.objective_weight),
        "correction_edges": [int(edge) for edge in np.flatnonzero(recovery.correction)],
        "wall_seconds": time.perf_counter() - started,
    }


def run(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6N":
        raise ValueError("manifest is not an active R6N registration")
    scope = manifest["scope"]
    size = int(scope["size"])
    error_rate = float(scope["physical_error_rate"])
    histories = int(scope["histories"])
    backend_provenance = require_r6d_dense_backend(scope.get("backend_id"))
    lattice = paper_periodic_honeycomb(size)
    bp_template = build_r6d_dense_template(lattice, error_rate=error_rate)
    rows: list[dict] = []
    for index in range(histories):
        physical_seed, observation_seed = trajectory_seeds(
            int(scope["seed_salt"]), size, error_rate, index
        )
        physical = (np.random.default_rng(physical_seed).random(lattice.edge_count) < error_rate).astype(np.uint8)
        observation = observation_from_error_edges(lattice, physical, seed=observation_seed)
        row = {
            "trajectory_index": index,
            "physical_seed": physical_seed,
            "observation_seed": observation_seed,
            "physical_error_edges": [int(edge) for edge in np.flatnonzero(physical)],
            "observation_status": observation.status,
            "policies": {},
        }
        if observation.status == "logical_failure":
            row["status"] = "terminal_physical_winding"
            rows.append(row)
            continue
        if observation.status != "sampled" or observation.charge_outcomes is None:
            raise RuntimeError(f"unexpected observation status {observation.status!r}")
        row["status"] = "nonterminal"
        row["public_observation"] = {
            "flux_syndrome": [int(value) for value in edge_chain_boundary(lattice, physical)],
            "charge_outcomes": [int(value) for value in observation.charge_outcomes],
        }
        row["policies"]["O0_unit_weight_MWPM"] = decode_matching_policy(
            lattice, physical, syndrome_only_weights(lattice)
        )
        row["policies"]["O2_published_herald_weight_MWPM"] = decode_matching_policy(
            lattice, physical,
            published_herald_weights(lattice, np.asarray(observation.charge_outcomes, dtype=np.int64)),
        )
        row["policies"]["R6D_local_BP_posterior_LLR_MWPM"] = decode_bp_policy(
            bp_template, lattice, physical, observation, scope["bp_defaults"]
        )
        rows.append(row)

    policies = scope["flux_policies"]
    summaries = {policy: policy_summary(rows, policy) for policy in policies}
    pairings = [
        paired_summary(rows, "O0_unit_weight_MWPM", "O2_published_herald_weight_MWPM"),
        paired_summary(rows, "O0_unit_weight_MWPM", "R6D_local_BP_posterior_LLR_MWPM"),
        paired_summary(rows, "O2_published_herald_weight_MWPM", "R6D_local_BP_posterior_LLR_MWPM"),
    ]
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_default_cell_flux_only_pilot",
        "manifest": manifest_path.name,
        "scope": scope,
        "backend_provenance": backend_provenance,
        "topology": {"vertices": lattice.vertex_count, "edges": lattice.edge_count, "forcing_scale": 3 * lattice.edge_count},
        "terminal_physical_winding_records": sum(row["status"] == "terminal_physical_winding" for row in rows),
        "policy_summaries": summaries,
        "paired_summaries": pairings,
        "rows": rows,
        "claim_boundary": manifest["method_boundary"] + " This is a 100-history default-cell flux-only pilot, not an LER, second-stage, threshold, or scalable-accuracy result.",
    }


def render(payload: dict) -> str:
    scope = payload["scope"]
    lines = [
        "# R6N default-cell matched flux-policy comparison",
        "",
        f"Paper-normalized D4 (L={scope['size']}), (p={scope['physical_error_rate']:.2f}), {scope['histories']} fixed trajectories.",
        "All three policies share each nonterminal physical/fusion record. The score is first-stage Boolean-union logical failure; terminal physical windings are excluded from the decoder-contingent denominator.",
        "",
        "| policy | decoded / nonterminal | flux failures | conditional flux failure | mean wall time |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for policy, summary in payload["policy_summaries"].items():
        rate = summary["conditional_flux_failure_rate"]
        mean_wall = summary["mean_wall_seconds"]
        wall_text = "—" if mean_wall is None else f"{1000.0 * mean_wall:.2f} ms"
        lines.append(
            f"| {policy} | {summary['decoded_records']} / {summary['nonterminal_records']} | "
            f"{summary['flux_union_logical_failures']} | {'—' if rate is None else f'{rate:.4f}'} | "
            f"{wall_text} |"
        )
    bp = payload["policy_summaries"]["R6D_local_BP_posterior_LLR_MWPM"]
    lines.extend([
        "",
        f"R6D-BP completed {bp['decoded_records']}/{bp['nonterminal_records']} nonterminal records; "
        f"{bp.get('converged_records', 0)} converged within the default 40 iterations and "
        f"{bp.get('nonconverged_records', 0)} were decoded from their finite final iterate.",
        "",
        "| paired contrast | right improves | right regresses | ties | right minus left flux-failure rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for pairing in payload["paired_summaries"]:
        difference = pairing["right_minus_left_flux_failure_rate"]
        lines.append(
            f"| {pairing['right']} vs {pairing['left']} | {pairing['right_improves']} | "
            f"{pairing['right_regresses']} | {pairing['ties']} | "
            f"{'—' if difference is None else f'{difference:+.4f}'} |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "The BP branch transfers the posterior-LLR matching principle to the R6D D4 local factor graph. It is not the Lab 002 phenomenological likelihood, and its unscreened 40-iteration loopy marginal is not an exact D4 posterior. This pilot is therefore a matched feasibility/performance observation, not a validation of a scalable D4 BP decoder.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run(args.manifest)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(payload), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "report": str(args.report),
        "policy_summaries": payload["policy_summaries"],
        "terminal_physical_winding_records": payload["terminal_physical_winding_records"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
