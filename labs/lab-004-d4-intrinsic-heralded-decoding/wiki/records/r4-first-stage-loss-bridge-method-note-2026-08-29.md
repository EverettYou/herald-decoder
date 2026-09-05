---
title: 'R4.4 matched first-stage loss bridge — registered method'
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

# R4.4 matched first-stage loss bridge — registered method

## Why a bridge is required

R4.2–R4.3 group compatible physical errors by the homology of their XOR
difference from a reference error. The published practical pipeline uses a
different object at its first logical gate: Appendix A classifies the Boolean
union of the physical and correction strings because both rounds contribute to
the post-flux stabilizer history. Equality of those two decision problems has
not been proved and will not be assumed.

The current full practical pipeline also receives a second, adaptive post-flux
charge measurement whose distribution depends on the first correction. That
measurement is absent from the R4.2 O2 record. Comparing the complete two-stage
pipeline directly with the R4 O2 posterior would therefore give the practical
decoder extra information. R4.4 instead makes a rigorously matched first-stage
comparison and defers the full two-stage comparison until its adaptive
observation channel has an exact posterior model.

## Exact matched decision problem

Use the complete primitive nonwinding support and unchanged
`p={0.1,0.3,0.5,0.6}` priors. For each flux syndrome, exhaust the affine space
of every binary correction with that boundary; the connected 12-edge fixture
should have 32 such actions. For candidate physical error `E` and correction
`C`, define loss as one exactly when any component of `E ∪ C` has nontrivial
winding under the validated Appendix-A classifier.

At O0, integrate over the flux-only posterior, minimize expected loss over the
complete correction set, and compare with unit-weight syndrome-only MWPM. At
O2, integrate over the `(flux, charge)` posterior, minimize the same loss, and
compare with the published heralded weights `w_e=1-n_e K`. Physical truth is
used only to sum and score candidate losses; neither decoder receives it.

This gives three distinct quantities:

1. exact information gain `R*_O0-R*_O2` under one common loss;
2. O0 algorithmic excess risk above `R*_O0`; and
3. O2 algorithmic excess risk above `R*_O2`.

## XOR-sector sufficiency diagnostic

For every observation and every correction action, test whether all candidate
errors within one R4 XOR-relative sector have the same Boolean-union loss. If
so, the sector is sufficient for that decision problem. If not, the direct
action-loss posterior is the valid exact comparator and the R4 sector posterior
remains an intrinsic information diagnostic rather than a practical-stage
Bayes oracle. Aggregate direct and sector risks are compared but equality is
not an acceptance requirement.

## Validation and stopping

Correction sets must be complete, unique, and syndrome faithful. Both public
corrections must belong to those sets and depend only on their declared O0 or
O2 record. O0 evidence must equal the O2 charge marginal; all posteriors must
normalize; and exact risk must not exceed the matched production risk.

Stop after the complete deterministic first-stage matrix, tests, JSON audit,
Markdown report, and Lab update. Do not sample the adaptive second charge
round, introduce terminal truth as input, enlarge the lattice, estimate LER, or
claim a threshold or complete practical-decoder performance result.

