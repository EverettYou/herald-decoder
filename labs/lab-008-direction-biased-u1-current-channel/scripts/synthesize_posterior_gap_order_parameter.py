#!/usr/bin/env python3
"""Synthesize a selector-free posterior-gap protocol from existing records only."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
SUMMARY = LAB / "results/size-bias-distributions-2026-09-18.json"
OUTPUT = LAB / "results/posterior-gap-order-parameter-synthesis-2026-09-21.json"
THRESHOLDS = (0.5, 1.0, 2.0, 4.0)


def load(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def raw_path_for_id(summary: dict, cell_id: str) -> Path:
    matches = [
        LAB / relative
        for relative in summary["input_sha256"]
        if relative.endswith(f"/{cell_id}.json")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one raw file for {cell_id}, found {matches}")
    relative = str(matches[0].relative_to(LAB))
    expected = summary["input_sha256"][relative]
    if sha256(matches[0]) != expected:
        raise RuntimeError(f"source hash mismatch for {relative}")
    return matches[0]


def gap_of(record: dict) -> float:
    if record["gap_infinite_sign"]:
        return math.inf
    return abs(float(record["signed_gap"]))


def analyze_cell(summary: dict, cell: dict) -> dict:
    raw_path = raw_path_for_id(summary, cell["id"])
    raw = load(raw_path)
    records = raw["records"]
    if len(records) != cell["shots"]:
        raise RuntimeError(f"shot mismatch for {cell['id']}")
    for key in ("L", "p", "q", "shots"):
        if raw["cell"][key] != cell[key]:
            raise RuntimeError(f"cell metadata mismatch for {cell['id']}:{key}")

    gaps = [gap_of(record) for record in records]
    risks = [float(record["bayes_risk"]) for record in records]
    total_risk = sum(risks)
    mean_risk = total_risk / len(risks)
    summary_risk = float(cell["risk"]["mean"][0])
    if abs(mean_risk - summary_risk) > 1e-14:
        raise RuntimeError(f"risk replay mismatch for {cell['id']}")

    logistic_errors = []
    for gap, risk in zip(gaps, risks):
        expected = 0.0 if math.isinf(gap) else 1.0 / (1.0 + math.exp(gap))
        logistic_errors.append(abs(risk - expected))

    diagnostics = {}
    for threshold in THRESHOLDS:
        mask = [gap <= threshold for gap in gaps]
        cdf = sum(mask) / len(mask)
        risk_mass = sum(risk for risk, keep in zip(risks, mask) if keep)
        diagnostics[str(threshold)] = {
            "low_gap_probability": cdf,
            "risk_share_from_low_gap_records": risk_mass / total_risk,
            "risk_lower_bound": cdf / (1.0 + math.exp(threshold)),
            "risk_upper_bound": 0.5 * cdf
            + (1.0 - cdf) / (1.0 + math.exp(threshold)),
        }

    finite_gaps = [gap for gap in gaps if not math.isinf(gap)]
    return {
        "id": cell["id"],
        "L": cell["L"],
        "p": cell["p"],
        "q": cell["q"],
        "records": cell["shots"],
        "Bayes_risk": mean_risk,
        "Bayes_risk_interval95": cell["risk"]["interval"][0],
        "conditional_logical_entropy_bits": cell["sector_entropy_bits"]["mean"],
        "median_abs_DeltaF": quantile(gaps, 0.5),
        "lower_quartile_abs_DeltaF": quantile(gaps, 0.25),
        "infinite_gap_fraction": cell["infinite_gap_fraction"],
        "threshold_diagnostics": diagnostics,
        "integrity": {
            "raw_file": str(raw_path.relative_to(ROOT)),
            "raw_sha256": sha256(raw_path),
            "maximum_record_logistic_identity_error": max(logistic_errors),
            "finite_gap_records": len(finite_gaps),
        },
    }


def main() -> None:
    summary = load(SUMMARY)
    cells = [cell for cell in summary["square_grid"] if cell["p"] == 0.3]
    rows = [analyze_cell(summary, cell) for cell in cells]
    rows.sort(key=lambda row: (row["q"], row["L"]))

    trajectories = []
    for q in sorted({row["q"] for row in rows}):
        group = [row for row in rows if row["q"] == q]
        trajectories.append(
            {
                "q": q,
                "sizes": [row["L"] for row in group],
                "Bayes_risk": [row["Bayes_risk"] for row in group],
                "median_abs_DeltaF": [row["median_abs_DeltaF"] for row in group],
                "low_gap_probability_at_1": [
                    row["threshold_diagnostics"]["1.0"]["low_gap_probability"]
                    for row in group
                ],
                "risk_share_from_abs_gap_at_most_1": [
                    row["threshold_diagnostics"]["1.0"][
                        "risk_share_from_low_gap_records"
                    ]
                    for row in group
                ],
            }
        )

    source_files = [
        Path(__file__).resolve(),
        SUMMARY,
        LAB / "results/thermodynamic-limits-2026-09-20.json",
        LAB / "results/replica-boundary-theory-2026-09-18.json",
        LAB / "results/square-midpoint-thermodynamics-2026-09-20.json",
        LAB / "results/midpoint-alternative-theorem-interface-audit-2026-09-21.json",
    ]
    source_files.extend(ROOT / row["integrity"]["raw_file"] for row in rows)

    result = {
        "status": "complete_order_parameter_identity_existing_data_insufficient_go_boundary_acquisition",
        "accessed": "2026-09-21",
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "new_bootstrap_replicates": 0,
        "existing_result_families_used": 5,
        "scientific_role": "decoder-independent transition-observable synthesis",
        "order_parameter": {
            "signed_gap": "DeltaF(Q)=log[Z0(Q)/Z1(Q)]",
            "absolute_gap": "G_L(Q)=abs(DeltaF(Q))",
            "record_risk": "b(G)=1/(1+exp(G))",
            "physical_Bayes_risk": "R_L=E_Q[b(G_L)]",
            "correctability_equivalence": "R_L->0 if and only if G_L->infinity in physical-record probability",
            "fixed_threshold_bounds": "C_L(a)/(1+exp(a)) <= R_L <= C_L(a)/2 + (1-C_L(a))/(1+exp(a)), where C_L(a)=Pr[G_L<=a]",
        },
        "discriminating_protocol": {
            "typical_stiffness": {
                "signature": "For every fixed a, C_L(a)->0; lower quantiles and the median of G_L move outward; R_L->0.",
                "warning": "A growing median alone is insufficient because a shrinking low-gap tail can dominate R_L."
            },
            "finite_gap_phase": {
                "signature": "There exist finite a and c>0 with liminf C_L(a)>=c, which forces liminf R_L>=c/(1+exp(a)).",
                "warning": "Finite sizes with nonzero C_L(a) do not establish a positive limiting c."
            },
            "broad_rare_event_mixture": {
                "signature": "Typical gap quantiles grow while B_L(a)=E[b(G_L) 1(G_L<=a)]/R_L approaches one for a fixed or slowly growing a.",
                "warning": "This can coexist with R_L->0; it identifies the mechanism controlling the decay, not a separate noncorrectable phase by itself."
            },
            "required_observables": [
                "Bayes risk R_L",
                "CDF C_L(a) on a fixed a grid",
                "median and lower quartile of abs(DeltaF)",
                "risk-concentration fraction B_L(a)",
                "conditional logical entropy as a cross-check"
            ],
            "independent_unit": "one physical current/charge record",
            "uncertainty": "record-level intervals for every CDF, quantile, risk and risk-concentration observable; size contrasts use independent resampling and q contrasts may use only registered matched streams",
        },
        "existing_p030_square_rows": rows,
        "existing_p030_square_trajectories": trajectories,
        "finite_evidence_assessment": {
            "q_0.50": "Large low-gap mass and Bayes risk persist over L=5,7,9; typical stiffness is not supported on these sizes, but a finite-gap thermodynamic phase is not established.",
            "q_0.75": "Risk and low-gap mass change only modestly; the sampled sizes do not discriminate persistent finite gaps from slow crossover.",
            "q_0.90": "L7-to-L9 risk and C_L(1) are nearly flat within existing uncertainty, so the branch remains unresolved rather than classified.",
            "q_0.97": "Median gaps move outward and L9 risk is lower, but C_L(1) remains substantial; typical stiffness and rare-tail control are not separated.",
            "q_1.00": "Risk and C_L(1) fall strongly and the median gap moves beyond four by L9, giving finite-size stiffness evidence only; no square asymptotic phase is claimed.",
            "global_decision": "The existing three-size design cannot discriminate the three registered asymptotic alternatives. Means or slopes alone would be misleading; fixed-gap CDF and risk-concentration scaling are required."
        },
        "go_no_go": {
            "decision": "GO_REGISTER_ONLY",
            "reason": "The q=0.90 and q=0.97 trajectories bracket qualitatively different finite-size behavior at p=0.30, but no larger size or interior q=0.94 trajectory exists.",
            "smallest_future_matrix": {
                "fixed_physical_error_rate": 0.3,
                "q_values": [0.9, 0.94, 0.97],
                "sizes": [7, 9, 11],
                "reuse_existing_without_pooling": [
                    {"q": 0.9, "sizes": [7, 9]},
                    {"q": 0.97, "sizes": [7, 9]}
                ],
                "new_cells": [
                    {"q": 0.9, "L": 11},
                    {"q": 0.94, "L": 7},
                    {"q": 0.94, "L": 9},
                    {"q": 0.94, "L": 11},
                    {"q": 0.97, "L": 11}
                ],
                "purpose": "separate persistent low-gap mass from outward-moving typical gaps and quantify whether low-gap records dominate the remaining Bayes risk"
            },
            "sampling_status": "not_started",
        },
        "claim_boundary": {
            "established": "The posterior-gap distribution is an exact decoder-independent order parameter for optimal correctability, and the listed observables form a discriminating protocol.",
            "not_established": "No square threshold, critical q, scaling exponent, BKT universality class or thermodynamic phase is inferred from L=5,7,9.",
            "selector_dependency": "none",
        },
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in source_files
        },
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n")
    print(json.dumps({"status": result["status"], "rows": len(rows), "output": str(OUTPUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
