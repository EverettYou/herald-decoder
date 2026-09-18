# Lab 007 — Statistical mechanics of representation-informed decoding

## Overview

### L007.1 Motivation

Explain the group and orientation contrasts seen in Lab 006 by formulating
the exact inference problem, then separating it from practical decoding.

### L007.2 Background

The decoder observes the interior binary syndrome m and full irrep R. A
logical sector groups error chains that the same correction can successfully
repair. Its partition function Z_h sums their posterior weights. “Hardening”
means replacing activity marginals by log-odds weights and choosing a
syndrome-compatible matching correction.

### L007.3 Question

What statistical-mechanics model governs these sector weights, what does
SU(2) self-conjugacy explain, and which information is lost in hardening?

### L007.4 Hypothesis

Representation constraints, orientation, geometry, and decoder approximation
can each matter. Conventional transitions, BKT-like behavior, smooth crossover,
and algorithmic effects remain competing explanations of the inherited curves.

## Evidence

### L007.5 Starting point

Lab 006 supplies the motivating orientation and lattice contrasts. Those
curves are inherited evidence, not new measurements in this lab. The
[inherited-evidence page](wiki/problem.md) fixes their scope.

### L007.9 Exact conditional model

The normalized likelihood gives a positive SU(N) vertex model with one shared
edge orientation and no measured rough-boundary factors. For visible record s,

\[
Q_h(s)=\frac{Z_h(s)}{\sum_g Z_g(s)}.
\]

Changing the reference correction only permutes h. Binary logical Bayes risk
is min(Q₀,Q₁); its physical average is the intrinsic decoding target. See the
[partition-function derivation](wiki/partition-function.md).

| Group or record | Exact reduction | Essential retained structure |
| --- | --- | --- |
| SU(2), full record | Binary activity / spin model | Degree-dependent fusion weights; hidden orientation cancels |
| U(1), full record | Bounded signed currents / relative integer heights | Exact charge constraint, rough-boundary paths, binary sector parity |
| SU(3), full record | Shared-orientation fusion vertex model | Full irrep weights; the same record can allow divergences +3 and −3 |
| Trivalent singlet-only record | Restricted loop gas | Fugacity 1 for SU(2), 2 for hidden SU(N≥3); N enters edge tension |

The [statistical-model page](wiki/statistical-model.md) gives the Hamiltonian,
spin and character representations, loop counting, and boundary terms.
The singlet-only reduction is not a typical-record transition theory.

### L007.10 Exact finite checks

Ninety fixture/group/orientation/prior cases pass rational normalization and
sector checks: 488,340 reference checks, 870 spin-sector contractions, and
16,764 U(1) current checks. A separate integer-cycle construction reconstructs
7,817 currents. Independent fusion recursion matches all 45 parent local
distributions tested through degree four.

SU(2)'s directed and hidden **joint activity/record laws** agree on all five
fixtures, as proved for arbitrary graphs. U(1)/SU(3) have explicit two-edge
sector counterexamples. The [conjugacy page](wiki/conjugacy.md) owns the theorem,
checks, and channel-comparison boundary.

### L007.11 Exact marginals can still select the wrong sector

On a rough SU(2) hexagon at p=1/3, one record has sector probabilities
(128/193,65/193). Exact-marginal matching uniquely chooses the second sector,
so its conditional failure is 128/193 versus the Bayes optimum 65/193.
PyMatching reproduces the witness. Tree examples also have exact BP marginals
and a strict mathematical hardening loss. The [decoder-gap page](wiki/decoder-gap.md)
reports the records, all 21 selected witnesses, and the separate parallel-edge
backend obstruction on the deliberately small star.

## Analysis

### L007.6 Implications

Self-conjugacy explains exact orientation invariance. It does not establish
an SU(2) threshold. Group-dependent vertex constraints and loss from choosing
a marginal-weighted chain are now distinct mechanisms. The next comparison
must measure sector Bayes risk alongside practical decoding on identical records;
see the [predictions and observable definitions](wiki/predictions.md).

### L007.7 Limitations

The model is the stipulated conditionally independent classical fusion
instrument, not a derived joint quantum measurement channel. Finite motifs
establish identities and counterexamples, not large-lattice effect sizes.
No threshold, stiffness, BKT transition, or universal jump was fitted.
The [source audit](wiki/source-context.md) explains why published quantum-loop
and integer-rotor transition results cannot be imported unchanged.

### L007.8 Next question

Can a controlled contraction of typical full-record sector weights separate
intrinsic recovery from BP and matching losses, and support a continuum theory?
The proposed next step is an exact narrow-strip contraction with the present
boundary and binary-score conventions. It is a follow-on design, not data
acquired in this formulation study.

Wiki-ingest handoff: promote the exact model and decoder distinction with their
finite-check provenance; retain transition and microscopic-channel claims as open.
