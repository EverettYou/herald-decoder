---
title: Final theory boundary for the direction-biased U(1) channel
status: current
updated: 2026-09-19
---

# Final theory boundary for the direction-biased U(1) channel

## Summary

**Reopened on 2026-09-19:** the researcher requested continued calculation,
and a new [connected-current theorem](connected-current-defects.md) supplies
the previously missing physical-LER interface. It improves biased square
bounds, gives an exact small-square curve, and proves all-p correctability
for fully directional honeycomb noise. The table below records the earlier
closure boundary; it does not supersede these new results.

Lab 008 explains the finite-patch logical error rate (LER) through exact
logical-sector partition sums and establishes several rigorous limits. It does
not derive the fair/intermediate moderate-noise curve or a thermodynamic phase
transition. Every registered controlled extension has either reached only the
low-activity or near-directed regime, failed its acceptance gate, or lost the
public-record `l1` target. This page fixes the final claim boundary and prevents
negative results from being silently recycled as positive evidence.

## Evidence

| Epistemic class | What is established | What it does not establish | Current owner |
| --- | --- | --- | --- |
| Exact finite-graph identity | The observed-charge sector sums obey `A0=Z0+Z1`, `A1=Z0-Z1`, and optimal LER is `(1-sum_Q abs(A1(Q)))/2`. Physical `M2` bounds LER within a factor of two; the complete physical even-moment hierarchy reconstructs LER with a certified remainder. | Efficient evaluation at large two-dimensional size, a phase transition, or a critical value. | [Replica boundary ratios](replica-boundary-ratios.md) |
| Rigorous limiting result | The one-dimensional path has an exact Chernoff rate, and revealing all vertical currents gives a lower bound on the square. Fixed-size dilute powers and leading coefficients are derived on the actual square. | The moderate-`p` square curve or interchange of fixed-size, `p -> 0`, `q -> 1`, replica and thermodynamic limits. | [Partition-function prediction](partition-function-ler.md) |
| Finite-patch empirical result | Matched exact-posterior experiments separate intrinsic sector ambiguity from BP/MWPM excess and show a large fair-versus-directed contrast at registered sizes. | An asymptotic threshold, universality class or decoder-independent phase diagram. | [Mechanism evidence](mechanism-results.md) |
| Controlled finite certificate | Positive-current activity bounds control every registered bias through `p=.05`; adaptive contraction narrows `p=.08` only for `q=.97,1`. | Fair/intermediate `p>=.08`, including the moderate-noise curve. | [Prediction evidence boundary](partition-function-ler.md) |
| Conditional continuum calculation | A compact Gaussian replica annulus, root-lattice twists and boundary-defect spectrum can be written under explicit stiffness, vortex and continuation assumptions. | Quantitative calibration of the physical square: bare curvature is not a renormalized stiffness, vortex fugacities and rough-boundary matching are uncontrolled, and integer replicas do not fix `R -> 1`. | [Complex weights and CFT](complex-weights-and-cft.md) |
| Closed computational routes | Positive two-current transfer, sector Hellinger, exact charge-prefix transfer, bounded decision diagrams, priority changes and posterior-bucket merging do not close the fair/intermediate interval within their registered budgets. | Their failure is not a proof that no target-specific representation can exist. | [Prediction evidence boundary](partition-function-ler.md) |
| Closed theorem/compression routes | Reviewed polymer, spatial-mixing, zero-free, positive-marginal and MPS results do not control the emitted-record `l1` target. The sole target-preserving low-order moment candidate fails its N=32 gate at `p=.30,q=.5,.75`. | A general hardness theorem for this lattice instance or the impossibility of a new target-specific theorem. | [Non-perturbative method audit](nonperturbative-method-audit.md) |

The remaining target is therefore precise: control
`sum_Q abs(A1(Q))` for fair/intermediate bias at moderate `p` in the
two-dimensional thermodynamic limit, while preserving the physical record law,
rough boundaries and binary logical score. A scalar partition function, clean
integer-replica model, fitted oracle curve or finite-size crossing is not a
substitute for that target.

## Status

The earlier finite-mechanism and method-audit stages are complete. The lab
is active again on the linked connected-defect calculation. The square
fair/intermediate moderate-noise curve, physical replica continuum limit
and CFT remain unresolved. The earlier Gaussian and compression rejections
are retained; the new theorem is not a reopening of those implementations.

## Related pages

- [Replica boundary ratios and logical error](replica-boundary-ratios.md)
- [From the auxiliary partition function to the LER curve](partition-function-ler.md)
- [Non-perturbative methods for the unresolved LER curve](nonperturbative-method-audit.md)
- [Intrinsic risk, decoder loss and bias controls](mechanism-results.md)
