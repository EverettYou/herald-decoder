#!/usr/bin/env python3
"""Select the smallest two-arm adaptive cohort from the fuzzy-trend gray map."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json"
DEFAULT_B1 = LAB_DIR / "results/phase-b1-honeycomb-l5-l13-bayesian-fuzzy-trend-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b2-honeycomb-gray-frontier-selection-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def select_cells(phase_map: dict, b1: dict) -> dict:
    analyses = phase_map["analyses"]
    q_values = [float(row["q"]) for row in analyses]
    p_values = [float(cell["p"]) for cell in analyses[0]["cells"]]
    grid = {(float(row["q"]), float(cell["p"])): cell for row in analyses for cell in row["cells"]}
    b1_cells = {(float(row["q"]), float(row["p"])): row for row in b1["analyses"]}

    distance_cells = []
    reused = []
    for coordinate, cell in sorted(grid.items()):
        if cell["gray_measurement_route"] != "add_L5_L13_distance_leverage":
            continue
        if coordinate in b1_cells and b1_cells[coordinate]["classification"] != "unresolved":
            reused.append({"q": coordinate[0], "p": coordinate[1], "classification": b1_cells[coordinate]["classification"], "evidence": "phase-b1-honeycomb-l5-l13-bayesian-fuzzy-trend-2026-08-28.json"})
        else:
            distance_cells.append({"branch": "distance_leverage", "q": coordinate[0], "p": coordinate[1], "sizes": [5, 13], "reason": "gray with posterior midpoint-curvature probability at least 0.95"})

    shot_candidates = []
    for iq, q_value in enumerate(q_values):
        for ip, p_value in enumerate(p_values):
            cell = grid[(q_value, p_value)]
            if cell["classification"] != "unresolved" or cell["gray_measurement_route"] != "more_shots_existing_L7_L9_L11_first":
                continue
            neighbor_classes = set()
            for jq, jp in ((iq - 1, ip), (iq + 1, ip), (iq, ip - 1), (iq, ip + 1)):
                if 0 <= jq < len(q_values) and 0 <= jp < len(p_values):
                    neighbor_classes.add(grid[(q_values[jq], p_values[jp])]["classification"])
            if {"decodable", "undecodable"}.issubset(neighbor_classes):
                p_up = float(cell["posterior_probability_upward_trend"])
                p_down = float(cell["posterior_probability_downward_trend"])
                shot_candidates.append({"q": q_value, "p": p_value, "p_up": p_up, "p_down": p_down, "confidence": max(p_up, p_down), "lean": "upward" if p_up >= p_down else "downward"})
    selected_shots = []
    for lean, branch in (("upward", "shot_limited_upward_frontier"), ("downward", "shot_limited_downward_frontier")):
        candidates = [row for row in shot_candidates if row["lean"] == lean]
        if not candidates:
            raise ValueError(f"no {lean} gray cell between resolved colors")
        selected = max(candidates, key=lambda row: (row["confidence"], -row["q"], -row["p"]))
        selected_shots.append({"branch": branch, "q": selected["q"], "p": selected["p"], "sizes": [7, 9, 11], "posterior_directional_confidence": selected["confidence"], "reason": "highest-confidence gray cell of this lean with both red and green four-neighbors"})
    return {"distance_leverage_new": distance_cells, "distance_leverage_reused": reused, "shot_limited_selected": selected_shots, "shot_limited_candidate_count": len(shot_candidates)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--b1", type=Path, default=DEFAULT_B1)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    phase_map = json.loads(args.phase_map.read_text())
    b1 = json.loads(args.b1.read_text())
    selection = select_cells(phase_map, b1)
    jobs = selection["distance_leverage_new"] + selection["shot_limited_selected"]
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "selected_not_registered",
        "selection_rule": "reuse resolved five-distance evidence; add L5/L13 for remaining curvature-routed gray cells; among shot-routed gray cells with both red and green four-neighbors, choose the highest-confidence upward-leaning and downward-leaning cells",
        "selection": selection,
        "jobs": jobs,
        "job_count": len(jobs),
        "planned_new_decodes": sum((2 if job["sizes"] == [5, 13] else 3) * 5 * 200 for job in jobs),
        "provenance": {
            "phase_map": {"path": str(args.phase_map), "sha256": sha256(args.phase_map)},
            "phase_b1": {"path": str(args.b1), "sha256": sha256(args.b1)},
            "selector": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        },
        "stop_rule": "Do not add further gray cells, q/p midpoints, or square-lattice jobs before this three-job cohort is audited and analyzed.",
    }
    atomic_json(args.output, output)
    print(json.dumps({"output": str(args.output), "jobs": jobs, "reused": selection["distance_leverage_reused"], "planned_new_decodes": output["planned_new_decodes"]}, indent=2))


if __name__ == "__main__":
    main()
