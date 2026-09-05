---
title: Herald Decoder research program
page_type: thesis
status: framing
updated: 2026-09-04
source_refs:
  - references/temkin2025-charge-informed-qec/paper.pdf
  - references/lessa2024-swssb-mixed-states/paper.pdf
  - references/pattison2021-soft-information-qec/paper.pdf
  - references/dennis2001-topological-quantum-memory/paper.pdf
  - labs/lab-006-sun-bp-theory/REPORT.md
idea_ids: []
---

# Herald Decoder research program

**Summary**: The project studies how symmetry enrichment of topological excitations changes quantum-code decodability and whether the resulting measurable structure can support more capable practical decoders; this is a research program, not an established threshold claim.

**Sources**: [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec); [Strong-to-Weak Spontaneous Symmetry Breaking in Mixed Quantum States](/reference?id=lessa2024-swssb-mixed-states); [Improved Quantum Error Correction Using Soft Information](/reference?id=pattison2021-soft-information-qec); [Topological Quantum Memory](/reference?id=dennis2001-topological-quantum-memory); [Lab 006: SU(N) full-irrep belief propagation](/lab?id=lab-006-sun-bp-theory)

**Last updated**: 2026-09-04

## Central question

How does enriching topological excitations with global-symmetry quantum numbers change the decodability transition of quantum error-correcting codes, and can that structure be converted into more capable practical decoders?

## Current operational research question

The current representation-resolved model asks whether a decoder can use the joint record \((m,R)\)—the
\(\mathbb Z_2\) topological boundary and a complete local SU(N) irrep—to improve inference without reconstructing
a fusion history. This is a bounded experimental question within the broader research program, not the project’s
final high-level thesis.

## Proposed mechanism

We begin with one \(\mathbb Z_2\) anyon species and let every anyon additionally transform as an \(SU(2)\) spin-\(1/2\). The relevant local representation decomposition is

\[
\tfrac12\otimes\tfrac12 = 0\oplus1.
\]

Under the simplest unbiased-state assumption, a representation-resolved local readout is singlet with probability
\(1/4\) and triplet with probability \(3/4\). The complete irrep \(R\), not an additional binary variable, is the
symmetry-resolved **heralding signal**. It need not be an energetic quasiparticle; operationally, it is current
classical side information.

[[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]] records the finite-dimensional representation convention. [[references/lieart|LieART]] provides the associated paper and toolkit.

Here **heralding** means the information contributed by the measured representation label \(R\). It is not the
“heralded erasure” common in loss-tolerant QEC: it does not reveal a particular erased edge.

One syndrome-extraction round produces the snapshot \((m,R)\). The decoder maps this joint gauge/symmetry record
directly to a correction or logical equivalence class. There is no lower-resolution surrogate for \(R\) in the
current model.

The decoder does **not** identify which anyons were originally paired, reconstruct a fusion tree, infer a worldline, or use a time-ordered fusion record. A microscopic history may explain why the local measurement exists, but it is neither an input nor a target of the decoding algorithm.

## Working hypothesis

A full-irrep decoder may outperform an endpoint-only decoder because \(R\) can reduce the set of error
configurations or correction classes compatible with \(m\). The immediate test is the paired contrast
\(P(e\mid m,R)-P(e\mid m)\); any stronger finite-size or threshold claim requires separately registered evidence.

The existing \(U(1)\) charge-informed decoder provides a direct precedent: locally measured anyon charge can substantially improve decoding. The \(SU(2)\) problem is nevertheless different because the useful information may live in non-Abelian fusion channels and may retain intrinsically quantum correlations.

Erasure locations, soft measurement outcomes, and local \(U(1)\) charge are distinct examples of currently available side information. They support the methodological requirement to compare matched observation models, not the conclusion that an \(SU(2)\) herald will improve a threshold. [Delfosse and Zémor (2020), abstract](../references/delfosse2020-erasure-ml-decoding/paper.pdf) [Pattison *et al.* (2021), abstract](../references/pattison2021-soft-information-qec/paper.pdf) [Temkin *et al.* (2025), abstract](../references/temkin2025-charge-informed-qec/paper.pdf)

## Relation to strong-to-weak symmetry breaking

Some related work formulates decodability through the inferability of particle worldlines or error histories. That literature supplies useful symmetry and information-transition context, but it is not the algorithmic task proposed here. Our operational question is static: does the current representation-resolved record \((m,R)\) change inference relative to the current boundary record \(m\) alone?

It is currently an open question whether the relevant two-dimensional \(SU(2)\) system has a finite strong-to-weak transition of the desired kind. Mermin--Wagner intuition motivates caution, but cannot simply be imported without specifying the mixed-state order parameter and effective model.

## Current evidence boundary

Lab 006 now supplies a normalized static generative model and a compiled
belief-matching implementation for the unique record \((m,R)\). A paired
two-dimensional diagnostic on the canonical square and honeycomb lattices
found that the present synchronous damped BP schedule is not uniformly
convergent: full-record inference converged in 106/128 frozen observations,
with the clearest failures on \(L=7\) honeycomb SU(2). This narrows the next
algorithmic question to convergence control on genuinely two-dimensional
loopy graphs.

The result does not establish a decoding threshold, logical-error improvement,
or a physical measurement protocol for the complete irrep. Those require
separately registered evidence. In particular, four samples per scan cell
cannot support a finite-size or group-comparison conclusion.

## Program-level next step

The finite-window phase-map work now serves as a diagnostic of the current
phenomenological model rather than the program's central objective. The
recommended next flagship question is whether partial symmetry/fusion-channel
readout defines a distinct recoverability transition and what minimal record is
sufficient to reach it. The staged theory, optimal-inference, spacetime, and
experimental plan is recorded in
[[questions/program-level-scientific-roadmap|Program-level scientific roadmap after the finite-window phase map]].

## Connected knowledge

- [Strong-to-weak symmetry breaking and decodability](concepts/strong-to-weak-ssb.md)
- [Charge-informed decoding](methods/charge-informed-decoding.md)
- [Error-correction decoding](concepts/error-correction-decoding.md)
- [Surface-code decoding baselines](methods/surface-code-decoding-baselines.md)
- [Side-information-aware decoding](methods/side-information-aware-decoding.md)
- [Scalable decoding methods](methods/scalable-decoding.md)
- [Symmetry-enriched topological order](concepts/symmetry-enriched-topological-order.md)
- [Lie groups, Lie algebras, and representations](concepts/lie-algebra-representations.md)
- [SU(N) full-irrep belief propagation](methods/sun-fusion-herald-belief-propagation.md)
- [LieART](references/lieart.md)
- [Quantum spin liquids](concepts/quantum-spin-liquids.md)
- [Program-level scientific roadmap after the finite-window phase map](questions/program-level-scientific-roadmap.md)

## Related pages

- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]]
- [[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]]
- [[references/lieart|LieART]]
- [[concepts/quantum-spin-liquids|Quantum spin liquids]]
