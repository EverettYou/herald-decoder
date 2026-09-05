---
title: 'J2 R1 causal callback remediation'
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

# J2 R1 causal callback remediation

R1 is verified. `InnerDecoderRequest` no longer contains the complete visible-history digest, and the request digest depends only on branch/trial identity, the supplied causal prefix, cluster/event identity, and the declared causal status. The complete history digest remains in the enclosing event, branch, and run provenance.

A four-row deterministic counterfactual changes only the last herald row. Immediate acts at round 1, fixed delay at round 2, and the bounded JIT fixture acts at round 2. For all three causal branches, the prefix, request, and response digests are identical across the pair. Offline acts at the changed final round, remains explicitly noncausal, and its prefix, request, and response digests change.

Eight focused callback tests and all 107 Lab 005 tests pass. No stochastic or performance data were generated. This repairs the callback-isolation claim but does not complete typed E1 schedule integration; I1 round-local E1 derivation is the next gate.

Machine-readable evidence: [manifests/j2-r1-causal-callback-remediation-2026-08-29.json](../../manifests/j2-r1-causal-callback-remediation-2026-08-29.json).

