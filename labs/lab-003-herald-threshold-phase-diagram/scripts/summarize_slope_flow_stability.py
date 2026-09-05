#!/usr/bin/env python3
"""Summarize size-window stability and target unresolved slope-flow cells.

This diagnostic never uses LER-curve crossings. It separates uncertainty that
is plausibly seed limited (the fitted beta sign survives every leave-one-size-
out refit) from uncertainty that is distance limited (at least one retained
size pair reverses or loses the fitted beta sign).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = LAB_DIR / "results/phase2-residual80-honeycomb-slope-flow-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase2-residual80-honeycomb-slope-flow-stability-2026-08-28.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(payload: dict) -> dict:
    q_values = [float(value) for value in payload["q_values"]]
    p_values = [float(value) for value in payload["p_values"]]
    grid = {
        (float(row["q"]), float(cell["p"])): cell
        for row in payload["analyses"]
        for cell in row["cells"]
    }
    if len(grid) != len(q_values) * len(p_values):
        raise ValueError("slope-flow result does not contain the complete q-p grid")

    class_stability = {}
    for classification in ("decodable", "undecodable", "unresolved"):
        cells = [cell for cell in grid.values() if cell["classification"] == classification]
        stable = sum(bool(cell["leave_one_distance_out_sign_stable"]) for cell in cells)
        class_stability[classification] = {
            "total": len(cells),
            "leave_one_distance_out_stable": stable,
            "leave_one_distance_out_unstable": len(cells) - stable,
        }

    targets = []
    for q_index, q in enumerate(q_values):
        for p_index, p in enumerate(p_values):
            cell = grid[(q, p)]
            if cell["classification"] != "unresolved":
                continue
            neighbors = []
            for neighbor_q, neighbor_p in (
                (q_index - 1, p_index),
                (q_index + 1, p_index),
                (q_index, p_index - 1),
                (q_index, p_index + 1),
            ):
                if 0 <= neighbor_q < len(q_values) and 0 <= neighbor_p < len(p_values):
                    neighbors.append(grid[(q_values[neighbor_q], p_values[neighbor_p])]["classification"])
            resolved_neighbors = sorted(set(neighbors) - {"unresolved"})
            if len(resolved_neighbors) == 2:
                priority_tier = 1
                location = "between both resolved phases"
            elif resolved_neighbors:
                priority_tier = 2
                location = "adjacent to one resolved phase"
            else:
                priority_tier = 3
                location = "unresolved interior"
            loo_stable = bool(cell["leave_one_distance_out_sign_stable"])
            targets.append(
                {
                    "q": q,
                    "p": p,
                    "beta": float(cell["beta"]),
                    "beta_interval90": [float(value) for value in cell["beta_interval90"]],
                    "dominant_sign_probability": float(
                        max(cell["probability_decodable"], cell["probability_undecodable"])
                    ),
                    "leave_one_distance_out_sign_stable": loo_stable,
                    "resolved_neighbor_classes": resolved_neighbors,
                    "priority_tier": priority_tier,
                    "priority_reason": location,
                    "evidence_need": (
                        "additional independent seed trajectories"
                        if loo_stable
                        else "an additional code distance before more same-distance shots"
                    ),
                }
            )

    targets.sort(
        key=lambda cell: (
            cell["priority_tier"],
            not cell["leave_one_distance_out_sign_stable"],
            -cell["dominant_sign_probability"],
            cell["q"],
            cell["p"],
        )
    )
    evidence_need_counts = {
        "seed_limited": sum(cell["leave_one_distance_out_sign_stable"] for cell in targets),
        "distance_limited": sum(not cell["leave_one_distance_out_sign_stable"] for cell in targets),
    }
    frontier_counts = {
        "between_both_resolved_phases": sum(cell["priority_tier"] == 1 for cell in targets),
        "adjacent_to_one_resolved_phase": sum(cell["priority_tier"] == 2 for cell in targets),
        "unresolved_interior": sum(cell["priority_tier"] == 3 for cell in targets),
    }
    stable_boundary_edges = 0
    for q in q_values:
        cells = [grid[(q, p)] for p in p_values]
        for left, right in zip(cells, cells[1:]):
            if (
                {left["classification"], right["classification"]} == {"decodable", "undecodable"}
                and left["leave_one_distance_out_sign_stable"]
                and right["leave_one_distance_out_sign_stable"]
            ):
                stable_boundary_edges += 1

    return {
        "schema_version": 1,
        "status": "complete",
        "method": "leave-one-distance-out beta sign stability on the crossing-free slope-flow map",
        "class_stability": class_stability,
        "unresolved_evidence_need": evidence_need_counts,
        "unresolved_frontier": frontier_counts,
        "stable_observed_boundary_edges": stable_boundary_edges,
        "target_ordering": [
            "measured gray cells neighboring both resolved phase colors",
            "measured gray cells neighboring one resolved phase color",
            "remaining unresolved interior cells",
            "within a tier, size-window-stable cells closest to the 0.95 sign-confidence gate first",
        ],
        "targets": targets,
        "interpretation": (
            "Same-distance shot extension is appropriate only for gray cells whose beta sign is stable "
            "under every leave-one-distance-out refit. Cells with a sign reversal need an additional "
            "distance to test scaling curvature before more shots can support phase promotion."
        ),
        "crossing_statistic_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    output = summarize(payload)
    output["generated_at"] = datetime.now(timezone.utc).isoformat()
    output["source"] = {"path": str(args.input), "sha256": sha256(args.input)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n")
    temporary.replace(args.output)
    print(json.dumps({key: output[key] for key in ("class_stability", "unresolved_evidence_need", "unresolved_frontier", "stable_observed_boundary_edges")}, indent=2))


if __name__ == "__main__":
    main()
