---
title: 'Corrected J2 typed E1 causal schedule integration'
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

# Corrected J2 typed E1 causal schedule integration

## Result

The bounded deterministic paper-\(L=2\) stage-1 interface now answers its registered question positively: every causal schedule invokes the typed public E1 D4 policy using only its decision-time prefix, both public modes share one physical trace, and the offline baseline remains explicitly noncausal. This is an interface-correctness result, not evidence of decoder or schedule performance.

## Invalid history and correction

The original J2 shared-history preflight remains partially invalid. Its callback contained the digest of the complete visible history, so future-only changes altered causal request and response digests. That artifact is retained for provenance and is not rehabilitated. Its branch timing, outer shared-history immutability, explicit offline label, and truth-field exclusion remain usable.

R1 removes the full-history digest from `InnerDecoderRequest` and its digest while retaining full-history identity in event, branch, and run provenance. Future-only counterfactuals then leave immediate, fixed-delay, and JIT callback outputs invariant; the final offline output changes as expected.

## Corrected causal pipeline

I1 accepts one bound schedule callback and derives a typed E1 report only from its final public syndrome/herald row. Across all 24 D4 vertices, syndrome membership maps to `m_flux` and herald membership maps independently to `e_charge`, including simultaneous membership at one site. Trial and round identity match the invocation. Truth-only and future-only counterfactuals are invariant, and malformed binding or spatial shape fails closed.

I2/I3 run the actual stage-1 D4 public policy in all eight cells:

| Mode | Immediate | Fixed delay 1 | JIT | Offline |
| --- | --- | --- | --- | --- |
| Syndrome only | causal, pass | causal, pass | causal, pass | noncausal, pass |
| Heralded | causal, pass | causal, pass | causal, pass | noncausal, pass |

All returned corrections reproduce the supplied flux syndrome. The modes share trace, timing, scheduler request, and policy implementation. Syndrome-only receives no charge measurements; heralded receives the complete public charge-membership record. Future-only, private-truth, simultaneous-label, odd-parity, offline-label, and replay controls pass.

## Claim boundary

The deterministic checks have no sampling uncertainty. They establish causal information flow and stage-1 syndrome fidelity only. The fixture's correction sizes and objectives cannot be interpreted as a comparison. There is no logical scorer, post-action charge recovery, runtime study, logical-error rate, threshold estimate, or fault-tolerance result.

The final focused suite passes 14 tests, the Lab passes all 121 tests, the dashboard passes 28 tests, and Wiki lint reports no findings. The next gate is a downstream consumer audit that releases only corrected evidence while performance sampling remains blocked.

Machine-readable analysis: [manifests/j2-e1-causal-integration-remediation-2026-08-29.json](../../manifests/j2-e1-causal-integration-remediation-2026-08-29.json).

