---
title: Periodic D4 operator algebra and compact vacuum orbit
status: current
updated: 2026-09-24
record: true
---

## Summary

On the fixed 108-qubit periodic kagome support, the source's CZ-aware stars
and color triangles pass exact symbolic algebra checks. A nonzero common
`+1` star/triangle state exists as a compact signed orbit of the all-zero
computational state. The orbit is not enumerated, and this result supplies no
sequential measurement or second-round public-record probabilities.

## Evidence

The [preregistered contract](../../manifests/j6m-periodic-operator-ground-orbit-2026-09-24.json),
[symbolic runner](../../scripts/run_j6m_periodic_operator_ground_orbit.py),
[machine-readable pair and relation audit](../../results/j6m-periodic-operator-ground-orbit-2026-09-24.json),
and [focused controls](../../scripts/test_j6m_periodic_operator_ground_orbit.py)
pin Jing Appendix A.1 Eqs. (A1)-(A4), Iqbal Fig. 2 and the prior
[periodic support map](../../results/j6l-periodic-kagome-incidence-2026-09-24.json).
Each of 36 stars is represented as a six-qubit outer-X flip and a quadratic
phase from six inner-ring CZ gates. Seventy-two color triangles are three-Z
operators. The 2,592 star/triangle pairs commute, and every star is a
Hermitian involution. Each of 522 nonadjacent star pairs commutes on every
basis state. All 108 adjacent pairs have a nonzero four-qubit commutator-Z
mask that equals the XOR/product of the two local triangles of their shared
physical-qubit color, directly matching the form of source Eq. (A3). The
commutators vanish on the all-triangle-`+1` vacuum sector; deleting CZ instead
makes every star pair commute globally, so that truncation loses the twisted
algebra. The affine GF(2) formula was independently checked on zero and every
single-qubit basis perturbation for each pair.

The 36 outer-X masks have rank 33, with three positive global relations
(one per star color). The triangle masks have rank 69. Starting from
`|0^108>`, every star action remains in the triangle vacuum, all star
actions commute there, and the three dependent relations return the starting
basis state with positive phase. Distinct independent-flip words have distinct
basis targets, so their signed orbit sum is nonzero and is a common `+1`
eigenstate of every star and triangle. This proves existence of one
anyon-free state under the source local terms, not its normalization,
preparation cost, logical-sector label or the full 22-fold ground-space
degeneracy.

## Status

The registered algebra/orbit gate passes with no stochastic histories,
schedule-arm evaluations or bootstrap replicates. The exact two-triangle
form of all 108 adjacent commutators is an additional source-image
cross-check beyond the preregistered row-span criterion. Next derive a
bounded sequential instrument on this same compact state: first measured
record, physical red-X error, correction action, normalized post-action
second record, and private/public separation. No public E2 channel or
five-round D4 schedule result is released by this algebra check.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6l-periodic-kagome-incidence-2026-09-24|Periodic incidence]] · [[records/index|Research-record index]]
