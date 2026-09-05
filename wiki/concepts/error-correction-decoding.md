---
title: Error-correction decoding
page_type: concept
status: established-background
updated: 2026-09-04
source_refs:
  - references/bravyi2014-surface-code-mld/paper.pdf
  - references/heim2016-optimal-circuit-decoding/paper.pdf
  - references/higgott2023-belief-matching/paper.pdf
  - references/lobl2024-bfs-union-find/paper.pdf
  - references/pattison2021-soft-information-qec/paper.pdf
  - references/delfosse2020-erasure-ml-decoding/paper.pdf
  - references/temkin2025-charge-informed-qec/paper.pdf
  - references/muller2025-relay-bp/paper.pdf
  - references/jing2025-intrinsic-heralding/paper.pdf
  - references/lyons2026-anyonic-fault-tolerance/paper.pdf
  - references/jing2026-ilp-topological-decoder/paper.pdf
  - labs/lab-006-sun-bp-theory/REPORT.md
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
---

# Error-correction decoding

**Summary**: Error-correction decoding is the inference task of mapping an available observation record to a correction or logical-equivalence class under a specified code and noise model. MWPM, Union-Find, Belief Matching, and the project's herald-aware variants are connected decoding methods and layers—not isolated concepts—and must be compared using the same observations.

**Sources**: [Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code](/reference?id=bravyi2014-surface-code-mld); [Optimal Circuit-Level Decoding for Surface Codes](/reference?id=heim2016-optimal-circuit-decoding); [Improved Decoding of Circuit Noise and Fragile Boundaries of Tailored Surface Codes](/reference?id=higgott2023-belief-matching); [Improved Belief Propagation Is Sufficient for Real-Time Decoding of Quantum Memory](/reference?id=muller2025-relay-bp); [Breadth-First Graph Traversal Union-Find Decoder](/reference?id=lobl2024-bfs-union-find); [Improved Quantum Error Correction Using Soft Information](/reference?id=pattison2021-soft-information-qec); [Linear-Time Maximum Likelihood Decoding of Surface Codes over the Quantum Erasure Channel](/reference?id=delfosse2020-erasure-ml-decoding); [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec); [Belief-Matching Decoder](/reference?id=beliefmatching-code); [Union-Find Decoder](/reference?id=uf-decoder-code); [PyMatching Decoder](/reference?id=pymatching-code); [Relay-BP Decoder](/reference?id=relay-bp-code); [Lab 006: SU(N) fusion-herald belief propagation](/lab?id=lab-006-sun-bp-theory)

**Last updated**: 2026-09-04

## Decoder family map

The common task is to infer a recovery from an observation record: syndrome alone in an endpoint-only baseline, or a joint record such as \((S,H)\) when auxiliary information is measured. The following categories separate the statistical objective from the algorithm used to approximate it.

| Family or role | Uses | Relationship in this Wiki |
| --- | --- | --- |
| Logical maximum likelihood (ML) | A fully specified noise and observation model | Performance reference or small-system oracle; exact methods need not be the scalable deployment decoder. |
| MWPM | A weighted matching graph built from the record | A strong endpoint-syndrome baseline and a hard constrained back end. [PyMatching Decoder](/reference?id=pymatching-code) is an implementation of this role. |
| Union-Find | Local cluster growth and a graph representation of the record | A fast alternative hard back end; breadth-first variants cover Pauli-error and erasure settings. [Union-Find Decoder](/reference?id=uf-decoder-code) is an implementation record. |
| Belief Matching / Belief Find | Belief propagation first, then MWPM or Union-Find | A soft-information front end that estimates/reweights faults before a hard correction back end. [Belief-Matching Decoder](/reference?id=beliefmatching-code) records an implementation. |
| Relay-BP | Successive BP legs with disordered memory strengths | A qLDPC-oriented BP dynamics modification that targets oscillation and trapping-set failures; it is not a matching back end. |
| SU(N) full-irrep BP | Binary gauge-sector parity plus the complete symmetry irrep \((m,R)\) | A representation-resolved soft front end whose tree-graph posterior is exact; the current hard back end uses posterior-LLR PyMatching, while the fixed 2D schedule has documented nonconvergence cases. |
| Side-information decoder | Syndrome plus measured erasure, soft, charge, or herald data | A likelihood model can feed any appropriate back end; side information is not by itself a separate matching algorithm. |
| Fault-tolerant anyonic decoder | Time-resolved anyon syndrome under noisy measurements | A non-Abelian, spacetime-decoding setting where fusion records and correction timing are part of the observation model. |
| ILP decoder | Discrete error, readout, and fusion-channel variables | A general constrained optimizer for correlated multi-species and non-Abelian anyon decoding; potentially an oracle or an inner spacetime decoder. |

