---
title: 'R6V bounded BP nonconvergence sensitivity'
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

# R6V bounded BP nonconvergence sensitivity

Twelve regenerated, matched R6U records: six each from `(L,pX)=(9,.22)` and `(13,.22)`. Each cell has five default-nonconverged records plus one converged control. O2 is fixed; only BP damping/cap changes.

| BP schedule | converged / 12 | BP failures | BP improves vs O2 | BP regresses vs O2 |
| --- | ---: | ---: | ---: | ---: |
| A_default_d025_cap40 | 2 / 12 | 0 | 4 | 0 |
| B_extend_d025_cap160 | 5 / 12 | 0 | 4 | 0 |
| C_damp_d050_cap160 | 5 / 12 | 0 | 4 | 0 |

Default dense-template replay correction matches recorded R6U correction on all rows: `True`.
Default dense-template replay Boolean-union score matches recorded R6U score on all rows: `True`.

Interpretation is limited to whether the selected R6U decoder ordering changes under these bounded schedules; it does not establish a BP fixed-point solution or a threshold.

