---
title: 'J3 causal detector-cluster construction preflight'
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

# J3 causal detector-cluster construction preflight

## Result

The abstract schedule no longer requires every cluster to be hand assembled.
Given a `CausalRecordPrefix` and declared spatial coordinates for each check,
the new constructor creates one event for each visible detector, appends the
ending readout round as its time coordinate, and takes deterministic connected
components under the registered integer spacetime \(L_\infty\) radius one.

Each snapshot cluster reports its oldest and youngest event round, age relative
to the causal horizon, inclusive spacetime extent, nearest other-cluster
separation, nearest active external absorber, and geometric link candidates
within twice its extent. Terminated absorbers and an absorber owned by the same
content-derived cluster identifier are excluded.

Only a component touching the current detector frontier may be converted into
an abstract schedule cluster. The handoff uses only its current-round check
indices, explicit extent, and active nearest-absorber distance. A focused
end-to-end fixture confirms that this constructed input drives the public
Lyons–Brown defer transition and decoder-record reversal without future data.

## Verification

Seven focused fixtures cover deterministic components, geometric summaries,
active link candidates, absorber exclusion, current-frontier handoff, public
schedule integration, and malformed prefix/coordinate rejection. All 53
current Lab 005 tests pass.

Contract and hashes:
[`manifests/j3-causal-detector-cluster-manifest-2026-08-29.json`](../../manifests/j3-causal-detector-cluster-manifest-2026-08-29.json).

## Claim boundary

This is a causal snapshot constructor with a registered diagnostic adjacency
rule. It does not establish that radius one is unique or physically optimal,
does not maintain persistent identity through future component mergers, does
not infer correction strings or fusion channels, and does not reproduce the
paper's full linked-cluster proof. It provides no noisy-channel, schedule
performance, threshold, or fault-tolerance evidence.

The next bounded gate is a persistent tracker over successive causal prefixes:
stable identifiers, append-only event ownership, deterministic cluster merges,
and absorber-link updates must be verified before a noisy-measurement pilot.

