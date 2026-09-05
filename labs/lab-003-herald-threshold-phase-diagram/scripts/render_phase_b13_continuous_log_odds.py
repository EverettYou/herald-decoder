#!/usr/bin/env python3
"""Merge current honeycomb trend evidence and render a continuous log-odds map.

This renderer deliberately does not turn trend evidence into phase labels.  It
preserves the posterior probabilities and QMC censoring metadata, while the
PNG uses a symmetric display-only clip so a few extreme cells do not collapse
the visible color resolution of the rest of the finite grid.
"""

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
DEFAULT_MANIFEST = LAB_DIR / "phase-b13-honeycomb-continuous-log-odds-map-manifest-2026-08-28.json"
EVIDENCE_FIELDS = (
    "posterior_probability_upward_trend",
    "posterior_probability_downward_trend",
    "posterior_log_odds_upward_vs_downward",
    "posterior_log_odds_censoring",
    "qmc_standard_error_upward_probability",
    "qmc_standard_error_downward_probability",
    "qmc_probability_resolution",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def validate_manifest(manifest: dict) -> None:
    if manifest["status"] not in {"registered", "rendered"}:
        raise ValueError("invalid Phase B13 lifecycle")
    if manifest["new_decoder_runs"] != 0 or manifest["new_decodes"] != 0:
        raise ValueError("Phase B13 must remain evidence-presentation only")
    if manifest["sample_selection"] is not None:
        raise ValueError("Phase B13 may not select samples")
    for source in manifest["sources"]:
        path = LAB_DIR / source["path"]
        if sha256(path) != source["sha256"]:
            raise ValueError(f"Phase B13 source hash drift: {source['role']}")
    renderer = LAB_DIR / manifest["renderer"]["path"]
    if sha256(renderer) != manifest["renderer"]["sha256"]:
        raise ValueError("Phase B13 renderer hash drift")
    semantics = manifest["display_semantics"]
    if semantics["axes"] != {"x": "edge error p", "y": "herald probability q"}:
        raise ValueError("Phase B13 axis contract drift")
    forbidden_true = ("cell_classification", "boundary_inference", "point_markers", "continuous_interpolation")
    if any(semantics[key] is not False for key in forbidden_true):
        raise ValueError("Phase B13 must remain evidence-only")
    if float(semantics["symmetric_display_limit"]) <= 0:
        raise ValueError("display limit must be positive")


def midpoint_edges(values: list[float]) -> list[float]:
    values = sorted(values)
    if len(values) < 2:
        raise ValueError("at least two grid values are required")
    interior = [(a + b) / 2.0 for a, b in zip(values[:-1], values[1:])]
    return [values[0] - (values[1] - values[0]) / 2.0, *interior,
            values[-1] + (values[-1] - values[-2]) / 2.0]


def source_by_role(manifest: dict, role: str) -> dict:
    matches = [row for row in manifest["sources"] if row["role"] == role]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one source role {role}")
    return json.loads((LAB_DIR / matches[0]["path"]).read_text())


def evidence_record(q: float, p: float, row: dict, source: str, display_limit: float) -> dict:
    missing = [field for field in EVIDENCE_FIELDS if field not in row]
    if missing:
        raise ValueError(f"missing evidence fields at {(q, p)}: {missing}")
    upward = float(row["posterior_probability_upward_trend"])
    downward = float(row["posterior_probability_downward_trend"])
    if abs(upward + downward - 1.0) > 1e-9:
        raise ValueError(f"direction probabilities do not sum to one at {(q, p)}")
    censoring = dict(row["posterior_log_odds_censoring"])
    relation = censoring.get("relation")
    if relation not in {"equal", "less_than", "greater_than"}:
        raise ValueError(f"unsupported censoring relation at {(q, p)}: {relation}")
    raw = row["posterior_log_odds_upward_vs_downward"]
    if relation == "equal" and raw is None:
        raise ValueError(f"uncensored log odds missing at {(q, p)}")
    display_source = float(raw) if raw is not None else float(censoring["bound"])
    display_value = max(-display_limit, min(display_limit, display_source))
    return {
        "q": q,
        "p": p,
        "posterior_probability_upward_trend": upward,
        "posterior_probability_downward_trend": downward,
        "posterior_log_odds_upward_vs_downward": raw,
        "posterior_log_odds_censoring": censoring,
        "qmc_standard_error_upward_probability": row["qmc_standard_error_upward_probability"],
        "qmc_standard_error_downward_probability": row["qmc_standard_error_downward_probability"],
        "qmc_probability_resolution": row["qmc_probability_resolution"],
        "display_source_value": display_source,
        "display_log_odds": display_value,
        "display_clipped": display_value != display_source,
        "evidence_source": source,
    }


def merge_evidence(manifest: dict) -> dict:
    base = source_by_role(manifest, "base_grid")
    updates = source_by_role(manifest, "measured_endpoint_updates")
    expected_updates = {(float(row["q"]), float(row["p"])) for row in manifest["expected_update_cells"]}
    update_by_key = {(float(row["q"]), float(row["p"])): row for row in updates["analyses"]}
    if set(update_by_key) != expected_updates or len(update_by_key) != 4:
        raise ValueError("Phase B13 update-key drift")
    limit = float(manifest["display_semantics"]["symmetric_display_limit"])
    cells = []
    seen = set()
    for analysis in base["analyses"]:
        q = float(analysis["q"])
        for row in analysis["cells"]:
            p = float(row["p"])
            key = (q, p)
            if key in seen:
                raise ValueError(f"duplicate base cell {key}")
            seen.add(key)
            source_row = update_by_key.get(key, row)
            source = "phase_b10_measured_endpoint_update" if key in update_by_key else "phase_b9_base_grid"
            cells.append(evidence_record(q, p, source_row, source, limit))
    if len(cells) != 231 or len(seen) != 231:
        raise ValueError("Phase B13 expects exactly 231 unique base-grid cells")
    if not expected_updates.issubset(seen):
        raise ValueError("Phase B13 update cell absent from base grid")
    q_values = sorted({row["q"] for row in cells})
    p_values = sorted({row["p"] for row in cells})
    if len(q_values) != 21 or len(p_values) != 11:
        raise ValueError("Phase B13 expects a 21x11 honeycomb grid")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "current_finite_window_trend_evidence",
        "quantity": manifest["display_semantics"]["quantity"],
        "axes": manifest["display_semantics"]["axes"],
        "display": {
            "symmetric_limit": limit,
            "clipping_applies_only_to_display": True,
            "clipped_cell_count": sum(row["display_clipped"] for row in cells),
        },
        "provenance": {
            "base_cell_count": 227,
            "updated_cell_count": 4,
            "new_decoder_runs": 0,
            "new_decodes": 0,
            "sample_selection": None,
        },
        "q_values": q_values,
        "p_values": p_values,
        "cells": cells,
        "interpretation_policy": "Evidence values only; no cell classification or boundary inference.",
    }


