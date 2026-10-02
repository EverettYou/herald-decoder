"""Lab-local copy of the frozen parent ternary BP; only sign priors generalized.

Endpoints are independently validated against the parent; production q=1 uses
its original binary kernel. Parent source remains unchanged.
"""
import numpy as np
from numba import njit

@njit(cache=True, fastmath=True)
def _infer_biased_inplace(
    syndrome, irreps, bank, factor_dirs, factor_degrees,
    edge_dirs, edge_degrees, prior, bias, max_iterations, damping, tolerance,
    variable, factors, updated_variable, updated_factors, marginals,
):
    """BP for x_e in {off, stored orientation, reversed orientation}."""
    directions = variable.shape[0]
    for direction in range(directions):
        variable[direction, 0] = 1.0 - prior
        variable[direction, 1] = bias * prior
        variable[direction, 2] = (1.0 - bias) * prior
        factors[direction, 0] = 1.0 / 3.0
        factors[direction, 1] = 1.0 / 3.0
        factors[direction, 2] = 1.0 / 3.0
    converged = False
    max_delta = np.inf
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        for factor in range(factor_dirs.shape[0]):
            degree = factor_degrees[factor]
            configurations = 3 ** degree
            for target in range(degree):
                values = np.zeros(3, dtype=np.float64)
                target_base = 3 ** target
                for configuration in range(configurations):
                    weight = bank[factor, syndrome[factor], irreps[factor], configuration]
                    if weight == 0.0:
                        continue
                    for position in range(degree):
                        if position != target:
                            direction = factor_dirs[factor, position]
                            state = (configuration // (3 ** position)) % 3
                            weight *= variable[direction, state]
                    state = (configuration // target_base) % 3
                    values[state] += weight
                total = values[0] + values[1] + values[2]
                direction = factor_dirs[factor, target]
                if total == 0.0:
                    for state in range(3):
                        updated_factors[direction, state] = 1.0 / 3.0
                else:
                    for state in range(3):
                        candidate = damping * factors[direction, state] + (1.0 - damping) * values[state] / total
                        updated_factors[direction, state] = candidate
                    normalization = updated_factors[direction, 0] + updated_factors[direction, 1] + updated_factors[direction, 2]
                    for state in range(3):
                        updated_factors[direction, state] /= normalization

        for edge in range(edge_dirs.shape[0]):
            degree = edge_degrees[edge]
            values = np.empty(3, dtype=np.float64)
            values[0] = 1.0 - prior
            values[1] = bias * prior
            values[2] = (1.0 - bias) * prior
            for target in range(degree):
                for state in range(3):
                    value = (1.0 - prior) if state == 0 else (bias * prior if state == 1 else (1.0 - bias) * prior)
                    for position in range(degree):
                        if position != target:
                            value *= updated_factors[edge_dirs[edge, position], state]
                    values[state] = value
                normalization = values[0] + values[1] + values[2]
                direction = edge_dirs[edge, target]
                for state in range(3):
                    updated_variable[direction, state] = values[state] / normalization

        max_delta = 0.0
        for direction in range(directions):
            for state in range(3):
                max_delta = max(max_delta, abs(updated_factors[direction, state] - factors[direction, state]))
                max_delta = max(max_delta, abs(updated_variable[direction, state] - variable[direction, state]))
                factors[direction, state] = updated_factors[direction, state]
                variable[direction, state] = updated_variable[direction, state]
        if max_delta < tolerance:
            converged = True
            break

    for edge in range(edge_dirs.shape[0]):
        values = np.empty(3, dtype=np.float64)
        values[0] = 1.0 - prior
        values[1] = bias * prior
        values[2] = (1.0 - bias) * prior
        for state in range(3):
            for position in range(edge_degrees[edge]):
                values[state] *= factors[edge_dirs[edge, position], state]
        marginals[edge] = (values[1] + values[2]) / (values[0] + values[1] + values[2])
    return converged, iteration, max_delta

