---
title: Same-state sequential local projector moments
status: current
updated: 2026-09-25
record: true
---

## Summary

The fixed periodic D4 vacuum orbit now supports an exact, ordered first
green-charge measurement, intervening red-X action, and conditional local
second blue-charge measurement. This is the first state-derived sequential
probability calculation in Lab 005, but it is not yet a full public E2 channel.

## Evidence

The [preregistered contract](../../manifests/j6n-sequential-local-projector-moments-2026-09-25.json),
[exact result](../../results/j6n-sequential-local-projector-moments-2026-09-25.json),
[runner](../../scripts/run_j6n_sequential_local_projector_moments.py), and
[tiny-vector controls](../../scripts/test_j6n_sequential_local_projector_moments.py)
pin Jing Appendix A.1/A.2/A.4, the J6L periodic map and the J6M compact
common-eigenstate orbit. The physical red-X error occupies red edge IDs
`[0,4]`. Green star 1 is measured first, before the action. Its two outcomes
are each `1/2`, as in the source's short-path limit.

An action on edge `[0]` leaves blue star 0 flux-free, and its second outcome
is `+` or `-` with probability `1/2` conditional on either actual first
outcome. A matched action on `[0,4]` makes both blue endpoints flux-free:
their joint outcomes are `++` or `--`, each with conditional probability
`1/2`; mismatched signs have zero weight. Deferring leaves post-flux E2
unavailable. Each first-conditioned row normalizes. These probabilities come
from ordered Born projectors on the *same* J6M state, with the red-X action
between measurements; a diagonal-Z character reduces the rank-33 orbit
average exactly without enumerating its amplitudes. Three independent
tiny-vector tests check the ordered-moment sign and Born expansion.

## Status

This validates only eligible **local** second-star marginals and the matched
two-blue joint law for one ideal geometry. It does not sample all 24 public
charge bits jointly, generate a full binary E2 record, implement a
first-record-aware adapter, or establish noisy five-round schedule risk.
Those remain the next bounded physical and interface gates. No stochastic
histories, schedule arms or bootstrap replicates were run.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6m-periodic-operator-ground-orbit-2026-09-24|Periodic operator-state gate]] · [[records/index|Research-record index]]
