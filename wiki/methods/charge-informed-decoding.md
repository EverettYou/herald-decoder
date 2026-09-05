---
title: Charge-informed decoding
page_type: method
status: framing
updated: 2026-08-26
source_refs:
  - references/temkin2025-charge-informed-qec/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Symmetry-Enriched Systems, Decoding Algorithms]
---

# Charge-informed decoding

**Summary**: The established \(U(1)\) charge-informed decoder is the closest precedent for testing whether a current herald field can improve decoding; it does not itself establish the proposed \(SU(2)\) model.

**Sources**: [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec)

**Last updated**: 2026-08-26

**Scope**: This page concerns the \(U(1)\) reference model. General side-information and fast-decoding comparisons are compiled separately so that they are not mistaken for a derivation of the proposed \(SU(2)\) herald mechanism.

## Why it matters here

The standard toric/surface-code decoder receives the current endpoint syndrome: it sees the locations of \(\mathbb Z_2\) anyons but not the current error configuration connecting them. Charge-informed decoding asks what changes when additional, locally measurable symmetry data are available in the same snapshot. This is the closest established decoder setting to the Herald Decoder project.

## Established result: the \(U(1)\) model

Temkin *et al.* study a \(U(1)\) symmetry-enriched topological quantum memory with charge-conserving phenomenological noise and assume the local charge of every anyon is measurable. They formulate optimal decoding as a disordered two-dimensional integer-loop model on the Nishimori line. The reported decoding transition has BKT universality, while the zero-temperature limit is a minimum-cost-flow decoder—their \(U(1)\) analogue of MWPM. Both their optimal and minimum-cost-flow decoders outperform a charge-agnostic optimal decoder in that model. [Temkin *et al.* (2025), abstract](../../references/temkin2025-charge-informed-qec/paper.pdf)

This is evidence that symmetry-resolved side information can change the inference problem and improve decoding. It does **not** by itself establish an \(SU(2)\) herald decoder or its threshold.

## Relation to the proposed \(SU(2)\) herald model

The project proposal differs from the \(U(1)\) model in the location and form of the auxiliary information:

| \(U(1)\) charge-informed model | Proposed \(SU(2)\) herald model |
| --- | --- |
| Local charge is measured on every anyon. | Each endpoint carries spin \(1/2\); a local fusion event may reveal its total representation. |
| The side information labels the current charge configuration. | A spin-1 triplet outcome is a current local marker correlated with string occupancy. |
| The decoder is formulated using integer charge loops. | The decoder conditions a correction on the simultaneous endpoint and herald fields. |

The second column is a **project hypothesis**, not a consequence already proved in the reference. In particular, the \(1/4\) singlet and \(3/4\) triplet rule requires an operational model for the fusion measurement and state preparation.

## Decoder-design consequences

The first lab should define a static joint generative model for current error configuration \(E\), endpoint syndrome \(S\), and herald snapshot \(H\). A decoder may compare candidate current error configurations or correction classes using \(P(E\mid S,H)\), not merely a geometrical path length. Here \(E\) has no time labels: it is the current hidden configuration, not a fusion history. Essential ablations are:

1. endpoint-only decoding, the standard MWPM-style baseline;
2. endpoint plus perfect herald record;
3. endpoint plus noisy or incomplete herald record;
4. a control in which marks have the same density but no correlation with the current error configuration.

The control is important: a threshold improvement would be meaningful only if it arises from information carried by the herald record rather than from a changed physical noise distribution.

## Open questions

- What local operation produces a representation-resolved herald in the current extraction round without exposing or reconstructing past history?
- Does the \(SU(2)\) model admit an efficient analogue of the minimum-cost-flow construction, or require a different graphical/probabilistic decoder?
- Which threshold comparison is fair: matched physical noise, matched endpoint density, or matched total measurement budget?

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
