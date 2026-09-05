#!/usr/bin/env python3
"""Recover Dropbox-reverted atomic raw files only after exact declaration checks."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_gzip_lines(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        return sum(1 for _ in source)


def recover_summary(summary_path: Path, *, lab_dir: Path = LAB_DIR) -> dict:
    payload = json.loads(summary_path.read_text())
    metadata = payload["raw_records"]
    raw_path = (lab_dir / metadata["path"]).resolve()
    expected_sha = metadata["sha256"]
    expected_records = int(metadata["records"])
    if raw_path.is_file():
        actual_sha = sha256(raw_path)
        actual_records = count_gzip_lines(raw_path)
        if actual_sha != expected_sha or actual_records != expected_records:
            raise RuntimeError(f"existing formal raw fails declaration: {raw_path}")
        return {"summary": str(summary_path), "raw": str(raw_path), "status": "already_formal", "sha256": actual_sha, "records": actual_records}
    candidates = sorted(raw_path.parent.glob(f".{raw_path.name}.tmp-*"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one atomic candidate for {raw_path}, found {len(candidates)}")
    candidate = candidates[0]
    actual_sha = sha256(candidate)
    if actual_sha != expected_sha:
        raise RuntimeError(f"atomic candidate SHA-256 mismatch: {candidate}")
    actual_records = count_gzip_lines(candidate)
    if actual_records != expected_records:
        raise RuntimeError(f"atomic candidate record-count mismatch: {candidate}")
    os.replace(candidate, raw_path)
    return {"summary": str(summary_path), "raw": str(raw_path), "status": "recovered", "sha256": actual_sha, "records": actual_records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    template = manifest["artifact_stem_template"]
    results_dir = LAB_DIR / "results"
    recovered = []
    for lattice in manifest["lattices"]:
        for q in manifest["q_values"]:
            tag = f"q{int(round(100 * float(q))):03d}"
            stem = template.format(lattice=lattice, q_tag=tag)
            recovered.append(recover_summary(results_dir / f"{stem}.json"))
    audit = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "campaign": manifest["campaign"],
        "status": "passed",
        "files": recovered,
        "recovered": sum(item["status"] == "recovered" for item in recovered),
        "already_formal": sum(item["status"] == "already_formal" for item in recovered),
        "total_records": sum(item["records"] for item in recovered),
        "evidence_boundary": "Storage-layer recovery only. Every move required exact summary-declared SHA-256 and gzip record count; scientific validation remains the analyzer's responsibility.",
    }
    audit_path = args.audit or results_dir / f"{manifest['campaign']}-atomic-raw-recovery.json"
    temporary = audit_path.with_name(f".{audit_path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(audit, indent=2) + "\n")
    os.replace(temporary, audit_path)
    print(json.dumps({"audit": str(audit_path), "recovered": audit["recovered"], "already_formal": audit["already_formal"], "total_records": audit["total_records"]}))


if __name__ == "__main__":
    main()
