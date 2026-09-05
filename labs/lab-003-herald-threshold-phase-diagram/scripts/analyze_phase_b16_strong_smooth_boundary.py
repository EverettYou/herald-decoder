#!/usr/bin/env python3
"""Fit one globally smooth cubic-Bezier finite-window LLR=0 guide."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_BRACKETS = LAB_DIR / "results/phase-b11-honeycomb-three-layer-reanalysis-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b16-strong-smooth-boundary-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b16-strong-smooth-boundary-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def bce_from_logit(logit: np.ndarray, target: np.ndarray) -> np.ndarray:
    return np.logaddexp(0.0, logit) - target * logit


def bezier_curve(control_p: np.ndarray, q: np.ndarray, q_critical: float = 1.0) -> np.ndarray:
    """Cubic Bezier p(q) on 0 <= q <= q_critical."""
    q = np.asarray(q, dtype=float)
    c = np.asarray(control_p, dtype=float)
    if c.shape != (4,):
        raise ValueError("exactly four p control values are required")
    if np.any(q < -1e-12) or np.any(q > q_critical + 1e-12):
        raise ValueError("q lies outside the Bezier support")
    u = np.clip(q / q_critical, 0.0, 1.0)
    return (
        (1.0 - u) ** 3 * c[0]
        + 3.0 * (1.0 - u) ** 2 * u * c[1]
        + 3.0 * (1.0 - u) * u ** 2 * c[2]
        + u ** 3 * c[3]
    )


def prepare(evidence: dict, brackets: dict, transition_margin: float, high_q_min_p: float) -> dict:
    bracket_rows = {
        float(row["q"]): row
        for row in brackets["lower_boundary_brackets"]
        if row["width"] is not None
    }
    if len(bracket_rows) != 16:
        raise ValueError("Phase B16 expects sixteen audited lower-boundary brackets")
    observations = []
    for row in evidence["cells"]:
        q, p = float(row["q"]), float(row["p"])
        bracket = bracket_rows.get(q)
        if bracket is not None:
            lower = float(bracket["lower_decodable_p"])
            upper = float(bracket["upper_undecodable_p"])
            include = lower - transition_margin - 1e-12 <= p <= upper + transition_margin + 1e-12
            region = "audited_lower_transition"
        else:
            include = p >= high_q_min_p - 1e-12
            region = "high_q_right_edge_closure"
        if not include:
            continue
        upward = float(row["posterior_probability_upward_trend"])
        observations.append({
            "q": q,
            "p": p,
            "target": upward,
            "weight": 0.20 + 0.80 * abs(2.0 * upward - 1.0),
            "region": region,
            "sizes": list(map(int, row["sizes"])),
            "logical_errors": list(map(int, row["logical_errors"])),
            "shots": list(map(int, row["shots"])),
        })
    return {
        "observations": observations,
        "bracket_q": np.asarray(sorted(bracket_rows)),
        "lower": np.asarray([float(bracket_rows[q]["lower_decodable_p"]) for q in sorted(bracket_rows)]),
        "upper": np.asarray([float(bracket_rows[q]["upper_undecodable_p"]) for q in sorted(bracket_rows)]),
    }


def row_roots(data: dict, targets: dict[tuple[float, float], float] | None = None, q_max: float = 0.82) -> tuple[np.ndarray, np.ndarray]:
    """Return the first low-p downward-to-upward transition on each q row."""
    grouped: dict[float, list[tuple[float, float]]] = {}
    for row in data["observations"]:
        if row["q"] > q_max + 1e-12:
            continue
        value = (targets or {}).get((row["q"], row["p"]), row["target"])
        grouped.setdefault(row["q"], []).append((row["p"], float(value)))
    roots = []
    for q, values in sorted(grouped.items()):
        values.sort()
        for (p0, y0), (p1, y1) in zip(values[:-1], values[1:]):
            if y0 < 0.5 <= y1:
                fraction = (0.5 - y0) / max(y1 - y0, 1e-12)
                roots.append((q, p0 + fraction * (p1 - p0)))
                break
    if len(roots) < 12:
        raise ValueError("too few valid lower-transition roots")
    return np.asarray([row[0] for row in roots]), np.asarray([row[1] for row in roots])


def fit_curve(data: dict, manifest: dict, targets: dict[tuple[float, float], float] | None = None) -> dict:
    q_critical = float(manifest["fit"]["critical_q"])
    start_p = float(manifest["fit"]["fixed_start_p"])
    q_root, p_root = row_roots(data, targets, q_critical)
    bracket_weight = float(manifest["fit"]["bracket_penalty"])
    control_weight = float(manifest["fit"]["control_regularization"])

    def objective(interior: np.ndarray) -> float:
        control = np.asarray([start_p, interior[0], interior[1], 0.5])
        boundary = bezier_curve(control, q_root, q_critical)
        root_loss = float(np.mean((boundary - p_root) ** 2))
        bracket_q = data["bracket_q"][data["bracket_q"] <= q_critical + 1e-12]
        row_boundary = bezier_curve(control, bracket_q, q_critical)
        count = len(bracket_q)
        width = data["upper"] - data["lower"]
        violation = np.maximum(data["lower"][:count] - row_boundary, 0.0) + np.maximum(row_boundary - data["upper"][:count], 0.0)
        bracket_loss = float(np.mean((violation / width[:count]) ** 2))
        regularization = float(np.sum((interior - np.asarray([0.25, 0.05])) ** 2))
        return root_loss + bracket_weight * bracket_loss + control_weight * regularization

    result = minimize(
        objective,
        np.asarray(manifest["fit"]["initial_control_p"][1:3], dtype=float),
        method="L-BFGS-B",
        bounds=[(0.0, 0.35), (0.0, 0.35)],
        options={"maxiter": 1200, "ftol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"Bezier optimization failed: {result.message}")
    control = np.asarray([start_p, result.x[0], result.x[1], 0.5])
    return {"control_p": control, "objective": float(result.fun), "root_q": q_root, "root_p": p_root}


def posterior_targets(data: dict, rng: np.random.Generator) -> dict[tuple[float, float], float]:
    targets = {}
    for row in data["observations"]:
        sizes = np.asarray(row["sizes"], dtype=float)
        errors = np.asarray(row["logical_errors"], dtype=float)
        shots = np.asarray(row["shots"], dtype=float)
        centered = sizes - sizes.mean()
        theta = rng.beta(errors + 0.5, shots - errors + 0.5)
        slope = float(theta @ centered / (centered @ centered))
        targets[(row["q"], row["p"])] = 0.99 if slope > 0 else 0.01
    return targets


def analyze(evidence_path: Path, bracket_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if sha256(evidence_path) != manifest["sources"]["current_evidence"]["sha256"]:
        raise ValueError("Phase B16 evidence hash drift")
    if sha256(bracket_path) != manifest["sources"]["brackets"]["sha256"]:
        raise ValueError("Phase B16 bracket hash drift")
    evidence = json.loads(evidence_path.read_text())
    brackets = json.loads(bracket_path.read_text())
    data = prepare(
        evidence,
        brackets,
        float(manifest["fit"]["transition_margin_p"]),
        float(manifest["fit"]["high_q_min_p"]),
    )
    fit = fit_curve(data, manifest)
    q_critical = float(manifest["fit"]["critical_q"])
    regular_q = np.arange(0.0, q_critical, 0.05)
    q_display = np.r_[regular_q, q_critical]
    curve = bezier_curve(fit["control_p"], q_display, q_critical)
    rng = np.random.default_rng(int(manifest["posterior_propagation"]["seed"]))
    draws = []
    for _ in range(int(manifest["posterior_propagation"]["replicates"])):
        draw_fit = fit_curve(data, manifest, posterior_targets(data, rng))
        draws.append(bezier_curve(draw_fit["control_p"], q_display, q_critical))
    draws = np.asarray(draws)
    low, median, high = np.quantile(draws, [0.05, 0.5, 0.95], axis=0)
    curvature = np.gradient(np.gradient(curve, q_display), q_display)
    regions = {}
    for row in data["observations"]:
        regions[row["region"]] = regions.get(row["region"], 0) + 1
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "strongly_smoothed_finite_window_guide",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "sources": {
            "current_evidence": {"path": str(evidence_path), "sha256": sha256(evidence_path)},
            "brackets": {"path": str(bracket_path), "sha256": sha256(bracket_path)},
        },
        "model": {
            "kind": "single cubic Bezier graph p(q)",
            "q_control": [0.0, q_critical / 3.0, 2.0 * q_critical / 3.0, q_critical],
            "p_control": fit["control_p"].tolist(),
            "endpoint_constraints": {"start_p": 0.18, "start_q": 0.0, "end_p": 0.5, "critical_q": q_critical},
            "objective": fit["objective"],
            "free_parameter_count": 2,
            "row_root_targets": {"q": fit["root_q"].tolist(), "p": fit["root_p"].tolist()},
        },
        "display": {
            "q": q_display.tolist(),
            "curve": curve.tolist(),
            "posterior_median": median.tolist(),
            "posterior_interval90": {"lower": low.tolist(), "upper": high.tolist()},
            "curve_point_count": len(q_display),
        },
        "diagnostics": {
            "observation_count": len(data["observations"]),
            "observation_regions": regions,
            "maximum_absolute_curvature": float(np.max(np.abs(curvature))),
            "minimum_control_q_spacing": q_critical / 3.0,
            "p_grid_nominal_spacing": 0.05,
            "sub_grid_features_possible": False,
            "bottom_edge_closed": bool(abs(q_display[0]) < 1e-12),
            "right_edge_closed": bool(abs(curve[-1] - 0.5) < 1e-12 and abs(q_display[-1] - q_critical) < 1e-12),
        },
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "claim_boundary": "Regularized finite-window LLR=0 visual guide only; not an asymptotic or thermodynamic phase boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--brackets", type=Path, default=DEFAULT_BRACKETS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = analyze(args.evidence, args.brackets, args.manifest)
    atomic_json(args.output, payload)
    print(json.dumps({"output": str(args.output), "model": payload["model"], "diagnostics": payload["diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
