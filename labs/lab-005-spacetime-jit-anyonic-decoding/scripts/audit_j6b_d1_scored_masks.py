#!/usr/bin/env python3
"""Frozen J6B scored-path mask and commit-timing audit; no new inference."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6b-d1-scored-mask-timing-audit-2026-09-23.json"
OUTPUT = LAB / "results/j6b-d1-scored-mask-timing-audit-2026-09-23.json"
OUTCOMES = ("failed_closed", "scored_failure", "scored_success")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def insist(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def mask_and_outcome(row: dict, flags: list[str]) -> tuple[str | None, str]:
    insist(row["denominator_included"] is True, "excluded row")
    insist(type(row["logical_failure"]) is bool, "non-Boolean loss")
    if row["status"] == "failed_closed":
        insist(row["logical_failure"] is True, "failed-closed nonfailure")
        return None, "failed_closed"
    insist(row["status"] == "scored", "unknown status")
    bits = []
    for flag in flags:
        insist(type(row[flag]) is bool, f"non-Boolean {flag}")
        bits.append("1" if row[flag] else "0")
    mask = "".join(bits)
    insist(row["logical_failure"] == (mask != "0000"), "scored Boolean-union mismatch")
    return mask, "scored_failure" if row["logical_failure"] else "scored_success"


def main() -> None:
    start = time.process_time()
    insist(not OUTPUT.exists(), "output exists; no silent rerun")
    contract = json.loads(CONTRACT.read_text())
    input_hashes = {}
    for name, item in contract["frozen_inputs"].items():
        path = LAB / item["path"]
        actual = sha256(path)
        insist(actual == item["sha256"], f"{name} hash mismatch")
        input_hashes[name] = {"path": item["path"], "sha256": actual}
    d0 = json.loads((LAB / contract["frozen_inputs"]["d0"]["path"]).read_text())
    paired = json.loads((LAB / contract["frozen_inputs"]["paired"]["path"]).read_text())
    insist(d0["status"] == contract["frozen_inputs"]["d0"]["required_status"], "D0 not passed")
    insist(len(paired["paired_contrasts"]) == len(d0["per_registered_online_contrast"]) == 14,
           "paired contrast count mismatch")
    flags = contract["scope"]["scored_mask_bit_order"]
    insist(flags == ["physical_winding", "union_winding", "charge_winding", "terminal_residual"],
           "mask convention changed")
    raw_rows = [json.loads(line) for line in
                (LAB / contract["frozen_inputs"]["rows"]["path"]).read_text().splitlines()]
    insist(len(raw_rows) == 2176, "raw row count")
    cells = contract["scope"]["cells"]
    modes = contract["scope"]["modes"]
    branches = contract["scope"]["schedules"]
    legal_rounds = set(contract["scope"]["legal_physical_commit_rounds"])
    by_history: dict[tuple[str, int], dict[tuple[str, str], dict]] = defaultdict(dict)
    for row in raw_rows:
        cell = row["cell_id"]
        insist(cell in cells or cell == "zero_control", "unexpected cell")
        arm = (row["mode"], row["branch"])
        insist(arm[0] in modes and arm[1] in branches, "unexpected arm")
        count = row["unique_commit_count"]
        rounds = row["commit_rounds"]
        insist(type(count) is int and count >= 0 and count == len(rounds), "physical-commit count mismatch")
        insist(all(type(r) is int and r in legal_rounds for r in rounds), "invalid physical-commit round")
        insist(type(row["invocation_count"]) is int and row["invocation_count"] >= count,
               "invocation/commit count mismatch")
        mask_and_outcome(row, flags)
        group = by_history[(cell, row["history_index"])]
        insist(arm not in group, "duplicate arm")
        group[arm] = row
    insist(len(by_history) == 272, "history count mismatch")
    expected_arms = {(m, b) for m in modes for b in branches}
    for cell in ("zero_control", *cells):
        n = 16 if cell == "zero_control" else 128
        insist({h for c, h in by_history if c == cell} == set(range(n)), "history index gap")
        for h in range(n):
            group = by_history[(cell, h)]
            insist(set(group) == expected_arms, "incomplete arm set")
            if cell == "zero_control":
                insist(all(mask_and_outcome(row, flags) == ("0000", "scored_success")
                           for row in group.values()), "zero-control mask failure")

    previous_arms = {(r["cell_id"], r["mode"], r["branch"]): r for r in d0["per_arm"]}
    per_arm = []
    for cell in cells:
        for mode in modes:
            for branch in branches:
                arm_rows = [by_history[(cell, h)][(mode, branch)] for h in range(128)]
                masks = Counter()
                outcomes = Counter()
                timings = {name: {"unique_commit_count": Counter(), "invocation_count": Counter(),
                                  "physical_commit_rounds": Counter()} for name in OUTCOMES}
                for row in arm_rows:
                    mask, outcome = mask_and_outcome(row, flags)
                    outcomes[outcome] += 1
                    if mask is not None:
                        masks[mask] += 1
                    timings[outcome]["unique_commit_count"][str(row["unique_commit_count"])] += 1
                    timings[outcome]["invocation_count"][str(row["invocation_count"])] += 1
                    timings[outcome]["physical_commit_rounds"].update(str(r) for r in row["commit_rounds"])
                insist(sum(outcomes.values()) == 128 and sum(masks.values()) == 128 - outcomes["failed_closed"],
                       "arm mask/outcome mass balance")
                old = previous_arms[(cell, mode, branch)]["outcome_counts"]
                insist(all(old[name] == outcomes[name] for name in OUTCOMES), "D0 arm mismatch")
                for outcome in OUTCOMES:
                    insist(sum(timings[outcome]["unique_commit_count"].values()) == outcomes[outcome],
                           "commit-count histogram mismatch")
                    insist(sum(timings[outcome]["invocation_count"].values()) == outcomes[outcome],
                           "invocation histogram mismatch")
                    expected_commits = sum(int(k) * v for k, v in
                                           timings[outcome]["unique_commit_count"].items())
                    insist(sum(timings[outcome]["physical_commit_rounds"].values()) == expected_commits,
                           "commit-round histogram mismatch")
                per_arm.append({"cell_id": cell, "mode": mode, "branch": branch, "denominator": 128,
                                "outcome_counts": {k: outcomes[k] for k in OUTCOMES},
                                "scored_mask_counts": {k: masks[k] for k in sorted(masks)},
                                "scored_failures_with_terminal_residual": sum(v for k, v in masks.items()
                                                                              if k != "0000" and k[3] == "1"),
                                "scored_failures_without_terminal_residual": sum(v for k, v in masks.items()
                                                                                 if k != "0000" and k[3] == "0"),
                                "timing_by_outcome": {name: {field: dict(sorted(hist.items()))
                                                              for field, hist in timings[name].items()}
                                                      for name in OUTCOMES}})

    previous_pairs = {(r["cell_id"], r["left"]["mode"], r["left"]["branch"],
                       r["right"]["mode"], r["right"]["branch"]): r
                      for r in d0["per_registered_online_contrast"]}
    paired_masks = []
    for contrast in paired["paired_contrasts"]:
        cell = contrast["cell_id"]
        left = (contrast["left"]["mode"], contrast["left"]["branch"])
        right = (contrast["right"]["mode"], contrast["right"]["branch"])
        insist(cell in cells and left[1] != "offline_full_history" and right[1] != "offline_full_history",
               "unregistered paired branch")
        transitions = Counter()
        outcome_pairs = Counter()
        for h in range(128):
            lm, lo = mask_and_outcome(by_history[(cell, h)][left], flags)
            rm, ro = mask_and_outcome(by_history[(cell, h)][right], flags)
            outcome_pairs[(lo, ro)] += 1
            if lm is not None and rm is not None:
                transitions[f"{lm}>{rm}"] += 1
        old = previous_pairs[(cell, *left, *right)]["matched_outcome_table"]
        insist(all(outcome_pairs[(a, b)] == old[a][b] for a in OUTCOMES for b in OUTCOMES),
               "D0 paired-outcome mismatch")
        both_scored = sum(outcome_pairs[(a, b)] for a in OUTCOMES[1:] for b in OUTCOMES[1:])
        insist(sum(transitions.values()) == both_scored and sum(outcome_pairs.values()) == 128,
               "paired mask mass balance")
        paired_masks.append({"cell_id": cell, "left": contrast["left"], "right": contrast["right"],
                             "denominator": 128, "both_scored_histories": both_scored,
                             "either_failed_closed_histories": 128 - both_scored,
                             "sparse_scored_mask_transitions": dict(sorted(transitions.items())),
                             "original_proposal_trigger_met": contrast["promotion_trigger_met"]})
    elapsed = time.process_time() - start
    insist(elapsed <= contract["budget"]["max_cpu_seconds"], "CPU cap exceeded")
    result = {"schema_version": 1, "status": "passed_descriptive_scored_mask_timing_only",
              "contract_sha256": sha256(CONTRACT), "input_hashes": input_hashes,
              "mask_bit_order": flags, "per_arm": per_arm,
              "per_registered_online_contrast": paired_masks,
              "checks": {"histories": len(by_history), "rows": len(raw_rows),
                         "stochastic_arms": len(per_arm), "online_contrasts": len(paired_masks),
                         "all_mask_timing_and_pair_balances_passed": True},
              "resource_use": {"cpu_seconds": elapsed, "output_bytes": 0},
              "claim_boundary": contract["claim_boundary"]}
    for _ in range(4):
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        result["resource_use"]["output_bytes"] = len(encoded.encode())
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    insist(result["resource_use"]["output_bytes"] == len(encoded.encode()), "output-size accounting")
    insist(len(encoded.encode()) <= contract["budget"]["max_output_mib"] * 1024**2,
           "output size cap exceeded")
    OUTPUT.write_text(encoded)
    print(json.dumps({"status": result["status"], "rows": len(raw_rows),
                      "arms": len(per_arm), "contrasts": len(paired_masks)}))


if __name__ == "__main__":
    main()
