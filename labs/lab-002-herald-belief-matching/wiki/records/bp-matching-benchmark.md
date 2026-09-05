---
title: 'BP + PyMatching benchmark'
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

# BP + PyMatching benchmark

> **INVALIDATED LOGICAL RESULTS — 2026-08-27.** The reweighted BP+MWPM
> logical fields below used `-log P(error)` instead of the LLR required by
> MWPM. Do not cite their LER, disagreement, rescue/harm, or effective-error
> values. Static-prior MWPM and BP-only posterior/convergence/runtime fields
> remain provenance. See [the field-level invalidation manifest](negative-log-invalidation.md).

Generated `2026-08-26T20:41:37.191211+00:00` with PyMatching `2.3.1` and seed `1001`.

`mwpm` is static-prior syndrome-only PyMatching. `syndrome_bp_mwpm` applies BP without herald factors, while `herald_bp_mwpm` includes the fusion-remnant herald likelihood before calling PyMatching. Matching itself is never reimplemented.

| Lattice | L | p | q | Decoder | Logical error rate | 95% CI | Disagree with MWPM | Mean ms/shot | BP convergence |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| square | 5 | 0.060 | 0.75 | mwpm | 0.0750 | [0.0460, 0.1200] | 0.0000 | 0.030 | — |
| square | 5 | 0.060 | 0.75 | syndrome_bp_mwpm | 0.0950 | [0.0617, 0.1436] | 0.0500 | 83.112 | 80.0% |
| square | 5 | 0.060 | 0.75 | herald_bp_mwpm | 0.0600 | [0.0347, 0.1019] | 0.0850 | 69.470 | 85.5% |
| square | 5 | 0.100 | 0.75 | mwpm | 0.1650 | [0.1200, 0.2227] | 0.0000 | 0.040 | — |
| square | 5 | 0.100 | 0.75 | syndrome_bp_mwpm | 0.1900 | [0.1417, 0.2500] | 0.0850 | 120.315 | 56.5% |
| square | 5 | 0.100 | 0.75 | herald_bp_mwpm | 0.1250 | [0.0861, 0.1780] | 0.1500 | 101.880 | 75.5% |
| honeycomb | 5 | 0.060 | 0.75 | mwpm | 0.0050 | [0.0009, 0.0278] | 0.0000 | 0.078 | — |
| honeycomb | 5 | 0.060 | 0.75 | syndrome_bp_mwpm | 0.0050 | [0.0009, 0.0278] | 0.0000 | 394.906 | 78.5% |
| honeycomb | 5 | 0.060 | 0.75 | herald_bp_mwpm | 0.0000 | [0.0000, 0.0188] | 0.0050 | 270.640 | 96.5% |
| honeycomb | 5 | 0.100 | 0.75 | mwpm | 0.0600 | [0.0347, 0.1019] | 0.0000 | 0.103 | — |
| honeycomb | 5 | 0.100 | 0.75 | syndrome_bp_mwpm | 0.0600 | [0.0347, 0.1019] | 0.0000 | 423.416 | 26.0% |
| honeycomb | 5 | 0.100 | 0.75 | herald_bp_mwpm | 0.0100 | [0.0027, 0.0357] | 0.0500 | 361.732 | 80.5% |

## Small-graph exact posterior checks

- square L=3 (8 edges, 200 shots): MWPM=0.2850, herald BP+MWPM=0.2850, exact logical MAP=0.2550; mean BP edge-marginal MAE=4.414e-10.
- honeycomb L=2 (11 edges, 200 shots): MWPM=0.1200, herald BP+MWPM=0.0750, exact logical MAP=0.0700; mean BP edge-marginal MAE=2.161e-10.

These are finite-shot implementation benchmarks, not a threshold estimate. The exact oracle is restricted to tiny graphs and predicts the logical class, so it is the accuracy reference rather than another scalable decoder.

