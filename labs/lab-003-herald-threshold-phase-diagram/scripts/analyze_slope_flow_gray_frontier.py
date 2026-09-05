#!/usr/bin/env python3
"""Reproduce the withdrawn Phase S1 slope-flow frontier analysis.

Methodology correction (2026-08-28): the underlying logit-versus-log-size
model assumes unsupported power-law logical-error odds.  This script is kept
for historical reproducibility only; its classifications are not phase claims.
See ``../METHODOLOGY.md``.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-s1-honeycomb-slope-flow-gray-frontier-manifest-2026-08-28.json"
DEFAULT_BASE = LAB_DIR / "results/phase2-residual80-honeycomb-slope-flow-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-s1-honeycomb-slope-flow-gray-frontier-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-s1-honeycomb-slope-flow-gray-frontier-analysis-2026-08-28.json"
DEFAULT_FIGURE = LAB_DIR / "figures/phase-s1-honeycomb-slope-flow-phase-map-2026-08-28.png"
SLOPE_ZERO_TOLERANCE = 1e-8
BOOTSTRAP_SEED = 780027


def load_slope_module():
    path = Path(__file__).with_name("analyze_slope_flow_phase_map.py")
    spec = importlib.util.spec_from_file_location("slope_flow_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_dispatcher():
    path = Path(__file__).with_name("submit_slope_flow_gray_frontier.py")
    spec = importlib.util.spec_from_file_location("gray_frontier_dispatcher_for_analysis", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cluster_rows(payload: dict, *, p: float, size: int) -> list[dict]:
    rows = [
        {"seed": int(row["seed"]), "logical_errors": int(row["logical_errors"]), "shots": int(row["shots"])}
        for row in payload["per_seed"]
        if int(row["L"]) == size and abs(float(row["p"]) - p) < 1e-12
    ]
    if not rows or len({row["seed"] for row in rows}) != len(rows):
        raise ValueError(f"missing or duplicate seed clusters at L={size}, p={p}")
    return rows


def preliminary_classification(interval: np.ndarray, probability_decodable: float, probability_undecodable: float) -> str:
    if interval[1] < -SLOPE_ZERO_TOLERANCE and probability_decodable >= 0.95:
        return "decodable"
    if interval[0] > SLOPE_ZERO_TOLERANCE and probability_undecodable >= 0.95:
        return "undecodable"
    return "unresolved"


def gated_classification(preliminary: str, *, loo_stable: bool, pair_agrees: bool | None) -> str:
    if preliminary == "unresolved" or not loo_stable or pair_agrees is False:
        return "unresolved"
    return preliminary


def analyze_target(
    *,
    base_payload: dict,
    new_payload: dict,
    branch: dict,
    cell: dict,
    replicates: int,
    slope_module,
) -> dict:
    q = float(cell["q"])
    p = float(cell["p"])
    sizes = [int(value) for value in branch["sizes"]]
    clusters = {}
    if branch["id"] == "seed-limited-pinch":
        for size in sizes:
            clusters[size] = cluster_rows(base_payload, p=p, size=size) + cluster_rows(new_payload, p=p, size=size)
    elif branch["id"] == "distance-limited-pinch":
        clusters[7] = cluster_rows(base_payload, p=p, size=7)
        clusters[9] = cluster_rows(base_payload, p=p, size=9)
        clusters[11] = cluster_rows(base_payload, p=p, size=11) + cluster_rows(new_payload, p=p, size=11)
        clusters[13] = cluster_rows(new_payload, p=p, size=13)
        sizes = [7, 9, 11, 13]
    else:
        raise ValueError(f"unknown branch {branch['id']}")

    log_sizes = np.log(np.asarray(sizes, dtype=np.float64))
    observed_successes = np.asarray([[sum(row["logical_errors"] for row in clusters[size]) for size in sizes]], dtype=float)
    observed_totals = np.asarray([[sum(row["shots"] for row in clusters[size]) for size in sizes]], dtype=float)
    beta = float(slope_module.fit_logit_slopes(observed_successes, observed_totals, log_sizes)[0])

    rng = np.random.default_rng(np.random.SeedSequence([BOOTSTRAP_SEED, int(round(q * 100)), int(round(p * 100))]))
    boot_successes = np.empty((replicates, len(sizes)), dtype=float)
    boot_totals = np.empty_like(boot_successes)
    for offset, size in enumerate(sizes):
        values = clusters[size]
        successes = np.asarray([row["logical_errors"] for row in values], dtype=float)
        totals = np.asarray([row["shots"] for row in values], dtype=float)
        draws = rng.integers(0, len(values), size=(replicates, len(values)))
        boot_successes[:, offset] = successes[draws].sum(axis=1)
        boot_totals[:, offset] = totals[draws].sum(axis=1)
    beta_samples = slope_module.fit_logit_slopes(boot_successes, boot_totals, log_sizes)
    interval = np.quantile(beta_samples, [0.05, 0.95])
    probability_decodable = float(np.mean(beta_samples < -SLOPE_ZERO_TOLERANCE))
    probability_undecodable = float(np.mean(beta_samples > SLOPE_ZERO_TOLERANCE))
    preliminary = preliminary_classification(interval, probability_decodable, probability_undecodable)

    loo_slopes = []
    for omitted in range(len(sizes)):
        retained = [index for index in range(len(sizes)) if index != omitted]
        loo_slopes.append(
            float(
                slope_module.fit_logit_slopes(
                    observed_successes[:, retained],
                    observed_totals[:, retained],
                    log_sizes[retained],
                )[0]
            )
        )
    beta_sign = int(np.sign(beta)) if abs(beta) > SLOPE_ZERO_TOLERANCE else 0
    loo_stable = beta_sign != 0 and all(
        abs(value) > SLOPE_ZERO_TOLERANCE and int(np.sign(value)) == beta_sign for value in loo_slopes
    )

    pair_beta = None
    pair_agrees = None
    if branch["id"] == "distance-limited-pinch":
        new_pair = {size: cluster_rows(new_payload, p=p, size=size) for size in (11, 13)}
        pair_successes = np.asarray([[sum(row["logical_errors"] for row in new_pair[size]) for size in (11, 13)]], dtype=float)
        pair_totals = np.asarray([[sum(row["shots"] for row in new_pair[size]) for size in (11, 13)]], dtype=float)
        pair_beta = float(
            slope_module.fit_logit_slopes(pair_successes, pair_totals, np.log(np.asarray([11, 13], dtype=float)))[0]
        )
        pair_sign = int(np.sign(pair_beta)) if abs(pair_beta) > SLOPE_ZERO_TOLERANCE else 0
        pair_agrees = beta_sign != 0 and pair_sign == beta_sign

    classification = gated_classification(preliminary, loo_stable=loo_stable, pair_agrees=pair_agrees)
    return {
        "q": q,
        "p": p,
        "branch": branch["id"],
        "sizes": sizes,
        "clusters_per_distance": {str(size): len(clusters[size]) for size in sizes},
        "shots_per_distance": {str(size): int(observed_totals[0, offset]) for offset, size in enumerate(sizes)},
        "beta": beta,
        "beta_interval90": [float(interval[0]), float(interval[1])],
        "probability_decodable": probability_decodable,
        "probability_undecodable": probability_undecodable,
        "preliminary_classification": preliminary,
        "leave_one_distance_out_slopes": loo_slopes,
        "leave_one_distance_out_sign_stable": loo_stable,
        "new_l11_l13_beta": pair_beta,
        "new_l11_l13_sign_agrees": pair_agrees,
        "previous_classification": "unresolved",
        "classification": classification,
        "classification_changed": classification != "unresolved",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    audit = json.loads(args.audit.read_text())
    if manifest["status"] != "data_complete_not_analyzed" or audit["status"] != "data_complete_not_analyzed":
        raise SystemExit("Phase S1 data and completion audit must be complete before analysis")
    if audit["scientific_analysis_performed"] or audit["crossing_statistic_used"]:
        raise SystemExit("completion audit is not analysis-clean")
    base = json.loads(args.base.read_text())
    slope_module = load_slope_module()
    dispatcher = load_dispatcher()
    jobs = dispatcher.expand_jobs(manifest)
    new_payloads = {(job["q"], job["p"]): json.loads(Path(job["result"]).read_text()) for job in jobs}
    base_payloads = {}
    for path in base["validated_summaries"]:
        payload = json.loads(Path(path).read_text())
        base_payloads[float(payload["q"])] = payload
    replicates = int(manifest["inference"]["bootstrap_replicates"])
    updates = []
    for branch in manifest["branches"]:
        for cell in branch["cells"]:
            key = (float(cell["q"]), float(cell["p"]))
            updates.append(
                analyze_target(
                    base_payload=base_payloads[key[0]],
                    new_payload=new_payloads[key],
                    branch=branch,
                    cell=cell,
                    replicates=replicates,
                    slope_module=slope_module,
                )
            )

    analyses = copy.deepcopy(base["analyses"])
    analysis_index = {float(row["q"]): row for row in analyses}
    for update in updates:
        row = analysis_index[update["q"]]
        target = next(cell for cell in row["cells"] if abs(float(cell["p"]) - update["p"]) < 1e-12)
        target.clear()
        target.update({key: value for key, value in update.items() if key not in {"q", "previous_classification", "classification_changed", "preliminary_classification", "clusters_per_distance", "shots_per_distance", "new_l11_l13_beta", "new_l11_l13_sign_agrees", "branch", "sizes"}})
        target["phase_s1_updated"] = True
        target["phase_s1_branch"] = update["branch"]
        target["analysis_sizes"] = update["sizes"]

    p_values = [float(value) for value in base["p_values"]]
    slope_module.plot_phase_map(
        analyses,
        p_values,
        args.figure,
        title="Honeycomb operational phase map from all-distance LER scaling flow\n"
        "Phase S1 updates 10 measured gray-frontier cells; no crossing statistic",
    )
    counts = {
        label: sum(cell["classification"] == label for row in analyses for cell in row["cells"])
        for label in ("decodable", "undecodable", "unresolved")
    }
    changed = {
        label: sum(update["classification"] == label for update in updates)
        for label in ("decodable", "undecodable", "unresolved")
    }
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "analyzed",
        "campaign": manifest["campaign"],
        "primary_statistic": manifest["inference"]["primary_statistic"],
        "bootstrap": {
            "replicates": replicates,
            "confidence_level": manifest["inference"]["confidence_level"],
            "unit": manifest["inference"]["cluster_policy"],
            "seed": BOOTSTRAP_SEED,
        },
        "updated_cells": updates,
        "updated_cell_outcomes": changed,
        "cell_counts_before": base["cell_counts"],
        "cell_counts_after": counts,
        "analyses": analyses,
        "figure": str(args.figure),
        "completion_audit": str(args.audit),
        "crossing_statistic_used": False,
        "evidence_boundary": "Only the ten preregistered Phase S1 cells are updated. Every other measured cell is copied unchanged from the Phase 2 slope-flow map; no interpolation or crossing inference is used.",
    }
    slope_module.load_validator().atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "figure": str(args.figure), "updated_cell_outcomes": changed, "cell_counts_after": counts}, indent=2))


if __name__ == "__main__":
    main()
