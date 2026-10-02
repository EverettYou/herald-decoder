#!/usr/bin/env python3
"""Registered J6B pointwise, whole-history paired uncertainty analysis."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
MANIFEST = LAB / "manifests/j6b-disjoint-temporal-handoff-pilot-2026-09-23.json"
INTEGRITY = LAB / "results/j6b-disjoint-temporal-handoff-analysis-2026-09-23.json"
ROWS = LAB / "results/j6b-disjoint-temporal-handoff-rows-2026-09-23.jsonl"
OUTPUT = LAB / "results/j6b-disjoint-temporal-handoff-paired-analysis-2026-09-23.json"
EXPECTED_MANIFEST = "8140182a4be0315a205936626c7ec727f765efe66047c02bbeac588097b7fdb2"
EXPECTED_ROWS = "620c5db65231e5c112a497397aad168eefd7d284f1af362c52d512c6741fbefe"
BOOTSTRAP_SEED = 923242000
REPLICATES = 2000
Z = 1.959963984540054


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def insist(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def quantile(sorted_values: list[float], p: float) -> float:
    position = (len(sorted_values) - 1) * p
    low = math.floor(position)
    high = math.ceil(position)
    return sorted_values[low] + (position - low) * (sorted_values[high] - sorted_values[low])


def wilson(k: int, n: int) -> list[float]:
    p = k / n
    denominator = 1 + Z * Z / n
    center = (p + Z * Z / (2 * n)) / denominator
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denominator
    return [center - half, center + half]


def main() -> None:
    insist(not OUTPUT.exists(), "analysis output already exists; never silently rerun")
    insist(digest(MANIFEST) == EXPECTED_MANIFEST, "manifest digest mismatch")
    insist(digest(ROWS) == EXPECTED_ROWS, "frozen raw-row digest mismatch")
    manifest = json.loads(MANIFEST.read_text())
    integrity = json.loads(INTEGRITY.read_text())
    insist(integrity["status"] == "production_integrity_passed_bootstrap_pending", "production not released")
    insist(integrity["integrity_passed"] and not integrity["integrity_failures"], "integrity gate failed")
    insist(integrity["provenance_passed"] and integrity["production_release_passed"], "provenance gate failed")
    insist(all(x["passed"] for x in integrity["event_gates"].values()), "event gate failed")
    insist(all(n >= 8 for n in integrity["resolved_handoff_histories_by_mode"].values()), "resolution gate failed")
    insist(integrity["raw_rows_sha256"] == EXPECTED_ROWS, "integrity result row digest mismatch")
    insist(integrity["manifest_sha256"] == EXPECTED_MANIFEST, "integrity result manifest mismatch")
    insist(integrity["counters"] == {"production_histories_generated": 272,
                                     "production_arm_evaluations": 2176,
                                     "bootstrap_replicates": 0}, "production counters mismatch")

    expected_cells = {c["id"]: (index, c["histories"]) for index, c in enumerate(manifest["matched_design"]["cells"])}
    modes = manifest["matched_design"]["modes"]
    branches = manifest["matched_design"]["schedules"]
    rows = [json.loads(line) for line in ROWS.read_text().splitlines()]
    insist(len(rows) == 2176, "row count mismatch")
    by_history: dict[tuple[str, int], dict[tuple[str, str], dict]] = defaultdict(dict)
    for row in rows:
        cell = row["cell_id"]
        index, n = expected_cells[cell]
        h = row["history_index"]
        insist(isinstance(h, int) and 0 <= h < n, "history index out of range")
        insist(row["cell_index"] == index, "cell index mismatch")
        insist(row["master_seed"] == 923240000 + 100000 * index + h, "seed mismatch")
        insist(row["trial_id"] == f"j6b-{cell}-{h:04d}", "trial id mismatch")
        insist(row["mode"] in modes and row["branch"] in branches, "unregistered arm")
        insist(row["denominator_included"] is True, "post-selection or missing denominator")
        insist(type(row["logical_failure"]) is bool, "non-Boolean loss")
        insist(row["status"] in ("scored", "failed_closed"), "unknown arm status")
        insist(row["status"] != "failed_closed" or row["logical_failure"] is True, "abort not scored as failure")
        arm = (row["mode"], row["branch"])
        group = by_history[(cell, h)]
        insist(arm not in group, "duplicate arm row")
        group[arm] = row

    expected_arms = {(mode, branch) for mode in modes for branch in branches}
    insist(len(by_history) == 272, "history count mismatch")
    for (cell, h), group in by_history.items():
        insist(set(group) == expected_arms, "incomplete matched arm set")
        for key in ("master_seed", "trial_id", "history_digest", "physical_key",
                    "first_observation_key", "second_exogenous_key"):
            insist(len({row[key] for row in group.values()}) == 1, f"unmatched {key}")
        if cell == "zero_control":
            insist(all(not row["logical_failure"] for row in group.values()), "zero-control failure")

    arm_risks = []
    contrasts = []
    rng = random.Random(BOOTSTRAP_SEED)
    for cell in ("clean_herald_schedule", "joint_readout_noise"):
        n = expected_cells[cell][1]
        histories = [by_history[(cell, h)] for h in range(n)]
        for mode in modes:
            for branch in branches:
                arm_rows = [g[(mode, branch)] for g in histories]
                k = sum(row["logical_failure"] for row in arm_rows)
                arm_risks.append({"cell_id": cell, "mode": mode, "branch": branch,
                                  "n": n, "failures": k, "risk": k / n,
                                  "wilson_95_pointwise": wilson(k, n),
                                  "failed_closed": sum(row["status"] == "failed_closed" for row in arm_rows),
                                  "resolved_prior_handoff": sum(row["resolved_prior_handoff"] for row in arm_rows)})

        pairs = []
        for mode in modes:
            for baseline in ("immediate", "fixed_delay_1"):
                pairs.append(("schedule", (mode, "jit_lyons_brown"), (mode, baseline)))
        for branch in ("immediate", "fixed_delay_1", "jit_lyons_brown"):
            pairs.append(("public_mode", ("heralded", branch), ("syndrome_only", branch)))
        for family, a, b in pairs:
            differences = [int(g[a]["logical_failure"]) - int(g[b]["logical_failure"]) for g in histories]
            mean = sum(differences) / n
            samples = []
            for _ in range(REPLICATES):
                samples.append(sum(differences[rng.randrange(n)] for _ in range(n)) / n)
            samples.sort()
            interval = [quantile(samples, 0.025), quantile(samples, 0.975)]
            excludes_zero = interval[0] > 0 or interval[1] < 0
            contrasts.append({"cell_id": cell, "family": family,
                              "left": {"mode": a[0], "branch": a[1]},
                              "right": {"mode": b[0], "branch": b[1]},
                              "n_matched_histories": n, "difference_left_minus_right": mean,
                              "discordant_left_failure_only": differences.count(1),
                              "discordant_right_failure_only": differences.count(-1),
                              "bootstrap_percentile_95_pointwise": interval,
                              "interval_excludes_zero": excludes_zero,
                              "promotion_trigger_met": abs(mean) >= 0.05 and excludes_zero})

    triggers = [x for x in contrasts if x["promotion_trigger_met"]]
    result = {
        "schema_version": 1,
        "status": "finite_pilot_trigger_met" if triggers else "finite_pilot_unresolved",
        "phase": "J6B registered paired whole-history analysis",
        "claim_boundary": manifest["claim_boundary"],
        "manifest_sha256": EXPECTED_MANIFEST,
        "integrity_result_sha256": digest(INTEGRITY),
        "raw_rows_sha256": EXPECTED_ROWS,
        "denominator": "All 128 independent matched histories per stochastic cell and arm; aborts and unresolved handoffs are failures",
        "uncertainty": {"arm": "pointwise 95% Wilson score interval",
                         "paired": "pointwise 95% percentile bootstrap of whole matched histories",
                         "seed": BOOTSTRAP_SEED, "replicates_per_contrast": REPLICATES,
                         "simultaneous_coverage": False, "contrasts": len(contrasts)},
        "arm_risks": arm_risks,
        "paired_contrasts": contrasts,
        "promotion_trigger_count": len(triggers),
        "interpretation": ("At least one registered contrast meets the exploratory proposal trigger; no superiority or threshold claim."
                           if triggers else "No registered contrast meets the exploratory proposal trigger; finite pilot remains unresolved, not equivalent."),
        "limitations": ["L=2 and five rounds only", "phenomenological/projector-level D4 model",
                         "high unconditional failure rates include retained failed-closed temporal handoffs",
                         "pointwise intervals are not multiple-comparison adjusted",
                         "no J6 pooling, crossing, scaling, threshold or universal JIT advantage"],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "contrasts": len(contrasts),
                      "replicates_per_contrast": REPLICATES,
                      "promotion_trigger_count": len(triggers)}))


if __name__ == "__main__":
    main()
