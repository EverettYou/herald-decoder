---
title: Surface-code decoding baselines
page_type: method
status: established-background
updated: 2026-08-26
source_refs:
  - references/dennis2001-topological-quantum-memory/paper.pdf
  - references/bravyi2014-surface-code-mld/paper.pdf
  - references/heim2016-optimal-circuit-decoding/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Topological Phases, Decoding Algorithms]
---

# Surface-code decoding baselines

**Summary**: Surface-code decoding selects a logical correction class conditioned on an observed record and a specified noise model. Maximum-likelihood decoding is the performance baseline, but its tractable implementations and attainable performance depend on those assumptions.

**Sources**: [Topological Quantum Memory](/reference?id=dennis2001-topological-quantum-memory); [Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code](/reference?id=bravyi2014-surface-code-mld); [Optimal Circuit-Level Decoding for Surface Codes](/reference?id=heim2016-optimal-circuit-decoding); [PyMatching Decoder](/reference?id=pymatching-code)

**Last updated**: 2026-08-26

## Current synthesis

Dennis *et al.* formulate surface-code recovery as inferring an error-equivalence class from syndrome information. With perfect syndrome measurements, they relate the threshold problem to a disordered two-dimensional Ising model; with unreliable repeated measurements, the relevant model becomes a three-dimensional disordered \(\mathbb Z_2\) gauge theory. [Dennis *et al.* (2001), abstract and §IV](../../references/dennis2001-topological-quantum-memory/paper.pdf#Sec.IV)

For noiseless syndrome extraction and independent bit- and phase-flip noise, Bravyi, Suchara, and Vargo give an exact \(O(n^2)\) maximum-likelihood decoder. For more general depolarizing noise, their MPS contraction method is approximate, with runtime \(O(n\chi^3)\); its empirical accuracy depends on the chosen bond dimension. [Bravyi, Suchara, and Vargo (2014), abstract and §§V–VII](../../references/bravyi2014-surface-code-mld/paper.pdf#Sec.V-Sec.VII)

At circuit level, a decoder must account for gate failures and error propagation through syndrome-extraction circuits. Heim, Svore, and Hastings report that both the threshold and the gap between MWPM and their mathematical ML decoder change with the circuit-noise model. [Heim, Svore, and Hastings (2016), abstract and §§I–II](../../references/heim2016-optimal-circuit-decoding/paper.pdf#Sec.I-Sec.II)

## Relevance to herald decoding

The project should compare an endpoint-only baseline and a herald-aware decoder under the same joint generative model and measurement budget. A change in an auxiliary record or in noise correlations changes the inference problem; it is not evidence of a higher threshold by itself.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[methods/scalable-decoding|Scalable decoding methods]]
