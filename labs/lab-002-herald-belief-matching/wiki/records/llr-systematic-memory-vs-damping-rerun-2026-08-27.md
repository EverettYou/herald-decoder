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

Five seeds × 200 shots give 1000 matched observations per cell. Parallel workers: 1.

| Lattice | p | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Selected converged | Mean iterations | Cache hit | Uncached ms |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| square | 0.080 | legacy_damped | 71/1000 | 0.0710 [0.0567, 0.0886] | 0.0704 | 0.0202 | 81.2% | 27.18 | 30.7% | 5.06 |
| square | 0.080 | memory_assisted | 90/1000 | 0.0900 [0.0738, 0.1093] | 0.1664 | 0.0256 | 0.0% | 88.31 | 30.7% | 23.73 |
- square p=0.080: new rescued 12, introduced 31, LER delta +0.0190, exact McNemar p=0.005402; log-loss delta +0.09602 CI=[0.0700633710820153, 0.12425465148097536].
| square | 0.100 | legacy_damped | 121/1000 | 0.1210 [0.1022, 0.1427] | 0.0974 | 0.0288 | 74.8% | 29.84 | 18.2% | 1.30 |
| square | 0.100 | memory_assisted | 116/1000 | 0.1160 [0.0976, 0.1373] | 0.1937 | 0.0336 | 0.0% | 83.73 | 18.2% | 16.30 |
- square p=0.100: new rescued 26, introduced 21, LER delta -0.0050, exact McNemar p=0.5601; log-loss delta +0.09623 CI=[0.071040915034325, 0.12384393137125624].
| square | 0.120 | legacy_damped | 154/1000 | 0.1540 [0.1330, 0.1777] | 0.1272 | 0.0381 | 70.6% | 31.77 | 10.9% | 0.89 |
| square | 0.120 | memory_assisted | 145/1000 | 0.1450 [0.1245, 0.1682] | 0.2206 | 0.0440 | 0.0% | 82.38 | 10.9% | 12.25 |
- square p=0.120: new rescued 33, introduced 24, LER delta -0.0090, exact McNemar p=0.2892; log-loss delta +0.09341 CI=[0.07012040167054034, 0.11846242436120899].
| honeycomb | 0.160 | legacy_damped | 30/1000 | 0.0300 [0.0211, 0.0425] | 0.0619 | 0.0184 | 42.0% | 37.88 | 0.0% | 2.32 |
| honeycomb | 0.160 | memory_assisted | 31/1000 | 0.0310 [0.0219, 0.0437] | 0.2973 | 0.0230 | 0.0% | 74.78 | 0.0% | 43.13 |
- honeycomb p=0.160: new rescued 1, introduced 2, LER delta +0.0010, exact McNemar p=1; log-loss delta +0.23545 CI=[0.19354686018068384, 0.279990198193124].
| honeycomb | 0.180 | legacy_damped | 56/1000 | 0.0560 [0.0434, 0.0720] | 0.0818 | 0.0244 | 27.2% | 38.93 | 0.0% | 3.41 |
| honeycomb | 0.180 | memory_assisted | 53/1000 | 0.0530 [0.0407, 0.0687] | 0.3985 | 0.0304 | 0.0% | 72.54 | 0.0% | 58.58 |
- honeycomb p=0.180: new rescued 3, introduced 0, LER delta -0.0030, exact McNemar p=0.25; log-loss delta +0.31665 CI=[0.267325240288786, 0.36713820601394975].
| honeycomb | 0.200 | legacy_damped | 82/1000 | 0.0820 [0.0666, 0.1006] | 0.1062 | 0.0320 | 15.6% | 39.46 | 0.0% | 1.76 |
| honeycomb | 0.200 | memory_assisted | 81/1000 | 0.0810 [0.0656, 0.0996] | 0.5323 | 0.0404 | 0.0% | 69.22 | 0.0% | 33.05 |
- honeycomb p=0.200: new rescued 4, introduced 3, LER delta -0.0010, exact McNemar p=1; log-loss delta +0.42611 CI=[0.36915972987865564, 0.4841383953286235].

## Descriptive pooled logical results

- square: legacy 346/3000 (0.1153), memory 351/3000 (0.1170); rescued 71, introduced 76, delta +0.0017, McNemar p=0.7416.
- honeycomb: legacy 168/3000 (0.0560), memory 165/3000 (0.0550); rescued 8, introduced 5, delta -0.0010, McNemar p=0.5811.
- all cells: legacy 514/6000 (0.0857), memory 516/6000 (0.0860); rescued 79, introduced 81, delta +0.0003, McNemar p=0.937.

This is systematic finite-size evidence at L=5, not threshold estimation. Grid selection used a legacy-only pilot and did not inspect the A/B effect.

