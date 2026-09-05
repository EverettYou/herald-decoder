---
title: 'R6V: finite-iteration stability, not a fixed-point gate'
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

# R6V: finite-iteration stability, not a fixed-point gate

For the composite decoder `BP posterior-LLR -> MWPM`, a BP fixed-point flag is
not a validity condition.  MWPM always receives finite weights and produces a
syndrome-consistent correction.  The scientific question is instead whether a
larger BP budget changes decoder-visible weights enough to change the matching
correction or the flux logical-loss score.

The existing matched, deliberately high-nonconvergence R6U cohort contains 12
records (six each at `(L,p_X)=(9,.22)` and `(13,.22)`).  Comparing 40 with 160
BP iterations at the same damping changes the fixed-point flag on 3/12
records and changes the MWPM correction on 1/12 records, but changes the flux
logical score on 0/12.  Comparing the two 160-iteration damping schedules
changes the correction on 5/12 records, but again changes the flux logical
score on 0/12.  The logical-score counts are 0/12 for all three schedules;
the BP-versus-O2 comparison is 4 improvements and 0 regressions for all three.

This is evidence of output robustness on a selected, small stress cohort.  It
is not a proof of asymptotic fixed-point convergence, nor a full-curve LER
stability measurement.  R6V Stage 1 therefore treats finite final iterates as
the primary decoder definition.  It records convergence only as a diagnostic.
The next acceptance test is a matched default-versus-160-iteration comparison
on the Stage-1 trajectories: report correction disagreement and paired flux
logical-score disagreement per `(L,p_X)`, together with LER intervals.  A
threshold claim depends on the finite-size curves and their uncertainty, not
on requiring BP convergence.

