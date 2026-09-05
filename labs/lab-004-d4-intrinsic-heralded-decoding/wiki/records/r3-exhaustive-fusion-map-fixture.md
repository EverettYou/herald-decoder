---
title: 'R3.0 exhaustive fusion-constrained MAP fixture'
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

# R3.0 exhaustive fusion-constrained MAP fixture

## Registered role

This bounded enumerator is the truth reference for a later MILP implementation. Given one observed flux/fusion record and a declared iid error rate, it enumerates all red-X edge sets and enforces:

- the observed flux boundary;
- degree-two support of every measured intermediate star;
- every candidate-generated fusion-parity relation;
- the exact Appendix-A conditional likelihood `P(s|E)=2^(C-N_internal)`;
- the Bernoulli prior `P(E)=p^|E|(1-p)^(N-|E|)`.

It returns every configuration maximizing `P(s|E)P(E)`. Candidate winding components whose observation likelihood would require an undeclared absolute logical-sector policy are censored rather than assigned a guessed likelihood.

## Tiny exhaustive result

The primitive `L=2` semantic fixture has 8 vertices, 12 edges, and 4096 possible error sets. For the observation sampled from mask 73 (edges 0, 3, 6; fusion seed 11), exactly four nonwinding explanations are compatible and no winding explanation is censored.

At `p=0.1`, masks 73, 82, and 268 tie for the MAP objective. Relative to mask 73, the three modes occupy trivial, horizontal-winding, and vertical-winding residual sectors. Thus a configuration-MAP optimum is not even a unique logical-sector decision on this fixture.

At `p=0.6`, mask 279 is the unique MAP explanation, demonstrating that the declared physical prior is part of the constrained objective rather than an implicit unit-weight convention.

Three tests cover the exact fixture, prior dependence, and fail-closed bounds. The complete Lab suite now passes 75 tests.

## Claim boundary

This is R3.0—the exhaustive validation target—not yet the MILP compilation. It also does not perform the R4 sum over posterior mass in each logical sector. The MAP tie across three relative sectors is direct evidence that R4 cannot be replaced by selecting one minimum-cost configuration.

