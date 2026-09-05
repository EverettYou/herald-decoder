#!/usr/bin/env python3
"""Render the B16 strongly smoothed full-domain LLR=0 guide."""

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
DEFAULT_ANALYSIS = LAB_DIR / "results/phase-b16-strong-smooth-boundary-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b16-strong-smooth-boundary-manifest-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-b16-strong-smooth-boundary-2026-08-28.png"


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
    q_curve = np.asarray(analysis["display"]["q"])
    low = np.asarray(analysis["display"]["posterior_interval90"]["lower"])
    high = np.asarray(analysis["display"]["posterior_interval90"]["upper"])
    control_p = np.asarray(analysis["model"]["p_control"])
    control_q = np.asarray(analysis["model"]["q_control"])
    limit = float(evidence["display"]["symmetric_limit"])
    cmap = LinearSegmentedColormap.from_list("trend", ["#14866d", "#f7f7f3", "#cf3f45"], N=256)

    figure, axis = plt.subplots(figsize=(9.4, 6.7))
    figure.subplots_adjust(left=0.105, right=0.83, top=0.87, bottom=0.18)
    mesh = axis.pcolormesh(
        midpoint_edges(p_values), midpoint_edges(q_values), matrix,
        cmap=cmap, norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
        edgecolors="#ffffff", linewidth=0.35, shading="flat",
    )
    axis.fill_betweenx(q_curve, low, high, color="#111827", alpha=0.12, linewidth=0)

    vertices = [
        (float(control_p[0]), float(control_q[0])),
        (float(control_p[1]), float(control_q[1])),
        (float(control_p[2]), float(control_q[2])),
        (float(control_p[3]), float(control_q[3])),
    ]
    path = MplPath(vertices, [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
    axis.add_patch(PathPatch(path, facecolor="none", edgecolor="#111827", linewidth=3.2, linestyle=(0, (7, 5))))

    axis.set_xlim(0.06, 0.50)
    axis.set_ylim(0.0, 1.0)
    axis.set_xlabel("Edge error probability p", fontsize=15)
    axis.set_ylabel("Herald probability q", fontsize=15)
    axis.set_title("Honeycomb finite-window trend evidence", fontsize=18, pad=13)
    axis.set_xticks(p_values)
    axis.set_yticks(np.arange(0.0, 1.01, 0.1))
    axis.tick_params(labelsize=11)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.03, fraction=0.06, extend="both")
    colorbar.set_label(
        r"$\log[\Pr(\mathrm{upward}\mid\mathrm{data})/\Pr(\mathrm{downward}\mid\mathrm{data})]$",
        rotation=270, labelpad=26, fontsize=13,
    )
    colorbar.ax.tick_params(labelsize=11)
    figure.text(
        0.47, 0.085,
        "Green: downward LER trend evidence   ·   Red: upward LER trend evidence",
        ha="center", fontsize=11, color="#334155",
    )
    figure.text(
        0.47, 0.045,
        "One four-control cubic Bézier; endpoints fixed to (p,q)=(0.18,0) and (0.5,0.82); light band is 90% posterior propagation",
        ha="center", fontsize=9.5, color="#64748b",
    )
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
        raise ValueError("Phase B16 render evidence hash drift")
    render(evidence, analysis, args.figure)
    audit = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "rendered_and_hash_audited",
        "figure": {"path": str(args.figure), "sha256": sha256(args.figure)},
        "analysis": {"path": str(args.analysis), "sha256": sha256(args.analysis)},
        "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
        "curve_point_count": analysis["display"]["curve_point_count"],
        "free_parameter_count": analysis["model"]["free_parameter_count"],
        "bottom_edge_closed": analysis["diagnostics"]["bottom_edge_closed"],
        "right_edge_closed": analysis["diagnostics"]["right_edge_closed"],
        "new_decoder_runs": 0,
        "new_decodes": 0,
    }
    atomic_json(LAB_DIR / manifest["render_audit_output"], audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