## How the named decoders connect

### Maximum likelihood and MWPM

Logical ML selects the most likely logical equivalence class under the declared model. It is the right reference definition, but it is not synonymous with a single scalable implementation. Bravyi, Suchara, and Vargo give exact and approximate ML approaches for different surface-code regimes, while circuit-level comparisons show that both the optimum and an MWPM gap depend on the circuit-noise model. [Bravyi, Suchara, and Vargo (2014)](/reference?id=bravyi2014-surface-code-mld) [Heim, Svore, and Hastings (2016)](/reference?id=heim2016-optimal-circuit-decoding)

MWPM instead solves a weighted pairing problem after the physical model has been reduced to a matching graph. It is therefore a natural baseline and a useful correction back end, but a bare matching graph does not automatically retain high-order correlations or an auxiliary vertex record. [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]] explains this performance-reference relationship; [[methods/two-stage-herald-decoder|Two-stage herald decoder]] uses PyMatching only for its residual MWPM stage.

### Union-Find and Belief Matching

Union-Find is a separate cluster-growing decoder family rather than a synonym for MWPM. Breadth-first graph-traversal variants provide one route to fast decoding with Pauli errors and erasures. [Löbl et al. (2024)](/reference?id=lobl2024-bfs-union-find)

Belief Matching and Belief Find connect the families: belief propagation estimates correlated fault probabilities, then supplies weights to MWPM or weighted Union-Find. This leaves a globally syndrome-consistent hard correction to the back end while carrying more of the observation model through the front end. [Higgott et al. (2023)](/reference?id=higgott2023-belief-matching) Thus PyMatching and belief matching are complementary in the project implementation—PyMatching is the matching back end, not a competing soft posterior model.

### Relay-BP

[[methods/relay-belief-propagation|Relay belief propagation]] is another BP-family method, aimed at qLDPC circuit-memory decoding. It changes BP's iterative dynamics using disordered memory strengths and relay initialization between legs; unlike belief matching, it does not require MWPM or Union-Find as a back end. Its reported comparisons are specific to its code families, circuit model, and tuned memory schedule. [Müller et al. (2025)](/reference?id=muller2025-relay-bp)

### Side information changes the inference input

Known erasure locations, soft measurement outcomes, locally measured charge, and this project's fusion-remnant herald all modify what has been observed. They should enter a matched likelihood or factor graph before the correction back end is selected. Soft-information work explicitly adapts both MWPM and Union-Find; erasure decoding conditions on a known affected-qubit pattern; charge-informed decoding uses a different (U(1)) model. [Pattison et al. (2021)](/reference?id=pattison2021-soft-information-qec) [Delfosse and Zémor (2020)](/reference?id=delfosse2020-erasure-ml-decoding) [Temkin et al. (2025)](/reference?id=temkin2025-charge-informed-qec)

The project's herald is not an erasure flag: it is a vertex observation correlated with incident error degree. It should therefore be modeled as a local likelihood factor, not converted into artificially known erased edges. [[methods/side-information-aware-decoding|Side-information-aware decoding]] defines this boundary.

