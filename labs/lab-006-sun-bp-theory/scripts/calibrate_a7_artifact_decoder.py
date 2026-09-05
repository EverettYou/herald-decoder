#!/usr/bin/env python3
"""Calibrate the A7 runner against the accepted Lab 006 artifact decoder.

This script deliberately imports the artifact backend rather than reimplementing
its likelihood, boundary treatment, BP schedule, or matching projection.  The
only throughput experiment is calling that same directed sum-product decoder's
existing ``infer_batch`` endpoint on repeated fixed-seed artifact records.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np

from artifact_backend import MAX_BP_ITERATIONS, _cached_decoder, artifact_payload, warm_numba_kernels
from herald_decoder.lattice_model import honeycomb_graph, square_graph
from numba_fusion_decoder import GROUP_IRREPS, GeneralizedSyndrome
from sun_fusion_bp import Graph


GROUPS = ("None", "U1", "SU2", "SU3")
LATTICES = ("square", "honeycomb")
SIZES = (5, 9)
SEEDS = tuple(range(9101, 9109))
PRIOR = 0.18
DAMPING = 0.5
TOLERANCE = 1e-10
BATCH_SIZE = 256
ATOL = 1e-12


def graph_context(lattice: str, size: int):
    lattice_graph = square_graph(size) if lattice == "square" else honeycomb_graph(size)
    observed_ids = tuple(vertex for vertex, edges in enumerate(lattice_graph.incident_edges) if edges)
    observed_row = {vertex: row for row, vertex in enumerate(observed_ids)}
    detector_rows = np.asarray(
        [observed_row[vertex] for vertex in lattice_graph.detector_vertices], dtype=np.int64,
    )
    boundary_factor_rows = tuple(
        row for row, vertex in enumerate(observed_ids)
        if not lattice_graph.vertices[vertex].detector
    )
    graph = Graph(
        tuple(f"v{vertex}" for vertex in observed_ids),
        tuple((f"v{tail}", f"v{head}") for tail, head in lattice_graph.edges),
    )
    return lattice_graph, graph, detector_rows, boundary_factor_rows


def observation(payload: dict, observed_ids: tuple[int, ...]) -> GeneralizedSyndrome:
    m_vertices = set(payload["observation"]["m_vertices"])
    return GeneralizedSyndrome(
        np.asarray([int(vertex in m_vertices) for vertex in observed_ids], dtype=np.uint8),
        tuple(payload["observation"]["irreps"]),
    )


def assert_close(label: str, actual, expected) -> float:
    difference = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
    if difference > ATOL:
        raise AssertionError(f"{label}: max abs difference {difference} exceeds {ATOL}")
    return difference


def calibrate_cell(group: str, lattice: str, size: int) -> dict:
    lattice_graph, graph, detector_rows, boundary_factor_rows = graph_context(lattice, size)
    samples = []
    max_scalar_artifact_difference = 0.0
    max_scalar_baseline_difference = 0.0
    scalar_inference_ns = 0

    for seed in SEEDS:
        request = {"group": group, "lattice": lattice, "L": size, "p": PRIOR, "seed": seed}
        payload = artifact_payload(request)
        if payload["model"]["orientation_mode"] != "directed":
            raise AssertionError("artifact calibration must use directed orientation")
        if payload["model"]["algorithm"] != "sum_product" or payload["model"]["damping"] != DAMPING:
            raise AssertionError("artifact default schedule drifted")
        if payload["model"]["measure_boundary_representation"]:
            raise AssertionError("artifact unexpectedly measures rough-boundary R")
        observed_ids = tuple(vertex for vertex, edges in enumerate(lattice_graph.incident_edges) if edges)
        record = observation(payload, observed_ids)
        matching_m = record.m[detector_rows]
        for arm, use_irrep, expected_marginals, expected_weights, expected_correction, expected_bp in (
            ("representation_herald", True, payload["posterior"]["edge_marginals"], payload["posterior"]["edge_weights"], payload["decoder"]["correction_edges"], payload["decoder"]["bp"]),
            ("syndrome_only", False, payload["m_only_baseline"]["edge_marginals"], payload["m_only_baseline"]["edge_weights"], payload["m_only_baseline"]["correction_edges"], payload["m_only_baseline"]["bp"]),
        ):
            decoder = _cached_decoder(
                graph, group=group, orientation_mode="directed", use_irrep=use_irrep,
                p=PRIOR, damping=DAMPING, boundary_factor_rows=boundary_factor_rows,
                measure_boundary_representation=False, algorithm="sum_product",
            )
            decoder.matrix = lattice_graph.check_matrix
            start = perf_counter_ns()
            decoded = decoder.decode(record, matching_m)
            scalar_inference_ns += perf_counter_ns() - start
            max_scalar_artifact_difference = max(
                max_scalar_artifact_difference,
                assert_close(f"{group}/{lattice}/L{size}/{seed}/{arm} posterior", decoded.bp.edge_marginals, expected_marginals),
                assert_close(f"{group}/{lattice}/L{size}/{seed}/{arm} weights", decoded.edge_weights, expected_weights),
            )
            if np.flatnonzero(decoded.correction).astype(int).tolist() != expected_correction:
                raise AssertionError(f"{group}/{lattice}/L{size}/{seed}/{arm} correction differs from artifact")
            if (decoded.bp.converged != expected_bp["converged"] or
                    decoded.bp.iterations != expected_bp["iterations"]):
                raise AssertionError(f"{group}/{lattice}/L{size}/{seed}/{arm} BP metadata differs from artifact")
            samples.append((arm, record, decoded.bp))

    # Artifact's no-symmetry control must supply no additional R information.
    if group == "None":
        for index in range(0, len(samples), 2):
            full, m_only = samples[index], samples[index + 1]
            max_scalar_baseline_difference = max(
                max_scalar_baseline_difference,
                assert_close("None full/m-only identity", full[2].edge_marginals, m_only[2].edge_marginals),
            )

    batch_differences, batch_iterations_match, batch_convergence_match = [], True, True
    batch_inference_ns = 0
    scalar_bp_ns = 0
    for arm, use_irrep in (("representation_herald", True), ("syndrome_only", False)):
        arm_samples = [(record, scalar) for sample_arm, record, scalar in samples if sample_arm == arm]
        records = [arm_samples[index % len(arm_samples)] for index in range(BATCH_SIZE)]
        m = np.asarray([record.m for record, _ in records], dtype=np.uint8)
        codes = {label: code for code, label in enumerate(GROUP_IRREPS[group])}
        irreps = np.asarray([[codes[label] for label in record.irrep] for record, _ in records], dtype=np.int8)
        decoder = _cached_decoder(
            graph, group=group, orientation_mode="directed", use_irrep=use_irrep,
            p=PRIOR, damping=DAMPING, boundary_factor_rows=boundary_factor_rows,
            measure_boundary_representation=False, algorithm="sum_product",
        )
        # This is intentionally BP-only: the same stage subsequently batched
        # below. Matching is separately retained per shot in the LER runner.
        for record, _ in records:
            start = perf_counter_ns()
            decoder.infer(record)
            scalar_bp_ns += perf_counter_ns() - start
        start = perf_counter_ns()
        batch_marginals, batch_converged, batch_iterations, _ = decoder.infer_batch(m, irreps)
        batch_inference_ns += perf_counter_ns() - start
        for index, (_, scalar) in enumerate(records):
            batch_differences.append(assert_close(f"{group}/{lattice}/L{size}/{arm}/batch[{index}]", batch_marginals[index], scalar.edge_marginals))
            batch_convergence_match &= bool(batch_converged[index]) == scalar.converged
            batch_iterations_match &= int(batch_iterations[index]) == scalar.iterations

    if not batch_convergence_match or not batch_iterations_match:
        raise AssertionError(f"{group}/{lattice}/L{size}: batch BP metadata differs from scalar artifact BP")
    return {
        "group": group, "lattice": lattice, "L": size, "p": PRIOR,
        "artifact_defaults": {"orientation": "directed", "algorithm": "sum_product", "damping": DAMPING, "max_iterations": MAX_BP_ITERATIONS, "tolerance": TOLERANCE, "measure_boundary_representation": False},
        "scalar_records_per_arm": len(SEEDS), "batch_records_per_arm": BATCH_SIZE,
        "max_abs_scalar_artifact_difference": max_scalar_artifact_difference,
        "max_abs_batch_scalar_difference": max(batch_differences, default=0.0),
        "none_full_syndrome_only_difference": max_scalar_baseline_difference,
        "batch_convergence_matches": batch_convergence_match,
        "batch_iteration_matches": batch_iterations_match,
        "timing_ms": {
            "scalar_artifact_decode_per_record": scalar_inference_ns / (len(samples) * 1e6),
            "scalar_bp_per_record": scalar_bp_ns / (2 * BATCH_SIZE * 1e6),
            "batch_bp_per_record": batch_inference_ns / (2 * BATCH_SIZE * 1e6),
            "batch_bp_speedup_over_scalar_bp": scalar_bp_ns / batch_inference_ns,
        },
    }


def main() -> None:
    warm_numba_kernels()
    cells = [calibrate_cell(group, lattice, size) for group in GROUPS for lattice in LATTICES for size in SIZES]
    output = {
        "protocol": "lab006-a7-artifact-default-calibration-2026-09-04",
        "purpose": "Artifact decoder calibration only; no new decoder, schedule tuning, LER, or threshold sample.",
        "artifact_default": {"orientation": "directed", "algorithm": "sum_product", "damping": DAMPING, "max_iterations": MAX_BP_ITERATIONS, "tolerance": TOLERANCE, "measure_boundary_representation": False},
        "cells": cells,
        "summary": {
            "cells": len(cells),
            "max_abs_scalar_artifact_difference": max(cell["max_abs_scalar_artifact_difference"] for cell in cells),
            "max_abs_batch_scalar_difference": max(cell["max_abs_batch_scalar_difference"] for cell in cells),
            "all_batch_convergence_match": all(cell["batch_convergence_matches"] for cell in cells),
            "all_batch_iteration_match": all(cell["batch_iteration_matches"] for cell in cells),
        },
    }
    target = Path(__file__).parents[1] / "results/a7-artifact-default-calibration.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
