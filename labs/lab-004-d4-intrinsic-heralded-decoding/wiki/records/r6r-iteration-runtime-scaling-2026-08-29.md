---
title: 'R6R dense R6D iteration-runtime scaling audit'
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

# R6R dense R6D iteration-runtime scaling audit

Profiled 20 frozen paper-L2 records: 36 physical edges, 108 binary variables, 144 factors, and 504 directed messages.

| forced cap | mean kernel time | mean per iteration |
| ---: | ---: | ---: |
| 1 | 0.363 ms | 362.68 µs |
| 2 | 0.671 ms | 335.32 µs |
| 5 | 1.437 ms | 287.31 µs |
| 10 | 2.900 ms | 290.05 µs |
| 20 | 6.871 ms | 343.53 µs |
| 40 | 12.676 ms | 316.91 µs |

Fixed per-record overhead: factor-graph build 13.139 ms; dense packing 1.376 ms.
At the default tolerance, mean performed iterations are 24.50 and pure prepacked-kernel cost is 309.21 µs per performed iteration.

Forced caps test the recurrence with early stopping disabled, so near-proportional cap scaling is the relevant check. This remains a CPU microbenchmark; a small single L2 instance will not predict GPU latency without batching.

