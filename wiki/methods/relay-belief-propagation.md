---
title: Relay belief propagation
page_type: method
status: established-background
updated: 2026-08-27
source_refs:
  - references/muller2025-relay-bp/paper.pdf
  - references/relay-bp-code/provenance.json
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
---

# Relay belief propagation

**Summary**: Relay belief propagation (Relay-BP) is a qLDPC decoding method that runs successive belief-propagation legs with disordered memory strengths, relaying each leg's final beliefs into the next. The archived Rust/Python implementation exposes that method for matrix-and-prior decoding problems; it is a useful BP-family reference, not an existing decoder for this project's syndrome–herald model.

**Sources**: [Improved Belief Propagation Is Sufficient for Real-Time Decoding of Quantum Memory](/reference?id=muller2025-relay-bp); [Relay-BP Decoder](/reference?id=relay-bp-code)

**Last updated**: 2026-08-27

## Method

Standard loopy BP can oscillate or become trapped on qLDPC Tanner graphs because stabilizer-induced symmetries and short loops make local messages ambiguous. Relay-BP adds a memory term to BP, makes the memory strengths disordered across variables, and carries the final marginals from one BP leg into the initialization of the next. The authors call this combination **DMem-BP plus relay ensembling**. [Müller *et al.* (2025), abstract and §§II–III](/reference?id=muller2025-relay-bp)

The method is still a message-passing decoder: it maps a declared check matrix, syndrome, and fault priors to a candidate correction. Its additional control parameters—including the initial memory strength, number of relay legs, per-leg iteration caps, and distribution of disordered memory strengths—are part of the decoder/noise-model configuration, not universal constants. The paper reports that problem-dependent intervals containing negative memory strengths were important in its evaluated settings. [Müller *et al.* (2025), §§III and V](/reference?id=muller2025-relay-bp)

## Evidence boundary and comparison

The paper evaluates circuit-level decoding for two bivariate-bicycle qLDPC memories and a rotated surface-code example. In those stated experiments, it reports an advantage over BP+OSD+CS-10 on the bivariate-bicycle codes and performance comparable to matching on the surface-code case. These are model-, code-, and parameter-dependent results; they do not establish a generic decoder ranking or an advantage for herald side information. [Müller *et al.* (2025), §§VI–VII](/reference?id=muller2025-relay-bp)

## Reference implementation

The archived `trmue/relay` snapshot implements the method in a Rust workspace with a core `relay_bp` crate and a PyO3 Python-binding crate. Its Python package accepts a sparse detector-by-error check matrix, optional observable matrix, error priors, and single-shot or batch decoding; it also provides optional Stim/Sinter adapters and bundled bivariate-bicycle and rotated-surface-code test data. [Relay-BP repository, README and `pyproject.toml`](/reference?id=relay-bp-code)

The public configuration includes `gamma0`, `pre_iter`, `num_sets`, `set_max_iter`, `gamma_dist_interval`, explicit per-variable gammas, and `stop_nconv`. These tune the accuracy/latency trade-off. In particular, a run that cannot find enough valid solutions may consume the full configured iteration budget, so the repository's settings are not portable defaults. [Relay-BP repository, README](/reference?id=relay-bp-code)

The source snapshot contains Rust and Python tests plus CI workflows, and documents `pytest tests/` and `cargo test`. Static inspection establishes it as a tested implementation reference, but does not establish that this workspace can reproduce paper figures or meet any hardware timing target without a separately scoped build and benchmark. [Relay-BP repository, README and test tree](/reference?id=relay-bp-code)

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [[methods/scalable-decoding|Scalable decoding methods]]
