---
title: 'R1 local D4 support and likelihood core audit'
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

# R1 local D4 support and likelihood core audit

Date: 2026-08-28

## Implemented transition

The first R1 primitive now validates an externally specified error subgraph and independent parity-constraint list for the single-colour red-X channel of Jing *et al.* It enforces:

- the measured red m-flux syndrome equals the mod-2 boundary of the error subgraph;
- intermediate Abelian charge outcomes occur only at degree-two internal vertices;
- each supplied parity constraint references measured vertices and has the required parity;
- disallowed support or a violated constraint has zero conditional likelihood.

For an allowed observation with `N_internal` measured internal stars and `C` independent satisfied constraints, the implementation uses the first form of Appendix A Eq. A12,

`P(s | E) = 2^(C - N_internal)`.

This form follows directly from fair intermediate measurements with one dependent outcome per independent constraint and avoids prematurely relying on the geometry-specific rewrite involving error length, Y intersections, and flux count.

## Verification

Six focused tests pass:

1. a two-edge path has one fair internal measurement and its two outcomes sum to probability one;
2. a three-vertex closed loop with one even-parity constraint has four allowed outcomes, each with probability one quarter;
3. a parity violation has zero likelihood;
4. a flux syndrome different from `boundary(E)` has zero likelihood;
5. an intermediate measurement away from degree-two support is rejected;
6. a constraint referring to an unmeasured vertex is rejected.

Command: `python3 -m pytest -q labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_observation.py`

Result: `6 passed`.

## Claim boundary and next gate

This is a local likelihood/support core, not yet the periodic D4 observation generator. It accepts rather than constructs the independent constraint list. The next R1 gate is to construct the coloured periodic-honeycomb topology, identify non-branching homologically trivial loop constraints, and exhaustively compare the generated constraint rank and normalized observation distribution on tiny tori.

