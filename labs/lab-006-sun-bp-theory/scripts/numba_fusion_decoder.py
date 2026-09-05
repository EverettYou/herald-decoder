#!/usr/bin/env python3
"""Fast SU(3) fusion BP and posterior-LLR belief matching for Lab 006 A1."""
from __future__ import annotations

from dataclasses import dataclass
from math import comb, log

import numpy as np
from scipy.sparse import csc_matrix

from sun_fusion_bp import Graph

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:
    njit = None
    NUMBA_AVAILABLE = False

try:
    import pymatching
    PYMATCHING_AVAILABLE = True
except Exception:
    pymatching = None
    PYMATCHING_AVAILABLE = False

IRREPS = (
    "1", "3", "3bar", "6", "6bar", "8", "10", "10bar", "15",
    "15bar", "15prime", "15primebar", "24", "24bar", "27",
)
IRREP_TO_CODE = {name: code for code, name in enumerate(IRREPS)}
GROUP_IRREPS = {
    "None": ("1",),
    "U1": ("0", "+1", "-1", "+2", "-2", "+3", "-3", "+4", "-4"),
    "SU2": ("1", "2", "3", "4", "5"),
    "SU3": IRREPS,
}

# A global lattice repeats only a small number of local incidence patterns.
# Cache their likelihood blocks by representation order, rather than deriving
# the same fusion table independently for every site and every system size.
_LOCAL_POTENTIAL_BLOCKS: dict[tuple, np.ndarray] = {}


@dataclass(frozen=True)
class GeneralizedSyndrome:
    m: np.ndarray
    irrep: tuple[str, ...]

    def arrays(self, group: str = "SU3") -> tuple[np.ndarray, np.ndarray]:
        codes = {name: code for code, name in enumerate(GROUP_IRREPS[group])}
        return (
            np.ascontiguousarray(self.m, dtype=np.uint8),
            np.ascontiguousarray([codes[x] for x in self.irrep], dtype=np.int8),
        )


@dataclass(frozen=True)
class FastBpResult:
    edge_marginals: np.ndarray
    converged: bool
    iterations: int
    max_message_delta: float


@dataclass(frozen=True)
class BeliefMatchingResult:
    correction: np.ndarray
    edge_weights: np.ndarray
    matching_weight: float
    bp: FastBpResult


def dense_topology(graph: Graph):
    incident = graph.incident
    max_factor_degree = max(len(x) for x in incident)
    factor_dirs = np.full((len(incident), max_factor_degree), -1, dtype=np.int64)
    factor_degrees = np.asarray([len(x) for x in incident], dtype=np.int64)
    edge_directions = [[] for _ in graph.edges]
    direction = 0
    for factor, leaves in enumerate(incident):
        for position, (edge, _) in enumerate(leaves):
            factor_dirs[factor, position] = direction
            edge_directions[edge].append(direction)
            direction += 1
    max_edge_degree = max(len(x) for x in edge_directions)
    edge_dirs = np.full((len(graph.edges), max_edge_degree), -1, dtype=np.int64)
    edge_degrees = np.asarray([len(x) for x in edge_directions], dtype=np.int64)
    for edge, directions in enumerate(edge_directions):
        edge_dirs[edge, :len(directions)] = directions
    return factor_dirs, factor_degrees, edge_dirs, edge_degrees


