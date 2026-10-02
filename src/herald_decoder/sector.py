"""Shared visible-record, correction and posterior contracts for sector decoders."""
from collections import deque
from dataclasses import dataclass
import numpy as np
from scipy.sparse import csr_matrix


class NumericalInferenceError(RuntimeError):
    """Inference failed its numerical gate; never silently substitute a sector."""


@dataclass(frozen=True)
class SectorResult:
    correction: np.ndarray
    sector_probabilities: np.ndarray | None
    method: str
    diagnostics: dict

    @property
    def conditional_risk(self):
        return None if self.sector_probabilities is None else float(np.min(self.sector_probabilities))


def validate_parameters(p, q):
    if not np.isfinite(p) or not np.isfinite(q) or not 0 <= p <= 1 or not 0 <= q <= 1:
        raise ValueError('require finite 0 <= p <= 1 and 0 <= q <= 1')


def observations(graph, s, h, p, q):
    validate_parameters(p, q)
    s, h = np.asarray(s), np.asarray(h)
    shape = (len(graph.detector_vertices),)
    if s.shape != shape or h.shape != shape or not np.all((s == 0) | (s == 1)) or not np.all((h == 0) | (h == 1)):
        raise ValueError('s and h must be binary arrays in graph.detector_vertices order')
    s, h = s.astype(np.uint8), h.astype(np.uint8)
    degree = np.array([len(graph.incident_edges[v]) for v in graph.detector_vertices])
    if (p == 0 and (s.any() or h.any())) or (q == 0 and h.any()) or np.any((h == 1) & (s + 2 > degree)):
        raise ValueError('observation has zero probability under the specified channel')
    if p == 1 and (np.any(s != (degree & 1)) or np.any((h == 1) & (degree < 2)) or (q == 1 and np.any(h != (degree >= 2)))):
        raise ValueError("observation has zero probability at p=1")
    return s, h


def batch_observations(graph, S, H, p, q):
    S, H = np.asarray(S), np.asarray(H)
    if S.ndim != 2 or H.shape != S.shape or S.shape[1] != len(graph.detector_vertices):
        raise ValueError('batch arrays must have shape (shots, detectors)')
    for s, h in zip(S, H):
        observations(graph, s, h, p, q)
    return S.astype(np.uint8), H.astype(np.uint8)


def select_sectors(probabilities, rng=None):
    probabilities = np.asarray(probabilities)
    sectors = np.argmax(probabilities, axis=-1)
    if rng is not None:
        generator = np.random.default_rng(rng)
        tied = np.abs(probabilities[:, 0] - probabilities[:, 1]) < 1e-12
        sectors[tied] = generator.integers(2, size=int(tied.sum()))
    return sectors


def reference_structure(graph):
    """Syndrome forest and one logical path; derived only from visible geometry."""
    adj = [[] for _ in graph.vertices]
    for e, (u, v) in enumerate(graph.edges):
        adj[u].append((v, e)); adj[v].append((u, e))
    parent = {}; queue = deque()
    for v in graph.boundary_vertices:
        if adj[v]: parent[v] = (None, None); queue.append(v)
    while queue:
        u = queue.popleft()
        for v, e in adj[u]:
            if v not in parent: parent[v] = (u, e); queue.append(v)
    rows, cols = [], []
    for j, v in enumerate(graph.detector_vertices):
        if v not in parent: raise ValueError('every detector must connect to an unmeasured boundary')
        while parent[v][0] is not None:
            v, e = parent[v]; rows.append(e); cols.append(j)
    T = csr_matrix((np.ones(len(rows), int), (rows, cols)), shape=(len(graph.edges),len(graph.detector_vertices)))
    # BFS from the left rough side to the right rough side.
    seen = {v:(None,None) for v in graph.boundary_vertices if graph.vertices[v].boundary_side == 'left' and adj[v]}
    queue = deque(seen); target = None
    while queue:
        u = queue.popleft()
        if graph.vertices[u].boundary_side == 'right': target = u; break
        for v,e in adj[u]:
            if v not in seen: seen[v]=(u,e); queue.append(v)
    if target is None: raise ValueError('a left-right logical path is required')
    path = np.zeros(len(graph.edges),np.uint8)
    while seen[target][0] is not None:
        target,e=seen[target];path[e]=1
    if graph.true_syndrome(path).any() or graph.logical_parity(path)!=1:
        raise ValueError('logical cut is inconsistent with the boundary path')
    return T, path


class SectorDecoderBase:
    def __init__(self, graph, *, p, q):
        validate_parameters(p,q)
        self.graph, self.p, self.q = graph,float(p),float(q)
        self._T,self._logical_path=reference_structure(graph)

    def representative(self,s,sector):
        c=np.asarray(self._T @ s).ravel().astype(np.uint8)&1
        if self.graph.logical_parity(c)!=sector:c ^= self._logical_path
        return c

    def decode(self,s,h,rng=None):
        probs,diag=self.posterior(s,h)
        # A deterministic tie convention is reproducible; explicit RNG is optional.
        sector=int(select_sectors(probs[None], rng)[0])
        return SectorResult(self.representative(np.asarray(s,np.uint8),sector),probs,self.method,diag)

    def decode_batch(self,S,H,rng=None):
        S,H=batch_observations(self.graph,S,H,self.p,self.q)
        generator = None if rng is None else np.random.default_rng(rng)
        return np.stack([self.decode(s,h,generator).correction for s,h in zip(S,H)]) if len(S) else np.empty((0,len(self.graph.edges)),np.uint8)
