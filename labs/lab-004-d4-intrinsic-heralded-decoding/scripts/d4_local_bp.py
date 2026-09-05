"""Exact binary table messages and the nonnegative R6D D4 factor graph."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from itertools import product
from pathlib import Path

import numpy as np

from d4_belief_factorization import PublicD4Observation, local_edge_flow_factor_weight
from d4_honeycomb import PeriodicHoneycomb, generate_loop_constraints
from herald_decoder.numba_bp_kernels import NUMBA_AVAILABLE, dense_topology, njit


# The Python recurrence remains an equivalence/reference implementation.  All
# production scans must use the dense template path below.  Keep this identity
# in one module so manifests, rows, and checkpoint guards cannot silently drift
# apart when a faster implementation is added.
R6D_DENSE_BACKEND_ID = "r6d_dense_template_numba_v1"
R6D_PYTHON_REFERENCE_ID = "r6d_python_table_reference_v1"


def r6d_dense_backend_provenance() -> dict[str, object]:
    """Return the runtime identity of the production R6D BP backend."""

    source_path = Path(__file__).resolve()
    return {
        "implementation": R6D_DENSE_BACKEND_ID,
        "module": source_path.name,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "numba_available": bool(NUMBA_AVAILABLE),
    }


def require_r6d_dense_backend(expected_implementation: str | None = None) -> dict[str, object]:
    """Fail closed unless the validated dense-Numba backend is available."""

    provenance = r6d_dense_backend_provenance()
    if not NUMBA_AVAILABLE:
        raise RuntimeError("production R6D BP requires the dense Numba backend")
    if expected_implementation is not None and provenance["implementation"] != expected_implementation:
        raise RuntimeError(
            "requested R6D BP implementation does not match the validated dense backend: "
            f"{expected_implementation!r} != {provenance['implementation']!r}"
        )
    return provenance


def validate_r6d_dense_checkpoint(payload: dict[str, object]) -> None:
    """Reject checkpoints that lack exact dense-backend provenance.

    Checkpoints are resumable scientific artifacts.  A row produced by the
    Python reference recurrence is numerically comparable but is not silently
    interchangeable with a production dense-Numba row.
    """

    expected = r6d_dense_backend_provenance()
    recorded = payload.get("backend_provenance")
    if recorded != expected:
        raise RuntimeError(
            "refusing checkpoint without matching dense-Numba provenance; "
            "start a fresh checkpoint with the production backend"
        )
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("checkpoint rows must be a list")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"checkpoint row {index} is not an object")
        policies = row.get("policies", {})
        if not isinstance(policies, dict):
            raise RuntimeError(f"checkpoint row {index} policies are not an object")
        if row.get("status") == "terminal_physical_winding":
            continue
        bp = policies.get("R6D_local_BP_posterior_LLR_MWPM")
        if not isinstance(bp, dict) or bp.get("backend_provenance") != expected:
            raise RuntimeError(
                f"refusing checkpoint row {index} without matching dense-Numba BP provenance"
            )


@dataclass(frozen=True)
class BinaryFactor:
    name: str
    variables: tuple[int, ...]
    table: np.ndarray

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("factor name must be nonempty")
        if len(self.variables) != len(set(self.variables)):
            raise ValueError("factor scope contains duplicate variables")
        table = np.asarray(self.table, dtype=float)
        if table.shape != (2,) * len(self.variables):
            raise ValueError("factor table shape does not match binary scope")
        if not np.isfinite(table).all() or np.any(table < 0):
            raise ValueError("factor table must be finite and nonnegative")
        object.__setattr__(self, "table", table)


@dataclass(frozen=True)
class BinaryFactorGraph:
    variable_count: int
    priors: np.ndarray
    factors: tuple[BinaryFactor, ...]

    def __post_init__(self) -> None:
        priors = np.asarray(self.priors, dtype=float)
        if priors.shape != (self.variable_count, 2):
            raise ValueError("priors must have shape (variable_count, 2)")
        if not np.isfinite(priors).all() or np.any(priors < 0):
            raise ValueError("priors must be finite and nonnegative")
        sums = priors.sum(axis=1)
        if np.any(sums <= 0):
            raise ValueError("every variable prior must have positive mass")
        priors = priors / sums[:, None]
        for factor in self.factors:
            if any(variable < 0 or variable >= self.variable_count for variable in factor.variables):
                raise ValueError("factor variable is out of range")
        object.__setattr__(self, "priors", priors)


@dataclass(frozen=True)
class SumProductResult:
    marginals: np.ndarray
    converged: bool
    iterations: int
    max_message_delta: float


@dataclass(frozen=True)
class R6DDenseTemplate:
    lattice: PeriodicHoneycomb
    priors: np.ndarray
    arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    incident: tuple[tuple[int, ...], ...]


@lru_cache(maxsize=None)
def assignments(arity: int) -> np.ndarray:
    return np.asarray(list(product((0, 1), repeat=arity)), dtype=np.int8)


def normalise(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(values.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("zero-probability BP message")
    return values / total


def incident_edges_by_vertex(lattice: PeriodicHoneycomb) -> tuple[tuple[int, ...], ...]:
    """Return incident physical-edge indices in O(E) time.

    The previous per-vertex ``flatnonzero`` scan was O(VE), which became a
    material construction bottleneck at production lattice sizes.  This is a
    topology-only transformation: edge order and each vertex's ascending edge
    order are preserved, so all factor scopes and message ordering remain
    unchanged.
    """

    incident: list[list[int]] = [[] for _ in range(lattice.vertex_count)]
    for edge, endpoints in enumerate(lattice.edge_vertices):
        first, second = (int(value) for value in endpoints)
        incident[first].append(edge)
        incident[second].append(edge)
    return tuple(tuple(edges) for edges in incident)


def _incidences(graph: BinaryFactorGraph) -> tuple[tuple[tuple[int, int], ...], ...]:
    by_variable: list[list[tuple[int, int]]] = [list() for _ in range(graph.variable_count)]
    for factor_index, factor in enumerate(graph.factors):
        for position, variable in enumerate(factor.variables):
            by_variable[variable].append((factor_index, position))
    return tuple(tuple(items) for items in by_variable)


def _factor_message(
    factor: BinaryFactor,
    target_position: int,
    variable_to_factor: dict[tuple[int, int], np.ndarray],
    factor_index: int,
) -> np.ndarray:
    states = assignments(len(factor.variables))
    values = factor.table.reshape(-1).copy()
    for position, _variable in enumerate(factor.variables):
        if position == target_position:
            continue
        values *= variable_to_factor[(factor_index, position)][states[:, position]]
    return normalise(
        np.bincount(states[:, target_position], weights=values, minlength=2).astype(float)
    )


def run_sum_product(
    graph: BinaryFactorGraph,
    *,
    old_message_weight: float,
    max_iterations: int,
    tolerance: float,
) -> SumProductResult:
    """Run synchronous probability-space sum product with optional damping."""

    if not 0 <= old_message_weight < 1:
        raise ValueError("old_message_weight must lie in [0, 1)")
    if max_iterations < 1 or tolerance <= 0:
        raise ValueError("invalid iteration controls")
    incidence = _incidences(graph)
    variable_to_factor = {
        (factor_index, position): graph.priors[variable].copy()
        for factor_index, factor in enumerate(graph.factors)
        for position, variable in enumerate(factor.variables)
    }
    factor_to_variable = {
        key: np.full(2, 0.5, dtype=float) for key in variable_to_factor
    }
    max_delta = float("inf")
    converged = False
    for iteration in range(1, max_iterations + 1):
        updated_factor: dict[tuple[int, int], np.ndarray] = {}
        for factor_index, factor in enumerate(graph.factors):
            for position, _variable in enumerate(factor.variables):
                key = (factor_index, position)
                raw = _factor_message(factor, position, variable_to_factor, factor_index)
                updated_factor[key] = normalise(
                    old_message_weight * factor_to_variable[key]
                    + (1.0 - old_message_weight) * raw
                )

        updated_variable: dict[tuple[int, int], np.ndarray] = {}
        for variable, variable_incidence in enumerate(incidence):
            for target in variable_incidence:
                message = graph.priors[variable].copy()
                for source in variable_incidence:
                    if source != target:
                        message *= updated_factor[source]
                updated_variable[target] = normalise(message)

        max_delta = 0.0
        for key, message in updated_factor.items():
            max_delta = max(max_delta, float(np.max(np.abs(message - factor_to_variable[key]))))
        for key, message in updated_variable.items():
            max_delta = max(max_delta, float(np.max(np.abs(message - variable_to_factor[key]))))
        factor_to_variable = updated_factor
        variable_to_factor = updated_variable
        if max_delta < tolerance:
            converged = True
            break

    marginals = np.empty((graph.variable_count, 2), dtype=float)
    for variable, variable_incidence in enumerate(incidence):
        belief = graph.priors[variable].copy()
        for source in variable_incidence:
            belief *= factor_to_variable[source]
        marginals[variable] = normalise(belief)
    return SumProductResult(marginals, converged, iteration, max_delta)


def dense_factor_graph_arrays(
    graph: BinaryFactorGraph,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Pack one binary factor graph into static dense arrays for the Numba kernel.

    This transformation preserves factor order, assignment order, and message
    update order of :func:`run_sum_product`; it does not change the R6D model.
    """

    factor_variables = tuple(factor.variables for factor in graph.factors)
    by_variable: list[list[int]] = [[] for _ in range(graph.variable_count)]
    for factor, variables in enumerate(factor_variables):
        for variable in variables:
            by_variable[variable].append(factor)
    (
        factor_dirs,
        factor_degrees,
        variable_dirs,
        variable_degrees,
        directed_keys,
    ) = dense_topology(factor_variables, tuple(tuple(items) for items in by_variable))
    direction_variables = np.asarray(
        [variable for variable, _factor in directed_keys], dtype=np.int64
    )
    max_degree = int(factor_dirs.shape[1])
    tables = np.zeros((len(graph.factors), 1 << max_degree), dtype=np.float64)
    for index, factor in enumerate(graph.factors):
        tables[index, : 1 << len(factor.variables)] = factor.table.reshape(-1)
    return (
        factor_dirs,
        factor_degrees,
        variable_dirs,
        variable_degrees,
        direction_variables,
        tables,
    )


