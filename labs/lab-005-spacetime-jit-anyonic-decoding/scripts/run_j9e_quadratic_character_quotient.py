"""Validate a quadratic Gauss-sum quotient of signed first-projector characters."""

from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

from run_j6m_periodic_operator_ground_orbit import parity
from run_j6n_sequential_local_projector_moments import conjugated_star
from run_j6o_full_binary_sequential_public_record import red_boundary
from run_j6x_full_first_dephasing_new_third import sector_sites
from run_j7a_postselected_next_first_limiting_fixtures import setup
from run_j7v_joint_second_walsh_reduction import compose
from run_j8b_alternate_first_complete_second_laws import commute


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j9e-quadratic-character-quotient-2026-09-28.json"
RESULT = LAB / "results/j9e-quadratic-character-quotient-2026-09-28.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def affine_basis(vectors, target):
    basis = {}
    kernel = []
    for index, vector in enumerate(vectors):
        residual, combination = vector, 1 << index
        while residual:
            pivot = residual.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (residual, combination)
                break
            old, old_bits = basis[pivot]
            residual ^= old
            combination ^= old_bits
        if not residual:
            kernel.append(combination)
    particular, residual = 0, target
    while residual:
        pivot = residual.bit_length() - 1
        if pivot not in basis:
            return None
        old, old_bits = basis[pivot]
        residual ^= old
        particular ^= old_bits
    return particular, kernel


