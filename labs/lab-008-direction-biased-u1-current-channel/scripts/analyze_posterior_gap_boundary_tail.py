#!/usr/bin/env python3
"""Analyze the preregistered 3x3 posterior-gap boundary matrix."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
MANIFEST = LAB / "manifests" / "posterior-gap-boundary-tail-acquisition-2026-09-21.json"
SYNTHESIS = LAB / "results" / "posterior-gap-order-parameter-synthesis-2026-09-21.json"
PROGRESS = LAB / "results" / "posterior-gap-boundary-tail-acquisition-progress-2026-09-21.json"
OUTPUT = LAB / "results" / "posterior-gap-boundary-tail-analysis-2026-09-21.json"
FIGURE = LAB / "figures" / "posterior-gap-boundary-tail-matrix.png"
THRESHOLDS = (0.5, 1.0, 2.0, 4.0)
REPLICATES = 4000
BASE_SEED = 2026092194


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gap(record: dict) -> float:
    return math.inf if record["gap_infinite_sign"] else abs(float(record["signed_gap"]))


def quantile(values: np.ndarray, probability: float) -> float:
    ordered = np.sort(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    if math.isinf(float(ordered[upper])):
        return math.inf
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def record_arrays(records: list[dict]) -> dict[str, np.ndarray]:
    risks = np.asarray([float(row["bayes_risk"]) for row in records], dtype=float)
    gaps = np.asarray([gap(row) for row in records], dtype=float)
    entropies = []
    for row in records:
        if "conditional_logical_entropy_bits" in row:
            entropies.append(float(row["conditional_logical_entropy_bits"]))
        else:
            probabilities = [float(x) for x in row["sector_probabilities"]]
            entropies.append(-sum(x * math.log2(x) for x in probabilities if x > 0))
    return {"risk": risks, "gap": gaps, "entropy": np.asarray(entropies)}


def statistics(arrays: dict[str, np.ndarray]) -> dict[str, float]:
    risks, gaps, entropy = arrays["risk"], arrays["gap"], arrays["entropy"]
    total_risk = float(risks.sum())
    result = {
        "Bayes_risk": float(risks.mean()),
        "median_abs_DeltaF": quantile(gaps, 0.5),
        "lower_quartile_abs_DeltaF": quantile(gaps, 0.25),
        "conditional_logical_entropy_bits": float(entropy.mean()),
    }
    for threshold in THRESHOLDS:
        key = str(threshold)
        mask = gaps <= threshold
        result[f"C_L({key})"] = float(mask.mean())
        result[f"B_L({key})"] = float(risks[mask].sum() / total_risk)
    return result


def bootstrap_statistics(arrays: dict[str, np.ndarray], seed: int) -> tuple[dict, dict[str, np.ndarray]]:
    point = statistics(arrays)
    samples = {key: np.empty(REPLICATES, dtype=float) for key in point}
    rng = np.random.default_rng(seed)
    n = len(arrays["risk"])
    block = 200
    for start in range(0, REPLICATES, block):
        count = min(block, REPLICATES - start)
        indices = rng.integers(0, n, size=(count, n))
        for offset, row_indices in enumerate(indices):
            value = statistics({key: array[row_indices] for key, array in arrays.items()})
            for key in samples:
                samples[key][start + offset] = value[key]
    intervals = {
        key: {
            "estimate": float(point[key]),
            "interval95": [float(x) for x in np.quantile(values, [0.025, 0.975])],
        }
        for key, values in samples.items()
    }
    return intervals, samples


def bootstrap_paired_contrast(left: dict[str, np.ndarray], right: dict[str, np.ndarray], seed: int) -> dict:
    n = min(len(left["risk"]), len(right["risk"]))
    left = {key: value[:n] for key, value in left.items()}
    right = {key: value[:n] for key, value in right.items()}
    rng = np.random.default_rng(seed)
    keys = statistics(left).keys()
    samples = {key: np.empty(REPLICATES, dtype=float) for key in keys}
    block = 200
    for start in range(0, REPLICATES, block):
        count = min(block, REPLICATES - start)
        indices = rng.integers(0, n, size=(count, n))
        for offset, row_indices in enumerate(indices):
            a = statistics({key: value[row_indices] for key, value in left.items()})
            b = statistics({key: value[row_indices] for key, value in right.items()})
            for key in samples:
                samples[key][start + offset] = b[key] - a[key]
    left_point, right_point = statistics(left), statistics(right)
    return {
        "common_prefix_records": n,
        "direction": "right minus left",
        "metrics": {
            key: {
                "estimate": float(right_point[key] - left_point[key]),
                "interval95": [float(x) for x in np.quantile(values, [0.025, 0.975])],
            }
            for key, values in samples.items()
        },
    }


def raw_inputs() -> tuple[dict[tuple[float, int], Path], set[tuple[float, int]]]:
    synthesis = load(SYNTHESIS)
    paths: dict[tuple[float, int], Path] = {}
    historical: set[tuple[float, int]] = set()
    for row in synthesis["existing_p030_square_rows"]:
        key = (float(row["q"]), int(row["L"]))
        if key[0] in (0.9, 0.97) and key[1] in (7, 9):
            path = ROOT / row["integrity"]["raw_file"]
            if sha256(path) != row["integrity"]["raw_sha256"]:
                raise RuntimeError(f"historical source hash mismatch: {path}")
            paths[key] = path
            historical.add(key)
    for q, L in ((0.94, 7), (0.94, 9), (0.9, 11), (0.94, 11), (0.97, 11)):
        paths[(q, L)] = LAB / "results" / "posterior-gap-boundary-tail-cells" / f"square-L{L}-p30-q{int(round(q * 100)):02d}-boundary-tail.json"
    if len(paths) != 9:
        raise RuntimeError("complete matrix does not contain nine cells")
    return paths, historical


def render(rows: list[dict]) -> None:
    plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 13, "legend.fontsize": 11})
    figure, axes = plt.subplots(2, 2, figsize=(10.5, 8.2), constrained_layout=True)
    panels = [
        ("Bayes_risk", r"Bayes risk $R_L$", "A  Optimal logical risk"),
        ("C_L(1.0)", r"$C_L(1)=\Pr(|\Delta F|\leq1)$", "B  Low-gap probability"),
        ("median_abs_DeltaF", r"Median $|\Delta F|$", "C  Typical posterior gap"),
        ("B_L(1.0)", r"$B_L(1)$", "D  Risk share from low-gap records"),
    ]
    colors = {0.9: "#2a9d8f", 0.94: "#e9a23b", 0.97: "#d1495b"}
    for axis, (metric, ylabel, title) in zip(axes.flat, panels):
        for q in (0.9, 0.94, 0.97):
            group = sorted((row for row in rows if row["q"] == q), key=lambda row: row["L"])
            x = np.asarray([row["L"] for row in group])
            y = np.asarray([row["metrics"][metric]["estimate"] for row in group])
            low = np.asarray([row["metrics"][metric]["interval95"][0] for row in group])
            high = np.asarray([row["metrics"][metric]["interval95"][1] for row in group])
            axis.plot(x, y, color=colors[q], linewidth=2, label=f"q={q:.2f}")
            for row, xx, yy, lo, hi in zip(group, x, y, low, high):
                marker_face = "white" if row["provenance_class"] == "historical_control" else colors[q]
                axis.errorbar(xx, yy, yerr=[[yy - lo], [hi - yy]], fmt="o", color=colors[q],
                              markerfacecolor=marker_face, markeredgewidth=1.8, markersize=7, capsize=3)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlabel("Linear size L")
        axis.set_ylabel(ylabel)
        axis.set_xticks([7, 9, 11])
        axis.grid(alpha=0.22)
    axes[0, 0].legend(frameon=False, ncol=3, loc="upper right")
    figure.suptitle("Posterior-gap diagnostics near the directed boundary (p=0.30)", fontsize=16, fontweight="bold")
    figure.text(0.5, -0.015, "Pointwise record-bootstrap 95% intervals; open markers are historical controls. Lines only join sampled sizes—no threshold or scaling fit.", ha="center", fontsize=10.5)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    manifest = load(MANIFEST)
    progress = load(PROGRESS)
    if manifest["status"] != "production_acquisition_complete_analysis_pending" or progress["status"] != "complete":
        raise RuntimeError("complete registered acquisition is required before analysis")
    paths, historical = raw_inputs()
    arrays_by_cell: dict[tuple[float, int], dict[str, np.ndarray]] = {}
    rows = []
    source_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in (Path(__file__).resolve(), MANIFEST, SYNTHESIS, PROGRESS)
    }
    maximum_identity_error = 0.0
    all_record_keys = []
    for index, ((q, L), path) in enumerate(sorted(paths.items())):
        raw = load(path)
        records = raw["records"]
        arrays = record_arrays(records)
        arrays_by_cell[(q, L)] = arrays
        metrics, _ = bootstrap_statistics(arrays, BASE_SEED + index * 10007)
        identity_errors = []
        for record, risk, record_gap in zip(records, arrays["risk"], arrays["gap"]):
            expected = 0.0 if math.isinf(record_gap) else 1.0 / (1.0 + math.exp(record_gap))
            identity_errors.append(abs(float(risk) - expected))
            if "record_key" in record:
                all_record_keys.append(record["record_key"])
        maximum_identity_error = max(maximum_identity_error, max(identity_errors))
        rows.append({
            "id": raw["cell"]["id"], "q": q, "L": L, "records": len(records),
            "provenance_class": "historical_control" if (q, L) in historical else "new_registered_cell",
            "raw_file": str(path.relative_to(ROOT)), "raw_sha256": sha256(path), "metrics": metrics,
        })
        source_hashes[str(path.relative_to(ROOT))] = sha256(path)

    size_contrasts = []
    for q in (0.9, 0.94, 0.97):
        left_metrics, left_samples = bootstrap_statistics(arrays_by_cell[(q, 7)], BASE_SEED + int(q * 1000) + 7)
        right_metrics, right_samples = bootstrap_statistics(arrays_by_cell[(q, 11)], BASE_SEED + int(q * 1000) + 11)
        size_contrasts.append({
            "q": q, "sizes": [7, 11], "resampling": "independent record bootstrap",
            "metrics": {
                key: {
                    "estimate": float(right_metrics[key]["estimate"] - left_metrics[key]["estimate"]),
                    "interval95": [float(x) for x in np.quantile(right_samples[key] - left_samples[key], [0.025, 0.975])],
                }
                for key in left_metrics
            },
        })

    matched_q_contrasts = [
        {
            "L": 11, "q_values": [left, right], "resampling": "paired common-prefix record bootstrap",
            **bootstrap_paired_contrast(arrays_by_cell[(left, 11)], arrays_by_cell[(right, 11)], BASE_SEED + int(1000 * left + 100 * right)),
        }
        for left, right in ((0.9, 0.94), (0.94, 0.97))
    ]

    trajectory_checks = []
    for q in (0.9, 0.94, 0.97):
        group = sorted((row for row in rows if row["q"] == q), key=lambda row: row["L"])
        value = lambda metric: [row["metrics"][metric]["estimate"] for row in group]
        trajectory_checks.append({
            "q": q,
            "Bayes_risk_strictly_decreases": all(a > b for a, b in zip(value("Bayes_risk"), value("Bayes_risk")[1:])),
            "C_L_1_strictly_decreases": all(a > b for a, b in zip(value("C_L(1.0)"), value("C_L(1.0)")[1:])),
            "median_gap_strictly_increases": all(a < b for a, b in zip(value("median_abs_DeltaF"), value("median_abs_DeltaF")[1:])),
            "lower_quartile_gap_strictly_increases": all(a < b for a, b in zip(value("lower_quartile_abs_DeltaF"), value("lower_quartile_abs_DeltaF")[1:])),
            "B_L_1_L11_not_above_L7": value("B_L(1.0)")[-1] <= value("B_L(1.0)")[0],
            "values": {
                "Bayes_risk": value("Bayes_risk"), "C_L(1)": value("C_L(1.0)"),
                "median_abs_DeltaF": value("median_abs_DeltaF"),
                "lower_quartile_abs_DeltaF": value("lower_quartile_abs_DeltaF"),
                "B_L(1)": value("B_L(1.0)"),
            },
        })

    result = {
        "status": "complete_finite_size_outward_gap_motion_no_rare_tail_takeover_asymptotic_class_unresolved",
        "contract": str(MANIFEST.relative_to(ROOT)),
        "question": manifest["question"],
        "new_physical_records": int(progress["new_physical_records"]),
        "new_bootstrap_replicates": REPLICATES,
        "matrix_cells": 9,
        "bootstrap_unit": "physical current/charge record",
        "pointwise_interval_level": 0.95,
        "rows": rows,
        "size_contrasts_L11_minus_L7": size_contrasts,
        "matched_L11_q_contrasts": matched_q_contrasts,
        "trajectory_checks": trajectory_checks,
        "mechanism_assessment": {
            "typical_stiffness": {
                "finite_size_evidence": "favored within the registered boundary window",
                "basis": "For every q, R_L and C_L(1) decrease from L7 to L11 while the median and lower quartile of abs(DeltaF) increase. The coordinated shift is strongest at q=.97 and is newly visible at q=.90 only after L11.",
                "limitation": "Three sizes do not establish divergence in probability or an asymptotic phase."
            },
            "persistent_finite_gap": {
                "finite_size_evidence": "weakened but not excluded asymptotically",
                "basis": "The prior q=.90 L7-to-L9 plateau does not persist at L11; risk, C_L(1), and both gap quantiles move outward. All q retain nonzero low-gap mass at L11.",
                "limitation": "Slow crossover or a nonzero limiting low-gap mass beyond L11 remains possible."
            },
            "rare_tail_control": {
                "finite_size_evidence": "not supported through L11",
                "basis": "B_L(1) at L11 is not above its L7 value for any q, so the shrinking low-gap set does not take an increasing share of the remaining risk on the sampled sizes.",
                "limitation": "A rare-tail regime could emerge only at larger sizes and is not ruled out."
            },
        },
        "decision": {
            "outcome": "finite-size outward gap motion across q=.90,.94,.97; no low-gap-tail takeover through L11; thermodynamic class unresolved",
            "threshold_claim": "No threshold, critical q, crossing, exponent, universality or BKT claim is made.",
            "next_scientific_question": "Determine whether fixed-gap CDFs continue to contract beyond L11 or cross over to a nonzero floor, using a separately registered larger-size method rather than extending this matrix silently.",
        },
        "integrity": {
            "maximum_record_logistic_identity_error": maximum_identity_error,
            "new_record_keys_unique": len(all_record_keys) == len(set(all_record_keys)),
            "all_nine_cells_present": len(rows) == 9,
            "all_new_cells_precision_complete": all(cell["summary"]["precision_targets_pass"] for cell in progress["cells"]),
            "historical_and_new_cells_numerically_unpooled": True,
        },
        "claim_boundary": {
            "supported": "finite-size joint motion of risk, fixed-gap mass, gap quantiles and low-gap risk concentration on the registered p=.30 matrix",
            "not_supported": "thermodynamic phase classification, threshold location, q_c, scaling exponent or BKT interpretation",
        },
        "figure": str(FIGURE.relative_to(ROOT)),
        "source_sha256": source_hashes,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    render(rows)
    print(json.dumps({"status": result["status"], "cells": len(rows), "records": result["new_physical_records"], "figure": result["figure"]}))


if __name__ == "__main__":
    main()