if NUMBA_AVAILABLE:

    @njit(cache=True)
    def _run_sum_product_dense_numba(
        priors,
        factor_dirs,
        factor_degrees,
        variable_dirs,
        variable_degrees,
        direction_variables,
        factor_tables,
        old_message_weight,
        max_iterations,
        tolerance,
    ):
        direction_count = direction_variables.shape[0]
        variable_to_factor = np.empty((direction_count, 2), dtype=np.float64)
        factor_to_variable = np.full((direction_count, 2), 0.5, dtype=np.float64)
        for direction in range(direction_count):
            variable = direction_variables[direction]
            variable_to_factor[direction, 0] = priors[variable, 0]
            variable_to_factor[direction, 1] = priors[variable, 1]
        converged = False
        max_delta = np.inf
        valid = True
        iteration = 0
        for iteration in range(1, max_iterations + 1):
            updated_factor = np.empty_like(factor_to_variable)
            for factor in range(factor_dirs.shape[0]):
                degree = factor_degrees[factor]
                for target_position in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        value = factor_tables[factor, mask]
                        if value == 0.0:
                            continue
                        for position in range(degree):
                            if position != target_position:
                                direction = factor_dirs[factor, position]
                                bit = (mask >> (degree - 1 - position)) & 1
                                value *= variable_to_factor[direction, bit]
                        bit = (mask >> (degree - 1 - target_position)) & 1
                        if bit == 0:
                            first += value
                        else:
                            second += value
                    total = first + second
                    if not np.isfinite(total) or total <= 0.0:
                        valid = False
                        return variable_to_factor, False, iteration, np.inf, valid
                    first /= total
                    second /= total
                    direction = factor_dirs[factor, target_position]
                    first = old_message_weight * factor_to_variable[direction, 0] + (1.0 - old_message_weight) * first
                    second = old_message_weight * factor_to_variable[direction, 1] + (1.0 - old_message_weight) * second
                    total = first + second
                    if not np.isfinite(total) or total <= 0.0:
                        valid = False
                        return variable_to_factor, False, iteration, np.inf, valid
                    updated_factor[direction, 0] = first / total
                    updated_factor[direction, 1] = second / total

            updated_variable = np.empty_like(variable_to_factor)
            for variable in range(variable_dirs.shape[0]):
                degree = variable_degrees[variable]
                for target_position in range(degree):
                    first = priors[variable, 0]
                    second = priors[variable, 1]
                    for position in range(degree):
                        if position != target_position:
                            direction = variable_dirs[variable, position]
                            first *= updated_factor[direction, 0]
                            second *= updated_factor[direction, 1]
                    total = first + second
                    if not np.isfinite(total) or total <= 0.0:
                        valid = False
                        return variable_to_factor, False, iteration, np.inf, valid
                    direction = variable_dirs[variable, target_position]
                    updated_variable[direction, 0] = first / total
                    updated_variable[direction, 1] = second / total

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

        marginals = np.empty((variable_dirs.shape[0], 2), dtype=np.float64)
        for variable in range(variable_dirs.shape[0]):
            first = priors[variable, 0]
            second = priors[variable, 1]
            for position in range(variable_degrees[variable]):
                direction = variable_dirs[variable, position]
                first *= factor_to_variable[direction, 0]
                second *= factor_to_variable[direction, 1]
            total = first + second
            if not np.isfinite(total) or total <= 0.0:
                valid = False
                return marginals, False, iteration, np.inf, valid
            marginals[variable, 0] = first / total
            marginals[variable, 1] = second / total
        return marginals, converged, iteration, max_delta, valid


    @njit(cache=True)
    def _refresh_r6d_dense_tables_numba(tables, flux, charge, vertex_colors, edge_count, signal_only):
        """Refresh observation-dependent rows in a reusable dense table buffer."""
        vertex_count = flux.shape[0]
        for vertex in range(vertex_count):
            for column in range(tables.shape[1]):
                tables[vertex, column] = 0.0
            measured = charge[vertex] != -1
            for mask in range(8):
                degree = ((mask >> 2) & 1) + ((mask >> 1) & 1) + (mask & 1)
                allowed = measured == (degree == 2)
                if signal_only:
                    allowed = not (charge[vertex] == 1 and degree != 2)
                if degree % 2 == flux[vertex] and allowed:
                    tables[vertex, mask] = 0.5 if degree == 2 else 1.0
            for colour in range(2):
                row = vertex_count + colour * (edge_count + vertex_count) + edge_count + vertex
                for column in range(tables.shape[1]):
                    tables[row, column] = 0.0
                for mask in range(64):
                    selected = ((mask >> 5) & 1) + ((mask >> 4) & 1) + ((mask >> 3) & 1)
                    if selected != 2:
                        tables[row, mask] = 2.0 ** (-selected / 2.0)
                        continue
                    required = charge[vertex] if vertex_colors[vertex] == colour else 0
                    if required < 0 or required > 1:
                        continue
                    first = -1
                    second = -1
                    for position in range(3):
                        if (mask >> (5 - position)) & 1:
                            if first < 0:
                                first = position
                            else:
                                second = position
                    first_flow = (mask >> (2 - first)) & 1
                    second_flow = (mask >> (2 - second)) & 1
                    if (first_flow ^ second_flow) == required:
                        tables[row, mask] = 1.0
        return tables


