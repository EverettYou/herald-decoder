#!/usr/bin/env python3
"""Bounded R6V schedule sensitivity on R6U's high-nonconvergence cells.

This is deliberately a *policy-sensitivity* control, not a new threshold
sample.  It regenerates the public records from frozen R6U seeds, so the
physical error and D4 observation are identical to the pilot.  BP schedules
alone change.  O2 is replayed once as the fixed comparator.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_belief_factorization import PublicD4Observation
from d4_honeycomb import paper_periodic_honeycomb
from d4_local_bp import build_r6d_dense_template, run_r6d_dense_template
from d4_matching import edge_chain_boundary, published_herald_weights
from d4_recovery import decode_and_score_flux_recovery
from d4_sampler import observation_from_error_edges
from run_r6n_default_flux_policy_comparison import llr_weights, trajectory_seeds


R6U = LAB_DIR / "results/r6u-d4-native-three-policy-curve-2026-08-30.json"
OUT = LAB_DIR / "results/r6v-r6u-nonconvergence-sensitivity-2026-08-30.json"
REPORT = LAB_DIR / "wiki/records/r6v-r6u-nonconvergence-sensitivity-2026-08-30.md"
CONFIGS = (
    {"id": "A_default_d025_cap40", "old_message_weight": 0.25, "max_iterations": 40, "tolerance": 1e-8},
    {"id": "B_extend_d025_cap160", "old_message_weight": 0.25, "max_iterations": 160, "tolerance": 1e-8},
    {"id": "C_damp_d050_cap160", "old_message_weight": 0.50, "max_iterations": 160, "tolerance": 1e-8},
)
# The first five nonconverged plus one converged trajectory from each of the
# two highest-R6U-nonconvergence cells.  This yields a bounded 12-record
# control while deliberately covering both high residual and near-tolerance
# nonconvergence.
CELLS = ((9, 0.22), (13, 0.22))
PER_CELL = 6


def select_indices(r6u: dict, size: int, p: float) -> list[int]:
    rows = [r for r in r6u["rows"] if r["size"] == size and r["p_X"] == p and r["status"] == "nonterminal"]
    bp = "R6D_local_BP_posterior_LLR_MWPM"
    nonconv = [r["trajectory_index"] for r in rows if not r["policies"][bp]["bp"]["converged"]]
    conv = [r["trajectory_index"] for r in rows if r["policies"][bp]["bp"]["converged"]]
    if len(nonconv) < PER_CELL - 1 or not conv:
        raise RuntimeError("R6U does not contain the registered sensitivity strata")
    return nonconv[: PER_CELL - 1] + conv[:1]


def main() -> None:
    r6u = json.loads(R6U.read_text())
    salt = int(r6u["scope"]["seed_salt"])
    rows: list[dict] = []
    for size, p in CELLS:
        lattice = paper_periodic_honeycomb(size)
        template = build_r6d_dense_template(lattice, error_rate=p)
        r6u_rows = {r["trajectory_index"]: r for r in r6u["rows"] if r["size"] == size and r["p_X"] == p}
        for index in select_indices(r6u, size, p):
            physical_seed, observation_seed = trajectory_seeds(salt, size, p, index)
            physical = (np.random.default_rng(physical_seed).random(lattice.edge_count) < p).astype(np.uint8)
            observation = observation_from_error_edges(lattice, physical, seed=observation_seed)
            if observation.status != "sampled" or observation.charge_outcomes is None:
                raise RuntimeError("selected R6U row unexpectedly terminal")
            public = PublicD4Observation(
                tuple(int(x) for x in edge_chain_boundary(lattice, physical)),
                tuple(int(x) for x in observation.charge_outcomes),
            )
            o2 = decode_and_score_flux_recovery(
                lattice, physical, published_herald_weights(lattice, np.asarray(observation.charge_outcomes, dtype=np.int64))
            )
            pilot_bp = r6u_rows[index]["policies"]["R6D_local_BP_posterior_LLR_MWPM"]
            row = {"size": size, "p_X": p, "trajectory_index": index,
                   "pilot": {"bp": pilot_bp["bp"], "correction_edges": pilot_bp["correction_edges"],
                             "logical_failure": pilot_bp["flux_union_logical_failure"]},
                   "O2": {"logical_failure": bool(o2.logical_error),
                          "correction_edges": [int(x) for x in np.flatnonzero(o2.correction)]},
                   "schedules": {}}
            for config in CONFIGS:
                result = run_r6d_dense_template(template, public, **{k: config[k] for k in ("old_message_weight", "max_iterations", "tolerance")})
                recovery = decode_and_score_flux_recovery(lattice, physical, llr_weights(result.marginals[:lattice.edge_count, 1]))
                correction = [int(x) for x in np.flatnonzero(recovery.correction)]
                row["schedules"][config["id"]] = {
                    "converged": bool(result.converged), "iterations": int(result.iterations),
                    "max_message_delta": float(result.max_message_delta),
                    "logical_failure": bool(recovery.logical_error), "correction_edges": correction,
                }
            default = row["schedules"]["A_default_d025_cap40"]
            row["default_matches_r6u_correction"] = default["correction_edges"] == row["pilot"]["correction_edges"]
            row["default_matches_r6u_score"] = default["logical_failure"] == row["pilot"]["logical_failure"]
            rows.append(row)

    summaries = {}
    for config in CONFIGS:
        srows = [r["schedules"][config["id"]] for r in rows]
        summaries[config["id"]] = {
            "decoded_records": len(srows), "converged_records": sum(x["converged"] for x in srows),
            "nonconverged_records": sum(not x["converged"] for x in srows),
            "logical_failures": sum(x["logical_failure"] for x in srows),
            "o2_bp_disagreements": sum(x["logical_failure"] != r["O2"]["logical_failure"] for x, r in zip(srows, rows)),
            "BP_improves_over_O2": sum((not x["logical_failure"]) and r["O2"]["logical_failure"] for x, r in zip(srows, rows)),
            "BP_regresses_against_O2": sum(x["logical_failure"] and (not r["O2"]["logical_failure"]) for x, r in zip(srows, rows)),
        }
    payload = {
        "schema_version": 1, "status": "completed_bounded_nonconvergence_sensitivity",
        "generated_at": datetime.now(timezone.utc).isoformat(), "source": R6U.name,
        "scope": {"cells": [{"size": x, "p_X": y} for x, y in CELLS], "records_per_cell": PER_CELL,
                  "selection": "first five R6U-default nonconverged records plus first converged record", "configs": CONFIGS},
        "acceptance": {"default_replay_correction_matches_all": all(r["default_matches_r6u_correction"] for r in rows),
                       "default_replay_score_matches_all": all(r["default_matches_r6u_score"] for r in rows)},
        "summaries": summaries, "rows": rows,
        "claim_boundary": "Bounded schedule sensitivity on selected high-nonconvergence R6U records; not a threshold estimate or a convergence proof.",
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    lines = ["# R6V bounded BP nonconvergence sensitivity", "",
             "Twelve regenerated, matched R6U records: six each from `(L,pX)=(9,.22)` and `(13,.22)`. Each cell has five default-nonconverged records plus one converged control. O2 is fixed; only BP damping/cap changes.", "",
             "| BP schedule | converged / 12 | BP failures | BP improves vs O2 | BP regresses vs O2 |", "| --- | ---: | ---: | ---: | ---: |"]
    for config in CONFIGS:
        s = summaries[config["id"]]
        lines.append(f"| {config['id']} | {s['converged_records']} / {s['decoded_records']} | {s['logical_failures']} | {s['BP_improves_over_O2']} | {s['BP_regresses_against_O2']} |")
    lines += ["", f"Default dense-template replay correction matches recorded R6U correction on all rows: `{payload['acceptance']['default_replay_correction_matches_all']}`.",
              f"Default dense-template replay Boolean-union score matches recorded R6U score on all rows: `{payload['acceptance']['default_replay_score_matches_all']}`.",
              "", "Interpretation is limited to whether the selected R6U decoder ordering changes under these bounded schedules; it does not establish a BP fixed-point solution or a threshold."]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(OUT), "report": str(REPORT), "summaries": summaries}))


if __name__ == "__main__":
    main()
