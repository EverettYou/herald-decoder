#!/usr/bin/env python3
"""Compact trajectory-heavy D4 flux scans into resumable sufficient statistics.

The compact format deliberately stores no per-trajectory physical errors,
observations, corrections, or BP messages.  For each (size, p_X) cell it keeps
the Bernoulli counts needed to recompute LER confidence intervals, deterministic
resume position, matched-policy contingency counts, and small fixed-size batch
histograms for drift/correlation diagnostics.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Iterator


POLICY_ORDER = (
    "O0_unit_weight_MWPM",
    "O2_published_herald_weight_MWPM",
    "R6D_local_BP_posterior_LLR_MWPM",
)


def wilson_interval(failures: int, total: int, confidence: float) -> list[float | None]:
    if total <= 0:
        return [None, None]
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    p = failures / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    radius = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def iter_rows_and_metadata(path: Path) -> tuple[Iterator[dict], dict]:
    """Return a streaming row iterator plus metadata populated after exhaustion."""
    decoder = json.JSONDecoder()
    metadata: dict = {}

    def rows() -> Iterator[dict]:
        with path.open("r", encoding="utf-8") as handle:
            prefix = ""
            marker = '"rows": ['
            while marker not in prefix:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    raise ValueError(f"{path} has no top-level rows array")
                prefix += chunk
            before, buffer = prefix.split(marker, 1)
            prefix_without_rows = before + '"rows": '
            while True:
                buffer = buffer.lstrip()
                if not buffer:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        raise ValueError(f"unterminated rows array in {path}")
                    buffer += chunk
                    continue
                if buffer[0] == "]":
                    suffix = buffer[1:] + handle.read()
                    metadata.update(json.loads(prefix_without_rows + "[]" + suffix))
                    return
                if buffer[0] == ",":
                    buffer = buffer[1:]
                    continue
                while True:
                    try:
                        row, end = decoder.raw_decode(buffer)
                        break
                    except json.JSONDecodeError:
                        chunk = handle.read(1024 * 1024)
                        if not chunk:
                            raise ValueError(f"invalid row JSON in {path}")
                        buffer += chunk
                if not isinstance(row, dict):
                    raise ValueError(f"non-object row in {path}")
                yield row
                buffer = buffer[end:]

    return rows(), metadata


def _new_policy() -> dict:
    return {
        "decoded": 0,
        "unavailable": 0,
        "decoder_logical_failures": 0,
        "bp_converged": 0,
        "bp_nonconverged": 0,
        "outcome_stage_counts": defaultdict(int),
    }


def _new_cell(size: int, rate: float) -> dict:
    return {
        "size": size,
        "p_X": rate,
        "attempted_histories": 0,
        "next_trajectory_index": 0,
        "terminal_physical_winding": 0,
        "policies": defaultdict(_new_policy),
        "paired_outcomes": defaultdict(lambda: {
            "matched_decoded": 0,
            "both_success": 0,
            "left_failure_right_success": 0,
            "left_success_right_failure": 0,
            "both_failure": 0,
        }),
        "batches": {},
    }


def _new_batch(start: int, batch_size: int) -> dict:
    return {
        "trajectory_index_start": start,
        "trajectory_index_stop_exclusive": start,
        "attempted_histories": 0,
        "terminal_physical_winding": 0,
        "policy_decoder_logical_failures": defaultdict(int),
        "policy_decoded": defaultdict(int),
        "policy_unavailable": defaultdict(int),
        "batch_capacity": batch_size,
    }


def compact(path: Path, *, batch_size: int = 256) -> dict:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    row_iter, metadata = iter_rows_and_metadata(path)
    cells: dict[tuple[int, float], dict] = {}
    for row in row_iter:
        size = int(row["size"])
        rate = float(row["p_X"])
        index = int(row["trajectory_index"])
        key = (size, rate)
        cell = cells.setdefault(key, _new_cell(size, rate))
        if index != cell["next_trajectory_index"]:
            raise ValueError(
                f"non-contiguous trajectory index in {path}: cell {key}, "
                f"expected {cell['next_trajectory_index']}, observed {index}"
            )
        cell["next_trajectory_index"] += 1
        cell["attempted_histories"] += 1

        batch_start = (index // batch_size) * batch_size
        batch = cell["batches"].setdefault(batch_start, _new_batch(batch_start, batch_size))
        batch["attempted_histories"] += 1
        batch["trajectory_index_stop_exclusive"] = index + 1

        terminal = row.get("status") == "terminal_physical_winding"
        if terminal:
            cell["terminal_physical_winding"] += 1
            batch["terminal_physical_winding"] += 1

        policies = row.get("policies", {})
        if not policies and "arms" in row:
            policies = {
                f"arm_{name}": {
                    # R6AF uses status="flux_union_logical_failure" for a
                    # completed logical-loss outcome.  It is an observed
                    # Bernoulli result, not decoder unavailability.
                    "status": "decoded" if isinstance(arm.get("logical_error"), bool) else arm.get("status"),
                    "flux_union_logical_failure": arm.get("logical_error"),
                    "outcome_stage": arm.get("stage"),
                }
                for name, arm in row["arms"].items()
            }
        elif not policies and "flux_union_logical_failure" in row:
            policies = {
                "single_decoder": {
                    "status": "decoded" if row.get("status") == "nonterminal" else "not_run",
                    "flux_union_logical_failure": row.get("flux_union_logical_failure"),
                }
            }
        for policy, decoded in policies.items():
            summary = cell["policies"][policy]
            if decoded.get("status") == "decoded":
                summary["decoded"] += 1
                batch["policy_decoded"][policy] += 1
                failure = bool(decoded.get("flux_union_logical_failure"))
                summary["decoder_logical_failures"] += int(failure)
                batch["policy_decoder_logical_failures"][policy] += int(failure)
                bp = decoded.get("bp")
                if isinstance(bp, dict):
                    if bool(bp.get("converged")):
                        summary["bp_converged"] += 1
                    else:
                        summary["bp_nonconverged"] += 1
                stage = decoded.get("outcome_stage")
                if stage is not None:
                    summary["outcome_stage_counts"][str(stage)] += 1
            else:
                summary["unavailable"] += 1
                batch["policy_unavailable"][policy] += 1

        ordered_policies = [policy for policy in POLICY_ORDER if policy in policies]
        ordered_policies.extend(sorted(set(policies) - set(ordered_policies)))
        decoded_policies = [
            policy for policy in ordered_policies
            if policies.get(policy, {}).get("status") == "decoded"
        ]
        for left_index, left in enumerate(decoded_policies):
            for right in decoded_policies[left_index + 1:]:
                pair = cell["paired_outcomes"][f"{left} :: {right}"]
                left_failure = bool(policies[left]["flux_union_logical_failure"])
                right_failure = bool(policies[right]["flux_union_logical_failure"])
                pair["matched_decoded"] += 1
                if left_failure and right_failure:
                    pair["both_failure"] += 1
                elif left_failure:
                    pair["left_failure_right_success"] += 1
                elif right_failure:
                    pair["left_success_right_failure"] += 1
                else:
                    pair["both_success"] += 1

    compact_cells = []
    for key in sorted(cells):
        cell = cells[key]
        attempted = cell["attempted_histories"]
        terminal = cell["terminal_physical_winding"]
        policy_payload = {}
        ordered_policies = [policy for policy in POLICY_ORDER if policy in cell["policies"]]
        ordered_policies.extend(sorted(set(cell["policies"]) - set(ordered_policies)))
        for policy in ordered_policies:
            summary = dict(cell["policies"][policy])
            summary["outcome_stage_counts"] = dict(summary["outcome_stage_counts"])
            failures = terminal + summary["decoder_logical_failures"]
            summary.update({
                "logical_failures": failures,
                "logical_error_rate": failures / attempted if attempted else None,
                "wilson_90": wilson_interval(failures, attempted, 0.90),
                "wilson_95": wilson_interval(failures, attempted, 0.95),
            })
            policy_payload[policy] = summary
        batches = []
        for start in sorted(cell["batches"]):
            batch = cell["batches"][start]
            batch["policy_decoder_logical_failures"] = dict(batch["policy_decoder_logical_failures"])
            batch["policy_decoded"] = dict(batch["policy_decoded"])
            batch["policy_unavailable"] = dict(batch["policy_unavailable"])
            batches.append(batch)
        compact_cells.append({
            "size": cell["size"],
            "p_X": cell["p_X"],
            "attempted_histories": attempted,
            "next_trajectory_index": cell["next_trajectory_index"],
            "terminal_physical_winding": terminal,
            "policies": policy_payload,
            "paired_outcomes": dict(cell["paired_outcomes"]),
            "batches": batches,
        })

    retained_metadata = {
        key: metadata[key]
        for key in (
            "schema_version", "status", "generated_at", "manifest", "scan_design",
            "backend_provenance", "integrity_gate_report", "claim_boundary",
        )
        if key in metadata
    }
    return {
        "schema_version": 1,
        "format": "resumable_flux_scan_sufficient_statistics",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "file": path.name,
            "bytes_before_compaction": path.stat().st_size,
            "metadata": retained_metadata,
        },
        "batch_size": batch_size,
        "cells": compact_cells,
        "totals": {
            "cells": len(compact_cells),
            "attempted_histories": sum(cell["attempted_histories"] for cell in compact_cells),
        },
        "semantics": {
            "logical_failure": (
                "terminal physical winding, or decoder flux_union_logical_failure on a decoded "
                "nonterminal record"
            ),
            "bp_convergence": "diagnostic only; never a logical-failure gate",
            "resume": (
                "resume deterministic sampling at next_trajectory_index using the manifest seed_salt; "
                "merge by integer addition of counts and append non-overlapping batches"
            ),
            "uncertainty": (
                "Wilson intervals use binomial attempted-history counts. Batches are retained only "
                "for drift/correlation diagnostics, not required for IID binomial intervals."
            ),
            "omitted": (
                "all per-trajectory physical errors, observations, corrections, BP messages, and timings"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-size", type=int, default=256)
    args = parser.parse_args()
    payload = compact(args.input, batch_size=args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({
        "output": str(args.output),
        "cells": payload["totals"]["cells"],
        "attempted_histories": payload["totals"]["attempted_histories"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
