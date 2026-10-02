---
title: Planar herald decoder survey
page_type: comparison
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Planar herald decoder survey

Lab 009 incorporates reusable inference methods into the existing classical observation model. It builds on [Lab 002](../../lab-002-herald-belief-matching/REPORT.md), [Lab 003](../../lab-003-herald-threshold-phase-diagram/REPORT.md), and the sector formulation of [Lab 007](../../lab-007-decoding-statistical-mechanics/PLAN.md).

- [BP and posterior-LLR matching](bp-matching.md): local messages, negative weights, projection loss and convergence.

1. [Model, record and logical loss](model.md): exactly what information a decoder receives.
2. [Statistical mechanics and sector partition functions](statistical-mechanics.md): edge/site weights, gauge variables, information ordering and sufficient recovery bound.
3. [Configuration MAP and signed matching](configuration-map.md): hard constraints, literal weights and geometry-specific integer reduction.
4. [Planar logical ML and matchgates](planar-ml.md): local gadgets, Pfaffian orientation and an observable that avoids subtracting sector sums.
5. [Exact transfer and controlled MPS](transfer-mps.md): width, truncation, normalization and validation.
6. [Kac–Ward determinant](kac-ward.md): even-subgraph construction, finite penalties and why this branch remains a research implementation.
7. [Survey, measurements and reuse](comparison.md): method selection, efficiency, inherited cohorts and scientific limits.

8. [SciCode2 assessment of nine agent submissions](scicode2-run-evaluation.md): the complete original independent evaluation, named-run comparison figure, per-run results and challenge-design lessons.

The [report](../REPORT.md) is the evidence synthesis. [Source API documentation](../../../src/herald_decoder/README.md) supplies callable examples. Numeric evidence lives in `data/` and `results/`; these method pages contain the durable derivations rather than duplicate campaign logs. Primary literature is linked on the relevant method pages. Internal source hashes preserve data provenance without making agent identities part of the algorithm names.
- [[records/index|Detailed research records]]

- [Survey integration record](records/survey-integration.md): acceptance receipts and delivery chain.
