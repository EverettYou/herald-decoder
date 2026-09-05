#!/usr/bin/env python3
"""Profile the accepted A7 full-record LER path on honeycomb L=9, SU(3).

The reported timings intentionally separate the work that Numba accelerates
(batched BP) from Monte-Carlo record generation and per-shot weighted matching.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pymatching

from artifact_backend import _cached_decoder, warm_numba_kernels
from run_a7_ler import TRIVIAL, context, select
from numba_fusion_decoder import GROUP_IRREPS, group_fusion_distribution

HERE = Path(__file__).resolve().parent
RESULT = HERE.parent / "results/a7-profile-honeycomb-L9-SU3.json"
GROUP = "SU3"
P = 0.18
# A 32-shot diagnostic batch is sufficient for a stable stage split while
# avoiding interference with the separately running 20,000-shot acquisition.
# Calibration has already established that 256-shot batch BP provides no
# material throughput gain on this geometry.
BATCH = 32
REPETITIONS = 3


def elapsed_ns(callback):
    start = perf_counter_ns()
    value = callback()
    return value, perf_counter_ns() - start


def main() -> None:
    warm_numba_kernels()
    (setup, setup_ns) = elapsed_ns(lambda: context("honeycomb", 9))
    model, graph, detector_rows, boundary_rows = setup
    check_matrix = model.check_matrix
    decoder, decoder_ns = elapsed_ns(
        lambda: _cached_decoder(
            graph, group=GROUP, orientation_mode="directed", use_irrep=True,
            p=P, damping=.5, boundary_factor_rows=boundary_rows,
            measure_boundary_representation=False, algorithm="sum_product",
        )
    )
    decoder.matrix = check_matrix
    codes = {label: code for code, label in enumerate(GROUP_IRREPS[GROUP])}
    rng = np.random.default_rng(9062026)
    stages = {key: [] for key in (
        "random_arrays", "record_generation", "bp_batch", "posterior_weights",
        "matching_construction", "matching_decode", "residual_and_logical",
    )}
    nonconverged = 0

    for _ in range(REPETITIONS):
        (arrays, duration) = elapsed_ns(lambda: (rng.random((BATCH, len(graph.edges))), rng.random((BATCH, len(graph.vertices)))))
        stages["random_arrays"].append(duration)
        error_uniforms, fusion_uniforms = arrays
        errors = (error_uniforms < P).astype(np.uint8)

        def records():
            m = np.zeros((BATCH, len(graph.vertices)), dtype=np.uint8)
            labels = np.empty((BATCH, len(graph.vertices)), dtype=np.int8)
            for sample in range(BATCH):
                for vertex, leaves in enumerate(graph.incident):
                    active = tuple("fund" if rep == "3" else "anti" for edge, rep in leaves if errors[sample, edge])
                    if vertex not in boundary_rows:
                        m[sample, vertex] = len(active) & 1
                    label = TRIVIAL[GROUP] if vertex in boundary_rows else select(group_fusion_distribution(GROUP, active), fusion_uniforms[sample, vertex])
                    labels[sample, vertex] = codes[label]
            return m, labels

        (record, duration) = elapsed_ns(records)
        stages["record_generation"].append(duration)
        m, labels = record
        matching_m = m[:, detector_rows]
        ((marginals, converged, _, _), duration) = elapsed_ns(lambda: decoder.infer_batch(m, labels))
        stages["bp_batch"].append(duration)
        nonconverged += int(BATCH - np.count_nonzero(converged))
        (weights, duration) = elapsed_ns(lambda: np.log((1 - np.clip(marginals, 1e-12, 1 - 1e-12)) / np.clip(marginals, 1e-12, 1 - 1e-12)))
        stages["posterior_weights"].append(duration)

        corrections = []
        build_ns = decode_ns = 0
        for sample in range(BATCH):
            (matching, duration) = elapsed_ns(lambda sample=sample: pymatching.Matching.from_check_matrix(check_matrix, weights=weights[sample]))
            build_ns += duration
            (correction, duration) = elapsed_ns(lambda matching=matching, sample=sample: matching.decode(matching_m[sample]).astype(np.uint8))
            decode_ns += duration
            corrections.append(correction)
        stages["matching_construction"].append(build_ns)
        stages["matching_decode"].append(decode_ns)

        def verify():
            logical = 0
            for sample, correction in enumerate(corrections):
                residual = matching_m[sample] ^ (np.asarray(check_matrix @ correction).ravel().astype(np.uint8) & 1)
                logical += int(bool(np.any(residual)) or model.logical_parity(errors[sample] ^ correction))
            return logical

        (_, duration) = elapsed_ns(verify)
        stages["residual_and_logical"].append(duration)

    per_shot_ns = {key: float(np.median(values) / BATCH) for key, values in stages.items()}
    total = sum(per_shot_ns.values())
    payload = {
        "protocol": "lab006-a7-end-to-end-profile",
        "status": "complete",
        "scope": {"lattice": "honeycomb", "L": 9, "group": GROUP, "p": P, "arm": "representation_herald", "batch_size": BATCH, "repetitions": REPETITIONS},
        "topology": {"vertices": len(graph.vertices), "edges": len(graph.edges), "detectors": len(detector_rows)},
        "one_time_setup_ms": {"context": setup_ns / 1e6, "cached_decoder_lookup_or_create": decoder_ns / 1e6},
        "per_shot_ms_median": {key: value / 1e6 for key, value in per_shot_ns.items()},
        "per_shot_share_percent": {key: 100 * value / total for key, value in per_shot_ns.items()},
        "end_to_end_per_shot_ms_median": total / 1e6,
        "nonconverged_shots": nonconverged,
        "total_profiled_shots": BATCH * REPETITIONS,
        "note": "BP time is amortized over the stated diagnostic batch size; matching construction and matching decode are measured separately for every shot because posterior weights differ by shot.",
    }
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
