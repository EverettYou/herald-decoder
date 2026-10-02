"""Fail-closed structural audit of action feedback in the frozen J6 model."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6-model-sufficiency-review-2026-09-24.json"
RESULT = LAB / "results/j6-model-sufficiency-review-2026-09-24.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(found) == 1, f"missing or duplicate function {name}")
    return found[0]


def calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [item for item in ast.walk(node) if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name) and item.func.id == name]


def main() -> int:
    started = time.process_time()
    require(not RESULT.exists(), "review result exists; no silent rerun")
    contract = json.loads(CONTRACT.read_text())
    result = {
        "schema_version": 1, "contract_sha256": sha(CONTRACT),
        "status": "censored", "reason": None,
        "new_stochastic_histories": 0, "new_arm_evaluations": 0,
        "new_bootstrap_replicates": 0, "checks": {},
        "claim_boundary": contract["claim_boundary"],
    }
    try:
        for item in contract["frozen_inputs"].values():
            require(sha(LAB / item["path"]) == item["sha256"], f"frozen input drift: {item['path']}")
        source = (LAB / contract["frozen_inputs"]["integrated_source"]["path"]).read_text()
        tree = ast.parse(source)
        build = function(tree, "build_integrated_d4_history_from_draws")
        generate = function(tree, "generate_integrated_d4_history")
        second = function(tree, "provide_action_conditioned_second_record")
        evaluate = function(tree, "evaluate_history_matrix")
        score = function(tree, "evaluate_schedule_arm")
        build_args = [arg.arg for arg in build.args.kwonlyargs]
        generate_args = [arg.arg for arg in generate.args.kwonlyargs]
        build_source = ast.get_source_segment(source, build)
        second_source = ast.get_source_segment(source, second)
        score_source = ast.get_source_segment(source, score)
        require(build_source is not None and second_source is not None and score_source is not None,
                "source segment unavailable")
        physical_update = [node for node in ast.walk(build) if isinstance(node, ast.Assign)
                           and ast.get_source_segment(source, node) and
                           "physical[round_index] = physical[round_index - 1] ^ faults[round_index - 1]"
                           in ast.get_source_segment(source, node)]
        project_calls = calls(build, "project_hidden_state")
        no_action_to_history = (
            "action" not in build_args and "invocation" not in build_args
            and "action" not in generate_args and "invocation" not in generate_args
            and len(physical_update) == 1
            and len(project_calls) == 1
            and all(key.arg != "bound_action_digest" for key in project_calls[0].keywords)
            and len(calls(build, "build_record_from_fault_masks")) == 1
            and not calls(build, "run_e1_policy_matrix")
        )
        require(no_action_to_history, "history-generation dependency differs from registered A/B fork")
        same_round_action_binding = (
            "invocation.flux_action.action_digest" in second_source
            and "second_exogenous_key" in second_source
            and "return ActionConditionedSecondRecordV1(" in second_source
            and "return IntegratedD4HistoryV1(" not in second_source
            and not calls(second, "build_record_from_fault_masks")
        )
        require(same_round_action_binding, "same-round E2 action binding unresolved")
        schedule_after_history = (
            "history" in [arg.arg for arg in evaluate.args.args]
            and len(calls(evaluate, "run_e1_policy_matrix")) == 1
            and not calls(build, "run_e1_policy_matrix")
        )
        require(schedule_after_history, "schedule/history dependency order unresolved")
        latest_frame_score = (
            "history.physical_edge_states[-1]" in score_source
            and "physical_commits[-1].flux_action.correction_edges" in score_source
            and "final_physical ^ final_correction" in score_source
        )
        require(latest_frame_score, "private last-frame score dependency unresolved")
        d2 = json.loads((LAB / contract["frozen_inputs"]["d2_fixture"]["path"]).read_text())
        d4 = json.loads((LAB / contract["frozen_inputs"]["d4_cohort_audit"]["path"]).read_text())
        require(d2["status"] == "passed_deterministic_interface_only" and len(d2["fixtures"]) == 5,
                "D2 accepted fixture status/coverage drift")
        require(d4["status"] == "passed_frozen_cohort_descriptive_overlap_only"
                and d4["checks"]["stochastic_histories"] == 256,
                "D4 accepted frozen-cohort status/coverage drift")
        divergent = []
        for fixture in d2["fixtures"]:
            arms = [arm for arm in fixture["arms"] if arm["mode"] == "syndrome_only"
                    and arm["branch"] in ("immediate", "fixed_delay_1", "jit_lyons_brown")]
            require(len(arms) == 3 and "final_physical_edges" in fixture
                    and "visible_history_digest" in fixture, "D2 shared-history fixture incomplete")
            paths = {(tuple(arm["commit_rounds"]), tuple(arm["latest_public_correction_edges"]))
                     for arm in arms}
            if len(paths) > 1:
                divergent.append(fixture["fixture_id"])
        require(divergent, "D2 lacks a nontrivial within-history schedule intervention")
        for item in contract["frozen_inputs"].values():
            require(sha(LAB / item["path"]) == item["sha256"], "frozen input drift after audit")
        result["checks"] = {
            "history_generation_action_argument_absent": True,
            "physical_chain_precomputed_from_exogenous_faults": True,
            "hidden_projector_update_has_no_bound_action": True,
            "public_first_record_built_before_schedule_evaluation": True,
            "same_round_action_conditioned_E2_present": True,
            "E2_returns_completion_not_next_hidden_history": True,
            "private_final_loss_uses_latest_public_frame": True,
            "accepted_D2_fixtures_with_distinct_online_actions_and_shared_history": divergent,
            "accepted_D4_stochastic_histories": 256,
            "accepted_D4_unconditional_JIT_rows": 512,
        }
        result["classification"] = {
            "implemented_path": "exogenous_faults_to_hidden_chain_and_first_record; causal_schedule_to_same_round_E2_and_latest_frame_score",
            "absent_path": "prior_public_action_to_future_hidden_anyon_or_projector_state_or_future_first_record",
            "identifiable_now": "finite-size causal timing/readout behavior under one precomputed exogenous history and its private score",
            "not_identifiable_now": "whether earlier active correction prevents later non-Abelian charge hiding or reveals absorbed anyons",
            "interpretation": "The missing path is an implemented-model limit, not a finding that JIT physics has no benefit. Existing J6B finite-pilot facts remain at their registered scope.",
        }
        result["status"] = "passed_structural_model_limit_only"
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}:{exc}"
        result.pop("classification", None)
    result["cpu_seconds"] = round(time.process_time() - started, 5)
    if result["cpu_seconds"] > contract["budget"]["max_cpu_seconds"]:
        result.update(status="censored", reason="registered CPU cap exceeded")
        result.pop("classification", None)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "reason": result["reason"],
                      "cpu_seconds": result["cpu_seconds"]}))
    return 0 if result["status"] == "passed_structural_model_limit_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
