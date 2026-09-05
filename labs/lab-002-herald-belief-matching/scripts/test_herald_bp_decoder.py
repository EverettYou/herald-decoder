#!/usr/bin/env python3
"""Tests for Lab 002 posterior inference and PyMatching integration."""

from __future__ import annotations

import unittest

import numpy as np

from herald_bp_decoder import (
    HeraldBeliefMatchingDecoder,
    SyndromeOnlyMatchingDecoder,
    exact_posterior,
    hard_bp_then_matching,
)
from artifact_backend import artifact_payload
from lattice_model import honeycomb_graph, sample_observation, square_graph
from legacy_damped_bp_decoder import LegacyDampedBpMatchingDecoder
from numba_bp_kernels import NUMBA_AVAILABLE


class LatticeModelTest(unittest.TestCase):
    def test_square_and_honeycomb_have_only_valid_matching_columns(self) -> None:
        for graph in (square_graph(5), honeycomb_graph(5)):
            column_weights = np.asarray(graph.check_matrix.sum(axis=0)).ravel()
            self.assertTrue(np.all((column_weights == 1) | (column_weights == 2)))
            self.assertGreater(len(graph.logical_edges), 0)
            self.assertEqual(
                {graph.vertices[v].boundary_side for v in graph.boundary_vertices},
                {"left", "right"},
            )

    def test_sampled_herald_is_a_degree_witness_not_an_erasure_location(self) -> None:
        graph = honeycomb_graph(3)
        observation = sample_observation(graph, np.random.default_rng(11), p=0.3, q=1, p_m=0, p_h=0)
        self.assertTrue(np.all(observation.detector_degrees[observation.herald == 1] >= 2))
        self.assertTrue(np.array_equal(observation.syndrome, observation.detector_degrees & 1))


