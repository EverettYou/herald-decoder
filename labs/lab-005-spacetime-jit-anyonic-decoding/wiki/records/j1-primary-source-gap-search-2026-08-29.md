---
title: 'J1 primary-source gap search'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# J1 primary-source gap search

Date: 2026-08-29

## Question

Can the primary-source chain close either physical gap localized by R0/E0: an
exact D(S3) circuit-fault event catalogue, or an operational repeated D4
anyon-measurement instrument?

## R branch: the microscopic circuit gap remains open

Lyons and Brown define repeated stabilizer readings, detector differences,
boundary detectors, and a coarse-grained local-circuit-noise model. Their text
explicitly *supposes* that each anyon-species stabilizer can be measured once
per unit time using additional degrees of freedom and noisy circuit elements.
It does not instantiate the ancilla circuit or enumerate primitive faults.

Their cited microscopic source, Verresen, Tantivasadakarn, and Vishwanath
(arXiv:2112.03061), does supply the finite-depth preparation/gauging sequence,
the D(S3) commuting projectors, and a Rydberg realization. It does not supply a
repeated D(S3) syndrome-extraction circuit, ancilla schedule, or the requested
primitive-fault-to-detector table. The citation chain therefore does not close
the three R0 gaps. Exact circuit-level R reproduction remains paused rather
than being completed with a guessed extraction circuit.

## E branch: a projector-level instrument basis is present

Jing *et al.* (arXiv:2507.23765v2), Supplemental Appendix D, goes beyond the
perfect-measurement benchmark. It gives a repeated-syndrome example with a
false-negative non-Abelian-flux readout, a time-like measurement-error weight,
and a time-ordered product of commuting syndrome projectors and physical-error
operators. This supplies an explicit projector-level state-update basis for a
phenomenological repeated-measurement model.

Jing *et al.* (arXiv:2608.18512v1), Section VII and Appendix B, independently
specify the complete local D(G) anyon projectors, spacetime physical and
measurement-error strings, and species/site/time measurement-error variables.
These sources therefore close the *projector-level* E0 state-update gap
sufficiently to register a bounded E1 model.

They do **not** provide an ancilla-resolved hardware extraction circuit or a
circuit-fault propagation table. E1 must consequently be named and interpreted
as a source-bounded phenomenological projector instrument, not as circuit-level
fault tolerance.

## Disposition

- R remains locally paused at a genuine circuit-model/external-source choice.
  No human ranking is needed while the independent D4-first E branch can move.
- E may advance to research-workflow registration of the smallest repeated-D4
  projector-instrument matrix, with the quasi-stabilizer false-negative example
  and the commuting-projector reporting channel kept distinct.
- Performance sampling remains blocked until that E1 contract passes its
  normalization, causal state-update, readout-only fault, physical-only fault,
  action dependence, truth-exclusion, and deterministic-replay gates.

No stochastic data, logical-error rate, threshold, schedule advantage, or
fault-tolerance result was produced by this source search.


