#!/usr/bin/env python3
"""Run the registered R4.5c corrected structural and resource preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge import charge_chain_boundary, charge_check_matrix
from d4_charge_multigraph import (
    branch_chain_sector,
    decode_expanded_branch_syndrome,
    infer_branch_postflux_relations,
    validate_endpoint_projection,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN
from d4_matching import d4_check_matrix
from d4_sequential import chain_mask, exact_second_record_channel, sequential_observation_key
from d4_sequential_corrected import (
    audit_relation_cycle_kernel,
    build_branch_representative_context,
    effective_branch_chain_from_record,
    relation_branch_ids,
)
from run_r4_distinct_observation_matrix import (
    CandidateSupport,
    _chain,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-corrected-sequential-policy-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-corrected-sequential-policy-preflight.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-corrected-sequential-policy-preflight.md"
LEGACY_PREFLIGHT = LAB_DIR / "results/r4-sequential-postflux-policy-preflight.json"
EXPECTED_CHANNEL_COUNTS = {
    "unique_physical_first_action_pairs": 127136,
    "terminal_unique_pairs": 120320,
    "nonterminal_unique_pairs": 6816,
    "o0_second_record_transition_contributions": 257020,
    "o2_candidate_first_action_pairs": 1595360,
    "o2_terminal_transition_contributions": 1545772,
    "o2_second_record_transition_contributions": 2063916,
    "total_streamed_second_record_transition_contributions": 2320936,
}


def _validate_manifest(manifest: dict) -> None:
    for relative, expected in manifest["source_freeze"].items():
        actual = _sha256(LAB_DIR / relative)
        if actual != expected:
            raise ValueError(f"R4.5c source hash drift: {relative}")


def _syndrome_for_color(context, record: tuple[int, ...]) -> np.ndarray:
    return np.asarray(
        [record[int(vertex)] for vertex in context.charge_lattice.vertex_ids],
        dtype=np.uint8,
    )


def _build_exact_action_cache(context, lattice, color: int) -> dict[int, dict]:
    check = charge_check_matrix(context.charge_lattice)
    cache = {}
    for syndrome_mask in range(1 << context.charge_lattice.vertex_count):
        syndrome = np.asarray(
            [
                (syndrome_mask >> vertex) & 1
                for vertex in range(context.charge_lattice.vertex_count)
            ],
            dtype=np.uint8,
        )
        if int(np.sum(syndrome)) % 2:
            continue
        actions = enumerate_affine_chains(check, syndrome)
        reference = min(actions, key=chain_mask)
        sectors: dict[tuple[int, int], set[int]] = defaultdict(set)
        for action in actions:
            sectors[branch_chain_sector(lattice, color, action ^ reference)].add(
                chain_mask(action)
            )
        cache[syndrome_mask] = {
            "syndrome": syndrome,
            "action_masks": {chain_mask(action) for action in actions},
            "reference": reference,
            "sector_sizes": {str(key): len(value) for key, value in sorted(sectors.items())},
            "sector_keys": set(sectors),
        }
    return cache


def run_preflight(manifest: dict) -> dict:
    _validate_manifest(manifest)
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    check = d4_check_matrix(lattice)
    contexts = {
        color: build_branch_representative_context(lattice, color)
        for color in (BLUE, GREEN)
    }
    exact_actions = {
        color: _build_exact_action_cache(contexts[color], lattice, color)
        for color in (BLUE, GREEN)
    }

    supports_by_flux: dict[tuple[int, ...], dict[int, CandidateSupport]] = defaultdict(dict)
    o2_rows_by_flux: dict[
        tuple[int, ...], list[tuple[tuple[int, ...], tuple[CandidateSupport, ...]]]
    ] = defaultdict(list)
    for (flux, charge), candidates in catalog.observations.items():
        o2_rows_by_flux[flux].append((charge, candidates))
        for candidate in candidates:
            supports_by_flux[flux].setdefault(candidate.mask, candidate)
    actions_by_flux = {
        flux: tuple(
            (chain_mask(action), action)
            for action in enumerate_affine_chains(check, np.asarray(flux, dtype=np.uint8))
        )
        for flux in sorted(supports_by_flux)
    }

    start = time.perf_counter()
    pair_stats: dict[tuple[int, int], tuple[bool, int]] = {}
    unique_pairs = terminal_pairs = nonterminal_pairs = 0
    o0_second = maximum_records = maximum_active = maximum_components = 0
    maximum_normalization_error = 0.0
    observable_key_failures = 0
    projection_failures = provenance_failures = 0
    relation_occurrences = 0
    representative_checks = representative_boundary_failures = 0
    representative_affine_membership_failures = 0
    kernel_cache = {}
    kernel_candidate_checks = kernel_chain_checks = kernel_nontrivial = 0
    failure_witnesses = []

    for flux in sorted(supports_by_flux):
        for physical_mask in sorted(supports_by_flux[flux]):
            physical = _chain(lattice.edge_count, physical_mask)
            for action_mask, action in actions_by_flux[flux]:
                channel = exact_second_record_channel(lattice, physical, action)
                unique_pairs += 1
                if channel.terminal_failure:
                    terminal_pairs += 1
                    pair_stats[(physical_mask, action_mask)] = (True, 0)
                    continue
                nonterminal_pairs += 1
                record_count = len(channel.binary_records)
                pair_stats[(physical_mask, action_mask)] = (False, record_count)
                o0_second += record_count
                maximum_records = max(maximum_records, record_count)
                maximum_active = max(maximum_active, channel.active_vertex_count)
                maximum_components = max(maximum_components, channel.component_count)
                maximum_normalization_error = max(
                    maximum_normalization_error,
                    abs(channel.probability_per_record * record_count - 1.0),
                )
                try:
                    enriched = infer_branch_postflux_relations(lattice, physical, action)
                    agrees, _ = validate_endpoint_projection(
                        lattice, physical, action, enriched
                    )
                except (ValueError, RuntimeError) as error:
                    provenance_failures += 1
                    if len(failure_witnesses) < 16:
                        failure_witnesses.append(
                            {
                                "failure": "branch_provenance",
                                "physical_mask": physical_mask,
                                "action_mask": action_mask,
                                "detail": str(error),
                            }
                        )
                    continue
                if not agrees:
                    projection_failures += 1
                relation_occurrences += len(enriched.relations)

                for color in (BLUE, GREEN):
                    branch_ids = relation_branch_ids(enriched, color)
                    signature = (color, branch_ids)
                    if signature not in kernel_cache:
                        audit = audit_relation_cycle_kernel(
                            lattice, color, branch_ids, contexts[color]
                        )
                        kernel_cache[signature] = audit
                        kernel_candidate_checks += audit.candidate_chain_count
                        kernel_chain_checks += audit.kernel_chain_count
                        kernel_nontrivial += audit.nontrivial_kernel_count
                        if not audit.passed and len(failure_witnesses) < 16:
                            failure_witnesses.append(
                                {
                                    "failure": "nontrivial_relation_cycle_kernel",
                                    "physical_mask": physical_mask,
                                    "action_mask": action_mask,
                                    "color": color,
                                    "branch_ids": list(branch_ids),
                                    "kernel_mask": audit.first_nontrivial_mask,
                                    "sector": list(audit.first_nontrivial_sector or ()),
                                }
                            )

                for record in channel.binary_records:
                    key = sequential_observation_key((flux,), action_mask, record)
                    if key != ((flux,), action_mask, tuple(record)):
                        observable_key_failures += 1
                    for color in (BLUE, GREEN):
                        representative_checks += 1
                        context = contexts[color]
                        syndrome = _syndrome_for_color(context, record)
                        syndrome_mask = chain_mask(syndrome)
                        try:
                            representative = effective_branch_chain_from_record(
                                lattice,
                                color,
                                enriched,
                                record,
                                context,
                            )
                        except (ValueError, RuntimeError) as error:
                            representative_boundary_failures += 1
                            if len(failure_witnesses) < 16:
                                failure_witnesses.append(
                                    {
                                        "failure": "representative_boundary",
                                        "physical_mask": physical_mask,
                                        "action_mask": action_mask,
                                        "color": color,
                                        "record": list(record),
                                        "detail": str(error),
                                    }
                                )
                            continue
                        if chain_mask(representative) not in exact_actions[color][syndrome_mask]["action_masks"]:
                            representative_affine_membership_failures += 1

    scan_seconds = time.perf_counter() - start

    o2_start = time.perf_counter()
    o2_candidate_pairs = o2_terminal = o2_second = 0
    for flux in sorted(o2_rows_by_flux):
        for _, candidates in o2_rows_by_flux[flux]:
            for candidate in candidates:
                for action_mask, _ in actions_by_flux[flux]:
                    terminal, count = pair_stats[(candidate.mask, action_mask)]
                    o2_candidate_pairs += 1
                    if terminal:
                        o2_terminal += 1
                    else:
                        o2_second += count
    o2_seconds = time.perf_counter() - o2_start

    public_start = time.perf_counter()
    quotient_failures = public_boundary_failures = public_membership_failures = 0
    public_sector_failures = public_objective_failures = 0
    maximum_public_objective_error = 0.0
    quotient_summary = {}
    for label, color in (("blue", BLUE), ("green", GREEN)):
        context = contexts[color]
        rows = exact_actions[color]
        sector_sizes = sorted(
            {size for row in rows.values() for size in row["sector_sizes"].values()}
        )
        color_quotient_failures = sum(
            row["sector_keys"] != {(0, 0), (0, 1), (1, 0), (1, 1)}
            or set(row["sector_sizes"].values()) != {128}
            for row in rows.values()
        )
        quotient_failures += color_quotient_failures
        for syndrome_mask, row in rows.items():
            syndrome = row["syndrome"]
            correction, objective = decode_expanded_branch_syndrome(
                lattice,
                color,
                syndrome,
                np.ones(context.charge_lattice.edge_count, dtype=np.float64),
            )
            if not np.array_equal(
                charge_chain_boundary(context.charge_lattice, correction), syndrome
            ):
                public_boundary_failures += 1
            if chain_mask(correction) not in row["action_masks"]:
                public_membership_failures += 1
            sector = branch_chain_sector(lattice, color, correction ^ row["reference"])
            if sector not in row["sector_keys"]:
                public_sector_failures += 1
            exact_objective = min(mask.bit_count() for mask in row["action_masks"])
            error = abs(objective - exact_objective)
            maximum_public_objective_error = max(maximum_public_objective_error, error)
            if error > 1e-6:
                public_objective_failures += 1
        quotient_summary[label] = {
            "even_syndrome_count": len(rows),
            "affine_actions_per_syndrome": 512,
            "sector_count": 4,
            "sector_sizes": sector_sizes,
            "quotient_failures": color_quotient_failures,
        }
    public_seconds = time.perf_counter() - public_start

    total_second = o0_second + o2_second
    channel = {
        "o0_observation_count": len(supports_by_flux),
        "o2_observation_count": len(catalog.observations),
        "candidate_observation_pair_count": catalog.candidate_observation_pair_count,
        "first_actions_per_syndrome": sorted({len(value) for value in actions_by_flux.values()}),
        "unique_physical_first_action_pairs": unique_pairs,
        "terminal_unique_pairs": terminal_pairs,
        "nonterminal_unique_pairs": nonterminal_pairs,
        "o0_second_record_transition_contributions": o0_second,
        "o2_candidate_first_action_pairs": o2_candidate_pairs,
        "o2_terminal_transition_contributions": o2_terminal,
        "o2_second_record_transition_contributions": o2_second,
        "total_streamed_second_record_transition_contributions": total_second,
        "maximum_second_records_per_nonterminal_pair": maximum_records,
        "maximum_active_vertices": maximum_active,
        "maximum_parity_components": maximum_components,
    }
    channel_count_mismatches = {
        key: {"expected": expected, "observed": channel[key]}
        for key, expected in EXPECTED_CHANNEL_COUNTS.items()
        if channel[key] != expected
    }

    elapsed = time.perf_counter() - start
    budget = manifest["compute_budget"]
    legacy_projection = float(
        manifest["resource_projection_amendment"][
            "source_frozen_original_four_prior_projection_seconds"
        ]
    )
    conservative_projection = scan_seconds + legacy_projection
    projected_memory = maximum_records * 2048 / (1024**3)
    validation = {
        "source_freeze_pass": True,
        "channel_count_reproduction_pass": not channel_count_mismatches,
        "maximum_second_channel_normalization_error": maximum_normalization_error,
        "observable_key_failures": observable_key_failures,
        "branch_provenance_failures": provenance_failures,
        "endpoint_projection_failures": projection_failures,
        "relation_cycle_kernel_invariance_pass": kernel_nontrivial == 0,
        "nontrivial_relation_cycle_kernel_count": kernel_nontrivial,
        "representative_boundary_failures": representative_boundary_failures,
        "representative_affine_membership_failures": representative_affine_membership_failures,
        "four_sector_quotient_pass": quotient_failures == 0,
        "expanded_public_boundary_failures": public_boundary_failures,
        "expanded_public_affine_membership_failures": public_membership_failures,
        "expanded_public_sector_failures": public_sector_failures,
        "expanded_public_objective_failures": public_objective_failures,
        "maximum_expanded_public_objective_error": maximum_public_objective_error,
        "kernel_check_guard_pass": kernel_candidate_checks <= int(budget["maximum_representative_kernel_checks"]),
        "transition_guard_pass": total_second <= int(budget["maximum_streamed_transition_contributions"]),
        "preflight_wall_guard_pass": elapsed <= 60.0 * float(budget["maximum_preflight_wall_time_minutes"]),
        "projected_total_wall_guard_pass": conservative_projection <= 60.0 * float(budget["maximum_total_wall_time_minutes"]),
        "projected_memory_guard_pass": projected_memory <= float(budget["maximum_resident_memory_gib"]),
        "policy_risk_intentionally_not_computed": True,
        "decoder_key_fields": ["initial_observation", "first_action_mask", "binary_Y"],
        "forbidden_decoder_key_fields": ["physical_error", "active_vertices", "relation_components", "effective_error"],
    }
    passed = all(
        (
            validation["channel_count_reproduction_pass"],
            maximum_normalization_error <= 1e-12,
            observable_key_failures == 0,
            provenance_failures == 0,
            projection_failures == 0,
            validation["relation_cycle_kernel_invariance_pass"],
            representative_boundary_failures == 0,
            representative_affine_membership_failures == 0,
            validation["four_sector_quotient_pass"],
            public_boundary_failures == 0,
            public_membership_failures == 0,
            public_sector_failures == 0,
            public_objective_failures == 0,
            validation["kernel_check_guard_pass"],
            validation["transition_guard_pass"],
            validation["preflight_wall_guard_pass"],
            validation["projected_total_wall_guard_pass"],
            validation["projected_memory_guard_pass"],
        )
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "corrected_sequential_preflight_passed" if passed else "corrected_sequential_preflight_failed",
        "lattice": {"size": lattice.size, "vertex_count": lattice.vertex_count, "edge_count": lattice.edge_count},
        "channel": channel,
        "channel_count_mismatches": channel_count_mismatches,
        "branch_representation": {
            "relation_occurrences": relation_occurrences,
            "unique_relation_signatures": len(kernel_cache),
            "kernel_candidate_chains_checked": kernel_candidate_checks,
            "kernel_closed_chains_checked": kernel_chain_checks,
            "representative_boundary_checks": representative_checks,
            "failure_witnesses": failure_witnesses,
        },
        "charge_action_quotient": quotient_summary,
        "resource_projection": {
            "corrected_channel_scan_seconds": scan_seconds,
            "o2_count_lookup_seconds": o2_seconds,
            "public_and_quotient_seconds": public_seconds,
            "total_preflight_seconds": elapsed,
            "conservative_four_prior_projection_seconds": conservative_projection,
            "projection_basis": "one corrected hidden-transition precompute plus the source-frozen original R4.5 conservative four-prior streaming projection",
            "source_frozen_original_four_prior_projection_seconds": legacy_projection,
            "overcounted_first_projection_seconds": 2176.794375950808,
            "projected_streaming_memory_gib": projected_memory,
        },
        "validation": validation,
        "new_stochastic_samples": 0,
        "claim_boundary": "Corrected primitive structural and resource preflight only. No posterior policy risk, algorithmic gap, LER, threshold, noisy-measurement, or scalable result is computed.",
        "source_hashes": {
            "scripts/d4_sequential_corrected.py": _sha256(LAB_DIR / "scripts/d4_sequential_corrected.py"),
            "scripts/run_r4_corrected_sequential_preflight.py": _sha256(Path(__file__)),
        },
    }
    payload["structural_digest_sha256"] = hashlib.sha256(
        json.dumps(
            {
                "channel": channel,
                "branch_representation": payload["branch_representation"],
                "charge_action_quotient": quotient_summary,
                "validation": validation,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return payload


def render_report(payload: dict) -> str:
    channel = payload["channel"]
    branch = payload["branch_representation"]
    validation = payload["validation"]
    resource = payload["resource_projection"]
    lines = [
        "# R4.5c corrected sequential-policy preflight",
        "",
        f"Status: **{payload['status']}**.",
        "",
        "## Reproduced channel",
        "",
        f"All {channel['unique_physical_first_action_pairs']:,} hidden `(E,A)` pairs were classified: {channel['terminal_unique_pairs']:,} terminal and {channel['nonterminal_unique_pairs']:,} nonterminal. The exact streamed second-record count is {channel['total_streamed_second_record_transition_contributions']:,}; count mismatches: `{payload['channel_count_mismatches']}`.",
        "",
        "## Branch-resolved invariance",
        "",
        f"The scan retained {branch['relation_occurrences']:,} actual-path relation occurrences and audited {branch['unique_relation_signatures']} distinct colour/signature subgraphs. It checked {branch['kernel_candidate_chains_checked']:,} candidate relation chains, including {branch['kernel_closed_chains_checked']:,} closed kernel chains. Nontrivial kernel sectors: `{validation['nontrivial_relation_cycle_kernel_count']}`.",
        "",
        f"All {branch['representative_boundary_checks']:,} colour-resolved supported-record representatives were checked. Boundary failures: `{validation['representative_boundary_failures']}`; exhaustive affine-membership failures: `{validation['representative_affine_membership_failures']}`.",
        "",
        "## Exact quotient and public continuation",
        "",
    ]
    for color in ("blue", "green"):
        result = payload["charge_action_quotient"][color]
        lines.append(
            f"- {color}: {result['even_syndrome_count']} even syndromes, {result['affine_actions_per_syndrome']} actions each, four sectors of {result['sector_sizes']}; quotient failures `{result['quotient_failures']}`."
        )
    lines.extend(
        [
            "",
            f"Expanded public correction boundary/membership/sector/objective failures: `{validation['expanded_public_boundary_failures']}` / `{validation['expanded_public_affine_membership_failures']}` / `{validation['expanded_public_sector_failures']}` / `{validation['expanded_public_objective_failures']}`.",
            "",
            "## Resource and stop rule",
            "",
            f"Preflight runtime was `{resource['total_preflight_seconds']:.3f} s`; the conservative four-prior projection is `{resource['conservative_four_prior_projection_seconds']:.1f} s`; projected streaming memory is `{resource['projected_streaming_memory_gib']:.6f} GiB`.",
            "",
            f"Kernel, transition, preflight-wall, total-wall, and memory guards: `{validation['kernel_check_guard_pass']}`, `{validation['transition_guard_pass']}`, `{validation['preflight_wall_guard_pass']}`, `{validation['projected_total_wall_guard_pass']}`, `{validation['projected_memory_guard_pass']}`.",
            "",
            "Policy risk was intentionally not computed in this prerequisite tick. A failed gate censors the downstream computation; a passing gate only authorizes the separately registered risk run.",
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
    payload = run_preflight(json.loads(args.manifest.read_text()))
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps(payload, indent=2))
    if payload["status"] != "corrected_sequential_preflight_passed":
        raise SystemExit("R4.5c corrected preflight failed")


if __name__ == "__main__":
    main()
