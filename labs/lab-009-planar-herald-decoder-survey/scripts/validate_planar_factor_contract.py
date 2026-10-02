"""Independent L=2 checks of the generic planar binary-factor interface."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from herald_decoder import LatticeGraph, honeycomb_graph  # noqa: E402
from herald_decoder.planar_ml import PlanarParitySolver  # noqa: E402


def weighted_oracle(graph, p, syndrome, factors):
    """Enumerate physical edge vectors without using a decoder reference."""
    edge_count = len(graph.edges)
    errors = ((np.arange(1 << edge_count)[:, None] >> np.arange(edge_count)) & 1).astype(np.uint8)
    parity = (errors.astype(int) @ graph.check_matrix.toarray().T) & 1
    selected = np.all(parity == syndrome, axis=1)
    weights = p ** errors.sum(axis=1) * (1 - p) ** (edge_count - errors.sum(axis=1))
    for vertex, factor in zip(graph.detector_vertices, factors):
        incident = graph.incident_edges[vertex]
        weights *= factor[tuple(errors[:, incident].T)]
    sectors = errors[:, list(graph.logical_edges)].sum(axis=1) & 1
    z = np.bincount(sectors[selected].astype(int), weights=weights[selected], minlength=2)
    return z / z.sum()


def permuted_graph_and_factors(graph, factors, order):
    old_to_new = np.empty(len(order), dtype=int)
    old_to_new[order] = np.arange(len(order))
    graph2 = LatticeGraph(
        graph.name, graph.size, graph.vertices,
        tuple(graph.edges[int(i)] for i in order),
        frozenset(int(old_to_new[i]) for i in graph.logical_edges),
        graph.logical_line,
    )
    factors2 = []
    for vertex, factor in zip(graph.detector_vertices, factors):
        old_incident = graph.incident_edges[vertex]
        new_incident = graph2.incident_edges[vertex]
        axes = [old_incident.index(int(order[i])) for i in new_incident]
        factors2.append(np.transpose(factor, axes))
    return graph2, factors2


def run():
    rng = np.random.default_rng(100913)
    graph = honeycomb_graph(2)
    p = 0.23
    solver = PlanarParitySolver(graph, p=p)
    errors = ((np.arange(1 << len(graph.edges))[:, None] >> np.arange(len(graph.edges))) & 1).astype(np.uint8)
    order = rng.permutation(len(graph.edges))
    worst_error = 0.0
    checked = 0
    for index in rng.choice(len(errors), size=12, replace=False):
        syndrome = graph.true_syndrome(errors[index])
        factors = [rng.uniform(0.2, 1.5, size=(2,) * len(graph.incident_edges[v]))
                   for v in graph.detector_vertices]
        expected = weighted_oracle(graph, p, syndrome, factors)
        graph2, factors2 = permuted_graph_and_factors(graph, factors, order)
        candidates = [
            solver.posterior_from_factors(syndrome, factors)[0],
            solver.posterior_from_factors(syndrome, factors, solver.representative(syndrome, 0))[0],
            solver.posterior_from_factors(syndrome, factors, solver.representative(syndrome, 1))[0],
            PlanarParitySolver(graph2, p=p).posterior_from_factors(syndrome, factors2)[0],
        ]
        error = max(float(np.max(np.abs(candidate - expected))) for candidate in candidates)
        worst_error = max(worst_error, error)
        assert error < 1e-9, (index, error, expected, candidates)
        checked += 1

    syndrome = graph.true_syndrome(errors[1])
    factors = [np.ones((2,) * len(graph.incident_edges[v])) for v in graph.detector_vertices]
    negative = [factor.copy() for factor in factors]
    negative[0].flat[0] = -0.1
    nonfinite = [factor.copy() for factor in factors]
    nonfinite[0].flat[0] = np.nan
    rejected = []
    for label, candidate in (("negative", negative), ("nonfinite", nonfinite)):
        try:
            solver.posterior_from_factors(syndrome, candidate)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(f"{label} local factor was accepted")

    result = {
        "status": "passed", "seed": 100913, "p": p, "L": 2,
        "cases": checked, "reference_choices_per_case": 3,
        "edge_order_permutations_per_case": 1,
        "max_posterior_error": worst_error, "tolerance": 1e-9,
        "rejected_factors": rejected,
        "scope": "generic positive binary factors on L=2 only; no asymptotic or all-record stability claim",
    }
    output = Path(__file__).resolve().parents[1] / "results" / "planar-factor-contract-validation.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    run()
