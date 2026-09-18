---
title: Full-record logical error rate curves
status: current
updated: 2026-09-09
---

# Full-record logical error rate curves

## Summary

Six finite-size logical error rate (LER) scans measure U(1), SU(2), and SU(3)
on square and honeycomb lattices. The decoder conditions on the complete
interior binary syndrome m and symmetry irrep R. Left/right rough-boundary
m and R are unmeasured and marginalized; smooth-edge detector sites retain
their ordinary records. None is deferred by the researcher.

## Evidence

The [registered contract](../manifests/a8-artifact-full-record-ler-curves-2026-09-05.json)
freezes directed pair errors, sum-product BP, damping 0.5, 300 iterations,
tolerance 1e-10, posterior-LLR PyMatching, L=5,7,9,11, and p=0.02,0.04,...,0.50.
Each sampled cell uses 20,000 independent shots. p=0 is an exact zero-error
endpoint and is not included in the shot total. Wilson 95% intervals describe
binomial uncertainty; a zero observed count does not establish zero LER.

| Lattice | Group | Raw counts | LER figure | BP diagnostic |
| --- | --- | --- | --- | --- |
| square | U1 | [Counts](../results/a8-fullrecord-square-U1-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-square-U1-nonconvergence.png) |
| square | SU2 | [Counts](../results/a8-fullrecord-square-SU2-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-square-SU2-nonconvergence.png) |
| square | SU3 | [Counts](../results/a8-fullrecord-square-SU3-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-square-SU3-nonconvergence.png) |
| honeycomb | U1 | [Counts](../results/a8-fullrecord-honeycomb-U1-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-honeycomb-U1-nonconvergence.png) |
| honeycomb | SU2 | [Counts](../results/a8-fullrecord-honeycomb-SU2-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-honeycomb-SU2-nonconvergence.png) |
| honeycomb | SU3 | [Counts](../results/a8-fullrecord-honeycomb-SU3-final-v2.json) | [LER](../figures/a8-full-record-ler-overview.png) | [Nonconvergence](../figures/a8-honeycomb-SU3-nonconvergence.png) |

[Acquisition progress](../results/a8-acquisition-progress.json) records
the completed cell count. Each final panel contains 100 sampled cells plus
the exact p=0 endpoint. Connecting lines only guide the eye; panel-specific
linear vertical ranges preserve visibility of the low-rate curves.


### Descriptive slice at p=0.30

This post-acquisition slice illustrates size dependence; it is not a fitted
threshold or a prespecified hypothesis test. Intervals are Wilson 95%.

| Lattice | Group | L=5 LER [95% interval] | L=11 LER [95% interval] |
| --- | --- | --- | --- |
| square | U1 | 0.1646 [0.15953, 0.1698] | 0.03785 [0.035293, 0.040585] |
| square | SU2 | 0.43635 [0.42949, 0.44323] | 0.47765 [0.47073, 0.48458] |
| square | SU3 | 0.01545 [0.013831, 0.017255] | 5e-05 [8.8263e-06, 0.00028319] |
| honeycomb | U1 | 0.0246 [0.022543, 0.02684] | 0.00025 [0.00010679, 0.00058515] |
| honeycomb | SU2 | 0.26325 [0.25719, 0.2694] | 0.24705 [0.24112, 0.25308] |
| honeycomb | SU3 | 0.00155 [0.0010922, 0.0021992] | 0 [0, 0.00019204] |

## Status

The [combined figure delivery audit](../results/a8-overview-delivery-audit.json) verifies one report image and one active LER result with the requested red size palette.

The current LER presentation is one 3×2 figure: Square left, Honeycomb right; U(1), SU(2), SU(3) top to bottom. All panels share x and use independent y scales. Four red shades darken with L=5,7,9,11; one external legend identifies the sizes, with no p=0 marker or legend entry. Figure L006.11.7 replaces the retired standalone Figures L006.11.1–L006.11.6; their PNGs have been removed.

All six curves are complete: 600 sampled cells and 12,000,000 shots, excluding exact endpoints. The [rendered delivery audit](../results/a8-delivery-audit-2026-09-07.json) records the earlier standalone-figure delivery; its presentation is superseded by the combined figure. The [combined-figure render record](../results/a8-ler-overview-render.json) identifies the six unchanged inputs and current panel layout. The [count and figure audit](../results/a8-completion-audit-2026-09-07.json) verifies the grid, Wilson intervals, seed schedule, source stability for new cells, and preservation of inherited counts. Forty
inherited corrected cells were retained with immutable pre-resume copies;
those files lack historical source hashes. New cells record their seed,
batch size, completion time, and frozen source hashes. The
[resume preflight](../results/a8-resume-preflight-2026-09-07.json) checks exact
legacy/optimized equality for all six full-record arms. Scheduling whole cells
preserves the registered RNG stream and does not split or reseed shots.

A logical failure means the final correction has nonzero measured syndrome
residual or nontrivial residual logical parity. BP nonconvergence never gates
LER. The earlier union-of-nonconvergence-and-failure aggregates are invalid
and cannot support a threshold or group comparison. No threshold fit is part
of this acquisition delivery; any apparent finite-size crossing needs further
analysis with the companion numerical diagnostics.

## Related pages

- [Method overview](overview.md)
- [Scoring correction](a8-ler-scoring-correction-2026-09-05.md)

- [Final group/orientation interpretation](interpretation.md)
