#!/usr/bin/env python3
"""Reversibly archive Phase 2 shards from one superseded source fingerprint."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = LAB_DIR / "results"


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--numba-kernel-sha256", required=True)
    parser.add_argument("--archive-name", required=True)
    args = parser.parse_args()
    archive = RESULTS_DIR / args.archive_name
    archive.mkdir(parents=True, exist_ok=True)
    moved = []
    for summary in sorted(RESULTS_DIR.glob("phase2-*-discovery-1000-2026-08-27.json")):
        payload = json.loads(summary.read_text())
        if payload.get("source_hashes", {}).get("numba_kernels") != args.numba_kernel_sha256:
            continue
        raw = LAB_DIR / payload["raw_records"]["path"]
        if not raw.is_file():
            raise SystemExit(f"raw artifact is missing: {raw}")
        archived_raw = archive / raw.name
        archived_summary = archive / summary.name
        if archived_raw.exists() or archived_summary.exists():
            raise SystemExit(f"archive destination already exists for {summary.name}")
        os.replace(raw, archived_raw)
        payload["raw_records"]["path"] = str(archived_raw.relative_to(LAB_DIR))
        payload["superseded"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "reason": "shared numba-kernel source fingerprint changed during the parallel campaign; shard excluded from combined inference and rerun under the final common source",
        }
        atomic_json(archived_summary, payload)
        summary.unlink()
        moved.append(summary.name)
    print(json.dumps({"archive": str(archive), "count": len(moved), "shards": moved}, indent=2))


if __name__ == "__main__":
    main()
