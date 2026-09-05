#!/usr/bin/env python3
"""Render the B18 p<->1-p symmetry-constrained finite-window guide."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_ANALYSIS = LAB_DIR / "results/phase-b18-symmetry-constrained-guide-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b18-symmetry-constrained-guide-manifest-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b18-symmetry-constrained-guide-2026-08-28.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def midpoint_edges(values: list[float]) -> list[float]:
    interior = [(a + b) / 2.0 for a, b in zip(values[:-1], values[1:])]
    return [values[0] - (values[1] - values[0]) / 2.0, *interior, values[-1] + (values[-1] - values[-2]) / 2.0]


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def render(evidence: dict, analysis: dict, destination: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch

    q_values, p_values = evidence["q_values"], evidence["p_values"]
    by_key = {(row["q"], row["p"]): row for row in evidence["cells"]}
    matrix = np.asarray([[by_key[(q, p)]["display_log_odds"] for p in p_values] for q in q_values])
    region_q = np.asarray(analysis["transition_region"]["q"])
    lower = np.asarray(analysis["transition_region"]["lower"])
    upper = np.asarray(analysis["transition_region"]["upper"])
    control_p = np.asarray(analysis["guide"]["p_control"])
    control_q = np.asarray(analysis["guide"]["q_control"])
    limit = float(evidence["display"]["symmetric_limit"])
    cmap = LinearSegmentedColormap.from_list("trend", ["#14866d", "#f7f7f3", "#cf3f45"], N=256)

    figure, axis = plt.subplots(figsize=(8.7, 6.2))
    figure.subplots_adjust(left=0.105, right=0.825, top=0.87, bottom=0.13)
    mesh = axis.pcolormesh(
        midpoint_edges(p_values), midpoint_edges(q_values), matrix,
        cmap=cmap, norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
        edgecolors="#ffffff", linewidth=0.35, shading="flat",
    )
    axis.fill_betweenx(region_q, lower, upper, color="#111827", alpha=0.15, linewidth=0)

    vertices = [(float(p), float(q)) for p, q in zip(control_p, control_q)]
    path = MplPath(vertices, [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
    axis.add_patch(PathPatch(path, facecolor="none", edgecolor="#111827", linewidth=3.2, linestyle=(0, (7, 5))))

    axis.set_xlim(0.0, 0.5)
    axis.set_ylim(0.0, 1.0)
    axis.set_xlabel("Edge error probability p", fontsize=16)
    axis.set_ylabel("Herald probability q", fontsize=16)
    axis.set_title("Honeycomb finite-window trend evidence", fontsize=19, pad=13)
    axis.set_xticks(np.arange(0.0, 0.51, 0.1))
    axis.set_yticks(np.arange(0.0, 1.01, 0.1))
    axis.tick_params(labelsize=12)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.03, fraction=0.06, extend="both")
    colorbar.set_label(
        r"$\log[\Pr(\mathrm{upward}\mid\mathrm{data})/\Pr(\mathrm{downward}\mid\mathrm{data})]$",
        rotation=270, labelpad=27, fontsize=14,
    )
    colorbar.ax.tick_params(labelsize=12)

    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text())
    analysis = json.loads(args.analysis.read_text())
    manifest = json.loads(args.manifest.read_text())
    if analysis["sources"]["current_evidence"]["sha256"] != sha256(args.evidence):
        raise ValueError("B18 render evidence hash drift")
    if analysis["manifest"]["sha256"] != sha256(args.manifest):
        raise ValueError("B18 render manifest hash drift")
    render(evidence, analysis, args.figure)
    audit = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "rendered_and_hash_audited",
        "figure": {"path": str(args.figure), "sha256": sha256(args.figure)},
        "analysis": {"path": str(args.analysis), "sha256": sha256(args.analysis)},
        "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
        "axis_p": analysis["display"]["axis_p"],
        "axis_q": analysis["display"]["axis_q"],
        "analytic_endpoint_dq_dp": analysis["diagnostics"]["analytic_endpoint_dq_dp"],
        "guide_p_nondecreasing": analysis["diagnostics"]["guide_p_nondecreasing"],
        "guide_q_nondecreasing": analysis["diagnostics"]["guide_q_nondecreasing"],
        "added_evidence_cell_count": analysis["diagnostics"]["added_evidence_cell_count"],
        "curve_legend_present": False,
        "method_footer_present": False,
        "new_decoder_runs": 0,
        "new_decodes": 0,
    }
    atomic_json(LAB_DIR / manifest["render_audit_output"], audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
