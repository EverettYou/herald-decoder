#!/usr/bin/env python3
"""Optional dense-array Numba kernels for the two Lab 002 BP updates."""

from __future__ import annotations

from math import exp, log

import numpy as np

try:
    from numba import njit

    NUMBA_AVAILABLE = True
except Exception:  # The default dashboard runtime may have incompatible NumPy.
    njit = None
    NUMBA_AVAILABLE = False


def dense_topology(factor_edges, edge_factors):
    """Return padded directed-incidence arrays with stable Python ordering."""
    factor_count = len(factor_edges)
    edge_count = len(edge_factors)
    max_factor_degree = max(len(edges) for edges in factor_edges)
    max_edge_degree = max(len(factors) for factors in edge_factors)
    factor_dirs = np.full((factor_count, max_factor_degree), -1, dtype=np.int64)
    factor_degrees = np.zeros(factor_count, dtype=np.int64)
    directed_keys = []
    key_to_direction = {}
    for factor, edges in enumerate(factor_edges):
        factor_degrees[factor] = len(edges)
        for position, edge in enumerate(edges):
            direction = len(directed_keys)
            directed_keys.append((edge, factor))
            key_to_direction[(edge, factor)] = direction
            factor_dirs[factor, position] = direction
    edge_dirs = np.full((edge_count, max_edge_degree), -1, dtype=np.int64)
    edge_degrees = np.zeros(edge_count, dtype=np.int64)
    for edge, factors in enumerate(edge_factors):
        edge_degrees[edge] = len(factors)
        for position, factor in enumerate(factors):
            edge_dirs[edge, position] = key_to_direction[(edge, factor)]
    return factor_dirs, factor_degrees, edge_dirs, edge_degrees, tuple(directed_keys)


