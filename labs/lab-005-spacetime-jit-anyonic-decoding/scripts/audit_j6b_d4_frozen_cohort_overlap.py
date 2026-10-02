"""Exact replay and descriptive overlap accounting on the immutable J6B cohort."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import time

from replay_j6b_d3_selected_histories import LAB, sha, trace_case


CONTRACT = LAB / "manifests/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json"
RESULT = LAB / "results/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json"
CELLS = ("clean_herald_schedule", "joint_readout_noise")
MODES = ("syndrome_only", "heralded")
BRANCHES = ("immediate", "fixed_delay_1", "jit_lyons_brown", "offline_full_history")
OUTCOMES = ("failed_closed", "scored_failure", "scored_success")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_rows(contract: dict) -> dict:
    path = LAB / contract["frozen_inputs"]["j6b_rows"]["path"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    require(len(rows) == 2176, "frozen raw row count")
    by_key = {}
    for row in rows:
        key = (row["trial_id"], row["mode"], row["branch"])
        require(key not in by_key, "duplicate original arm")
        require(row["denominator_included"] is True, "excluded original arm")
        require(row["status"] in ("scored", "failed_closed"), "unknown original status")
        require(row["status"] != "failed_closed" or row["logical_failure"] is True,
                "failed-closed original arm is not a Boolean loss")
        by_key[key] = row
    for cell, n in (("zero_control", 16), (CELLS[0], 128), (CELLS[1], 128)):
        for h in range(n):
            trial = f"j6b-{cell}-{h:04d}"
            require({(mode, branch) for (t, mode, branch) in by_key if t == trial}
                    == {(m, b) for m in MODES for b in BRANCHES},
                    f"incomplete original history: {trial}")
    return by_key


def outcome(row: dict) -> str:
    if row["status"] == "failed_closed":
        return "failed_closed"
    return "scored_failure" if row["logical_failure"] else "scored_success"


def flag_mask(arm: dict) -> str:
    require(arm["stored_status"] == "scored", "flags require scored row")
    no_commit = arm["last_commit_round"] is None
    later = arm["physical_transition_after_last_commit"]
    mismatch = arm["private_public_readout_mismatch_at_last_commit"]
    residual_at_commit = arm["residual_immediately_after_last_commit"]
    require(not no_commit or not (later or mismatch or residual_at_commit),
            "no-commit row has inapplicable commit flags")
    return "".join("1" if bit else "0" for bit in
                   (no_commit, later, mismatch, residual_at_commit))


def main() -> int:
    started = time.monotonic()
    require(not RESULT.exists(), "result exists; immutable audit cannot silently rerun")
    contract = json.loads(CONTRACT.read_text())
    result = {
        "schema_version": 1, "status": "censored", "reason": None,
        "contract_sha256": sha(CONTRACT),
        "new_stochastic_seeds": 0, "new_unique_production_histories": 0,
        "new_unique_production_arm_rows": 0, "new_bootstrap_replicates": 0,
        "replayed_existing_histories": 0, "replayed_existing_arm_rows": 0,
        "flag_bit_order": contract["scope"]["flags"],
        "per_cell_mode": [], "checks": {}, "claim_boundary": contract["claim_boundary"],
    }
    try:
        for item in contract["frozen_inputs"].values():
            require(sha(LAB / item["path"]) == item["sha256"], f"frozen hash: {item['path']}")
        frozen = load_rows(contract)
        d1 = json.loads((LAB / contract["frozen_inputs"]["d1"]["path"]).read_text())
        d3 = json.loads((LAB / contract["frozen_inputs"]["d3"]["path"]).read_text())
        d1_jit = {(x["cell_id"], x["mode"]): x for x in d1["per_arm"]
                  if x["branch"] == "jit_lyons_brown"}
        d3_jit = {(x["trial_id"], arm["mode"]): arm for x in d3["cases"]
                  for arm in x["arms"] if arm["branch"] == "jit_lyons_brown"}
        counts = {(cell, mode): {"outcomes": Counter(), "scored_flag_masks": Counter(),
                                 "failure_flag_masks": Counter(), "success_flag_masks": Counter(),
                                 "last_commit_round": Counter()}
                  for cell in CELLS for mode in MODES}
        selected_checked = 0
        for cell in CELLS:
            for h in range(128):
                trial = f"j6b-{cell}-{h:04d}"
                case = {"trial_id": trial, "cell_id": cell, "history_index": h,
                        "stratum": "full_frozen_cohort"}
                trace = trace_case(contract, case, frozen)
                require(len(trace["arms"]) == 8, "incomplete replayed arm set")
                for mode in MODES:
                    arm = next(x for x in trace["arms"] if x["mode"] == mode
                               and x["branch"] == "jit_lyons_brown")
                    row = frozen[(trial, mode, "jit_lyons_brown")]
                    key = (cell, mode)
                    label = outcome(row)
                    counts[key]["outcomes"][label] += 1
                    if label != "failed_closed":
                        mask = flag_mask(arm)
                        counts[key]["scored_flag_masks"][mask] += 1
                        counts[key]["failure_flag_masks" if label == "scored_failure"
                                    else "success_flag_masks"][mask] += 1
                        counts[key]["last_commit_round"]["none" if arm["last_commit_round"] is None
                                                         else str(arm["last_commit_round"])] += 1
                    if (trial, mode) in d3_jit:
                        old = d3_jit[(trial, mode)]
                        for field in ("last_commit_round", "physical_transition_after_last_commit",
                                      "private_public_readout_mismatch_at_last_commit",
                                      "residual_immediately_after_last_commit", "stored_status",
                                      "stored_logical_failure", "stored_terminal_residual"):
                            require(arm[field] == old[field], f"selected D3 flag drift: {trial}:{mode}:{field}")
                        selected_checked += 1
                result["replayed_existing_histories"] += 1
                result["replayed_existing_arm_rows"] += 8
                require(time.monotonic() - started <= contract["budget"]["max_wall_seconds"],
                        "registered wall-time cap")
        require(len(frozen) == 2176 and selected_checked == 16, "frozen/selected coverage")
        for (cell, mode), item in counts.items():
            outcomes = item["outcomes"]
            old = d1_jit[(cell, mode)]["outcome_counts"]
            require(all(outcomes[name] == old[name] for name in OUTCOMES),
                    f"D1 outcome mismatch: {cell}/{mode}")
            require(sum(outcomes.values()) == 128, "unconditional denominator drift")
            require(sum(item["scored_flag_masks"].values()) ==
                    outcomes["scored_failure"] + outcomes["scored_success"],
                    "scored-mask mass balance")
            require(sum(item["failure_flag_masks"].values()) == outcomes["scored_failure"]
                    and sum(item["success_flag_masks"].values()) == outcomes["scored_success"],
                    "outcome-mask mass balance")
            result["per_cell_mode"].append({
                "cell_id": cell, "mode": mode, "unconditional_denominator": 128,
                "outcome_counts": {name: outcomes[name] for name in OUTCOMES},
                **{name: dict(sorted(item[name].items())) for name in
                   ("scored_flag_masks", "failure_flag_masks", "success_flag_masks", "last_commit_round")},
            })
        for item in contract["frozen_inputs"].values():
            require(sha(LAB / item["path"]) == item["sha256"], "frozen input changed after replay")
        result["checks"] = {"original_rows": len(frozen), "stochastic_histories": 256,
                            "stochastic_arm_rows": 2048, "jit_rows": 512,
                            "selected_d3_jit_arms_checked": selected_checked,
                            "exact_replay_private_public_action_binding_and_d1_balance": True}
        result["status"] = "passed_frozen_cohort_descriptive_overlap_only"
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}:{exc}"
        result["per_cell_mode"] = []
    result["elapsed_seconds"] = round(time.monotonic() - started, 4)
    if result["elapsed_seconds"] > contract["budget"]["max_wall_seconds"]:
        result.update(status="censored", reason="registered wall-time cap exceeded", per_cell_mode=[])
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if len(encoded.encode()) > contract["budget"]["max_result_mib"] * 1024**2:
        result.update(status="censored", reason="registered result-size cap exceeded", per_cell_mode=[])
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    RESULT.write_text(encoded)
    print(json.dumps({"status": result["status"], "reason": result["reason"],
                      "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["status"] == "passed_frozen_cohort_descriptive_overlap_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
