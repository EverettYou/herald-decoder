#!/usr/bin/env python3
"""Audit the frozen R6N O2-versus-D4-BP flux-stage divergences."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import generate_loop_constraints, paper_periodic_honeycomb
from d4_local_bp import build_r6d_factor_graph, run_sum_product
from d4_matching import edge_chain_boundary, published_herald_weights
from d4_recovery import decode_and_score_flux_recovery


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r6o-paired-flux-mechanism-audit-manifest-2026-08-29.json"
DEFAULT_INPUT = LAB_DIR / "results/r6n-default-flux-policy-comparison-2026-08-29.json"
DEFAULT_OUTPUT = LAB_DIR / "results/r6o-paired-flux-mechanism-audit-2026-08-29.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r6o-paired-flux-mechanism-audit-2026-08-29.md"
O2 = "O2_published_herald_weight_MWPM"
BP = "R6D_local_BP_posterior_LLR_MWPM"


def selected_chain(edge_count: int, selected: list[int]) -> np.ndarray:
    chain = np.zeros(edge_count, dtype=np.uint8)
    chain[np.asarray(selected, dtype=int)] = 1
    return chain


def llr_weights(marginals: np.ndarray) -> np.ndarray:
    probabilities = np.clip(np.asarray(marginals, dtype=float), 1e-12, 1.0 - 1e-12)
    return np.log((1.0 - probabilities) / probabilities)


def entropy(probabilities: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probabilities, dtype=float), 1e-12, 1.0 - 1e-12)
    return -(values * np.log2(values) + (1.0 - values) * np.log2(1.0 - values))


def group_name(o2_failure: bool, bp_failure: bool) -> str:
    if o2_failure and not bp_failure:
        return "BP_improves_O2"
    if not o2_failure and bp_failure:
        return "BP_regresses_O2"
    return "same_first_stage_outcome"


def numeric_summary(rows: list[dict], key: str) -> dict:
    values = np.asarray([float(row[key]) for row in rows], dtype=float)
    return {
        "count": len(rows),
        "mean": float(values.mean()) if len(values) else None,
        "median": float(np.median(values)) if len(values) else None,
        "minimum": float(values.min()) if len(values) else None,
        "maximum": float(values.max()) if len(values) else None,
    }


def run(manifest_path: Path, input_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "registered" or manifest.get("phase") != "R6O":
        raise ValueError("manifest is not an active R6O registration")
    source = json.loads(input_path.read_text(encoding="utf-8"))
    scope = source["scope"]
    lattice = paper_periodic_honeycomb(int(scope["size"]))
    config = scope["bp_defaults"]
    rows: list[dict] = []
    replay_failures: list[dict] = []

    for frozen in source["rows"]:
        if frozen["status"] != "nonterminal":
            continue
        public = frozen["public_observation"]
        physical = selected_chain(lattice.edge_count, frozen["physical_error_edges"])
        charge = np.asarray(public["charge_outcomes"], dtype=np.int64)
        syndrome = np.asarray(public["flux_syndrome"], dtype=np.uint8)
        if not np.array_equal(syndrome, edge_chain_boundary(lattice, physical)):
            replay_failures.append({"trajectory_index": frozen["trajectory_index"], "failure": "public_syndrome_mismatch"})
            continue
        observation = PublicD4Observation(tuple(int(value) for value in syndrome), tuple(int(value) for value in charge))
        graph = build_r6d_factor_graph(
            lattice, observation, error_rate=float(scope["physical_error_rate"]),
            terminal_screened=bool(config["terminal_screened"]),
        )
        bp = run_sum_product(
            graph, old_message_weight=float(config["old_message_weight"]),
            max_iterations=int(config["max_iterations"]), tolerance=float(config["tolerance"]),
        )
        o2 = decode_and_score_flux_recovery(lattice, physical, published_herald_weights(lattice, charge))
        bp_recovery = decode_and_score_flux_recovery(lattice, physical, llr_weights(bp.marginals[: lattice.edge_count, 1]))
        frozen_o2 = selected_chain(lattice.edge_count, frozen["policies"][O2]["correction_edges"])
        frozen_bp = selected_chain(lattice.edge_count, frozen["policies"][BP]["correction_edges"])
        if not np.array_equal(o2.correction, frozen_o2):
            replay_failures.append({"trajectory_index": frozen["trajectory_index"], "failure": "o2_correction_replay_mismatch"})
        if not np.array_equal(bp_recovery.correction, frozen_bp):
            replay_failures.append({"trajectory_index": frozen["trajectory_index"], "failure": "bp_correction_replay_mismatch"})
        marginal = bp.marginals[: lattice.edge_count, 1]
        n_e = np.sum(charge[lattice.edge_vertices] == 1, axis=1, dtype=np.int64)
        difference = o2.correction ^ bp_recovery.correction
        difference_analysis = generate_loop_constraints(lattice, difference.astype(bool))
        group = group_name(bool(o2.logical_error), bool(bp_recovery.logical_error))
        rows.append({
            "trajectory_index": int(frozen["trajectory_index"]),
            "group": group,
            "o2_flux_failure": bool(o2.logical_error),
            "bp_flux_failure": bool(bp_recovery.logical_error),
            "physical_edge_count": int(physical.sum()),
            "measured_charge_vertex_count": int(np.sum(charge != -1)),
            "charge_one_vertex_count": int(np.sum(charge == 1)),
            "herald_incidence_total": int(n_e.sum()),
            "o2_correction_edge_count": int(o2.correction.sum()),
            "bp_correction_edge_count": int(bp_recovery.correction.sum()),
            "o2_bp_correction_symmetric_difference_edges": int(difference.sum()),
            "difference_component_count": len(difference_analysis.components),
            "difference_winding_component_count": sum(
                not component.homologically_trivial for component in difference_analysis.components
            ),
            "bp_converged": bool(bp.converged),
            "bp_iterations": int(bp.iterations),
            "bp_final_max_message_delta": float(bp.max_message_delta),
            "bp_mean_edge_entropy_bits": float(entropy(marginal).mean()),
            "bp_max_edge_entropy_bits": float(entropy(marginal).max()),
            "bp_extreme_marginal_fraction": float(np.mean((marginal <= 0.01) | (marginal >= 0.99))),
            "bp_mean_absolute_llr": float(np.abs(llr_weights(marginal)).mean()),
            "bp_correction_matches_physical": bool(np.array_equal(bp_recovery.correction, physical)),
            "o2_correction_matches_physical": bool(np.array_equal(o2.correction, physical)),
        })

    if replay_failures:
        raise AssertionError(f"R6N replay failure: {replay_failures[:3]}")
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)
    keys = (
        "physical_edge_count", "measured_charge_vertex_count", "charge_one_vertex_count",
        "herald_incidence_total", "o2_correction_edge_count", "bp_correction_edge_count",
        "o2_bp_correction_symmetric_difference_edges", "difference_winding_component_count",
        "bp_iterations", "bp_final_max_message_delta", "bp_mean_edge_entropy_bits",
        "bp_max_edge_entropy_bits", "bp_extreme_marginal_fraction", "bp_mean_absolute_llr",
    )
    group_summaries = {
        group: {
            "count": len(selected),
            "bp_nonconverged_count": sum(not row["bp_converged"] for row in selected),
            "bp_correction_matches_physical_count": sum(row["bp_correction_matches_physical"] for row in selected),
            "o2_correction_matches_physical_count": sum(row["o2_correction_matches_physical"] for row in selected),
            "metrics": {key: numeric_summary(selected, key) for key in keys},
        }
        for group, selected in sorted(groups.items())
    }
    expected = len(rows)
    if sum(item["count"] for item in group_summaries.values()) != expected:
        raise AssertionError("group accounting does not cover the nonterminal cohort")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed_replay_consistent_mechanism_audit",
        "manifest": manifest_path.name,
        "source": input_path.name,
        "replayed_nonterminal_records": expected,
        "replay_failure_count": 0,
        "group_summaries": group_summaries,
        "divergence_rows": [row for row in rows if row["group"] != "same_first_stage_outcome"],
        "claim_boundary": manifest["claim_boundary"],
    }


def render(payload: dict) -> str:
    groups = payload["group_summaries"]
    lines = [
        "# R6O paired flux-policy mechanism audit",
        "",
        f"All {payload['replayed_nonterminal_records']} frozen R6N nonterminal records replay exactly under their recorded public observations and default 40-iteration R6D-BP settings.",
        "",
        "| group | count | BP nonconverged | BP correction = physical | O2 correction = physical |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for group, summary in groups.items():
        lines.append(
            f"| {group} | {summary['count']} | {summary['bp_nonconverged_count']} | "
            f"{summary['bp_correction_matches_physical_count']} | {summary['o2_correction_matches_physical_count']} |"
        )
    lines.extend([
        "",
        "| group | measured charge vertices (mean) | charge-one vertices (mean) | O2/BP correction difference (mean edges) | BP entropy (mean bits) | BP extreme-marginal fraction (mean) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for group, summary in groups.items():
        metrics = summary["metrics"]
        lines.append(
            f"| {group} | {metrics['measured_charge_vertex_count']['mean']:.3f} | "
            f"{metrics['charge_one_vertex_count']['mean']:.3f} | "
            f"{metrics['o2_bp_correction_symmetric_difference_edges']['mean']:.3f} | "
            f"{metrics['bp_mean_edge_entropy_bits']['mean']:.4f} | "
            f"{metrics['bp_extreme_marginal_fraction']['mean']:.4f} |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "These are descriptive associations in one frozen default cell. They identify which public-record and approximation-state features co-occur with the paired divergences; they do not prove why BP wins or loses, nor do they require BP marginals to equal an exact posterior.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    payload = run(args.manifest, args.input)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "report": str(args.report), "groups": payload["group_summaries"]}, indent=2))


if __name__ == "__main__":
    main()