if NUMBA_AVAILABLE:

    @njit(cache=True)
    def _normalise_pair(first, second):
        total = first + second
        return first / total, second / total


    @njit(cache=True)
    def _vertex_likelihood_mask(mask, degree, syndrome, herald, q, p_m, p_h):
        incident_degree = 0
        for position in range(degree):
            incident_degree += (mask >> (degree - 1 - position)) & 1
        parity_probability = 1.0 - p_m if (incident_degree & 1) == syndrome else p_m
        alpha = q * (1.0 - p_h)
        if herald == 1:
            herald_probability = alpha if incident_degree >= 2 else 0.0
        else:
            herald_probability = 1.0 - alpha if incident_degree >= 2 else 1.0
        return parity_probability * herald_probability


    @njit(cache=True)
    def _stable_descending_residual_order(residuals):
        """Return residual-descending factor indices with index-ascending ties.

        The C3/C4 reference scheduler repeatedly scans candidates with a strict
        ``>`` comparison, which selects the lowest factor index on an exact
        tie.  This stable bottom-up merge sort has precisely that ordering in
        O(F log F) comparisons, while leaving the BP recurrence untouched.
        """
        count = residuals.shape[0]
        order = np.empty(count, dtype=np.int64)
        scratch = np.empty(count, dtype=np.int64)
        for index in range(count):
            order[index] = index
        width = 1
        while width < count:
            start = 0
            while start < count:
                middle = start + width
                if middle > count:
                    middle = count
                end = start + 2 * width
                if end > count:
                    end = count
                left = start
                right = middle
                destination = start
                while left < middle and right < end:
                    # Equal residuals take the left element, preserving the
                    # original increasing-factor-index tie rule.
                    if residuals[order[left]] >= residuals[order[right]]:
                        scratch[destination] = order[left]
                        left += 1
                    else:
                        scratch[destination] = order[right]
                        right += 1
                    destination += 1
                while left < middle:
                    scratch[destination] = order[left]
                    left += 1
                    destination += 1
                while right < end:
                    scratch[destination] = order[right]
                    right += 1
                    destination += 1
                start += 2 * width
            replacement = order
            order = scratch
            scratch = replacement
            width *= 2
        return order


    @njit(cache=True)
    def _stable_descending_residual_order_reuse(residuals, order, scratch):
        """Fill reusable buffers with the exact C5 stable priority order."""
        count = residuals.shape[0]
        for index in range(count):
            order[index] = index
        source = order
        destination_buffer = scratch
        width = 1
        while width < count:
            start = 0
            while start < count:
                middle = start + width
                if middle > count:
                    middle = count
                end = start + 2 * width
                if end > count:
                    end = count
                left = start
                right = middle
                destination = start
                while left < middle and right < end:
                    if residuals[source[left]] >= residuals[source[right]]:
                        destination_buffer[destination] = source[left]
                        left += 1
                    else:
                        destination_buffer[destination] = source[right]
                        right += 1
                    destination += 1
                while left < middle:
                    destination_buffer[destination] = source[left]
                    left += 1
                    destination += 1
                while right < end:
                    destination_buffer[destination] = source[right]
                    right += 1
                    destination += 1
                start += 2 * width
            replacement = source
            source = destination_buffer
            destination_buffer = replacement
            width *= 2
        return source, destination_buffer


    @njit(cache=True)
    def legacy_infer_dense(
        syndrome,
        herald,
        factor_dirs,
        factor_degrees,
        edge_dirs,
        edge_degrees,
        prior_error,
        q,
        p_m,
        p_h,
        max_iterations,
        damping,
        tolerance,
    ):
        direction_count = int(np.sum(factor_degrees))
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        for direction in range(direction_count):
            variable_to_factor[direction, 0] = 1.0 - prior_error
            variable_to_factor[direction, 1] = prior_error
        converged = False
        max_delta = np.inf
        marginals = np.full(edge_dirs.shape[0], prior_error, dtype=np.float64)

        for iteration in range(1, max_iterations + 1):
            updated_factor = np.empty_like(factor_to_variable)
            for factor in range(factor_dirs.shape[0]):
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        likelihood = _vertex_likelihood_mask(
                            mask,
                            degree,
                            syndrome[factor],
                            herald[factor],
                            q,
                            p_m,
                            p_h,
                        )
                        if likelihood == 0.0:
                            continue
                        value = likelihood
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable_to_factor[direction, bit]
                        target_bit = (mask >> (degree - 1 - target_position)) & 1
                        if target_bit == 0:
                            first += value
                        else:
                            second += value
                    first, second = _normalise_pair(first, second)
                    direction = factor_dirs[factor, target_position]
                    first = damping * factor_to_variable[direction, 0] + (1.0 - damping) * first
                    second = damping * factor_to_variable[direction, 1] + (1.0 - damping) * second
                    first, second = _normalise_pair(first, second)
                    updated_factor[direction, 0] = first
                    updated_factor[direction, 1] = second

            updated_variable = np.empty_like(variable_to_factor)
            for edge in range(edge_dirs.shape[0]):
                degree = edge_degrees[edge]
                for target_position in range(degree):
                    first = 1.0 - prior_error
                    second = prior_error
                    for position in range(degree):
                        if position != target_position:
                            direction = edge_dirs[edge, position]
                            first *= updated_factor[direction, 0]
                            second *= updated_factor[direction, 1]
                    first, second = _normalise_pair(first, second)
                    direction = edge_dirs[edge, target_position]
                    updated_variable[direction, 0] = first
                    updated_variable[direction, 1] = second

            max_delta = 0.0
            for direction in range(direction_count):
                delta = abs(updated_factor[direction, 0] - factor_to_variable[direction, 0])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_factor[direction, 1] - factor_to_variable[direction, 1])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_variable[direction, 0] - variable_to_factor[direction, 0])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_variable[direction, 1] - variable_to_factor[direction, 1])
                if delta > max_delta:
                    max_delta = delta
            factor_to_variable = updated_factor
            variable_to_factor = updated_variable
            if max_delta < tolerance:
                converged = True
                break

        for edge in range(edge_dirs.shape[0]):
            first = 1.0 - prior_error
            second = prior_error
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                first *= factor_to_variable[direction, 0]
                second *= factor_to_variable[direction, 1]
            first, second = _normalise_pair(first, second)
            marginals[edge] = second
        return marginals, converged, max_delta, iteration


    @njit(cache=True)
    def residual_priority_infer_dense(
        syndrome, herald, factor_dirs, factor_degrees, edge_dirs, edge_degrees,
        direction_edges, direction_factors, prior_error, q, p_m, p_h,
        max_iterations, damping, tolerance, stable_priority_order=False,
    ):
        """Compiled equivalent of the C1 residual-priority Python recurrence."""
        direction_count = int(np.sum(factor_degrees))
        factor_count = factor_dirs.shape[0]
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        for direction in range(direction_count):
            variable_to_factor[direction, 0] = 1.0 - prior_error
            variable_to_factor[direction, 1] = prior_error
        previous_residuals = np.zeros(factor_count, dtype=np.float64)
        has_previous_residuals = False
        converged = False
        max_delta = np.inf

        for iteration in range(1, max_iterations + 1):
            factors = factor_to_variable.copy()
            variable = variable_to_factor.copy()
            residuals = np.zeros(factor_count, dtype=np.float64)
            priority_order = np.empty(factor_count, dtype=np.int64)
            processed = np.zeros(factor_count, dtype=np.uint8)
            if has_previous_residuals and stable_priority_order:
                priority_order = _stable_descending_residual_order(previous_residuals)
            max_delta = 0.0
            for slot in range(factor_count):
                factor = slot
                if has_previous_residuals and stable_priority_order:
                    factor = priority_order[slot]
                elif has_previous_residuals:
                    best_residual = -1.0
                    for candidate in range(factor_count):
                        if processed[candidate] == 0 and previous_residuals[candidate] > best_residual:
                            best_residual = previous_residuals[candidate]
                            factor = candidate
                    processed[factor] = 1
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        likelihood = _vertex_likelihood_mask(mask, degree, syndrome[factor], herald[factor], q, p_m, p_h)
                        if likelihood == 0.0:
                            continue
                        value = likelihood
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable[direction, bit]
                        target_bit = (mask >> (degree - 1 - target_position)) & 1
                        if target_bit == 0:
                            first += value
                        else:
                            second += value
                    first, second = _normalise_pair(first, second)
                    direction = factor_dirs[factor, target_position]
                    first = damping * factors[direction, 0] + (1.0 - damping) * first
                    second = damping * factors[direction, 1] + (1.0 - damping) * second
                    first, second = _normalise_pair(first, second)
                    delta = abs(first - factors[direction, 0])
                    second_delta = abs(second - factors[direction, 1])
                    if second_delta > delta:
                        delta = second_delta
                    if delta > max_delta:
                        max_delta = delta
                    if delta > residuals[factor]:
                        residuals[factor] = delta
                    factors[direction, 0] = first
                    factors[direction, 1] = second

                    edge = direction_edges[direction]
                    edge_degree = edge_degrees[edge]
                    for edge_position in range(edge_degree):
                        target_direction = edge_dirs[edge, edge_position]
                        target_factor = direction_factors[target_direction]
                        if target_factor == factor:
                            continue
                        first = 1.0 - prior_error
                        second = prior_error
                        for other_position in range(edge_degree):
                            other_direction = edge_dirs[edge, other_position]
                            if other_direction != target_direction:
                                first *= factors[other_direction, 0]
                                second *= factors[other_direction, 1]
                        first, second = _normalise_pair(first, second)
                        delta = abs(first - variable[target_direction, 0])
                        second_delta = abs(second - variable[target_direction, 1])
                        if second_delta > delta:
                            delta = second_delta
                        if delta > max_delta:
                            max_delta = delta
                        if delta > residuals[target_factor]:
                            residuals[target_factor] = delta
                        variable[target_direction, 0] = first
                        variable[target_direction, 1] = second
            factor_to_variable = factors
            variable_to_factor = variable
            previous_residuals = residuals
            has_previous_residuals = True
            if max_delta < tolerance:
                converged = True
                break

        marginals = np.empty(edge_dirs.shape[0], dtype=np.float64)
        for edge in range(edge_dirs.shape[0]):
            first = 1.0 - prior_error
            second = prior_error
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                first *= factor_to_variable[direction, 0]
                second *= factor_to_variable[direction, 1]
            first, second = _normalise_pair(first, second)
            marginals[edge] = second
        return marginals, converged, max_delta, iteration


    @njit(cache=True)
    def residual_priority_infer_dense_reuse(
        syndrome, herald, factor_dirs, factor_degrees, edge_dirs, edge_degrees,
        direction_edges, direction_factors, prior_error, q, p_m, p_h,
        max_iterations, damping, tolerance, stable_priority_order=False,
    ):
        """C7 allocation-only equivalent of residual-priority inference.

        The validated kernel above allocates message copies and scheduler
        scratch arrays on every iteration. This variant preallocates and swaps
        those buffers. Factor order and floating-point operation order are
        intentionally unchanged; C7 requires bit-identical outputs.
        """
        direction_count = int(np.sum(factor_degrees))
        factor_count = factor_dirs.shape[0]
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        for direction in range(direction_count):
            variable_to_factor[direction, 0] = 1.0 - prior_error
            variable_to_factor[direction, 1] = prior_error

        factors = np.empty_like(factor_to_variable)
        variable = np.empty_like(variable_to_factor)
        previous_residuals = np.zeros(factor_count, dtype=np.float64)
        residuals = np.empty(factor_count, dtype=np.float64)
        priority_order = np.empty(factor_count, dtype=np.int64)
        priority_scratch = np.empty(factor_count, dtype=np.int64)
        processed = np.empty(factor_count, dtype=np.uint8)
        has_previous_residuals = False
        converged = False
        max_delta = np.inf

        for iteration in range(1, max_iterations + 1):
            for direction in range(direction_count):
                factors[direction, 0] = factor_to_variable[direction, 0]
                factors[direction, 1] = factor_to_variable[direction, 1]
                variable[direction, 0] = variable_to_factor[direction, 0]
                variable[direction, 1] = variable_to_factor[direction, 1]
            for factor in range(factor_count):
                residuals[factor] = 0.0
                processed[factor] = 0
            if has_previous_residuals and stable_priority_order:
                priority_order, priority_scratch = _stable_descending_residual_order_reuse(
                    previous_residuals, priority_order, priority_scratch
                )
            max_delta = 0.0
            for slot in range(factor_count):
                factor = slot
                if has_previous_residuals and stable_priority_order:
                    factor = priority_order[slot]
                elif has_previous_residuals:
                    best_residual = -1.0
                    for candidate in range(factor_count):
                        if processed[candidate] == 0 and previous_residuals[candidate] > best_residual:
                            best_residual = previous_residuals[candidate]
                            factor = candidate
                    processed[factor] = 1
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        likelihood = _vertex_likelihood_mask(
                            mask, degree, syndrome[factor], herald[factor], q, p_m, p_h
                        )
                        if likelihood == 0.0:
                            continue
                        value = likelihood
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable[direction, bit]
                        target_bit = (mask >> (degree - 1 - target_position)) & 1
                        if target_bit == 0:
                            first += value
                        else:
                            second += value
                    first, second = _normalise_pair(first, second)
                    direction = factor_dirs[factor, target_position]
                    first = damping * factors[direction, 0] + (1.0 - damping) * first
                    second = damping * factors[direction, 1] + (1.0 - damping) * second
                    first, second = _normalise_pair(first, second)
                    delta = abs(first - factors[direction, 0])
                    second_delta = abs(second - factors[direction, 1])
                    if second_delta > delta:
                        delta = second_delta
                    if delta > max_delta:
                        max_delta = delta
                    if delta > residuals[factor]:
                        residuals[factor] = delta
                    factors[direction, 0] = first
                    factors[direction, 1] = second

                    edge = direction_edges[direction]
                    edge_degree = edge_degrees[edge]
                    for edge_position in range(edge_degree):
                        target_direction = edge_dirs[edge, edge_position]
                        target_factor = direction_factors[target_direction]
                        if target_factor == factor:
                            continue
                        first = 1.0 - prior_error
                        second = prior_error
                        for other_position in range(edge_degree):
                            other_direction = edge_dirs[edge, other_position]
                            if other_direction != target_direction:
                                first *= factors[other_direction, 0]
                                second *= factors[other_direction, 1]
                        first, second = _normalise_pair(first, second)
                        delta = abs(first - variable[target_direction, 0])
                        second_delta = abs(second - variable[target_direction, 1])
                        if second_delta > delta:
                            delta = second_delta
                        if delta > max_delta:
                            max_delta = delta
                        if delta > residuals[target_factor]:
                            residuals[target_factor] = delta
                        variable[target_direction, 0] = first
                        variable[target_direction, 1] = second

            replacement = factor_to_variable
            factor_to_variable = factors
            factors = replacement
            replacement = variable_to_factor
            variable_to_factor = variable
            variable = replacement
            replacement_residuals = previous_residuals
            previous_residuals = residuals
            residuals = replacement_residuals
            has_previous_residuals = True
            if max_delta < tolerance:
                converged = True
                break

        marginals = np.empty(edge_dirs.shape[0], dtype=np.float64)
        for edge in range(edge_dirs.shape[0]):
            first = 1.0 - prior_error
            second = prior_error
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                first *= factor_to_variable[direction, 0]
                second *= factor_to_variable[direction, 1]
            first, second = _normalise_pair(first, second)
            marginals[edge] = second
        return marginals, converged, max_delta, iteration


    @njit(cache=True)
    def residual_priority_infer_dense_cached(
        syndrome, herald, factor_dirs, factor_degrees, edge_dirs, edge_degrees,
        direction_edges, direction_factors, prior_error, q, p_m, p_h,
        max_iterations, damping, tolerance, stable_priority_order=False,
    ):
        """C8 cached edge products for a bounded numerical-equivalence test."""
        direction_count = int(np.sum(factor_degrees))
        factor_count = factor_dirs.shape[0]
        edge_count = edge_dirs.shape[0]
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        for direction in range(direction_count):
            variable_to_factor[direction, 0] = 1.0 - prior_error
            variable_to_factor[direction, 1] = prior_error
        previous_residuals = np.zeros(factor_count, dtype=np.float64)
        edge_products = np.empty((edge_count, 2), dtype=np.float64)
        has_previous_residuals = False
        converged = False
        max_delta = np.inf

        for iteration in range(1, max_iterations + 1):
            factors = factor_to_variable.copy()
            variable = variable_to_factor.copy()
            residuals = np.zeros(factor_count, dtype=np.float64)
            priority_order = np.empty(factor_count, dtype=np.int64)
            processed = np.zeros(factor_count, dtype=np.uint8)
            if has_previous_residuals and stable_priority_order:
                priority_order = _stable_descending_residual_order(previous_residuals)
            for edge in range(edge_count):
                first = 1.0 - prior_error
                second = prior_error
                for position in range(edge_degrees[edge]):
                    direction = edge_dirs[edge, position]
                    first *= factors[direction, 0]
                    second *= factors[direction, 1]
                edge_products[edge, 0] = first
                edge_products[edge, 1] = second

            max_delta = 0.0
            for slot in range(factor_count):
                factor = slot
                if has_previous_residuals and stable_priority_order:
                    factor = priority_order[slot]
                elif has_previous_residuals:
                    best_residual = -1.0
                    for candidate in range(factor_count):
                        if processed[candidate] == 0 and previous_residuals[candidate] > best_residual:
                            best_residual = previous_residuals[candidate]
                            factor = candidate
                    processed[factor] = 1
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        likelihood = _vertex_likelihood_mask(
                            mask, degree, syndrome[factor], herald[factor], q, p_m, p_h
                        )
                        if likelihood == 0.0:
                            continue
                        value = likelihood
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable[direction, bit]
                        target_bit = (mask >> (degree - 1 - target_position)) & 1
                        if target_bit == 0:
                            first += value
                        else:
                            second += value
                    first, second = _normalise_pair(first, second)
                    direction = factor_dirs[factor, target_position]
                    old_first = factors[direction, 0]
                    old_second = factors[direction, 1]
                    first = damping * old_first + (1.0 - damping) * first
                    second = damping * old_second + (1.0 - damping) * second
                    first, second = _normalise_pair(first, second)
                    delta = abs(first - old_first)
                    second_delta = abs(second - old_second)
                    if second_delta > delta:
                        delta = second_delta
                    if delta > max_delta:
                        max_delta = delta
                    if delta > residuals[factor]:
                        residuals[factor] = delta
                    factors[direction, 0] = first
                    factors[direction, 1] = second

                    edge = direction_edges[direction]
                    if old_first != 0.0:
                        edge_products[edge, 0] = edge_products[edge, 0] / old_first * first
                    else:
                        value = 1.0 - prior_error
                        for position in range(edge_degrees[edge]):
                            value *= factors[edge_dirs[edge, position], 0]
                        edge_products[edge, 0] = value
                    if old_second != 0.0:
                        edge_products[edge, 1] = edge_products[edge, 1] / old_second * second
                    else:
                        value = prior_error
                        for position in range(edge_degrees[edge]):
                            value *= factors[edge_dirs[edge, position], 1]
                        edge_products[edge, 1] = value

                    edge_degree = edge_degrees[edge]
                    for edge_position in range(edge_degree):
                        target_direction = edge_dirs[edge, edge_position]
                        target_factor = direction_factors[target_direction]
                        if target_factor == factor:
                            continue
                        target_first = factors[target_direction, 0]
                        target_second = factors[target_direction, 1]
                        if target_first != 0.0:
                            first = edge_products[edge, 0] / target_first
                        else:
                            first = 1.0 - prior_error
                            for other_position in range(edge_degree):
                                other_direction = edge_dirs[edge, other_position]
                                if other_direction != target_direction:
                                    first *= factors[other_direction, 0]
                        if target_second != 0.0:
                            second = edge_products[edge, 1] / target_second
                        else:
                            second = prior_error
                            for other_position in range(edge_degree):
                                other_direction = edge_dirs[edge, other_position]
                                if other_direction != target_direction:
                                    second *= factors[other_direction, 1]
                        first, second = _normalise_pair(first, second)
                        delta = abs(first - variable[target_direction, 0])
                        second_delta = abs(second - variable[target_direction, 1])
                        if second_delta > delta:
                            delta = second_delta
                        if delta > max_delta:
                            max_delta = delta
                        if delta > residuals[target_factor]:
                            residuals[target_factor] = delta
                        variable[target_direction, 0] = first
                        variable[target_direction, 1] = second
            factor_to_variable = factors
            variable_to_factor = variable
            previous_residuals = residuals
            has_previous_residuals = True
            if max_delta < tolerance:
                converged = True
                break

        marginals = np.empty(edge_count, dtype=np.float64)
        for edge in range(edge_count):
            first = 1.0 - prior_error
            second = prior_error
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                first *= factor_to_variable[direction, 0]
                second *= factor_to_variable[direction, 1]
            first, second = _normalise_pair(first, second)
            marginals[edge] = second
        return marginals, converged, max_delta, iteration


    @njit(cache=True)
    def _memory_prior(prior_log_odds, previous_probability, gamma):
        if previous_probability < 1e-12:
            previous_probability = 1e-12
        elif previous_probability > 1.0 - 1e-12:
            previous_probability = 1.0 - 1e-12
        previous_log_odds = log((1.0 - previous_probability) / previous_probability)
        combined = (1.0 - gamma) * prior_log_odds + gamma * previous_log_odds
        if combined >= 0.0:
            exponential = exp(-combined)
            error = exponential / (1.0 + exponential)
            return 1.0 - error, error
        exponential = exp(combined)
        no_error = exponential / (1.0 + exponential)
        return no_error, 1.0 - no_error


    @njit(cache=True)
    def memory_leg_dense(
        syndrome,
        herald,
        factor_dirs,
        factor_degrees,
        edge_dirs,
        edge_degrees,
        initial_marginals,
        gammas,
        prior_error,
        q,
        p_m,
        p_h,
        max_iterations,
        tolerance,
    ):
        direction_count = int(np.sum(factor_degrees))
        prior_log_odds = log((1.0 - prior_error) / prior_error)
        previous_marginals = initial_marginals.copy()
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        marginals = np.empty(edge_dirs.shape[0], dtype=np.float64)
        for edge in range(edge_dirs.shape[0]):
            first, second = _memory_prior(prior_log_odds, previous_marginals[edge], gammas[edge])
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                variable_to_factor[direction, 0] = first
                variable_to_factor[direction, 1] = second
        converged = False
        max_delta = np.inf

        for iteration in range(1, max_iterations + 1):
            updated_factor = np.empty_like(factor_to_variable)
            for factor in range(factor_dirs.shape[0]):
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        likelihood = _vertex_likelihood_mask(
                            mask,
                            degree,
                            syndrome[factor],
                            herald[factor],
                            q,
                            p_m,
                            p_h,
                        )
                        if likelihood == 0.0:
                            continue
                        value = likelihood
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable_to_factor[direction, bit]
                        target_bit = (mask >> (degree - 1 - target_position)) & 1
                        if target_bit == 0:
                            first += value
                        else:
                            second += value
                    first, second = _normalise_pair(first, second)
                    direction = factor_dirs[factor, target_position]
                    updated_factor[direction, 0] = first
                    updated_factor[direction, 1] = second

            updated_variable = np.empty_like(variable_to_factor)
            for edge in range(edge_dirs.shape[0]):
                degree = edge_degrees[edge]
                prior_first, prior_second = _memory_prior(
                    prior_log_odds,
                    previous_marginals[edge],
                    gammas[edge],
                )
                first = prior_first
                second = prior_second
                for position in range(degree):
                    direction = edge_dirs[edge, position]
                    first *= updated_factor[direction, 0]
                    second *= updated_factor[direction, 1]
                first, second = _normalise_pair(first, second)
                marginals[edge] = second
                for target_position in range(degree):
                    first = prior_first
                    second = prior_second
                    for position in range(degree):
                        if position != target_position:
                            direction = edge_dirs[edge, position]
                            first *= updated_factor[direction, 0]
                            second *= updated_factor[direction, 1]
                    first, second = _normalise_pair(first, second)
                    direction = edge_dirs[edge, target_position]
                    updated_variable[direction, 0] = first
                    updated_variable[direction, 1] = second

            max_delta = 0.0
            for direction in range(direction_count):
                delta = abs(updated_factor[direction, 0] - factor_to_variable[direction, 0])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_factor[direction, 1] - factor_to_variable[direction, 1])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_variable[direction, 0] - variable_to_factor[direction, 0])
                if delta > max_delta:
                    max_delta = delta
                delta = abs(updated_variable[direction, 1] - variable_to_factor[direction, 1])
                if delta > max_delta:
                    max_delta = delta
            factor_to_variable = updated_factor
            variable_to_factor = updated_variable
            previous_marginals = marginals.copy()
            if max_delta < tolerance:
                converged = True
                break
        return marginals, variable_to_factor, converged, max_delta, iteration

else:

    def legacy_infer_dense(*args, **kwargs):
        raise RuntimeError("Numba is unavailable in this Python environment")

    def residual_priority_infer_dense(*args, **kwargs):
        raise RuntimeError("Numba is unavailable in this Python environment")

    def residual_priority_infer_dense_reuse(*args, **kwargs):
        raise RuntimeError("Numba is unavailable in this Python environment")

    def residual_priority_infer_dense_cached(*args, **kwargs):
        raise RuntimeError("Numba is unavailable in this Python environment")

    def memory_leg_dense(*args, **kwargs):
        raise RuntimeError("Numba is unavailable in this Python environment")
