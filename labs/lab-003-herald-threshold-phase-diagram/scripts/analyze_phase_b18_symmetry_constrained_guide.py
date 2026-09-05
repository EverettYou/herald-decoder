#!/usr/bin/env python3
"""Build the B18 p<->1-p symmetry-constrained finite-window guide."""

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
DEFAULT_B17 = LAB_DIR / "results/phase-b17-resolution-aware-guide-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b18-symmetry-constrained-guide-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b18-symmetry-constrained-guide-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def bezier(control: np.ndarray, u: np.ndarray) -> np.ndarray:
    control = np.asarray(control, dtype=float)
    u = np.asarray(u, dtype=float)
    if control.shape != (4,):
        raise ValueError("exactly four controls are required")
    return (
        (1.0 - u) ** 3 * control[0]
        + 3.0 * (1.0 - u) ** 2 * u * control[1]
        + 3.0 * (1.0 - u) * u ** 2 * control[2]
        + u ** 3 * control[3]
    )


def fit_symmetry_constrained_guide(b17: dict) -> dict:
    start_p = float(b17["guide"]["derived_endpoints"]["start"][0])
    end_q = float(b17["guide"]["derived_endpoints"]["end"][1])
    target_q = np.asarray(b17["guide"]["fit_targets"]["q"], dtype=float)
    target_p = np.asarray(b17["guide"]["fit_targets"]["bracket_midpoint_p"], dtype=float)
    control_q = np.asarray([0.0, end_q / 3.0, end_q, end_q], dtype=float)
    dense_u = np.linspace(0.0, 1.0, 10001)
    dense_q = bezier(control_q, dense_u)

    def objective(interior: np.ndarray) -> float:
        control_p = np.asarray([start_p, interior[0], interior[1], 0.5], dtype=float)
        dense_p = bezier(control_p, dense_u)
        predicted_p = np.interp(target_q, dense_q, dense_p)
        return float(np.mean((predicted_p - target_p) ** 2))

    result = minimize(
        objective,
        np.asarray([start_p, 0.35], dtype=float),
        method="SLSQP",
        bounds=[(start_p, 0.495), (start_p, 0.495)],
        constraints=[{"type": "ineq", "fun": lambda interior: interior[1] - interior[0]}],
        options={"maxiter": 1200, "ftol": 1e-14},
    )
    if not result.success:
        raise RuntimeError(f"B18 symmetry-constrained optimization failed: {result.message}")
    control_p = np.asarray([start_p, result.x[0], result.x[1], 0.5], dtype=float)
    if not control_p[2] < control_p[3]:
        raise AssertionError("the endpoint derivative requires distinct final p controls")
    return {
        "control_p": control_p,
        "control_q": control_q,
        "objective": float(result.fun),
        "target_p": target_p,
        "target_q": target_q,
    }


def analyze(evidence_path: Path, b17_path: Path, manifest_path: Path) -> dict:
    evidence = json.loads(evidence_path.read_text())
    b17 = json.loads(b17_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if sha256(evidence_path) != manifest["sources"]["current_evidence"]["sha256"]:
        raise ValueError("B18 evidence hash drift")
    if sha256(b17_path) != manifest["sources"]["b17_analysis"]["sha256"]:
        raise ValueError("B18 B17-source hash drift")
    expected_p = [0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.45, 0.49]
    if evidence["p_values"] != expected_p:
        raise ValueError("B18 measured p grid drift")

    fit = fit_symmetry_constrained_guide(b17)
    display_u = np.linspace(0.0, 1.0, 31)
    display_p = bezier(fit["control_p"], display_u)
    display_q = bezier(fit["control_q"], display_u)
    analytic_endpoint_slope = float(
        (fit["control_q"][3] - fit["control_q"][2])
        / (fit["control_p"][3] - fit["control_p"][2])
    )
    sampled_endpoint_slope = float((display_q[-1] - display_q[-2]) / (display_p[-1] - display_p[-2]))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "symmetry_constrained_existing_data_guide_complete",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "sources": {
            "current_evidence": {"path": str(evidence_path), "sha256": sha256(evidence_path)},
            "b17_analysis": {"path": str(b17_path), "sha256": sha256(b17_path)},
        },
        "symmetry": {
            "statement": "q_c(p)=q_c(1-p)",
            "fundamental_p_domain": [0.0, 0.5],
            "endpoint_derivative": "dq_c/dp at p=0.5",
            "required_value": 0.0,
        },
        "guide": {
            "kind": "p<->1-p symmetry-constrained parametric cubic Bezier visual guide",
            "p_control": fit["control_p"].tolist(),
            "q_control": fit["control_q"].tolist(),
            "derived_endpoints": b17["guide"]["derived_endpoints"],
            "objective": fit["objective"],
            "free_parameter_count": 2,
            "inferential_interval": False,
            "fit_targets": {"q": fit["target_q"].tolist(), "bracket_midpoint_p": fit["target_p"].tolist()},
        },
        "transition_region": b17["transition_region"],
        "display": {
            "axis_p": [0.0, 0.5],
            "axis_q": [0.0, 1.0],
            "measured_p_centers": expected_p,
            "measured_p_cell_support": [0.06, 0.5],
            "unsampled_p_intervals": [[0.0, 0.06]],
            "guide_u": display_u.tolist(),
            "guide_p": display_p.tolist(),
            "guide_q": display_q.tolist(),
        },
        "diagnostics": {
            "analytic_endpoint_dq_dp": analytic_endpoint_slope,
            "sampled_terminal_secant_dq_dp": sampled_endpoint_slope,
            "guide_p_nondecreasing": bool(np.all(np.diff(display_p) >= -1e-12)),
            "guide_q_nondecreasing": bool(np.all(np.diff(display_q) >= -1e-12)),
            "low_q_reversal_present": bool(np.any(np.diff(display_p[display_q <= 0.4 + 1e-12]) < -1e-12)),
            "transition_region_unchanged_from_b17": True,
            "evidence_cell_count": len(evidence["cells"]),
            "added_evidence_cell_count": 0,
            "curve_legend_required": False,
            "method_footer_required": False,
        },
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "claim_boundary": "The curve is a symmetry-constrained visual guide. The unchanged shaded object is finite-grid directional bracket/censoring evidence, not a confidence set for a thermodynamic phase boundary.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--b17", type=Path, default=DEFAULT_B17)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = analyze(args.evidence, args.b17, args.manifest)
    atomic_json(args.output, payload)
    print(json.dumps({"output": str(args.output), "guide": payload["guide"], "diagnostics": payload["diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
