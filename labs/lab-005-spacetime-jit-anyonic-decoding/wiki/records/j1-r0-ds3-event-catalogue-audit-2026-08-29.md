---
title: 'R0 D(S3) source-event catalogue audit'
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

# R0 D(S3) source-event catalogue audit

Date: 2026-08-29

## Outcome

R0 yields a **localized source gap**, not a completed D(S3) circuit
reproduction.

The archived Lyons–Brown paper specifies several detector relations exactly at
stabilizer level:

- a false `S_i(t)` readout produces `D_i(t)` and `D_i(t+1)`;
- boundary `mu` detectors follow Eq. (34);
- boundary `e/m` detectors follow Eq. (35); and
- `eta` has no detector spanning the D(S3)–D(Z3) boundary.

It also supplies the coarse-grained bound that a local circuit fault occupies a
unit cube and its syndrome lies in the fault's 1-neighborhood. This is enough
for the theorem's cluster argument, but it is not an exact gate-level event
catalogue.

## Blocking details

Three maps needed for numerical source reproduction are not fully specified in
the archived paper:

1. gate-level D(S3) stabilizer-extraction faults to exact detector indices;
2. a complete primitive-fault table through ungauging, the D(Z3) waiting
   interval, and re-gauging; and
3. an index-level detector adjustment for arbitrary known computational-anyon
   motion.

The structured catalogue marks these rows `coarse_grained_bound_only` or
`known_motion_not_fault`. It does not fill them using D4 fusion labels or the G
phenomenological channel. Four focused fixtures verify citations, phase
ownership, source locality, explicit unresolved status, motion separation, and
absence of D4 herald data.

Machine-readable result:
[`j1-r0-ds3-event-catalogue-audit-2026-08-29.json`](../../results/j1-r0-ds3-event-catalogue-audit-2026-08-29.json).

## Claim boundary

The stabilizer-level detector identities and locality bounds are source-backed.
An exact microscopic D(S3) circuit-noise generator is not yet reproducible from
the archived paper alone. The abstract schedule, absorber, and phase-lifecycle
fixtures remain valid at their previously stated interface level.

