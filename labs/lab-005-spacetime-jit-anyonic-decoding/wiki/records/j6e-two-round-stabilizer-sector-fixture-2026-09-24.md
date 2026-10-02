---
title: Two-round D4 stabilizer-sector limiting fixture
status: current
updated: 2026-09-24
record: true
---

## Summary

**Source-consistent in this narrow L=2 case.** A later [source-image
disambiguation](j6g-source-stabilizer-disambiguation-2026-09-24.md) retracts
J6F's false objection: Appendix A.4 Eq. (A13) contains both a bare green-star
`+1` stabilizer and a distinct `p2`-weighted *dressed* green stabilizer.
The blue measurement replaces the latter; Eq. (A14) retains the bare green
vacuum outcome. This restores the narrow J6E postflux support, not a general
physical channel or five-round performance result.

An exact, zero-sampling fixture on the paper-normalized (L=2) D4 honeycomb
passes narrow physical limits. A prescribed matching correction clears
the flux boundary and makes the full post-flux charge record available;
deferral leaves the flux and has no such E2 record. The correction is an
oracle-matched intervention for a limiting case, not a causal decoder output.

## Evidence

The [registered contract](../../manifests/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json),
[exact runner](../../scripts/run_j6e_two_round_stabilizer_fixture.py), and
[machine result](../../results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json)
pin J6D and the four Lab 004 geometry/observation/post-flux source files.
All hashes and the accepted upstream status matched. The fixed lattice has
24 vertices and 36 red-qubit edges. The selected two-edge path is `[0,4]`
through green vertex `1`, with blue endpoints `0,2`; it is homologically
trivial. Zero, one-edge and two-edge cases each include defer and matching
red-X intervention branches.

The two-edge first full-binary observation has two supported charge records,
each with probability (1/2), at the path's degree-two green center; its two
blue endpoints carry flux. Without correction that flux persists and a
post-flux E2 record is **not** fabricated. Matching correction clears it.
The physical-plus-correction union then yields a blue parity component
`[0,2]` and a green singleton `[1]`. Exhaustive charge support consists of
blue outcomes `00` and `11` with green `0`; the full-binary public
charge/vacuum arrays contain no private union or relation fields. A one-edge
union has only two even singletons and one all-vacuum E2 record. The no-error
control has no action-conditioned E2.

For the two possible post-flux records, orthogonal ideal measurement
projectors give the exact no-new-fault repeat kernel `[[1,0],[0,1]]`.
This is repeatability *after* the first post-flux measurement, not an
assumption that its outcome is independent of the earlier pre-correction
herald. The first-to-post-flux joint distribution and the evolution under
further faults remain unresolved. [Jing et al., Appendix A.3–A.4](https://arxiv.org/html/2507.23765)
supports the flux and parity limits; the fixture does not derive a complete
D4 density operator or numerical three-label cross-round kernel.

## Status

The registered support gate is consistent with the source after J6G's
correction of the J6F misread. No stochastic
history, schedule evaluation, bootstrap, LER or threshold was produced.
The next prerequisite is an explicit first-measurement/correction/post-flux
conditional instrument (density or stabilizer-state update) on this same
geometry, then a check of whether and how it reduces to a tractable
cross-round hidden-state kernel. The five-round caller remains unchanged.

## Related pages

[[schedule-state|Schedule state]] · [[records/index|Research-record index]]
