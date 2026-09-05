---
title: 'J2 causal callback remediation and E1 integration registration'
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

# J2 causal callback remediation and E1 integration registration

Orientation for the typed E1 schedule integration exposed an upstream causal defect. The existing callback receives a digest of the complete visible history, and its request and response digests depend on that value even for `immediate`, `fixed_delay_1`, and `jit_lyons_brown`.

A deterministic counterfactual confirms the issue: two histories identical through the immediate invocation have the same causal prefix digest but different immediate request digests when only future rows change. This invalidates the prior claim that causal callback requests and responses are future-independent. It does not invalidate the original branch timing, immutable shared-history storage, explicit noncausal offline label, or truth-field exclusion. No stochastic or performance result used the affected callback.

The registered matrix therefore runs a prerequisite first. R1 removes full-history identity from the callback while retaining it in outer branch/run provenance, then checks future-counterfactual invariance for all three causal schedules and explicit sensitivity for offline. Only after R1 passes may I1 derive a round-local E1 report from the causal prefix's public syndrome and herald rows. I2 runs both policy modes across all four schedule branches, and I3 checks future, truth, odd-parity, multi-label, and offline boundaries.

All cells use paper L=2, at most four deterministic readout rows, less than five CPU minutes and 1 GiB, and no sampling. The matrix stops before post-action charge recovery or performance comparison.

Canonical contract: [`../manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json`](../../manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json). Counterfactual evidence: [`j2-causal-request-future-digest-audit-2026-08-29.json`](../../results/j2-causal-request-future-digest-audit-2026-08-29.json).

