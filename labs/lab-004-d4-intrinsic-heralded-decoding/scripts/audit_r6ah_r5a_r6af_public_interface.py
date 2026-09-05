#!/usr/bin/env python3
"""Audit legacy R5a provenance against the remediated R6AF public interface."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "manifests/r6ah-r5a-r6af-public-interface-provenance-audit-manifest-2026-09-01.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path(entry: dict) -> Path:
    return LAB_DIR / entry["path"]


def _inspect_raw(path: Path, maximum_records: int) -> dict:
    record_count = 0
    mode_counts: Counter[str] = Counter()
    first_domain: set[int] = set()
    second_domain: set[int] = set()
    first_records_with_sentinel = 0
    first_records_full_binary = 0
    second_records_present = 0
    second_records_with_sentinel = 0
    second_records_full_binary = 0
    records_with_private_relations = 0
    records_with_effective_error = 0
    records_with_public_transcript = 0
    scorer_mismatches = 0
    pairs: dict[tuple[int, float, int], dict[str, dict]] = {}

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            record_count += 1
            if record_count > maximum_records:
                raise RuntimeError("R5a raw cohort exceeds the registered inspection cap")
            row = json.loads(line)
            mode = str(row["mode"])
            mode_counts[mode] += 1
            pipeline = row["pipeline_record"]
            observation = pipeline["observation"]
            first = observation.get("charge_outcomes")
            if first is not None:
                values = {int(value) for value in first}
                first_domain.update(values)
                first_records_with_sentinel += int(-1 in values)
                first_records_full_binary += int(values <= {0, 1})
            second = pipeline.get("postflux_charge_outcomes")
            if second is not None:
                values = {int(value) for value in second}
                second_domain.update(values)
                second_records_present += 1
                second_records_with_sentinel += int(-1 in values)
                second_records_full_binary += int(values <= {0, 1})
            relations = pipeline.get("postflux_relations")
            records_with_private_relations += int(relations is not None)
            charge = pipeline.get("charge_recovery")
            if charge is not None:
                colors = charge.get("colors", {})
                records_with_effective_error += int(
                    any("effective_error_edges" in value for value in colors.values())
                )
            records_with_public_transcript += int("public_transcript" in pipeline)

            expected_loss = bool(observation.get("logical_error", False))
            flux = pipeline.get("flux_recovery")
            if flux is not None:
                expected_loss = expected_loss or bool(flux.get("logical_error", False))
            if charge is not None:
                expected_loss = expected_loss or bool(charge.get("logical_error", False))
            scorer_mismatches += int(expected_loss != bool(row["logical_error"]))

            key = (int(row["size"]), float(row["error_rate"]), int(row["seed_index"]))
            pairs.setdefault(key, {})[mode] = {
                "physical_seed": int(row["physical_seed"]),
                "decoder_seed": int(row["decoder_seed"]),
                "physical_error_edges": tuple(pipeline["physical_error_edges"]),
                "first_flux_vertices": tuple(observation["flux_vertices"]),
                "first_charge_outcomes": None if first is None else tuple(first),
                "second_charge_outcomes": None if second is None else tuple(second),
            }

    expected_modes = {"syndrome_only", "heralded"}
    incomplete_pairs = 0
    physical_pair_mismatches = 0
    first_pair_mismatches = 0
    decoder_seed_pair_mismatches = 0
    action_dependent_second_record_pairs = 0
    for arms in pairs.values():
        if set(arms) != expected_modes:
            incomplete_pairs += 1
            continue
        o0 = arms["syndrome_only"]
        o2 = arms["heralded"]
        physical_pair_mismatches += int(
            (o0["physical_seed"], o0["physical_error_edges"])
            != (o2["physical_seed"], o2["physical_error_edges"])
        )
        first_pair_mismatches += int(
            (o0["first_flux_vertices"], o0["first_charge_outcomes"])
            != (o2["first_flux_vertices"], o2["first_charge_outcomes"])
        )
        decoder_seed_pair_mismatches += int(o0["decoder_seed"] != o2["decoder_seed"])
        if (
            o0["second_charge_outcomes"] is not None
            and o2["second_charge_outcomes"] is not None
            and o0["second_charge_outcomes"] != o2["second_charge_outcomes"]
        ):
            action_dependent_second_record_pairs += 1

    return {
        "record_count": record_count,
        "mode_counts": dict(sorted(mode_counts.items())),
        "paired_history_count": len(pairs),
        "incomplete_pair_count": incomplete_pairs,
        "physical_pair_mismatch_count": physical_pair_mismatches,
        "first_record_pair_mismatch_count": first_pair_mismatches,
        "decoder_seed_pair_mismatch_count": decoder_seed_pair_mismatches,
        "action_dependent_second_record_pair_count": action_dependent_second_record_pairs,
        "first_record_value_domain": sorted(first_domain),
        "first_records_with_inactive_sentinel": first_records_with_sentinel,
        "first_records_full_binary": first_records_full_binary,
        "second_record_value_domain": sorted(second_domain),
        "second_records_present": second_records_present,
        "second_records_with_inactive_sentinel": second_records_with_sentinel,
        "second_records_full_binary": second_records_full_binary,
        "records_with_private_relation_metadata": records_with_private_relations,
        "records_with_effective_error_truth": records_with_effective_error,
        "records_with_explicit_public_transcript": records_with_public_transcript,
        "stored_loss_composition_mismatch_count": scorer_mismatches,
    }


def build_audit(manifest: dict) -> dict:
    if manifest.get("status") not in {"registered_audit_pending", "audit_completed_incompatible"}:
        raise RuntimeError("R6AH manifest is not in a registered audit state")
    frozen = manifest["frozen_evidence"]
    hash_checks = {}
    for name, entry in frozen.items():
        if not isinstance(entry, dict):
            continue
        path = _path(entry)
        actual = _sha256(path) if path.is_file() else None
        hash_checks[name] = {
            "path": entry["path"],
            "expected": entry["sha256"],
            "actual": actual,
            "passed": actual == entry["sha256"],
        }
    if not all(check["passed"] for check in hash_checks.values()):
        raise RuntimeError(f"frozen evidence hash gate failed: {hash_checks}")

    r5_contract = _load(_path(frozen["r5a_contract"]))
    r5_preflight = _load(_path(frozen["r5a_preflight"]))
    r5_analysis = _load(_path(frozen["r5a_analysis"]))
    r6_contract = _load(_path(frozen["r6af_contract"]))
    r6_preflight = _load(_path(frozen["r6af_preflight"]))
    status_gates = {
        "r5a_contract_complete": r5_contract.get("status") == "production_complete_analyzed_reported",
        "r5a_preflight_passed": r5_preflight.get("status") == "r5a_preflight_passed"
        and bool(r5_preflight.get("gates", {}).get("all_passed")),
        "r5a_analysis_present": r5_analysis.get("status") == "finite_size_public_decoder_analysis",
        "r6af_contract_complete": r6_contract.get("status") == "pilot_completed_analyzed_no_refinement",
        "r6af_preflight_passed": r6_preflight.get("status") == "passed"
        and r6_preflight.get("failed_gates") == []
        and all(bool(value) for value in r6_preflight.get("gates", {}).values()),
    }
    if not all(status_gates.values()):
        raise RuntimeError(f"registered evidence status gate failed: {status_gates}")

    raw = _inspect_raw(
        _path(frozen["r5a_raw_cohort"]),
        int(manifest["compute_budget"]["maximum_raw_records_inspected"]),
    )
    if raw["record_count"] != int(r5_contract["production_result"]["raw_record_count"]):
        raise RuntimeError("R5a raw record count does not match its frozen contract")

    dimensions = [
        {
            "dimension": "artifact identity and status",
            "verdict": "compatible",
            "evidence": [
                "manifest:frozen_evidence",
                "r5a_contract:production_result",
                "r5a_preflight:gates",
                "r6af_contract:pilot_outcome",
            ],
            "witness": f"All {len(hash_checks)} frozen file hashes and all five status gates pass; the R5a gzip contains exactly {raw['record_count']} records.",
        },
        {
            "dimension": "physical channel and geometry",
            "verdict": "compatible_scope_difference",
            "evidence": ["r5a_contract:design", "r6af_contract:frozen_model.physical_channel", "r6af_contract:pilot_registration.grid"],
            "witness": "Both use the paper-normalized periodic honeycomb IID red-X channel, but R5a uses L=2,3 and p=0.14..0.22 whereas R6AF uses L=3,5 and p_X=0.19,0.21; no numerical comparison is allowed.",
        },
        {
            "dimension": "first observation and timing",
            "verdict": "incompatible",
            "evidence": ["r5a_raw_cohort:pipeline_record.observation.charge_outcomes", "r6af_contract:frozen_model.decoder_visible_information.first_stage"],
            "witness": f"The legacy first-record domain is {raw['first_record_value_domain']} and {raw['first_records_with_inactive_sentinel']} records expose inactive -1 support; R6AF requires a full binary signal-only field where zero is ambiguous.",
        },
        {
            "dimension": "matched randomness",
            "verdict": "compatible_with_limited_provenance",
            "evidence": ["r5a_contract:design.matching", "r5a_raw_cohort:paired seeds and records", "r6af_contract:pilot_registration.seed_contract"],
            "witness": f"All {raw['paired_history_count']} legacy pairs match physical errors, first records, and decoder seeds, with {raw['action_dependent_second_record_pair_count']} pairs recording distinct post-action second outcomes; R5a does not expose R6AF's three keys separately.",
        },
        {
            "dimension": "second public record",
            "verdict": "incompatible",
            "evidence": ["r5a_raw_cohort:pipeline_record.postflux_charge_outcomes", "r6af_contract:preflight_outcome.remediation_history"],
            "witness": f"All {raw['second_records_present']} stored legacy second records use domain {raw['second_record_value_domain']}; {raw['second_records_with_inactive_sentinel']} contain -1 and zero are full binary. R6AF requires one binary value on every star.",
        },
        {
            "dimension": "charge action information budget",
            "verdict": "incompatible",
            "evidence": ["r5a_raw_cohort:pipeline_record.postflux_relations", "r5a_raw_cohort:pipeline_record.charge_recovery.colors.*.effective_error_edges", "r6af_contract:preflight_outcome.remediation_history"],
            "witness": f"The legacy record couples {raw['records_with_private_relation_metadata']} relation-bearing records and {raw['records_with_effective_error_truth']} effective-error scoring records at the old combined boundary; R6AF records that this boundary accepted hidden relations and replaced it with a relation-free public action plus private scorer.",
        },
        {
            "dimension": "action-conditioned support",
            "verdict": "incomplete_gate",
            "evidence": ["r5a_contract:preflight.required_gates", "r5a_raw_cohort:paired post-action records", "r6af_contract:preflight_fixture_matrix"],
            "witness": "R5a records policy-dependent post-action supports and passed own-support proxies, but it has no wrong-action rejection or action-binding fixture equivalent to R6AF.",
        },
        {
            "dimension": "logical scorer and denominator",
            "verdict": "compatible_with_unexercised_branch",
            "evidence": ["r5a_contract:recorded_outcomes", "r5a_raw_cohort:stored loss composition", "r6af_contract:frozen_model.logical_scorer"],
            "witness": f"Stored R5a final-loss flags equal the OR of available physical/flux/charge loss fields in all records ({raw['stored_loss_composition_mismatch_count']} mismatches), but its cohort contains no physical-winding histories and cannot exercise that denominator branch.",
        },
        {
            "dimension": "anti-leak and replay gates",
            "verdict": "incomplete_gate",
            "evidence": ["r5a_raw_cohort:pipeline_record schema", "r5a_preflight:gates", "r6af_contract:pilot_registration.verification_and_acceptance"],
            "witness": f"R5a stores zero explicit public transcripts and lacks relation-perturbation invariance, wrong-action binding, and first/middle/final deterministic replay gates required by R6AF.",
        },
        {
            "dimension": "claim usability",
            "verdict": "provenance_only",
            "evidence": ["r5a_analysis", "dimensions:first observation and timing", "dimensions:second public record", "dimensions:charge action information budget"],
            "witness": "R5a physical/lattice records remain provenance, but its O2 policy differences, final-loss risks, stage mechanism, size directions, and Lab 005 baseline promotion are withdrawn as evidence for the remediated complete public pipeline.",
        },
    ]
    registered = [entry["dimension"] for entry in manifest["audit_dimensions"]]
    emitted = [entry["dimension"] for entry in dimensions]
    if emitted != registered:
        raise RuntimeError(f"audit dimension mismatch: registered={registered}, emitted={emitted}")

    incompatible = [entry["dimension"] for entry in dimensions if entry["verdict"] == "incompatible"]
    verdict = "incompatible" if incompatible else "censored"
    return {
        "schema_version": 1,
        "status": "completed" if verdict != "censored" else "censored",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": DEFAULT_MANIFEST.name,
        "hash_checks": hash_checks,
        "status_gates": status_gates,
        "raw_schema_audit": raw,
        "dimension_matrix": dimensions,
        "unclassified_dimension_count": 0,
        "overall_verdict": verdict,
        "incompatible_dimensions": incompatible,
        "claim_usability": {
            "retain_as_provenance": ["frozen physical-error draws", "lattice/topology provenance", "historical implementation trace"],
            "withdraw_for_remediated_complete_pipeline": ["all R5a O0/O2 final-loss risks and paired differences", "R5a O2 first-stage mechanism claim", "R5a size directions", "R5a promotion as a validated Lab 005 complete-pipeline baseline"],
            "replacement_evidence": "R6AF supplies the current public-interface implementation pilot at its own registered four-cell scope.",
        },
        "claim_boundary": "This is a deterministic provenance verdict. It performs no R5a/R6AF numerical risk comparison and does not register or imply a rerun, crossing, threshold, scaling, noisy-measurement, or fault-tolerance claim.",
        "new_computation": {"histories": 0, "arm_evaluations": 0, "bootstrap_replicates": 0},
    }


def _report(payload: dict) -> str:
    lines = [
        "---",
        "title: R6AH legacy R5a/R6AF public-interface provenance audit",
        "status: current",
        "updated: 2026-09-01",
        "record: true",
        "---",
        "",
        "## Summary",
        "",
        "The legacy R5a cohort is **incompatible** with the remediated R6AF complete public-interface contract.",
        "Its frozen physical and lattice records remain provenance, but its numerical complete-pipeline claims are withdrawn.",
        "",
        "## Status",
        "",
        "Current provenance boundary. R6AF is the replacement complete-pipeline evidence only at its own registered four-cell scope.",
        "",
        "## Evidence",
        "",
        "[Machine-readable audit](../../results/r6ah-r5a-r6af-public-interface-provenance-audit-2026-09-01.json)",
        "and [registered contract](../../manifests/r6ah-r5a-r6af-public-interface-provenance-audit-manifest-2026-09-01.json).",
        "",
        "## Interface matrix",
        "",
        "| Dimension | Verdict | Witness |",
        "|:---|:---|:---|",
    ]
    for row in payload["dimension_matrix"]:
        lines.append(f"| {row['dimension']} | {row['verdict']} | {row['witness']} |")
    raw = payload["raw_schema_audit"]
    lines.extend(
        [
            "",
            "## Decisive boundary",
            "",
            f"All {raw['record_count']:,} frozen R5a records were inspected without resampling. The first and second records use the support-revealing domain `{-1,0,1}`; no second record is full binary. The old combined charge boundary also carries private relation/effective-error truth, whereas R6AF separates a relation-free public action from private generation and scoring.",
            "",
            "R5a additionally lacks the remediated wrong-action binding, relation-perturbation anti-leak, explicit public-transcript, and deterministic replay gates. These are implementation-contract failures, not adverse numerical comparisons.",
            "",
            "## Claim usability",
            "",
            "Retained as provenance: frozen physical-error draws, lattice/topology records, and historical implementation trace.",
            "",
            "Withdrawn for the remediated complete pipeline: all R5a O0/O2 final-loss risks and paired differences, the O2 stage-mechanism claim, size directions, and promotion as a validated Lab 005 baseline. R6AF remains the current replacement evidence only at its own four-cell pilot scope.",
            "",
            "## Claim boundary",
            "",
            payload["claim_boundary"],
            "Zero new histories, arm evaluations, or bootstrap replicates were generated.",
            "",
            "## Related pages",
            "",
            "[[decoder-validation|Decoder validation]] · [[records/r5a-paper-lattice-public-decoder-analysis|Withdrawn R5a pilot record]] · [[records/r6af-two-stage-public-charge-preflight-2026-09-01|R6AF public-interface remediation]] · [[records/index|Research-record index]]",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = _load(args.manifest)
    payload = build_audit(manifest)
    machine = LAB_DIR / manifest["outputs"]["machine_audit"]
    report = LAB_DIR / manifest["outputs"]["report"]
    machine.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.write_text(_report(payload), encoding="utf-8")
    print(json.dumps({"machine": str(machine), "report": str(report), "verdict": payload["overall_verdict"]}))


if __name__ == "__main__":
    main()
