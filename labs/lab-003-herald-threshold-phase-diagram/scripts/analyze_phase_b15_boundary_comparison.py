#!/usr/bin/env python3
"""Fit peer constrained-neural and constrained-spline B15 summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from scipy.interpolate import PchipInterpolator
from scipy.optimize import minimize


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_BRACKETS = LAB_DIR / "results/phase-b11-honeycomb-three-layer-reanalysis-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b15-neural-spline-comparison-manifest-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b15-neural-spline-comparison-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def sigmoid(value):
    return 1.0 / (1.0 + np.exp(-np.clip(value, -40.0, 40.0)))


def bce_from_logit(logit: np.ndarray, target: np.ndarray) -> np.ndarray:
    return np.logaddexp(0.0, logit) - target * logit


def prepare(evidence: dict, bracket_payload: dict, margin: float) -> dict:
    brackets = [row for row in bracket_payload["lower_boundary_brackets"] if row["width"] is not None]
    q = np.asarray([float(row["q"]) for row in brackets])
    lower = np.asarray([float(row["lower_decodable_p"]) for row in brackets])
    upper = np.asarray([float(row["upper_undecodable_p"]) for row in brackets])
    if len(q) != 16 or not np.all(np.diff(q) > 0):
        raise ValueError("Phase B15 expects sixteen ordered two-sided bracket rows")
    cells = {(float(row["q"]), float(row["p"])): row for row in evidence["cells"]}
    observations = []
    for qi, a, b in zip(q, lower, upper):
        for p in evidence["p_values"]:
            if float(p) < a - margin - 1e-12 or float(p) > b + margin + 1e-12:
                continue
            row = cells[(float(qi), float(p))]
            upward = float(row["posterior_probability_upward_trend"])
            observations.append({
                "q": float(qi), "p": float(p), "target": upward,
                "weight": 0.25 + 0.75 * abs(2.0 * upward - 1.0),
                "sizes": list(map(int, row["sizes"])),
                "logical_errors": list(map(int, row["logical_errors"])),
                "shots": list(map(int, row["shots"])),
            })
    if len(observations) < 60:
        raise ValueError("Phase B15 transition mask unexpectedly sparse")
    return {"q": q, "lower": lower, "upper": upper, "observations": observations}


def bounds_at(data: dict, q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.interp(q, data["q"], data["lower"]), np.interp(q, data["q"], data["upper"])


def spline_curve(data: dict, q_fit: np.ndarray, z: np.ndarray, q_eval: np.ndarray) -> np.ndarray:
    z_eval = PchipInterpolator(q_fit, z, extrapolate=False)(q_eval)
    # Leave-one-row-out removes an endpoint in two folds.  Those folds use a
    # preregistered nearest-endpoint continuation rather than silently dropping
    # q=0 or q=0.75 or allowing unconstrained polynomial extrapolation.
    z_eval = np.where(q_eval < q_fit[0], z[0], z_eval)
    z_eval = np.where(q_eval > q_fit[-1], z[-1], z_eval)
    low, high = bounds_at(data, q_eval)
    return low + (high - low) * sigmoid(z_eval)


def fit_spline(data: dict, *, excluded_q: float | None = None, targets: dict[tuple[float, float], float] | None = None) -> dict:
    q_fit = np.asarray([q for q in data["q"] if excluded_q is None or abs(q - excluded_q) > 1e-12])
    selected = [row for row in data["observations"] if excluded_q is None or abs(row["q"] - excluded_q) > 1e-12]
    q_index = {float(q): index for index, q in enumerate(q_fit)}
    obs_q = np.asarray([row["q"] for row in selected])
    obs_p = np.asarray([row["p"] for row in selected])
    target = np.asarray([(targets or {}).get((row["q"], row["p"]), row["target"]) for row in selected])
    weight = np.asarray([row["weight"] for row in selected])
    tau = 0.025

    def objective(z):
        low, high = bounds_at(data, q_fit)
        knot = low + (high - low) * sigmoid(z)
        boundary = np.asarray([knot[q_index[float(q)]] for q in obs_q])
        data_loss = float(np.mean(weight * bce_from_logit((obs_p - boundary) / tau, target)))
        smooth = float(np.mean(np.diff(knot, 2) ** 2)) if len(knot) > 2 else 0.0
        first = float(np.mean(np.diff(knot) ** 2)) if len(knot) > 1 else 0.0
        return data_loss + 1200.0 * smooth + 2.0 * first

    result = minimize(objective, np.zeros(len(q_fit)), method="L-BFGS-B", options={"maxiter": 800, "ftol": 1e-12})
    if not result.success:
        raise RuntimeError(f"spline optimization failed: {result.message}")
    return {"q_fit": q_fit, "z": result.x, "objective": float(result.fun)}


class TinyBoundary(torch.nn.Module):
    def __init__(self, seed: int):
        super().__init__()
        torch.manual_seed(seed)
        self.hidden_weight = torch.nn.Parameter(0.7 * torch.randn(3, dtype=torch.float64))
        self.hidden_bias = torch.nn.Parameter(0.2 * torch.randn(3, dtype=torch.float64))
        self.output_weight = torch.nn.Parameter(0.4 * torch.randn(3, dtype=torch.float64))
        self.output_bias = torch.nn.Parameter(torch.zeros((), dtype=torch.float64))

    def logits(self, q: torch.Tensor) -> torch.Tensor:
        x = 2.0 * q / 0.75 - 1.0
        hidden = torch.tanh(x[:, None] * self.hidden_weight[None, :] + self.hidden_bias[None, :])
        return hidden @ self.output_weight + self.output_bias


def neural_curve(model: TinyBoundary, data: dict, q_eval: np.ndarray) -> np.ndarray:
    q_tensor = torch.as_tensor(q_eval, dtype=torch.float64)
    low, high = bounds_at(data, q_eval)
    with torch.no_grad():
        fraction = torch.sigmoid(model.logits(q_tensor)).cpu().numpy()
    return low + (high - low) * fraction


def fit_neural(
    data: dict,
    *,
    excluded_q: float | None = None,
    targets: dict[tuple[float, float], float] | None = None,
    starts: int = 8,
    steps: int = 900,
    seed: int = 915000,
) -> dict:
    selected = [row for row in data["observations"] if excluded_q is None or abs(row["q"] - excluded_q) > 1e-12]
    obs_q_np = np.asarray([row["q"] for row in selected])
    obs_p = torch.as_tensor([row["p"] for row in selected], dtype=torch.float64)
    target = torch.as_tensor([(targets or {}).get((row["q"], row["p"]), row["target"]) for row in selected], dtype=torch.float64)
    weight = torch.as_tensor([row["weight"] for row in selected], dtype=torch.float64)
    obs_q = torch.as_tensor(obs_q_np, dtype=torch.float64)
    low_np, high_np = bounds_at(data, obs_q_np)
    low = torch.as_tensor(low_np, dtype=torch.float64)
    high = torch.as_tensor(high_np, dtype=torch.float64)
    grid_np = np.linspace(0.0, 0.75, 151)
    grid_q = torch.as_tensor(grid_np, dtype=torch.float64)
    grid_low_np, grid_high_np = bounds_at(data, grid_np)
    grid_low = torch.as_tensor(grid_low_np, dtype=torch.float64)
    grid_high = torch.as_tensor(grid_high_np, dtype=torch.float64)
    best = None
    for start in range(starts):
        model = TinyBoundary(seed + start)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.025)
        for _ in range(steps):
            optimizer.zero_grad()
            boundary = low + (high - low) * torch.sigmoid(model.logits(obs_q))
            logits = (obs_p - boundary) / 0.025
            data_loss = torch.mean(weight * torch.nn.functional.binary_cross_entropy_with_logits(logits, target, reduction="none"))
            curve = grid_low + (grid_high - grid_low) * torch.sigmoid(model.logits(grid_q))
            first = curve[1:] - curve[:-1]
            second = first[1:] - first[:-1]
            parameter_penalty = sum(torch.sum(parameter * parameter) for parameter in model.parameters())
            loss = data_loss + 1200.0 * torch.mean(second * second) + 2.0 * torch.mean(first * first) + 1e-4 * parameter_penalty
            loss.backward()
            optimizer.step()
        value = float(loss.detach())
        if best is None or value < best[0]:
            best = (value, model)
    assert best is not None
    return {"objective": best[0], "model": best[1]}


def heldout_logloss(data: dict, method: str) -> tuple[float, float, list[dict]]:
    records = []
    for index, heldout in enumerate(data["q"]):
        if method == "spline":
            fit = fit_spline(data, excluded_q=float(heldout))
            boundary = float(spline_curve(data, fit["q_fit"], fit["z"], np.asarray([heldout]))[0])
        else:
            fit = fit_neural(data, excluded_q=float(heldout), starts=4, steps=650, seed=916000 + 20 * index)
            boundary = float(neural_curve(fit["model"], data, np.asarray([heldout]))[0])
        rows = [row for row in data["observations"] if abs(row["q"] - heldout) < 1e-12]
        p = np.asarray([row["p"] for row in rows])
        y = np.asarray([row["target"] for row in rows])
        w = np.asarray([row["weight"] for row in rows])
        loss = float(np.mean(w * bce_from_logit((p - boundary) / 0.025, y)))
        records.append({"q": float(heldout), "boundary": boundary, "weighted_log_loss": loss})
    values = np.asarray([row["weighted_log_loss"] for row in records])
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(len(values))), records


def posterior_targets(data: dict, rng: np.random.Generator) -> dict[tuple[float, float], float]:
    targets = {}
    for row in data["observations"]:
        sizes = np.asarray(row["sizes"], dtype=float)
        centered = sizes - sizes.mean()
        theta = rng.beta(np.asarray(row["logical_errors"]) + 0.5, np.asarray(row["shots"]) - np.asarray(row["logical_errors"]) + 0.5)
        slope = float(theta @ centered / (centered @ centered))
        targets[(row["q"], row["p"])] = 0.99 if slope > 0 else 0.01
    return targets


def curve_metrics(q: np.ndarray, curve: np.ndarray, data: dict) -> dict:
    dq = float(q[1] - q[0])
    first = np.gradient(curve, dq)
    second = np.gradient(first, dq)
    row_curve = np.interp(data["q"], q, curve)
    violations = np.maximum(data["lower"] - row_curve, 0.0) + np.maximum(row_curve - data["upper"], 0.0)
    return {
        "bracket_violation_count": int(np.count_nonzero(violations > 1e-10)),
        "maximum_bracket_violation": float(violations.max()),
        "integrated_squared_curvature": float(np.trapz(second * second, q)),
        "maximum_absolute_slope": float(np.max(np.abs(first))),
        "maximum_absolute_curvature": float(np.max(np.abs(second))),
    }


def analyze(evidence_path: Path, bracket_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if sha256(evidence_path) != manifest["sources"]["current_evidence"]["sha256"]:
        raise ValueError("Phase B15 evidence hash drift")
    if sha256(bracket_path) != manifest["sources"]["brackets"]["sha256"]:
        raise ValueError("Phase B15 bracket hash drift")
    evidence = json.loads(evidence_path.read_text())
    brackets = json.loads(bracket_path.read_text())
    data = prepare(evidence, brackets, float(manifest["transition_margin_p"]))
    q_dense = np.linspace(0.0, 0.75, 151)
    timings = {}
    started = time.perf_counter()
    spline = fit_spline(data)
    spline_curve_full = spline_curve(data, spline["q_fit"], spline["z"], q_dense)
    timings["spline_full_fit_seconds"] = time.perf_counter() - started
    started = time.perf_counter()
    neural = fit_neural(data, starts=manifest["neural"]["full_fit_initializations"], steps=manifest["neural"]["full_fit_steps"])
    neural_curve_full = neural_curve(neural["model"], data, q_dense)
    timings["neural_full_fit_seconds"] = time.perf_counter() - started
    spline_loss, spline_se, spline_folds = heldout_logloss(data, "spline")
    neural_loss, neural_se, neural_folds = heldout_logloss(data, "neural")
    rng = np.random.default_rng(manifest["posterior_propagation"]["seed"])
    spline_draws, neural_draws = [], []
    started = time.perf_counter()
    for replicate in range(manifest["posterior_propagation"]["replicates"]):
        targets = posterior_targets(data, rng)
        sf = fit_spline(data, targets=targets)
        nf = fit_neural(data, targets=targets, starts=2, steps=manifest["neural"]["posterior_fit_steps"], seed=917000 + 5 * replicate)
        spline_draws.append(spline_curve(data, sf["q_fit"], sf["z"], q_dense))
        neural_draws.append(neural_curve(nf["model"], data, q_dense))
    timings["posterior_propagation_seconds"] = time.perf_counter() - started
    spline_draws = np.asarray(spline_draws)
    neural_draws = np.asarray(neural_draws)

    def branch(name, curve, draws, loss, se, folds, fit_seconds):
        low, median, high = np.quantile(draws, [0.05, 0.5, 0.95], axis=0)
        metrics = curve_metrics(q_dense, curve, data)
        metrics.update({
            "heldout_weighted_log_loss": loss,
            "heldout_weighted_log_loss_standard_error": se,
            "mean_posterior_envelope_width": float(np.mean(high - low)),
            "maximum_posterior_envelope_width": float(np.max(high - low)),
            "full_fit_seconds": fit_seconds,
        })
        return {
            "name": name,
            "q": q_dense.tolist(),
            "full_data_curve": curve.tolist(),
            "posterior_median_curve": median.tolist(),
            "posterior_interval90": {"lower": low.tolist(), "upper": high.tolist()},
            "metrics": metrics,
            "leave_one_q_row_out": folds,
        }

    spline_branch = branch("interval_constrained_spline", spline_curve_full, spline_draws, spline_loss, spline_se, spline_folds, timings["spline_full_fit_seconds"])
    neural_branch = branch("width3_constrained_neural", neural_curve_full, neural_draws, neural_loss, neural_se, neural_folds, timings["neural_full_fit_seconds"])
    difference = neural_draws - spline_draws
    diff_low, diff_median, diff_high = np.quantile(difference, [0.05, 0.5, 0.95], axis=0)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_peer_comparison_no_physical_winner",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "sources": {
            "current_evidence": {"path": str(evidence_path), "sha256": sha256(evidence_path)},
            "brackets": {"path": str(bracket_path), "sha256": sha256(bracket_path)},
        },
        "eligible_q_rows": data["q"].tolist(),
        "transition_observation_count": len(data["observations"]),
        "branches": {"spline": spline_branch, "neural": neural_branch},
        "pairwise_difference_neural_minus_spline": {
            "q": q_dense.tolist(), "median": diff_median.tolist(),
            "interval90": {"lower": diff_low.tolist(), "upper": diff_high.tolist()},
            "mean_absolute_full_curve_displacement": float(np.mean(np.abs(neural_curve_full - spline_curve_full))),
            "maximum_absolute_full_curve_displacement": float(np.max(np.abs(neural_curve_full - spline_curve_full))),
        },
        "uncertainty_definition": (
            "Independent Jeffreys-Beta latent-LER posterior draws at each measured cell are projected to slope signs, "
            "then both constrained models are refit. The 90% bands are posterior-propagation/model-fit envelopes, "
            "not thermodynamic-boundary confidence intervals and not seed-cluster bootstrap intervals."
        ),
        "timings": timings,
        "preferred_model": None,
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "phase_classification_performed": False,
        "thermodynamic_boundary_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--brackets", type=Path, default=DEFAULT_BRACKETS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.evidence, args.brackets, args.manifest)
    atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "observations": output["transition_observation_count"], "preferred_model": None}, indent=2))


if __name__ == "__main__":
    main()
