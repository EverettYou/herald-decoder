---
title: 'R6S production-size R6D BP CPU baseline'
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

# R6S production-size R6D BP CPU baseline

This controlled benchmark uses one deterministic, finite observation per size and forces 10 iterations. Each timing is the mean of 5 calls after one excluded compilation warm-up.

| L | edges | build + pack + BP | cached refresh + BP | speedup |
| ---: | ---: | ---: | ---: | ---: |
| 15 | 2025 | 1658.07 ms | 327.15 ms | 5.07x |

This is a controlled CPU scaling baseline, not a decoder-accuracy study, GPU benchmark, or a claim about typical observation-distribution latency. It establishes the target sizes and the removable topology-construction cost before caching.

