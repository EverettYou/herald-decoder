---
title: CZ-aware local star-factor representation gate
status: current
updated: 2026-09-24
record: true
---

## Summary

The source's kagome star operator contains both X and CZ factors. On a
three-qubit *factor* isolated from the diagram, retaining CZ changes the
measurement probability for a coherent product input. A plain Pauli-only
replacement therefore cannot be assumed equivalent before constructing the
complete lattice operator-state update.

## Evidence

The [registered contract](../../manifests/j6j-cz-star-factor-representation-2026-09-24.json),
[exact arithmetic runner](../../scripts/run_j6j_cz_star_factor_representation.py),
and [machine-readable eight-cell result](../../results/j6j-cz-star-factor-representation-2026-09-24.json)
pin the archived [Jing et al. Appendix A.1 Eq. (A2)](https://arxiv.org/html/2507.23765)
and the prior readiness audit. We transcribe one local factor as
`A = X_b CZ_(g,r)` and compare only with a diagnostic truncation `T = X_b`.
Both factors are Hermitian involutions. For `|+,+,+>`, exact projector
probabilities are `P_A(+)=3/4`, `P_A(-)=1/4`, versus `P_T(+)=1`. For the
`|+,0,0>` control, both yield `P(+)=1`. Relabeling the three qubits leaves
both contrasts unchanged. The CZ sign pattern is not a linear Pauli-Z
character. These are exact rational checks, not sampled frequencies.

## Status

This establishes an operator-representation requirement only: a generic
Pauli-only deletion of CZ can change a local measurement law. The chosen
product inputs are **not** asserted to be D4 ground states, and the isolated
factor is **not** the complete kagome star. It neither invalidates the current
parity sampler nor supplies a physical first-to-second conditional law.
Next construct and validate the full A2/A4 operator mapping on the pinned
lattice for the known path and another action or geometry, using a CZ-aware
exact representation; only then test the first-record-aware public adapter.
No histories, schedule arms, bootstraps, JIT risk or threshold were produced.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6i-general-instrument-readiness-2026-09-24|Instrument readiness]] · [[records/index|Research-record index]]
