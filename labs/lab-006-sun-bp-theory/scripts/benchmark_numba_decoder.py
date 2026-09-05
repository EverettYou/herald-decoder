#!/usr/bin/env python3
"""Registered A1 correctness and warmed throughput benchmark."""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np

from numba_fusion_decoder import (
    FastFusionBeliefMatchingDecoder, GeneralizedSyndrome, IRREP_TO_CODE,
)
from sun_fusion_bp import bp_marginals, fusion_distribution, ring_graph


def sample_observations(graph, count: int, seed: int, p: float):
    rng = np.random.default_rng(seed)
    records = []
    for _ in range(count):
        error = (rng.random(len(graph.edges)) < p).astype(np.uint8)
        record = []
        for leaves in graph.incident:
            active = tuple(rep for edge, rep in leaves if error[edge])
            channel = fusion_distribution(active)
            labels, probabilities = zip(*channel.items())
            irrep = str(rng.choice(labels, p=probabilities))
            record.append((len(active) & 1, irrep))
        records.append(tuple(record))
    return records


def observation_object(record):
    return GeneralizedSyndrome(
        np.asarray([x[0] for x in record], dtype=np.uint8),
        tuple(x[1] for x in record),
    )


def main():
    p = .18
    graph = ring_graph(64)
    records = sample_observations(graph, 260, 6001, p)
    warmup, measured = records[:4], records[4:]
    decoder = FastFusionBeliefMatchingDecoder(graph, p=p)

    for record in warmup:
        decoder.infer(observation_object(record))
        bp_marginals(graph, record, p, max_iter=80, tol=1e-10, damping=.25)

    reference_times, scalar_times = [], []
    reference_results, scalar_results = [], []
    for record in measured:
        start = perf_counter_ns()
        reference_results.append(bp_marginals(graph, record, p, max_iter=80, tol=1e-10, damping=.25))
        reference_times.append(perf_counter_ns() - start)
        start = perf_counter_ns()
        scalar_results.append(decoder.infer(observation_object(record)))
        scalar_times.append(perf_counter_ns() - start)

    m = np.asarray([[x[0] for x in record] for record in measured], dtype=np.uint8)
    irreps = np.asarray([[IRREP_TO_CODE[x[1]] for x in record] for record in measured], dtype=np.int8)
    decoder.infer_batch(m[:4], irreps[:4])
    batch_times = []
    batch_outputs = np.empty((len(measured), len(graph.edges)))
    for start_index in range(0, len(measured), 32):
        stop = start_index + 32
        start = perf_counter_ns()
        result = decoder.infer_batch(m[start_index:stop], irreps[start_index:stop])
        elapsed = perf_counter_ns() - start
        batch_outputs[start_index:stop] = result[0]
        batch_times.append(elapsed / (stop - start_index))

    max_reference_difference = max(
        float(np.max(np.abs(ref[0] - candidate.edge_marginals)))
        for ref, candidate in zip(reference_results, scalar_results, strict=True)
    )
    max_batch_difference = max(
        float(np.max(np.abs(candidate.edge_marginals - batch_outputs[index])))
        for index, candidate in enumerate(scalar_results)
    )

    correction_checks = 0
    for record in measured[:16]:
        observation = observation_object(record)
        decoded = decoder.decode(observation)
        recovered = np.asarray(decoder.matrix @ decoded.correction, dtype=np.uint8).ravel() & 1
        if np.array_equal(recovered, observation.m):
            correction_checks += 1

    python_median = float(np.median(reference_times) / 1e6)
    scalar_median = float(np.median(scalar_times) / 1e6)
    batch_median = float(np.median(batch_times) / 1e6)
    payload = {
        "protocol": "lab006-a3-full-irrep-belief-matching-2026-09-04",
        "observation_record": ["m", "R"],
        "graph": {"kind": "oriented_ring", "vertices": 64, "edges": 64},
        "observations": 256, "warmups_per_arm": 4,
        "equivalence": {
            "max_abs_python_vs_numba_scalar": max_reference_difference,
            "max_abs_numba_scalar_vs_batch": max_batch_difference,
            "convergence_matches": int(sum(ref[1] == candidate.converged for ref, candidate in zip(reference_results, scalar_results, strict=True))),
            "iteration_matches": int(sum(ref[2] == candidate.iterations for ref, candidate in zip(reference_results, scalar_results, strict=True))),
        },
        "matching": {"syndrome_faithful": correction_checks, "checked": 16},
        "timing_ms_per_observation": {
            "python_median": python_median,
            "numba_scalar_median": scalar_median,
            "numba_batch_chunk_median": batch_median,
        },
        "speedup": {
            "scalar_over_python": python_median / scalar_median,
            "batch_over_python": python_median / batch_median,
            "batch_over_scalar": scalar_median / batch_median,
        },
    }
    target = Path(__file__).parents[1] / "results/a1-numba-belief-matching.json"
    target.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
