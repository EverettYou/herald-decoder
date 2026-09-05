---
title: 'R6E exact-message and small-graph BP marginal gate'
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

# R6E exact-message and small-graph BP marginal gate

## Implementation gate

Both registered schedules reproduce the brute-force factor-tree marginals; the largest tree error is 2.853e-11. Factor-to-variable messages explicitly sum every assignment of each nonnegative R6D table, and variable messages multiply the prior by every other incoming factor message.

## Loopy primitive result

The matrix contains 32 matched primitive-D4 runs across four observation strata, two physical error rates, local-only versus terminal-screened graphs, and two schedules. Raw synchronous BP converges on 0/16 rows; damping 0.25 converges on 10/16 rows. Among converged rows, the largest physical-edge marginal error is 0.5; 0/32 rows both converge and agree within `1e-8`.

The local-only and terminal-screened branches each contain 16 and 16 matched rows. They are intentionally separate: the local R6D factors represent the observation likelihood, whereas the finite 12-edge terminal projector enforces the current ground-state-relative winding policy. The projector is an exact primitive control, not a scalable localization.

## Interpretation

Passing the tree gate verifies message arithmetic. Any loopy bias or nonconvergence is an algorithmic property of this factorization and schedule, not a likelihood error and not something that can be removed by relabeling the result. The next gate must be chosen from the observed failure mode: fixed-point approximation if converged but biased, or schedule/region-graph work if nonconvergent.

## Claim boundary

Tree message correctness and descriptive finite primitive loopy-BP marginal evidence only. No correction, LER, threshold, scalable convergence, runtime scaling, or fault-tolerance claim.

