#!/usr/bin/env python3
"""Apply only the hash-validated removals in the repository cleanup manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "repository-cleanup-2026-09-05.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe(relative: str) -> Path:
    path = (REPO / relative).resolve()
    path.relative_to(REPO.resolve())
    return path


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    deleted_files = 0
    deleted_bytes = 0
    for item in manifest["validated_removals"]:
        path = safe(item["path"])
        if not path.is_file():
            raise RuntimeError(f"validated source is missing: {item['path']}")
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"validated source changed since manifest: {item['path']}")
        deleted_bytes += path.stat().st_size
        path.unlink()
        deleted_files += 1

    # These paths are local, ignored, reproducible caches or incomplete files.
    # The exact allowlist protects .env, .tmp/README.md, results, and source code.
    cache_dirs = [
        ".venv",
        ".uv-cache",
        "tmp",
        ".pytest_cache",
        "dashboard/__pycache__",
        "dashboard/backend/__pycache__",
        "dashboard/tests/__pycache__",
        "labs/lab-001-string-herald-visualization/scripts/__pycache__",
        "labs/lab-002-herald-belief-matching/scripts/__pycache__",
        "labs/lab-003-herald-threshold-phase-diagram/scripts/__pycache__",
        "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/__pycache__",
        "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/__pycache__",
        "labs/lab-006-sun-bp-theory/scripts/__pycache__",
        "scripts/__pycache__",
        "skills/consult-human/tests/__pycache__",
        "skills/organize-lab/scripts/__pycache__",
        "skills/wiki-lint/scripts/__pycache__",
        "skills/wiki-lint/tests/__pycache__",
        "src/herald_decoder/__pycache__",
    ]
    cache_files = [
        ".DS_Store",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-honeycomb-q000-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5259",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-honeycomb-q005-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5261",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-honeycomb-q010-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5383",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-honeycomb-q015-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5544",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-residual80-honeycomb-q090-discovery-1000-2026-08-28-raw.jsonl.gz.tmp-32596",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-square-q015-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5529",
        "labs/lab-003-herald-threshold-phase-diagram/results/.phase2-square-q020-discovery-1000-2026-08-27-raw.jsonl.gz.tmp-5598",
        "labs/lab-003-herald-threshold-phase-diagram/results/.q1-square-l5-l13-crossing-refined-10000-2026-08-27-raw.jsonl.gz.tmp-9453",
        "labs/lab-004-d4-intrinsic-heralded-decoding/results/r6ai-critical-band-refinement.checkpoint.json",
    ]
    local_bytes = 0
    for child in (REPO / ".tmp").iterdir():
        if child.name != "README.md":
            local_bytes += child.stat().st_size if child.is_file() else 0
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    for relative in cache_dirs:
        path = safe(relative)
        if path.is_dir():
            shutil.rmtree(path)
    for relative in cache_files:
        path = safe(relative)
        if path.is_file():
            local_bytes += path.stat().st_size
            path.unlink()
    print(json.dumps({"validated_files_deleted": deleted_files, "validated_bytes_deleted": deleted_bytes, "ignored_file_bytes_deleted_excluding_directories": local_bytes}, indent=2))


if __name__ == "__main__":
    main()
