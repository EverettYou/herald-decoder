from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_honeycomb import periodic_honeycomb  # noqa: E402
from d4_r4 import exact_conditioned_logical_posterior  # noqa: E402
from d4_sampler import observation_from_error_edges  # noqa: E402


def _fixture():
    lattice = periodic_honeycomb(2)
    physical = np.zeros(lattice.edge_count, dtype=np.uint8)
    physical[[0, 3, 6]] = 1
    observation = observation_from_error_edges(lattice, physical, seed=11)
    assert observation.charge_outcomes is not None
    flux = np.zeros(lattice.vertex_count, dtype=np.uint8)
    flux[list(observation.flux_vertices)] = 1
    return lattice, flux, np.asarray(observation.charge_outcomes, dtype=np.int64)


def test_r4_low_p_sums_four_sectors_and_exposes_map_tie() -> None:
    lattice, flux, charge = _fixture()
    result = exact_conditioned_logical_posterior(lattice, flux, charge, 0.1)
    probabilities = sorted(
        sector.posterior_probability for sector in result.sectors
    )
    assert result.total_candidate_count == 4
    assert len(result.sectors) == 4
    assert np.allclose(probabilities, [1 / 244, 81 / 244, 81 / 244, 81 / 244])
    assert np.isclose(result.bayes_logical_failure_probability, 163 / 244)
    assert np.isclose(result.top_two_log2_evidence_gap, 0.0)


def test_r4_high_p_unique_map_still_has_nonzero_sector_bayes_risk() -> None:
    lattice, flux, charge = _fixture()
    result = exact_conditioned_logical_posterior(lattice, flux, charge, 0.6)
    probabilities = sorted(
        sector.posterior_probability for sector in result.sectors
    )
    assert np.allclose(probabilities, [4 / 21, 4 / 21, 4 / 21, 3 / 7])
    assert np.isclose(result.bayes_logical_failure_probability, 4 / 7)
    assert np.isclose(
        result.top_two_log2_evidence_gap, np.log2(9 / 4)
    )


def test_r4_posterior_normalizes_and_reports_positive_entropy() -> None:
    lattice, flux, charge = _fixture()
    for error_rate in (0.1, 0.6):
        result = exact_conditioned_logical_posterior(
            lattice, flux, charge, error_rate
        )
        assert np.isclose(
            sum(sector.posterior_probability for sector in result.sectors), 1.0
        )
        assert result.conditional_entropy_bits > 0.0


def test_r4_reference_relabeling_preserves_evidence_multiset_and_risk() -> None:
    lattice, flux, charge = _fixture()
    masks = (73, 82, 268, 279)
    baseline = exact_conditioned_logical_posterior(lattice, flux, charge, 0.1)
    baseline_probabilities = sorted(
        sector.posterior_probability for sector in baseline.sectors
    )
    for mask in masks:
        reference = np.asarray(
            [(mask >> edge) & 1 for edge in range(lattice.edge_count)],
            dtype=np.uint8,
        )
        result = exact_conditioned_logical_posterior(
            lattice, flux, charge, 0.1, reference_error=reference
        )
        assert np.allclose(
            sorted(sector.posterior_probability for sector in result.sectors),
            baseline_probabilities,
        )
        assert np.isclose(
            result.bayes_logical_failure_probability,
            baseline.bayes_logical_failure_probability,
        )
        assert np.isclose(
            result.conditional_entropy_bits, baseline.conditional_entropy_bits
        )


def test_r4_sector_evidence_genuinely_sums_multiple_configurations() -> None:
    lattice = periodic_honeycomb(2)
    flux = np.asarray((1, 0, 1, 1, 1, 1, 0, 1), dtype=np.uint8)
    charge = np.full(lattice.vertex_count, -1, dtype=np.int64)
    result = exact_conditioned_logical_posterior(lattice, flux, charge, 0.1)
    assert result.total_candidate_count == 2
    assert len(result.sectors) == 1
    assert result.sectors[0].candidate_count == 2
    assert np.isclose(result.sectors[0].posterior_probability, 1.0)
    assert np.isclose(result.bayes_logical_failure_probability, 0.0)
    single_log_weight = 3 * np.log2(0.1) + 9 * np.log2(0.9)
    assert np.isclose(result.log2_total_evidence, single_log_weight + 1.0)
