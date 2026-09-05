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

> **INVALIDATED LOGICAL RESULTS — 2026-08-27.** Both reweighted arms used
> `-log P(error)` instead of posterior LLR. Their LER, rescue/harm, McNemar,
> pooled logical statistics, and promotion/regression interpretations are
> invalid. BP log loss, Brier score, convergence, iterations, candidate
> metadata, and runtime remain mechanism provenance. See
> [the field-level invalidation manifest](negative-log-invalidation.md).

Five seeds × 200 shots give 1000 matched observations per cell. Parallel workers: 4.

| Lattice | p | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Selected converged | Mean iterations | Cache hit | Uncached ms |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| square | 0.080 | legacy_damped | 72/1000 | 0.0720 [0.0576, 0.0897] | 0.0704 | 0.0202 | 81.2% | 27.18 | 30.7% | 1.90 |
| square | 0.080 | memory_assisted | 92/1000 | 0.0920 [0.0756, 0.1115] | 0.1664 | 0.0256 | 0.0% | 88.31 | 30.7% | 13.07 |
- square p=0.080: new rescued 10, introduced 30, LER delta +0.0200, exact McNemar p=0.002221; log-loss delta +0.09602 CI=[0.0700633710820153, 0.12425465148097536].
| square | 0.100 | legacy_damped | 121/1000 | 0.1210 [0.1022, 0.1427] | 0.0974 | 0.0288 | 74.8% | 29.84 | 18.2% | 1.82 |
| square | 0.100 | memory_assisted | 121/1000 | 0.1210 [0.1022, 0.1427] | 0.1937 | 0.0336 | 0.0% | 83.73 | 18.2% | 12.71 |
- square p=0.100: new rescued 22, introduced 22, LER delta +0.0000, exact McNemar p=1; log-loss delta +0.09623 CI=[0.071040915034325, 0.12384393137125624].
| square | 0.120 | legacy_damped | 152/1000 | 0.1520 [0.1311, 0.1756] | 0.1272 | 0.0381 | 70.6% | 31.77 | 10.9% | 1.70 |
| square | 0.120 | memory_assisted | 150/1000 | 0.1500 [0.1292, 0.1735] | 0.2206 | 0.0440 | 0.0% | 82.38 | 10.9% | 12.76 |
- square p=0.120: new rescued 28, introduced 26, LER delta -0.0020, exact McNemar p=0.8919; log-loss delta +0.09341 CI=[0.07012040167054034, 0.11846242436120899].
| honeycomb | 0.160 | legacy_damped | 31/1000 | 0.0310 [0.0219, 0.0437] | 0.0619 | 0.0184 | 42.0% | 37.88 | 0.0% | 2.52 |
| honeycomb | 0.160 | memory_assisted | 32/1000 | 0.0320 [0.0228, 0.0448] | 0.2973 | 0.0230 | 0.0% | 74.78 | 0.0% | 33.79 |
- honeycomb p=0.160: new rescued 1, introduced 2, LER delta +0.0010, exact McNemar p=1; log-loss delta +0.23545 CI=[0.19354686018068384, 0.279990198193124].
| honeycomb | 0.180 | legacy_damped | 56/1000 | 0.0560 [0.0434, 0.0720] | 0.0818 | 0.0244 | 27.2% | 38.93 | 0.0% | 2.37 |
| honeycomb | 0.180 | memory_assisted | 54/1000 | 0.0540 [0.0416, 0.0698] | 0.3985 | 0.0304 | 0.0% | 72.54 | 0.0% | 45.99 |
- honeycomb p=0.180: new rescued 3, introduced 1, LER delta -0.0020, exact McNemar p=0.625; log-loss delta +0.31665 CI=[0.267325240288786, 0.36713820601394975].
| honeycomb | 0.200 | legacy_damped | 87/1000 | 0.0870 [0.0711, 0.1061] | 0.1062 | 0.0320 | 15.6% | 39.46 | 0.0% | 2.55 |
| honeycomb | 0.200 | memory_assisted | 81/1000 | 0.0810 [0.0656, 0.0996] | 0.5323 | 0.0404 | 0.0% | 69.22 | 0.0% | 47.66 |
- honeycomb p=0.200: new rescued 8, introduced 2, LER delta -0.0060, exact McNemar p=0.1094; log-loss delta +0.42611 CI=[0.36915972987865564, 0.4841383953286235].

## Descriptive pooled logical results

- square: legacy 345/3000 (0.1150), memory 363/3000 (0.1210); rescued 60, introduced 78, delta +0.0060, McNemar p=0.1476.
- honeycomb: legacy 174/3000 (0.0580), memory 167/3000 (0.0557); rescued 12, introduced 5, delta -0.0023, McNemar p=0.1435.
- all cells: legacy 519/6000 (0.0865), memory 530/6000 (0.0883); rescued 72, introduced 83, delta +0.0018, McNemar p=0.4219.

This is systematic finite-size evidence at L=5, not threshold estimation. Grid selection used a legacy-only pilot and did not inspect the A/B effect.

