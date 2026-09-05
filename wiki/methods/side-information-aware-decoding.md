---
title: Side-information-aware decoding
page_type: method
status: established-background
updated: 2026-09-04
source_refs:
  - references/delfosse2020-erasure-ml-decoding/paper.pdf
  - references/pattison2021-soft-information-qec/paper.pdf
  - references/temkin2025-charge-informed-qec/paper.pdf
  - references/jing2025-intrinsic-heralding/paper.pdf
  - references/lyons2026-anyonic-fault-tolerance/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Symmetry-Enriched Systems, Decoding Algorithms]
---

# Side-information-aware decoding

**Summary**: Additional simultaneously available observations can sharpen decoding posteriors, but only relative to a fully specified physical observation model and matched baseline. The project's fusion-remnant herald is not an erasure or loss flag.

**Sources**: [Linear-Time Maximum Likelihood Decoding of Surface Codes over the Quantum Erasure Channel](/reference?id=delfosse2020-erasure-ml-decoding); [Improved Quantum Error Correction Using Soft Information](/reference?id=pattison2021-soft-information-qec); [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec); [Lab 001 model](/lab?id=lab-001-string-herald-visualization)

**Last updated**: 2026-09-04

## Current synthesis

For the quantum erasure channel, the known erasure pattern is side information: conditional on that pattern and syndrome, all compatible error cosets are equiprobable in the stated model. Delfosse and Zémor give a linear-time surface-code procedure that returns a maximum-likelihood coset. [Delfosse and Zémor (2020), abstract and “Maximum likelihood decoding for qubit loss”](../../references/delfosse2020-erasure-ml-decoding/paper.pdf#Maximum-likelihood-decoding-for-qubit-loss)

Pattison *et al.* model richer measurement outcomes rather than discarding them to binary values. They modify MWPM and Union-Find to use soft information and report improvements for their phenomenological Gaussian models; their result also shows that optimizing a physical measurement-error proxy need not optimize logical performance. [Pattison *et al.* (2021), abstract and §§2–6](../../references/pattison2021-soft-information-qec/paper.pdf#Sec.2-Sec.6)

Temkin *et al.* give the closest symmetry-enriched precedent: locally measured \(U(1)\) anyon charges enter an optimal decoder under a charge-conserving phenomenological model. Their result concerns that model and measured charge record, not a general guarantee for non-Abelian heralds. [Temkin *et al.* (2025), abstract and model discussion](../../references/temkin2025-charge-informed-qec/paper.pdf#Sec.Model)

Non-Abelian fusion products provide another, structurally different example. In a \(D_4\) topological-order model, measured intermediate fusion outcomes condition the decoder and can serve as intrinsic heralds without flag qubits. This is direct support for treating a fusion record as evidence, but its threshold analysis assumes perfect syndrome measurements. [Jing *et al.* (2025), pp. 1–5](/reference?id=jing2025-intrinsic-heralding)

## Project implication

The proposed herald field \(H\) must be treated as an observation sampled jointly with the endpoint syndrome \(S\) from the hidden current error configuration \(E\). Relevant controls are an endpoint-only decoder, a matched \((S,H)\) decoder, noisy/missing-herald ablations, and a same-density but uncorrelated mark field. This is project synthesis, not a result of the cited papers.

## Terminology boundary: herald does not mean erasure

In much of the quantum-error-correction literature, “heralded error” means that a loss or erasure event has been flagged and its data-qubit or edge location is known. The erasure pattern is then itself an input to the decoder. That is the model studied by erasure decoders such as Delfosse and Zémor's surface-code decoder. [Delfosse and Zémor (2020), abstract and decoding model](../../references/delfosse2020-erasure-ml-decoding/paper.pdf)

The Herald Decoder project uses the word in its broader operational sense—an additional signal that announces that something locally informative occurred—but for a different physical and probabilistic object. Its herald is a **fusion-remnant witness**: a remnant left after local syndrome/anyon fusion or cancellation. In Lab 001 it is represented by a vertex observation \(h_v\) correlated with the incident error-string degree \(d_v\). It neither reports atom or qubit loss nor names a particular erroneous/erased edge.

This is why a standard erasure decoder is not the recommended default. An erasure decoder conditions on a known subset of affected data variables. By contrast, a fusion-remnant herald supplies a many-edge likelihood factor,

\[
P\!\left(h_v\mid\{x_e:e\ni v\}\right),
\]

without resolving which incident \(x_e\) are one. Converting a herald vertex into adjacent erased edges would therefore solve a different inference problem: it would add artificial edge-location information and throw away the degree/fusion constraint. A matched decoder should instead retain \(h_v\) as a vertex factor—for example in belief propagation or exact posterior inference—and use the resulting edge marginals to reweight a matching back end.

To prevent ambiguity, this Wiki uses **erasure herald** or **loss herald** for the conventional flagged-loss meaning. The unqualified term **herald** refers to the project's fusion-remnant witness unless a page explicitly says otherwise. Erasure-decoding papers are useful methodological comparisons about side information; they do not define this project's observation model.

## Honeycomb advantage: local degree is identifiable

The honeycomb lattice is structurally useful because every bulk vertex is trivalent. Let

\[
d_v=\sum_{e\ni v}x_e.
\]

\[
s_v=d_v\bmod 2.
\]

\[
z_v=\mathbf 1[d_v\ge 2].
\]

where \(s_v\) is the noiseless parity syndrome and \(z_v\) is the underlying herald-eligibility bit. Since \(d_v\in\{0,1,2,3\}\), their joint value determines the incident error-string degree exactly:

| \(s_v\) | \(z_v\) | incident degree \(d_v\) |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 0 | 1 | 2 |
| 1 | 1 | 3 |

This one-to-one map is a specific advantage over a four-valent square-lattice bulk vertex: there, \((s_v,z_v)=(0,1)\) cannot distinguish \(d_v=2\) from \(d_v=4\). It is therefore a central reason to study the honeycomb lattice alongside the square lattice: the joint syndrome–herald record can impose a complete local degree constraint on candidate error configurations, rather than merely indicating that a string passes through the vertex. This is a project-level inference from the [Lab 001 observation model](../../labs/lab-001-string-herald-visualization/PLAN.md#honeycomb-variant).

The exact identification statement applies to the true syndrome and ideal herald eligibility. In the implemented observation model, \(p_m>0\) can flip the parity readout, while \(q<1\) or \(p_h>0\) can hide an eligible herald. In those regimes an observed herald still rules in \(d_v\ge2\), but an absent herald does not rule it out; decoding must use a posterior over \(d_v\) rather than treating the table as a deterministic lookup.

## Time-resolved records under faulty measurements

When syndrome extraction itself is faulty, a record from one round is not sufficient. Repeated measurements produce a spacetime record in which physical and readout faults have different time-space structure. A just-in-time decoder can commit only to sufficiently persistent, well-resolved detection clusters and defer ambiguous events rather than treating a fresh readout as a certain physical fault. [Lyons and Brown (2026), pp. 1–3](/reference?id=lyons2026-anyonic-fault-tolerance)

For this project, any extension from \((S,H)\) to \(\{(S_t,H_t)\}\) must declare the temporal correlations and readout channels for both observations. This is a future modeling requirement, not evidence that the current simulator implements circuit-level measurement noise.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[methods/fault-tolerant-anyonic-decoding|Fault-tolerant anyonic decoding]]
- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
- [[methods/sun-fusion-herald-belief-propagation|SU(N) fusion-herald belief propagation]]