def run_sum_product_dense_numba(
    graph: BinaryFactorGraph,
    *,
    old_message_weight: float,
    max_iterations: int,
    tolerance: float,
) -> SumProductResult:
    """Compiled dense equivalent of the fixed synchronous R6D recurrence."""

    if not NUMBA_AVAILABLE:
        raise RuntimeError("Numba is unavailable for the dense R6D BP kernel")
    if not 0 <= old_message_weight < 1:
        raise ValueError("old_message_weight must lie in [0, 1)")
    if max_iterations < 1 or tolerance <= 0:
        raise ValueError("invalid iteration controls")
    arrays = dense_factor_graph_arrays(graph)
    marginals, converged, iterations, max_delta, valid = _run_sum_product_dense_numba(
        graph.priors,
        *arrays,
        float(old_message_weight),
        int(max_iterations),
        float(tolerance),
    )
    if not valid:
        raise ValueError("zero-probability BP message")
    return SumProductResult(marginals, bool(converged), int(iterations), float(max_delta))


def build_r6d_dense_template(lattice: PeriodicHoneycomb, *, error_rate: float) -> R6DDenseTemplate:
    """Build fixed-L scopes and static tables once for many observations."""
    empty = PublicD4Observation((0,) * lattice.vertex_count, (0,) * lattice.vertex_count)
    graph = build_r6d_factor_graph(lattice, empty, error_rate=error_rate, terminal_screened=False)
    return R6DDenseTemplate(lattice, graph.priors, dense_factor_graph_arrays(graph), incident_edges_by_vertex(lattice))


