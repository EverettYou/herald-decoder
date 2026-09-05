#!/usr/bin/env python3
"""Extract a compact, reproducible cell-level summary from a completed scan."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def header(path: Path) -> dict:
    chunks: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line == '  "rows": [\n':
                break
            chunks.append(line)
    text = "".join(chunks).rstrip().rstrip(",")
    return json.loads(text + "\n}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path); parser.add_argument("output", type=Path)
    args = parser.parse_args(); payload = header(args.source)
    summary = {key: value for key, value in payload.items() if key not in {"rows", "checkpoint"}}
    summary["compaction"] = {
        "source_name": args.source.name,
        "source_sha256": hashlib.file_digest(args.source.open("rb"), "sha256").hexdigest(),
        "omitted": "per-trajectory raw rows; regenerate from manifest, seed_salt, and source hash",
    }
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source": str(args.source), "output": str(args.output), "bytes": args.output.stat().st_size}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
