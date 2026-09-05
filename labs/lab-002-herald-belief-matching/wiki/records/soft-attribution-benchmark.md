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
> MWPM. Do not cite their LER, disagreement, rescue/harm, McNemar, or
> effective-error values. Static-prior MWPM and BP-only posterior scores,
> convergence, and runtime remain provenance. See
> [the field-level invalidation manifest](negative-log-invalidation.md).

Generated `2026-08-26T21:37:01.367531+00:00` with PyMatching `2.3.1` and seed `260826`.

`mwpm` is static-prior syndrome-only PyMatching. `syndrome_bp_mwpm` applies BP without herald factors, while `herald_bp_mwpm` includes the fusion-remnant herald likelihood before calling PyMatching. Matching itself is never reimplemented. Edge log loss and Brier score evaluate the soft posterior against simulator truth; logical error is the primary decoder outcome.

| Lattice | L | p | q | Decoder | Logical error rate | 95% CI | Disagree with MWPM | Mean ms/shot | BP convergence |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| square | 5 | 0.060 | 0.75 | mwpm | 0.0600 | [0.0278, 0.1248] | 0.0000 | 0.036 | — |
| square | 5 | 0.060 | 0.75 | syndrome_bp_mwpm | 0.0700 | [0.0343, 0.1375] | 0.0300 | 71.824 | 87.0% |
| square | 5 | 0.060 | 0.75 | herald_bp_mwpm | 0.0600 | [0.0278, 0.1248] | 0.0200 | 62.963 | 93.0% |
| square | 5 | 0.100 | 0.75 | mwpm | 0.1100 | [0.0625, 0.1863] | 0.0000 | 0.029 | — |
| square | 5 | 0.100 | 0.75 | syndrome_bp_mwpm | 0.1400 | [0.0853, 0.2214] | 0.0900 | 81.757 | 61.0% |
| square | 5 | 0.100 | 0.75 | herald_bp_mwpm | 0.0500 | [0.0215, 0.1118] | 0.1200 | 69.017 | 73.0% |
| honeycomb | 5 | 0.060 | 0.75 | mwpm | 0.0100 | [0.0018, 0.0545] | 0.0000 | 0.069 | — |
| honeycomb | 5 | 0.060 | 0.75 | syndrome_bp_mwpm | 0.0100 | [0.0018, 0.0545] | 0.0000 | 207.256 | 84.0% |
| honeycomb | 5 | 0.060 | 0.75 | herald_bp_mwpm | 0.0100 | [0.0018, 0.0545] | 0.0000 | 159.543 | 97.0% |
| honeycomb | 5 | 0.100 | 0.75 | mwpm | 0.0400 | [0.0157, 0.0984] | 0.0000 | 0.054 | — |
| honeycomb | 5 | 0.100 | 0.75 | syndrome_bp_mwpm | 0.0400 | [0.0157, 0.0984] | 0.0000 | 323.351 | 38.0% |
| honeycomb | 5 | 0.100 | 0.75 | herald_bp_mwpm | 0.0000 | [0.0000, 0.0370] | 0.0400 | 247.875 | 81.0% |

## Small-graph exact posterior checks

- square L=3 (8 edges, 20 shots): MWPM=0.3500, herald BP+MWPM=0.3500, exact logical MAP=0.1500; mean BP edge-marginal MAE=5.492e-10.
- honeycomb L=2 (11 edges, 20 shots): MWPM=0.0500, herald BP+MWPM=0.0500, exact logical MAP=0.0000; mean BP edge-marginal MAE=2.343e-10.

## Paired attribution

- square L=5 p=0.060: syndrome_bp_mwpm versus mwpm rescued 1 failures and introduced 2 (paired LER delta +0.0100, exact McNemar p=1).
- square L=5 p=0.060: herald_bp_mwpm versus syndrome_bp_mwpm rescued 1 failures and introduced 0 (paired LER delta -0.0100, exact McNemar p=1).
- square L=5 p=0.060: herald_bp_mwpm versus mwpm rescued 1 failures and introduced 1 (paired LER delta +0.0000, exact McNemar p=1).
- square L=5 p=0.100: syndrome_bp_mwpm versus mwpm rescued 3 failures and introduced 6 (paired LER delta +0.0300, exact McNemar p=0.5078).
- square L=5 p=0.100: herald_bp_mwpm versus syndrome_bp_mwpm rescued 11 failures and introduced 2 (paired LER delta -0.0900, exact McNemar p=0.02246).
- square L=5 p=0.100: herald_bp_mwpm versus mwpm rescued 9 failures and introduced 3 (paired LER delta -0.0600, exact McNemar p=0.146).
- honeycomb L=5 p=0.060: syndrome_bp_mwpm versus mwpm rescued 0 failures and introduced 0 (paired LER delta +0.0000, exact McNemar p=1).
- honeycomb L=5 p=0.060: herald_bp_mwpm versus syndrome_bp_mwpm rescued 0 failures and introduced 0 (paired LER delta +0.0000, exact McNemar p=1).
- honeycomb L=5 p=0.060: herald_bp_mwpm versus mwpm rescued 0 failures and introduced 0 (paired LER delta +0.0000, exact McNemar p=1).
- honeycomb L=5 p=0.100: syndrome_bp_mwpm versus mwpm rescued 0 failures and introduced 0 (paired LER delta +0.0000, exact McNemar p=1).
- honeycomb L=5 p=0.100: herald_bp_mwpm versus syndrome_bp_mwpm rescued 4 failures and introduced 0 (paired LER delta -0.0400, exact McNemar p=0.125).
- honeycomb L=5 p=0.100: herald_bp_mwpm versus mwpm rescued 4 failures and introduced 0 (paired LER delta -0.0400, exact McNemar p=0.125).

These are finite-shot implementation benchmarks, not a threshold estimate. The exact oracle is restricted to tiny graphs and predicts the logical class, so it is the accuracy reference rather than another scalable decoder.


## Operational effective physical error

- square L=5 at p=0.060: p_eff 0.0600 (reduction 0.0000).
- square L=5 at p=0.100: p_eff < 0.06.
- honeycomb L=5 at p=0.060: p_eff 0.0600 (reduction 0.0000).
- honeycomb L=5 at p=0.100: p_eff < 0.06.

