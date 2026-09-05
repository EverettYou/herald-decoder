---
title: 'R6AF complete two-stage O0/O2 pilot'
status: current
updated: 2026-09-01
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

# R6AF complete two-stage O0/O2 pilot

Status: **analyzed_registered_pilot**.

## Paired results

| L | p_X | O0 risk (90% Wilson) | O2 risk (90% Wilson) | Delta O2-O0 (90% paired bootstrap) | direction | discordance O0-only/O2-only |
|---:|---:|---:|---:|---:|:---|:---|
| 3 | 0.19 | 0.4668 [0.4308, 0.5031] | 0.2363 [0.2069, 0.2685] | -0.2305 [-0.2676, -0.1934] | resolved_improvement | 143/25 |
| 3 | 0.21 | 0.5938 [0.5576, 0.6289] | 0.3320 [0.2988, 0.3671] | -0.2617 [-0.3027, -0.2227] | resolved_improvement | 166/32 |
| 5 | 0.19 | 0.5586 [0.5223, 0.5943] | 0.1719 [0.1462, 0.2010] | -0.3867 [-0.4258, -0.3477] | resolved_improvement | 212/14 |
| 5 | 0.21 | 0.7031 [0.6689, 0.7352] | 0.3281 [0.2950, 0.3631] | -0.3750 [-0.4160, -0.3340] | resolved_improvement | 214/22 |

## Integrity

All 2,048 independent matched histories and 4,096 arm evaluations completed in 41.91 s. All structural gates and all 12 registered first/middle/final replay checks passed.

## Claim boundary

Pointwise paired pilot directions only. No multiplicity-adjusted discovery, threshold, crossing, scaling, fault-tolerance, BP, or Lab 003 comparison claim.
The registered 512-history/cell stop is final for this pilot; unresolved cells are not adaptively extended.

