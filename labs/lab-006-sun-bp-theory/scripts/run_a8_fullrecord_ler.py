#!/usr/bin/env python3
"""Checkpointed A8 curves using the artifact's complete interior (m,R) decoder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_a7_ler as artifact_runner

RATES = [round(.02 * number, 2) for number in range(1, 26)]
SIZES = (5, 7, 9, 11)
SCORING_RULE = artifact_runner.SCORING_RULE


def endpoint_rows(lattice: str, group: str, shots: int, sizes: tuple[int, ...]) -> list[dict]:
    return [{"lattice": lattice, "L": size, "p": 0.0, "shots": shots, "group": group,
             "arm": "representation_herald", "logical_failures": 0, "ler": 0.0,
             "logical_parity_failures": 0, "wilson95": [0.0, 0.0], "bp_nonconverged": 0, "invalid_correction": 0,
             "exact_endpoint": True} for size in sizes]


def render(rows: list[dict], destination: Path, *, convergence: bool, preview: bool = False) -> None:
    fig, axis = plt.subplots(figsize=(8.5, 5.5))
    styles = {5: "-", 7: "--", 9: ":", 11: "-."}
    sizes = sorted({row["L"] for row in rows})
    for size in sizes:
        curve = sorted((row for row in rows if row["L"] == size), key=lambda row: row["p"])
        if convergence:
            axis.plot([row["p"] for row in curve], [row["bp_nonconverged"] / row["shots"] for row in curve], color="#d34f8d", linestyle=styles[size], marker="o", label=f"L={size}")
        else:
            axis.errorbar([row["p"] for row in curve], [row["ler"] for row in curve],
                          yerr=[[row["ler"] - row["wilson95"][0] for row in curve], [row["wilson95"][1] - row["ler"] for row in curve]],
                          color="#d34f8d", linestyle=styles[size], marker="o", label=f"L={size}")
    sample = rows[0]
    qualifier = " — completed-size preview" if preview else ""
    axis.set_title(f"{sample['lattice']} {sample['group']} — full interior (m,R), {sample['shots']:,} shots/cell{qualifier}")
    axis.set_xlabel("physical edge-error rate p"); axis.set_xlim(0, .5)
    if convergence:
        maximum = max(row["bp_nonconverged"] / row["shots"] for row in rows)
    else:
        maximum = max(row["wilson95"][1] for row in rows)
    axis.set_ylim(0.0, max(.02, 1.15 * maximum))
    axis.set_ylabel("BP nonconvergence fraction" if convergence else "logical error rate")
    axis.grid(alpha=.25); axis.legend(title="code distance"); fig.tight_layout(); fig.savefig(destination, dpi=200); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lattice", choices=("honeycomb", "square"), required=True)
    parser.add_argument("--group", choices=("SU3", "SU2", "U1"), required=True)
    parser.add_argument("--shots", type=int, default=20000)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--sizes", type=int, nargs="+", choices=SIZES, default=SIZES)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preview", action="store_true", help="render only the completed checkpoint rows, without sampling")
    args = parser.parse_args()
    selected_sizes = tuple(args.sizes)
    # Reuse the calibrated artifact path, restricting only what is displayed.
    artifact_runner.GROUPS = (args.group,)
    artifact_runner.ARMS = ("representation_herald",)
    artifact_runner.warm_numba_kernels()
    results = HERE.parent / "results"
    target = results / f"a8-fullrecord-{args.tag}.json"
    scope = {"lattice": args.lattice, "group": args.group, "shots_per_cell": args.shots, "scoring_rule": SCORING_RULE,
             "runner": "numba-record-generation+fixed-weight-pymatching-decode-batch"}
    rows = []
    if args.resume and target.exists():
        existing = json.loads(target.read_text())
        if existing["scope"] != scope:
            raise ValueError("checkpoint scope differs")
        rows = existing["rows"]
    if args.preview:
        if not rows:
            raise ValueError("no checkpoint rows to preview")
        completed_sizes = {row["L"] for row in rows if row["p"] == .5}
        preview_rows = [row for row in rows if row["L"] in completed_sizes]
        render(preview_rows, results / f"a8-fullrecord-{args.tag}-preview-ler.png", convergence=False, preview=True)
        render(preview_rows, results / f"a8-fullrecord-{args.tag}-preview-nonconvergence.png", convergence=True, preview=True)
        return
    completed = {(row["L"], row["p"]) for row in rows}
    for row in endpoint_rows(args.lattice, args.group, args.shots, selected_sizes):
        if (row["L"], row["p"]) not in completed:
            rows.append(row)
    for size in selected_sizes:
        for rate_index, p in enumerate(RATES):
            if (size, p) not in completed:
                rows.extend(artifact_runner.run_cell(args.lattice, size, p, args.shots, 950000 + 100 * size + rate_index, 256, optimized=True))
                payload = {"status": "running", "scope": scope, "rows": rows}
                target.write_text(json.dumps(payload, indent=2) + "\n")
    payload = {"status": "complete", "scope": scope, "rows": rows}
    target.write_text(json.dumps(payload, indent=2) + "\n")
    render(rows, results / f"a8-fullrecord-{args.tag}-ler.png", convergence=False)
    render(rows, results / f"a8-fullrecord-{args.tag}-nonconvergence.png", convergence=True)


if __name__ == "__main__":
    main()