def render(payload: dict, destination: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

    q_values, p_values = payload["q_values"], payload["p_values"]
    by_key = {(row["q"], row["p"]): row for row in payload["cells"]}
    matrix = np.array([[by_key[(q, p)]["display_log_odds"] for p in p_values] for q in q_values])
    limit = float(payload["display"]["symmetric_limit"])
    cmap = LinearSegmentedColormap.from_list(
        "downward_neutral_upward", ["#14866d", "#f7f7f3", "#cf3f45"], N=256
    )
    # A compact canvas makes the scientific labels comfortably readable at the
    # report's normal display size, rather than relying on a very large image.
    figure, axis = plt.subplots(figsize=(9.2, 6.5))
    figure.subplots_adjust(left=0.115, right=0.84, top=0.87, bottom=0.19)
    mesh = axis.pcolormesh(
        midpoint_edges(p_values), midpoint_edges(q_values), matrix,
        cmap=cmap, norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
        edgecolors="#ffffff", linewidth=0.35, shading="flat",
    )
    axis.set_xlabel("Edge error probability p", fontsize=15)
    axis.set_ylabel("Herald probability q", fontsize=15)
    axis.set_title("Honeycomb finite-window LER trend evidence", fontsize=18, pad=13)
    axis.set_xticks(p_values)
    axis.set_yticks(q_values[::2])
    axis.tick_params(labelsize=12)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.03, fraction=0.06, extend="both")
    colorbar.set_label(
        r"$\log\!\left[\Pr(\mathrm{upward}\mid\mathrm{data}) / "
        r"\Pr(\mathrm{downward}\mid\mathrm{data})\right]$",
        rotation=270, labelpad=25, fontsize=14,
    )
    colorbar.ax.tick_params(labelsize=11)
    figure.text(
        0.48, 0.065,
        "Green: evidence favors downward LER trend   ·   Red: evidence favors upward LER trend",
        ha="center", va="center", fontsize=11.5, color="#334155",
    )
    figure.text(
        0.48, 0.035,
        f"Finite 21×11 grid · display clipped at ±{limit:g} · full values in companion JSON",
        ha="center", va="center", fontsize=9.5, color="#64748b",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=220)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate_manifest(manifest)
    payload = merge_evidence(manifest)
    machine_output = LAB_DIR / manifest["machine_output"]
    atomic_json(machine_output, payload)
    destination = LAB_DIR / manifest["render_output"]
    render(payload, destination)
    audit = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "rendered_evidence_only",
        "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
        "machine_output": {"path": manifest["machine_output"], "sha256": sha256(machine_output)},
        "figure": {"path": manifest["render_output"], "sha256": sha256(destination)},
        "cell_count": len(payload["cells"]),
        "base_cell_count": payload["provenance"]["base_cell_count"],
        "updated_cell_count": payload["provenance"]["updated_cell_count"],
        "clipped_cell_count": payload["display"]["clipped_cell_count"],
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "sample_selection": None,
        "cell_classification": False,
        "boundary_inference": False,
    }
    atomic_json(LAB_DIR / manifest["render_audit_output"], audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
