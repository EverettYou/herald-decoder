#!/usr/bin/env python3
"""Read-only, preregistered post-hoc outcome accounting for frozen J6B rows."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6b-d0-frozen-outcome-attribution-2026-09-23.json"
OUTPUT = LAB / "results/j6b-d0-frozen-outcome-attribution-2026-09-23.json"
CATEGORIES = ("failed_closed", "scored_failure", "scored_success")
FLAGS = ("physical_winding", "union_winding", "charge_winding", "terminal_residual")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def category(row: dict) -> str:
    if row["status"] == "failed_closed":
        require(row["logical_failure"] is True, "failed-closed row not a failure")
        return "failed_closed"
    require(row["status"] == "scored", "unknown score status")
    require(type(row["logical_failure"]) is bool, "non-Boolean logical score")
    require(row["logical_failure"] == any(row[flag] for flag in FLAGS), "scored Boolean-union mismatch")
    return "scored_failure" if row["logical_failure"] else "scored_success"


def main() -> None:
    start = time.process_time()
    require(not OUTPUT.exists(), "output already exists; no silent rerun")
    contract = json.loads(CONTRACT.read_text())
    frozen = {}
    for name, spec in contract["frozen_inputs"].items():
        path = LAB / spec["path"]
        actual = sha256(path)
        require(actual == spec["sha256"], f"{name} input hash mismatch")
        frozen[name] = {"path": spec["path"], "sha256": actual}
    integrity = json.loads((LAB / contract["frozen_inputs"]["integrity"]["path"]).read_text())
    paired = json.loads((LAB / contract["frozen_inputs"]["paired_analysis"]["path"]).read_text())
    require(integrity["status"] == contract["frozen_inputs"]["integrity"]["required_status"], "integrity status")
    require(integrity["integrity_passed"] and not integrity["integrity_failures"], "integrity failed")
    require(paired["status"] == contract["frozen_inputs"]["paired_analysis"]["required_status"], "paired status")
    require(len(paired["paired_contrasts"]) == 14, "contrast count")
    require(paired["raw_rows_sha256"] == frozen["rows"]["sha256"], "paired raw-row binding")

    row_path = LAB / contract["frozen_inputs"]["rows"]["path"]
    rows = [json.loads(line) for line in row_path.read_text().splitlines()]
    require(len(rows) == 2176, "row count")
    by_history: dict[tuple[str, int], dict[tuple[str, str], dict]] = defaultdict(dict)
    modes = contract["scope"]["modes"]
    branches = contract["scope"]["schedules"]
    cells = contract["scope"]["cells"]
    for row in rows:
        require(row["denominator_included"] is True, "denominator exclusion")
        require(row["mode"] in modes and row["branch"] in branches, "unregistered arm")
        require(row["cell_id"] in cells or row["cell_id"] == "zero_control", "unregistered cell")
        arm = (row["mode"], row["branch"])
        history = by_history[(row["cell_id"], row["history_index"])]
        require(arm not in history, "duplicate arm row")
        category(row)
        history[arm] = row
    require(len(by_history) == 272, "history count")
    for cell in ("zero_control", *cells):
        expected = 16 if cell == "zero_control" else 128
        require({h for c, h in by_history if c == cell} == set(range(expected)), f"{cell} history indexes")
        for h in range(expected):
            group = by_history[(cell, h)]
            require(set(group) == {(m, b) for m in modes for b in branches}, "incomplete arm set")

    per_arm = []
    for cell in cells:
        for mode in modes:
            for branch in branches:
                arm_rows = [by_history[(cell, h)][(mode, branch)] for h in range(128)]
                counts = Counter(category(row) for row in arm_rows)
                require(sum(counts.values()) == 128, "arm mass balance")
                require(counts["failed_closed"] + counts["scored_failure"] ==
                        sum(row["logical_failure"] for row in arm_rows), "arm loss balance")
                reasons = Counter(row["failure_reason"] for row in arm_rows
                                  if category(row) == "failed_closed")
                flag_counts = {flag: sum(row[flag] for row in arm_rows
                                         if category(row) == "scored_failure") for flag in FLAGS}
                per_arm.append({"cell_id": cell, "mode": mode, "branch": branch,
                                "denominator": 128, "outcome_counts": {key: counts[key] for key in CATEGORIES},
                                "failed_closed_reasons": dict(sorted(reasons.items())),
                                "scored_failure_flag_counts_overlapping": flag_counts})

    per_contrast = []
    for prior in paired["paired_contrasts"]:
        cell = prior["cell_id"]
        left = (prior["left"]["mode"], prior["left"]["branch"])
        right = (prior["right"]["mode"], prior["right"]["branch"])
        require(cell in cells and left[1] != "offline_full_history" and right[1] != "offline_full_history",
                "non-online or unexpected contrast")
        table = Counter((category(by_history[(cell, h)][left]),
                         category(by_history[(cell, h)][right])) for h in range(128))
        left_counts = Counter(category(by_history[(cell, h)][left]) for h in range(128))
        right_counts = Counter(category(by_history[(cell, h)][right]) for h in range(128))
        require(sum(table.values()) == 128, "paired table mass balance")
        require(all(sum(table[(a, b)] for b in CATEGORIES) == left_counts[a] for a in CATEGORIES),
                "left table marginal mismatch")
        require(all(sum(table[(a, b)] for a in CATEGORIES) == right_counts[b] for b in CATEGORIES),
                "right table marginal mismatch")
        abort_delta = left_counts["failed_closed"] - right_counts["failed_closed"]
        scored_delta = left_counts["scored_failure"] - right_counts["scored_failure"]
        total_delta = abort_delta + scored_delta
        require(total_delta / 128 == prior["difference_left_minus_right"], "paired estimate decomposition mismatch")
        left_only = sum(table[(a, "scored_success")] for a in CATEGORIES if a != "scored_success")
        right_only = sum(table[("scored_success", b)] for b in CATEGORIES if b != "scored_success")
        require(left_only == prior["discordant_left_failure_only"], "left discordance mismatch")
        require(right_only == prior["discordant_right_failure_only"], "right discordance mismatch")
        per_contrast.append({"cell_id": cell, "family": prior["family"],
                             "left": prior["left"], "right": prior["right"],
                             "denominator": 128,
                             "matched_outcome_table": {a: {b: table[(a, b)] for b in CATEGORIES}
                                                       for a in CATEGORIES},
                             "left_minus_right_failed_closed_count": abort_delta,
                             "left_minus_right_scored_failure_count": scored_delta,
                             "left_minus_right_total_failure_count": total_delta,
                             "original_point_difference": prior["difference_left_minus_right"],
                             "original_proposal_trigger_met": prior["promotion_trigger_met"]})

    elapsed = time.process_time() - start
    require(elapsed <= contract["budget"]["max_cpu_seconds"], "CPU budget exceeded")
    result = {"schema_version": 1, "status": "passed_descriptive_accounting_only",
              "contract_sha256": sha256(CONTRACT), "frozen_inputs": frozen,
              "scope": "Existing J6B L=2 five-round matched histories; no new sampling, bootstrap, or risk test",
              "outcome_categories": list(CATEGORIES),
              "per_arm": per_arm, "per_registered_online_contrast": per_contrast,
              "checks": {"histories": len(by_history), "rows": len(rows),
                         "stochastic_arms": len(per_arm), "online_contrasts": len(per_contrast),
                         "all_mass_balances_passed": True},
              "resource_use": {"cpu_seconds": elapsed, "output_bytes": 0},
              "claim_boundary": contract["claim_boundary"]}
    for _ in range(4):
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        result["resource_use"]["output_bytes"] = len(encoded.encode())
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    require(result["resource_use"]["output_bytes"] == len(encoded.encode()), "size accounting mismatch")
    require(len(encoded.encode()) <= contract["budget"]["max_output_mib"] * 1024**2,
            "output budget exceeded")
    OUTPUT.write_text(encoded)
    print(json.dumps({"status": result["status"], "rows": len(rows),
                      "arms": len(per_arm), "contrasts": len(per_contrast)}))


if __name__ == "__main__":
    main()
