---
title: 'R4.5c corrected sequential-policy audit'
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

# R4.5c corrected sequential-policy audit

Status: **corrected_sequential_policy_audited**.

## Exact primitive policy risks

Risks below are conditioned on the source-frozen nonwinding initial channel. Terminal physical-winding mass and full risks are retained in the machine-readable result.

| p | layer | public fixed | public first + exact | myopic first + exact | future-aware exact | public excess | myopia cost |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 0.10 | O0 | 0.163554 | 0.141617 | 0.136656 | 0.136655 | 0.026899 | 0.000001 |
| 0.10 | O2 | 0.130871 | 0.096470 | 0.048176 | 0.048176 | 0.082695 | 0.000000 |
| 0.30 | O0 | 0.720907 | 0.648485 | 0.633362 | 0.633337 | 0.087570 | 0.000025 |
| 0.30 | O2 | 0.640124 | 0.515937 | 0.302868 | 0.302868 | 0.337255 | 0.000000 |
| 0.50 | O0 | 0.943458 | 0.893952 | 0.893563 | 0.892013 | 0.051445 | 0.001550 |
| 0.50 | O2 | 0.923306 | 0.843532 | 0.669975 | 0.669000 | 0.254306 | 0.000975 |
| 0.60 | O0 | 0.973254 | 0.942371 | 0.942190 | 0.941961 | 0.031293 | 0.000229 |
| 0.60 | O2 | 0.973877 | 0.933277 | 0.824079 | 0.824079 | 0.149799 | 0.000000 |

## Decomposition and first-action changes

- p=0.10: exact O0-minus-O2 information gain `0.088479`; future/public first-action disagreement O0/O2 `0.079837` / `0.286830`; future/myopic disagreement `0.003217` / `0.000000`.
- p=0.30: exact O0-minus-O2 information gain `0.330468`; future/public first-action disagreement O0/O2 `0.382234` / `0.707856`; future/myopic disagreement `0.014649` / `0.000000`.
- p=0.50: exact O0-minus-O2 information gain `0.223013`; future/public first-action disagreement O0/O2 `0.417820` / `0.880388`; future/myopic disagreement `0.233577` / `0.027939`.
- p=0.60: exact O0-minus-O2 information gain `0.117882`; future/public first-action disagreement O0/O2 `0.437520` / `0.925031`; future/myopic disagreement `0.115906` / `0.000000`.

## Validation

Maximum channel, action-branch, O0/O2 marginalization, and global-normalization errors are `0.000e+00`, `1.388e-15`, `1.388e-15`, and `6.439e-14`.

Maximum registered within-layer risk-order violation is `0.000e+00`; maximum O2-versus-O0 exact-information ordering violation is `0.000e+00`. Decoder truth inputs: `[]`.

## Claim boundary

Exact primitive L=2 noiseless sequential-policy audit under the registered observation model. It is not an LER, threshold, larger-lattice, noisy-measurement, fault-tolerance, or scalable-optimality result.

