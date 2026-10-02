"""Exact selected-first-public-record mass census over the full same-flux coset."""

from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from math import comb
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j9e_quadratic_character_quotient import affine_basis, quadratic_sum


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9f-selected-first-mass-census-2026-09-28.json"
RESULT = LAB / "results/j9f-selected-first-mass-census-2026-09-28.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    budget = contract["budget"]
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    paths = {name: LAB / spec["path"] for name, spec in contract["pinned_inputs"].items()}
    assert all(sha(path) == contract["pinned_inputs"][name]["sha256"]
               for name, path in paths.items())
    old = {name: json.loads(path.read_text()) for name, path in paths.items()}
    known = old["j8i_result"]
    assert known["status"] == "all_support_complete_second_laws_closed"
    assert len(known["rows"]) == 55
    assert old["j8j_result"]["same_first_flux_error_count"] == 8192
    assert old["j9e_result"]["status"] == "quadratic_character_quotient_gate_verified"
    assert old["j9e_result"]["counters"]["first_mass_replays"] == 55
    assert old["j9e_result"]["counters"]["second_singleton_replays"] == 2420
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    first_flux = known["first_public"]["flux"]
    assert len(first_flux) == 24 and known["first_public"]["charge"] == [0] * 24
    known_masses = {sum(1 << edge for edge in row["error_edges_private"]):
                    Fraction(row["first_public_mass"]) for row in known["rows"]}
    assert len(known_masses) == 55
    stress = old["j9e_result"]["stress_fixture"]
    stress_mask = sum(1 << edge for edge in stress["error_edges_private_analysis_only"])
    counters = Counter()

    def signature(zmask):
        return sum(parity(zmask & flip) << i for i, flip in enumerate(flips))

    class CapReached(Exception):
        pass

    def exact_first_mass(first_ops, check_phase):
        vectors = [signature(op[1]) for op in first_ops]
        solution = affine_basis(vectors, 0)
        assert solution is not None
        particular, kernel = solution
        assert particular == 0
        width = len(kernel)

        def phase(subset):
            if counters["signed_phase_evaluations"] >= budget["max_signed_phase_evaluations"]:
                raise CapReached("signed_phase_cap")
            factors = [op for i, op in enumerate(first_ops) if subset >> i & 1]
            sign, zmask, _ = compose(factors)
            assert signature(zmask) == 0
            counters["signed_phase_evaluations"] += 1
            return int(sign == -1)

        if (1 << width) <= 1 + width + comb(width, 2):
            total = 0
            for choice in range(1 << width):
                subset = 0
                for i, relation in enumerate(kernel):
                    if choice >> i & 1:
                        subset ^= relation
                total += -1 if phase(subset) else 1
            counters["direct_affine_sums"] += 1
        else:
            constant = phase(0)
            linear = [phase(relation) ^ constant for relation in kernel]
            cross = [[0] * width for _ in range(width)]
            for i, j in itertools.combinations(range(width), 2):
                cross[i][j] = cross[j][i] = (phase(kernel[i] ^ kernel[j])
                                                ^ constant ^ linear[i] ^ linear[j])
            if check_phase:
                for choice in range(min(1 << width, budget["heldout_points_per_checked_error"])):
                    subset = 0
                    for i, relation in enumerate(kernel):
                        if choice >> i & 1:
                            subset ^= relation
                    predicted = constant ^ sum(linear[i] * ((choice >> i) & 1)
                                               for i in range(width))
                    predicted ^= sum(cross[i][j] * ((choice >> i) & 1) * ((choice >> j) & 1)
                                     for i, j in itertools.combinations(range(width), 2))
                    assert phase(subset) == (predicted & 1)
                    counters["heldout_phase_checks"] += 1
            total = quadratic_sum(constant, linear, cross)
            counters["quadratic_gauss_sums"] += 1
        mass = Fraction(total, 1 << len(first_ops))
        assert 0 <= mass <= 1
        return mass, width

    # Reconstruct J8J's complete 13-dimensional same-flux private-error coset.
    columns = []
    for edge in range(36):
        _, flux = red_boundary(red, [edge])
        columns.append(sum(bit << i for i, bit in enumerate(flux)))
    basis = {}
    null_vectors = []
    for edge, column in enumerate(columns):
        residual, combination = column, 1 << edge
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (residual, combination)
                break
            old_vector, old_bits = basis[pivot]
            residual ^= old_vector
            combination ^= old_bits
        if not residual:
            null_vectors.append(combination)
    assert len(basis) == 23 and len(null_vectors) == 13
    base_mask = sum(1 << edge for edge in known["rows"][0]["error_edges_private"])
    rows = []
    stop = None
    site_tests = 0
    replayed = set()
    kernel_hist = Counter()
    variable_hist = Counter()
    positive = 0
    selected_mass = Fraction()
    known_contribution = Fraction()
    flux_prior = Fraction()
    for coset_index in range(1 << len(null_vectors)):
        mask = base_mask
        for i, vector in enumerate(null_vectors):
            if coset_index >> i & 1:
                mask ^= vector
        edges = [i for i in range(36) if mask >> i & 1]
        physical, flux = red_boundary(red, edges)
        assert flux == first_flux
        eligible, means = sector_sites(sites, physical, flips, pairs)
        site_tests += len(eligible)
        if site_tests > budget["max_first_site_character_tests"]:
            stop = "first_site_test_cap"
            break
        assert all(means[site] != -1 for site in eligible)
        variable = [site for site in eligible if means[site] == 0]
        first_ops = [conjugated_star(sites[site], physical) for site in variable]
        try:
            mass, dimension = exact_first_mass(
                first_ops, coset_index % budget["phase_check_stride"] == 0)
        except CapReached as error:
            stop = str(error)
            break
        if mask in known_masses:
            assert mass == known_masses[mask]
            replayed.add(mask)
        if mask == stress_mask:
            assert mass == Fraction(stress["first_allplus_mass_diagnostic_only"])
            counters["stress_replays"] += 1
        prior_numerator = 9 ** (36 - len(edges))
        weighted = Fraction(prior_numerator, 10 ** 36) * mass
        flux_prior += Fraction(prior_numerator, 10 ** 36)
        selected_mass += weighted
        if mask in known_masses:
            known_contribution += weighted
        positive += mass > 0
        kernel_hist[dimension] += 1
        variable_hist[len(variable)] += 1
        rows.append({"coset_index": coset_index, "private_error_mask_analysis_only": mask,
                     "error_weight": len(edges), "first_variable_site_count": len(variable),
                     "affine_kernel_dimension": dimension, "first_public_mass": str(mass)})
        if time.process_time() - started > budget["max_cpu_seconds"]:
            stop = "cpu_cap"
            break
    complete = len(rows) == 8192 and stop is None
    if complete:
        assert len(replayed) == 55 and counters["stress_replays"] == 1
        assert flux_prior == Fraction(old["j8j_result"]["selected_flux_prior_mass"])
        assert variable_hist == {int(k): v for k, v in old["j8j_result"]
                                ["first_variable_site_histogram"].items()}
        assert 0 < selected_mass < flux_prior < 1
        assert 0 < known_contribution <= selected_mass
    assert all(sha(path) == contract["pinned_inputs"][name]["sha256"]
               for name, path in paths.items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    return {"schema_version": 1, "id": contract["id"],
            "status": ("selected_first_mass_census_complete" if complete
                       else "selected_first_mass_census_censored"),
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "completed_errors": len(rows), "required_errors": 8192,
            "stop": stop, "rows": rows,
            "summary": {"first_site_character_tests": site_tests,
                        "signed_phase_evaluations": counters["signed_phase_evaluations"],
                        "replayed_known_first_masses": len(replayed),
                        "positive_first_masses": positive,
                        "affine_kernel_dimension_histogram": dict(sorted(kernel_hist.items())),
                        "first_variable_site_histogram": dict(sorted(variable_hist.items())),
                        "selected_complete_first_public_mass": str(selected_mass) if complete else None,
                        "known_55_weighted_fraction_of_selected_record":
                            str(known_contribution / selected_mass) if complete else None,
                        "selected_first_flux_prior_mass_replay": str(flux_prior) if complete else None},
            "counters": dict(counters), "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "Exact mass-only census for one complete all-zero-charge first public record in one L=2 first-flux sector if and only if complete. A censored prefix has no full-record denominator. No second public laws, physical-error posterior logical-sector risk, full-IID channel information/risk, noisy JIT, scaling or threshold. Private-error masks are analysis-only and never decoder-visible."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "completed_errors": result["completed_errors"],
                      "stop": result["stop"], "summary": result["summary"],
                      "cpu_seconds": result["cpu_seconds"]}))
