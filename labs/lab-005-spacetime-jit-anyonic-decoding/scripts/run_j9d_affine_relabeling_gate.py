"""Bounded rank-invariant gate for public-charge affine relabeling of J9B laws."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9d-affine-relabeling-gate-2026-09-28.json"
RESULT = LAB / "results/j9d-affine-relabeling-gate-2026-09-28.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    start = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    source_path = LAB / contract["source_result"]
    assert sha(source_path) == contract["source_sha256"]
    source = json.loads(source_path.read_text())
    assert source["status"] == "cross_sector_character_census_verified"
    assert len(source["rows"]) == 24
    assert source["summary"]["complete_laws"] == 48
    counts = Counter()
    rows = []
    for cell in source["rows"]:
        assert cell["public_action_red_edges"] in [[0], [1, 30, 32, 34, 35]]
        assert len(cell["private_error_laws"]) == 2
        ranks = [law["affine_parity_rank"] for law in cell["private_error_laws"]]
        support_sizes = [law["positive_active_assignments"] for law in cell["private_error_laws"]]
        n = len(cell["active_charge_sites"])
        assert all(size == 1 << (n - rank) for size, rank in zip(support_sizes, ranks))
        positive_tv = cell["full_second_total_variation"] != "0"
        unequal_rank = ranks[0] != ranks[1]
        assert unequal_rank == (support_sizes[0] != support_sizes[1])
        if positive_tv:
            counts["positive_tv"] += 1
            if unequal_rank:
                counts["positive_tv_rank_obstructed"] += 1
        else:
            counts["null_tv"] += 1
        rows.append({"first_flux_mask": cell["first_flux_mask"],
                     "public_action_red_edges": cell["public_action_red_edges"],
                     "affine_parity_ranks": ranks,
                     "positive_active_assignments": support_sizes,
                     "full_second_total_variation": cell["full_second_total_variation"],
                     "invertible_affine_public_relabeling_possible_by_rank": not unequal_rank})
        assert time.process_time() - start <= contract["budget"]["max_cpu_seconds"]
    assert counts == {"null_tv": 18, "positive_tv": 6,
                      "positive_tv_rank_obstructed": 6}
    assert sha(source_path) == contract["source_sha256"]
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "affine_public_relabeling_rank_gate_closed",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "rows": rows, "summary": dict(counts),
            "counters": {"new_operator_characters": 0, "new_born_terms": 0,
                         "new_public_laws": 0, "histories": 0, "schedule_arms": 0,
                         "bootstraps": 0},
            "cpu_seconds": round(time.process_time() - start, 6),
            "claim_boundary": "Within the 24 frozen deterministic-first pair/action cells, every six unequal public laws has unequal affine rank/support cardinality, so no invertible affine relabeling (including sign flips or site permutations) can map either paired law to the other. Null cells need no map. This does not exclude non-bijective signed-character identities, first-record mixture reductions, or uncomputed laws; no full-IID information/risk, noisy JIT, scaling or threshold."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "summary": result["summary"],
                      "cpu_seconds": result["cpu_seconds"]}))
