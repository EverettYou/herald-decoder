#!/usr/bin/env python3
"""Register a no-new-data two-branch acquisition matrix for Phase B14."""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
BASE_PATH = LAB_DIR / "results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
EVIDENCE_PATH = LAB_DIR / "results/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.json"
SELECTION_PATH = LAB_DIR / "results/phase-b14-honeycomb-two-branch-selection-2026-08-28.json"
MANIFEST_PATH = LAB_DIR / "phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json"
EXPECTED_HASHES = {
    BASE_PATH.name: "8692b610ee6e19bb45452494b04c8c45b4d1fb31f240a8c10dd2f81c24c254bf",
    EVIDENCE_PATH.name: "51084739a016db8ff8f2eb2c27c68119491ad0edd30b183264a4058561583d7c",
}
LOW_Q_RANGE = (0.0, 0.4)
HIGH_Q_RANGE = (0.6, 0.8)
P_MAX = 0.32
LER_RANGE = (0.05, 0.45)
MIN_SIGN_ENTROPY_NATS = 0.5
DISTANCE_SEEDS = [891001, 891002, 891003, 891004, 891005]
PRECISION_SEEDS = [892001, 892002, 892003, 892004, 892005]
SHOTS_PER_SEED = 100
REQUIRED_SOURCE_HASHES = {
    "runner": "14adf7579825e64fa4dd74a6ff374207c3f7b55349b5b533c1ff054bf6d66474",
    "lattice_model": "b87a5feba27675e26970360d730324b7d3740e4dc0492b4dc478e510f140c9e7",
    "decoder": "990af03ac4c99684e9e9dac6e5a8bb64d773015879c1638906f5fb592cdc6a43",
    "damping_decoder": "a08ddf0b58e63bb2627c35cafbe570fe6a0ee8dc21bd4eaca720d6dbcbc5e182",
    "numba_kernels": "c2254c95600c4f5e3a8c2279d5686a99c8d3810a4bb0c814a4fd0cbf16c184cc",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_hash(path: Path) -> str:
    """Hash scientific content while excluding B13's volatile generation time."""
    if path == EVIDENCE_PATH:
        payload = json.loads(path.read_text())
        payload.pop("generated_at", None)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()
    return sha256(path)


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def entropy(upward: float) -> float:
    downward = 1.0 - upward
    return -sum(value * math.log(value) for value in (upward, downward) if value > 0.0)


def base_cells(payload: dict) -> dict[tuple[float, float], dict]:
    cells = {}
    for analysis in payload["analyses"]:
        q = float(analysis["q"])
        for row in analysis["cells"]:
            p = float(row["p"])
            sizes = row.get("sizes") or ([7, 9, 11] if len(row.get("logical_errors", [])) == 3 else [])
            cells[(q, p)] = {**row, "q": q, "p": p, "sizes": sizes}
    return cells


def select_pairs(base: dict, evidence: dict) -> list[dict]:
    by_key = {(float(row["q"]), float(row["p"])): row for row in evidence["cells"]}
    candidates = {}
    for key, row in base.items():
        q, p = key
        current = by_key[key]
        if current["evidence_source"] != "phase_b9_base_grid" or row["sizes"] != [7, 9, 11]:
            continue
        mean_ler = sum(e / n for e, n in zip(row["logical_errors"], row["shots"])) / 3.0
        upward = float(current["posterior_probability_upward_trend"])
        sign_entropy = entropy(upward)
        if p > P_MAX or not (LER_RANGE[0] <= mean_ler <= LER_RANGE[1]) or sign_entropy < MIN_SIGN_ENTROPY_NATS:
            continue
        candidates[key] = {
            "q": q,
            "p": p,
            "sizes": [7, 9, 11],
            "logical_errors": row["logical_errors"],
            "shots": row["shots"],
            "mean_ler": mean_ler,
            "posterior_probability_upward_trend": upward,
            "posterior_probability_downward_trend": 1.0 - upward,
            "posterior_log_odds_upward_vs_downward": current["display_source_value"],
            "sign_entropy_nats": sign_entropy,
        }

    rows = []
    q_values = sorted({q for q, _ in candidates})
    for q in q_values:
        at_q = sorted((p, row) for (row_q, p), row in candidates.items() if row_q == q)
        for (left_p, left), (right_p, right) in zip(at_q[:-1], at_q[1:]):
            left_sign = left["posterior_log_odds_upward_vs_downward"]
            right_sign = right["posterior_log_odds_upward_vs_downward"]
            if left_sign * right_sign < 0:
                rows.append({
                    "q": q,
                    "p_pair": [left_p, right_p],
                    "cells": [left, right],
                    "combined_sign_entropy_nats": left["sign_entropy_nats"] + right["sign_entropy_nats"],
                })

    def best_in(q_range: tuple[float, float]) -> dict:
        eligible = [row for row in rows if q_range[0] <= row["q"] <= q_range[1]]
        if not eligible:
            raise ValueError(f"no eligible sign-contrast pair in q range {q_range}")
        return max(eligible, key=lambda row: (row["combined_sign_entropy_nats"], -row["q"]))

    selected = [best_in(LOW_Q_RANGE), best_in(HIGH_Q_RANGE)]
    keys = {(cell["q"], cell["p"]) for pair in selected for cell in pair["cells"]}
    if keys != {(0.2, 0.16), (0.2, 0.2), (0.7, 0.28), (0.7, 0.32)}:
        raise ValueError(f"Phase B14 deterministic selection drift: {sorted(keys)}")
    return selected


def build() -> tuple[dict, dict]:
    for path in (BASE_PATH, EVIDENCE_PATH):
        if evidence_hash(path) != EXPECTED_HASHES[path.name]:
            raise ValueError(f"Phase B14 source hash drift: {path.name}")
    base = json.loads(BASE_PATH.read_text())
    evidence = json.loads(EVIDENCE_PATH.read_text())
    pairs = select_pairs(base_cells(base), evidence)
    cells = [cell for pair in pairs for cell in pair["cells"]]
    jobs = []
    for cell in cells:
        for branch, sizes, seeds in (
            ("distance_leverage_L5_L13", [5, 13], DISTANCE_SEEDS),
            ("same_window_precision_L7_L9_L11", [7, 9, 11], PRECISION_SEEDS),
        ):
            jobs.append({
                "branch": branch,
                "q": cell["q"],
                "p": cell["p"],
                "sizes": sizes,
                "seeds": seeds,
                "shots_per_seed": SHOTS_PER_SEED,
                "expected_decodes": len(sizes) * len(seeds) * SHOTS_PER_SEED,
            })
    selection = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "registered_no_data_launched",
        "scientific_question": (
            "At moderate-LER lower-transition cells, does adding new distance leverage "
            "or adding same-window precision yield more posterior trend-sign information per decode?"
        ),
        "selection_rule": {
            "source": "current Phase B13 continuous trend evidence with Phase B9 count vectors",
            "required_current_sizes": [7, 9, 11],
            "mean_ler_range": list(LER_RANGE),
            "minimum_binary_sign_entropy_nats": MIN_SIGN_ENTROPY_NATS,
            "maximum_p": P_MAX,
            "required_within_row_neighbor_log_odds_sign_contrast": True,
            "q_strata": [list(LOW_Q_RANGE), list(HIGH_Q_RANGE)],
            "choice_within_stratum": "maximum combined sign entropy; lower q deterministic tie-break",
        },
        "selected_pairs": pairs,
        "selected_cell_count": 4,
        "branches": {
            "distance_leverage_L5_L13": "500 fresh shots at each previously unmeasured endpoint",
            "same_window_precision_L7_L9_L11": "500 fresh shots at each existing distance",
        },
        "jobs": jobs,
        "job_count": len(jobs),
        "expected_new_decodes": sum(row["expected_decodes"] for row in jobs),
        "new_data_launched": False,
        "phase_interpretation": None,
        "boundary_inference": None,
    }
    manifest = {
        "schema_version": 1,
        "status": "registered_preflight_required",
        "campaign": "phase-b14-honeycomb-two-branch-acquisition-2026-08-28",
        "purpose": "Empirically discriminate distance leverage from same-window precision without imposing a cross-size predictive model.",
        "sources": [
            {"path": str(BASE_PATH.relative_to(LAB_DIR)), "sha256": sha256(BASE_PATH), "hash_kind": "full_file_sha256"},
            {"path": str(EVIDENCE_PATH.relative_to(LAB_DIR)), "sha256": evidence_hash(EVIDENCE_PATH), "hash_kind": "canonical_json_excluding_generated_at"},
        ],
        "selection_evidence": {
            "path": str(SELECTION_PATH.relative_to(LAB_DIR)),
            "sha256": None,
        },
        "designer": {
            "path": str(Path(__file__).resolve().relative_to(LAB_DIR)),
            "sha256": sha256(Path(__file__).resolve()),
        },
        "lattice": "honeycomb",
        "jobs": jobs,
        "job_count": len(jobs),
        "workers_cap": 4,
        "expected_new_decodes": selection["expected_new_decodes"],
        "decoder": {
            "name": "HeraldAwareBpMatchingDecoder",
            "recurrence_mode": "damping",
            "damping": 0.25,
            "max_iterations": 80,
            "update_schedule": "residual_priority",
            "residual_priority_order": "stable_sort",
            "residual_priority_buffer_reuse": False,
            "residual_priority_cached_products": False,
            "matching_projection": "posterior_llr",
            "p_m": 0.0,
            "p_h": 0.0,
            "use_numba": True,
        },
        "required_source_hashes": REQUIRED_SOURCE_HASHES,
        "analysis_contract": {
            "primary": "posterior trend-sign entropy reduction in nats per 1000 new decodes",
            "secondary": "change in continuous log posterior odds and 90% slope interval",
            "branch_comparisons": ["distance_leverage_vs_base", "same_window_precision_vs_base", "combined_vs_base"],
            "cell_or_phase_classification": False,
            "boundary_inference": False,
        },
        "preflight_evidence_path": "results/phase-b14-honeycomb-two-branch-preflight-2026-08-28.json",
        "completion_evidence_path": "results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json",
        "analysis_evidence_path": "results/phase-b14-honeycomb-two-branch-analysis-2026-08-28.json",
        "stop_rule": "Stop after exactly eight jobs and 10000 decodes; no adaptive cell, p, q, size, branch, seed, or shot change.",
        "launch_gate": "requires_valid_preflight_artifact",
    }
    return selection, manifest


def main() -> None:
    selection, manifest = build()
    atomic_json(SELECTION_PATH, selection)
    manifest["selection_evidence"]["sha256"] = sha256(SELECTION_PATH)
    atomic_json(MANIFEST_PATH, manifest)
    print(json.dumps({
        "selection": str(SELECTION_PATH),
        "manifest": str(MANIFEST_PATH),
        "selected_cells": [(cell["q"], cell["p"]) for pair in selection["selected_pairs"] for cell in pair["cells"]],
        "job_count": selection["job_count"],
        "expected_new_decodes": selection["expected_new_decodes"],
        "new_data_launched": False,
    }, indent=2))


if __name__ == "__main__":
    main()
