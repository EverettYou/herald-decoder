---
title: 'R6Q dense Numba R6D recurrence benchmark'
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

# R6Q dense Numba R6D recurrence benchmark

All 100 frozen R6N records match exactly at the recorded default recurrence: maximum marginal difference 0.000e+00; no convergence, iteration, residual, or MWPM-correction mismatches.

| implementation | mean recurrence time | median recurrence time |
| --- | ---: | ---: |
| Python table recurrence | 526.49 ms | 475.60 ms |
| Dense Numba recurrence + packing | 4.22 ms | 3.86 ms |

Warm mean speedup: 124.65×; median speedup: 123.12×. The excluded first-call JIT compilation cost is 0.57 s.

The comparison preserves the approximation exactly; it is a CPU Numba result, not a GPU benchmark or an exact-posterior claim.

