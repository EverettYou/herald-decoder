#!/usr/bin/env python3
"""Run the preregistered R4.4 primitive first-stage loss bridge audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_exact import enumerate_affine_chains
from d4_matching import (
    classify_physical_correction_union,
    d4_check_matrix,
    decode_flux_syndrome,
    published_herald_weights,
    syndrome_only_weights,
)
from run_r4_distinct_observation_matrix import (
    CandidateSupport,
    PrimitiveObservationCatalog,
    Sector,
    _chain,
    _relative_sector,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-first-stage-loss-bridge-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-first-stage-loss-bridge-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-first-stage-loss-bridge-audit.md"


def _mask(chain: np.ndarray) -> int:
    return sum(int(bit) << edge for edge, bit in enumerate(chain))


def _prior(mask: int, edge_count: int, p: float) -> float:
    weight = int(mask.bit_count())
    return p**weight * (1.0 - p) ** (edge_count - weight)


def _sector_risk(
    catalog: PrimitiveObservationCatalog,
    masks: list[int],
    weights: np.ndarray,
) -> float:
    reference = min(masks)
    evidence: dict[Sector, float] = defaultdict(float)
    for mask, weight in zip(masks, weights, strict=True):
        evidence[_relative_sector(catalog.lattice, reference, mask)] += float(weight)
    total = float(np.sum(weights))
    return 1.0 - max(evidence.values()) / total


def _xor_sector_loss_sufficient(
    catalog: PrimitiveObservationCatalog,
    masks: list[int],
    loss_rows: np.ndarray,
) -> bool:
    reference = min(masks)
    by_sector: dict[Sector, list[int]] = defaultdict(list)
    for index, mask in enumerate(masks):
        by_sector[_relative_sector(catalog.lattice, reference, mask)].append(index)
    for indices in by_sector.values():
        baseline = loss_rows[indices[0]]
        if any(not np.array_equal(loss_rows[index], baseline) for index in indices[1:]):
            return False
    return True


def _observation_metrics(
    catalog: PrimitiveObservationCatalog,
    masks: list[int],
    joint_weights: np.ndarray,
    loss_rows: np.ndarray,
    production_action_index: int,
) -> dict:
    evidence = float(np.sum(joint_weights))
    if evidence <= 0.0:
        raise AssertionError("R4.4 observation evidence vanished")
    action_risks = np.asarray(joint_weights @ loss_rows, dtype=np.float64) / evidence
    exact = float(np.min(action_risks))
    production = float(action_risks[production_action_index])
    return {
        "evidence": evidence,
        "exact_union_loss_risk": exact,
        "production_union_loss_risk": production,
        "algorithmic_excess_risk": production - exact,
        "xor_sector_bayes_risk": _sector_risk(catalog, masks, joint_weights),
        "exact_action_tie_count": int(
            np.sum(np.isclose(action_risks, exact, rtol=0.0, atol=1e-12))
        ),
    }


def analyze_first_stage_loss_bridge(
    catalog: PrimitiveObservationCatalog,
    priors: tuple[float, ...],
    r43_audit: dict,
    *,
    candidate_action_guard: int,
) -> dict:
    lattice = catalog.lattice
    check = d4_check_matrix(lattice)
    flux_groups: dict[
        tuple[int, ...],
        list[tuple[tuple[int, ...], tuple[CandidateSupport, ...]]],
    ] = defaultdict(list)
    mask_support_by_flux: dict[tuple[int, ...], dict[int, CandidateSupport]] = defaultdict(dict)
    for (flux, charge), candidates in catalog.observations.items():
        flux_groups[flux].append((charge, candidates))
        for candidate in candidates:
            existing = mask_support_by_flux[flux].setdefault(candidate.mask, candidate)
            if existing.weight != candidate.weight:
                raise AssertionError("R4.4 candidate weight drift across charge records")

    union_loss_cache: dict[int, bool] = {}

    def union_loss(physical_mask: int, correction_mask: int) -> bool:
        union_mask = physical_mask | correction_mask
        if union_mask not in union_loss_cache:
            analysis = classify_physical_correction_union(
                lattice,
                _chain(lattice.edge_count, physical_mask),
                _chain(lattice.edge_count, correction_mask),
            )
            union_loss_cache[union_mask] = any(
                not component.homologically_trivial for component in analysis.components
            )
        return union_loss_cache[union_mask]

    flux_data: dict[tuple[int, ...], dict] = {}
    candidate_action_evaluations = 0
    maximum_action_boundary_error = 0
    action_counts = set()
    syndrome_only_membership_failures = 0
    for flux in sorted(flux_groups):
        syndrome = np.asarray(flux, dtype=np.uint8)
        actions = enumerate_affine_chains(check, syndrome)
        action_masks = [_mask(action) for action in actions]
        action_counts.add(len(actions))
        if len(set(action_masks)) != len(action_masks):
            raise AssertionError("R4.4 affine action set has duplicates")
        maximum_action_boundary_error = max(
            maximum_action_boundary_error,
            int(np.max(np.abs(((check @ actions.T) % 2) - syndrome[:, None]))),
        )
        mask_index = {mask: index for index, mask in enumerate(action_masks)}
        unit = decode_flux_syndrome(lattice, syndrome, syndrome_only_weights(lattice))
        unit_mask = _mask(unit.correction)
        if unit_mask not in mask_index:
            syndrome_only_membership_failures += 1
        physical_masks = sorted(mask_support_by_flux[flux])
        candidate_action_evaluations += len(physical_masks) * len(actions)
        if candidate_action_evaluations > candidate_action_guard:
            raise RuntimeError("R4.4 candidate-action guard exceeded")
        loss_rows = np.asarray(
            [
                [union_loss(physical_mask, correction_mask) for correction_mask in action_masks]
                for physical_mask in physical_masks
            ],
            dtype=np.float64,
        )
        flux_data[flux] = {
            "action_masks": action_masks,
            "mask_index": mask_index,
            "physical_masks": physical_masks,
            "physical_index": {
                mask: index for index, mask in enumerate(physical_masks)
            },
            "loss_rows": loss_rows,
            "syndrome_only_action_index": mask_index[unit_mask],
        }

    if syndrome_only_membership_failures:
        raise AssertionError("R4.4 syndrome-only correction absent from action set")

    o0_structural_insufficient = 0
    o2_structural_insufficient = 0
    o0_rows = []
    for flux in sorted(flux_groups):
        data = flux_data[flux]
        masks = data["physical_masks"]
        sufficient = _xor_sector_loss_sufficient(
            catalog, masks, data["loss_rows"]
        )
        o0_structural_insufficient += int(not sufficient)
        o0_rows.append((flux, masks, sufficient))

    herald_cache: dict[tuple[tuple[int, ...], int], int] = {}
    herald_membership_failures = 0
    o2_rows = []
    maximum_o2_observations = 0
    for flux, charge in sorted(catalog.observations):
        candidates = catalog.observations[(flux, charge)]
        data = flux_data[flux]
        masks = [candidate.mask for candidate in candidates]
        indices = [data["physical_index"][mask] for mask in masks]
        loss_rows = data["loss_rows"][indices]
        sufficient = _xor_sector_loss_sufficient(catalog, masks, loss_rows)
        o2_structural_insufficient += int(not sufficient)
        charge_one_mask = sum(
            (int(value) == 1) << vertex for vertex, value in enumerate(charge)
        )
        cache_key = (flux, charge_one_mask)
        if cache_key not in herald_cache:
            decoded = decode_flux_syndrome(
                lattice,
                np.asarray(flux, dtype=np.uint8),
                published_herald_weights(lattice, np.asarray(charge, dtype=np.int64)),
            )
            correction_mask = _mask(decoded.correction)
            if correction_mask not in data["mask_index"]:
                herald_membership_failures += 1
            herald_cache[cache_key] = data["mask_index"][correction_mask]
        o2_rows.append(
            (flux, charge, candidates, masks, loss_rows, sufficient, herald_cache[cache_key])
        )
        maximum_o2_observations += 1

    if herald_membership_failures:
        raise AssertionError("R4.4 heralded correction absent from action set")

    r43_by_prior = {float(row["p"]): row for row in r43_audit["prior_summaries"]}
    summaries = []
    maximum_o0_o2_flux_evidence_error = 0.0
    maximum_global_normalization_error = 0.0
    maximum_exact_lower_bound_violation = 0.0
    maximum_r43_sector_risk_recovery_error = 0.0
    maximum_observation_direct_sector_risk_gap = 0.0
    for p in priors:
        o0_acc = defaultdict(float)
        o2_acc = defaultdict(float)
        o2_evidence_by_flux = defaultdict(float)

        for flux, masks, sufficient in o0_rows:
            data = flux_data[flux]
            weights = np.asarray(
                [_prior(mask, lattice.edge_count, p) for mask in masks],
                dtype=np.float64,
            )
            metrics = _observation_metrics(
                catalog,
                masks,
                weights,
                data["loss_rows"],
                data["syndrome_only_action_index"],
            )
            evidence = metrics["evidence"]
            o0_acc["mass"] += evidence
            for key in (
                "exact_union_loss_risk",
                "production_union_loss_risk",
                "algorithmic_excess_risk",
                "xor_sector_bayes_risk",
            ):
                o0_acc[key] += evidence * metrics[key]
            o0_acc["insufficient_mass"] += evidence * int(not sufficient)
            maximum_observation_direct_sector_risk_gap = max(
                maximum_observation_direct_sector_risk_gap,
                abs(metrics["exact_union_loss_risk"] - metrics["xor_sector_bayes_risk"]),
            )
            maximum_exact_lower_bound_violation = max(
                maximum_exact_lower_bound_violation,
                metrics["exact_union_loss_risk"]
                - metrics["production_union_loss_risk"],
            )

        for flux, _, candidates, masks, loss_rows, sufficient, action_index in o2_rows:
            weights = np.asarray(
                [
                    _prior(candidate.mask, lattice.edge_count, p)
                    * 2.0**candidate.log2_conditional_probability
                    for candidate in candidates
                ],
                dtype=np.float64,
            )
            metrics = _observation_metrics(
                catalog, masks, weights, loss_rows, action_index
            )
            evidence = metrics["evidence"]
            o2_evidence_by_flux[flux] += evidence
            o2_acc["mass"] += evidence
            for key in (
                "exact_union_loss_risk",
                "production_union_loss_risk",
                "algorithmic_excess_risk",
                "xor_sector_bayes_risk",
            ):
                o2_acc[key] += evidence * metrics[key]
            o2_acc["insufficient_mass"] += evidence * int(not sufficient)
            maximum_observation_direct_sector_risk_gap = max(
                maximum_observation_direct_sector_risk_gap,
                abs(metrics["exact_union_loss_risk"] - metrics["xor_sector_bayes_risk"]),
            )
            maximum_exact_lower_bound_violation = max(
                maximum_exact_lower_bound_violation,
                metrics["exact_union_loss_risk"]
                - metrics["production_union_loss_risk"],
            )

        for flux, masks, _ in o0_rows:
            direct = sum(_prior(mask, lattice.edge_count, p) for mask in masks)
            maximum_o0_o2_flux_evidence_error = max(
                maximum_o0_o2_flux_evidence_error,
                abs(direct - o2_evidence_by_flux[flux]),
            )
        r43 = r43_by_prior[p]
        terminal = float(r43["terminal_winding_prior_mass"])
        maximum_global_normalization_error = max(
            maximum_global_normalization_error,
            abs(terminal + o0_acc["mass"] - 1.0),
            abs(terminal + o2_acc["mass"] - 1.0),
        )

        def normalized(acc: dict[str, float]) -> dict:
            mass = acc["mass"]
            return {
                "nonwinding_observation_mass": mass,
                "exact_union_loss_bayes_risk": acc["exact_union_loss_risk"] / mass,
                "production_union_loss_risk": acc["production_union_loss_risk"] / mass,
                "algorithmic_excess_risk": acc["algorithmic_excess_risk"] / mass,
                "xor_sector_bayes_risk": acc["xor_sector_bayes_risk"] / mass,
                "xor_sector_loss_insufficient_probability": acc["insufficient_mass"] / mass,
            }

        o0 = normalized(o0_acc)
        o2 = normalized(o2_acc)
        maximum_r43_sector_risk_recovery_error = max(
            maximum_r43_sector_risk_recovery_error,
            abs(o0["xor_sector_bayes_risk"] - r43["o0_flux_only"]["mean_bayes_risk"]),
            abs(o2["xor_sector_bayes_risk"] - r43["o2_flux_and_charge"]["mean_bayes_risk"]),
        )
        summaries.append(
            {
                "p": p,
                "terminal_winding_prior_mass": terminal,
                "o0_flux_only": o0,
                "o2_flux_and_charge": o2,
                "decomposition": {
                    "exact_union_loss_information_gain": (
                        o0["exact_union_loss_bayes_risk"]
                        - o2["exact_union_loss_bayes_risk"]
                    ),
                    "syndrome_only_algorithmic_excess": o0["algorithmic_excess_risk"],
                    "heralded_algorithmic_excess": o2["algorithmic_excess_risk"],
                    "production_risk_difference_o0_minus_o2": (
                        o0["production_union_loss_risk"]
                        - o2["production_union_loss_risk"]
                    ),
                },
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "first_stage_loss_bridge_audited",
        "lattice": {
            "size": lattice.size,
            "vertex_count": lattice.vertex_count,
            "edge_count": lattice.edge_count,
        },
        "matrix": {
            "o0_observation_count": len(o0_rows),
            "o2_observation_count": len(o2_rows),
            "action_counts_per_syndrome": sorted(action_counts),
            "candidate_action_evaluations": candidate_action_evaluations,
            "distinct_union_masks_classified": len(union_loss_cache),
            "distinct_herald_decoder_inputs": len(herald_cache),
            "o0_xor_sector_loss_insufficient_observation_count": o0_structural_insufficient,
            "o2_xor_sector_loss_insufficient_observation_count": o2_structural_insufficient,
        },
        "prior_summaries": summaries,
        "validation": {
            "maximum_action_boundary_error": maximum_action_boundary_error,
            "syndrome_only_action_membership_failures": syndrome_only_membership_failures,
            "heralded_action_membership_failures": herald_membership_failures,
            "maximum_o0_vs_marginalized_o2_flux_evidence_error": maximum_o0_o2_flux_evidence_error,
            "maximum_global_normalization_error": maximum_global_normalization_error,
            "maximum_exact_lower_bound_violation": maximum_exact_lower_bound_violation,
            "maximum_r4_3_xor_sector_risk_recovery_error": maximum_r43_sector_risk_recovery_error,
            "maximum_observation_direct_union_vs_xor_sector_risk_gap": maximum_observation_direct_sector_risk_gap,
            "production_decoder_truth_inputs": [],
            "postflux_second_measurement_used": False,
        },
        "new_stochastic_samples": 0,
        "claim_boundary": (
            "Complete exact first-stage primitive nonwinding audit under Appendix-A "
            "Boolean-union loss. It excludes the adaptive second measurement and is "
            "not a full decoder benchmark, LER, threshold, or scalable result."
        ),
    }
    digest = hashlib.sha256(
        json.dumps(payload["prior_summaries"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload["prior_summary_digest_sha256"] = digest
    return payload


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        actual = _sha256(LAB_DIR / relative)
        if actual != expected:
            raise ValueError(f"R4.4 source hash drift: {relative}")


def _render_report(payload: dict) -> str:
    matrix = payload["matrix"]
    lines = [
        "# R4.4 matched first-stage loss bridge audit",
        "",
        "## Exact scope",
        "",
        f"The audit exhausts {matrix['o0_observation_count']} O0 flux records, {matrix['o2_observation_count']} O2 `(flux, charge)` records, and {matrix['action_counts_per_syndrome'][0]} syndrome-faithful corrections per syndrome on the primitive 12-edge nonwinding channel.",
        "",
        "The production syndrome-only and heralded corrections receive only their declared O0 and O2 records. Physical errors are integrated only for posterior scoring. The adaptive second post-flux measurement is excluded.",
        "",
        "## Matched Boolean-union decision risks",
        "",
        "| p | exact O0 | unit-MWPM O0 | O0 excess | exact O2 | herald-MWPM O2 | O2 excess | exact information gain |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["prior_summaries"]:
        o0 = row["o0_flux_only"]
        o2 = row["o2_flux_and_charge"]
        d = row["decomposition"]
        lines.append(
            f"| {row['p']:.2f} | {o0['exact_union_loss_bayes_risk']:.6f} | "
            f"{o0['production_union_loss_risk']:.6f} | {o0['algorithmic_excess_risk']:.6f} | "
            f"{o2['exact_union_loss_bayes_risk']:.6f} | {o2['production_union_loss_risk']:.6f} | "
            f"{o2['algorithmic_excess_risk']:.6f} | {d['exact_union_loss_information_gain']:.6f} |"
        )
    validation = payload["validation"]
    lines += [
        "",
        "## XOR-sector bridge",
        "",
        f"XOR-relative sectors fail the complete Boolean-union action-loss sufficiency test on {matrix['o0_xor_sector_loss_insufficient_observation_count']}/{matrix['o0_observation_count']} O0 observations and {matrix['o2_xor_sector_loss_insufficient_observation_count']}/{matrix['o2_observation_count']} O2 observations. The largest single-observation difference between direct union-loss Bayes risk and XOR-sector Bayes risk is `{validation['maximum_observation_direct_union_vs_xor_sector_risk_gap']:.6g}`. Therefore the direct action-loss posterior, not the XOR-sector posterior by assumption, is the matched practical-stage comparator whenever this count is nonzero.",
        "",
        "## Validation",
        "",
        f"All action sets are syndrome faithful and both public corrections belong to them. The maximum O0-versus-charge-marginalized-O2 evidence error is `{validation['maximum_o0_vs_marginalized_o2_flux_evidence_error']:.3e}`; global normalization error is `{validation['maximum_global_normalization_error']:.3e}`; R4.3 XOR-risk recovery error is `{validation['maximum_r4_3_xor_sector_risk_recovery_error']:.3e}`. Exact risk never exceeds matched production risk beyond tolerance.",
        "",
        "## Claim boundary",
        "",
        payload["claim_boundary"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    _validate_manifest(manifest)
    r43 = json.loads(
        (LAB_DIR / "results/r4-nonwinding-information-hierarchy-audit.json").read_text()
    )
    catalog = build_primitive_observation_catalog()
    payload = analyze_first_stage_loss_bridge(
        catalog,
        tuple(float(value) for value in manifest["analysis"]["prior_matrix"]),
        r43,
        candidate_action_guard=int(
            manifest["compute_budget"]["maximum_candidate_action_evaluations"]
        ),
    )
    tolerance = float(manifest["validation"]["absolute_tolerance"])
    checks = payload["validation"]
    if payload["matrix"]["action_counts_per_syndrome"] != [
        int(manifest["compute_budget"]["expected_actions_per_syndrome"])
    ]:
        raise AssertionError("R4.4 affine action count drift")
    if checks["maximum_action_boundary_error"] != 0:
        raise AssertionError("R4.4 action syndrome fidelity failed")
    if checks["syndrome_only_action_membership_failures"]:
        raise AssertionError("R4.4 syndrome-only membership failed")
    if checks["heralded_action_membership_failures"]:
        raise AssertionError("R4.4 heralded membership failed")
    if max(
        checks["maximum_o0_vs_marginalized_o2_flux_evidence_error"],
        checks["maximum_global_normalization_error"],
        checks["maximum_r4_3_xor_sector_risk_recovery_error"],
        checks["maximum_exact_lower_bound_violation"],
    ) > tolerance:
        raise AssertionError("R4.4 normalization, recovery, or lower-bound gate failed")
    if checks["production_decoder_truth_inputs"]:
        raise AssertionError("R4.4 production decoder received truth")
    if checks["postflux_second_measurement_used"]:
        raise AssertionError("R4.4 used an unregistered adaptive observation")
    if payload["new_stochastic_samples"] != 0:
        raise AssertionError("R4.4 stochastic-sample guard failed")

    payload["manifest"] = {
        "path": str(args.manifest.resolve()),
        "sha256": _sha256(args.manifest),
    }
    payload["implementation"] = {
        "path": str(Path(__file__).resolve()),
        "sha256": _sha256(Path(__file__).resolve()),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(_render_report(payload))


if __name__ == "__main__":
    main()
