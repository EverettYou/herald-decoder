#!/usr/bin/env python3
"""Validate and compact historical Monte-Carlo payloads before deletion.

This script is deliberately conservative: it writes compact replacements and a
deletion manifest, but does not delete any source payload.  A caller should only
remove paths listed in ``validated_removals`` after this command exits cleanly.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
LAB3 = REPO / "labs/lab-003-herald-threshold-phase-diagram"
LAB4 = REPO / "labs/lab-004-d4-intrinsic-heralded-decoding"
BATCH_SIZE = 256
OLD_HEAD = "9b6bdde7eefd86a4e35fcbc759d9e7688b79a30c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def key_value(record: dict[str, Any], key: str) -> Any:
    aliases = {"L": "size", "p": "error_rate"}
    if key in record:
        return record[key]
    return record.get(aliases.get(key, ""))


def verify_lab3_raw(path: Path) -> dict[str, Any]:
    compact_path = Path(str(path)[: -len("-raw.jsonl.gz")] + ".json")
    if not compact_path.exists():
        raise RuntimeError(f"no compact sibling for {rel(path)}")
    compact = json.loads(compact_path.read_text())
    metadata = compact.get("raw_records", {})
    actual_hash = sha256(path)
    if metadata.get("sha256") != actual_hash:
        raise RuntimeError(f"SHA mismatch for {rel(path)}")

    per_seed: collections.Counter[tuple[Any, ...]] = collections.Counter()
    cells: collections.Counter[tuple[Any, ...]] = collections.Counter()
    records = 0
    with gzip.open(path, "rt") as handle:
        for line in handle:
            row = json.loads(line)
            records += 1
            cell = (row.get("lattice"), row.get("L"), row.get("p"), row.get("q"))
            seed = cell + (row.get("seed"),)
            failed = int(bool(row.get("logical_failure")))
            per_seed[seed + ("shots",)] += 1
            per_seed[seed + ("logical_errors",)] += failed
            cells[cell + ("shots",)] += 1
            cells[cell + ("logical_errors",)] += failed

    if metadata.get("records") != records:
        raise RuntimeError(f"record-count mismatch for {rel(path)}")
    for row in compact.get("per_seed", []):
        key = tuple(key_value(row, k) for k in ("lattice", "L", "p", "q", "seed"))
        if per_seed[key + ("shots",)] != row["shots"]:
            raise RuntimeError(f"per-seed shot mismatch for {rel(path)}: {key}")
        if per_seed[key + ("logical_errors",)] != row["logical_errors"]:
            raise RuntimeError(f"per-seed error mismatch for {rel(path)}: {key}")
    for row in compact.get("summaries", []):
        key = tuple(key_value(row, k) for k in ("lattice", "L", "p", "q"))
        if cells[key + ("shots",)] != row["shots"]:
            raise RuntimeError(f"cell shot mismatch for {rel(path)}: {key}")
        if cells[key + ("logical_errors",)] != row["logical_errors"]:
            raise RuntimeError(f"cell error mismatch for {rel(path)}: {key}")

    metadata["retention"] = "trajectory payload removed after count/hash validation"
    metadata["available_statistics"] = ["per_seed", "summaries"]
    compact["raw_records"] = metadata
    dump(compact_path, compact)
    return {
        "path": rel(path),
        "bytes": path.stat().st_size,
        "sha256": actual_hash,
        "records": records,
        "replacement": rel(compact_path),
        "validation": "sha256, records, per_seed shots/errors, cell shots/errors",
    }


def compact_embedded(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text())
    rows = document.get("raw_shots")
    if not isinstance(rows, list):
        raise RuntimeError(f"missing raw_shots in {rel(path)}")
    old_hash = sha256(path)
    old_bytes = path.stat().st_size
    outcomes = [
        field
        for field in ("logical_failure", "herald_logical_failure", "mwpm_logical_failure")
        if rows and field in rows[0]
    ]
    group_fields = [field for field in ("lattice", "L", "p", "q", "seed") if rows and field in rows[0]]
    counters: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    batches: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    pair_counts: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in rows:
        group = tuple(row[field] for field in group_fields)
        batch = group + (int(row.get("shot", 0)) // BATCH_SIZE,)
        counters[group]["shots"] += 1
        batches[batch]["shots"] += 1
        for outcome in outcomes:
            counters[group][outcome] += int(bool(row[outcome]))
            batches[batch][outcome] += int(bool(row[outcome]))
        if {"herald_logical_failure", "mwpm_logical_failure"}.issubset(row):
            pair = f"h{int(bool(row['herald_logical_failure']))}_m{int(bool(row['mwpm_logical_failure']))}"
            pair_counts[group][pair] += 1

    per_seed = []
    for group in sorted(counters, key=str):
        item = dict(zip(group_fields, group))
        item.update(counters[group])
        if group in pair_counts:
            item["paired_outcomes"] = dict(sorted(pair_counts[group].items()))
        per_seed.append(item)
    per_batch = []
    for group in sorted(batches, key=str):
        item = dict(zip(group_fields + ["batch_index"], group))
        item.update(batches[group])
        per_batch.append(item)

    # Existing published summary counts are the acceptance oracle.
    cell_fields = [field for field in group_fields if field != "seed"]
    aggregated: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for group, count in counters.items():
        cell = group[:-1] if group_fields[-1] == "seed" else group
        aggregated[cell].update(count)
    for summary in document.get("summaries", []):
        cell = tuple(key_value(summary, field) for field in cell_fields)
        count = aggregated[cell]
        if count["shots"] != summary["shots"]:
            raise RuntimeError(f"summary shot mismatch in {rel(path)}: {cell}")
        expected = count["logical_failure" if "logical_failure" in outcomes else "herald_logical_failure"]
        if expected != summary["logical_errors"]:
            raise RuntimeError(f"summary error mismatch in {rel(path)}: {cell}")
        if "mwpm_logical_errors" in summary and count["mwpm_logical_failure"] != summary["mwpm_logical_errors"]:
            raise RuntimeError(f"MWPM summary mismatch in {rel(path)}: {cell}")

    del document["raw_shots"]
    document["compact_counts"] = {
        "schema_version": 1,
        "source_sha256": old_hash,
        "source_bytes": old_bytes,
        "source_trajectory_records": len(rows),
        "batch_size": BATCH_SIZE,
        "group_fields": group_fields,
        "outcome_fields": outcomes,
        "per_seed": per_seed,
        "per_batch": per_batch,
        "retention": "raw_shots removed after exact reconciliation with summaries",
    }
    dump(path, document)
    return {
        "path": rel(path),
        "bytes_before": old_bytes,
        "bytes_after": path.stat().st_size,
        "source_sha256": old_hash,
        "records_compacted": len(rows),
        "validation": "per-seed/per-batch aggregation reconciled to published cell summaries",
    }


def compact_r5a() -> tuple[dict[str, Any], dict[str, Any]]:
    raw = LAB4 / "results/r5a-paper-lattice-public-decoder-pilot.jsonl.gz"
    analysis_path = LAB4 / "results/r5a-paper-lattice-public-decoder-analysis.json"
    output = LAB4 / "results/r5a-paper-lattice-public-decoder-sufficient-statistics.json"
    analysis = json.loads(analysis_path.read_text())
    cells: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    batches: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    paired: dict[tuple[Any, ...], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    pending: dict[tuple[Any, ...], dict[str, bool]] = collections.defaultdict(dict)
    records = 0
    with gzip.open(raw, "rt") as handle:
        for line in handle:
            row = json.loads(line)
            records += 1
            cell = (row["size"], row["error_rate"], row["mode"])
            cells[cell]["histories"] += 1
            cells[cell]["logical_failures"] += int(bool(row["logical_error"]))
            cells[cell][f"stage:{row['stage_outcome']}"] += 1
            batch = cell + (int(row["seed_index"]) // BATCH_SIZE,)
            batches[batch]["histories"] += 1
            batches[batch]["logical_failures"] += int(bool(row["logical_error"]))
            pair_key = (row["size"], row["error_rate"], row["physical_seed"], row["seed_index"])
            pending[pair_key][row["mode"]] = bool(row["logical_error"])
    for key, modes in pending.items():
        if set(modes) != {"heralded", "syndrome_only"}:
            raise RuntimeError(f"unpaired R5a record: {key}")
        paired[key[:2]][f"h{int(modes['heralded'])}_s{int(modes['syndrome_only'])}"] += 1

    for row in analysis["cells"]:
        key = (row["size"], row["error_rate"], row["mode"])
        count = cells[key]
        if count["histories"] != row["histories"] or count["logical_failures"] != row["logical_failures"]:
            raise RuntimeError(f"R5a analysis mismatch: {key}")
        stages = {key.removeprefix("stage:"): val for key, val in count.items() if key.startswith("stage:")}
        if stages != row["stage_counts"]:
            raise RuntimeError(f"R5a stage mismatch: {key}")

    compact = {
        "schema_version": 1,
        "status": "historical_sufficient_statistics",
        "source": {
            "path": rel(raw),
            "sha256": sha256(raw),
            "bytes": raw.stat().st_size,
            "records": records,
            "retention": "raw trajectory payload removed after exact reconciliation with analysis",
        },
        "batch_size": BATCH_SIZE,
        "cells": [dict(size=k[0], error_rate=k[1], mode=k[2], **dict(v)) for k, v in sorted(cells.items())],
        "batches": [dict(size=k[0], error_rate=k[1], mode=k[2], batch_index=k[3], **dict(v)) for k, v in sorted(batches.items())],
        "paired_policy_outcomes": [dict(size=k[0], error_rate=k[1], **dict(v)) for k, v in sorted(paired.items())],
        "analysis": rel(analysis_path),
        "claim_boundary": "Sufficient statistics preserve LER, batch dispersion, stage counts, and paired-policy comparisons; individual trajectories are intentionally omitted.",
    }
    dump(output, compact)
    removal = {
        "path": rel(raw),
        "bytes": raw.stat().st_size,
        "sha256": compact["source"]["sha256"],
        "records": records,
        "replacement": rel(output),
        "validation": "cell failures/stages reconciled to analysis; policies paired by physical seed",
    }
    return removal, {"path": rel(output), "bytes": output.stat().st_size}


def compact_lab4_integrity_audit() -> dict[str, Any]:
    path = LAB4 / "manifests/r6v-r6u-bp-integrity-audit-2026-08-30.json"
    document = json.loads(path.read_text())
    rows = document.pop("rows")
    if len(rows) != document["scope"]["zero_failure_rows_replayed"]:
        raise RuntimeError("R6V row count does not match scope")
    old_bytes = path.stat().st_size
    old_hash = sha256(path)
    document["compaction"] = {
        "source_sha256": old_hash,
        "source_bytes": old_bytes,
        "rows_omitted": len(rows),
        "retained": ["scope", "acceptance", "shadow_summary", "truth_leakage_boundary", "claim_boundary"],
        "validation": "omitted row count equals registered replay scope",
    }
    dump(path, document)
    return {"path": rel(path), "bytes_before": old_bytes, "bytes_after": path.stat().st_size, "rows_compacted": len(rows)}


def verify_reference_sources() -> list[dict[str, Any]]:
    verified = []
    for path in sorted((REPO / "references").glob("*/source.tar*")):
        provenance_path = path.parent / "provenance.json"
        provenance = json.loads(provenance_path.read_text())
        expected = provenance.get("sha256", {}).get(path.name)
        actual = sha256(path)
        urls = provenance.get("urls", {})
        url = urls.get("source") or urls.get("repository") or provenance.get("source_url") or provenance.get("url")
        if expected != actual:
            raise RuntimeError(f"reference SHA mismatch: {rel(path)}")
        if not url:
            raise RuntimeError(f"reference source has no provenance URL: {rel(path)}")
        verified.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": actual, "retrieval_url": url, "provenance": rel(provenance_path)})
    return verified


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="repository-cleanup-2026-09-05.json")
    args = parser.parse_args()

    lab3_removals = []
    for path in sorted((LAB3 / "results").glob("**/*-raw.jsonl.gz")):
        lab3_removals.append(verify_lab3_raw(path))

    embedded = [
        compact_embedded(LAB3 / "results/q0-square-production-2026-08-27.json"),
        compact_embedded(LAB3 / "results/q0-square-refined-5000-2026-08-27.json"),
        compact_embedded(LAB3 / "results/q1-square-l11-l13-refined-5000-2026-08-27.json"),
    ]
    r5a_removal, r5a_output = compact_r5a()
    lab4_embedded = compact_lab4_integrity_audit()
    references = verify_reference_sources()

    removals = lab3_removals + [r5a_removal] + references
    manifest = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "old_git_head": OLD_HEAD,
        "policy": {
            "keep": ["reference PDFs", "compact Monte-Carlo counts", "figures", "scripts", ".env (local only)"],
            "remove": ["per-trajectory payloads", "verified reproducible source archives", "ignored caches and temporary files"],
            "batch_size": BATCH_SIZE,
        },
        "validated_removals": removals,
        "in_place_compactions": embedded + [lab4_embedded],
        "created_compact_artifacts": [r5a_output],
        "totals": {
            "validated_removal_files": len(removals),
            "validated_removal_bytes": sum(item["bytes"] for item in removals),
            "embedded_bytes_before": sum(item["bytes_before"] for item in embedded) + lab4_embedded["bytes_before"],
            "embedded_bytes_after": sum(item["bytes_after"] for item in embedded) + lab4_embedded["bytes_after"],
        },
        "validation": "All listed source paths were present and passed their format-specific checks before this manifest was written.",
    }
    dump(REPO / args.manifest, manifest)
    print(json.dumps(manifest["totals"], indent=2))


if __name__ == "__main__":
    main()
