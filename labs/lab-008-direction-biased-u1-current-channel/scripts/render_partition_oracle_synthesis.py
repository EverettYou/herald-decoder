"""Render the registered partition-prediction / exact-oracle evidence boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
MANIFEST = LAB / "manifests/partition-oracle-synthesis-2026-09-19.json"
ACTIVITY = LAB / "results/current-activity-expansion-2026-09-18.json"
ADAPTIVE = LAB / "results/adaptive-charge-branch-bound-2026-09-19.json"
ORACLE = LAB / "results/square-mechanism-2026-09-18-analysis.json"
SIZE_BIAS = LAB / "results/size-bias-distributions-2026-09-18.json"
RESULT = LAB / "results/partition-oracle-synthesis-2026-09-19.json"
FIGURE = LAB / "figures/partition-oracle-evidence-boundary.png"


def load(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    activity = load(ACTIVITY)
    adaptive = load(ADAPTIVE)
    oracle = load(ORACLE)
    size_bias = load(SIZE_BIAS)

    final_activity = activity["pilot"]["checkpoints"][-1]["cells"]
    certified = {}
    for row in final_activity:
        key = (float(row["p"]), float(row["q"]))
        certified[key] = {
            "p": float(row["p"]),
            "q": float(row["q"]),
            "lower": float(row["lower"]),
            "upper": float(row["upper"]),
            "leading": float(row["leading_dilute_prediction"]),
            "upper_method": "activity_k4",
        }

    adaptive_best = {float(study["q"]): study["runs"][-1] for study in adaptive["studies"]}
    for q in (0.97, 1.0):
        row = certified[(0.08, q)]
        promoted = adaptive_best[q]
        assert promoted["promoted"]
        assert promoted["upper"] < row["upper"]
        row["upper"] = float(promoted["upper"])
        row["upper_method"] = "adaptive_B1024"

    oracle_rows = []
    for row in oracle["rows"]:
        if int(row["L"]) == 5 and float(row["q"]) in (0.5, 0.75, 1.0):
            oracle_rows.append({
                "p": float(row["p"]),
                "q": float(row["q"]),
                "mean": float(row["risk"]["mean"][0]),
                "interval": [float(x) for x in row["risk"]["interval"][0]],
                "shots": int(row["shots"]),
                "interval_type": "pointwise bootstrap 95% over independent physical records",
            })
    for row in size_bias["square_grid"]:
        if int(row["L"]) == 5 and float(row["q"]) == 0.97:
            oracle_rows.append({
                "p": float(row["p"]),
                "q": 0.97,
                "mean": float(row["risk"]["mean"][0]),
                "interval": [float(x) for x in row["risk"]["interval"][0]],
                "shots": int(row["shots"]),
                "interval_type": "pointwise bootstrap 95% over independent physical records",
            })

    certified_rows = [certified[key] for key in sorted(certified)]
    checks = {
        "certificate_count": len(certified_rows),
        "oracle_anchor_count": len(oracle_rows),
        "all_certificates_ordered": all(0 <= r["lower"] <= r["upper"] <= 0.5 for r in certified_rows),
        "all_oracle_means_inside_intervals": all(r["interval"][0] <= r["mean"] <= r["interval"][1] for r in oracle_rows),
        "promoted_p08_upper_q": [q for q in (0.97, 1.0) if certified[(0.08, q)]["upper_method"] == "adaptive_B1024"],
        "retained_activity_p08_upper_q": [q for q in (0.5, 0.75) if certified[(0.08, q)]["upper_method"] == "activity_k4"],
        "fitted_or_interpolated_points": 0,
    }
    assert checks["certificate_count"] == 12
    assert checks["oracle_anchor_count"] == 10
    assert checks["all_certificates_ordered"]
    assert checks["all_oracle_means_inside_intervals"]

    q_values = (0.5, 0.75, 0.97, 1.0)
    colors = {0.5: "#2A6FBB", 0.75: "#6A4C93", 0.97: "#D97706", 1.0: "#B42318"}
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 10.5), sharex=True, sharey=True)
    for ax, q in zip(axes.flat, q_values):
        color = colors[q]
        rows = [r for r in certified_rows if r["q"] == q]
        for r in rows:
            ax.vlines(r["p"], r["lower"], r["upper"], color=color, linewidth=6, alpha=0.82, zorder=2)
            ax.hlines([r["lower"], r["upper"]], r["p"] - 0.006, r["p"] + 0.006, color=color, linewidth=2.2, zorder=2)
            ax.scatter(r["p"], r["leading"], marker="x", s=95, linewidth=2.4, color="#111827", zorder=4)
        anchors = [r for r in oracle_rows if r["q"] == q]
        for r in anchors:
            lo, hi = r["interval"]
            ax.errorbar(r["p"], r["mean"], yerr=[[r["mean"] - lo], [hi - r["mean"]]], fmt="o",
                        ms=8.5, capsize=4.5, color=color, markeredgecolor="white", markeredgewidth=1.1,
                        linewidth=2.0, zorder=5)
        if q in (0.5, 0.75):
            ax.axvspan(0.08, 0.48, color="#E5E7EB", alpha=0.55, zorder=0)
            ax.text(0.28, 1.8e-4, "analytic prediction\nunresolved",
                    ha="center", va="bottom", fontsize=13, color="#4B5563", weight="semibold")
        ax.set_title(f"q = {q:.2f}", fontsize=18, weight="bold", color=color, pad=10)
        ax.set_yscale("log")
        ax.set_ylim(4e-6, 0.62)
        ax.set_xlim(0.0, 0.48)
        ax.set_xticks([0.02, 0.08, 0.30, 0.46])
        ax.tick_params(axis="both", labelsize=13)
        ax.grid(True, which="major", color="#CBD5E1", linewidth=0.8, alpha=0.75)
        ax.grid(True, which="minor", axis="y", color="#E2E8F0", linewidth=0.5, alpha=0.55)
        ax.spines[["top", "right"]].set_visible(False)

    for ax in axes[-1, :]:
        ax.set_xlabel("physical error rate p", fontsize=16)
    for ax in axes[:, 0]:
        ax.set_ylabel("Bayes LER (log scale)", fontsize=16)

    legend = [
        Line2D([0], [0], color="#475569", linewidth=6, label="certified analytic interval"),
        Line2D([0], [0], marker="x", linestyle="None", color="#111827", markersize=10,
               markeredgewidth=2.2, label="leading dilute term"),
        Line2D([0], [0], marker="o", linestyle="None", color="#475569", markerfacecolor="#475569",
               markersize=9, label="exact-posterior MC mean (95% bootstrap)"),
        Patch(facecolor="#E5E7EB", edgecolor="none", alpha=0.8, label="fair/intermediate analytic region unresolved"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=2, frameon=False, fontsize=13.5,
               bbox_to_anchor=(0.5, 0.015), columnspacing=2.2, handlelength=2.4)
    fig.suptitle("L=5 square: controlled partition prediction and oracle anchors",
                 fontsize=23, weight="bold", y=0.98)
    fig.text(0.5, 0.94, "No fit or interpolation; deterministic bounds and Monte Carlo uncertainty are not pooled",
             ha="center", fontsize=14.5, color="#475569")
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.13, hspace=0.25, wspace=0.16)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180, facecolor="white")
    plt.close(fig)

    sources = [Path(__file__), MANIFEST, ACTIVITY, ADAPTIVE, ORACLE, SIZE_BIAS]
    out = {
        "status": "complete",
        "scope": "Existing-evidence synthesis for the L=5 square; no sampling, fit, interpolation, threshold or phase claim.",
        "selection": load(MANIFEST)["selection"],
        "certified_bounds": certified_rows,
        "oracle_anchors": sorted(oracle_rows, key=lambda r: (r["q"], r["p"])),
        "checks": checks,
        "conclusions": [
            "The controlled partition prediction is quantitatively certified through p=.05 for every registered q.",
            "At p=.08, promoted B=1024 bounds narrow only q=.97 and q=1; fair q=.5 and intermediate q=.75 retain broad activity certificates.",
            "Existing exact-posterior Monte Carlo anchors describe moderate p but do not supply an analytic continuation between the certified points.",
            "The fair/intermediate analytic curve at p>=.08 remains unresolved; no crossing, threshold, monotonicity, or phase interpretation follows.",
        ],
        "figure": str(FIGURE.relative_to(ROOT)),
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
    }
    RESULT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "checks": checks, "figure": out["figure"]}, indent=2))


if __name__ == "__main__":
    main()
