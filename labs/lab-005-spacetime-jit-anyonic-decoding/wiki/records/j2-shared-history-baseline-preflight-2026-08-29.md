---
title: 'J2 shared-history scheduling baseline harness preflight'
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

# J2 shared-history scheduling baseline harness preflight

> **Partial invalidation, 2026-08-29:** The original callback request contained a digest
> of the complete visible history, so causal request/response digests are
> future-sensitive. Branch timing, shared-history immutability, explicit
> offline noncausality, and truth-field exclusion remain valid. Replacement
> contract: [`../manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json`](../../manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json).
> Evidence: [`j2-causal-request-future-digest-audit-2026-08-29.json`](../../results/j2-causal-request-future-digest-audit-2026-08-29.json).

## Result

All four registered scheduling branches now run through one public deterministic
harness on one immutable `SpacetimeRecord`:

| Branch | Preflight invocation |
|---|---:|
| Immediate | first visible cluster frontier, round 1 |
| Fixed delay 1 | one round after first visibility, round 2 |
| Abstract Lyons–Brown JIT | defer at rounds 1 and 2; invoke when age reaches active absorber distance at round 3 |
| Offline full history | full horizon at round 3, explicitly noncausal |

The exact rounds above are fixture results, not a performance comparison.
Every branch binds to the same outer digest over decoder-visible syndrome/
herald readouts and expected known syndrome changes. The original callback
also received that complete-history digest; therefore its claimed causal
request/response isolation is invalid despite truth-field exclusion.

Different private truth/fault decompositions that produce identical visible
readouts have the same history digest. The runner recomputes the digest after
all branches to reject shared-history mutation. Replaying the full four-branch
matrix produces bit-identical event, request, and response records.

## Verification

Seven focused fixtures verify branch timing, shared history and callback
identity, prefix truncation, explicit offline access, truth-field exclusion,
private-decomposition invariance, deterministic replay, and missing trial/JIT
absorber rejection. All 67 current Lab 005 tests pass.

Contract and hashes:
[`manifests/j2-shared-history-baseline-manifest-2026-08-29.json`](../../manifests/j2-shared-history-baseline-manifest-2026-08-29.json).

## Claim boundary

The callback returns a canonical token and performs no physical correction.
The harness has no stochastic noise generator, logical scorer, LER, latency
distribution, or resource metric. Therefore it does not show that any branch
is better, validate a D(S3) or D4 decoder, or establish a threshold or fault
tolerance.

The next gate is a source-matched repeated-measurement history generator with
separate data faults, syndrome-readout faults, and herald false-positive,
false-negative, and label-confusion channels. It must pass causal,
normalization, and matched-history tests before any pilot sampling.

## Superseding causal-callback evidence

This original preflight's request/response future-isolation claim was later
invalidated because its callback digest included the complete visible-history
digest. R1 has now removed that field and verified future-only invariance for
immediate, fixed-delay, and JIT callbacks while preserving full-history
identity in outer provenance. The original artifact remains historical rather
than being retroactively rehabilitated. Replacement evidence:
[`j2-r1-causal-callback-remediation-2026-08-29.md`](j2-r1-causal-callback-remediation-2026-08-29.md).

