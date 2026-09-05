---
title: 'R6V Stage-1 checkpoint 001 — D4-native X-only flux scan'
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

# R6V Stage-1 checkpoint 001 — D4-native X-only flux scan

This is an in-progress, single-cell checkpoint, not a threshold estimate.
All policies use the same 1,000 D4 trajectories at `L=5`, `p_X=0.14`, with
`p_Z=0` and flux recovery only. No terminal physical-winding trajectory
occurred in this cell.

| policy | flux logical failures / 1000 | conditional flux failure |
| --- | ---: | ---: |
| O0 unit-weight MWPM | 152 | 0.152 |
| O2 published herald-weight MWPM | 14 | 0.014 |
| BP posterior-LLR -> MWPM, 40-step default | 0 | 0.000 |

Matched contrasts: O2 improves over O0 on 142 records and regresses on 4;
BP improves over O0 on 152 and regresses on 0; BP improves over O2 on 14 and
regresses on 0.

The BP numerical diagnostic reports 903/1000 fixed-point flags at the chosen
tolerance, 97/1000 non-flags, mean 26.924 iterations, and median final
message delta `6.476e-9`. Since MWPM consumes the finite final BP weights,
the primary result is the finite-iterate decoder outcome above. The upcoming
matched 40-versus-160-step replay will test whether these finite-iterate
outcomes are iteration-budget stable; it must not run concurrently with the
large scan merely to avoid delaying its primary allocation.

