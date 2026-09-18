---
title: Statistical mechanics of representation-informed logical sectors
page_type: model
status: exact-classical-formulation
updated: 2026-09-14
source_refs:
  - labs/lab-007-decoding-statistical-mechanics/REPORT.md
  - labs/lab-007-decoding-statistical-mechanics/results/exact-model-checks-2026-09-14.json
  - labs/lab-007-decoding-statistical-mechanics/results/mapping-supplement-2026-09-14.json
idea_ids: []
topics: [Quantum Error Correction, Symmetry-Enriched Systems, Topological Phases]
---

# Statistical mechanics of representation-informed logical sectors

**Summary**: The classical full-irrep herald instrument defines a positive,
observation-conditioned vertex model whose logical-sector probabilities give
optimal decoding. SU(2) loses hidden orientation exactly; U(1) admits bounded
integer currents; SU(3) generally retains representation-dependent sources.

**Sources**: [Lab 007, exact formulation and finite checks](/lab?id=lab-007-decoding-statistical-mechanics).

**Last updated**: 2026-09-14

## Exact model and recoverability observable

The physical edge activity is Bernoulli. A hidden pair orientation, when present,
is shared by its endpoints. The observed record contains m and full irrep R at
measured vertices only; rough boundaries have neither measurement. Conditional
on edge states, the stipulated classical local instrument samples irrep R with
probability equal to fusion multiplicity times irrep dimension divided by the
leaf-space dimension. This independence assumption is not a derived quantum
measurement protocol.

For a syndrome-compatible reference correction c₀, the sum of joint weights
in relative binary sector h defines Z_h(s). Its sum over h is the physical
record probability. The normalized sector law is

\[
Q_h(s)=\frac{Z_h(s)}{\sum_g Z_g(s)}.
\]

For one logical bit the exact Bayes failure is min(Q₀,Q₁). The thermodynamic
recovery criterion is its physical-record average tending to zero, equivalently
the magnitude of the sector free-energy contrast diverging in probability.
This gives an intrinsic target independently of BP convergence or matching.
[Lab 007, sector proof](../../labs/lab-007-decoding-statistical-mechanics/wiki/partition-function.md).

## Which reductions preserve the inference problem?

| Model | Valid reduction | Boundary of the claim |
| --- | --- | --- |
| SU(2), full record | Binary activity/spin model; hidden and directed joint laws coincide | Fusion multiplicities and degree-dependent factors remain; no generic nearest-neighbor Ising identification |
| U(1), full record | Bounded signed current with fixed divergence; relative integer-cycle/height coordinates | Open rough boundaries and binary winding parity differ from periodic integer-rotor decoding |
| SU(3), full record | Positive shared-orientation fusion vertex model | A trivalent odd-syndrome singlet can have signed divergence +3 or −3; a source-free integer height model loses states |
| Trivalent singlet-only record | Loop gas with fugacity 1 for SU(2), 2 for hidden complex fundamentals | N enters the tension; nontrivial records and four-leg vertices obstruct importing this as the typical ensemble |

These are derived from the classical instrument rather than assigned from a
symmetry name. A character integral is also exact, but character insertions and
sector projectors need not be positive. Neither it nor the restricted loop gas
establishes a clean magnetic universality class.
[Lab 007, mappings and source boundary](../../labs/lab-007-decoding-statistical-mechanics/wiki/statistical-model.md).

## Exact marginals do not guarantee the optimal logical sector

Matching with posterior edge log-odds maximizes an independent-edge surrogate
under the syndrome constraint. It selects one chain, whereas sector inference
sums a correlated posterior over every chain in each class. In a finite SU(2)
rough-hexagon example, exact sector probabilities are (128/193,65/193), yet
exact-marginal matching selects the second sector; the backend reproduces this
strict counterexample. Exact tree BP can also retain a mathematical hardening
gap. Thus improving BP alone need not recover Bayes performance.
[Lab 007, exact decoder witnesses and backend limitations](../../labs/lab-007-decoding-statistical-mechanics/wiki/decoder-gap.md).

The finite evidence comprises 90 fixture/group/orientation/prior cases with
rational normalization and sector checks, plus independent integer-cycle and
backend checks. It supports identities and counterexamples, not large-lattice
loss magnitudes or a threshold. The next scientific step is controlled
contraction of typical-record sectors and matched comparison with practical
decoding. [Lab 007, predictions](../../labs/lab-007-decoding-statistical-mechanics/wiki/predictions.md).

## Related pages

- [[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[questions/program-level-scientific-roadmap|Program-level scientific roadmap]]
- [[thesis|Research program]]
