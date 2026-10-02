"""Independent tiny-vector controls for the exact orbit-character moment rule."""

from fractions import Fraction
import math
import unittest

from run_j6n_sequential_local_projector_moments import (
    moment, run, sequential_probability,
)


def apply_factor(vector: list[complex], factor: tuple[int, int, int]) -> list[complex]:
    sign, zmask, flip = factor
    result = [0j] * len(vector)
    for basis, amplitude in enumerate(vector):
        phase = -1 if (basis & zmask).bit_count() & 1 else 1
        result[basis ^ flip] += sign * phase * amplitude
    return result


def project(vector: list[complex], factor: tuple[int, int, int], outcome: int) -> list[complex]:
    acted = apply_factor(vector, factor)
    return [(left + outcome * right) / 2 for left, right in zip(vector, acted)]


class SequentialLocalMomentsTest(unittest.TestCase):
    def test_noncommuting_two_projectors_against_vector(self) -> None:
        # |+++> is fixed by the three independent X generators. Z_2 X_0
        # and X_2 are both Hermitian, but anticommute with each other.
        state = [1 / math.sqrt(8)] * 8
        first = (1, 1 << 2, 1 << 0)
        second = (1, 0, 1 << 2)
        flips = [1 << bit for bit in range(3)]
        for first_sign in (+1, -1):
            for second_sign in (+1, -1):
                projected = project(project(state, first, first_sign), second, second_sign)
                direct = sum(abs(amplitude) ** 2 for amplitude in projected)
                symbolic = sequential_probability(first, [second], first_sign,
                                                  (second_sign,), flips)
                self.assertEqual(symbolic, Fraction(1, 4))
                self.assertAlmostEqual(direct, float(symbolic))

    def test_ordered_moment_commutation_sign(self) -> None:
        flips = [1 << bit for bit in range(3)]
        first = (1, 1 << 2, 1 << 0)
        second = (1, 0, 1 << 2)
        self.assertEqual(moment([first, second, first], flips), -1)

    def test_registered_periodic_source_limits(self) -> None:
        result = run()
        self.assertEqual(result["status"], "passed_exact_local_sequential_projector_moments_only")
        self.assertEqual(result["first_green_probabilities"], {"1": 0.5, "-1": 0.5})
        self.assertEqual(result["stochastic_histories"], 0)
        self.assertEqual(result["schedule_arm_evaluations"], 0)
        self.assertEqual(result["bootstrap_replicates"], 0)


if __name__ == "__main__":
    unittest.main()