def refresh_r6d_dense_tables(template: R6DDenseTemplate, observation: PublicD4Observation) -> np.ndarray:
    """Refresh local observation/flow tables while preserving all topology."""
    lattice = template.lattice
    if len(observation.flux_syndrome) != lattice.vertex_count:
        raise ValueError("observation has the wrong vertex count")
    if not NUMBA_AVAILABLE:
        raise RuntimeError("Numba is unavailable for the dense R6D table refresh")
    return _refresh_r6d_dense_tables_numba(
        template.arrays[-1], np.asarray(observation.flux_syndrome, dtype=np.int64),
        np.asarray(observation.charge_outcomes, dtype=np.int64),
        np.asarray(lattice.vertex_colors, dtype=np.int64), lattice.edge_count,
        bool(np.all(np.asarray(observation.charge_outcomes, dtype=np.int64) != -1)),
    )
    tables = template.arrays[-1].copy()
    edges, vertices = lattice.edge_count, lattice.vertex_count
    for vertex, vertex_edges in enumerate(template.incident):
        arity = len(vertex_edges)
        tables[vertex] = 0.0
        for mask, bits in enumerate(product((0, 1), repeat=arity)):
            degree = sum(bits)
            measured = int(observation.charge_outcomes[vertex]) != -1
            if degree % 2 == int(observation.flux_syndrome[vertex]) and measured == (degree == 2):
                tables[vertex, mask] = 0.5 if degree == 2 else 1.0
        for colour in (0, 1):
            row = vertices + colour * (edges + vertices) + edges + vertex
            tables[row] = 0.0
            for mask, bits in enumerate(product((0, 1), repeat=2 * arity)):
                selected, flow = bits[:arity], bits[arity:]
                degree = sum(selected)
                if degree != 2:
                    tables[row, mask] = 2.0 ** (-degree / 2.0)
                    continue
                required = int(observation.charge_outcomes[vertex]) if int(lattice.vertex_colors[vertex]) == colour else 0
                if required in (0, 1):
                    hits = [index for index, value in enumerate(selected) if value]
                    if (flow[hits[0]] ^ flow[hits[1]]) == required:
                        tables[row, mask] = 1.0
    return tables


