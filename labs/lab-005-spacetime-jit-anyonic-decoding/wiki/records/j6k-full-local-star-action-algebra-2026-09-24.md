---
title: Full local star and red-X action algebra
status: current
updated: 2026-09-24
record: true
---

## Summary

An exact 12-qubit, single-star construction now retains all six CZ ring
factors, six outer X factors and both color-triangle Z operators. Exhaustive
red-X conjugation confirms geometry-dependent green-Z dressing for two local
red-error pairs and three action choices per pair. This is a source-local
operator result, not the full periodic D4 state or an E2 observation law.

## Evidence

The [registered contract](../../manifests/j6k-full-local-star-action-algebra-2026-09-24.json),
[exhaustive runner](../../scripts/run_j6k_full_local_star_action_algebra.py),
and [machine-readable result](../../results/j6k-full-local-star-action-algebra-2026-09-24.json)
pin [Jing et al. Appendix A.1 Eq. (A2)-(A4)](https://arxiv.org/html/2507.23765)
and Iqbal et al. Fig. 2. The local inner ring has alternating green sites
`0,2,4` and red sites `1,3,5`; the outer X sites are `6..11`. The star is
`A=∏CZ_(i,i+1) ∏X_outer`, with ring index modulo six. The red and green
triangles are their respective three-site Z products.

Across all 4096 basis states, the star is a Hermitian involution, commutes
with both triangles locally, and the Eq. (A4) charge projector is idempotent
and vanishes outside the two-triangle vacuum sector; its exact rank is 512.
For red-X errors on sites `1,3`, the uncorrected star acquires green-Z
dressing on `0,4`; for errors on `1,5`, dressing lies on `2,4`.
An exactly matched red-X action restores the undressed star and red-triangle
sign in both geometries. Correcting only the first red site leaves a
one-red-error residual, flips the red-triangle sign, and gives dressing on
`2,4` or `0,4`, respectively. These six branch checks are exhaustive, not
Monte Carlo estimates.

## Status

The local operator-action matrix passes at its registered bound. Its ring
sites are not yet embedded into the source-normalized periodic `L=2`
honeycomb edge IDs; neighboring star constraints, a D4 ground state,
first-measurement state update and post-correction public charge probabilities
remain absent. In particular, no branch here generates an E2 public record,
and a locally restored triangle cannot prove global flux clearance. Next
derive the multi-star embedding and state/measurement update before adapting
the first-record-aware public interface. No histories, schedule arms or
threshold analysis were performed.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6j-cz-star-factor-representation-2026-09-24|CZ factor gate]] · [[records/index|Research-record index]]
