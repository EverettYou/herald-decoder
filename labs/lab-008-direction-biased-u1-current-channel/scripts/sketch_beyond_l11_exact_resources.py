#!/usr/bin/env python3
"""Read-only resource sketch for exact frontier contraction beyond L=11.

This script calls only ``CurrentOracle._sketch`` on graph metadata.  It does
not construct transition tables, generate physical histories, or evaluate a
posterior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(LAB / "scripts"))

from herald_decoder.lattice_model import square_graph
from current_oracle import CurrentOracle


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(size: int) -> dict:
    model = square_graph(size)
    oracle = CurrentOracle.__new__(CurrentOracle)
    oracle.model = model
    oracle.measured = tuple(model.detector_vertices)
    oracle.base = 3
    orders = {
        "detector_order": list(oracle.measured),
        "row_major": sorted(
            oracle.measured,
            key=lambda v: (round(model.vertices[v].y, 6), model.vertices[v].x),
        ),
        "column_major": sorted(
            oracle.measured,
            key=lambda v: (round(model.vertices[v].x, 6), model.vertices[v].y),
        ),
    }
    candidates = {}
    for name, order in orders.items():
        _, cost, width = oracle._sketch(order)
        candidates[name] = {
            "candidate_transitions": int(cost),
            "maximum_frontier": int(width),
            # Seven int32 columns are allocated before charge grouping.
            "ungrouped_transition_bytes_lower_proxy": int(cost * 7 * 4),
        }
    selected_name, selected = min(
        candidates.items(), key=lambda item: item[1]["candidate_transitions"]
    )
    return {
        "size": size,
        "vertices": len(model.vertices),
        "edges": len(model.edges),
        "measured_vertices": len(oracle.measured),
        "base": 3,
        "orders": candidates,
        "selected_order": selected_name,
        "selected": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profiles = {str(size): profile(size) for size in (11, 13)}
    cap_transitions = 50_000_000
    cap_bytes = 8 * 1024**3
    l11 = profiles["11"]["selected"]
    l13 = profiles["13"]["selected"]
    result = {
        "id": "lab008-beyond-l11-exact-resource-sketch-2026-09-21",
        "status": "complete",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "operation": "metadata-only CurrentOracle._sketch; no transition construction, sampling, inference, or bootstrap",
        "profiles": profiles,
        "registered_exact_caps": {
            "candidate_transitions": cap_transitions,
            "peak_memory_bytes": cap_bytes,
        },
        "control": {
            "l11_registered_candidate_transitions": 43_578_135,
            "l11_sketch_matches_registered_preflight": l11["candidate_transitions"] == 43_578_135,
        },
        "decision": {
            "l13_transition_cap_pass": l13["candidate_transitions"] <= cap_transitions,
            "l13_ungrouped_array_lower_proxy_memory_cap_pass": l13["ungrouped_transition_bytes_lower_proxy"] <= cap_bytes,
            "exact_l13_production_armed": False,
            "reason": "L13 exceeds the registered exact transition cap; the lower memory proxy excludes grouped copies, charge partitions, forward/backward arrays, and interpreter overhead.",
        },
        "source_hashes": {
            "script": sha256(Path(__file__)),
            "current_oracle": sha256(LAB / "scripts" / "current_oracle.py"),
            "lattice_model": sha256(ROOT / "src" / "herald_decoder" / "lattice_model.py"),
        },
        "counters": {
            "new_physical_records": 0,
            "posterior_evaluations": 0,
            "bootstrap_replicates": 0,
        },
    }
    if not result["control"]["l11_sketch_matches_registered_preflight"]:
        raise SystemExit("L11 sketch failed the registered control")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["decision"], indent=2))


if __name__ == "__main__":
    main()