def run_r6d_dense_template(template: R6DDenseTemplate, observation: PublicD4Observation, *, old_message_weight: float, max_iterations: int, tolerance: float) -> SumProductResult:
    """Run the same recurrence without rebuilding Python factor objects."""
    arrays = (*template.arrays[:-1], refresh_r6d_dense_tables(template, observation))
    marginals, converged, iterations, max_delta, valid = _run_sum_product_dense_numba(template.priors, *arrays, old_message_weight, max_iterations, tolerance)
    if not valid:
        raise ValueError("zero-probability BP message")
    return SumProductResult(marginals, bool(converged), int(iterations), float(max_delta))


def exact_marginals(graph: BinaryFactorGraph) -> tuple[np.ndarray, float]:
    """Brute-force a small binary graph; used only for registered controls."""

    if graph.variable_count > 24:
        raise ValueError("generic exact enumeration is limited to 24 variables")
    weighted = np.zeros((graph.variable_count, 2), dtype=float)
    evidence = 0.0
    for state_tuple in product((0, 1), repeat=graph.variable_count):
        state = np.asarray(state_tuple, dtype=np.int8)
        weight = float(np.prod(graph.priors[np.arange(graph.variable_count), state]))
        for factor in graph.factors:
            weight *= float(factor.table[tuple(state[list(factor.variables)])])
            if weight == 0.0:
                break
        evidence += weight
        for variable, value in enumerate(state):
            weighted[variable, value] += weight
    if evidence <= 0:
        raise ValueError("factor graph has zero evidence")
    return weighted / evidence, evidence


