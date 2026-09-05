---
title: 'R6A public-input factor ledger and exact fixtures'
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

# R6A public-input factor ledger and exact fixtures

## Implemented gate

The first R6A implementation gate now passes. `d4_belief_factorization.py`
accepts one latent candidate edge assignment and only the public flux/charge
record. It evaluates two registered branches:

- F1 multiplies local flux-boundary, degree-two measurement-support, and fair
  charge-outcome factors.
- F2 adds the independent closed-loop parity multipliers required by the D4
  likelihood.

The public observation schema rejects physical-error, component, winding,
logical-sector, relation, and truth fields. Nontrivial winding candidates are
classified as terminal logical failures rather than assigned an ordinary BP
likelihood.

## Exact fixtures

All fixtures in this gate use the primitive periodic size-2 graph with 8
vertices and 12 edges. They are exact local/finite-support controls, not the
24-vertex, 36-edge paper-normalized `L=2` supercell.

Seven focused tests cover vacuum, an open two-edge path, a degree-three branch,
a homologically trivial loop, a parity violation, a winding loop, wrong local
support, and hidden-field rejection. The key discriminating loop has physical
mask 27328, six degree-two internal vertices, and two independent parity
constraints:

| branch | conditional weight |
|---|---:|
| F1 local support | 0.015625 |
| F2 support + parity | 0.0625 |
| exact oracle | 0.0625 |

Flipping one charge bit leaves F1 positive but makes F2 and the oracle zero.
Thus the fixtures already falsify support-only factorization and verify the
registered parity multiplier on a nontrivial exact case. Seven of seven focused
tests and all 137 Lab 004 tests pass. No random sample was generated.

## Important unresolved boundary

F2 currently constructs its parity scopes while evaluating a latent candidate.
That ledger is diagnostic-only: exposing those scopes to a decoder would leak
candidate component structure. The later complete primitive-size-2 matrix
found one-or-fewer scope signatures per public observation, but that finite
consistency result neither supplies a constructive rule nor tests the
paper-normalized `L=2` graph. This is not a released BP factor graph and no BP,
logical-performance, scaling, threshold, or fault-tolerance claim follows.

