---
title: Source context and transfer boundary
status: current
updated: 2026-09-14
---

# Source context and transfer boundary

## Summary

The literature motivates sector partition functions and current/loop dualities.
The new Lab 007 formulation is derived from Lab 006's classical likelihood;
it does not substitute a quantum overlap model or an unbounded rotor channel.

## Evidence

### Targeted source audit

On 2026-09-14 the research workflow first inspected the local reference archive
and parent method, then searched for decoding-sector statistical mechanics,
Sala–Verresen loop models, and charge-informed U(1) decoding. Primary source
HTML/abstract pages were opened; no secondary-source claim is needed here.
This is a focused mapping audit, not an exhaustive literature review.

| Source | What it supplies | Transfer boundary and effect on this study |
| --- | --- | --- |
| [Dennis, Kitaev, Landahl, Preskill, Topological quantum memory](https://arxiv.org/abs/quant-ph/0110143) | Homology-based recovery and disordered statistical mechanics | Motivates summing all configurations in each sector, rather than identifying an optimal chain with the most probable sector |
| [Sala–Verresen, Stability and Loop Models from Decohering Non-Abelian Topological Order, Eqs. 1–12](https://arxiv.org/html/2409.12230v2) | Channel-specific quantum overlaps produce loop weights; purity and logical fidelity are distinct statistical objects | Requires deriving our conditional classical weights and retaining the observable. Their quantum dimension is not assigned to our loop fugacity |
| [Temkin et al., Charge-Informed Quantum Error Correction, model and statistical mapping](https://arxiv.org/html/2512.22119v1) | Gaussian integer edge errors on a torus lead to a constrained current/height description and a BKT analysis | Supports using current variables, but our errors have bounded support, open rough boundaries, and a binary rather than integer winding score; its fitted transition and jump cannot transfer |

The local [Sala PDF](../../../references/sala2025-decohering-nonabelian-topological-order/paper.pdf),
[Temkin PDF](../../../references/temkin2025-charge-informed-qec/paper.pdf), and
[Dennis PDF](../../../references/dennis2001-topological-quantum-memory/paper.pdf)
remain archived references. Online HTML was checked separately; the local
archives and their existing provenance were not overwritten.

### Model assumption that controls the result

The [parent method](../../../wiki/methods/sun-fusion-herald-belief-propagation.md)
assumes independently sampled local full-irrep outcomes conditional on the
shared physical edge states. Local multiplicity times irrep dimension, divided
by leaf-space dimension, is the likelihood. An actual entangled-pair quantum
preparation may correlate distant irrep outcomes differently. Deriving that
microscopic joint instrument would define a separate physical-model gate.
The present theory is exact for the stipulated classical law.

### What was derived here

The [sector posterior](partition-function.md) fixes the observation, boundary,
relative score and matched disorder measure. The [statistical model](statistical-model.md)
derives positive vertex and binary-spin forms, U(1) constrained currents/heights,
a character integral, and a restricted singlet loop gas. The latter has a
fugacity determined by orientation counting, with separate boundary factors.
These are model-specific derivations checked against exact finite sums.

The [decoder gap](decoder-gap.md) is an independent issue: even perfect marginals
can select the wrong logical sector after hardening. The existing BP-MWPM
curves are therefore not direct measurements of the partition-function optimum.

## Status

Source and assumption audit complete for the bounded formulation. No source
establishes universality for the typical-record SU(N) model defined here.

## Related pages

- [Inherited evidence](problem.md)
- [Partition function](partition-function.md)
- [Statistical-mechanics models](statistical-model.md)
- [Predictions and follow-on study](predictions.md)