def build_r6d_factor_graph(
    lattice: PeriodicHoneycomb,
    observation: PublicD4Observation,
    *,
    error_rate: float,
    terminal_screened: bool,
) -> BinaryFactorGraph:
    """Build the fixed nonnegative R6D graph for one public observation."""

    if not 0 < error_rate < 1:
        raise ValueError("error_rate must lie strictly between zero and one")
    if len(observation.flux_syndrome) != lattice.vertex_count:
        raise ValueError("observation has the wrong vertex count")
    edge_count = lattice.edge_count
    variable_count = 3 * edge_count
    priors = np.full((variable_count, 2), 0.5, dtype=float)
    priors[:edge_count] = (1.0 - error_rate, error_rate)
    incident = incident_edges_by_vertex(lattice)
    signal_only = all(int(value) != -1 for value in observation.charge_outcomes)
    factors: list[BinaryFactor] = []

    for vertex, vertex_edges in enumerate(incident):
        table = np.zeros((2,) * len(vertex_edges), dtype=float)
        for bits in product((0, 1), repeat=len(vertex_edges)):
            degree = sum(bits)
            measured = int(observation.charge_outcomes[vertex]) != -1
            if degree % 2 != int(observation.flux_syndrome[vertex]):
                continue
            if (measured != (degree == 2)) if not signal_only else (int(observation.charge_outcomes[vertex]) == 1 and degree != 2):
                continue
            table[bits] = 0.5 if degree == 2 else 1.0
        factors.append(BinaryFactor(f"observation-v{vertex}", vertex_edges, table))

    for colour in (0, 1):
        flow_offset = edge_count * (1 + colour)
        for edge in range(edge_count):
            factors.append(
                BinaryFactor(
                    f"pin-c{colour}-e{edge}",
                    (edge, flow_offset + edge),
                    np.asarray([[1.0, 0.0], [1.0, 1.0]], dtype=float),
                )
            )
        for vertex, vertex_edges in enumerate(incident):
            scope = vertex_edges + tuple(flow_offset + edge for edge in vertex_edges)
            table = np.zeros((2,) * len(scope), dtype=float)
            arity = len(vertex_edges)
            for bits in product((0, 1), repeat=len(scope)):
                selected = bits[:arity]
                flow = bits[arity:]
                selected_positions = tuple(
                    position for position, value in enumerate(selected) if value
                )
                degree = len(selected_positions)
                if degree == 2:
                    required = (
                        int(observation.charge_outcomes[vertex])
                        if int(lattice.vertex_colors[vertex]) == colour
                        else 0
                    )
                    if required not in (0, 1):
                        continue
                    if (flow[selected_positions[0]] ^ flow[selected_positions[1]]) != required:
                        continue
                    table[bits] = 1.0
                else:
                    table[bits] = 2.0 ** (-degree / 2.0)
            factors.append(BinaryFactor(f"flow-c{colour}-v{vertex}", scope, table))

    if terminal_screened:
        table = np.ones((2,) * edge_count, dtype=float)
        for bits in product((0, 1), repeat=edge_count):
            selected = np.asarray(bits, dtype=bool)
            analysis = generate_loop_constraints(lattice, selected)
            if any(
                component.nonbranching_closed and not component.homologically_trivial
                for component in analysis.components
            ):
                table[bits] = 0.0
        factors.append(BinaryFactor("finite-terminal-projector", tuple(range(edge_count)), table))

    return BinaryFactorGraph(variable_count, priors, tuple(factors))


