from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_charge import build_charge_lattice, charge_chain_boundary  # noqa: E402
from d4_honeycomb import BLUE, GREEN, paper_periodic_honeycomb  # noqa: E402
from d4_pipeline import (  # noqa: E402
    decode_physical_error,
    sample_postflux_charge_outcomes,
)
from d4_postflux import (  # noqa: E402
    accumulate_postflux_constraints,
    infer_periodic_postflux_relations,
    periodic_local_neighborhood,
)


def _paper_winding_loop(lattice) -> np.ndarray:
    period_x, period_y = (int(value) for value in lattice.period_matrix[:, 0])
    coordinates = [(0, 0)]
    coordinates.extend((step, 0) for step in range(1, period_x + 1))
    coordinates.extend(
        (period_x, step) for step in range(1, period_y + 1)
    )
    selected = np.zeros(lattice.edge_count, dtype=np.uint8)
    for current, following in zip(coordinates, coordinates[1:]):
        green = lattice.vertex_id(*current, GREEN)
        selected[lattice.edge_between(lattice.vertex_id(*current, BLUE), green)] = 1
        selected[lattice.edge_between(green, lattice.vertex_id(*following, BLUE))] = 1
    return selected


def test_zero_error_runs_both_public_modes_end_to_end() -> None:
    lattice = paper_periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    for mode in ("syndrome_only", "heralded"):
        record = decode_physical_error(lattice, physical, mode=mode, seed=7)
        assert record.status == "decoded"
        assert not record.logical_error
        assert record.flux_recovery is not None
        assert record.postflux_relations is not None
        assert record.postflux_charge_outcomes is not None
        assert record.charge_recovery is not None
        assert record.postflux_relations.active_vertices == ()
        assert json.loads(json.dumps(record.to_dict()))["mode"] == mode


def test_postflux_sampler_is_deterministic_uniform_support() -> None:
    lattice = paper_periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    _, edges = periodic_local_neighborhood(
        lattice, lattice.vertex_id(0, 0, BLUE)
    )
    physical[list(edges)] = (1, 1, 0)
    relations = infer_periodic_postflux_relations(
        lattice, physical, np.zeros_like(physical)
    )
    first = sample_postflux_charge_outcomes(
        lattice.vertex_count, relations, seed=99
    )
    second = sample_postflux_charge_outcomes(
        lattice.vertex_count, relations, seed=99
    )
    assert np.array_equal(first, second)
    analysis = accumulate_postflux_constraints(
        lattice.vertex_count,
        relations.active_vertices,
        relations.entanglement_pairs,
        first,
    )
    assert analysis.allowed


def test_physical_winding_short_circuits_both_modes() -> None:
    lattice = paper_periodic_honeycomb(2)
    physical = _paper_winding_loop(lattice)
    for mode in ("syndrome_only", "heralded"):
        record = decode_physical_error(lattice, physical, mode=mode, seed=3)
        assert record.status == "physical_winding_failure"
        assert record.logical_error
        assert record.flux_recovery is None
        assert record.charge_recovery is None


def test_bounded_truth_matrix_covers_both_modes_and_final_invariants() -> None:
    lattice = paper_periodic_honeycomb(2)
    seen = {"syndrome_only": set(), "heralded": set()}
    for error_rate in (0.0, 0.05, 0.10):
        for seed in range(16):
            physical_seed = int(
                np.random.SeedSequence([seed, int(error_rate * 1000)]).generate_state(1)[0]
            )
            physical = (
                np.random.default_rng(physical_seed).random(lattice.edge_count)
                < error_rate
            )
            records = {
                mode: decode_physical_error(
                    lattice, physical, mode=mode, seed=20_000 + seed
                )
                for mode in ("syndrome_only", "heralded")
            }
            assert records["syndrome_only"].physical_error_edges == records[
                "heralded"
            ].physical_error_edges
            assert records["syndrome_only"].observation == records[
                "heralded"
            ].observation
            for mode, record in records.items():
                seen[mode].add(record.status)
                assert record.logical_error == (
                    record.status != "decoded"
                    or (
                        record.charge_recovery is not None
                        and record.charge_recovery.logical_error
                    )
                )
                if record.status != "decoded":
                    continue
                assert record.flux_recovery is not None
                assert not record.flux_recovery.logical_error
                assert record.postflux_relations is not None
                assert record.postflux_charge_outcomes is not None
                assert record.charge_recovery is not None
                public_second = np.asarray(record.postflux_charge_outcomes)
                assert set(public_second.tolist()) <= {0, 1}
                internal_second = public_second.astype(np.int64)
                inactive = set(range(lattice.vertex_count)) - set(
                    record.postflux_relations.active_vertices
                )
                internal_second[list(inactive)] = -1
                constraints = accumulate_postflux_constraints(
                    lattice.vertex_count,
                    record.postflux_relations.active_vertices,
                    record.postflux_relations.entanglement_pairs,
                    internal_second,
                )
                assert constraints.allowed
                for color, result in (
                    (BLUE, record.charge_recovery.blue),
                    (GREEN, record.charge_recovery.green),
                ):
                    assert not np.any(
                        charge_chain_boundary(
                            build_charge_lattice(lattice, color), result.residual
                        )
                    )
    assert "decoded" in seen["syndrome_only"]
    assert "decoded" in seen["heralded"]
