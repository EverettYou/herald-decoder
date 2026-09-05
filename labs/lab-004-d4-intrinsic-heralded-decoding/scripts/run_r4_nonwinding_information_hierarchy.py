#!/usr/bin/env python3
"""Run the preregistered R4.3 matched nonwinding O0--O2 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from math import log2
from pathlib import Path

from run_r4_distinct_observation_matrix import (
    CandidateSupport,
    PrimitiveObservationCatalog,
    Sector,
    _relative_sector,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    LAB_DIR / "r4-nonwinding-information-hierarchy-manifest-2026-08-29.json"
)
DEFAULT_JSON = LAB_DIR / "results/r4-nonwinding-information-hierarchy-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-nonwinding-information-hierarchy-audit.md"


def _prior_probability(candidate: CandidateSupport, edge_count: int, p: float) -> float:
    return p**candidate.weight * (1.0 - p) ** (edge_count - candidate.weight)


def _posterior_metrics(
    catalog: PrimitiveObservationCatalog,
    candidates: list[CandidateSupport] | tuple[CandidateSupport, ...],
    p: float,
    *,
    reference_mask: int,
) -> dict:
    sector_evidence: dict[Sector, float] = defaultdict(float)
    for candidate in candidates:
        sector = _relative_sector(catalog.lattice, reference_mask, candidate.mask)
        sector_evidence[sector] += (
            _prior_probability(candidate, catalog.lattice.edge_count, p)
            * 2.0**candidate.log2_conditional_probability
        )
    evidence = sum(sector_evidence.values())
    if evidence <= 0.0:
        raise AssertionError("R4.3 observation evidence vanished")
    posterior = [value / evidence for value in sector_evidence.values()]
    entropy = -sum(value * log2(value) for value in posterior if value > 0.0)
    return {
        "evidence": evidence,
        "bayes_risk": 1.0 - max(posterior),
        "entropy_bits": entropy,
        "sector_evidence": dict(sector_evidence),
        "posterior_normalization_error": abs(sum(posterior) - 1.0),
    }


def _direct_o0_sector_evidence(
    catalog: PrimitiveObservationCatalog,
    candidates: list[CandidateSupport],
    p: float,
    *,
    reference_mask: int,
) -> dict[Sector, float]:
    """Marginalize charge independently: each compatible mask contributes P(E) once."""
    unique_by_mask: dict[int, CandidateSupport] = {}
    for candidate in candidates:
        unique_by_mask.setdefault(candidate.mask, candidate)
    direct: dict[Sector, float] = defaultdict(float)
    for candidate in unique_by_mask.values():
        sector = _relative_sector(catalog.lattice, reference_mask, candidate.mask)
        direct[sector] += _prior_probability(candidate, catalog.lattice.edge_count, p)
    return dict(direct)


def analyze_information_hierarchy(
    catalog: PrimitiveObservationCatalog,
    priors: tuple[float, ...],
    r42_audit: dict,
) -> dict:
    flux_groups: dict[tuple[int, ...], list[tuple[tuple[int, ...], tuple[CandidateSupport, ...]]]] = defaultdict(list)
    for (flux, charge), candidates in catalog.observations.items():
        flux_groups[flux].append((charge, candidates))

    prior_rows = []
    maximum_o0_posterior_error = 0.0
    maximum_o2_posterior_error = 0.0
    maximum_sector_conservation_error = 0.0
    maximum_total_mass_conservation_error = 0.0
    maximum_r42_recovery_error = 0.0
    tolerance = 1e-12

    r42_by_prior = {float(row["p"]): row for row in r42_audit["prior_summaries"]}
    for p in priors:
        o2_total = 0.0
        o2_weighted_risk = 0.0
        o2_weighted_entropy = 0.0
        for candidates in catalog.observations.values():
            reference_mask = min(candidate.mask for candidate in candidates)
            metrics = _posterior_metrics(
                catalog, candidates, p, reference_mask=reference_mask
            )
            o2_total += metrics["evidence"]
            o2_weighted_risk += metrics["evidence"] * metrics["bayes_risk"]
            o2_weighted_entropy += metrics["evidence"] * metrics["entropy_bits"]
            maximum_o2_posterior_error = max(
                maximum_o2_posterior_error,
                metrics["posterior_normalization_error"],
            )

        o0_total = 0.0
        o0_weighted_risk = 0.0
        o0_weighted_entropy = 0.0
        maximum_charge_refinements = 0
        for rows in flux_groups.values():
            all_candidates = [candidate for _, candidates in rows for candidate in candidates]
            reference_mask = min(candidate.mask for candidate in all_candidates)
            aggregated = _posterior_metrics(
                catalog, all_candidates, p, reference_mask=reference_mask
            )
            direct = _direct_o0_sector_evidence(
                catalog, all_candidates, p, reference_mask=reference_mask
            )
            sectors = set(aggregated["sector_evidence"]) | set(direct)
            maximum_sector_conservation_error = max(
                maximum_sector_conservation_error,
                max(
                    (
                        abs(
                            aggregated["sector_evidence"].get(sector, 0.0)
                            - direct.get(sector, 0.0)
                        )
                        for sector in sectors
                    ),
                    default=0.0,
                ),
            )
            o0_total += aggregated["evidence"]
            o0_weighted_risk += aggregated["evidence"] * aggregated["bayes_risk"]
            o0_weighted_entropy += aggregated["evidence"] * aggregated["entropy_bits"]
            maximum_o0_posterior_error = max(
                maximum_o0_posterior_error,
                aggregated["posterior_normalization_error"],
            )
            maximum_charge_refinements = max(maximum_charge_refinements, len(rows))

        maximum_total_mass_conservation_error = max(
            maximum_total_mass_conservation_error, abs(o0_total - o2_total)
        )
        if o2_total <= 0.0 or o0_total <= 0.0:
            raise AssertionError("R4.3 nonwinding mass vanished")
        o2_risk = o2_weighted_risk / o2_total
        o2_entropy = o2_weighted_entropy / o2_total
        o0_risk = o0_weighted_risk / o0_total
        o0_entropy = o0_weighted_entropy / o0_total
        r42 = r42_by_prior[p]
        recovery_errors = {
            "nonterminal_mass": abs(o2_total - r42["nonterminal_observation_mass"]),
            "o2_bayes_risk": abs(o2_risk - r42["mean_nonterminal_bayes_risk"]),
            "o2_entropy_bits": abs(
                o2_entropy - r42["mean_nonterminal_conditional_entropy_bits"]
            ),
        }
        maximum_r42_recovery_error = max(
            maximum_r42_recovery_error, *recovery_errors.values()
        )
        prior_rows.append(
            {
                "p": p,
                "terminal_winding_prior_mass": r42["terminal_winding_prior_mass"],
                "nonwinding_observation_mass": o2_total,
                "o0_flux_only": {
                    "mean_bayes_risk": o0_risk,
                    "mean_conditional_entropy_bits": o0_entropy,
                },
                "o2_flux_and_charge": {
                    "mean_bayes_risk": o2_risk,
                    "mean_conditional_entropy_bits": o2_entropy,
                },
                "fusion_charge_increment": {
                    "bayes_risk_reduction": o0_risk - o2_risk,
                    "conditional_mutual_information_bits": o0_entropy - o2_entropy,
                },
                "data_processing": {
                    "bayes_risk_monotone": o2_risk <= o0_risk + tolerance,
                    "conditional_entropy_monotone": o2_entropy <= o0_entropy + tolerance,
                },
                "r4_2_recovery_errors": recovery_errors,
                "maximum_charge_refinements_per_flux": maximum_charge_refinements,
            }
        )

    mapping_digest = hashlib.sha256()
    for key in sorted(catalog.observations):
        flux, charge = key
        mapping_digest.update(
            json.dumps(
                {"flux": flux, "charge": charge},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "matched_nonwinding_information_hierarchy_audited",
        "lattice": {
            "size": catalog.lattice.size,
            "vertex_count": catalog.lattice.vertex_count,
            "edge_count": catalog.lattice.edge_count,
        },
        "observation_hierarchy": {
            "o2_distinct_flux_charge_observations": len(catalog.observations),
            "o0_distinct_flux_observations": len(flux_groups),
            "o2_to_o0_mapping_is_total_and_single_valued": True,
            "mapping_digest_sha256": mapping_digest.hexdigest(),
            "conditioned_channel": "nonwinding physical masks only",
            "terminal_winding_status_is_decoder_visible": False,
        },
        "prior_summaries": prior_rows,
        "validation": {
            "maximum_o0_posterior_normalization_error": maximum_o0_posterior_error,
            "maximum_o2_posterior_normalization_error": maximum_o2_posterior_error,
            "maximum_per_flux_sector_evidence_conservation_error": maximum_sector_conservation_error,
            "maximum_total_nonwinding_mass_conservation_error": maximum_total_mass_conservation_error,
            "maximum_r4_2_aggregate_recovery_error": maximum_r42_recovery_error,
            "all_bayes_risk_inequalities_pass": all(
                row["data_processing"]["bayes_risk_monotone"] for row in prior_rows
            ),
            "all_conditional_entropy_inequalities_pass": all(
                row["data_processing"]["conditional_entropy_monotone"]
                for row in prior_rows
            ),
        },
        "new_stochastic_samples": 0,
        "claim_boundary": (
            "Exact O0-versus-O2 information comparison on the primitive "
            "nonwinding-conditioned channel only; not a complete physical-channel "
            "comparison, LER, threshold, or scalable-decoder result."
        ),
    }


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        actual = _sha256(LAB_DIR / relative)
        if actual != expected:
            raise ValueError(f"R4.3 source hash drift: {relative}")


def _render_report(payload: dict) -> str:
    hierarchy = payload["observation_hierarchy"]
    lines = [
        "# R4.3 matched nonwinding O0–O2 information audit",
        "",
        "## Exact matched scope",
        "",
        f"The primitive channel has {hierarchy['o2_distinct_flux_charge_observations']} supported O2 `(flux, charge)` observations. Deterministically deleting charge produces {hierarchy['o0_distinct_flux_observations']} O0 flux-only observations. Both layers use the same nonwinding physical ensemble and priors.",
        "",
        "Terminal winding status is scoring truth, not decoder input. Its prior mass is reported separately; no winding charge likelihood or truth-revealing terminal symbol is introduced.",
        "",
        "## Information supplied by fusion charge",
        "",
        "| p | terminal mass | O0 Bayes risk | O2 Bayes risk | risk reduction | H(L|O0) bits | H(L|O2) bits | I(L;charge|flux) bits |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["prior_summaries"]:
        o0 = row["o0_flux_only"]
        o2 = row["o2_flux_and_charge"]
        gain = row["fusion_charge_increment"]
        lines.append(
            f"| {row['p']:.2f} | {row['terminal_winding_prior_mass']:.6f} | "
            f"{o0['mean_bayes_risk']:.6f} | {o2['mean_bayes_risk']:.6f} | "
            f"{gain['bayes_risk_reduction']:.6f} | "
            f"{o0['mean_conditional_entropy_bits']:.6f} | "
            f"{o2['mean_conditional_entropy_bits']:.6f} | "
            f"{gain['conditional_mutual_information_bits']:.6f} |"
        )
    validation = payload["validation"]
    lines += [
        "",
        "At every registered prior, O2 weakly improves the Bayes decision and weakly lowers conditional logical entropy, as required because O0 is a deterministic coarse-graining of O2.",
        "",
        "## Validation",
        "",
        f"The maximum per-flux, per-sector evidence-conservation error is `{validation['maximum_per_flux_sector_evidence_conservation_error']:.3e}`; total nonwinding-mass conservation is `{validation['maximum_total_nonwinding_mass_conservation_error']:.3e}`. The O2 aggregate reproduces R4.2 to `{validation['maximum_r4_2_aggregate_recovery_error']:.3e}`. O0/O2 posterior normalization and both registered data-processing inequalities pass.",
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
    r42_audit = json.loads(
        (LAB_DIR / "results/r4-distinct-observation-matrix-audit.json").read_text()
    )
    catalog = build_primitive_observation_catalog()
    payload = analyze_information_hierarchy(
        catalog,
        tuple(float(value) for value in manifest["prior_matrix"]),
        r42_audit,
    )
    tolerance = float(manifest["validation"]["absolute_tolerance"])
    checks = payload["validation"]
    numeric_checks = [
        checks["maximum_o0_posterior_normalization_error"],
        checks["maximum_o2_posterior_normalization_error"],
        checks["maximum_per_flux_sector_evidence_conservation_error"],
        checks["maximum_total_nonwinding_mass_conservation_error"],
        checks["maximum_r4_2_aggregate_recovery_error"],
    ]
    if max(numeric_checks) > tolerance:
        raise AssertionError("R4.3 exact conservation or recovery gate failed")
    if not checks["all_bayes_risk_inequalities_pass"]:
        raise AssertionError("R4.3 Bayes-risk data-processing gate failed")
    if not checks["all_conditional_entropy_inequalities_pass"]:
        raise AssertionError("R4.3 entropy data-processing gate failed")
    if payload["new_stochastic_samples"] != 0:
        raise AssertionError("R4.3 stochastic-sample guard failed")

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
