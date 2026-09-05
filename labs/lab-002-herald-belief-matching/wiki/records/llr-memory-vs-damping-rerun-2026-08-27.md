---
title: 'Matched BP-update A/B'
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

# Matched BP-update A/B

Generated `2026-08-27T15:40:12.584216+00:00` with 100 matched shots per seed and seeds `[281001, 281002, 281003]`. Both arms use posterior-LLR weights and the same PyMatching backend.

| Lattice | Scope | Arm | Errors/shots | LER (95% Wilson CI) | Log loss | Brier | Converged | Iterations | Mean ms |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| square | pooled | legacy_damped | 31/300 | 0.1033 [0.0738, 0.1429] | 0.0983 | 0.0284 | 77.3% | 29.48 | 4.81 |
| square | pooled | memory_assisted | 35/300 | 0.1167 [0.0851, 0.1579] | 0.1875 | 0.0337 | 0.0% | 85.16 | 33.54 |
| square | seed 281001 | legacy_damped | 12/100 | 0.1200 [0.0700, 0.1981] | 0.0926 | 0.0272 | 78.0% | 29.94 | 6.85 |
| square | seed 281001 | memory_assisted | 13/100 | 0.1300 [0.0776, 0.2098] | 0.1126 | 0.0315 | 0.0% | 85.78 | 15.22 |
| square | seed 281002 | legacy_damped | 10/100 | 0.1000 [0.0552, 0.1744] | 0.0996 | 0.0293 | 74.0% | 29.81 | 3.57 |
| square | seed 281002 | memory_assisted | 12/100 | 0.1200 [0.0700, 0.1981] | 0.2438 | 0.0366 | 0.0% | 87.86 | 32.46 |
| square | seed 281003 | legacy_damped | 9/100 | 0.0900 [0.0481, 0.1623] | 0.1027 | 0.0287 | 80.0% | 28.69 | 4.02 |
| square | seed 281003 | memory_assisted | 10/100 | 0.1000 [0.0552, 0.1744] | 0.2061 | 0.0330 | 0.0% | 81.85 | 52.92 |

- **square pooled:** memory-assisted rescued 5 legacy failures and introduced 9; LER delta +0.0133; exact McNemar p=0.424.
  Paired soft deltas (new minus old): log loss +0.08923 (bootstrap 95% CI [0.04309226898563795, 0.13970255123527536]), Brier +0.00534 (bootstrap 95% CI [0.002757759011614203, 0.008113863218042907]).

| honeycomb | pooled | legacy_damped | 1/300 | 0.0033 [0.0006, 0.0186] | 0.0181 | 0.0056 | 78.3% | 32.28 | 2.01 |
| honeycomb | pooled | memory_assisted | 1/300 | 0.0033 [0.0006, 0.0186] | 0.0754 | 0.0067 | 0.0% | 76.99 | 40.10 |
| honeycomb | seed 281001 | legacy_damped | 0/100 | 0.0000 [0.0000, 0.0370] | 0.0174 | 0.0055 | 77.0% | 32.45 | 2.87 |
| honeycomb | seed 281001 | memory_assisted | 0/100 | 0.0000 [0.0000, 0.0370] | 0.0616 | 0.0063 | 0.0% | 76.18 | 60.61 |
| honeycomb | seed 281002 | legacy_damped | 1/100 | 0.0100 [0.0018, 0.0545] | 0.0169 | 0.0053 | 74.0% | 32.67 | 1.85 |
| honeycomb | seed 281002 | memory_assisted | 1/100 | 0.0100 [0.0018, 0.0545] | 0.0788 | 0.0062 | 0.0% | 76.00 | 32.54 |
| honeycomb | seed 281003 | legacy_damped | 0/100 | 0.0000 [0.0000, 0.0370] | 0.0200 | 0.0061 | 84.0% | 31.71 | 1.29 |
| honeycomb | seed 281003 | memory_assisted | 0/100 | 0.0000 [0.0000, 0.0370] | 0.0860 | 0.0075 | 0.0% | 78.79 | 27.16 |

- **honeycomb pooled:** memory-assisted rescued 0 legacy failures and introduced 0; LER delta +0.0000; exact McNemar p=1.
  Paired soft deltas (new minus old): log loss +0.05732 (bootstrap 95% CI [0.022411705629567857, 0.0997018996020535]), Brier +0.00104 (bootstrap 95% CI [-6.309113255296904e-05, 0.002310739135515772]).

## Evidence boundary

This is a finite-size, two-cell implementation A/B, not a threshold estimate. The selected memory-search candidate is ranked only from the observed factor model; simulator truth is used only after decoding for evaluation. Runtime includes BP, per-shot matching-graph construction, and PyMatching decode.

