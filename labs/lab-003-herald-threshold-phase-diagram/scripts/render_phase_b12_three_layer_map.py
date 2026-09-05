#!/usr/bin/env python3
"""Render the Phase B12 honeycomb map from frozen Phase B11 evidence only."""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b12-honeycomb-three-layer-map-manifest-2026-08-28.json"
LAYER_ORDER = ["decodable", "boundary", "undecodable", "unclassified"]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def validate_manifest(manifest: dict) -> None:
    if manifest["status"] not in {"registered", "preflight_passed", "rendered"}:
        raise ValueError("invalid Phase B12 lifecycle")
    if manifest["new_decoder_runs"] != 0 or manifest["new_decodes"] != 0:
        raise ValueError("Phase B12 must remain presentation-only")
    if manifest["sample_selection"] is not None:
        raise ValueError("Phase B12 may not select samples")
    source = LAB_DIR / manifest["source_analysis"]["path"]
    if sha256(source) != manifest["source_analysis"]["sha256"]:
        raise ValueError("Phase B12 source-analysis hash drift")
    renderer = LAB_DIR / manifest["renderer"]["path"]
    if sha256(renderer) != manifest["renderer"]["sha256"]:
        raise ValueError("Phase B12 renderer hash drift")
    semantics = manifest["display_semantics"]
    if semantics["axes"] != {"x": "edge error p", "y": "herald probability q"}:
        raise ValueError("Phase B12 axis contract drift")
    if semantics["crossing_markers"] is not False or semantics["continuous_interpolation"] is not False:
        raise ValueError("Phase B12 forbids crossing markers and interpolation")


def midpoint_edges(values: list[float]) -> list[float]:
    values = sorted(values)
    if len(values) < 2:
        raise ValueError("at least two grid values are required")
    interior = [(a + b) / 2.0 for a, b in zip(values[:-1], values[1:])]
    return [values[0] - (values[1] - values[0]) / 2.0, *interior,
            values[-1] + (values[-1] - values[-2]) / 2.0]


def classify(source: dict) -> dict:
    anchors = {(float(row["q"]), float(row["p"])): row["anchor"] for row in source["anchors"]}
    brackets = {float(row["q"]): row for row in source["lower_boundary_brackets"]}
    q_values = sorted(brackets)
    p_values = sorted({p for _, p in anchors})
    if len(q_values) != 21 or len(p_values) != 11 or len(anchors) != 231:
        raise ValueError("Phase B12 expects the frozen 21x11 honeycomb grid")
    cells = []
    for q in q_values:
        bracket = brackets[q]
        lower = bracket["lower_decodable_p"]
        upper = bracket["upper_undecodable_p"]
        if (lower is None) != (upper is None):
            raise ValueError(f"one-sided Phase B12 bracket at q={q}")
        for p in p_values:
            anchor = anchors[(q, p)]
            if lower is not None:
                if anchor == "decodable" and p >= float(upper):
                    raise ValueError(f"decodable anchor conflicts with bracket at {(q, p)}")
                if anchor == "undecodable" and p <= float(lower):
                    raise ValueError(f"undecodable anchor conflicts with bracket at {(q, p)}")
                layer = "decodable" if p <= float(lower) else "undecodable" if p >= float(upper) else "boundary"
            else:
                layer = anchor if anchor is not None else "unclassified"
            cells.append({"q": q, "p": p, "layer": layer, "absolute_anchor": anchor})
    counts = {layer: sum(row["layer"] == layer for row in cells) for layer in LAYER_ORDER}
    anchor_counts = {
        "decodable": sum(row["absolute_anchor"] == "decodable" for row in cells),
        "undecodable": sum(row["absolute_anchor"] == "undecodable" for row in cells),
    }
    return {"q_values": q_values, "p_values": p_values, "cells": cells,
            "display_counts": counts, "absolute_anchor_counts": anchor_counts}


def render(payload: dict, destination: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch, Rectangle

    q_values, p_values = payload["q_values"], payload["p_values"]
    code = {name: index for index, name in enumerate(LAYER_ORDER)}
    matrix = np.empty((len(q_values), len(p_values)), dtype=int)
    by_key = {(row["q"], row["p"]): row for row in payload["cells"]}
    for j, q in enumerate(q_values):
        for i, p in enumerate(p_values):
            matrix[j, i] = code[by_key[(q, p)]["layer"]]

    colors = ["#3aa76d", "#f2c14e", "#d85b5b", "#e5e7eb"]
    figure, axis = plt.subplots(figsize=(11.2, 7.4))
    figure.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.17)
    axis.pcolormesh(midpoint_edges(p_values), midpoint_edges(q_values), matrix,
                    cmap=ListedColormap(colors), vmin=-0.5, vmax=3.5,
                    edgecolors="white", linewidth=0.35, shading="flat")

    q_edges, p_edges = midpoint_edges(q_values), midpoint_edges(p_values)
    for row in payload["cells"]:
        if row["absolute_anchor"] is None:
            continue
        j, i = q_values.index(row["q"]), p_values.index(row["p"])
        axis.add_patch(Rectangle((p_edges[i], q_edges[j]), p_edges[i + 1] - p_edges[i],
                                 q_edges[j + 1] - q_edges[j], fill=False,
                                 edgecolor="#17324d", linewidth=0.8))

    axis.set_xlim(p_edges[0], p_edges[-1])
    axis.set_ylim(q_edges[0], q_edges[-1])
    axis.set_xlabel("Edge error probability p")
    axis.set_ylabel("Herald probability q")
    axis.set_title("Honeycomb operational phase map — absolute anchors and lower-boundary uncertainty")
    axis.set_xticks(p_values)
    axis.set_yticks(q_values[::2])
    axis.grid(False)
    legend = [Patch(facecolor=colors[0], label="Decodable side"),
              Patch(facecolor=colors[1], label="Discrete boundary bracket"),
              Patch(facecolor=colors[2], label="Undecodable side"),
              Patch(facecolor=colors[3], label="No two-sided bracket"),
              Patch(facecolor="none", edgecolor="#17324d", label="Posterior-stable absolute-LER anchor")]
    axis.legend(handles=legend, loc="upper left", frameon=True, ncol=2)
    figure.text(0.5, 0.035,
                "Finite 21x11 grid; no crossing markers, continuous interpolation, asymptotic threshold, or thermodynamic phase claim.",
                ha="center", va="bottom", fontsize=9, color="#475569")
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate_manifest(manifest)
    source = json.loads((LAB_DIR / manifest["source_analysis"]["path"]).read_text())
    payload = classify(source)
    if args.preflight:
        output = LAB_DIR / manifest["preflight_output"]
        preflight = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "preflight_passed_not_rendered",
            "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
            "source_hash_valid": True,
            "display_counts": payload["display_counts"],
            "absolute_anchor_counts": payload["absolute_anchor_counts"],
            "new_decoder_runs": 0,
            "new_decodes": 0,
            "sample_selection": None,
            "figure_rendered": False,
        }
        atomic_json(output, preflight)
        print(json.dumps(preflight, indent=2))
        return
    destination = LAB_DIR / manifest["render_output"]
    render(payload, destination)
    audit = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "rendered_presentation_only",
        "figure": {"path": manifest["render_output"], "sha256": sha256(destination)},
        "display_counts": payload["display_counts"],
        "absolute_anchor_counts": payload["absolute_anchor_counts"],
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "sample_selection": None,
    }
    atomic_json(LAB_DIR / manifest["render_audit_output"], audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
