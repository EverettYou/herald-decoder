#!/usr/bin/env python3
"""Run the preregistered R4.2 complete primitive-observation audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from math import log2
from pathlib import Path

import numpy as np

from d4_honeycomb import PeriodicHoneycomb, generate_loop_constraints, periodic_honeycomb
from d4_matching import classify_closed_chain
from d4_observation import evaluate_observation
from d4_r4 import exact_conditioned_logical_posterior
from d4_sampler import observation_from_error_edges


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-distinct-observation-matrix-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-distinct-observation-matrix-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-distinct-observation-matrix-audit.md"


ObservationKey = tuple[tuple[int, ...], tuple[int, ...]]
Sector = tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class CandidateSupport:
    mask: int
    weight: int
    log2_conditional_probability: int


@dataclass(frozen=True)
class PrimitiveObservationCatalog:
    lattice: PeriodicHoneycomb
    observations: dict[ObservationKey, tuple[CandidateSupport, ...]]
    terminal_winding_masks: tuple[int, ...]
    nonwinding_mask_count: int
    candidate_observation_pair_count: int
    maximum_per_error_normalization_error: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _chain(edge_count: int, mask: int) -> np.ndarray:
    return np.asarray(
        [(mask >> edge) & 1 for edge in range(edge_count)], dtype=np.uint8
    )


def _mask(chain: np.ndarray) -> int:
    return sum(int(bit) << edge for edge, bit in enumerate(chain))


def _has_terminal_winding(analysis) -> bool:
    return any(
        component.nonbranching_closed and not component.homologically_trivial
        for component in analysis.components
    )


def _relative_sector(lattice: PeriodicHoneycomb, reference_mask: int, mask: int) -> Sector:
    residual = _chain(lattice.edge_count, reference_mask ^ mask)
    analysis = classify_closed_chain(lattice, residual)
    return tuple(
        sorted(
            {
                winding
                for component in analysis.components
                for winding in component.winding_vectors
            }
        )
    )


def _sector_json(sector: Sector) -> list[list[int]]:
    return [[int(x), int(y)] for x, y in sector]


def _logsumexp2(values: list[float]) -> float:
    maximum = max(values)
    return maximum + log2(sum(2.0 ** (value - maximum) for value in values))


def observation_key(flux: np.ndarray, charge: np.ndarray) -> ObservationKey:
    return tuple(int(value) for value in flux), tuple(int(value) for value in charge)


def build_primitive_observation_catalog(
    *, candidate_observation_pair_guard: int = 1_000_000
) -> PrimitiveObservationCatalog:
    lattice = periodic_honeycomb(2)
    observations: dict[ObservationKey, list[CandidateSupport]] = {}
    terminal_masks: list[int] = []
    nonwinding_count = 0
    pair_count = 0
    maximum_normalization_error = 0.0

    for mask in range(1 << lattice.edge_count):
        error = _chain(lattice.edge_count, mask)
        selected = error.astype(bool)
        analysis = generate_loop_constraints(lattice, selected)
        if _has_terminal_winding(analysis):
            terminal_masks.append(mask)
            continue
        nonwinding_count += 1
        degrees = np.bincount(
            lattice.edge_vertices[selected].ravel(), minlength=lattice.vertex_count
        )
        flux = np.asarray(degrees % 2, dtype=np.uint8)
        internal_vertices = tuple(int(v) for v in np.flatnonzero(degrees == 2))
        allowed_probability = 0.0
        allowed_count = 0
        for bits in product((0, 1), repeat=len(internal_vertices)):
            charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
            if internal_vertices:
                charge[np.asarray(internal_vertices, dtype=np.int64)] = bits
            evaluation = evaluate_observation(
                lattice.edge_vertices,
                error,
                flux,
                charge,
                analysis.constraints,
            )
            if not evaluation.allowed or evaluation.log2_probability is None:
                continue
            key = observation_key(flux, charge)
            observations.setdefault(key, []).append(
                CandidateSupport(
                    mask=mask,
                    weight=int(error.sum()),
                    log2_conditional_probability=evaluation.log2_probability,
                )
            )
            allowed_probability += evaluation.probability
            allowed_count += 1
            pair_count += 1
            if pair_count > candidate_observation_pair_guard:
                raise RuntimeError("R4.2 candidate-observation pair guard exceeded")
        if allowed_count == 0:
            raise AssertionError(f"nonwinding mask {mask} has no allowed observation")
        maximum_normalization_error = max(
            maximum_normalization_error, abs(allowed_probability - 1.0)
        )

    return PrimitiveObservationCatalog(
        lattice=lattice,
        observations={key: tuple(value) for key, value in observations.items()},
        terminal_winding_masks=tuple(terminal_masks),
        nonwinding_mask_count=nonwinding_count,
        candidate_observation_pair_count=pair_count,
        maximum_per_error_normalization_error=maximum_normalization_error,
    )


def _analyze_observation(
    lattice: PeriodicHoneycomb,
    candidates: tuple[CandidateSupport, ...],
    error_rate: float,
) -> dict:
    reference_mask = min(candidate.mask for candidate in candidates)
    sector_by_mask = {
        candidate.mask: _relative_sector(lattice, reference_mask, candidate.mask)
        for candidate in candidates
    }
    log_error = log2(error_rate)
    log_no_error = log2(1.0 - error_rate)
    log_weight = {
        candidate.mask: (
            candidate.weight * log_error
            + (lattice.edge_count - candidate.weight) * log_no_error
            + candidate.log2_conditional_probability
        )
        for candidate in candidates
    }
    grouped: dict[Sector, list[float]] = {}
    for candidate in candidates:
        grouped.setdefault(sector_by_mask[candidate.mask], []).append(
            log_weight[candidate.mask]
        )
    sector_logs = {sector: _logsumexp2(values) for sector, values in grouped.items()}
    total_log = _logsumexp2(list(sector_logs.values()))
    sector_probabilities = {
        sector: 2.0 ** (value - total_log) for sector, value in sector_logs.items()
    }
    probabilities = tuple(sector_probabilities.values())
    entropy = -sum(
        probability * log2(probability)
        for probability in probabilities
        if probability > 0.0
    )
    ranked_sector_logs = sorted(sector_logs.values(), reverse=True)
    sector_maximum = ranked_sector_logs[0]
    bayes_sectors = {
        sector
        for sector, value in sector_logs.items()
        if np.isclose(value, sector_maximum, rtol=0.0, atol=1e-12)
    }
    configuration_maximum = max(log_weight.values())
    configuration_masks = {
        mask
        for mask, value in log_weight.items()
        if np.isclose(value, configuration_maximum, rtol=0.0, atol=1e-12)
    }
    configuration_sectors = {sector_by_mask[mask] for mask in configuration_masks}
    if len(configuration_sectors) == len(bayes_sectors) == 1 and configuration_sectors == bayes_sectors:
        agreement_class = "exact_singleton_agreement"
    elif configuration_sectors.isdisjoint(bayes_sectors):
        agreement_class = "forced_disjoint_disagreement"
    else:
        agreement_class = "overlapping_or_tied_ambiguity"
    lexicographic_mask = min(configuration_masks)
    lexicographic_sector = sector_by_mask[lexicographic_mask]
    return {
        "candidate_count": len(candidates),
        "sector_count": len(grouped),
        "reference_mask": reference_mask,
        "log2_observation_evidence": total_log,
        "observation_evidence": 2.0 ** total_log,
        "conditional_entropy_bits": entropy,
        "bayes_logical_failure_probability": 1.0 - max(probabilities),
        "top_two_log2_evidence_gap": (
            None if len(ranked_sector_logs) == 1 else ranked_sector_logs[0] - ranked_sector_logs[1]
        ),
        "configuration_map_mask_count": len(configuration_masks),
        "configuration_map_masks": sorted(configuration_masks),
        "configuration_map_sectors": sorted(_sector_json(value) for value in configuration_sectors),
        "bayes_sector_mode_count": len(bayes_sectors),
        "bayes_sectors": sorted(_sector_json(value) for value in bayes_sectors),
        "agreement_class": agreement_class,
        "lexicographic_configuration_map_mask": lexicographic_mask,
        "lexicographic_configuration_map_is_bayes_optimal": lexicographic_sector in bayes_sectors,
        "sectors": [
            {
                "relative_windings": _sector_json(sector),
                "candidate_count": len(grouped[sector]),
                "log2_evidence": sector_logs[sector],
                "posterior_probability": sector_probabilities[sector],
            }
            for sector in sorted(grouped)
        ],
    }


def analyze_catalog(catalog: PrimitiveObservationCatalog, priors: tuple[float, ...]) -> dict:
    lattice = catalog.lattice
    ordered_observations = sorted(catalog.observations)
    structural_candidate_histogram = Counter(
        len(catalog.observations[key]) for key in ordered_observations
    )
    structural_sector_histogram = Counter()
    observation_rows: list[dict] = []
    for index, key in enumerate(ordered_observations):
        flux, charge = key
        candidates = catalog.observations[key]
        base = _analyze_observation(lattice, candidates, priors[0])
        structural_sector_histogram[base["sector_count"]] += 1
        observation_rows.append(
            {
                "observation_index": index,
                "flux": list(flux),
                "charge": list(charge),
                "candidate_masks": [candidate.mask for candidate in candidates],
                "by_prior": {str(prior): _analyze_observation(lattice, candidates, prior) for prior in priors},
            }
        )

    prior_summaries = []
    maximum_global_normalization_error = 0.0
    for prior in priors:
        prior_key = str(prior)
        terminal_mass = sum(
            prior ** int(mask.bit_count())
            * (1.0 - prior) ** (lattice.edge_count - int(mask.bit_count()))
            for mask in catalog.terminal_winding_masks
        )
        nonterminal_mass = sum(
            row["by_prior"][prior_key]["observation_evidence"]
            for row in observation_rows
        )
        normalization_error = abs(terminal_mass + nonterminal_mass - 1.0)
        maximum_global_normalization_error = max(
            maximum_global_normalization_error, normalization_error
        )
        if nonterminal_mass <= 0.0:
            raise AssertionError("R4.2 nonterminal observation mass vanished")
        weighted_risk = sum(
            row["by_prior"][prior_key]["observation_evidence"]
            * row["by_prior"][prior_key]["bayes_logical_failure_probability"]
            for row in observation_rows
        )
        weighted_entropy = sum(
            row["by_prior"][prior_key]["observation_evidence"]
            * row["by_prior"][prior_key]["conditional_entropy_bits"]
            for row in observation_rows
        )
        agreement_count = Counter(
            row["by_prior"][prior_key]["agreement_class"] for row in observation_rows
        )
        agreement_mass = Counter()
        sector_count_mass = Counter()
        lexicographic_failure_mass = 0.0
        for row in observation_rows:
            result = row["by_prior"][prior_key]
            evidence = result["observation_evidence"]
            agreement_mass[result["agreement_class"]] += evidence
            sector_count_mass[result["sector_count"]] += evidence
            if not result["lexicographic_configuration_map_is_bayes_optimal"]:
                lexicographic_failure_mass += evidence
        prior_summaries.append(
            {
                "p": prior,
                "terminal_winding_prior_mass": terminal_mass,
                "nonterminal_observation_mass": nonterminal_mass,
                "normalization_error": normalization_error,
                "mean_nonterminal_bayes_risk": weighted_risk / nonterminal_mass,
                "combined_ground_state_relative_bayes_failure_probability": terminal_mass + weighted_risk,
                "mean_nonterminal_conditional_entropy_bits": weighted_entropy / nonterminal_mass,
                "agreement_structural_counts": dict(sorted(agreement_count.items())),
                "agreement_nonterminal_probability": {
                    key: value / nonterminal_mass for key, value in sorted(agreement_mass.items())
                },
                "sector_count_nonterminal_probability": {
                    str(key): value / nonterminal_mass for key, value in sorted(sector_count_mass.items())
                },
                "lexicographic_configuration_map_nonbayes_probability": lexicographic_failure_mass / nonterminal_mass,
            }
        )

    fixture_checks = _fixture_checks(catalog, observation_rows)
    matrix_digest = hashlib.sha256()
    maximum_sector_normalization_error = 0.0
    agreement_classes: set[str] = set()
    disagreement_examples: dict[str, list[dict]] = {}
    for row in observation_rows:
        matrix_digest.update(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        )
        for prior_key, result in row["by_prior"].items():
            maximum_sector_normalization_error = max(
                maximum_sector_normalization_error,
                abs(
                    sum(
                        sector["posterior_probability"]
                        for sector in result["sectors"]
                    )
                    - 1.0
                ),
            )
            agreement_classes.add(result["agreement_class"])
            if result["agreement_class"] == "forced_disjoint_disagreement":
                examples = disagreement_examples.setdefault(prior_key, [])
                if len(examples) < 3:
                    examples.append(
                        {
                            "observation_index": row["observation_index"],
                            "flux": row["flux"],
                            "charge": row["charge"],
                            "candidate_masks": row["candidate_masks"],
                            "configuration_map_masks": result["configuration_map_masks"],
                            "configuration_map_sectors": result["configuration_map_sectors"],
                            "bayes_sectors": result["bayes_sectors"],
                        }
                    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_distinct_observation_matrix_audited",
        "lattice": {
            "size": lattice.size,
            "vertex_count": lattice.vertex_count,
            "edge_count": lattice.edge_count,
        },
        "enumeration": {
            "physical_mask_count": 1 << lattice.edge_count,
            "nonwinding_mask_count": catalog.nonwinding_mask_count,
            "terminal_winding_mask_count": len(catalog.terminal_winding_masks),
            "distinct_nonwinding_observation_count": len(catalog.observations),
            "candidate_observation_pair_count": catalog.candidate_observation_pair_count,
            "maximum_per_error_observation_normalization_error": catalog.maximum_per_error_normalization_error,
            "candidate_count_histogram": {str(key): value for key, value in sorted(structural_candidate_histogram.items())},
            "sector_count_histogram": {str(key): value for key, value in sorted(structural_sector_histogram.items())},
        },
        "prior_summaries": prior_summaries,
        "maximum_global_normalization_error": maximum_global_normalization_error,
        "fixture_checks": fixture_checks,
        "observation_matrix_digest_sha256": matrix_digest.hexdigest(),
        "posterior_validation": {
            "maximum_sector_posterior_normalization_error": maximum_sector_normalization_error,
            "agreement_classes_present": sorted(agreement_classes),
            "forced_disagreement_examples": disagreement_examples,
            "full_observation_rows_written": False,
            "reason": "The deterministic complete matrix is hashed and summarized instead of emitting a 100+ MB dashboard-hostile JSON payload.",
        },
        "new_stochastic_samples": 0,
        "claim_boundary": "Complete exact audit of the primitive 12-edge fixture only; not an LER, threshold, or scalable-decoder result.",
    }


def _fixture_checks(catalog: PrimitiveObservationCatalog, observation_rows: list[dict]) -> dict:
    lattice = catalog.lattice
    by_key = {
        (tuple(row["flux"]), tuple(row["charge"])): row for row in observation_rows
    }
    physical = _chain(lattice.edge_count, 73)
    record = observation_from_error_edges(lattice, physical, seed=11)
    if record.charge_outcomes is None:
        raise AssertionError("R4.0 fixture unexpectedly became terminal")
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(record.flux_vertices)] = 1
    key = observation_key(flux, np.asarray(record.charge_outcomes, dtype=np.int64))
    row = by_key[key]
    expected = {
        "0.1": [1 / 244, 81 / 244, 81 / 244, 81 / 244],
        "0.6": [4 / 21, 4 / 21, 4 / 21, 3 / 7],
    }
    r40_errors = {}
    for prior_key, target in expected.items():
        actual = sorted(
            sector["posterior_probability"]
            for sector in row["by_prior"][prior_key]["sectors"]
        )
        r40_errors[prior_key] = max(abs(left - right) for left, right in zip(actual, target))

    r41_flux = (1, 0, 1, 1, 1, 1, 0, 1)
    r41_charge = tuple([-1] * lattice.vertex_count)
    r41_row = by_key[(r41_flux, r41_charge)]
    r41_candidate_masks = r41_row["candidate_masks"]
    r41_one_sector = all(
        r41_row["by_prior"][str(prior)]["sector_count"] == 1
        for prior in (0.1, 0.3, 0.5, 0.6)
    )

    subset_indices = sorted({0, len(observation_rows) // 2, len(observation_rows) - 1})
    subset_errors = []
    for index in subset_indices:
        subset_row = observation_rows[index]
        exact = exact_conditioned_logical_posterior(
            lattice,
            np.asarray(subset_row["flux"], dtype=np.uint8),
            np.asarray(subset_row["charge"], dtype=np.int64),
            0.3,
        )
        expected_probabilities = sorted(
            sector.posterior_probability for sector in exact.sectors
        )
        actual_probabilities = sorted(
            sector["posterior_probability"]
            for sector in subset_row["by_prior"]["0.3"]["sectors"]
        )
        subset_errors.append(
            {
                "observation_index": index,
                "maximum_sector_probability_error": max(
                    abs(left - right)
                    for left, right in zip(expected_probabilities, actual_probabilities)
                ),
                "bayes_risk_error": abs(
                    exact.bayes_logical_failure_probability
                    - subset_row["by_prior"]["0.3"]["bayes_logical_failure_probability"]
                ),
            }
        )
    return {
        "r4_0_maximum_probability_errors": r40_errors,
        "r4_1_candidate_masks": r41_candidate_masks,
        "r4_1_candidate_masks_equal_98_140": r41_candidate_masks == [98, 140],
        "r4_1_one_sector_at_every_prior": r41_one_sector,
        "independent_subset": subset_errors,
    }


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        actual = _sha256(LAB_DIR / relative)
        if actual != expected:
            raise ValueError(f"R4.2 source hash drift: {relative}")


def _render_report(payload: dict) -> str:
    enumeration = payload["enumeration"]
    lines = [
        "# R4.2 complete distinct-observation posterior audit",
        "",
        "## Exact scope",
        "",
        f"The primitive 12-edge fixture contains {enumeration['physical_mask_count']} physical masks. "
        f"Exactly {enumeration['terminal_winding_mask_count']} are terminal winding failures; the other "
        f"{enumeration['nonwinding_mask_count']} masks generate {enumeration['distinct_nonwinding_observation_count']} "
        f"distinct supported observations through {enumeration['candidate_observation_pair_count']} candidate-observation pairs.",
        "",
        "All allowed records normalize for every nonwinding error, and terminal mass plus nonwinding observation evidence normalizes at every registered prior. No stochastic sample or winding-sector charge record is introduced.",
        "",
        "## Prior-weighted exact inference",
        "",
        "| p | terminal winding mass | mean nonterminal Bayes risk | combined failure | mean conditional entropy (bits) | forced MAP/Bayes disagreement |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in payload["prior_summaries"]:
        forced = summary["agreement_nonterminal_probability"].get(
            "forced_disjoint_disagreement", 0.0
        )
        lines.append(
            f"| {summary['p']:.2f} | {summary['terminal_winding_prior_mass']:.6f} | "
            f"{summary['mean_nonterminal_bayes_risk']:.6f} | "
            f"{summary['combined_ground_state_relative_bayes_failure_probability']:.6f} | "
            f"{summary['mean_nonterminal_conditional_entropy_bits']:.6f} | {forced:.6f} |"
        )
    lines += [
        "",
        "The MAP comparison is set-valued: a tied configuration optimum is not forced into an arbitrary sector. `forced` means every maximum-weight configuration lies outside every maximum-evidence logical sector. The lexicographic convention remains a separately recorded implementation diagnostic.",
        "",
        "## Validation",
        "",
        f"The maximum per-error record-normalization error is {enumeration['maximum_per_error_observation_normalization_error']:.3e}; the maximum global normalization error is {payload['maximum_global_normalization_error']:.3e}. R4.0 exact fractions, the masks 98/140 one-sector R4.1 sum, and three independently re-evaluated observations all pass.",
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
    guard = int(manifest["observation_enumeration"]["candidate_observation_pair_guard"])
    catalog = build_primitive_observation_catalog(
        candidate_observation_pair_guard=guard
    )
    payload = analyze_catalog(catalog, tuple(float(value) for value in manifest["prior_matrix"]))
    if len(catalog.terminal_winding_masks) != 123:
        raise AssertionError("R4.2 terminal winding count drift")
    if catalog.maximum_per_error_normalization_error > 1e-12:
        raise AssertionError("R4.2 per-error observation normalization failed")
    if payload["maximum_global_normalization_error"] > 1e-12:
        raise AssertionError("R4.2 global evidence normalization failed")
    if payload["posterior_validation"]["maximum_sector_posterior_normalization_error"] > 1e-12:
        raise AssertionError("R4.2 sector posterior normalization failed")
    checks = payload["fixture_checks"]
    if max(checks["r4_0_maximum_probability_errors"].values()) > 1e-12:
        raise AssertionError("R4.2 no longer reproduces R4.0")
    if not checks["r4_1_candidate_masks_equal_98_140"] or not checks["r4_1_one_sector_at_every_prior"]:
        raise AssertionError("R4.2 no longer reproduces R4.1")
    if any(
        max(row["maximum_sector_probability_error"], row["bayes_risk_error"]) > 1e-12
        for row in checks["independent_subset"]
    ):
        raise AssertionError("R4.2 independent posterior subset mismatch")
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
