#!/usr/bin/env python3
"""Plot the R6AE Stage-1 paper-unconditional finite-size LER curves."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


# This scan was intentionally allocated around the herald-aware transition.
# Unit-weight MWPM is omitted: its decision region is near p_X=0.159 and is
# presented in a dedicated low-p figure rather than as a saturated curve here.
POLICIES = (
    ("O2_published_herald_weight_MWPM", "Herald-weight MWPM"),
    ("R6D_local_BP_posterior_LLR_MWPM", "Signal-only BeliefMatching"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--stage-label", default="Stage 1")
    args = parser.parse_args()

    payload = json.loads(args.analysis.read_text(encoding="utf-8"))
    rows = payload["cells"]
    sizes = sorted({int(row["size"]) for row in rows})
    colours = plt.cm.viridis([index / max(1, len(sizes) - 1) for index in range(len(sizes))])

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.3), sharex=True, sharey=True)
    for axis, (policy, title) in zip(axes, POLICIES):
        for colour, size in zip(colours, sizes):
            selected = sorted((row for row in rows if int(row["size"]) == size), key=lambda row: row["p_X"])
            x = [row["p_X"] for row in selected]
            records = [row[policy]["all_final_iterates"] for row in selected]
            y = [record["risk"] for record in records]
            lower = [value - record["wilson_90"][0] for value, record in zip(y, records)]
            upper = [record["wilson_90"][1] - value for value, record in zip(y, records)]
            axis.errorbar(x, y, yerr=[lower, upper], marker="o", linewidth=1.4,
                          capsize=2.5, color=colour, label=f"L={size}")
        if policy == "O2_published_herald_weight_MWPM":
            axis.axvline(0.20842, color="#b33b3b", linestyle="--", linewidth=1.1,
                         label="published herald-weight threshold 20.842%")
        axis.set_title(title)
        axis.set_xlabel(r"$p_X$")
        axis.grid(alpha=0.22)
    axes[0].set_ylabel("paper-unconditional flux LER")
    axes[0].legend(fontsize=8, frameon=False)
    histories = sorted({int(row["attempted_histories"]) for row in rows})
    history_label = f"{histories[0]:,}" if len(histories) == 1 else "mixed"
    fig.suptitle(f"R6AE signal-only D4 flux scan — {args.stage_label} ({history_label} matched histories/cell)")
    fig.text(0.5, 0.01, "Finite-size diagnostic only; no threshold fit or threshold claim.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(f"wrote {args.output}", flush=True)
    plt.close(fig)


if __name__ == "__main__":
    main()
