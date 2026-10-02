"""Exact L3/L4 audit of direct midpoint cross-sector switching maps.

At p=1/2,q=1 every binary current has equal probability.  Flipping a simple
residual directed path between rough sides preserves the full measured charge
and changes logical parity.  Turning this observation into a Bayes-risk lower
bound requires a deterministic injection (or bounded multiplicity), not just
the existence of a crossing.  This script audits two extremal path selectors
and the local-plaquette alternative on the registered exact state spaces.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import time

import numpy as np

from current_oracle import LAB, ROOT, charge_matrix, square_graph


RESULT = LAB / "results/midpoint-switching-pairing-2026-09-20.json"


def _simple_crossing_paths(graph):
    left = {i for i, vertex in enumerate(graph.vertices) if vertex.boundary_side == "left"}
    right = {i for i, vertex in enumerate(graph.vertices) if vertex.boundary_side == "right"}
    adjacency = [[] for _ in graph.vertices]
    for edge, (u, v) in enumerate(graph.edges):
        adjacency[u].append((v, edge))
        adjacency[v].append((u, edge))

    paths = []
    for start in sorted(left):
        stack = [(start, [start], [])]
        while stack:
            vertex, vertices, edges = stack.pop()
            for neighbor, edge in adjacency[vertex]:
                if neighbor in vertices or neighbor in left:
                    continue
                next_vertices = vertices + [neighbor]
                next_edges = edges + [edge]
                if neighbor in right:
                    mask = 0
                    required = 0
                    for u, v, path_edge in zip(
                        next_vertices, next_vertices[1:], next_edges
                    ):
                        mask |= 1 << path_edge
                        if graph.edges[path_edge] != (u, v):
                            required |= 1 << path_edge
                    paths.append(
                        {
                            "vertices": tuple(next_vertices),
                            "edges": tuple(next_edges),
                            "mask": mask,
                            "required": required,
                        }
                    )
                elif graph.vertices[neighbor].boundary_side is None:
                    stack.append((neighbor, next_vertices, next_edges))
    return paths


def _path_available(path, bits):
    restricted = bits & path["mask"]
    return restricted == path["required"] or restricted == (
        path["mask"] ^ path["required"]
    )


def _path_key(path, graph):
    return (
        tuple(graph.vertices[vertex].y for vertex in path["vertices"]),
        path["edges"],
    )


def _selector_audit(graph, ordered_paths):
    edge_count = len(graph.edges)
    selected = [None] * (1 << edge_count)
    for bits in range(1 << edge_count):
        for path_index, path in enumerate(ordered_paths):
            if _path_available(path, bits):
                selected[bits] = path_index
                break

    outputs = defaultdict(list)
    stable_states = set()
    first_instability = None
    for bits, path_index in enumerate(selected):
        if path_index is None:
            continue
        path = ordered_paths[path_index]
        image = bits ^ path["mask"]
        outputs[image].append(bits)
        image_path_index = selected[image]
        assert image_path_index is not None
        if ordered_paths[image_path_index]["mask"] == path["mask"]:
            stable_states.add(bits)
        elif first_instability is None:
            first_instability = {
                "current_integer": bits,
                "chosen_path_edges": list(path["edges"]),
                "image_integer": image,
                "reselected_path_edges": list(ordered_paths[image_path_index]["edges"]),
            }

    for bits in stable_states:
        path = ordered_paths[selected[bits]]
        image = bits ^ path["mask"]
        assert image in stable_states
        assert selected[image] is not None
        assert ordered_paths[selected[image]]["mask"] == path["mask"]
        assert (image ^ ordered_paths[selected[image]]["mask"]) == bits

    stable_images = [
        bits ^ ordered_paths[selected[bits]]["mask"] for bits in stable_states
    ]
    assert len(set(stable_images)) == len(stable_images)
    eligible = sum(path_index is not None for path_index in selected)
    multiplicities = Counter(len(preimages) for preimages in outputs.values())
    return {
        "eligible_crossing_states": eligible,
        "selector_stable_states": len(stable_states),
        "selector_stable_fraction_given_crossing_exact": str(
            Fraction(len(stable_states), eligible)
        ),
        "certified_disjoint_cross_sector_pairs": len(stable_states) // 2,
        "finite_Bayes_LER_pairing_lower_bound_exact": str(
            Fraction(len(stable_states) // 2, 1 << edge_count)
        ),
        "all_eligible_map_distinct_images": len(outputs),
        "all_eligible_map_collision_images": sum(
            len(preimages) > 1 for preimages in outputs.values()
        ),
        "all_eligible_map_maximum_multiplicity": max(multiplicities),
        "all_eligible_map_injective": len(outputs) == eligible,
        "stable_subset_involution": True,
        "stable_subset_injective": True,
        "first_selector_instability": first_instability,
    }


def _plaquettes(graph):
    coordinates = {
        (int(vertex.x), int(vertex.y)): index
        for index, vertex in enumerate(graph.vertices)
    }
    edge_index = {
        frozenset((u, v)): edge for edge, (u, v) in enumerate(graph.edges)
    }
    plaquettes = []
    for x in range(max(x for x, _ in coordinates)):
        for y in range(max(y for _, y in coordinates)):
            vertices = [
                coordinates[(x, y)],
                coordinates[(x + 1, y)],
                coordinates[(x + 1, y + 1)],
                coordinates[(x, y + 1)],
            ]
            try:
                edges = [
                    edge_index[frozenset((vertices[index], vertices[(index + 1) % 4]))]
                    for index in range(4)
                ]
            except KeyError:
                continue
            mask = sum(1 << edge for edge in edges)
            required = 0
            for u, v, edge in zip(vertices, vertices[1:] + vertices[:1], edges):
                if graph.edges[edge] != (u, v):
                    required |= 1 << edge
            plaquettes.append(
                {
                    "vertices": vertices,
                    "edges": edges,
                    "mask": mask,
                    "required": required,
                }
            )
    return plaquettes


def _algebraic_path_checks(graph, incidence, paths):
    failures = Counter()
    for path in paths:
        for direction in (0, 1):
            bits = path["required"] if direction == 0 else path["mask"] ^ path["required"]
            current = np.array(
                [(bits >> edge) & 1 for edge in range(len(graph.edges))], dtype=int
            )
            image_bits = bits ^ path["mask"]
            image = np.array(
                [(image_bits >> edge) & 1 for edge in range(len(graph.edges))], dtype=int
            )
            failures["charge_preservation"] += int(
                not np.array_equal(incidence @ current, incidence @ image)
            )
            parity_delta = sum(
                int(current[edge] != image[edge]) for edge in graph.logical_edges
            ) % 2
            failures["logical_parity_flip"] += int(parity_delta != 1)
    return failures


def _plaquette_audit(graph, incidence, plaquettes):
    eligible = set()
    charge_failures = 0
    parity_flip_successes = 0
    for bits in range(1 << len(graph.edges)):
        for plaquette in plaquettes:
            if not _path_available(plaquette, bits):
                continue
            eligible.add(bits)
            image_bits = bits ^ plaquette["mask"]
            current = np.array(
                [(bits >> edge) & 1 for edge in range(len(graph.edges))], dtype=int
            )
            image = np.array(
                [(image_bits >> edge) & 1 for edge in range(len(graph.edges))], dtype=int
            )
            charge_failures += int(
                not np.array_equal(incidence @ current, incidence @ image)
            )
            parity_flip_successes += int(
                sum(
                    int(current[edge] != image[edge])
                    for edge in graph.logical_edges
                )
                % 2
                == 1
            )
    return {
        "elementary_plaquettes": len(plaquettes),
        "states_with_directed_plaquette": len(eligible),
        "charge_preservation_failures": charge_failures,
        "logical_parity_flip_successes": parity_flip_successes,
        "decision": "standalone plaquette flips cannot pair logical sectors",
    }


def _size_audit(size):
    graph = square_graph(size)
    incidence = charge_matrix(graph)
    paths = _simple_crossing_paths(graph)
    algebra = _algebraic_path_checks(graph, incidence, paths)
    assert not algebra["charge_preservation"]
    assert not algebra["logical_parity_flip"]

    lower = sorted(paths, key=lambda path: _path_key(path, graph))
    upper = list(reversed(lower))
    lower_audit = _selector_audit(graph, lower)
    upper_audit = _selector_audit(graph, upper)
    plaquette_audit = _plaquette_audit(graph, incidence, _plaquettes(graph))
    assert plaquette_audit["charge_preservation_failures"] == 0
    assert plaquette_audit["logical_parity_flip_successes"] == 0
    return {
        "L": size,
        "edges": len(graph.edges),
        "current_states": 1 << len(graph.edges),
        "simple_rough_to_rough_paths": len(paths),
        "path_flip_charge_preservation_failures": algebra["charge_preservation"],
        "path_flip_logical_parity_failures": algebra["logical_parity_flip"],
        "lower_extremal_selector": lower_audit,
        "upper_extremal_selector": upper_audit,
        "local_plaquette": plaquette_audit,
    }


def analyze():
    start = time.monotonic()
    sizes = [_size_audit(3), _size_audit(4)]
    assert sizes[0]["lower_extremal_selector"]["eligible_crossing_states"] == 238
    assert sizes[1]["lower_extremal_selector"]["eligible_crossing_states"] == 232822
    assert not sizes[0]["lower_extremal_selector"]["all_eligible_map_injective"]
    assert not sizes[1]["lower_extremal_selector"]["all_eligible_map_injective"]
    elapsed = time.monotonic() - start
    assert elapsed < 300

    source_files = [
        LAB / "scripts/check_midpoint_switching_pairing.py",
        LAB / "scripts/current_oracle.py",
        LAB / "manifests/midpoint-switching-pairing-2026-09-20.json",
    ]
    return {
        "status": "complete_selector_obstruction",
        "physical_parameters": {"geometry": "square", "p": "1/2", "q": "1"},
        "new_physical_record_samples": 0,
        "decoder_runs": 0,
        "paired_mass_inequality": "sum_Q min(N0(Q),N1(Q)) >= number of disjoint charge-matched cross-sector pairs",
        "selector_definition": "enumerate simple paths that touch rough boundaries only at their endpoints; order their left-to-right y-coordinate sequences lexicographically, then choose the lower or upper extreme among residual-directed paths",
        "size_audits": sizes,
        "primary_source_boundary": {
            "source": "Duminil-Copin, Introduction to Bernoulli percolation, 2017, RSW section",
            "url": "https://www.ihes.fr/~duminil/publi/2017percolation.pdf",
            "supported": "ordinary RSW lower-bounds the existence of a box crossing",
            "not_supported": "RSW alone does not lower-bound invariance of a deterministic path selector after all edges on its selected crossing are reversed",
            "additional_prerequisite": "a selector-stability or suitable multi-arm/local-gadget event with a size-uniform probability bound",
        },
        "decision": {
            "outcome": "natural_selector_obstruction_and_missing_event_theorem",
            "established": "Every simple residual crossing flip preserves the full charge and flips logical parity. Selector-stable subsets give valid finite involutive pairings.",
            "obstruction": "Both extremal selectors are noninjective on the full crossing event and lose selector stability; standalone directed plaquette flips preserve logical parity.",
            "finite_only": "The stable pairing lower bound drops from 43/128 at L3 to 28353/131072 at L4; two sizes do not determine its thermodynamic limit.",
            "not_established": "No RSW consequence supplies a size-uniform probability for the selector-stable subset, and no nonzero limiting Bayes risk is proved.",
            "threshold_claim": "No square midpoint or decoding-threshold claim is promoted.",
        },
        "elapsed_seconds": elapsed,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files
        },
    }


def main():
    result = analyze()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
