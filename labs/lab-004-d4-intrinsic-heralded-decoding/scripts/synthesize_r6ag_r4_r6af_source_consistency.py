#!/usr/bin/env python3
"""Deterministically synthesize R4.5c and R6AF without new computation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "manifests/r6ag-r4-r6af-source-consistency-synthesis-manifest-2026-09-01.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing frozen evidence: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_synthesis(manifest: dict) -> dict:
    if manifest.get("status") not in {
        "registered_synthesis_pending",
        "synthesis_completed_qualitative_consistency",
    }:
        raise RuntimeError("R6AG manifest is not in a registered synthesis state")
    evidence = manifest["evidence_freeze"]
    paths = {name: LAB_DIR / relative for name, relative in evidence.items()}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing frozen evidence entries: {missing}")
    r4 = _load(paths["r4_machine"])
    r4_contract = _load(paths["r4_contract"])
    r6 = _load(paths["r6af_machine"])
    r6_contract = _load(paths["r6af_contract"])
    status_gates = {
        "r4_machine_audited": r4.get("status")
        == "corrected_sequential_policy_audited",
        "r4_contract_audited": r4_contract.get("status") == "audited",
        "r6af_machine_analyzed": r6.get("status") == "analyzed_registered_pilot",
        "r6af_contract_completed": r6_contract.get("status")
        == "pilot_completed_analyzed_no_refinement",
        "r4_report_present": paths["r4_report"].is_file(),
        "r6af_report_present": paths["r6af_report"].is_file(),
    }
    if not all(status_gates.values()):
        raise RuntimeError(f"frozen evidence status gate failed: {status_gates}")

    r4_rows = []
    for source in r4["prior_summaries"]:
        o0 = float(source["o0_flux_only"]["nonwinding_conditioned_risks"]["public_fixed"])
        o2 = float(source["o2_flux_and_charge"]["nonwinding_conditioned_risks"]["public_fixed"])
        decomposition = source["decomposition"]
        first = float(
            decomposition["o2"]["public_first_action_excess_after_exact_continuation"]
        )
        second = float(
            decomposition["o2"]["second_stage_mwpm_excess_at_public_first"]
        )
        r4_rows.append(
            {
                "p": float(source["p"]),
                "public_fixed_o0_nonwinding_risk": o0,
                "public_fixed_o2_nonwinding_risk": o2,
                "public_fixed_delta_o2_minus_o0": o2 - o0,
                "public_fixed_direction": "improvement" if o2 < o0 else "regression",
                "future_aware_exact_information_gain_o0_minus_o2": float(
                    decomposition["future_aware_exact_information_gain_o0_minus_o2"]
                ),
                "o2_public_first_action_excess_after_exact_continuation": first,
                "o2_second_stage_mwpm_excess_at_public_first": second,
                "o2_first_action_excess_exceeds_second_stage_excess": first > second,
            }
        )

    r6_rows = []
    for source in r6["cells"]:
        o0_stage = source["arms"]["O0"]["stage_counts"]
        o2_stage = source["arms"]["O2"]["stage_counts"]
        first_reduction = int(o0_stage.get("flux_union_logical_failure", 0)) - int(
            o2_stage.get("flux_union_logical_failure", 0)
        )
        charge_reduction = int(o0_stage.get("charge_logical_failure", 0)) - int(
            o2_stage.get("charge_logical_failure", 0)
        )
        r6_rows.append(
            {
                "size": int(source["size"]),
                "p_X": float(source["p_X"]),
                "public_fixed_o0_unconditional_risk": float(source["arms"]["O0"]["risk"]),
                "public_fixed_o2_unconditional_risk": float(source["arms"]["O2"]["risk"]),
                "paired_delta_o2_minus_o0": float(source["paired"]["delta_O2_minus_O0"]),
                "paired_interval_90": list(source["paired"]["bootstrap_90"]),
                "paired_direction": source["paired"]["direction"],
                "first_union_failure_reduction_o0_minus_o2": first_reduction,
                "charge_failure_reduction_o0_minus_o2": charge_reduction,
                "first_union_reduction_dominates_charge_difference": first_reduction
                > abs(charge_reduction),
            }
        )

    classifications = [
        {
            "quantity": "O0/O2 public observation and first-policy labels",
            "class": "comparable",
            "use": "Confirm shared source-level policy semantics only.",
        },
        {
            "quantity": "sign of public fixed O2-minus-O0 risk",
            "class": "qualitative_only",
            "use": "Compare within-study direction without comparing magnitude or p coordinates.",
        },
        {
            "quantity": "first-stage policy as a major performance lever",
            "class": "qualitative_only",
            "use": "Compare R4 O2 excess decomposition with R6AF stage-count localization.",
        },
        {
            "quantity": "lattice topology and size",
            "class": "incommensurate",
            "use": "Primitive branch-resolved L=2 versus paper-normalized L=3,5.",
        },
        {
            "quantity": "conditioning and denominator",
            "class": "incommensurate",
            "use": "R4 nonwinding-conditioned versus R6AF unconditional attempted histories.",
        },
        {
            "quantity": "p grid",
            "class": "incommensurate",
            "use": "No interpolation or nearest-p matching.",
        },
        {
            "quantity": "risk and delta magnitudes",
            "class": "incommensurate",
            "use": "No pooling, ratio, difference-of-differences, or transfer coefficient.",
        },
        {
            "quantity": "evidence and uncertainty type",
            "class": "incommensurate",
            "use": "Exact enumeration versus paired Monte Carlo intervals.",
        },
        {
            "quantity": "charge graph representation",
            "class": "incommensurate",
            "use": "Primitive private-auxiliary branch graph versus nondegenerate paper lattice graph.",
        },
        {
            "quantity": "stage counts, p-values, size trends, exact-policy excesses",
            "class": "incommensurate",
            "use": "Retain only inside the owning study.",
        },
    ]
    allowed_classes = {"comparable", "qualitative_only", "incommensurate"}
    unclassified = [row for row in classifications if row["class"] not in allowed_classes]

    r4_low_intermediate_improvement = any(
        row["p"] <= 0.5 and row["public_fixed_direction"] == "improvement"
        for row in r4_rows
    )
    r4_p06_regression = any(
        row["p"] == 0.6 and row["public_fixed_direction"] == "regression"
        for row in r4_rows
    )
    r4_first_stage_leverage = all(
        row["o2_first_action_excess_exceeds_second_stage_excess"] for row in r4_rows
    )
    r6_improvement = all(
        row["paired_direction"] == "resolved_improvement" for row in r6_rows
    )
    r6_first_stage_leverage = all(
        row["first_union_reduction_dominates_charge_difference"] for row in r6_rows
    )
    verdict_gates = {
        "status_gates_passed": all(status_gates.values()),
        "all_quantities_classified": not unclassified,
        "r4_low_intermediate_public_direction_improves": r4_low_intermediate_improvement,
        "r4_p0.6_nonuniversal_regression_preserved": r4_p06_regression,
        "r4_o2_first_stage_excess_dominates": r4_first_stage_leverage,
        "r6af_all_registered_cells_improve": r6_improvement,
        "r6af_first_union_reduction_dominates": r6_first_stage_leverage,
        "new_histories": 0,
        "new_arm_evaluations": 0,
        "new_bootstrap_replicates": 0,
    }
    verdict = (
        "qualitatively_consistent_with_nonuniversal_boundary"
        if all(
            value is True
            for key, value in verdict_gates.items()
            if not key.startswith("new_")
        )
        else "censored"
    )
    return {
        "schema_version": 1,
        "status": "completed" if verdict != "censored" else "censored",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": DEFAULT_MANIFEST.name,
        "evidence_status_gates": status_gates,
        "r4_exact_primitive_extraction": r4_rows,
        "r6af_complete_pipeline_extraction": r6_rows,
        "comparison_matrix": classifications,
        "unclassified_quantity_count": len(unclassified),
        "verdict_gates": verdict_gates,
        "verdict": verdict,
        "allowed_claim": manifest["allowed_claim"],
        "nonuniversal_boundary": manifest["known_nonuniversal_boundary"],
        "interpretation": (
            "R6AF agrees qualitatively with the low/intermediate-prior R4.5c "
            "public direction, and both studies independently identify first-stage "
            "policy choice as a major lever. The R4.5c p=0.6 public-fixed regression "
            "prevents a universal O2-dominance claim."
        ),
        "claim_boundary": (
            "No numeric cross-study risk comparison, interpolation, pooling, "
            "threshold, scaling, fault-tolerance, BP, or Lab 003 claim."
        ),
        "new_computation": {
            "histories": 0,
            "arm_evaluations": 0,
            "bootstrap_replicates": 0,
        },
    }


def report_markdown(payload: dict) -> str:
    lines = [
        "# R6AG R4.5c/R6AF source-consistency synthesis",
        "",
        f"Verdict: **{payload['verdict']}**.",
        "",
        "## Exact primitive R4.5c extraction",
        "",
        "| p | public O0 | public O2 | O2-O0 | direction | O2 first-action excess | O2 charge-stage excess |",
        "|---:|---:|---:|---:|:---|---:|---:|",
    ]
    for row in payload["r4_exact_primitive_extraction"]:
        lines.append(
            f"| {row['p']:.1f} | {row['public_fixed_o0_nonwinding_risk']:.6f} | "
            f"{row['public_fixed_o2_nonwinding_risk']:.6f} | "
            f"{row['public_fixed_delta_o2_minus_o0']:+.6f} | "
            f"{row['public_fixed_direction']} | "
            f"{row['o2_public_first_action_excess_after_exact_continuation']:.6f} | "
            f"{row['o2_second_stage_mwpm_excess_at_public_first']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## R6AF paired pilot extraction",
            "",
            "| L | p_X | O0 | O2 | O2-O0 (90% paired) | first-union reduction | charge-loss reduction |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["r6af_complete_pipeline_extraction"]:
        interval = row["paired_interval_90"]
        lines.append(
            f"| {row['size']} | {row['p_X']:.2f} | "
            f"{row['public_fixed_o0_unconditional_risk']:.4f} | "
            f"{row['public_fixed_o2_unconditional_risk']:.4f} | "
            f"{row['paired_delta_o2_minus_o0']:+.4f} "
            f"[{interval[0]:+.4f}, {interval[1]:+.4f}] | "
            f"{row['first_union_failure_reduction_o0_minus_o2']} | "
            f"{row['charge_failure_reduction_o0_minus_o2']} |"
        )
    lines.extend(
        [
            "",
            "## Synthesis",
            "",
            payload["interpretation"],
            "",
            "The agreement is qualitative only. R4.5c and R6AF differ in topology, "
            "size, conditioning, p grid, charge-graph representation, and exact-versus-"
            "Monte-Carlo evidence. Their risk and delta magnitudes are not compared.",
            "",
            "## Nonuniversal boundary",
            "",
            payload["nonuniversal_boundary"],
            "",
            "## Claim boundary",
            "",
            payload["claim_boundary"],
            "Zero new histories, arm evaluations, or bootstrap replicates were generated.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = _load(args.manifest)
    payload = build_synthesis(manifest)
    outputs = manifest["outputs"]
    machine = LAB_DIR / outputs["machine_synthesis"]
    report = LAB_DIR / outputs["report"]
    machine.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.write_text(report_markdown(payload), encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "output": str(machine)}, sort_keys=True))


if __name__ == "__main__":
    main()
