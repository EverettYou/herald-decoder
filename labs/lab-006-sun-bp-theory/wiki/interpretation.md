---
title: Group contrast and the statistical-mechanics question
status: current
updated: 2026-09-09
---

# Group contrast and the statistical-mechanics question

## Summary

Lab 006 establishes a practical-decoder contrast between the self-conjugate
SU(2) fundamental and the complex U(1)/SU(3) charge or fundamental. It does not
establish the thermodynamic existence, absence, or universality of a threshold.
The mechanism and statistical-mechanics questions pass to Lab 007.

## Evidence

The [directed curves](ler-curves.md) and [complete paired orientation study](hidden-orientation.md)
show different finite-size patterns across groups and geometries. The latter
owns the 12,000,000-pair audit, all statistical tests, and the pointwise counts.
SU(2) has crossing-like size reversals on both lattices in both channels;
U(1)/SU(3) show channel-dependent improvements, merging, or weak size reversal.
The orientation intervention significantly raises LER in 313/400 tested
U(1)/SU(3) cells, with no significant decrease; SU(2) is identical shotwise.

The algebraic distinction is \(F\cong\bar F\) for SU(2) (the fundamental is
pseudoreal, not a real two-dimensional representation), versus \(+1\not\cong-1\)
for the nonzero U(1) charge and \(\mathbf3\not\cong\bar{\mathbf3}\) for SU(3).
In this local classical fusion-instrument model, SU(2) orientation can be summed
out exactly without changing the activity posterior. The registered decoder
uses that quotient before damping, so its practical decisions also agree.
This inherited control does not prove that self-conjugacy explains the
finite-size transition pattern, nor that all microscopic SU(2) models lack
physical orientation. The [method definition](../../../wiki/methods/sun-fusion-herald-belief-propagation.md)
and [orientation validation](../results/a9-validation.json) specify the scope.

“Hardening” here means passing activity beliefs through posterior log-odds
weights into a syndrome-constrained MWPM correction. It is not independent
rounding of each edge. Even exact edge marginals need not determine the most
probable logical sector: correlations and sector multiplicities matter, in
addition to the loopy-BP approximation. This is the missing link between local
representation conjugacy and logical failure.

## Status

Current final interpretation. The square hidden-U(1) curve merging is a
researcher-proposed KT/BKT-like clue, not a measured BKT transition. The present
L=5,7,9,11 range, coarse p grid, finite BP schedule, and substantial numerical
nonconvergence cannot distinguish that hypothesis from ordinary finite-size
crossing drift or decoder artifacts. No threshold is fitted. A lack of crossing
on p≤0.50 is not evidence that a threshold does not exist.

Directed and hidden channels share activity and syndrome but intentionally
change the irrep record law; this is not a comparison of nested observations on
one unchanged physical channel. Square and honeycomb have different coordination,
edge counts, and boundaries at the same nominal L. The 40 inherited corrected
directed cells retain their documented missing historical source hashes;
current paired replay checks do not retroactively supply them. See the current
[rate boundary](ler-curves.md) and [paired-study boundary](hidden-orientation.md).

## Related pages

- [Method and implementation](overview.md)
- [Directed rate evidence](ler-curves.md)
- [Paired orientation evidence](hidden-orientation.md)
- [Lab 007 theory plan](../../lab-007-decoding-statistical-mechanics/PLAN.md)
