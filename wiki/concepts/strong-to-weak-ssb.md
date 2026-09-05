---
title: Strong-to-weak symmetry breaking and decodability
page_type: concept
status: framing
updated: 2026-08-26
source_refs:
  - references/lessa2024-swssb-mixed-states/paper.pdf
  - references/hauser2026-swssb-hydrodynamics/paper.pdf
  - references/moharramipour2024-symmetry-enforced-entanglement/paper.pdf
  - references/fan2023-mixed-state-topological-memory/paper.pdf
idea_ids: []
topics: [Topological Phases, Symmetry-Enriched Systems, Decoding Algorithms]
---

# Strong-to-weak symmetry breaking and decodability

**Summary**: Strong-to-weak symmetry breaking supplies information-transition context for the project's static herald-aware decoding question; it does not establish an \(SU(2)\) decoding threshold.

**Sources**: [Strong-to-Weak Spontaneous Symmetry Breaking in Mixed Quantum States](/reference?id=lessa2024-swssb-mixed-states); [Strong-to-Weak Symmetry Breaking in Open Quantum Systems](/reference?id=hauser2026-swssb-hydrodynamics); [Symmetry Enforced Entanglement in Maximally Mixed States](/reference?id=moharramipour2024-symmetry-enforced-entanglement); [Diagnostics of Mixed-State Topological Order and Breakdown of Quantum Memory](/reference?id=fan2023-mixed-state-topological-memory)

**Last updated**: 2026-08-26

**Evidence boundary**: The cited mixed-state and symmetry results motivate information-transition questions, but do not establish a static \(SU(2)\) herald measurement, its generative model, or a decoding threshold.

## Strong and weak symmetry

For a mixed state or open-system channel, a symmetry can be **strong**—resolved within each symmetry/charge sector—or merely **weak**, meaning it is preserved only after averaging over the ensemble. Strong-to-weak spontaneous symmetry breaking (SW-SSB) is therefore not ordinary symmetry breaking to no symmetry. It is diagnosed by nonlinear mixed-state quantities such as fidelity or Rényi correlators rather than ordinary one-copy correlators. [Lessa *et al.* (2024), abstract](../../references/lessa2024-swssb-mixed-states/paper.pdf)

## Connection to quantum-memory decoding

Lessa *et al.* identify the SW-SSB transition of a decohered Ising model as the ungauged counterpart of the toric-code decodability transition. [Lessa *et al.* (2024), abstract](../../references/lessa2024-swssb-mixed-states/paper.pdf) This provides the project’s symmetry-language motivation: above a transition, the available measurement record no longer retains enough information to reconstruct the relevant error history.

Hauser *et al.* make the information-theoretic picture more literal for \(U(1)\)-symmetric open dynamics. Their transition time marks the point beyond which discrete particle worldlines cannot be inferred; they also construct explicit decoding protocols. In two dimensions they report field-theory and numerical evidence for a finite-time BKT-like SW-SSB transition. [Hauser *et al.* (2026), abstract and introduction](../../references/hauser2026-swssb-hydrodynamics/paper.pdf)

These references provide symmetry and information-transition background, but the Herald Decoder deliberately poses a simpler operational task. It does not reconstruct worldlines or a fusion history. It compares two current-time inference problems: decoding from endpoint syndrome \(S\) alone, and decoding from the simultaneous snapshot \((S,H)\) that also contains local representation-resolved heralds.

## Why \(SU(2)\) is not just a larger \(U(1)\)

The key distinction is non-Abelian representation structure. In a strongly symmetric unital channel, the maximally mixed invariant sector is separable for Abelian symmetries but entangled for non-Abelian symmetries; for compact semisimple groups such as \(SU(2)\), the cited work finds logarithmically growing bipartite entanglement. [Moharramipour *et al.* (2024), abstract](../../references/moharramipour2024-symmetry-enforced-entanglement/paper.pdf)

This supports treating an \(SU(2)\) extension as physically distinct from the existing \(U(1)\) decoder theory. It does **not** prove the existence, universality class, or threshold benefit of an \(SU(2)\) SW-SSB transition in the proposed two-dimensional topological-memory model.

## Project questions

1. Can pair creation in a global \(SU(2)\) singlet and local fusion-channel readout be embedded in a consistent noisy surface/toric-code process?
2. Does the current herald snapshot modify the decoding threshold relative to endpoint-only decoding under the same error samples?
3. Which static observable should diagnose the transition: logical-decoding success, a fidelity/Rényi correlator, or a representation-resolved equal-time observable?

## Evidence boundary

The standard threshold framework remains necessary: a toric-code memory threshold can be characterized by mixed-state diagnostics and agrees with optimal decoding for the independent-error model studied by Fan *et al.* [Fan *et al.* (2023), abstract](../../references/fan2023-mixed-state-topological-memory/paper.pdf) The present project is a proposal to enrich that inference problem, not yet a result about a new phase transition.

## Related pages

- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
