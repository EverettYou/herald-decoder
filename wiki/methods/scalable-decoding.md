---
title: Scalable decoding methods
page_type: method
status: established-background
updated: 2026-08-26
source_refs:
  - references/higgott2023-belief-matching/paper.pdf
  - references/lobl2024-bfs-union-find/paper.pdf
  - references/muller2025-relay-bp/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
---

# Scalable decoding methods

**Summary**: Fast decoders trade off model fidelity, threshold performance, and runtime; they are candidate implementation baselines rather than substitutes for the herald observation model.

**Sources**: [Improved Decoding of Circuit Noise and Fragile Boundaries of Tailored Surface Codes](/reference?id=higgott2023-belief-matching); [Breadth-First Graph Traversal Union-Find Decoder](/reference?id=lobl2024-bfs-union-find); [Improved Belief Propagation Is Sufficient for Real-Time Decoding of Quantum Memory](/reference?id=muller2025-relay-bp); [Belief-Matching Decoder](/reference?id=beliefmatching-code); [Union-Find Decoder](/reference?id=uf-decoder-code); [Relay-BP Decoder](/reference?id=relay-bp-code)

**Last updated**: 2026-08-26

## Current synthesis

Higgott *et al.* combine belief propagation with MWPM or weighted Union-Find so that reweighted matching graphs retain more circuit-noise information than standard matching graphs. Their reported circuit-level thresholds are model- and decoder-specific; the work demonstrates the value of retaining correlations while preserving efficient runtime. [Higgott *et al.* (2023), abstract and §I](../../references/higgott2023-belief-matching/paper.pdf#Sec.I)

Löbl *et al.* develop breadth-first graph-traversal Union-Find variants that simplify cluster growth and can include Pauli errors and erasures. Their performance and low-error runtime claims are tied to the tested code families and noise models. [Löbl *et al.* (2024), abstract and §§1–2](../../references/lobl2024-bfs-union-find/paper.pdf#Sec.1-Sec.2)

Relay-BP is a contrasting scalable BP-family route for qLDPC circuit-memory problems: it uses disordered memory strengths and successive relayed BP legs rather than a matching or cluster-growth back end. Its reported accuracy and real-time feasibility depend on the tested bivariate-bicycle/surface-code circuits and tuned memory schedules. [Müller *et al.* (2025), abstract and §§III, VI–VII](/reference?id=muller2025-relay-bp)

## Project implication

Once a herald-aware likelihood or factor graph is specified, compare a likelihood-oriented reference implementation with fast approximations that consume exactly the same \((S,H)\) record. Do not infer an algorithmic speedup or threshold improvement merely from the existence of an auxiliary field.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/relay-belief-propagation|Relay belief propagation]]
