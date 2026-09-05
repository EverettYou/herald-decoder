---
title: 'Systematic matched BP-update A/B'
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

# Systematic matched BP-update A/B

Five seeds × 1 shots give 1000 matched observations per cell. Parallel workers: 1.

| Lattice | p | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Selected converged | Mean iterations | Cache hit | Uncached ms |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| square | 0.080 | legacy_damped | 0/1 | 0.0000 [0.0000, 0.7935] | 0.3394 | 0.1205 | 0.0% | 40.00 | 0.0% | 3886.40 |
| square | 0.080 | memory_assisted | 0/1 | 0.0000 [0.0000, 0.7935] | 0.3472 | 0.1211 | 0.0% | 40.00 | 0.0% | 120.84 |
- square p=0.080: new rescued 0, introduced 0, LER delta +0.0000, exact McNemar p=1; log-loss delta +0.00786 CI=[0.007856622537779856, 0.007856622537779856].
| honeycomb | 0.160 | legacy_damped | 0/1 | 0.0000 [0.0000, 0.7935] | 0.2740 | 0.0662 | 0.0% | 40.00 | 0.0% | 18.52 |
| honeycomb | 0.160 | memory_assisted | 0/1 | 0.0000 [0.0000, 0.7935] | 0.5902 | 0.0676 | 0.0% | 40.00 | 0.0% | 84.49 |
- honeycomb p=0.160: new rescued 0, introduced 0, LER delta +0.0000, exact McNemar p=1; log-loss delta +0.31624 CI=[0.31623871684550703, 0.31623871684550703].

## Descriptive pooled logical results

- square: legacy 0/1 (0.0000), memory 0/1 (0.0000); rescued 0, introduced 0, delta +0.0000, McNemar p=1.
- honeycomb: legacy 0/1 (0.0000), memory 0/1 (0.0000); rescued 0, introduced 0, delta +0.0000, McNemar p=1.
- all cells: legacy 0/2 (0.0000), memory 0/2 (0.0000); rescued 0, introduced 0, delta +0.0000, McNemar p=1.

This is systematic finite-size evidence at L=5, not threshold estimation. Grid selection used a legacy-only pilot and did not inspect the A/B effect.