[[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]] makes that likelihood
representation-resolved with the unique record \((m,R)\). Here \(m\) labels the \(\mathbb Z_2\) gauge-sector
boundary and the complete irrep \(R\) is the symmetry-resolved heralding signal. A paired baseline marginalizes
the irrep information to compare \(P(e\mid m)\) with \(P(e\mid m,R)\) on the same sample. The resulting posterior
LLRs feed a syndrome-constrained matching back end; exactness is restricted to factor trees.
The current two-dimensional scan also shows that convergence must be measured rather than inferred from the
ring fixture: 22/128 full-record runs reached the 80-iteration cap without meeting the frozen tolerance.

### Non-Abelian and measurement-noise decoding

Non-Abelian fusion products can themselves be measured side information: in a fixed-point (D_4) model, intermediate fusion outcomes give an intrinsically heralded MWPM decoder more information than endpoint charges alone. That result is conditioned on the paper's noise model and perfect syndrome measurements. [Jing *et al.* (2025)](/reference?id=jing2025-intrinsic-heralding) With faulty measurements, the record must become time-resolved; just-in-time decoding commits only when a detection cluster is sufficiently reliable and defers ambiguous events. [Lyons and Brown (2026)](/reference?id=lyons2026-anyonic-fault-tolerance) [[methods/fault-tolerant-anyonic-decoding|Fault-tolerant anyonic decoding]] keeps these details separate from the present static project model.

Integer linear programming is a further decoder option for general fusion rules: it retains physical-error, measurement-error, and selected fusion-channel variables instead of reducing the record to pairwise matches. Its just-in-time spacetime version is proposed, not threshold-benchmarked. [Jing *et al.* (2026), §VII](/reference?id=jing2026-ilp-topological-decoder) [[methods/integer-linear-programming-decoding|Integer linear programming decoding]] records the scope.

## Project decoder stack

The two currently implemented project methods share a common observation model but use information differently:

- [[methods/two-stage-herald-decoder|Two-stage herald decoder]] treats selected herald patterns as hard local rules, then passes the residual syndrome to PyMatching MWPM. It is a deterministic demonstrator, not a posterior-optimal decoder.
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]] uses BP over the joint syndrome–herald factor graph and passes posterior-derived weights to PyMatching. It is a direct project instance of the belief-matching architecture, with the BP-to-independent-edge-weight projection remaining an approximation.

Both methods must be assessed against matched endpoint-only and syndrome-only-BP-plus-MWPM controls. Current lab evidence is finite-size and preliminary; it does not establish a decoding threshold or runtime advantage. [[models/string-herald-simulator|String-herald simulator model]] owns the shared generative model.

## Selection guide

Choose the decoder layer to match the information and the question:

- Use ML or exhaustive small-system decoding as an oracle when checking whether an approximation loses information.
- Use MWPM/PyMatching for a transparent syndrome-only baseline or a hard back end after likelihood reweighting.
- Use Union-Find when a cluster-growth back end and its operating regime are the intended comparison.
- Use belief matching/find when correlations or local auxiliary observations can be encoded in a factor graph but a scalable hard correction is still required.
- Use Relay-BP when a qLDPC BP decoder needs an explicitly tuned, relay-style convergence mechanism; do not treat it as evidence that the herald likelihood has been modeled.
- Do not compare decoders after changing their observation record: an endpoint-only decoder and a decoder receiving \((S,H)\) answer different conditional-inference problems.

## Thesis impact

This page does not strengthen the project's threshold hypothesis. It makes the testable claim more precise: any reported benefit must be attributed to the herald likelihood while holding the code, noise model, observation budget, and chosen hard back end appropriately controlled.

## Related pages

- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
- [[methods/scalable-decoding|Scalable decoding methods]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[methods/two-stage-herald-decoder|Two-stage herald decoder]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]]
- [[methods/relay-belief-propagation|Relay belief propagation]]
- [[methods/fault-tolerant-anyonic-decoding|Fault-tolerant anyonic decoding]]
- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
- [[methods/integer-linear-programming-decoding|Integer linear programming decoding]]
- [[models/string-herald-simulator|String-herald simulator model]]
- [[thesis|Herald Decoder research program]]