def quadratic_sum(constant, linear, cross):
    """Sum (-1)^quadratic over all GF(2) assignments, eliminating pairs."""
    linear = linear[:]
    cross = [row[:] for row in cross]
    active = list(range(len(linear)))
    eliminated_pairs = 0
    while True:
        chosen = next(((i, j) for i, j in itertools.combinations(active, 2)
                       if cross[i][j]), None)
        if chosen is None:
            break
        i, j = chosen
        remaining = [r for r in active if r not in (i, j)]
        ai, aj = linear[i], linear[j]
        constant ^= ai & aj
        for r in remaining:
            linear[r] ^= (ai & cross[j][r]) ^ (aj & cross[i][r]) ^ (cross[i][r] & cross[j][r])
        for r, s in itertools.combinations(remaining, 2):
            cross[r][s] ^= (cross[i][r] & cross[j][s]) ^ (cross[i][s] & cross[j][r])
            cross[s][r] = cross[r][s]
        active = remaining
        eliminated_pairs += 1
    if any(linear[r] for r in active):
        return 0
    return (-1 if constant else 1) * (1 << (eliminated_pairs + len(active)))


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
    assert len(known["rows"]) == 55 and known["candidate_action_cells"] == 108
    assert old["j8j_result"]["same_first_flux_error_count"] == 8192
    red, sites, flips, pairs = setup(old["j6l_result"], old["j6m_result"])
    assert len(red) == 36 and len(sites) == 24
    actions = known["actions"]
    assert actions == [[0], [1, 30, 32, 34, 35]]
    counters = Counter()

    def signature(zmask):
        return sum(parity(zmask & flip) << index for index, flip in enumerate(flips))

    # Independent exhaustive algebra controls, before physical-law replay.
    for width in range(4):
        terms = width * (width - 1) // 2
        for form in range(1 << (1 + width + terms)):
            constant = form & 1
            linear = [(form >> (1 + i)) & 1 for i in range(width)]
            cross = [[0] * width for _ in range(width)]
            for bit, (i, j) in enumerate(itertools.combinations(range(width), 2)):
                cross[i][j] = cross[j][i] = (form >> (1 + width + bit)) & 1
            brute = 0
            for value in range(1 << width):
                phase = constant ^ sum(linear[i] * ((value >> i) & 1) for i in range(width))
                phase ^= sum(cross[i][j] * ((value >> i) & 1) * ((value >> j) & 1)
                             for i, j in itertools.combinations(range(width), 2))
                brute += -1 if phase & 1 else 1
            assert quadratic_sum(constant, linear, cross) == brute
            counters["synthetic_quadratic_forms"] += 1

    def signed_sum(first_ops, tail=()):
        tail_product = compose(list(tail))
        vectors = [signature(op[1]) for op in first_ops]
        solution = affine_basis(vectors, signature(tail_product[1]))
        if solution is None:
            return 0, 0
        particular, kernel = solution
        width = len(kernel)

        def phase(subset):
            operators = [op for index, op in enumerate(first_ops) if (subset >> index) & 1]
            sign, zmask, _ = compose(operators + list(tail))
            assert signature(zmask) == 0
            counters["signed_phase_evaluations"] += 1
            assert counters["signed_phase_evaluations"] <= budget["max_signed_phase_evaluations"]
            return int(sign == -1)

        constant = phase(particular)
        linear = [phase(particular ^ vector) ^ constant for vector in kernel]
        cross = [[0] * width for _ in range(width)]
        for i, j in itertools.combinations(range(width), 2):
            cross[i][j] = cross[j][i] = (phase(particular ^ kernel[i] ^ kernel[j])
                                            ^ constant ^ linear[i] ^ linear[j])
        # The Pauli-group sign is quadratic: held-out affine points detect
        # a bad phase convention before this quotient can be trusted.
        for choice in range(min(1 << width, budget["max_heldout_affine_points_per_sum"])):
            subset = particular
            for i, vector in enumerate(kernel):
                if choice >> i & 1:
                    subset ^= vector
            predicted = constant ^ sum(linear[i] * ((choice >> i) & 1)
                                       for i in range(width))
            predicted ^= sum(cross[i][j] * ((choice >> i) & 1) * ((choice >> j) & 1)
                             for i, j in itertools.combinations(range(width), 2))
            assert phase(subset) == (predicted & 1)
            counters["heldout_quadratic_checks"] += 1
        answer = quadratic_sum(constant, linear, cross)
        assert abs(answer) <= 1 << width
        counters["gauss_sums"] += 1
        return answer, width

    control_rows = []
    for row in known["rows"]:
        edges = row["error_edges_private"]
        physical, first_flux = red_boundary(red, edges)
        assert first_flux == known["first_public"]["flux"]
        eligible, means = sector_sites(sites, physical, flips, pairs)
        assert all(means[site] != -1 for site in eligible)
        first_ops = [conjugated_star(sites[site], physical) for site in eligible
                     if means[site] == 0]
        assert all(commute(a, b) for a, b in itertools.combinations(first_ops, 2))
        denominator, width = signed_sum(first_ops)
        mass = Fraction(denominator, 1 << len(first_ops))
        assert mass == Fraction(row["first_public_mass"]) > 0
        counters["first_mass_replays"] += 1
        for action_index, action in enumerate(actions):
            cell = row["cells"][action_index]
            action_mask, _ = red_boundary(red, action)
            residual = physical ^ action_mask
            assert cell["public_action_red_edges"] == action
            eligible_second, _ = sector_sites(sites, residual, flips, pairs)
            assert len(eligible_second) == 22
            law_rows = cell["rows"]
            assert sum((Fraction(item["conditional_probability"]) for item in law_rows),
                       Fraction()) == 1
            for site in eligible_second:
                second = conjugated_star(sites[site], residual)
                if any(not commute(first, second) for first in first_ops):
                    expectation = Fraction(0)
                    counters["noncommuting_zero_checks"] += 1
                else:
                    numerator, _ = signed_sum(first_ops, (second,))
                    expectation = Fraction(numerator, denominator)
                direct = sum((Fraction(item["conditional_probability"])
                              * (-1 if item["public"]["charge"][site] else 1)
                              for item in law_rows), Fraction())
                assert expectation == direct
                counters["second_singleton_replays"] += 1
        control_rows.append({"error_edges_private_analysis_only": edges,
                             "first_variable_sites": len(first_ops),
                             "first_affine_kernel_dimension": width,
                             "replayed_first_mass": str(mass)})
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    assert counters["first_mass_replays"] == 55
    assert counters["second_singleton_replays"] == 55 * 2 * 22

    # A deterministic high-variable-site stress fixture from a fixed prefix
    # of the J8J coset. It is *not* used as a new accepted public law.
    base = known["rows"][0]["error_edges_private"]
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
            prior, prior_bits = basis[pivot]
            residual ^= prior
            combination ^= prior_bits
        if not residual:
            null_vectors.append(combination)
    assert len(null_vectors) == 13
    base_mask = sum(1 << edge for edge in base)
    stress = None
    for free_bits in range(budget["stress_coset_prefix"]):
        mask = base_mask
        for i, vector in enumerate(null_vectors):
            if free_bits >> i & 1:
                mask ^= vector
        edges = [i for i in range(36) if mask >> i & 1]
        physical, flux = red_boundary(red, edges)
        assert flux == known["first_public"]["flux"]
        eligible, means = sector_sites(sites, physical, flips, pairs)
        variable = [site for site in eligible if means[site] == 0]
        candidate = (len(variable), -free_bits, edges, physical, variable)
        if stress is None or candidate[:2] > stress[:2]:
            stress = candidate
        counters["stress_coset_candidates"] += 1
        assert time.process_time() - started <= budget["max_cpu_seconds"]
    count, negative_index, edges, physical, variable = stress
    first_ops = [conjugated_star(sites[site], physical) for site in variable]
    numerator, kernel_dimension = signed_sum(first_ops)
    stress_summary = {"selection": "maximum variable-site count, then earliest in first 256 J8J coset masks",
                      "coset_index_analysis_only": -negative_index,
                      "error_edges_private_analysis_only": edges,
                      "first_variable_sites": count,
                      "affine_kernel_dimension": kernel_dimension,
                      "first_allplus_mass_diagnostic_only": str(Fraction(numerator, 1 << count))}
    assert all(sha(path) == contract["pinned_inputs"][name]["sha256"]
               for name, path in paths.items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert time.process_time() - started <= budget["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "quadratic_character_quotient_gate_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "counters": dict(counters), "control_rows": control_rows,
            "stress_fixture": stress_summary,
            "cpu_seconds": round(time.process_time() - started, 6),
            "claim_boundary": "Quadratic signed-character quotient matches 55 previously computed first masses and all 2,420 stored second single-site means, plus deterministic synthetic controls; one fixed-prefix high-variable error is a cost/phase-consistency stress fixture only. No new complete public law, full-prior mixture, information/risk, noisy JIT, scaling or threshold. The quotient is not a physical law-transfer symmetry and does not license pooling of uncomputed errors."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "counters": result["counters"],
                      "stress_fixture": result["stress_fixture"],
                      "cpu_seconds": result["cpu_seconds"]}))
