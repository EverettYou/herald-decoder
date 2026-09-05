#!/usr/bin/env python3
"""Produce the registered exact-versus-BP evidence for Lab 006."""
from __future__ import annotations
import json
from pathlib import Path
from sun_fusion_bp import bp_marginals, exact_marginals, exact_posterior, path_graph, plaquette_graph

CASES = {
    "tree_path": (path_graph(), ((1, "3bar"), (0, "8"), (0, "8"), (1, "3"))),
    # Identity outcomes permit an empty loop or a globally occupied loop;
    # their correlation is precisely what a loopy BP fixed point can lose.
    "loopy_plaquette": (plaquette_graph(), ((0, "1"), (0, "1"), (0, "1"), (0, "1"))),
}

def main() -> None:
    output = {"model": "SU(3), p=0.18, full vertex record (m,R)", "cases": {}}
    for name, (graph, observation) in CASES.items():
        posterior = exact_posterior(graph, observation, p=0.18)
        exact = exact_marginals(posterior, len(graph.edges))
        bp, converged, iterations = bp_marginals(graph, observation, p=0.18)
        output["cases"][name] = {
            "edges": list(graph.edges), "observation": [list(x) for x in observation],
            "exact_edge_marginals": exact.tolist(), "bp_edge_marginals": bp.tolist(),
            "max_abs_difference": float(abs(exact - bp).max()),
            "bp_converged": bool(converged), "bp_iterations": int(iterations),
        }
    Path(__file__).parents[1].joinpath("results").mkdir(exist_ok=True)
    Path(__file__).parents[1].joinpath("results/small-graph-exact-vs-bp.json").write_text(json.dumps(output, indent=2) + "\n")

if __name__ == "__main__": main()
