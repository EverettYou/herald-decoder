#!/usr/bin/env python3
"""Run the registered R4.5 structural and resource preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import build_charge_lattice
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN
from d4_matching import classify_physical_correction_union, d4_check_matrix
from d4_pipeline import sample_postflux_charge_outcomes
from d4_postflux import infer_periodic_postflux_relations
from d4_postflux import periodic_local_neighborhood
from d4_sequential import (
    chain_mask,
    exact_second_record_channel,
    sequential_observation_key,
    validate_charge_quotient,
)
from run_r4_distinct_observation_matrix import (
    CandidateSupport,
    _chain,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-sequential-postflux-policy-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-sequential-postflux-policy-preflight.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-sequential-postflux-policy-preflight.md"


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        actual = _sha256(LAB_DIR / relative)
        if actual != expected:
            raise ValueError(f"R4.5 source hash drift: {relative}")


def _charge_parallel_edge_diagnostic(lattice, color: int) -> dict:
    opposite = GREEN if color == BLUE else BLUE
    records: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for center in range(opposite, lattice.vertex_count, 2):
        neighbors, _ = periodic_local_neighborhood(lattice, center)
        x, y = lattice.vertex_coordinate(center)
        coordinates = (
            ((x, y), (x, y + 1), (x + 1, y))
            if opposite == GREEN
            else ((x, y), (x - 1, y), (x, y - 1))
        )
        for first, second in ((0, 1), (1, 2), (2, 0)):
            left = int(neighbors[first])
            right = int(neighbors[second])
            dx = coordinates[second][0] - coordinates[first][0]
            dy = coordinates[second][1] - coordinates[first][1]
            if left > right:
                left, right = right, left
                dx, dy = -dx, -dy
            records[(left, right)].append(
                {"opposite_center": center, "displacement": [dx, dy]}
            )
    ambiguous = [
        {
            "endpoints": list(pair),
            "branches": branches,
        }
        for pair, branches in sorted(records.items())
        if len(branches) > 1
    ]
    return {
        "raw_edge_count": sum(len(branches) for branches in records.values()),
        "unique_endpoint_pair_count": len(records),
        "ambiguous_endpoint_pair_count": len(ambiguous),
        "maximum_parallel_multiplicity": max(map(len, records.values())),
        "ambiguous_pairs": ambiguous,
        "interpretation": (
            "Every repeated endpoint pair carries distinct periodic displacement. "
            "Endpoint-only post-flux relations cannot choose the physical branch."
        ),
    }


def run_preflight(manifest: dict) -> dict:
    _validate_manifest(manifest)
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    check = d4_check_matrix(lattice)
    supports_by_flux: dict[tuple[int, ...], dict[int, CandidateSupport]] = defaultdict(dict)
    o2_rows_by_flux: dict[
        tuple[int, ...], list[tuple[tuple[int, ...], tuple[CandidateSupport, ...]]]
    ] = defaultdict(list)
    for (flux, charge), candidates in catalog.observations.items():
        o2_rows_by_flux[flux].append((charge, candidates))
        for candidate in candidates:
            supports_by_flux[flux].setdefault(candidate.mask, candidate)

    actions_by_flux: dict[tuple[int, ...], tuple[tuple[int, np.ndarray], ...]] = {}
    for flux in sorted(supports_by_flux):
        actions = enumerate_affine_chains(check, np.asarray(flux, dtype=np.uint8))
        actions_by_flux[flux] = tuple((chain_mask(action), action) for action in actions)

    start = time.perf_counter()
    pair_stats: dict[tuple[int, int], tuple[bool, int, int, int]] = {}
    unique_pair_count = 0
    terminal_pair_count = 0
    nonterminal_pair_count = 0
    o0_second_record_contributions = 0
    maximum_records = 0
    maximum_active = 0
    maximum_components = 0
    maximum_normalization_error = 0.0
    observable_key_failures = 0
    validation_fixtures: list[tuple[np.ndarray, np.ndarray, tuple[tuple[int, ...], ...]]] = []
    for flux in sorted(supports_by_flux):
        for physical_mask in sorted(supports_by_flux[flux]):
            physical = _chain(lattice.edge_count, physical_mask)
            for action_mask, action in actions_by_flux[flux]:
                channel = exact_second_record_channel(lattice, physical, action)
                unique_pair_count += 1
                if channel.terminal_failure:
                    terminal_pair_count += 1
                    pair_stats[(physical_mask, action_mask)] = (True, 0, 0, 0)
                    continue
                nonterminal_pair_count += 1
                count = len(channel.binary_records)
                o0_second_record_contributions += count
                maximum_records = max(maximum_records, count)
                maximum_active = max(maximum_active, channel.active_vertex_count)
                maximum_components = max(maximum_components, channel.component_count)
                maximum_normalization_error = max(
                    maximum_normalization_error,
                    abs(channel.probability_per_record * count - 1.0),
                )
                pair_stats[(physical_mask, action_mask)] = (
                    False,
                    count,
                    channel.active_vertex_count,
                    channel.component_count,
                )
                for record in channel.binary_records:
                    key = sequential_observation_key((flux,), action_mask, record)
                    if (
                        key[0] != (flux,)
                        or key[1] != action_mask
                        or any(value not in (0, 1) for value in key[2])
                    ):
                        observable_key_failures += 1
                if len(validation_fixtures) < 32:
                    validation_fixtures.append(
                        (physical.copy(), action.copy(), channel.binary_records)
                    )
    channel_seconds = time.perf_counter() - start

    o2_lookup_start = time.perf_counter()
    o2_candidate_action_pairs = 0
    o2_terminal_contributions = 0
    o2_second_record_contributions = 0
    for flux in sorted(o2_rows_by_flux):
        actions = actions_by_flux[flux]
        for _, candidates in o2_rows_by_flux[flux]:
            for candidate in candidates:
                for action_mask, _ in actions:
                    terminal, records, _, _ = pair_stats[(candidate.mask, action_mask)]
                    o2_candidate_action_pairs += 1
                    if terminal:
                        o2_terminal_contributions += 1
                    else:
                        o2_second_record_contributions += records
    o2_lookup_seconds = time.perf_counter() - o2_lookup_start

    sampler_support_failures = 0
    seeded_validation_draws = 0
    for fixture_index, (physical, action, records) in enumerate(validation_fixtures):
        union = classify_physical_correction_union(lattice, physical, action)
        if any(not component.homologically_trivial for component in union.components):
            raise AssertionError("nonterminal validation fixture became terminal")
        relations = infer_periodic_postflux_relations(lattice, physical, action)
        record_set = set(records)
        for seed_offset in range(4):
            sampled = sample_postflux_charge_outcomes(
                lattice.vertex_count,
                relations,
                seed=1009 * fixture_index + seed_offset,
            )
            binary = tuple(0 if int(value) < 0 else int(value) for value in sampled)
            seeded_validation_draws += 1
            if binary not in record_set:
                sampler_support_failures += 1

    quotient_start = time.perf_counter()
    quotient: dict[str, dict | None] = {}
    charge_topology_errors: dict[str, str] = {}
    charge_topology_diagnostics: dict[str, dict] = {}
    for label, color in (("blue", BLUE), ("green", GREEN)):
        charge_topology_diagnostics[label] = _charge_parallel_edge_diagnostic(
            lattice, color
        )
        try:
            charge_lattice = build_charge_lattice(lattice, color)
        except ValueError as error:
            quotient[label] = None
            charge_topology_errors[label] = str(error)
        else:
            quotient[label] = validate_charge_quotient(charge_lattice)
    quotient_seconds = time.perf_counter() - quotient_start

    compute = manifest["compute_budget"]
    total_second = o0_second_record_contributions + o2_second_record_contributions
    raw_guard = int(compute["maximum_streamed_candidate_transition_contributions"])
    if o0_second_record_contributions:
        conservative_projection_seconds = (
            quotient_seconds
            + channel_seconds
            * (1.0 + o2_second_record_contributions / o0_second_record_contributions)
            * len(manifest["scientific_question"]["possible_outcomes"][:4])
        )
    else:
        conservative_projection_seconds = float("inf")
    # A streaming implementation needs at most 64 Y keys for one first action.
    # Budget 2 KiB per key for four priors, sixteen losses, and Python overhead.
    projected_memory_gib = maximum_records * 2048 / (1024**3)
    wall_guard_seconds = float(compute["maximum_projected_wall_time_minutes"]) * 60.0
    memory_guard_gib = float(compute["maximum_resident_memory_gib"])
    quotient_pass = not charge_topology_errors and all(
        result is not None
        and result["sector_count_expected"] == 4
        and result["quotient_failures"] == 0
        and result["within_sector_loss_failures"] == 0
        and result["public_membership_failures"] == 0
        for result in quotient.values()
    )
    validation = {
        "maximum_second_channel_normalization_error": maximum_normalization_error,
        "observable_key_failures": observable_key_failures,
        "seeded_sampler_support_failures": sampler_support_failures,
        "seeded_validation_draws_not_used_as_evidence": seeded_validation_draws,
        "charge_quotient_pass": quotient_pass,
        "charge_topology_errors": charge_topology_errors,
        "transition_guard_pass": total_second <= raw_guard,
        "projected_wall_guard_pass": conservative_projection_seconds <= wall_guard_seconds,
        "projected_memory_guard_pass": projected_memory_gib <= memory_guard_gib,
        "decoder_key_fields": ["initial_observation", "first_action_mask", "binary_Y"],
        "forbidden_decoder_key_fields": [
            "physical_error",
            "active_vertices",
            "relation_components",
            "internal_minus_one_sentinel",
            "effective_error",
        ],
    }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "sequential_channel_preflight_passed"
        if all(
            (
                validation["maximum_second_channel_normalization_error"] <= 1e-12,
                validation["observable_key_failures"] == 0,
                validation["seeded_sampler_support_failures"] == 0,
                validation["charge_quotient_pass"],
                validation["transition_guard_pass"],
                validation["projected_wall_guard_pass"],
                validation["projected_memory_guard_pass"],
            )
        )
        else "sequential_channel_preflight_failed",
        "lattice": {
            "size": lattice.size,
            "vertex_count": lattice.vertex_count,
            "edge_count": lattice.edge_count,
        },
        "channel": {
            "o0_observation_count": len(supports_by_flux),
            "o2_observation_count": len(catalog.observations),
            "candidate_observation_pair_count": catalog.candidate_observation_pair_count,
            "first_actions_per_syndrome": sorted(
                {len(actions) for actions in actions_by_flux.values()}
            ),
            "unique_physical_first_action_pairs": unique_pair_count,
            "terminal_unique_pairs": terminal_pair_count,
            "nonterminal_unique_pairs": nonterminal_pair_count,
            "o0_second_record_transition_contributions": o0_second_record_contributions,
            "o2_candidate_first_action_pairs": o2_candidate_action_pairs,
            "o2_terminal_transition_contributions": o2_terminal_contributions,
            "o2_second_record_transition_contributions": o2_second_record_contributions,
            "total_streamed_second_record_transition_contributions": total_second,
            "maximum_second_records_per_nonterminal_pair": maximum_records,
            "maximum_active_vertices": maximum_active,
            "maximum_parity_components": maximum_components,
        },
        "charge_action_quotient": quotient,
        "charge_topology_diagnostics": charge_topology_diagnostics,
        "resource_projection": {
            "channel_enumeration_seconds": channel_seconds,
            "o2_count_lookup_seconds": o2_lookup_seconds,
            "charge_quotient_validation_seconds": quotient_seconds,
            "conservative_four-prior_projection_seconds": conservative_projection_seconds,
            "projected_streaming_memory_gib": projected_memory_gib,
            "transition_guard": raw_guard,
            "wall_guard_seconds": wall_guard_seconds,
            "memory_guard_gib": memory_guard_gib,
        },
        "validation": validation,
        "new_stochastic_samples": 0,
        "claim_boundary": (
            "Structural and resource preflight only. No posterior policy risk, "
            "algorithmic gap, LER, threshold, or scalable result is computed."
        ),
    }
    payload["structural_digest_sha256"] = hashlib.sha256(
        json.dumps(
            {
                "channel": payload["channel"],
                "charge_action_quotient": quotient,
                "validation": validation,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    channel = payload["channel"]
    resource = payload["resource_projection"]
    validation = payload["validation"]
    lines = [
        "# R4.5 sequential post-flux policy preflight",
        "",
        f"Status: **{payload['status']}**.",
        "",
        "## Structural channel",
        "",
        f"The exact primitive cache contains {channel['unique_physical_first_action_pairs']:,} hidden `(E,A)` pairs: "
        f"{channel['terminal_unique_pairs']:,} terminate at union homology and "
        f"{channel['nonterminal_unique_pairs']:,} emit a second record. The largest "
        f"allowed affine support has {channel['maximum_second_records_per_nonterminal_pair']} binary records.",
        "",
        f"Streaming the eventual audit requires {channel['o0_second_record_transition_contributions']:,} O0 and "
        f"{channel['o2_second_record_transition_contributions']:,} O2 second-record contributions, "
        f"{channel['total_streamed_second_record_transition_contributions']:,} total.",
        "",
        "## Exact charge-action quotient",
        "",
    ]
    for color in ("blue", "green"):
        result = payload["charge_action_quotient"][color]
        if result is None:
            topology = payload["charge_topology_diagnostics"][color]
            lines.append(
                f"- {color}: **blocked** — {validation['charge_topology_errors'][color]}. "
                f"The 12 physical triangular edges collapse to "
                f"{topology['unique_endpoint_pair_count']} endpoint pairs; all "
                f"{topology['ambiguous_endpoint_pair_count']} pairs have two distinct periodic branches."
            )
        else:
            lines.append(
                f"- {color}: {result['supported_even_syndrome_count']} even syndromes, "
                f"{result['affine_actions_per_syndrome']} affine chains per syndrome, "
                f"four classes of {result['class_sizes'][0]} chains; "
                f"{result['within_sector_loss_failures']} within-class loss failures."
            )
    lines.extend(
        [
            "",
            "## Validation and resource gate",
            "",
            f"- maximum second-channel normalization error: `{validation['maximum_second_channel_normalization_error']:.3e}`",
            f"- observation-key or sampler-support failures: `{validation['observable_key_failures']}` / `{validation['seeded_sampler_support_failures']}`",
            f"- conservative four-prior projection: `{resource['conservative_four-prior_projection_seconds']:.1f} s` against `{resource['wall_guard_seconds']:.0f} s`",
            f"- projected streaming memory: `{resource['projected_streaming_memory_gib']:.6f} GiB` against `{resource['memory_guard_gib']:.1f} GiB`",
            f"- transition, wall, and memory guards: `{validation['transition_guard_pass']}`, `{validation['projected_wall_guard_pass']}`, `{validation['projected_memory_guard_pass']}`",
            "",
            "Decoder keys contain only the initial observation, known first-action mask, and full binary `Y`. Hidden relation/active metadata and internal `-1` sentinels are excluded.",
            "",
            "## Claim boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    payload = run_preflight(manifest)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    if payload["status"] != "sequential_channel_preflight_passed":
        raise SystemExit("R4.5 preflight failed")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
