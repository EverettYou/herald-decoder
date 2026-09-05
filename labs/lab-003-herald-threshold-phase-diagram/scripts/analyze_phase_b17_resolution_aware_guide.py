#!/usr/bin/env python3
"""Build the B17 monotone guide and finite-grid directional bracket region."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_BRACKETS = LAB_DIR / "results/phase-b11-honeycomb-three-layer-reanalysis-2026-08-28.json"
DEFAULT_B16 = LAB_DIR / "results/phase-b16-strong-smooth-boundary-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b17-resolution-aware-guide-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b17-resolution-aware-guide-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def bezier_curve(control_p: np.ndarray, q: np.ndarray, q_end: float) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    control = np.asarray(control_p, dtype=float)
    if control.shape != (4,):
        raise ValueError("exactly four p controls are required")
    if np.any(q < -1e-12) or np.any(q > q_end + 1e-12):
        raise ValueError("q lies outside the guide support")
    u = np.clip(q / q_end, 0.0, 1.0)
    return (
        (1.0 - u) ** 3 * control[0]
        + 3.0 * (1.0 - u) ** 2 * u * control[1]
        + 3.0 * (1.0 - u) * u ** 2 * control[2]
        + u ** 3 * control[3]
    )


def crossing(x0: float, y0: float, x1: float, y1: float, level: float = 0.5) -> float:
    if (y0 - level) * (y1 - level) > 0 or y0 == y1:
        raise ValueError("values do not bracket the requested crossing")
    return float(x0 + (level - y0) * (x1 - x0) / (y1 - y0))


def derive_guide_endpoints(evidence: dict) -> tuple[float, float]:
    q0 = sorted((row for row in evidence["cells"] if abs(float(row["q"])) < 1e-12), key=lambda row: row["p"])
    start_p = None
    for left, right in zip(q0[:-1], q0[1:]):
        y0 = float(left["posterior_probability_upward_trend"])
        y1 = float(right["posterior_probability_upward_trend"])
        if y0 < 0.5 <= y1:
            start_p = crossing(float(left["p"]), y0, float(right["p"]), y1)
            break
    if start_p is None:
        raise ValueError("q=0 row has no lower directional crossing")

    edge = sorted(
        (row for row in evidence["cells"] if abs(float(row["p"]) - 0.49) < 1e-12 and float(row["q"]) >= 0.7),
        key=lambda row: row["q"],
    )
    end_q = None
    for lower, upper in zip(edge[:-1], edge[1:]):
        y0 = float(lower["posterior_probability_upward_trend"])
        y1 = float(upper["posterior_probability_upward_trend"])
        if y0 >= 0.5 > y1:
            end_q = crossing(float(lower["q"]), y0, float(upper["q"]), y1)
            break
    if end_q is None:
        raise ValueError("p=0.49 edge has no high-q directional crossing")
    return start_p, end_q


def build_raw_brackets(evidence: dict, brackets: dict, gate: float) -> list[dict]:
    rows = []
    for row in brackets["lower_boundary_brackets"]:
        if row["width"] is None:
            continue
        rows.append({
            "q": float(row["q"]),
            "lower": float(row["lower_decodable_p"]),
            "upper": float(row["upper_undecodable_p"]),
            "kind": "measured_directional_bracket",
        })

    by_q = {}
    for row in evidence["cells"]:
        by_q.setdefault(float(row["q"]), []).append(row)
    for q in sorted(value for value in by_q if value >= 0.8 - 1e-12):
        candidates = [
            float(row["p"])
            for row in by_q[q]
            if float(row["posterior_probability_upward_trend"]) <= 1.0 - gate + 1e-12
        ]
        if not candidates:
            continue
        lower = max(candidates)
        rows.append({"q": q, "lower": lower, "upper": 0.5, "kind": "right_censored_at_p_edge"})
        p049 = next(row for row in by_q[q] if abs(float(row["p"]) - 0.49) < 1e-12)
        if float(p049["posterior_probability_upward_trend"]) <= 1.0 - gate + 1e-12:
            break
    rows.sort(key=lambda row: row["q"])
    return rows


def containing_monotone_envelope(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q = np.asarray([row["q"] for row in rows], dtype=float)
    raw_lower = np.asarray([row["lower"] for row in rows], dtype=float)
    raw_upper = np.asarray([row["upper"] for row in rows], dtype=float)
    lower = np.minimum.accumulate(raw_lower[::-1])[::-1]
    upper = np.maximum.accumulate(raw_upper)
    if np.any(np.diff(lower) < -1e-12) or np.any(np.diff(upper) < -1e-12):
        raise AssertionError("constructed envelope is not nondecreasing")
    if np.any(lower > raw_lower + 1e-12) or np.any(upper < raw_upper - 1e-12):
        raise AssertionError("constructed envelope does not contain raw brackets")
    return q, lower, upper


def fit_monotone_guide(rows: list[dict], start_p: float, end_q: float) -> dict:
    fit_rows = [row for row in rows if row["q"] <= end_q + 1e-12]
    q = np.asarray([row["q"] for row in fit_rows], dtype=float)
    midpoint = np.asarray([(row["lower"] + row["upper"]) / 2.0 for row in fit_rows], dtype=float)

    def objective(interior: np.ndarray) -> float:
        control = np.asarray([start_p, interior[0], interior[1], 0.5])
        return float(np.mean((bezier_curve(control, q, end_q) - midpoint) ** 2))

    result = minimize(
        objective,
        np.asarray([start_p, start_p], dtype=float),
        method="SLSQP",
        bounds=[(start_p, 0.5), (start_p, 0.5)],
        constraints=[{"type": "ineq", "fun": lambda interior: interior[1] - interior[0]}],
        options={"maxiter": 1200, "ftol": 1e-14},
    )
    if not result.success:
        raise RuntimeError(f"monotone guide optimization failed: {result.message}")
    return {
        "control_p": np.asarray([start_p, result.x[0], result.x[1], 0.5]),
        "objective": float(result.fun),
        "fit_q": q,
        "fit_midpoint": midpoint,
    }


def analyze(evidence_path: Path, bracket_path: Path, b16_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if sha256(evidence_path) != manifest["sources"]["current_evidence"]["sha256"]:
        raise ValueError("B17 evidence hash drift")
    if sha256(bracket_path) != manifest["sources"]["directional_brackets"]["sha256"]:
        raise ValueError("B17 bracket hash drift")
    evidence = json.loads(evidence_path.read_text())
    brackets = json.loads(bracket_path.read_text())
    b16 = json.loads(b16_path.read_text())
    gate = float(manifest["evidence_model"]["directional_gate"])

    start_p, end_q = derive_guide_endpoints(evidence)
    rows = build_raw_brackets(evidence, brackets, gate)
    q_region, lower, upper = containing_monotone_envelope(rows)
    fit = fit_monotone_guide(rows, start_p, end_q)
    q_guide = np.r_[np.arange(0.0, end_q, 0.05), end_q]
    curve = bezier_curve(fit["control_p"], q_guide, end_q)

    old_q = np.asarray(b16["display"]["q"], dtype=float)
    old_low = np.asarray(b16["display"]["posterior_interval90"]["lower"], dtype=float)
    old_high = np.asarray(b16["display"]["posterior_interval90"]["upper"], dtype=float)
    old_mask = old_q <= 0.75 + 1e-12
    new_mask = q_region <= 0.75 + 1e-12
    old_mean_width = float(np.mean(old_high[old_mask] - old_low[old_mask]))
    new_mean_width = float(np.mean(upper[new_mask] - lower[new_mask]))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "resolution_aware_finite_grid_guide_complete",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "sources": {
            "current_evidence": {"path": str(evidence_path), "sha256": sha256(evidence_path)},
            "directional_brackets": {"path": str(bracket_path), "sha256": sha256(bracket_path)},
            "withdrawn_b16_comparator": {"path": str(b16_path), "sha256": sha256(b16_path)},
        },
        "guide": {
            "kind": "monotone cubic Bezier visual guide",
            "q_control": [0.0, end_q / 3.0, 2.0 * end_q / 3.0, end_q],
            "p_control": fit["control_p"].tolist(),
            "derived_endpoints": {"start": [start_p, 0.0], "end": [0.5, end_q]},
            "objective": fit["objective"],
            "free_parameter_count": 2,
            "inferential_interval": False,
            "fit_targets": {"q": fit["fit_q"].tolist(), "bracket_midpoint_p": fit["fit_midpoint"].tolist()},
        },
        "transition_region": {
            "kind": "conservative finite-grid directional bracket and right-censoring region",
            "directional_gate": gate,
            "joint_coverage_claim": False,
            "raw_brackets": rows,
            "q": q_region.tolist(),
            "lower": lower.tolist(),
            "upper": upper.tolist(),
        },
        "display": {"guide_q": q_guide.tolist(), "guide_p": curve.tolist(), "guide_point_count": len(q_guide)},
        "diagnostics": {
            "raw_bracket_count": len(rows),
            "measured_bracket_count": sum(row["kind"] == "measured_directional_bracket" for row in rows),
            "right_censor_bracket_count": sum(row["kind"] == "right_censored_at_p_edge" for row in rows),
            "guide_monotone_nondecreasing_p": bool(np.all(np.diff(curve) >= -1e-12)),
            "low_q_reversal_present": bool(np.any(np.diff(curve[q_guide <= 0.4 + 1e-12]) < -1e-12)),
            "all_raw_brackets_contained": bool(all(l <= row["lower"] + 1e-12 and u >= row["upper"] - 1e-12 for l, u, row in zip(lower, upper, rows))),
            "old_b16_mean_width_through_q075": old_mean_width,
            "b17_mean_width_through_q075": new_mean_width,
            "width_ratio_b17_to_b16": new_mean_width / old_mean_width,
            "method_footer_required": False,
            "curve_legend_required": False,
        },
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "claim_boundary": "The dashed curve is a visual guide; the shaded region is a marginal-gate finite-grid bracket/censoring region, not a confidence set for a thermodynamic phase boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--brackets", type=Path, default=DEFAULT_BRACKETS)
    parser.add_argument("--b16", type=Path, default=DEFAULT_B16)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = analyze(args.evidence, args.brackets, args.b16, args.manifest)
    atomic_json(args.output, payload)
    print(json.dumps({"output": str(args.output), "guide": payload["guide"], "diagnostics": payload["diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