def build_r6d_superfactor_graph(
    lattice: PeriodicHoneycomb,
    observation: PublicD4Observation,
    *,
    error_rate: float,
    terminal_screened: bool,
) -> BinaryFactorGraph:
    """Build an exact bounded clustering of the R6D nonnegative graph.

    The two colour pin factors on an edge are multiplied into one arity-three
    edge factor.  At each vertex, the observation factor and the two colour
    flow factors are multiplied into one factor of arity at most nine.  This
    changes only the factor-graph representation, not its joint weight.
    """

    if not 0 < error_rate < 1:
        raise ValueError("error_rate must lie strictly between zero and one")
    if len(observation.flux_syndrome) != lattice.vertex_count:
        raise ValueError("observation has the wrong vertex count")
    edge_count = lattice.edge_count
    variable_count = 3 * edge_count
    priors = np.full((variable_count, 2), 0.5, dtype=float)
    priors[:edge_count] = (1.0 - error_rate, error_rate)
    incident = incident_edges_by_vertex(lattice)
    signal_only = all(int(value) != -1 for value in observation.charge_outcomes)
    factors: list[BinaryFactor] = []

    edge_table = np.zeros((2, 2, 2), dtype=float)
    for selected, blue_flow, green_flow in product((0, 1), repeat=3):
        if selected or not (blue_flow or green_flow):
            edge_table[selected, blue_flow, green_flow] = 1.0
    for edge in range(edge_count):
        factors.append(
            BinaryFactor(
                f"edge-superfactor-e{edge}",
                (edge, edge_count + edge, 2 * edge_count + edge),
                edge_table,
            )
        )

    for vertex, vertex_edges in enumerate(incident):
        arity = len(vertex_edges)
        scope = (
            vertex_edges
            + tuple(edge_count + edge for edge in vertex_edges)
            + tuple(2 * edge_count + edge for edge in vertex_edges)
        )
        table = np.zeros((2,) * len(scope), dtype=float)
        for bits in product((0, 1), repeat=len(scope)):
            selected = bits[:arity]
            blue_flow = bits[arity : 2 * arity]
            green_flow = bits[2 * arity :]
            degree = sum(selected)
            measured = int(observation.charge_outcomes[vertex]) != -1
            if degree % 2 != int(observation.flux_syndrome[vertex]):
                continue
            if (measured != (degree == 2)) if not signal_only else (int(observation.charge_outcomes[vertex]) == 1 and degree != 2):
                continue
            if degree == 2:
                selected_positions = tuple(
                    position for position, value in enumerate(selected) if value
                )
                for colour, flow in ((0, blue_flow), (1, green_flow)):
                    required = (
                        int(observation.charge_outcomes[vertex])
                        if int(lattice.vertex_colors[vertex]) == colour
                        else 0
                    )
                    if (flow[selected_positions[0]] ^ flow[selected_positions[1]]) != required:
                        break
                else:
                    table[bits] = 0.5
            else:
                # Preserve the exact floating-point product of the two
                # original colour-flow factors, not merely its algebraic
                # simplification, so the merge identity is bitwise auditable.
                table[bits] = (2.0 ** (-degree / 2.0)) ** 2
        factors.append(BinaryFactor(f"vertex-superfactor-v{vertex}", scope, table))

    if terminal_screened:
        terminal_table = np.ones((2,) * edge_count, dtype=float)
        for bits in product((0, 1), repeat=edge_count):
            selected = np.asarray(bits, dtype=bool)
            analysis = generate_loop_constraints(lattice, selected)
            if any(
                component.nonbranching_closed and not component.homologically_trivial
                for component in analysis.components
            ):
                terminal_table[bits] = 0.0
        factors.append(
            BinaryFactor(
                "finite-terminal-projector", tuple(range(edge_count)), terminal_table
            )
        )
    return BinaryFactorGraph(variable_count, priors, tuple(factors))


def build_exact_physical_factor_graph(
    lattice: PeriodicHoneycomb,
    observation: PublicD4Observation,
    *,
    error_rate: float,
    terminal_screened: bool,
) -> BinaryFactorGraph:
    """Exactly contract R6D auxiliaries into one finite physical factor.

    This is an exact primitive-system ceiling, not a scalable representation:
    its table has ``2**edge_count`` entries and arity ``edge_count``.
    """

    if not 0 < error_rate < 1:
        raise ValueError("error_rate must lie strictly between zero and one")
    if len(observation.flux_syndrome) != lattice.vertex_count:
        raise ValueError("observation has the wrong vertex count")
    edge_count = lattice.edge_count
    table = np.zeros((2,) * edge_count, dtype=float)
    for bits in product((0, 1), repeat=edge_count):
        selected = np.asarray(bits, dtype=bool)
        table[bits] = local_edge_flow_factor_weight(
            lattice,
            selected,
            observation,
            terminal_winding=terminal_screened,
        ).probability
    priors = np.tile((1.0 - error_rate, error_rate), (edge_count, 1))
    return BinaryFactorGraph(
        edge_count,
        priors,
        (BinaryFactor("exact-physical-likelihood", tuple(range(edge_count)), table),),
    )