def group_fusion_distribution(group: str, leaves: tuple[str, ...]) -> dict[str, float]:
    """Degree-two local fusion laws used by the A2 comparison artifact."""
    if group == "None":
        return {"1": 1.0}
    if group == "U1":
        charge = sum(1 if leaf == "fund" else -1 for leaf in leaves)
        return {f"{charge:+d}" if charge else "0": 1.0}
    if group == "SU2":
        count = len(leaves)
        if count > 4:
            raise ValueError("SU(2) fusion table supports degree at most four")
        result = {}
        for k in range(count // 2 + 1):
            dimension = count - 2 * k + 1
            multiplicity = comb(count, k) - (comb(count, k - 1) if k else 0)
            result[str(dimension)] = multiplicity * dimension / (2 ** count)
        return result
    translated = tuple("3" if leaf == "fund" else "3bar" for leaf in leaves)
    from sun_fusion_bp import fusion_distribution
    return fusion_distribution(translated)


def group_local_likelihood(group: str, leaves: tuple[str, ...], observation,
                           m_flip: float, use_irrep: bool = True) -> float:
    syndrome, irrep = observation
    parity_probability = (1.0 - m_flip) if syndrome == (len(leaves) & 1) else m_flip
    if not use_irrep:
        return parity_probability
    distribution = group_fusion_distribution(group, leaves)
    if irrep not in distribution:
        return 0.0
    return parity_probability * distribution[irrep]


def potential_bank(graph: Graph, m_flip: float, group: str = "SU3", use_irrep: bool = True) -> np.ndarray:
    max_states = 1 << max(len(x) for x in graph.incident)
    labels = GROUP_IRREPS[group]
    bank = np.zeros((len(graph.vertices), 2, len(labels), max_states), dtype=np.float64)
    for factor in range(len(graph.vertices)):
        reps = tuple(rep for _, rep in graph.incident[factor])
        key = ("binary", group, use_irrep, m_flip, reps)
        block = _LOCAL_POTENTIAL_BLOCKS.get(key)
        if block is None:
            states = 1 << len(reps)
            block = np.zeros((2, len(labels), states), dtype=np.float64)
            for m in (0, 1):
                for code, irrep in enumerate(labels):
                    for mask in range(states):
                        active = tuple(
                            "fund" if rep == "3" else "anti"
                            for position, rep in enumerate(reps)
                            if (mask >> position) & 1
                        )
                        block[m, code, mask] = group_local_likelihood(
                            group, active, (m, irrep), m_flip, use_irrep
                        )
            _LOCAL_POTENTIAL_BLOCKS[key] = block
        bank[factor, :, :, :block.shape[2]] = block
    return bank


def undirected_potential_bank(graph: Graph, m_flip: float, group: str = "SU3", use_irrep: bool = True) -> np.ndarray:
    """Local likelihood bank for x_e in {off, stored direction, reversed direction}."""
    max_states = 3 ** max(len(x) for x in graph.incident)
    labels = GROUP_IRREPS[group]
    bank = np.zeros((len(graph.vertices), 2, len(labels), max_states), dtype=np.float64)
    for factor, leaves in enumerate(graph.incident):
        reps = tuple(rep for _, rep in leaves)
        key = ("ternary", group, use_irrep, m_flip, reps)
        block = _LOCAL_POTENTIAL_BLOCKS.get(key)
        if block is None:
            states = 3 ** len(reps)
            block = np.zeros((2, len(labels), states), dtype=np.float64)
            for m in (0, 1):
                for code, irrep in enumerate(labels):
                    for configuration in range(states):
                        value, leaves_at_vertex = configuration, []
                        for rep in reps:
                            state = value % 3
                            value //= 3
                            if state:
                                original = (rep == "3")
                                leaves_at_vertex.append("fund" if original == (state == 1) else "anti")
                        block[m, code, configuration] = group_local_likelihood(
                            group, tuple(leaves_at_vertex), (m, irrep), m_flip, use_irrep
                        )
            _LOCAL_POTENTIAL_BLOCKS[key] = block
        bank[factor, :, :, :block.shape[2]] = block
    return bank


def check_matrix(graph: Graph) -> csc_matrix:
    rows, cols = [], []
    row_for_vertex = {vertex: row for row, vertex in enumerate(graph.vertices)}
    for edge, (tail, head) in enumerate(graph.edges):
        for endpoint in (tail, head):
            if endpoint in row_for_vertex:
                rows.append(row_for_vertex[endpoint])
                cols.append(edge)
    return csc_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)), shape=(len(graph.vertices), len(graph.edges)))


