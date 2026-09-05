---
title: 'R4.5a branch-labelled primitive charge topology'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# R4.5a branch-labelled primitive charge topology

**Registered 2026-08-29; branch-catalog and provenance preflight passed. No sequential risk is computed.**

## Why this is the next prerequisite

R4.5 verified the exact adaptive second-record likelihood and its resource budget, then failed before policy computation. On `periodic_honeycomb(2)`, each charge colour has twelve physical triangular edges but only six endpoint pairs. Every endpoint pair is connected by two branches through different opposite-colour centres, and those branches have different periodic displacements. Thus they have the same charge boundary but can differ in logical winding.

The existing `PeriodicPostFluxRelations` keeps only endpoint pairs. That is a valid description of the parity constraint after forgetting geometry, but it is not sufficient to choose a physical charge edge. The production `ChargeLattice` correctly fails rather than selecting one parallel branch.

## Registered physical representation

R4.5a retains the primitive physical model and gives each triangular branch a stable id together with its charge colour, two charge endpoints, opposite-colour centre, and primitive displacement. A post-flux relation must be derived from the actual two-step union path through that centre and must identify exactly one branch. Endpoint matching is only a validation projection; it is never a branch-selection rule.

The enriched relation object must satisfy two simultaneous conditions:

1. forgetting branch labels reproduces the existing endpoint-only DSU connectivity and parity partition exactly; and
2. keeping branch displacement gives a well-defined lifted path and torus homology.

These conditions distinguish three outcomes. Direct branch labels may solve the defect; actual path provenance may be required to solve it; or the current union invariant may have lost the needed local path information. The third outcome is a legitimate fail-closed result, not permission to guess a branch.

## Smallest discriminating audit

The preflight first builds the branch catalog for blue and green, then streams all 127,136 source-frozen primitive `(E,A)` pairs. It records whether each old endpoint relation has zero, one, or multiple compatible physical branches and checks that branch-forgetting recovers the old parity components. It stops there on any provenance ambiguity.

Only after provenance passes will the audit run explicit periodic fixtures: parallel branches must have equal boundary and distinct displacement; their XOR must close and carry the expected relative winding. The exhaustive affine charge-chain quotient must then contain exactly four homology classes per colour, with loss constant inside each class. A lifted universal-cover calculation is an independent oracle for displacement and winding, not a replacement model.

Finally, duplicate check-matrix columns require a direct public-decoder test. If PyMatching does not preserve distinct branch fault ids and weights, the exact quotient can still pass, but the published second-stage MWPM is not yet reproduced. An expanded-graph adapter would then be registered separately.

## Scope and stop rules

This is deterministic topology remediation: no new samples, no larger lattice, no approximate posterior, and no policy-risk number. The wall-time and memory guards are ten minutes and 2 GiB. Any relation with zero or multiple branch provenance stops the audit before the homology quotient. Any decoder-side branch collapse stops the public-policy claim. R4.4 remains the latest valid decision result until every R4.5a gate passes.

The implemented prerequisite classified all 127,136 primitive `(E,A)` pairs. All 6,816 nonterminal pairs passed: 48,000 endpoint relation occurrences each mapped to one physical centre/path-labelled branch, and forgetting those labels recovered the production endpoint relation set and DSU parity partition exactly.

The homology gate then validated all twelve parallel-pair fixtures and all 512 closed chains per colour. Homology is evaluated by the registered period cochain: each branch displacement is compared with the fixed endpoint representatives, giving an edge wrap vector modulo two; XOR over a closed chain is therefore linear by construction. The result is four equal sectors of 128 and four equal action classes for every even syndrome. The prior component-level winding collector remains a valid oracle on all nonbranching cycle-like fixtures, but its Boolean component aggregation is not linear on branched/multicycle chains and is excluded from the quotient. The public-decoder branch test remains a separate later gate.

The machine-readable contract is [`../manifests/r4-branch-labelled-charge-topology-manifest-2026-08-29.json`](../../manifests/r4-branch-labelled-charge-topology-manifest-2026-08-29.json).

Preflight evidence: [`manifests/r4-branch-labelled-charge-topology-audit.json`](../../manifests/r4-branch-labelled-charge-topology-audit.json) and [`r4-branch-labelled-charge-topology-audit.md`](r4-branch-labelled-charge-topology-audit.md).

