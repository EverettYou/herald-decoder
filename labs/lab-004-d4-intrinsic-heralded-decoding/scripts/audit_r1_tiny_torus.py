"""Exhaustive L=2 audit of the periodic D4 loop-constraint generator."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from math import exp2
from pathlib import Path

import numpy as np

from d4_honeycomb import generate_loop_constraints, periodic_honeycomb


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = LAB_DIR / "results/r1-periodic-constraint-generator-audit.json"


def audit(size: int = 2) -> dict:
    lattice = periodic_honeycomb(size)
    configuration_count = 1 << lattice.edge_count
    component_classes: Counter[str] = Counter()
    total_charge_assignments = 0
    total_allowed_assignments = 0
    max_internal_vertices = 0
    max_constraint_count = 0

    for mask in range(configuration_count):
        selected = np.array(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=bool,
        )
        analysis = generate_loop_constraints(lattice, selected)
        degrees = np.bincount(
            lattice.edge_vertices[selected].ravel(),
            minlength=lattice.vertex_count,
        )
        internal_vertices = np.flatnonzero(degrees == 2)
        internal_index = {int(vertex): index for index, vertex in enumerate(internal_vertices)}

        expected_constraints = 0
        for component in analysis.components:
            if not component.nonbranching_closed:
                component_classes["open_or_branched"] += 1
            elif component.homologically_trivial:
                component_classes["trivial_nonbranching_loop"] += 1
                expected_constraints += 2
            else:
                component_classes["winding_nonbranching_loop"] += 1
        if len(analysis.constraints) != expected_constraints:
            raise AssertionError("constraint count does not match component classes")

        for constraint in analysis.constraints:
            if any(vertex not in internal_index for vertex in constraint.vertices):
                raise AssertionError("constraint references non-internal support")
            colors = {int(lattice.vertex_colors[vertex]) for vertex in constraint.vertices}
            if len(colors) != 1:
                raise AssertionError("one constraint mixes blue and green vertices")

        internal_count = len(internal_vertices)
        constraint_count = len(analysis.constraints)
        max_internal_vertices = max(max_internal_vertices, internal_count)
        max_constraint_count = max(max_constraint_count, constraint_count)
        assignment_count = 1 << internal_count
        total_charge_assignments += assignment_count
        allowed_count = 0
        for assignment in range(assignment_count):
            bits = [
                (assignment >> internal_index[vertex]) & 1
                for vertex in internal_vertices
            ]
            values = {
                int(vertex): int(bit)
                for vertex, bit in zip(internal_vertices, bits)
            }
            if all(
                sum(values[vertex] for vertex in constraint.vertices) % 2
                == constraint.required_parity
                for constraint in analysis.constraints
            ):
                allowed_count += 1

        expected_allowed = 1 << (internal_count - constraint_count)
        if allowed_count != expected_allowed:
            raise AssertionError("generated constraints are not independent")
        if allowed_count * exp2(constraint_count - internal_count) != 1.0:
            raise AssertionError("Eq. A12 likelihood does not normalize")
        total_allowed_assignments += allowed_count

    return {
        "schema_version": 1,
        "status": "verified",
        "lattice": "periodic_coloured_honeycomb",
        "size": size,
        "vertices": lattice.vertex_count,
        "edges": lattice.edge_count,
        "error_configurations_exhausted": configuration_count,
        "charge_assignments_checked": total_charge_assignments,
        "allowed_charge_assignments": total_allowed_assignments,
        "component_classes": dict(sorted(component_classes.items())),
        "max_internal_vertices": max_internal_vertices,
        "max_constraint_count": max_constraint_count,
        "constraint_count_failures": 0,
        "constraint_support_failures": 0,
        "constraint_independence_failures": 0,
        "normalization_failures": 0,
        "claim_boundary": (
            "This exhausts the binary L=2 topology and generated charge-parity "
            "assignments. Logical-sector-dependent constraints on winding loops "
            "remain intentionally unassigned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=2)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = audit(args.size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
