---
title: 'Lyons–Brown just-in-time decoding method audit'
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

# Lyons–Brown just-in-time decoding method audit

Source: *Quantum computing with anyons is fault tolerant* (2026), Anasuya Lyons and Benjamin J. Brown.

## Problem identified by the paper

Anyonic error correction has two competing timing hazards. Correct too slowly and erroneous anyons can hide later syndrome information or interact with moving computational anyons. Correct too quickly and a false measurement can trigger a damaging fusion/correction. Fault tolerance therefore requires an online schedule, not only a spatial decoder.

## Spacetime observation

- Stabilizers are repeatedly measured at discrete times.
- A detector compares adjacent rounds, schematically `D_i(t) = S_i(t) - S_i(t-1)` in the paper's notation.
- A physical fault produces a spatial string whose endpoints are detector events in one time slice.
- A measurement fault produces a time-directed string with detector events in adjacent rounds.
- Detector definitions are adjusted for known computational-anyon positions and motion.

## JIT state machine

At each time `T`, the decoder uses only detector history up to `T`.

1. Track clusters of excitations/detector events.
2. Defer a cluster containing events too young relative to its size/separation/nearest absorber; attempt correction only when all relevant events are old enough.
3. Reverse/update the most recent measurement outcome for a deferred event, effectively moving it into the next time step.
4. For attempted clusters, account for whether the cluster is in D(S3), in an ungauged D(Z3) region, or at their boundary.
5. Ungauge to reveal hidden fusion information. Correct a neutral cluster; defer a non-neutral cluster because it belongs to a larger cluster not yet identified.
6. Re-gauge after correction and continue online.

The schedule creates absorbing regions and permits controlled linking of smaller clusters to larger ones. The proof bounds cluster lifetime and spatial spread using a recursive chunk decomposition.

## Result and its limit

The paper proves that, for sufficiently weak local circuit noise, logical failure can be suppressed exponentially with system size while universal D(S3) anyonic computation proceeds. It does not report a ready-to-reproduce numerical threshold value or a benchmark implementation.

The proof assumes a local spacetime circuit-noise model and uses gauging/ungauging properties specific to the D(S3) construction. Its JIT rule is therefore not automatically a decoder for the project's D4 intrinsic-herald model.

## Project extension

Lab 005 will add explicit noisy fusion/herald observations as a second repeated record. This extension must specify false-positive, false-negative, and outcome-confusion channels and must compare causal schedules on identical fault histories. Lab 004 supplies spatial D4 decoders only after a D4 spacetime translation is derived.

## Reproduction hazards

1. Accidentally using future detector events converts the online decoder into an offline oracle.
2. A static readout-flip model misses the time-directed detector strings central to measurement noise.
3. Cluster age, absorber distance, and boundary state are all part of the commit predicate.
4. Reproducing the abstract schedule without gauging/ungauging does not reproduce the complete correction protocol.
5. A schedule comparison is confounded unless every policy shares fault histories and inner-decoder semantics.

