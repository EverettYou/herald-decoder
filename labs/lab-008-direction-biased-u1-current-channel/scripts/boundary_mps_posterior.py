"""Charge-only boundary-MPS contraction for the ternary U(1) current model.

Local tensors contain only the frozen current prior, measured charge delta,
and logical-cut parity.  A dense boundary tensor is used only as the local
work buffer; between vertices it is factorized by TT-SVD and optionally
truncated to a fixed bond dimension.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.sparse.linalg import svds
from numpy.linalg import LinAlgError


ALPHABET = np.asarray([0, 1, -1], dtype=np.int8)


def _tt_svd(tensor: np.ndarray, chi: int | None, solver: str = "full") -> tuple[list[np.ndarray], float]:
    dims = tensor.shape
    cores: list[np.ndarray] = []
    work = tensor
    left = 1
    discarded = 0.0
    for dim in dims[:-1]:
        matrix = work.reshape(left * dim, -1)
        min_dim = min(matrix.shape)
        use_partial = solver == "propack" and chi is not None and chi < min_dim
        if use_partial:
            try:
                u, s, vh = svds(
                    matrix, k=chi, which="LM", solver="propack", tol=1e-13,
                    maxiter=2000, return_singular_vectors=True, rng=0,
                )
                order = np.argsort(s)[::-1]
                u, s, vh = u[:, order], s[order], vh[order]
                rank = chi
                discarded += max(0.0, float(np.square(matrix).sum() - np.square(s).sum()))
            except LinAlgError:
                use_partial = False
        if not use_partial:
            u, s, vh = np.linalg.svd(matrix, full_matrices=False)
            rank = len(s) if chi is None else min(len(s), chi)
            discarded += float(np.square(s[rank:]).sum())
        cores.append(u[:, :rank].reshape(left, dim, rank))
        work = s[:rank, None] * vh[:rank]
        left = rank
    cores.append(work.reshape(left, dims[-1], 1))
    return cores, discarded


def _tt_dense(cores: list[np.ndarray]) -> np.ndarray:
    out = cores[0]
    for core in cores[1:]:
        out = np.tensordot(out, core, axes=(-1, 0))
    return np.squeeze(out, axis=(0, -1))


@dataclass
class BoundaryMPSResult:
    sectors: np.ndarray
    bayes_risk: float
    signed_gap: float
    log_evidence: float
    maximum_bond: int
    discarded_frobenius_sq: float
    minimum_sector_mass: float


class BoundaryMPSPosterior:
    def __init__(self, model, *, order=None):
        self.model = model
        self.measured = tuple(model.detector_vertices)
        self.row = {v: i for i, v in enumerate(self.measured)}
        if order is None:
            order = list(self.measured)
        self.order = list(order)
        self.steps = self._steps()

    def _steps(self):
        visited, assigned = set(), set()
        frontier, steps = [], []
        measured = set(self.measured)
        for vertex in self.order:
            old = [edge for edge in self.model.incident_edges[vertex] if edge in assigned]
            new = [edge for edge in self.model.incident_edges[vertex] if edge not in assigned]
            keep = [edge for edge in frontier if edge not in old]
            visited.add(vertex)
            future = [
                edge for edge in new
                if any(v in measured and v not in visited for v in self.model.edges[edge])
            ]
            steps.append((list(frontier), old, new, keep, future, vertex))
            assigned.update(new)
            frontier = keep + future
        if frontier or len(assigned) != len(self.model.edges):
            raise ValueError("invalid contraction order")
        return steps

    def infer(self, charges, p: float, q: float, *, chi: int | None = None,
              truncation_schedule: str = "vertex", svd_solver: str = "full") -> BoundaryMPSResult:
        charges = np.asarray(charges, dtype=int)
        if charges.shape != (len(self.measured),):
            raise ValueError("charges must contain the full measured record")
        if truncation_schedule not in {"vertex", "row"}:
            raise ValueError("truncation_schedule must be 'vertex' or 'row'")
        if svd_solver not in {"full", "propack"}:
            raise ValueError("svd_solver must be 'full' or 'propack'")
        dense = np.asarray([1.0, 0.0])  # parity is the final tensor index
        cores, _ = _tt_svd(dense, chi, svd_solver)
        dense = None
        log_evidence = 0.0
        total_discarded = 0.0
        maximum_bond = 1

        for step_index, (before, old, new, keep, future, vertex) in enumerate(self.steps):
            if dense is None:
                dense = _tt_dense(cores).reshape((3,) * len(before) + (2,))
            out = np.zeros((3,) * (len(keep) + len(future)) + (2,), dtype=float)
            old_pos = [before.index(edge) for edge in old]
            signs_old = [1 if self.model.edges[e][1] == vertex else -1 for e in old]
            signs_new = [1 if self.model.edges[e][1] == vertex else -1 for e in new]
            future_pos = [new.index(edge) for edge in future]

            for old_digits in np.ndindex(*(3,) * len(old)) if old else [()]:
                source = [slice(None)] * len(before) + [slice(None)]
                old_charge = 0
                for pos, digit, sign in zip(old_pos, old_digits, signs_old):
                    source[pos] = digit
                    old_charge += sign * int(ALPHABET[digit])
                block = dense[tuple(source)]
                for new_digits in np.ndindex(*(3,) * len(new)) if new else [()]:
                    charge = old_charge + sum(
                        sign * int(ALPHABET[digit])
                        for sign, digit in zip(signs_new, new_digits)
                    )
                    if charge != int(charges[self.row[vertex]]):
                        continue
                    values = ALPHABET[list(new_digits)] if new_digits else np.asarray([], dtype=int)
                    nplus = int(np.count_nonzero(values == 1))
                    nminus = int(np.count_nonzero(values == -1))
                    weight = (1 - p) ** (len(new) - nplus - nminus) * (p * q) ** nplus * (p * (1 - q)) ** nminus
                    parity = 0
                    for edge, digit in zip(new, new_digits):
                        if edge in self.model.logical_edges and ALPHABET[digit] != 0:
                            parity ^= 1
                    target = [slice(None)] * len(keep) + [new_digits[pos] for pos in future_pos]
                    if parity == 0:
                        out[tuple(target + [0])] += weight * block[..., 0]
                        out[tuple(target + [1])] += weight * block[..., 1]
                    else:
                        out[tuple(target + [0])] += weight * block[..., 1]
                        out[tuple(target + [1])] += weight * block[..., 0]

            scale = float(out.sum())
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("zero or nonfinite record evidence")
            out /= scale
            log_evidence += float(np.log(scale))
            next_row = None if step_index + 1 == len(self.steps) else self.model.vertices[self.steps[step_index + 1][-1]].y
            truncate_now = truncation_schedule == "vertex" or next_row != self.model.vertices[vertex].y
            if truncate_now:
                cores, discarded = _tt_svd(out, chi, svd_solver)
                total_discarded += discarded
                maximum_bond = max(maximum_bond, max(core.shape[2] for core in cores))
                dense = None
            else:
                dense = out

        sectors = (_tt_dense(cores) if dense is None else dense).reshape(2)
        sectors /= sectors.sum()
        if np.any(~np.isfinite(sectors)):
            raise ValueError("nonfinite sector posterior")
        gap = float(np.log(sectors[0] / sectors[1])) if np.all(sectors > 0) else (float("inf") if sectors[0] > 0 else -float("inf"))
        return BoundaryMPSResult(
            sectors=sectors,
            bayes_risk=float(np.min(sectors)),
            signed_gap=gap,
            log_evidence=log_evidence,
            maximum_bond=maximum_bond,
            discarded_frobenius_sq=total_discarded,
            minimum_sector_mass=float(np.min(sectors)),
        )
