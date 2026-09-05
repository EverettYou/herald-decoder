#!/usr/bin/env python3
"""Execute the preregistered Lab 006 A5 two-dimensional BP diagnostic scan."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from herald_decoder.lattice_model import honeycomb_graph, square_graph
from numba_fusion_decoder import (
    FastFusionBeliefMatchingDecoder,
    GeneralizedSyndrome,
    group_fusion_distribution,
)
from sun_fusion_bp import Graph

GROUPS = ("SU2", "SU3")
LATTICES = ("square", "honeycomb")
SIZES = (5, 7)
RATES = (0.1, 0.2, 0.3, 0.4)
SEEDS_PER_CELL = 4
TRIVIAL = {"SU2": "1", "SU3": "1"}


def decoder_graph(lattice: str, size: int) -> Graph:
    source = square_graph(size) if lattice == "square" else honeycomb_graph(size)
    return Graph(
        tuple(f"v{vertex}" for vertex in source.detector_vertices),
        tuple((f"v{tail}", f"v{head}") for tail, head in source.edges),
    )


def sample_record(graph: Graph, group: str, p: float, seed: int):
    rng = np.random.default_rng(seed)
    error = (rng.random(len(graph.edges)) < p).astype(np.uint8)
    records: list[tuple[int, str]] = []
    for leaves in graph.incident:
        active = tuple("fund" if rep == "3" else "anti" for edge, rep in leaves if error[edge])
        channel = group_fusion_distribution(group, active)
        labels, probabilities = zip(*channel.items())
        records.append((len(active) & 1, str(rng.choice(labels, p=probabilities))))
    return GeneralizedSyndrome(
        np.asarray([record[0] for record in records], dtype=np.uint8),
        tuple(record[1] for record in records),
    )


def arm_summary(rows: list[dict], prefix: str) -> dict:
    converged = [row[f"{prefix}_converged"] for row in rows]
    iterations = [row[f"{prefix}_iterations"] for row in rows]
    residuals = [row[f"{prefix}_residual"] for row in rows]
    return {
        "converged": int(sum(converged)),
        "total": len(rows),
        "fraction": float(np.mean(converged)),
        "iterations_mean": float(np.mean(iterations)),
        "iterations_max": int(max(iterations)),
        "residual_max": float(max(residuals)),
        "residual_median": float(np.median(residuals)),
    }


def main() -> None:
    observations: list[dict] = []
    cells: list[dict] = []
    cell_index = 0
    for lattice in LATTICES:
        for size in SIZES:
            graph = decoder_graph(lattice, size)
            for group in GROUPS:
                for p in RATES:
                    full = FastFusionBeliefMatchingDecoder(
                        graph, group=group, p=p, use_irrep=True,
                        max_iterations=80, damping=0.25, tolerance=1e-10,
                    )
                    baseline = FastFusionBeliefMatchingDecoder(
                        graph, group=group, p=p, use_irrep=False,
                        max_iterations=80, damping=0.25, tolerance=1e-10,
                    )
                    cell_rows: list[dict] = []
                    for replicate in range(SEEDS_PER_CELL):
                        seed = 61000 + 100 * cell_index + replicate
                        record = sample_record(graph, group, p, seed)
                        full_result = full.infer(record)
                        baseline_result = baseline.infer(record)
                        row = {
                            "lattice": lattice,
                            "L": size,
                            "group": group,
                            "p": p,
                            "replicate": replicate,
                            "seed": seed,
                            "nontrivial_R": int(sum(irrep != TRIVIAL[group] for irrep in record.irrep)),
                            "full_converged": full_result.converged,
                            "full_iterations": full_result.iterations,
                            "full_residual": full_result.max_message_delta,
                            "m_only_converged": baseline_result.converged,
                            "m_only_iterations": baseline_result.iterations,
                            "m_only_residual": baseline_result.max_message_delta,
                            "mean_abs_R_shift": float(np.mean(np.abs(
                                full_result.edge_marginals - baseline_result.edge_marginals
                            ))),
                        }
                        observations.append(row)
                        cell_rows.append(row)
                    cells.append({
                        "lattice": lattice,
                        "L": size,
                        "group": group,
                        "p": p,
                        "full": arm_summary(cell_rows, "full"),
                        "m_only": arm_summary(cell_rows, "m_only"),
                        "mean_abs_R_shift": float(np.mean([row["mean_abs_R_shift"] for row in cell_rows])),
                        "max_abs_R_shift": float(max(row["mean_abs_R_shift"] for row in cell_rows)),
                    })
                    cell_index += 1

    assert len(observations) == 128
    nonconverged_full = [row for row in observations if not row["full_converged"]]
    nonconverged_baseline = [row for row in observations if not row["m_only_converged"]]
    payload = {
        "protocol": "lab006-a5b-two-dimensional-convergence-scan-2026-09-04",
        "status": "complete",
        "registered_observations": 128,
        "executed_observations": len(observations),
        "schedule": {
            "kind": "synchronous", "damping": 0.25,
            "max_iterations": 80, "tolerance": 1e-10,
        },
        "global": {
            "full_converged": 128 - len(nonconverged_full),
            "m_only_converged": 128 - len(nonconverged_baseline),
            "full_nonconverged": len(nonconverged_full),
            "m_only_nonconverged": len(nonconverged_baseline),
            "mean_abs_R_shift": float(np.mean([row["mean_abs_R_shift"] for row in observations])),
        },
        "cells": cells,
        "observations": observations,
        "interpretation_boundary": (
            "This fixed 128-observation diagnostic probes convergence of one synchronous damped BP schedule. "
            "It is not a threshold, logical-error, exactness, or optimized-schedule result."
        ),
    }
    destination = HERE.parent / "results" / "a5b-two-dimensional-convergence-scan.json"
    destination.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["global"], indent=2))
    for cell in cells:
        if cell["full"]["converged"] < cell["full"]["total"] or cell["m_only"]["converged"] < cell["m_only"]["total"]:
            print(json.dumps(cell, indent=2))


if __name__ == "__main__":
    main()
