#!/usr/bin/env python3
"""Compare Phase B14 branches using continuous posterior trend evidence only."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b14-honeycomb-two-branch-analysis-2026-08-28.json"


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def find_base_cell(phase_map: dict, q: float, p: float) -> dict:
    for row in phase_map["analyses"]:
        if abs(float(row["q"]) - q) > 1e-12:
            continue
        for cell in row["cells"]:
            if abs(float(cell["p"]) - p) < 1e-12:
                return {"sizes": [7, 9, 11], "logical_errors": cell["logical_errors"], "shots": cell["shots"]}
    raise ValueError("missing Phase B14 base cell")


def summary_counts(payload: dict, job: dict) -> dict[int, tuple[int, int]]:
    counts = {}
    for row in payload["summaries"]:
        if abs(float(row["q"]) - float(job["q"])) < 1e-12 and abs(float(row["p"]) - float(job["p"])) < 1e-12:
            counts[int(row["L"])] = (int(row["logical_errors"]), int(row["shots"]))
    if set(counts) != set(job["sizes"]):
        raise ValueError("Phase B14 summary size coverage mismatch")
    return counts


def pool_counts(base: dict, additions: list[dict[int, tuple[int, int]]]) -> tuple[list[int], list[int], list[int]]:
    pooled = {int(L): [int(e), int(n)] for L, e, n in zip(base["sizes"], base["logical_errors"], base["shots"])}
    for addition in additions:
        for size, (errors, shots) in addition.items():
            if size in pooled:
                pooled[size][0] += errors
                pooled[size][1] += shots
            else:
                pooled[size] = [errors, shots]
    sizes = sorted(pooled)
    return sizes, [pooled[size][0] for size in sizes], [pooled[size][1] for size in sizes]


def sign_entropy(probability_upward: float) -> float:
    return -sum(value * math.log(value) for value in (probability_upward, 1.0 - probability_upward) if value > 0.0)


def continuous_summary(sizes: list[int], errors: list[int], shots: list[int], seed: int) -> dict:
    fuzzy = load("analyze_phase_b1_bayesian_fuzzy_trend.py", f"phase_b14_fuzzy_{seed}")
    result = fuzzy.posterior_fuzzy_linear_trend(
        np.asarray(errors), np.asarray(shots), np.asarray(sizes), seed=seed
    )
    return {
        "sizes": sizes,
        "logical_errors": errors,
        "shots": shots,
        "posterior_probability_upward_trend": result["posterior_probability_upward_trend"],
        "posterior_probability_downward_trend": result["posterior_probability_downward_trend"],
        "posterior_log_odds_upward_vs_downward": result["posterior_log_odds_upward_vs_downward"],
        "posterior_log_odds_censoring": result["posterior_log_odds_censoring"],
        "posterior_mean_slope_ler_per_distance": result["posterior_mean_slope_ler_per_distance"],
        "posterior_slope_interval90": result["posterior_slope_interval90"],
        "posterior_sign_entropy_nats": sign_entropy(result["posterior_probability_upward_trend"]),
        "qmc_standard_error_upward_probability": result["qmc_standard_error_upward_probability"],
    }


def analyze(manifest_path: Path, audit_path: Path) -> dict:
    submit = load("submit_phase_b14_two_branch.py", "phase_b14_submit_for_analysis")
    manifest = json.loads(Path(manifest_path).read_text())
    audit = json.loads(Path(audit_path).read_text())
    if audit.get("status") != "data_complete_not_analyzed" or audit.get("jobs_complete") != 8 or audit.get("raw_rows_observed") != 10000:
        raise ValueError("Phase B14 completion audit incomplete")
    if audit.get("manifest", {}).get("sha256") != submit.sha256(manifest_path):
        raise ValueError("Phase B14 audit/manifest hash mismatch")
    phase_map = json.loads((LAB_DIR / manifest["sources"][0]["path"]).read_text())
    summaries = {
        (row["branch"], float(row["q"]), float(row["p"])): json.loads(Path(row["summary"]).read_text())
        for row in audit["records"]
    }
    analyses = []
    cells = sorted({(float(job["q"]), float(job["p"])) for job in manifest["jobs"]})
    for offset, (q, p) in enumerate(cells):
        jobs = {(job["branch"]): job for job in manifest["jobs"] if float(job["q"]) == q and float(job["p"]) == p}
        base = find_base_cell(phase_map, q, p)
        distance = summary_counts(summaries[("distance_leverage_L5_L13", q, p)], jobs["distance_leverage_L5_L13"])
        precision = summary_counts(summaries[("same_window_precision_L7_L9_L11", q, p)], jobs["same_window_precision_L7_L9_L11"])
        variants = {}
        for index, (name, additions, new_decodes) in enumerate((
            ("base", [], 0),
            ("distance_leverage", [distance], 1000),
            ("same_window_precision", [precision], 1500),
            ("combined", [distance, precision], 2500),
        )):
            sizes, errors, shots = pool_counts(base, additions)
            variants[name] = continuous_summary(sizes, errors, shots, 914000 + 10 * offset + index)
            variants[name]["new_decodes"] = new_decodes
        base_entropy = variants["base"]["posterior_sign_entropy_nats"]
        for name in ("distance_leverage", "same_window_precision", "combined"):
            item = variants[name]
            item["sign_entropy_reduction_nats"] = base_entropy - item["posterior_sign_entropy_nats"]
            item["sign_entropy_reduction_nats_per_1000_new_decodes"] = (
                item["sign_entropy_reduction_nats"] * 1000.0 / item["new_decodes"]
            )
        analyses.append({"q": q, "p": p, "variants": variants})
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_continuous_evidence_only",
        "manifest": {"path": str(manifest_path), "sha256": submit.sha256(manifest_path)},
        "completion_audit": {"path": str(audit_path), "sha256": submit.sha256(audit_path)},
        "primary_comparison": "posterior sign-entropy reduction in nats per 1000 new decodes",
        "analyses": analyses,
        "cells_analyzed": len(analyses),
        "new_decodes": 10000,
        "cell_or_phase_classification_performed": False,
        "boundary_inference_performed": False,
        "crossing_statistic_used": False,
        "evidence_boundary": "Four preregistered moderate-LER cells; branch-separated finite-window posterior trend evidence only.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.manifest, args.audit)
    load("submit_phase_b14_two_branch.py", "phase_b14_writer").atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells_analyzed": output["cells_analyzed"]}, indent=2))


if __name__ == "__main__":
    main()
