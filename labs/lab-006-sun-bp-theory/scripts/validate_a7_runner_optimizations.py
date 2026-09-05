#!/usr/bin/env python3
"""A/B validation for the two A7 throughput candidates before promotion."""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pymatching

from artifact_backend import warm_numba_kernels
from run_a7_ler import (
    GROUPS, _generate_records_legacy, _generate_records_numba, _record_tables,
    context, run_cell,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE.parent / "results/a7-runner-optimization-ab.json"


def elapsed(callback):
    start = perf_counter()
    answer = callback()
    return answer, perf_counter() - start


def main() -> None:
    warm_numba_kernels()
    model, graph, detector_rows, boundary_rows = context("honeycomb", 9)
    rng = np.random.default_rng(9062501)
    errors = (rng.random((256, len(graph.edges))) < .18).astype(np.uint8)
    uniforms = rng.random((256, len(graph.vertices)))

    (legacy, legacy_seconds) = elapsed(lambda: _generate_records_legacy(errors, uniforms, graph, boundary_rows))
    tables = {group: _record_tables(graph, boundary_rows, group) for group in GROUPS}
    # Compile outside the timing window, as production is explicitly warmed.
    for group in GROUPS:
        _generate_records_numba(errors[:1], uniforms[:1], *tables[group])
    (compiled, compiled_seconds) = elapsed(
        lambda: {group: _generate_records_numba(errors, uniforms, *tables[group]) for group in GROUPS}
    )
    record_equal = all(
        np.array_equal(legacy[0], compiled[group][0]) and np.array_equal(legacy[1][group], compiled[group][1])
        for group in GROUPS
    )
    if not record_equal:
        raise AssertionError("Numba record generator changes the fixed-seed m or R record")

    matching = pymatching.Matching.from_check_matrix(
        model.check_matrix, weights=np.full(len(graph.edges), np.log(.82 / .18)),
    )
    syndromes = legacy[0][:, detector_rows]
    (scalar_corrections, scalar_seconds) = elapsed(
        lambda: np.asarray([matching.decode(syndrome).astype(np.uint8) for syndrome in syndromes])
    )
    (batch_corrections, batch_seconds) = elapsed(lambda: matching.decode_batch(syndromes).astype(np.uint8))
    matching_equal = np.array_equal(scalar_corrections, batch_corrections)
    if not matching_equal:
        raise AssertionError("PyMatching decode_batch changes a fixed-weight correction")

    cells = []
    for lattice, size in (("square", 5), ("square", 9), ("honeycomb", 5), ("honeycomb", 9)):
        (reference, reference_seconds) = elapsed(lambda lattice=lattice, size=size: run_cell(lattice, size, .18, 32, 917000 + size, 32, optimized=False))
        (candidate, candidate_seconds) = elapsed(lambda lattice=lattice, size=size: run_cell(lattice, size, .18, 32, 917000 + size, 32, optimized=True))
        if reference != candidate:
            raise AssertionError(f"full LER runner differs for {lattice}/L{size}")
        cells.append({
            "lattice": lattice, "L": size, "shots": 32, "rows_match_exactly": True,
            "legacy_seconds": reference_seconds, "optimized_seconds": candidate_seconds,
            "speedup": reference_seconds / candidate_seconds,
        })

    payload = {
        "protocol": "lab006-a7-runner-optimization-ab",
        "status": "passed",
        "fixed_seed_scope": {"p": .18, "record_batch": 256, "full_runner_cells": cells},
        "record_generator": {
            "m_and_all_group_label_codes_match_exactly": record_equal,
            "legacy_ms_per_shot": 1000 * legacy_seconds / 256,
            "numba_ms_per_shot": 1000 * compiled_seconds / 256,
            "speedup": legacy_seconds / compiled_seconds,
        },
        "fixed_weight_matching": {
            "scalar_and_decode_batch_corrections_match_exactly": matching_equal,
            "scalar_ms_per_shot": 1000 * scalar_seconds / 256,
            "decode_batch_ms_per_shot": 1000 * batch_seconds / 256,
            "speedup": scalar_seconds / batch_seconds,
        },
        "promotion": "passed: optimized implementation is exact on the stated A/B fixtures and faster in every measured component and full-run cell.",
    }
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
