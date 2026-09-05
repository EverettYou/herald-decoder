#!/usr/bin/env python3
"""Merge disjoint A7 LER acquisition blocks without altering any samples."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_a7_ler import render_four_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    payloads = [json.loads(Path(item).read_text()) for item in args.inputs]
    scope = payloads[0]["scope"]
    if any(payload["scope"]["shots_per_cell"] != scope["shots_per_cell"] or payload["scope"]["rates"] != scope["rates"] or payload["scope"]["decoder"] != scope["decoder"] for payload in payloads[1:]):
        raise ValueError("only identical-shot, identical-rate, identical-decoder blocks may be merged")
    rows = [row for payload in payloads for row in payload["rows"]]
    keys = [(row["lattice"], row["L"], row["p"], row["group"], row["arm"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("input blocks overlap")
    result = {"protocol": "lab006-a7-frozen-artifact-ler-merged", "tag": args.tag,
              "scope": {**scope, "source_blocks": args.inputs}, "rows": rows}
    results = HERE.parent / "results"
    json_path = results / f"a7-ler-{args.tag}.json"
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    render_four_size(rows, results / f"a7-ler-{args.tag}.png", f"Lab 006 LER — {args.tag}; {scope['shots_per_cell']} shots/cell")
    render_four_size(rows, results / f"a7-bp-nonconvergence-{args.tag}.png", f"Lab 006 BP nonconvergence — {args.tag}; {scope['shots_per_cell']} shots/cell", convergence=True)


if __name__ == "__main__":
    main()
