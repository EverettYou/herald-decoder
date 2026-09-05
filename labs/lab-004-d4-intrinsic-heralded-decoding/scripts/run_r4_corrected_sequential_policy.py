#!/usr/bin/env python3
"""Run the registered R4.5c exact primitive sequential-policy audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from d4_charge_multigraph import (
    branch_chain_sector,
    decode_expanded_branch_syndrome,
    infer_branch_postflux_relations,
)
from d4_exact import enumerate_affine_chains
from d4_honeycomb import BLUE, GREEN
from d4_matching import (
    d4_check_matrix,
    decode_flux_syndrome,
    published_herald_weights,
    syndrome_only_weights,
)
from d4_sequential import chain_mask, exact_second_record_channel, sequential_observation_key
from d4_sequential_corrected import (
    build_branch_representative_context,
    effective_branch_chain_from_record,
)
from run_r4_distinct_observation_matrix import (
    CandidateSupport,
    _chain,
    _sha256,
    build_primitive_observation_catalog,
)


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "r4-corrected-sequential-policy-manifest-2026-08-29.json"
DEFAULT_JSON = LAB_DIR / "results/r4-corrected-sequential-policy-audit.json"
DEFAULT_REPORT = LAB_DIR / "wiki/records/r4-corrected-sequential-policy-audit.md"
PREFLIGHT = LAB_DIR / "results/r4-corrected-sequential-policy-preflight.json"
ORIGINAL_MANIFEST = LAB_DIR / "r4-sequential-postflux-policy-manifest-2026-08-29.json"


@dataclass(frozen=True)
class HiddenActionTransition:
    terminal: bool
    probability_per_record: float
    outcomes: tuple[tuple[int, int], ...]


def _prior(mask: int, edge_count: int, p: float) -> float:
    weight = mask.bit_count()
    return p**weight * (1.0 - p) ** (edge_count - weight)


def _record_mask(record: tuple[int, ...]) -> int:
    return sum(int(bit) << vertex for vertex, bit in enumerate(record))


def _sector_index(sector: tuple[int, int]) -> int:
    return 2 * int(sector[0]) + int(sector[1])


def _joint_sector_index(
    blue: tuple[int, int], green: tuple[int, int]
) -> int:
    return 4 * _sector_index(blue) + _sector_index(green)


def _select_min_mask(
    risks: np.ndarray,
    action_masks: tuple[int, ...],
    tolerance: float,
) -> int:
    minimum = float(np.min(risks))
    eligible = [
        index
        for index, value in enumerate(risks)
        if abs(float(value) - minimum) <= tolerance
    ]
    return min(eligible, key=lambda index: action_masks[index])


def evaluate_weighted_observation(
    weighted_masks: tuple[tuple[int, float], ...],
    action_masks: tuple[int, ...],
    transitions: dict[tuple[int, int], HiddenActionTransition],
    public_action_index: int,
    public_second_predictions: dict[int, int],
    tolerance: float,
) -> dict:
    """Evaluate all four registered policies for one initial observation."""

    evidence = sum(weight for _, weight in weighted_masks)
    if evidence <= 0.0:
        raise ValueError("initial observation has zero evidence")
    immediate_numerators = np.zeros(len(action_masks), dtype=np.float64)
    exact_numerators = np.zeros(len(action_masks), dtype=np.float64)
    public_numerators = np.zeros(len(action_masks), dtype=np.float64)
    maximum_mass_error = 0.0
    history_count = 0
    for action_index, action_mask in enumerate(action_masks):
        by_record: dict[int, np.ndarray] = {}
        immediate = 0.0
        continued = 0.0
        for physical_mask, hidden_weight in weighted_masks:
            transition = transitions[(physical_mask, action_mask)]
            if transition.terminal:
                immediate += hidden_weight
                continue
            for record_mask, truth_sector in transition.outcomes:
                contribution = hidden_weight * transition.probability_per_record
                by_record.setdefault(record_mask, np.zeros(16, dtype=np.float64))[
                    truth_sector
                ] += contribution
                continued += contribution
        maximum_mass_error = max(
            maximum_mass_error, abs(immediate + continued - evidence)
        )
        exact_continuation_loss = 0.0
        public_continuation_loss = 0.0
        for record_mask, sector_evidence in by_record.items():
            total = float(np.sum(sector_evidence))
            exact_continuation_loss += total - float(np.max(sector_evidence))
            public_continuation_loss += (
                total - float(sector_evidence[public_second_predictions[record_mask]])
            )
        history_count += len(by_record)
        immediate_numerators[action_index] = immediate
        exact_numerators[action_index] = immediate + exact_continuation_loss
        public_numerators[action_index] = immediate + public_continuation_loss

    immediate_risks = immediate_numerators / evidence
    exact_risks = exact_numerators / evidence
    public_risks = public_numerators / evidence
    myopic_index = _select_min_mask(immediate_risks, action_masks, tolerance)
    future_index = _select_min_mask(exact_risks, action_masks, tolerance)
    public_index = int(public_action_index)
    return {
        "evidence": evidence,
        "risk_numerators": {
            "public_fixed": float(public_numerators[public_index]),
            "fixed_first_exact_continuation": float(exact_numerators[public_index]),
            "myopic_first_exact_continuation": float(exact_numerators[myopic_index]),
            "future_aware_exact": float(exact_numerators[future_index]),
        },
        "actions": {
            "public": action_masks[public_index],
            "myopic": action_masks[myopic_index],
            "future_aware": action_masks[future_index],
        },
        "maximum_action_mass_conservation_error": maximum_mass_error,
        "observable_history_action_count": history_count,
    }


def _validate_source_freeze(manifest: dict) -> None:
    for freeze_name in ("source_freeze", "final_computation_source_freeze"):
        for relative, expected in manifest.get(freeze_name, {}).items():
            if _sha256(LAB_DIR / relative) != expected:
                raise ValueError(f"R4.5c source hash drift: {relative}")


def _build_charge_references(lattice, contexts) -> dict:
    references = {}
    for color in (BLUE, GREEN):
        charge_lattice = contexts[color].charge_lattice
        check = np.zeros(
            (charge_lattice.vertex_count, charge_lattice.edge_count), dtype=np.uint8
        )
        for edge, (left, right) in enumerate(charge_lattice.edge_vertices):
            check[int(left), edge] = 1
            check[int(right), edge] = 1
        color_rows = {}
        for syndrome_mask in range(1 << charge_lattice.vertex_count):
            syndrome = np.asarray(
                [
                    (syndrome_mask >> vertex) & 1
                    for vertex in range(charge_lattice.vertex_count)
                ],
                dtype=np.uint8,
            )
            if int(np.sum(syndrome)) % 2:
                continue
            actions = enumerate_affine_chains(check, syndrome)
            reference = min(actions, key=chain_mask)
            correction, _ = decode_expanded_branch_syndrome(
                lattice,
                color,
                syndrome,
                np.ones(charge_lattice.edge_count, dtype=np.float64),
            )
            public_sector = branch_chain_sector(
                lattice, color, correction ^ reference
            )
            color_rows[syndrome_mask] = {
                "reference": reference,
                "public_sector": public_sector,
            }
        references[color] = color_rows
    return references


def _build_public_second_predictions(lattice, references) -> dict[int, int]:
    predictions = {}
    for record_mask in range(1 << lattice.vertex_count):
        record = tuple(
            (record_mask >> vertex) & 1 for vertex in range(lattice.vertex_count)
        )
        syndromes = {}
        valid = True
        for color in (BLUE, GREEN):
            bits = tuple(record[vertex] for vertex in range(color, lattice.vertex_count, 2))
            if sum(bits) % 2:
                valid = False
                break
            syndrome_mask = sum(bit << index for index, bit in enumerate(bits))
            syndromes[color] = syndrome_mask
        if not valid:
            continue
        predictions[record_mask] = _joint_sector_index(
            references[BLUE][syndromes[BLUE]]["public_sector"],
            references[GREEN][syndromes[GREEN]]["public_sector"],
        )
    return predictions


def _build_transition_cache(catalog, actions_by_flux, contexts, references) -> tuple[dict, dict]:
    lattice = catalog.lattice
    supports_by_flux = defaultdict(dict)
    for (flux, _), candidates in catalog.observations.items():
        for candidate in candidates:
            supports_by_flux[flux].setdefault(candidate.mask, candidate)
    transitions = {}
    terminal = nonterminal = outcomes = observable_key_failures = 0
    maximum_channel_normalization_error = 0.0
    for flux in sorted(supports_by_flux):
        for physical_mask in sorted(supports_by_flux[flux]):
            physical = _chain(lattice.edge_count, physical_mask)
            for action_mask, action in actions_by_flux[flux]:
                channel = exact_second_record_channel(lattice, physical, action)
                if channel.terminal_failure:
                    transitions[(physical_mask, action_mask)] = HiddenActionTransition(
                        True, 0.0, ()
                    )
                    terminal += 1
                    continue
                nonterminal += 1
                enriched = infer_branch_postflux_relations(lattice, physical, action)
                rows = []
                for record in channel.binary_records:
                    if sequential_observation_key((flux,), action_mask, record) != (
                        (flux,), action_mask, record
                    ):
                        observable_key_failures += 1
                    truth = {}
                    for color in (BLUE, GREEN):
                        context = contexts[color]
                        effective = effective_branch_chain_from_record(
                            lattice, color, enriched, record, context
                        )
                        bits = tuple(
                            record[vertex]
                            for vertex in range(color, lattice.vertex_count, 2)
                        )
                        syndrome_mask = sum(
                            bit << index for index, bit in enumerate(bits)
                        )
                        reference = references[color][syndrome_mask]["reference"]
                        truth[color] = branch_chain_sector(
                            lattice, color, effective ^ reference
                        )
                    rows.append(
                        (
                            _record_mask(record),
                            _joint_sector_index(truth[BLUE], truth[GREEN]),
                        )
                    )
                maximum_channel_normalization_error = max(
                    maximum_channel_normalization_error,
                    abs(channel.probability_per_record * len(rows) - 1.0),
                )
                outcomes += len(rows)
                transitions[(physical_mask, action_mask)] = HiddenActionTransition(
                    False, channel.probability_per_record, tuple(rows)
                )
    return transitions, {
        "transition_pair_count": len(transitions),
        "terminal_transition_pairs": terminal,
        "nonterminal_transition_pairs": nonterminal,
        "unique_hidden_second_outcomes": outcomes,
        "maximum_channel_normalization_error": maximum_channel_normalization_error,
        "observable_key_failures": observable_key_failures,
    }


def run_policy_audit(manifest: dict) -> dict:
    _validate_source_freeze(manifest)
    preflight = json.loads(PREFLIGHT.read_text())
    if preflight["status"] != "corrected_sequential_preflight_passed":
        raise RuntimeError("R4.5c final audit requires a passing corrected preflight")
    original = json.loads(ORIGINAL_MANIFEST.read_text())
    r44 = json.loads(
        (LAB_DIR / "results/r4-first-stage-loss-bridge-audit.json").read_text()
    )
    priors = tuple(float(row["p"]) for row in r44["prior_summaries"])
    tolerance = float(original["validation"]["absolute_tolerance"])
    catalog = build_primitive_observation_catalog()
    lattice = catalog.lattice
    check = d4_check_matrix(lattice)
    contexts = {
        color: build_branch_representative_context(lattice, color)
        for color in (BLUE, GREEN)
    }
    references = _build_charge_references(lattice, contexts)
    public_second = _build_public_second_predictions(lattice, references)

    flux_groups = defaultdict(list)
    supports_by_flux = defaultdict(dict)
    for (flux, charge), candidates in catalog.observations.items():
        flux_groups[flux].append((charge, candidates))
        for candidate in candidates:
            supports_by_flux[flux].setdefault(candidate.mask, candidate)
    actions_by_flux = {}
    action_index_by_flux = {}
    for flux in sorted(supports_by_flux):
        actions = enumerate_affine_chains(check, np.asarray(flux, dtype=np.uint8))
        rows = tuple(sorted(((chain_mask(action), action) for action in actions)))
        actions_by_flux[flux] = rows
        action_index_by_flux[flux] = {mask: index for index, (mask, _) in enumerate(rows)}

    unit_public = {}
    for flux in sorted(supports_by_flux):
        decoded = decode_flux_syndrome(
            lattice,
            np.asarray(flux, dtype=np.uint8),
            syndrome_only_weights(lattice),
        )
        unit_public[flux] = action_index_by_flux[flux][chain_mask(decoded.correction)]
    herald_public = {}
    for flux, charge in sorted(catalog.observations):
        decoded = decode_flux_syndrome(
            lattice,
            np.asarray(flux, dtype=np.uint8),
            published_herald_weights(lattice, np.asarray(charge, dtype=np.int64)),
        )
        herald_public[(flux, charge)] = action_index_by_flux[flux][
            chain_mask(decoded.correction)
        ]

    start = time.perf_counter()
    transitions, transition_summary = _build_transition_cache(
        catalog, actions_by_flux, contexts, references
    )
    cache_seconds = time.perf_counter() - start

    prior_summaries = []
    maximum_action_mass_error = 0.0
    maximum_global_normalization_error = 0.0
    maximum_o0_o2_flux_evidence_error = 0.0
    maximum_risk_order_violation = 0.0
    maximum_information_order_violation = 0.0
    total_history_action_count = 0
    for p in priors:
        layer_acc = {}
        o2_evidence_by_flux = defaultdict(float)
        for layer in ("o0", "o2"):
            acc = defaultdict(float)
            rows = []
            if layer == "o0":
                rows = [
                    (
                        flux,
                        flux,
                        tuple(
                            (mask, _prior(mask, lattice.edge_count, p))
                            for mask in sorted(supports_by_flux[flux])
                        ),
                        unit_public[flux],
                    )
                    for flux in sorted(supports_by_flux)
                ]
            else:
                for flux, charge in sorted(catalog.observations):
                    weighted = tuple(
                        (
                            candidate.mask,
                            _prior(candidate.mask, lattice.edge_count, p)
                            * 2.0**candidate.log2_conditional_probability,
                        )
                        for candidate in catalog.observations[(flux, charge)]
                    )
                    rows.append(
                        ((flux, charge), flux, weighted, herald_public[(flux, charge)])
                    )
            for observation_key, flux, weighted, public_index in rows:
                action_masks = tuple(mask for mask, _ in actions_by_flux[flux])
                result = evaluate_weighted_observation(
                    weighted,
                    action_masks,
                    transitions,
                    public_index,
                    public_second,
                    tolerance,
                )
                evidence = result["evidence"]
                acc["mass"] += evidence
                if layer == "o2":
                    o2_evidence_by_flux[flux] += evidence
                for policy, numerator in result["risk_numerators"].items():
                    acc[policy] += numerator
                actions = result["actions"]
                acc["future_vs_public_difference_mass"] += evidence * (
                    actions["future_aware"] != actions["public"]
                )
                acc["future_vs_myopic_difference_mass"] += evidence * (
                    actions["future_aware"] != actions["myopic"]
                )
                acc["myopic_vs_public_difference_mass"] += evidence * (
                    actions["myopic"] != actions["public"]
                )
                maximum_action_mass_error = max(
                    maximum_action_mass_error,
                    result["maximum_action_mass_conservation_error"],
                )
                total_history_action_count += result["observable_history_action_count"]
            mass = acc["mass"]
            layer_acc[layer] = {
                "nonwinding_observation_mass": mass,
                "nonwinding_conditioned_risks": {
                    policy: acc[policy] / mass
                    for policy in (
                        "public_fixed",
                        "fixed_first_exact_continuation",
                        "myopic_first_exact_continuation",
                        "future_aware_exact",
                    )
                },
                "first_action_difference_probability": {
                    "future_vs_public": acc["future_vs_public_difference_mass"] / mass,
                    "future_vs_myopic": acc["future_vs_myopic_difference_mass"] / mass,
                    "myopic_vs_public": acc["myopic_vs_public_difference_mass"] / mass,
                },
                "observation_count": len(rows),
            }

        for flux in sorted(supports_by_flux):
            direct = sum(
                _prior(mask, lattice.edge_count, p)
                for mask in supports_by_flux[flux]
            )
            maximum_o0_o2_flux_evidence_error = max(
                maximum_o0_o2_flux_evidence_error,
                abs(direct - o2_evidence_by_flux[flux]),
            )
        terminal_mass = sum(
            _prior(mask, lattice.edge_count, p)
            for mask in catalog.terminal_winding_masks
        )
        for layer in ("o0", "o2"):
            maximum_global_normalization_error = max(
                maximum_global_normalization_error,
                abs(terminal_mass + layer_acc[layer]["nonwinding_observation_mass"] - 1.0),
            )
            mass = layer_acc[layer]["nonwinding_observation_mass"]
            layer_acc[layer]["terminal_physical_winding_mass"] = terminal_mass
            layer_acc[layer]["full_risks_with_terminal_mass"] = {
                policy: terminal_mass + mass * risk
                for policy, risk in layer_acc[layer]["nonwinding_conditioned_risks"].items()
            }
            risks = layer_acc[layer]["nonwinding_conditioned_risks"]
            future = risks["future_aware_exact"]
            maximum_risk_order_violation = max(
                maximum_risk_order_violation,
                future - risks["public_fixed"],
                future - risks["fixed_first_exact_continuation"],
                future - risks["myopic_first_exact_continuation"],
                risks["fixed_first_exact_continuation"] - risks["public_fixed"],
            )
        o0_future = layer_acc["o0"]["nonwinding_conditioned_risks"]["future_aware_exact"]
        o2_future = layer_acc["o2"]["nonwinding_conditioned_risks"]["future_aware_exact"]
        maximum_information_order_violation = max(
            maximum_information_order_violation, o2_future - o0_future
        )
        prior_summaries.append(
            {
                "p": p,
                "o0_flux_only": layer_acc["o0"],
                "o2_flux_and_charge": layer_acc["o2"],
                "decomposition": {
                    "future_aware_exact_information_gain_o0_minus_o2": o0_future - o2_future,
                    "o0": _decomposition(layer_acc["o0"]["nonwinding_conditioned_risks"]),
                    "o2": _decomposition(layer_acc["o2"]["nonwinding_conditioned_risks"]),
                },
            }
        )

    total_seconds = time.perf_counter() - start
    validation = {
        "maximum_second_channel_normalization_error": transition_summary["maximum_channel_normalization_error"],
        "observable_key_failures": transition_summary["observable_key_failures"],
        "maximum_action_branch_mass_conservation_error": maximum_action_mass_error,
        "maximum_o0_vs_marginalized_o2_flux_evidence_error": maximum_o0_o2_flux_evidence_error,
        "maximum_global_normalization_error": maximum_global_normalization_error,
        "maximum_registered_policy_risk_order_violation": maximum_risk_order_violation,
        "maximum_o2_vs_o0_exact_information_order_violation": maximum_information_order_violation,
        "public_first_action_membership_failures": 0,
        "public_second_prediction_count": len(public_second),
        "production_decoder_truth_inputs": [],
        "new_stochastic_samples": 0,
        "larger_lattice_sizes": 0,
    }
    passed = max(
        transition_summary["maximum_channel_normalization_error"],
        maximum_action_mass_error,
        maximum_o0_o2_flux_evidence_error,
        maximum_global_normalization_error,
        maximum_risk_order_violation,
        maximum_information_order_violation,
    ) <= tolerance and transition_summary["observable_key_failures"] == 0
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "corrected_sequential_policy_audited" if passed else "corrected_sequential_policy_failed",
        "lattice": {"size": lattice.size, "vertex_count": lattice.vertex_count, "edge_count": lattice.edge_count},
        "matrix": {
            "o0_observation_count": len(supports_by_flux),
            "o2_observation_count": len(catalog.observations),
            "first_actions_per_syndrome": 32,
            "joint_second_sector_actions": 16,
            "priors": list(priors),
            "observable_history_action_aggregations": total_history_action_count,
            **transition_summary,
        },
        "prior_summaries": prior_summaries,
        "validation": validation,
        "resource": {
            "transition_cache_seconds": cache_seconds,
            "total_wall_time_seconds": total_seconds,
            "wall_guard_seconds": 60.0 * float(manifest["compute_budget"]["maximum_total_wall_time_minutes"]),
            "streamed_transition_guard": int(manifest["compute_budget"]["maximum_streamed_transition_contributions"]),
        },
        "claim_boundary": "Exact primitive L=2 noiseless sequential-policy audit under the registered observation model. It is not an LER, threshold, larger-lattice, noisy-measurement, fault-tolerance, or scalable-optimality result.",
        "source_hashes": {
            "scripts/run_r4_corrected_sequential_policy.py": _sha256(Path(__file__)),
            "scripts/d4_sequential_corrected.py": _sha256(LAB_DIR / "scripts/d4_sequential_corrected.py"),
            "results/r4-corrected-sequential-policy-preflight.json": _sha256(PREFLIGHT),
        },
    }
    payload["prior_summary_digest_sha256"] = hashlib.sha256(
        json.dumps(prior_summaries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def _decomposition(risks: dict[str, float]) -> dict:
    return {
        "public_full_policy_excess": risks["public_fixed"] - risks["future_aware_exact"],
        "second_stage_mwpm_excess_at_public_first": risks["public_fixed"] - risks["fixed_first_exact_continuation"],
        "public_first_action_excess_after_exact_continuation": risks["fixed_first_exact_continuation"] - risks["future_aware_exact"],
        "myopia_cost": risks["myopic_first_exact_continuation"] - risks["future_aware_exact"],
    }


def render_report(payload: dict) -> str:
    lines = [
        "# R4.5c corrected sequential-policy audit",
        "",
        f"Status: **{payload['status']}**.",
        "",
        "## Exact primitive policy risks",
        "",
        "Risks below are conditioned on the source-frozen nonwinding initial channel. Terminal physical-winding mass and full risks are retained in the machine-readable result.",
        "",
        "| p | layer | public fixed | public first + exact | myopic first + exact | future-aware exact | public excess | myopia cost |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["prior_summaries"]:
        for label, key in (("O0", "o0_flux_only"), ("O2", "o2_flux_and_charge")):
            risks = row[key]["nonwinding_conditioned_risks"]
            decomposition = row["decomposition"][label.lower()]
            lines.append(
                f"| {row['p']:.2f} | {label} | {risks['public_fixed']:.6f} | {risks['fixed_first_exact_continuation']:.6f} | {risks['myopic_first_exact_continuation']:.6f} | {risks['future_aware_exact']:.6f} | {decomposition['public_full_policy_excess']:.6f} | {decomposition['myopia_cost']:.6f} |"
            )
    lines.extend(["", "## Decomposition and first-action changes", ""])
    for row in payload["prior_summaries"]:
        lines.append(
            f"- p={row['p']:.2f}: exact O0-minus-O2 information gain `{row['decomposition']['future_aware_exact_information_gain_o0_minus_o2']:.6f}`; future/public first-action disagreement O0/O2 `{row['o0_flux_only']['first_action_difference_probability']['future_vs_public']:.6f}` / `{row['o2_flux_and_charge']['first_action_difference_probability']['future_vs_public']:.6f}`; future/myopic disagreement `{row['o0_flux_only']['first_action_difference_probability']['future_vs_myopic']:.6f}` / `{row['o2_flux_and_charge']['first_action_difference_probability']['future_vs_myopic']:.6f}`."
        )
    validation = payload["validation"]
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"Maximum channel, action-branch, O0/O2 marginalization, and global-normalization errors are `{validation['maximum_second_channel_normalization_error']:.3e}`, `{validation['maximum_action_branch_mass_conservation_error']:.3e}`, `{validation['maximum_o0_vs_marginalized_o2_flux_evidence_error']:.3e}`, and `{validation['maximum_global_normalization_error']:.3e}`.",
            "",
            f"Maximum registered within-layer risk-order violation is `{validation['maximum_registered_policy_risk_order_violation']:.3e}`; maximum O2-versus-O0 exact-information ordering violation is `{validation['maximum_o2_vs_o0_exact_information_order_violation']:.3e}`. Decoder truth inputs: `{validation['production_decoder_truth_inputs']}`.",
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
    payload = run_policy_audit(json.loads(args.manifest.read_text()))
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    args.report.write_text(render_report(payload))
    print(json.dumps(payload, indent=2))
    if payload["status"] != "corrected_sequential_policy_audited":
        raise SystemExit("R4.5c corrected sequential policy audit failed")


if __name__ == "__main__":
    main()
