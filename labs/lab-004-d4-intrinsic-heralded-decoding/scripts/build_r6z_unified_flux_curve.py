#!/usr/bin/env python3
"""Render provenance-preserving pooled D4 flux LER curves for Lab 004."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

LAB = Path(__file__).resolve().parents[1]
RESULTS = LAB / "results"
SOURCES = [
    ("R6V low-p (generic, equivalence-audited)", RESULTS / "r6v-x-only-flux-threshold-scan-2026-08-30.checkpoint.json"),
    ("6.23 coarse scan", RESULTS / "6-23-bp-threshold-coarse-summary.json"),
    ("6.24 upper refinement", RESULTS / "6-24-bp-threshold-upper-summary.json"),
    ("6.25 lower refinement", RESULTS / "6-25-bp-threshold-lower-summary.json"),
    ("6.27 interleaved refinement", RESULTS / "6-27-bp-threshold-interleaved-summary.json"),
]
OUT = RESULTS / "r6z-unified-d4-flux-ler-o2-vs-beliefmatching-2026-08-31.png"
SUMMARY = RESULTS / "r6z-unified-d4-flux-ler-o2-vs-beliefmatching-2026-08-31.json"
POLICIES = {
    "BeliefMatching (BP→MWPM)": "R6D_local_BP_posterior_LLR_MWPM",
    "O2 published herald-MWPM": "O2_published_herald_weight_MWPM",
}


def header(path: Path) -> dict:
    """Read metadata and cells while avoiding the large raw-row payload."""
    lines = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line == '  "rows": [\n':
                break
            lines.append(line)
    text = "".join(lines).rstrip()
    if text.endswith("}"):
        return json.loads(text)
    if text.endswith(","):
        text = text[:-1]
    return json.loads(text + "\n}")


def wilson90(k: int, n: int) -> tuple[float, float]:
    z = 1.6448536269514722
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - radius, center + radius


def main() -> None:
    pooled: dict[tuple[str, int, float], list[int]] = defaultdict(lambda: [0, 0])
    provenance = []
    for label, path in SOURCES:
        if not path.is_file():
            continue
        payload = header(path)
        count = 0
        for cell in payload["cells"]:
            for display, policy in POLICIES.items():
                summary = cell["summaries"][policy]
                key = (display, int(cell["size"]), float(cell["p_X"]))
                pooled[key][0] += int(summary["flux_union_logical_failures"])
                pooled[key][1] += int(summary["decoded_records"])
            count += 1
        provenance.append({"label": label, "path": str(path.relative_to(LAB)), "cells": count})

    records = []
    for (policy, size, rate), (failures, histories) in sorted(pooled.items()):
        lo, hi = wilson90(failures, histories)
        records.append({"policy": policy, "size": size, "p_X": rate, "failures": failures,
                        "histories": histories, "ler": failures / histories, "wilson90": [lo, hi]})
    SUMMARY.write_text(json.dumps({"scope": "D4 X-only first-stage conditional flux Boolean-union LER; p_Z=0", "provenance": provenance, "records": records}, indent=2) + "\n", encoding="utf-8")

    sizes = sorted({r["size"] for r in records})
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, len(sizes)))
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), sharex=True, sharey=True, constrained_layout=True)
    for axis, display in zip(axes, POLICIES):
        for size, color in zip(sizes, colors):
            vals = [r for r in records if r["policy"] == display and r["size"] == size]
            if not vals:
                continue
            x = np.array([r["p_X"] for r in vals]); y = np.array([r["ler"] for r in vals])
            lo = np.array([r["wilson90"][0] for r in vals]); hi = np.array([r["wilson90"][1] for r in vals])
            axis.errorbar(x, y, yerr=np.vstack((y - lo, hi - y)), color=color, marker="o", markersize=4,
                          linewidth=1.5, capsize=2, label=f"L={size}")
        axis.set_title(display)
        axis.set_xlabel(r"physical X-error rate $p_X$")
        axis.set_xlim(0.13, 0.41)
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.24)
    axes[0].set_ylabel("conditional first-stage flux logical-error rate")
    axes[1].legend(title="paper-normalized size", loc="upper left", frameon=False, ncols=2)
    fig.suptitle("D4 X-only flux recovery: O2 versus BeliefMatching", fontsize=14)
    fig.savefig(OUT, dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