if NUMBA_AVAILABLE:
    @njit(cache=True, fastmath=True)
    def _infer_min_sum_inplace(syndrome, irreps, costs, factor_dirs, factor_degrees, edge_dirs, edge_degrees, prior, states, max_iterations, damping, tolerance, variable, factors, updated_variable, updated_factors, marginals):
        inf = 1e100
        prior0, prior1 = -np.log(1.0-prior), -np.log(prior)
        for d in range(variable.shape[0]):
            for s in range(3):
                variable[d,s]=0.0; factors[d,s]=0.0
        residual=inf; converged=False
        for iteration in range(1,max_iterations+1):
            for f in range(factor_dirs.shape[0]):
                degree=factor_degrees[f]; configs=states**degree
                for target in range(degree):
                    vals=np.full(3,inf); base=states**target
                    for config in range(configs):
                        value=costs[f,syndrome[f],irreps[f],config]
                        for position in range(degree):
                            if position!=target: value+=variable[factor_dirs[f,position],(config//(states**position))%states]
                        state=(config//base)%states
                        if value<vals[state]: vals[state]=value
                    floor=vals[0]
                    for s in range(1,states):
                        if vals[s]<floor: floor=vals[s]
                    d=factor_dirs[f,target]
                    for s in range(states):
                        relative=vals[s]-floor
                        if relative>1e6: relative=1e6
                        updated_factors[d,s]=damping*factors[d,s]+(1.0-damping)*relative
            for e in range(edge_dirs.shape[0]):
                for target in range(edge_degrees[e]):
                    vals=np.full(3,inf)
                    for s in range(states):
                        value=prior0 if s==0 else prior1 if states==2 else (prior1 if s==1 or s==2 else prior0)
                        if states==3 and s>0: value=-np.log(0.5*prior)
                        for position in range(edge_degrees[e]):
                            if position!=target: value+=updated_factors[edge_dirs[e,position],s]
                        vals[s]=value
                    floor=vals[0]
                    for s in range(1,states):
                        if vals[s]<floor: floor=vals[s]
                    d=edge_dirs[e,target]
                    for s in range(states): updated_variable[d,s]=vals[s]-floor
            residual=0.0
            for d in range(variable.shape[0]):
                for s in range(states):
                    residual=max(residual,abs(updated_factors[d,s]-factors[d,s]),abs(updated_variable[d,s]-variable[d,s])); factors[d,s]=updated_factors[d,s]; variable[d,s]=updated_variable[d,s]
            if residual<tolerance: converged=True; break
        for e in range(edge_dirs.shape[0]):
            c0=prior0; c1=prior1
            for pos in range(edge_degrees[e]): c0+=factors[edge_dirs[e,pos],0]
            if states==2:
                for pos in range(edge_degrees[e]): c1+=factors[edge_dirs[e,pos],1]
            else:
                c1=-np.log(0.5*prior)
                c2=c1
                for pos in range(edge_degrees[e]): c1+=factors[edge_dirs[e,pos],1]; c2+=factors[edge_dirs[e,pos],2]
                if c2<c1: c1=c2
            marginals[e]=1.0/(1.0+np.exp(c1-c0))
        return converged,iteration,residual
    @njit(cache=True, fastmath=True)
    def _infer_inplace(
        syndrome, irreps, bank, factor_dirs, factor_degrees,
        edge_dirs, edge_degrees, prior, max_iterations, damping, tolerance,
        variable, factors, updated_variable, updated_factors, marginals,
    ):
        direction_count = variable.shape[0]
        for direction in range(direction_count):
            variable[direction, 0] = 1.0 - prior
            variable[direction, 1] = prior
            factors[direction, 0] = 0.5
            factors[direction, 1] = 0.5
        converged = False
        max_delta = np.inf
        iteration = 0
        for iteration in range(1, max_iterations + 1):
            for factor in range(factor_dirs.shape[0]):
                degree = factor_degrees[factor]
                for target in range(degree):
                    first = 0.0
                    second = 0.0
                    for mask in range(1 << degree):
                        value = bank[factor, syndrome[factor], irreps[factor], mask]
                        if value == 0.0:
                            continue
                        for position in range(degree):
                            if position != target:
                                direction = factor_dirs[factor, position]
                                value *= variable[direction, (mask >> position) & 1]
                        if ((mask >> target) & 1) == 0:
                            first += value
                        else:
                            second += value
                    total = first + second
                    direction = factor_dirs[factor, target]
                    first = damping * factors[direction, 0] + (1.0 - damping) * first / total
                    second = damping * factors[direction, 1] + (1.0 - damping) * second / total
                    total = first + second
                    updated_factors[direction, 0] = first / total
                    updated_factors[direction, 1] = second / total

            for edge in range(edge_dirs.shape[0]):
                degree = edge_degrees[edge]
                for target in range(degree):
                    first = 1.0 - prior
                    second = prior
                    for position in range(degree):
                        if position != target:
                            direction = edge_dirs[edge, position]
                            first *= updated_factors[direction, 0]
                            second *= updated_factors[direction, 1]
                    total = first + second
                    direction = edge_dirs[edge, target]
                    updated_variable[direction, 0] = first / total
                    updated_variable[direction, 1] = second / total

            max_delta = 0.0
            for direction in range(direction_count):
                d0 = abs(updated_factors[direction, 0] - factors[direction, 0])
                d1 = abs(updated_factors[direction, 1] - factors[direction, 1])
                d2 = abs(updated_variable[direction, 0] - variable[direction, 0])
                d3 = abs(updated_variable[direction, 1] - variable[direction, 1])
                max_delta = max(max_delta, d0, d1, d2, d3)
                factors[direction, 0] = updated_factors[direction, 0]
                factors[direction, 1] = updated_factors[direction, 1]
                variable[direction, 0] = updated_variable[direction, 0]
                variable[direction, 1] = updated_variable[direction, 1]
            if max_delta < tolerance:
                converged = True
                break

        for edge in range(edge_dirs.shape[0]):
            first = 1.0 - prior
            second = prior
            for position in range(edge_degrees[edge]):
                direction = edge_dirs[edge, position]
                first *= factors[direction, 0]
                second *= factors[direction, 1]
            marginals[edge] = second / (first + second)
        return converged, iteration, max_delta


    @njit(cache=True, fastmath=True)
    def infer_batch_dense(
        syndromes, irreps, bank, factor_dirs, factor_degrees,
        edge_dirs, edge_degrees, prior, max_iterations, damping, tolerance,
    ):
        batch = syndromes.shape[0]
        directions = int(np.sum(factor_degrees))
        outputs = np.empty((batch, edge_dirs.shape[0]), dtype=np.float64)
        convergence = np.empty(batch, dtype=np.uint8)
        iterations = np.empty(batch, dtype=np.int64)
        residuals = np.empty(batch, dtype=np.float64)
        variable = np.empty((directions, 2), dtype=np.float64)
        factors = np.empty((directions, 2), dtype=np.float64)
        updated_variable = np.empty((directions, 2), dtype=np.float64)
        updated_factors = np.empty((directions, 2), dtype=np.float64)
        for sample in range(batch):
            converged, iteration, residual = _infer_inplace(
                syndromes[sample], irreps[sample], bank,
                factor_dirs, factor_degrees, edge_dirs, edge_degrees, prior,
                max_iterations, damping, tolerance, variable, factors,
                updated_variable, updated_factors, outputs[sample],
            )
            convergence[sample] = converged
            iterations[sample] = iteration
            residuals[sample] = residual
        return outputs, convergence, iterations, residuals


    @njit(cache=True, fastmath=True)
    def _infer_undirected_inplace(
        syndrome, irreps, bank, factor_dirs, factor_degrees,
        edge_dirs, edge_degrees, prior, max_iterations, damping, tolerance,
        variable, factors, updated_variable, updated_factors, marginals,
    ):
        """BP for x_e in {off, stored orientation, reversed orientation}."""
        directions = variable.shape[0]
        for direction in range(directions):
            variable[direction, 0] = 1.0 - prior
            variable[direction, 1] = 0.5 * prior
            variable[direction, 2] = 0.5 * prior
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
                values[1] = 0.5 * prior
                values[2] = 0.5 * prior
                for target in range(degree):
                    for state in range(3):
                        value = (1.0 - prior) if state == 0 else 0.5 * prior
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
            values[1] = 0.5 * prior
            values[2] = 0.5 * prior
            for state in range(3):
                for position in range(edge_degrees[edge]):
                    values[state] *= factors[edge_dirs[edge, position], state]
            marginals[edge] = (values[1] + values[2]) / (values[0] + values[1] + values[2])
        return converged, iteration, max_delta


class FastFusionBeliefMatchingDecoder:
    """Cached, preallocated scalar inference plus a compiled batch endpoint."""
    def __init__(self, graph: Graph, *, p: float, m_flip: float = 0.0,
                 group: str = "SU3",
                 use_irrep: bool = True,
                 max_iterations: int = 80, damping: float = 0.25, tolerance: float = 1e-10):
        if not NUMBA_AVAILABLE:
            raise RuntimeError("Numba is unavailable")
        if group not in GROUP_IRREPS:
            raise ValueError("group must be None, U1, SU2, or SU3")
        self.graph, self.p, self.m_flip, self.group, self.use_irrep = graph, p, m_flip, group, use_irrep
        self.max_iterations, self.damping, self.tolerance = max_iterations, damping, tolerance
        self.factor_dirs, self.factor_degrees, self.edge_dirs, self.edge_degrees = dense_topology(graph)
        self.bank = potential_bank(graph, m_flip, group, use_irrep)
        directions = int(self.factor_degrees.sum())
        self.variable = np.empty((directions, 2))
        self.factors = np.empty((directions, 2))
        self.updated_variable = np.empty((directions, 2))
        self.updated_factors = np.empty((directions, 2))
        self.marginals = np.empty(len(graph.edges))
        self.matrix = check_matrix(graph)

    def infer(self, observation: GeneralizedSyndrome) -> FastBpResult:
        syndrome, irreps = observation.arrays(self.group)
        converged, iterations, residual = _infer_inplace(
            syndrome, irreps, self.bank, self.factor_dirs,
            self.factor_degrees, self.edge_dirs, self.edge_degrees, self.p,
            self.max_iterations, self.damping, self.tolerance, self.variable,
            self.factors, self.updated_variable, self.updated_factors,
            self.marginals,
        )
        return FastBpResult(self.marginals.copy(), bool(converged), int(iterations), float(residual))

    def infer_batch(self, m: np.ndarray, irreps: np.ndarray):
        return infer_batch_dense(
            np.ascontiguousarray(m, dtype=np.uint8),
            np.ascontiguousarray(irreps, dtype=np.int8), self.bank,
            self.factor_dirs, self.factor_degrees, self.edge_dirs,
            self.edge_degrees, self.p, self.max_iterations, self.damping,
            self.tolerance,
        )

    def decode(self, observation: GeneralizedSyndrome, matching_m: np.ndarray | None = None) -> BeliefMatchingResult:
        if not PYMATCHING_AVAILABLE:
            raise RuntimeError("PyMatching is unavailable")
        if self.m_flip != 0.0:
            raise ValueError("hard matching currently requires a perfect binary m syndrome")
        bp = self.infer(observation)
        clipped = np.clip(bp.edge_marginals, 1e-12, 1.0 - 1e-12)
        weights = np.log((1.0 - clipped) / clipped)
        matching = pymatching.Matching.from_check_matrix(self.matrix, weights=weights)
        matching_syndrome = observation.m if matching_m is None else matching_m
        correction, matching_weight = matching.decode(np.asarray(matching_syndrome, dtype=np.uint8), return_weight=True)
        return BeliefMatchingResult(correction.astype(np.uint8), weights, float(matching_weight), bp)


class UndirectedFusionBeliefMatchingDecoder(FastFusionBeliefMatchingDecoder):
    """Belief matching with a hidden 50/50 orientation on each active edge."""
    def __init__(self, graph: Graph, **kwargs):
        super().__init__(graph, **kwargs)
        self.bank = undirected_potential_bank(graph, self.m_flip, self.group, self.use_irrep)
        directions = int(self.factor_degrees.sum())
        self.variable = np.empty((directions, 3))
        self.factors = np.empty((directions, 3))
        self.updated_variable = np.empty((directions, 3))
        self.updated_factors = np.empty((directions, 3))

    def infer(self, observation: GeneralizedSyndrome) -> FastBpResult:
        syndrome, irreps = observation.arrays(self.group)
        converged, iterations, residual = _infer_undirected_inplace(
            syndrome, irreps, self.bank, self.factor_dirs,
            self.factor_degrees, self.edge_dirs, self.edge_degrees, self.p,
            self.max_iterations, self.damping, self.tolerance, self.variable,
            self.factors, self.updated_variable, self.updated_factors,
            self.marginals,
        )
        return FastBpResult(self.marginals.copy(), bool(converged), int(iterations), float(residual))


class MinSumFusionBeliefMatchingDecoder(FastFusionBeliefMatchingDecoder):
    """Numba min-sum / min-marginal belief matching for either edge alphabet."""
    def __init__(self, graph: Graph, *, undirected: bool = False, **kwargs):
        super().__init__(graph, **kwargs)
        self.states = 3 if undirected else 2
        if undirected:
            self.bank = undirected_potential_bank(graph, self.m_flip, self.group, self.use_irrep)
        self.costs = np.where(self.bank > 0.0, -np.log(np.maximum(self.bank, 1e-300)), 1e100)
        directions = int(self.factor_degrees.sum())
        self.variable = np.empty((directions, 3))
        self.factors = np.empty((directions, 3))
        self.updated_variable = np.empty((directions, 3))
        self.updated_factors = np.empty((directions, 3))

    def infer(self, observation: GeneralizedSyndrome) -> FastBpResult:
        syndrome, irreps = observation.arrays(self.group)
        converged, iterations, residual = _infer_min_sum_inplace(
            syndrome, irreps, self.costs, self.factor_dirs, self.factor_degrees,
            self.edge_dirs, self.edge_degrees, self.p, self.states,
            self.max_iterations, self.damping, self.tolerance, self.variable,
            self.factors, self.updated_variable, self.updated_factors, self.marginals,
        )
        return FastBpResult(self.marginals.copy(), bool(converged), int(iterations), float(residual))