class HeraldBpDecoderTest(unittest.TestCase):
    @unittest.skipUnless(NUMBA_AVAILABLE, "compatible Numba runtime is not active")
    def test_numba_kernels_are_exactly_equivalent_to_python_updates(self) -> None:
        for graph, seed in ((square_graph(5), 551), (honeycomb_graph(5), 552)):
            observation = sample_observation(
                graph,
                np.random.default_rng(seed),
                p=0.14,
                q=0.75,
            )
            for decoder_class in (
                LegacyDampedBpMatchingDecoder,
                HeraldBeliefMatchingDecoder,
            ):
                options = (
                    {"recurrence_mode": "memory"}
                    if decoder_class is HeraldBeliefMatchingDecoder
                    else {}
                )
                python_result = decoder_class(
                    graph,
                    p=0.14,
                    q=0.75,
                    use_numba=False,
                    **options,
                ).decode(observation.syndrome, observation.herald)
                numba_result = decoder_class(
                    graph,
                    p=0.14,
                    q=0.75,
                    use_numba=True,
                    **options,
                ).decode(observation.syndrome, observation.herald)
                np.testing.assert_array_equal(
                    numba_result.bp.edge_marginals,
                    python_result.bp.edge_marginals,
                )
                np.testing.assert_array_equal(
                    numba_result.correction,
                    python_result.correction,
                )
                self.assertEqual(numba_result.bp.iterations, python_result.bp.iterations)
                self.assertEqual(numba_result.bp.converged, python_result.bp.converged)
                if hasattr(numba_result.bp, "selected_leg"):
                    self.assertEqual(
                        numba_result.bp.selected_leg,
                        python_result.bp.selected_leg,
                    )

    def test_frozen_legacy_damping_ablation_matches_archived_result(self) -> None:
        graph = square_graph(3)
        observation = sample_observation(
            graph,
            np.random.default_rng(7123),
            p=0.14,
            q=0.75,
            p_m=0,
            p_h=0,
        )
        result = LegacyDampedBpMatchingDecoder(graph, p=0.14, q=0.75).decode(
            observation.syndrome,
            observation.herald,
        )
        expected = np.asarray(
            [
                0.00712738881213327,
                0.00712738881213327,
                0.00110614052326991,
                0.00763052996233404,
                0.00763052996233404,
                0.00110614052326991,
                0.00712738881213327,
                0.00712738881213327,
            ]
        )
        np.testing.assert_allclose(result.bp.edge_marginals, expected, rtol=0, atol=1e-15)
        self.assertEqual(result.bp.iterations, 15)
        self.assertTrue(result.bp.converged)
        np.testing.assert_array_equal(
            graph.true_syndrome(result.correction),
            observation.syndrome,
        )

    def test_bp_matches_exact_posterior_on_tree_factor_graph(self) -> None:
        graph = square_graph(3)
        observation = sample_observation(
            graph,
            np.random.default_rng(7),
            p=0.12,
            q=0.75,
            p_m=0.04,
            p_h=0.1,
        )
        decoder = HeraldBeliefMatchingDecoder(
            graph,
            p=0.12,
            q=0.75,
            p_m=0.04,
            p_h=0.1,
            max_iterations=20,
            recurrence_mode="memory",
            gamma0=0,
            relay_legs=0,
        )
        bp = decoder.infer(observation.syndrome, observation.herald)
        exact_edges, exact_logical = exact_posterior(
            graph,
            observation.syndrome,
            observation.herald,
            p=0.12,
            q=0.75,
            p_m=0.04,
            p_h=0.1,
        )
        self.assertTrue(bp.converged)
        np.testing.assert_allclose(bp.edge_marginals, exact_edges, atol=1e-10)
        self.assertAlmostEqual(float(np.sum(exact_logical)), 1.0)

    def test_bp_weighted_correction_reproduces_observed_syndrome(self) -> None:
        for graph in (square_graph(5), honeycomb_graph(3)):
            observation = sample_observation(graph, np.random.default_rng(19), p=0.16, q=0.75)
            result = HeraldBeliefMatchingDecoder(graph, p=0.16, q=0.75).decode(
                observation.syndrome, observation.herald
            )
            np.testing.assert_array_equal(graph.true_syndrome(result.correction), observation.syndrome)

    def test_relay_memory_is_deterministic_and_returns_a_scored_candidate(self) -> None:
        graph = honeycomb_graph(3)
        observation = sample_observation(graph, np.random.default_rng(43), p=0.12, q=0.75)
        decoder = HeraldBeliefMatchingDecoder(
            graph,
            p=0.12,
            q=0.75,
            recurrence_mode="memory",
            max_iterations=10,
            relay_legs=3,
            relay_leg_iterations=6,
            gamma_interval=(-0.24, 0.66),
            relay_seed=9,
        )
        first = decoder.infer(observation.syndrome, observation.herald)
        second = decoder.infer(observation.syndrome, observation.herald)
        np.testing.assert_allclose(first.edge_marginals, second.edge_marginals)
        self.assertEqual(first.legs, 4)
        self.assertIn(first.selected_leg, range(first.legs))
        self.assertTrue(np.isfinite(first.score))

    def test_unified_decoder_defaults_to_damping_and_memory_is_opt_in(self) -> None:
        graph = square_graph(3)
        observation = sample_observation(graph, np.random.default_rng(81), p=0.14, q=0.75)
        unified_decoder = HeraldBeliefMatchingDecoder(graph, p=0.14, q=0.75)
        unified = unified_decoder.decode(
            observation.syndrome,
            observation.herald,
        )
        reference = LegacyDampedBpMatchingDecoder(graph, p=0.14, q=0.75).decode(
            observation.syndrome,
            observation.herald,
        )
        np.testing.assert_array_equal(unified.bp.edge_marginals, reference.bp.edge_marginals)
        np.testing.assert_array_equal(unified.correction, reference.correction)
        self.assertIsNone(unified.bp.score)
        self.assertEqual((unified.bp.selected_leg, unified.bp.legs), (0, 1))

        memory = HeraldBeliefMatchingDecoder(
            graph,
            p=0.14,
            q=0.75,
            recurrence_mode="memory",
            relay_legs=2,
        ).infer(observation.syndrome, observation.herald)
        self.assertEqual(memory.legs, 3)
        self.assertTrue(np.isfinite(memory.score))

        with self.assertRaisesRegex(ValueError, "recurrence_mode"):
            HeraldBeliefMatchingDecoder(
                graph,
                p=0.14,
                q=0.75,
                recurrence_mode="unknown",
            )

    def test_default_matching_weights_are_posterior_log_likelihood_ratios(self) -> None:
        graph = square_graph(3)
        for decoder in (
            LegacyDampedBpMatchingDecoder(graph, p=0.14, q=0.75),
            HeraldBeliefMatchingDecoder(graph, p=0.14, q=0.75),
        ):
            weights = decoder._matching_weights(np.asarray([0.2, 0.8]))
            np.testing.assert_allclose(weights, np.log(np.asarray([4.0, 0.25])))

    def test_memory_decode_uses_posterior_llr_weights_end_to_end(self) -> None:
        """Keep the Relay-memory branch inside the corrected MWPM interface."""
        graph = square_graph(3)
        observation = sample_observation(graph, np.random.default_rng(42), p=0.14, q=0.75)
        result = HeraldBeliefMatchingDecoder(
            graph,
            p=0.14,
            q=0.75,
            recurrence_mode="memory",
            max_iterations=4,
            relay_legs=1,
            relay_leg_iterations=3,
            use_numba=False,
        ).decode(observation.syndrome, observation.herald)
        expected = np.log(
            (1 - np.clip(result.bp.edge_marginals, 1e-12, 1 - 1e-12))
            / np.clip(result.bp.edge_marginals, 1e-12, 1 - 1e-12)
        )
        np.testing.assert_allclose(result.edge_weights, expected)
        np.testing.assert_array_equal(graph.true_syndrome(result.correction), observation.syndrome)

    def test_residual_priority_schedule_is_opt_in_and_syndrome_faithful(self) -> None:
        graph = square_graph(5)
        observation = sample_observation(graph, np.random.default_rng(902), p=0.20, q=1.0)
        python_decoder = LegacyDampedBpMatchingDecoder(
            graph,
            p=0.20,
            q=1.0,
            max_iterations=40,
            update_schedule="residual_priority",
            use_numba=False,
        )
        numba_decoder = LegacyDampedBpMatchingDecoder(
            graph,
            p=0.20,
            q=1.0,
            max_iterations=40,
            update_schedule="residual_priority",
            use_numba=True,
        )
        result = python_decoder.decode(observation.syndrome, observation.herald)
        compiled = numba_decoder.decode(observation.syndrome, observation.herald)
        expected = np.log(
            (1 - np.clip(result.bp.edge_marginals, 1e-12, 1 - 1e-12))
            / np.clip(result.bp.edge_marginals, 1e-12, 1 - 1e-12)
        )
        np.testing.assert_allclose(result.edge_weights, expected)
        np.testing.assert_array_equal(graph.true_syndrome(result.correction), observation.syndrome)
        np.testing.assert_array_equal(compiled.bp.edge_marginals, result.bp.edge_marginals)
        np.testing.assert_array_equal(compiled.edge_weights, result.edge_weights)
        np.testing.assert_array_equal(compiled.correction, result.correction)
        self.assertEqual(compiled.bp.iterations, result.bp.iterations)
        self.assertEqual(compiled.bp.converged, result.bp.converged)
        self.assertEqual(compiled.bp.max_message_delta, result.bp.max_message_delta)

    def test_stable_residual_priority_order_is_bit_identical_to_scan(self) -> None:
        """C5 may accelerate selection, but not change factor update order."""
        graph = square_graph(5)
        observation = sample_observation(graph, np.random.default_rng(903), p=0.20, q=1.0)
        reference = LegacyDampedBpMatchingDecoder(
            graph, p=0.20, q=1.0, max_iterations=80,
            update_schedule="residual_priority", residual_priority_order="scan", use_numba=True,
        ).decode(observation.syndrome, observation.herald)
        optimized = LegacyDampedBpMatchingDecoder(
            graph, p=0.20, q=1.0, max_iterations=80,
            update_schedule="residual_priority", residual_priority_order="stable_sort", use_numba=True,
        ).decode(observation.syndrome, observation.herald)
        np.testing.assert_array_equal(optimized.bp.edge_marginals, reference.bp.edge_marginals)
        np.testing.assert_array_equal(optimized.edge_weights, reference.edge_weights)
        np.testing.assert_array_equal(optimized.correction, reference.correction)
        self.assertEqual(optimized.bp.iterations, reference.bp.iterations)
        self.assertEqual(optimized.bp.converged, reference.bp.converged)
        self.assertEqual(optimized.bp.max_message_delta, reference.bp.max_message_delta)

    def test_reused_residual_priority_buffers_are_bit_identical(self) -> None:
        """C7 may remove allocations, but not alter BP or matching output."""
        for make_graph, size, seed in ((square_graph, 5, 904), (honeycomb_graph, 5, 905)):
            graph = make_graph(size)
            observation = sample_observation(graph, np.random.default_rng(seed), p=0.20, q=1.0)
            reference = LegacyDampedBpMatchingDecoder(
                graph, p=0.20, q=1.0, max_iterations=80,
                update_schedule="residual_priority",
                residual_priority_order="stable_sort",
                use_numba=True,
            ).decode(observation.syndrome, observation.herald)
            optimized = LegacyDampedBpMatchingDecoder(
                graph, p=0.20, q=1.0, max_iterations=80,
                update_schedule="residual_priority",
                residual_priority_order="stable_sort",
                residual_priority_buffer_reuse=True,
                use_numba=True,
            ).decode(observation.syndrome, observation.herald)
            np.testing.assert_array_equal(optimized.bp.edge_marginals, reference.bp.edge_marginals)
            np.testing.assert_array_equal(optimized.edge_weights, reference.edge_weights)
            np.testing.assert_array_equal(optimized.correction, reference.correction)
            self.assertEqual(optimized.bp.iterations, reference.bp.iterations)
            self.assertEqual(optimized.bp.converged, reference.bp.converged)
            self.assertEqual(optimized.bp.max_message_delta, reference.bp.max_message_delta)

    def test_seed12_llr_pins_the_high_probability_right_chain(self) -> None:
        """Prevent recurrence of the 2026-08-26 negative-log interface bug."""
        payload = artifact_payload(
            {
                "lattice": "square",
                "L": 9,
                "p": 0.20,
                "q": 1.0,
                "p_m": 0.0,
                "p_h": 0.0,
                "seed": 12,
                "recurrence_mode": "damping",
            }
        )
        right_chain = np.asarray([123, 124, 125, 126])
        correction = set(payload["herald_decoder"]["correction_edge_indices"])
        weights = np.asarray(payload["posterior"]["matching_weights"])
        self.assertEqual(payload["model"]["matching_projection"], "posterior_llr")
        self.assertTrue(set(right_chain).issubset(correction))
        self.assertTrue(np.all(weights[right_chain] < -1.0))
        self.assertFalse(payload["herald_decoder"]["logical_error"])

    def test_syndrome_only_baseline_is_pymatching_and_reproduces_syndrome(self) -> None:
        graph = honeycomb_graph(4)
        observation = sample_observation(graph, np.random.default_rng(23), p=0.1, q=0.75)
        correction, weight = SyndromeOnlyMatchingDecoder(graph, p=0.1).decode(observation.syndrome)
        np.testing.assert_array_equal(graph.true_syndrome(correction), observation.syndrome)
        self.assertGreaterEqual(weight, 0)

    def test_hard_bp_predecode_exposes_residual_before_mwpm(self) -> None:
        graph = square_graph(5)
        observation = sample_observation(graph, np.random.default_rng(31), p=0.14, q=0.75)
        bp = HeraldBeliefMatchingDecoder(graph, p=0.14, q=0.75).infer(
            observation.syndrome, observation.herald
        )
        result = hard_bp_then_matching(
            graph,
            observation.syndrome,
            bp.edge_marginals,
            SyndromeOnlyMatchingDecoder(graph, p=0.14),
        )
        np.testing.assert_array_equal(
            result.residual_syndrome,
            observation.syndrome ^ graph.true_syndrome(result.pre_correction),
        )
        np.testing.assert_array_equal(result.final_syndrome, np.zeros_like(observation.syndrome))
        np.testing.assert_array_equal(
            result.correction, result.pre_correction ^ result.completion_correction
        )

    def test_soft_bp_inference_does_not_modify_syndrome(self) -> None:
        payload = artifact_payload(
            {"lattice": "square", "L": 3, "p": 0.1, "q": 0.75, "p_m": 0, "p_h": 0, "seed": 12}
        )
        flow = payload["staged_diagnostic"]["density_flow"]
        self.assertEqual(flow["input_syndrome"], flow["after_soft_bp_inference"])

    def test_ideal_honeycomb_joint_signal_identifies_degree(self) -> None:
        for degree, expected in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
            syndrome = degree & 1
            herald_eligibility = int(degree >= 2)
            self.assertEqual((syndrome, herald_eligibility), expected)

    def test_artifact_payload_exposes_inference_layers_deterministically(self) -> None:
        request = {
            "lattice": "honeycomb",
            "L": 3,
            "p": 0.1,
            "q": 0.75,
            "p_m": 0.0,
            "p_h": 0.0,
            "seed": 17,
        }
        first = artifact_payload(request)
        second = artifact_payload(request)
        self.assertEqual(first["observation"], second["observation"])
        self.assertEqual(first["posterior"], second["posterior"])
        edge_count = len(first["graph"]["edges"])
        self.assertEqual(len(first["posterior"]["herald_aware"]), edge_count)
        self.assertEqual(len(first["posterior"]["herald_delta"]), edge_count)
        self.assertIn("correction_edge_indices", first["baseline"])
        self.assertIn("correction_edge_indices", first["syndrome_bp_decoder"])
        self.assertIn("correction_edge_indices", first["herald_decoder"])
        self.assertIn("residual_syndrome_vertices", first["herald_decoder"])
        self.assertEqual(first["herald_decoder"]["residual_syndrome_vertices"], [])
        self.assertIn("unexplained_herald_vertices", first["herald_decoder"])
        self.assertTrue(
            set(first["herald_decoder"]["unexplained_herald_vertices"])
            .issubset(first["observation"]["herald_vertices"])
        )
        self.assertIn("density_flow", first["staged_diagnostic"])
        self.assertIn("bp_search", first["model"])
        self.assertEqual(first["model"]["recurrence_mode"], "damping")
        self.assertFalse(first["model"]["bp_search"]["enabled"])
        self.assertEqual(first["herald_decoder"]["bp"]["legs"], 1)
        self.assertIsNone(first["herald_decoder"]["bp"]["score"])

        memory = artifact_payload({**request, "recurrence_mode": "memory"})
        self.assertEqual(memory["model"]["recurrence_mode"], "memory")
        self.assertTrue(memory["model"]["bp_search"]["enabled"])
        self.assertEqual(memory["herald_decoder"]["bp"]["legs"], 7)
        self.assertTrue(np.isfinite(memory["herald_decoder"]["bp"]["score"]))
        self.assertEqual(set(first["soft_quality"]), {"scope", "prior", "syndrome_bp", "herald_bp"})

    def test_artifact_accepts_full_physical_error_slider_range(self) -> None:
        """The Lab 002 workbench must support p=0 and p=1 without infinite LLRs."""
        base = {
            "lattice": "square", "L": 3, "q": 0.75,
            "p_m": 0.0, "p_h": 0.0, "seed": 19,
        }
        for p in (0.0, 1.0):
            payload = artifact_payload({**base, "p": p})
            self.assertEqual(payload["model"]["p"], p)
            self.assertTrue(np.all(np.isfinite(payload["posterior"]["matching_weights"])))


if __name__ == "__main__":
    unittest.main()
