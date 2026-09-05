#!/usr/bin/env python3
"""Analyze Phase B1 with five-distance Bayesian order probabilities."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import beta as beta_distribution
from scipy.stats import qmc


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b1-honeycomb-l5-l13-sentinels-manifest-2026-08-28.json"
DEFAULT_BASE = LAB_DIR / "results/phase2-residual80-honeycomb-bayesian-order-phase-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-sentinels-completion-audit-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-sentinels-analysis-2026-08-28.json"
SIZES = [5, 7, 9, 11, 13]
POSTERIOR_THRESHOLD = 0.90


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def posterior_order_qmc(
    errors: np.ndarray,
    shots: np.ndarray,
    *,
    prior_alpha: float = 0.5,
    prior_beta: float = 0.5,
    scramble_replicates: int = 8,
    base2_power: int = 13,
    seed: int = 880028,
) -> dict:
    """Estimate strict order posterior masses with replicated scrambled Sobol draws."""
    errors = np.asarray(errors, dtype=np.float64)
    shots = np.asarray(shots, dtype=np.float64)
    if errors.shape != shots.shape or errors.ndim != 1 or errors.size < 3:
        raise ValueError("matching one-dimensional counts for at least three sizes are required")
    if np.any(shots <= 0) or np.any(errors < 0) or np.any(errors > shots):
        raise ValueError("invalid binomial counts")
    alpha = errors + prior_alpha
    beta = shots - errors + prior_beta
    decreasing = []
    increasing = []
    order_counts: dict[tuple[int, ...], int] = {}
    for replicate in range(scramble_replicates):
        uniforms = qmc.Sobol(errors.size, scramble=True, seed=seed + replicate).random_base2(base2_power)
        draws = beta_distribution.ppf(uniforms, alpha, beta)
        deltas = np.diff(draws, axis=1)
        decreasing.append(float(np.mean(np.all(deltas < 0, axis=1))))
        increasing.append(float(np.mean(np.all(deltas > 0, axis=1))))
        orderings, counts = np.unique(np.argsort(draws, axis=1), axis=0, return_counts=True)
        for ordering, count in zip(orderings, counts):
            key = tuple(int(value) for value in ordering)
            order_counts[key] = order_counts.get(key, 0) + int(count)
    draws_per_replicate = 2**base2_power
    total_draws = scramble_replicates * draws_per_replicate
    decreasing_events = int(round(sum(decreasing) * draws_per_replicate))
    increasing_events = int(round(sum(increasing) * draws_per_replicate))
    p_down = float(decreasing_events / total_draws)
    p_up = float(increasing_events / total_draws)
    p_other = float(max(0.0, 1.0 - p_down - p_up))
    probability_resolution = 1.0 / total_draws
    ordering_masses = sorted(
        (
            {"indices_low_to_high": list(ordering), "probability": count / total_draws}
            for ordering, count in order_counts.items()
        ),
        key=lambda row: (-row["probability"], row["indices_low_to_high"]),
    )
    ordering_entropy = float(
        -sum(row["probability"] * np.log2(row["probability"]) for row in ordering_masses)
    )
    if p_up > 0.0 and p_down > 0.0:
        log_odds = float(np.log(p_up) - np.log(p_down))
        log_odds_censoring = {"relation": "equal", "bound": log_odds}
    elif p_up == 0.0 and p_down > 0.0:
        log_odds = None
        log_odds_censoring = {
            "relation": "less_than",
            "bound": float(np.log(probability_resolution) - np.log(p_down)),
        }
    elif p_down == 0.0 and p_up > 0.0:
        log_odds = None
        log_odds_censoring = {
            "relation": "greater_than",
            "bound": float(np.log(p_up) - np.log(probability_resolution)),
        }
    else:
        log_odds = None
        log_odds_censoring = {"relation": "indeterminate", "bound": None}
    return {
        "posterior_probability_decreasing": p_down,
        "posterior_probability_increasing": p_up,
        "posterior_probability_other_order": p_other,
        "posterior_log_odds_increasing_vs_decreasing": log_odds,
        "posterior_log_odds_censoring": log_odds_censoring,
        "qmc_standard_error_decreasing": None if decreasing_events == 0 else float(np.std(decreasing, ddof=1) / np.sqrt(scramble_replicates)),
        "qmc_standard_error_increasing": None if increasing_events == 0 else float(np.std(increasing, ddof=1) / np.sqrt(scramble_replicates)),
        "qmc_decreasing_events": decreasing_events,
        "qmc_increasing_events": increasing_events,
        "qmc_probability_resolution": probability_resolution,
        "qmc_ordering_entropy_bits": ordering_entropy,
        "qmc_effective_ordering_count": float(2.0**ordering_entropy),
        "qmc_top_orderings": ordering_masses[:8],
        "qmc_scramble_replicates": scramble_replicates,
        "qmc_draws_per_replicate": draws_per_replicate,
    }


def classify(posterior: dict, threshold: float = POSTERIOR_THRESHOLD) -> str:
    if posterior["posterior_probability_decreasing"] >= threshold:
        return "decodable"
    if posterior["posterior_probability_increasing"] >= threshold:
        return "undecodable"
    return "unresolved"


def summary_counts(payload: dict, *, p: float, sizes: list[int]) -> tuple[list[int], list[int]]:
    rows = {(int(row["L"]), round(float(row["p"]), 12)): row for row in payload["summaries"]}
    selected = [rows[(size, round(p, 12))] for size in sizes]
    return [int(row["logical_errors"]) for row in selected], [int(row["shots"]) for row in selected]


def load_new_shard(manifest: dict, cell: dict) -> dict:
    tag = lambda value: f"{int(round(100 * value)):03d}"
    stem = f"phase-b1-honeycomb-l5-l13-q{tag(cell['q'])}-p{tag(cell['p'])}-2026-08-28"
    path = LAB_DIR / "results" / f"{stem}.json"
    payload = json.loads(path.read_text())
    if payload["campaign"] != manifest["campaign"] or payload["sizes"] != manifest["new_sizes"]:
        raise ValueError(f"Phase B1 shard configuration mismatch: {path}")
    if payload["decoder"] != manifest["decoder"] or payload["source_hashes"] != manifest["required_source_hashes"]:
        raise ValueError(f"Phase B1 shard provenance mismatch: {path}")
    raw = LAB_DIR / "results" / f"{stem}-raw.jsonl.gz"
    if not raw.is_file() or sha256(raw) != payload["raw_records"]["sha256"]:
        raise ValueError(f"Phase B1 raw integrity mismatch: {raw}")
    return payload


def label_orderings(posterior: dict) -> dict:
    """Attach physical distances to the ascending-index order diagnostic."""
    for row in posterior["qmc_top_orderings"]:
        row["sizes_low_to_high_ler"] = [SIZES[index] for index in row["indices_low_to_high"]]
    return posterior


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    base = json.loads(args.base.read_text())
    audit = json.loads(args.audit.read_text())
    if audit["status"] != "data_complete_not_analyzed":
        raise SystemExit("Phase B1 completion audit is not analysis-ready")
    if audit["manifest"]["sha256"] != sha256(args.manifest):
        raise SystemExit("Phase B1 completion audit does not match the current manifest")
    if audit["raw_rows_observed"] != manifest["expected_new_decodes"] or audit["syndrome_faithful_rows"] != manifest["expected_new_decodes"]:
        raise SystemExit("Phase B1 completion audit does not cover the registered decode budget")
    if sha256(args.base) != manifest["selection_evidence"]["bayesian_source_sha256"]:
        raise SystemExit("Bayesian base hash differs from Phase B1 contract")
    base_paths = {round(float(row["q"]), 12): Path(path) for row, path in zip(base["analyses"], base["validated_summaries"])}
    analyses = []
    for offset, cell in enumerate(manifest["cells"]):
        q_value = round(float(cell["q"]), 12)
        baseline = json.loads(base_paths[q_value].read_text())
        new = load_new_shard(manifest, cell)
        old_errors, old_shots = summary_counts(baseline, p=float(cell["p"]), sizes=[7, 9, 11])
        new_errors, new_shots = summary_counts(new, p=float(cell["p"]), sizes=[5, 13])
        by_size_errors = {5: new_errors[0], 7: old_errors[0], 9: old_errors[1], 11: old_errors[2], 13: new_errors[1]}
        by_size_shots = {5: new_shots[0], 7: old_shots[0], 9: old_shots[1], 11: old_shots[2], 13: new_shots[1]}
        errors = np.asarray([by_size_errors[size] for size in SIZES])
        shots = np.asarray([by_size_shots[size] for size in SIZES])
        posterior = label_orderings(posterior_order_qmc(errors, shots, seed=880028 + offset))
        sensitivity = label_orderings(posterior_order_qmc(errors, shots, prior_alpha=1.0, prior_beta=1.0, seed=890028 + offset))
        analyses.append({"role": cell["role"], "q": cell["q"], "p": cell["p"], "sizes": SIZES, "logical_errors": errors.tolist(), "shots": shots.tolist(), **posterior, "classification": classify(posterior), "uniform_prior_sensitivity": {**sensitivity, "classification": classify(sensitivity)}})
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "campaign": manifest["campaign"],
        "sizes": SIZES,
        "hypotheses": manifest["inference"],
        "numerical_method": "eight replicated scrambled Sobol integrations with 8192 draws per replicate",
        "zero_event_policy": "A zero directional event count is resolution-censored at one over total QMC draws; the log odds is null and a one-sided numerical bound is reported instead of inventing a finite floor.",
        "provenance": {
            "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
            "completion_audit": {"path": str(args.audit), "sha256": sha256(args.audit)},
            "three_distance_base": {"path": str(args.base), "sha256": sha256(args.base)},
            "analyzer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        },
        "analyses": analyses,
        "crossing_statistic_used": False,
        "evidence_boundary": "Four-cell five-distance sentinel analysis only; no grid fill or asymptotic boundary.",
    }
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "classifications": {row["role"]: row["classification"] for row in analyses}}, indent=2))


if __name__ == "__main__":
    main()
