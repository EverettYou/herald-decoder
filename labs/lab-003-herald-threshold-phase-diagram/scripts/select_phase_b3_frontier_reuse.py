#!/usr/bin/env python3
"""Select the smallest Phase B3 frontier matrix while reusing valid Phase S1 data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b3-honeycomb-frontier-reuse-selection-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def frontier_candidates(phase_map: dict) -> list[dict]:
    analyses = phase_map["analyses"]
    q_values = [float(row["q"]) for row in analyses]
    p_values = [float(cell["p"]) for cell in analyses[0]["cells"]]
    grid = {(float(row["q"]), float(cell["p"])): cell for row in analyses for cell in row["cells"]}
    candidates = []
    for q_index, q in enumerate(q_values):
        for p_index, p in enumerate(p_values):
            cell = grid[(q, p)]
            if cell["classification"] != "unresolved":
                continue
            neighbors = []
            for q_step, p_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                qi, pi = q_index + q_step, p_index + p_step
                if 0 <= qi < len(q_values) and 0 <= pi < len(p_values):
                    neighbors.append(grid[(q_values[qi], p_values[pi])]["classification"])
            if "decodable" not in neighbors or "undecodable" not in neighbors:
                continue
            p_up = float(cell["posterior_probability_upward_trend"])
            p_down = float(cell["posterior_probability_downward_trend"])
            candidates.append({
                "q": q,
                "p": p,
                "lean": "upward" if p_up > p_down else "downward",
                "directional_confidence": max(p_up, p_down),
                "posterior_probability_upward_trend": p_up,
                "posterior_probability_downward_trend": p_down,
                "neighbor_classifications": neighbors,
            })
    return sorted(candidates, key=lambda row: (-row["directional_confidence"], row["q"], row["p"]))


def reuse_path(q: float, p: float) -> tuple[str, str] | None:
    table = {
        (0.10, 0.20): ("seed_limited", "results/phase-s1-honeycomb-seed-q010-p020-2026-08-28.json"),
        (0.30, 0.20): ("distance_limited", "results/phase-s1-honeycomb-distance-q030-p020-2026-08-28.json"),
        (0.35, 0.20): ("distance_limited", "results/phase-s1-honeycomb-distance-q035-p020-2026-08-28.json"),
        (0.40, 0.20): ("distance_limited", "results/phase-s1-honeycomb-distance-q040-p020-2026-08-28.json"),
        (0.60, 0.28): ("distance_limited", "results/phase-s1-honeycomb-distance-q060-p028-2026-08-28.json"),
    }
    return table.get((round(q, 2), round(p, 2)))


def select(phase_map_path: Path) -> dict:
    phase_map = json.loads(phase_map_path.read_text())
    candidates = frontier_candidates(phase_map)
    reused, new_jobs = [], []
    for row in candidates:
        source = reuse_path(row["q"], row["p"])
        if source is None:
            new_jobs.append({**row, "branch": "independent_shots", "sizes": [7, 9, 11], "additional_shots_per_size": 1000})
            continue
        source_kind, relative = source
        path = LAB_DIR / relative
        if not path.is_file():
            raise ValueError(f"missing registered Phase S1 reuse source: {path}")
        reused.append({**row, "reuse_kind": source_kind, "path": relative, "sha256": sha256(path)})
    if {(row["q"], row["p"]) for row in candidates} != {(0.10, 0.20), (0.30, 0.20), (0.35, 0.20), (0.40, 0.20), (0.55, 0.24), (0.60, 0.28)}:
        raise ValueError("Phase B3 frontier candidate set drift")
    if [(row["q"], row["p"]) for row in new_jobs] != [(0.55, 0.24)] or len(reused) != 5:
        raise ValueError("Phase B3 reuse/new split drift")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "source_map": {"path": str(phase_map_path), "sha256": sha256(phase_map_path)},
        "selection_rule": "All unresolved four-neighbor cells adjacent to both green and red. Reuse any audited source-compatible Phase S1 measurements before authorizing fresh shots.",
        "frontier_candidates": candidates,
        "reused_phase_s1_evidence": reused,
        "new_jobs": new_jobs,
        "candidate_count": len(candidates),
        "reuse_count": len(reused),
        "new_job_count": len(new_jobs),
        "expected_new_decodes": 3000,
        "claim_boundary": "Selection only. Phase S1 raw outcomes are valid posterior-LLR measurements, but their withdrawn slope-flow interpretation is not reused.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = select(args.phase_map)
    atomic_json(args.output, output)
    print(json.dumps({key: output[key] for key in ("candidate_count", "reuse_count", "new_job_count", "expected_new_decodes")}, indent=2))


if __name__ == "__main__":
    main()
