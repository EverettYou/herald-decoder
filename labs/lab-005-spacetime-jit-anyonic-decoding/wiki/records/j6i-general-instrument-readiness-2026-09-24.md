---
title: General D4 instrument and public-adapter readiness
status: current
updated: 2026-09-24
record: true
---

## Summary

The exact short-path four-branch result still normalizes, but it is not a
general action-conditioned D4 instrument. Two independent prerequisites remain:
a lattice-wide operator-state update from the paper's kagome operators, and a
second-record adapter capable of receiving the first public observation.

## Evidence

The [preregistered matrix](../../manifests/j6i-general-instrument-readiness-2026-09-24.json),
[zero-sampling audit runner](../../scripts/audit_j6i_general_instrument_readiness.py),
and [machine-readable result](../../results/j6i-general-instrument-readiness-2026-09-24.json)
pin the archived paper, J6H result and both production interfaces. All four
hashes pass. The J6H four joint rows and two conditional row sums still equal
one. [Jing et al., Appendix A.1 Eq. (A2)-(A4)](https://arxiv.org/html/2507.23765)
gives graphical kagome star/triangle operators and a commuting-projector
formulation; A6/A13/A14 determine the illustrated local path, not an already
validated executable update for arbitrary physical/correction geometry.

The Lab 004 `sample_postflux_charge_outcomes` signature has only vertex count,
postflux relations and seed. Its Lab 004 and Lab 005 callers pass no first
charge record to that sampler. The Lab 005 call remains bound to the chosen
flux action and second exogenous key. This is an **interface coverage gap**:
it does not prove the independent uniform parity law wrong for any particular
geometry. Both scientific and adapter prerequisites need their own exact
limiting fixtures before promotion.

## Status

Readiness audit passed at its registered bound; zero histories, schedule arms
or bootstraps were run. The general physical instrument and five-round D4
schedule interpretation remain unvalidated. Next derive an operator-state
fixture on the pinned lattice, including an alternative action/geometry, then
pass its first-record-conditioned public kernel through a separate adapter
gate. Do not infer JIT superiority or a threshold from this audit.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6h-l2-conditional-stabilizer-instrument-2026-09-24|Local conditional instrument]] · [[records/index|Research-record index]]
