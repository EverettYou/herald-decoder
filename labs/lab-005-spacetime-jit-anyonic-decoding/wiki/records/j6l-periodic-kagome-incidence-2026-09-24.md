---
title: Periodic kagome incidence completion of the D4 honeycomb
status: current
updated: 2026-09-24
record: true
---

## Summary

The paper-normalized periodic `L=2` blue/green honeycomb admits an exact
three-color kagome incidence completion. This maps every existing red error
edge to a unique physical red qubit and embeds the complete local 12-qubit
star supports. It is a combinatorial result, not a prepared D4 state or a
two-round measurement instrument.

## Evidence

The [preregistered contract](../../manifests/j6l-periodic-kagome-incidence-2026-09-24.json),
[runner](../../scripts/run_j6l_periodic_kagome_incidence.py), and
[machine-readable support map](../../results/j6l-periodic-kagome-incidence-2026-09-24.json)
pin Jing Appendix A.1/C.1, Iqbal Fig. 2, the Lab 004 geometry/cycle code,
and the preceding single-star result. Twelve distinct contractible hexagons
of the 24-vertex/36-edge honeycomb become red star centers. Every existing
edge borders exactly two faces; every blue/green center belongs to exactly
three faces. Face completion produces 12 centers of each color and 36 physical
qubits of each color, or 36 stars and 108 qubits in total, agreeing with the
source's nine-star/27-qubit unit cell at `L=2`.

Every star has six alternating-color inner-ring qubits, six outer X qubits of
its own color, six adjacent inner-ring CZ pairs, and two disjoint three-qubit
color triangles. Each qubit belongs to two inner rings at its endpoint stars
and two same-color outer supports. The 36 red physical qubits preserve Lab
004's edge IDs exactly. All 36 single-red-edge boundaries and one fixed
two-edge boundary agree with the existing honeycomb incidence. A representative
blue star maps the two previously checked red-error pairs to edge IDs
`[2,1]` and `[2,0]`, retaining the exact local green-Z dressing patterns.

## Status

The registered incidence matrix passes with no stochastic histories,
schedule-arm evaluations, or bootstrap replicates. The support map has not
yet verified neighboring noncommuting star relations, constructed a common
ground state, applied sequential projectors, or produced the action- and
first-record-conditioned public second observation. Those are the next
physical-state gates; five-round performance sampling remains frozen.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6k-full-local-star-action-algebra-2026-09-24|Single-star algebra]] · [[records/index|Research-record index]]
