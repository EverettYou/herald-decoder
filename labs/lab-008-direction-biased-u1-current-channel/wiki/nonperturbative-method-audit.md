---
title: Non-perturbative methods for the unresolved LER curve
status: current
updated: 2026-09-19
---

# Non-perturbative methods for the unresolved LER curve

## Summary

The controlled L5 square prediction reaches every registered bias through
`p=.05` and narrows `p=.08` only for `q=.97,1`. This audit asks whether an
established non-perturbative method directly closes the fair/intermediate
analytic gap without fitting the exact-posterior Monte Carlo anchors.

The target is not a scalar partition function. With `A0(Q)=Z0(Q)+Z1(Q)` and
`A1(Q)=Z0(Q)-Z1(Q)`, optimal logical error is

\[
\mathcal R=\frac12\left(1-\sum_Q|A_1(Q)|\right).
\]

Thus a method must control an `l1` norm over every public charge record after
the signed logical twist has been pushed forward. Accurate evaluation of one
untwisted or twisted scalar partition function does not imply such a bound.

## Evidence

| Method family | Established result | First failed interface condition here | Decision |
| --- | --- | --- | --- |
| Polymer/contour expansion | [Helmuth, Perkins and Regts](https://arxiv.org/abs/1806.11548) give algorithmic Pirogov--Sinai counting from a convergent contour representation in low-temperature regimes. | No convergent contour gas has been derived for the charge-record `l1` functional; applying the expansion separately to scalar sectors leaves the recordwise absolute value uncontrolled. | No plug-in theorem. A new target-specific polymer theorem would be required. |
| Correlation decay and zero-free counting | [Liu, Sinclair and Srivastava](https://arxiv.org/abs/1906.01228) connect strong spatial mixing, zero-free regions and scalar approximate counting for specified spin systems. | The charge constraints are hard incidence delta factors, and the desired output-distance functional is not a scalar `Z`. Neither strong spatial mixing nor zero-freeness for one sector supplies `sum_Q abs(A1(Q))`. | Reject as a direct certificate. |
| Certified positive marginal polytopes | [Li and Yang](https://arxiv.org/abs/2609.12352) construct rational marginal polytopes for positive interactions under a Birkhoff-contraction condition. | The current factorization contains zeros from exact charge conservation, so positivity and finite projective diameter fail before the contraction test; even a blocked scalar model would still not certify the emitted-record `l1` norm. | Interesting implementation idea, but not an applicable theorem. |
| Zero-free interpolation | [Barvinok and Soberón](https://arxiv.org/abs/1406.1771) approximate graph-homomorphism partition functions in a zero-free domain. | The method approximates analytic scalar partition functions. The absolute value and exponentially many charge coefficients are outside that analytic scalar target. | Reject as a direct route. |
| MPS/tensor contraction | [Bravyi, Suchara and Vargo](https://arxiv.org/abs/1405.4883) approximate surface-code coset probabilities with bond-dimension-controlled MPS contraction. | Standard truncation supplies a numerical approximation, not a certified global error on the sum of recordwise sector minima. Repeating it for sampled records would be another oracle estimate, not an analytic curve. | Retain only as a future heuristic benchmark, not the controlled deliverable. |
| Generic output total variation | [Kiefer](https://arxiv.org/abs/1804.06170) proves additive approximation of total variation for finite-word labelled Markov chains is `#P`-hard, even for acyclic models. | This is not a hardness proof for the present lattice instance, but it shows why an emitted-record `l1` norm can remain hard after each underlying scalar model is tractable. | Treat generic transfer/HMM reduction as insufficient without extra structure. |

The source search covered polymer/contour algorithms, correlation decay,
zero-free interpolation, positive multi-spin marginal bounds, tensor-network
maximum-likelihood decoding and output-distribution total variation. The
reviewed papers establish their own model-specific results; the failed
interface conditions above are project-specific deductions.

## Remaining target-preserving route

The existing physical even-moment hierarchy preserves the estimand:

\[
M_{2k}=\mathbb E[m(Q)^{2k}],\qquad
\mathcal R=\frac12\sum_{k\ge1}a_k
\mathbb E[(1-m(Q)^2)^k].
\]

Its partial sums and analytic remainder give certified LER intervals. Unlike
the scalar methods above, it retains the record distribution and the absolute
logical ambiguity. Its obstruction is also explicit: the physical moments
require the `R -> 1` record weighting; the clean integer-replica `R=2` model
uses `A0(Q)^2` and is not interchangeable.

The smallest discriminating follow-up used exact L3 sector tables and seven
already stored L5 posterior cohorts at `N in {1,2,4,8,16,32}`. It collected no
new records. The preregistered primary gate required every L5 cell at
`p in {.10,.30}`, `q in {.5,.75}` to have N=32 point width at most `.010` and
bootstrap-95 upper width at most `.0125`.

The p=.10 cells pass: fair width `.003516` (upper `.005392`) and q=.75 width
`.001314` (upper `.002449`). Both p=.30 cells fail: fair width `.017491`
(upper `.019032`) and q=.75 width `.013702` (upper `.015213`). Exact L3 also
shows slow convergence in the ambiguous regime, with N=32 width `.034377` at
p=.30,q=.5. Near-directed stored L5 cells are narrow, but secondary cells
cannot rescue the failed primary gate. The registered stop rule therefore
closes low-order moment compression and forbids a physical replica-transfer
implementation for this statistic. These empirical interval widths do not
constitute an analytic curve or a threshold estimate.

## Status

No reviewed theorem directly extends the fair/intermediate controlled curve
beyond `p=.05`. Polymer, spatial-mixing, zero-free and MPS methods all lose the
public-record `l1` target at their first interface; the sole target-preserving
moment candidate fails its bounded feasibility gate. The shaded `p>=.08`
region therefore remains unresolved. No threshold or phase conclusion changes,
and another compression refinement is not justified by this audit.

## Related pages

- [Partition-function prediction and evidence boundary](partition-function-ler.md)
- [Replica moment bounds](replica-boundary-ratios.md)
- [Complex weights and conditional continuum route](complex-weights-and-cft.md)
- [Machine-readable moment feasibility result](../results/physical-moment-feasibility-2026-09-19.json)
