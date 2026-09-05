---
title: 'R6D nonnegative local edge-flow identity'
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

# R6D nonnegative local edge-flow identity

## Purpose

This note records the mathematical reason for the R6D factorization before it
is used by a decoder. It is a project-derived identity for the validated
Eq. A12 likelihood, not a formula attributed to Jing et al.

Let `E_e in {0,1}` denote a candidate physical edge string and let
`d_v(E)` be its selected degree at vertex `v`. For each charge colour `c`,
introduce one binary auxiliary variable `a_e^c` on every physical edge.

The fixed local factors are:

1. An edge-pin factor `A_e(E_e,a_e^c)` equal to one when `E_e=1`, equal to
   `1[a_e^c=0]` when `E_e=0`, and zero otherwise.
2. A vertex factor depending on the three incident physical-edge bits, their
   three auxiliary bits, and the public charge bit. If `d_v(E)=2`, it is the
   indicator that the XOR of the two selected auxiliary bits equals the public
   charge at `v` when `v` has colour `c`, and equals zero for the other colour.
   If `d_v(E) != 2`, its value is `2^{-d_v(E)/2}` and it imposes no relation
   among selected auxiliary bits.

All factor values are nonnegative. Unselected auxiliary bits are pinned, so
they introduce no multiplicity.

## Proposition

For one charge colour, summing the product of these local factors over all
auxiliary edge bits gives one for every selected connected component that is
not an isolated degree-two loop. An isolated degree-two loop gives two when
the observed same-colour charge parity is even and zero when it is odd.

## Proof

Consider a connected component containing at least one vertex of degree other
than two. Cut the component at every such vertex. Its selected edges partition
into maximal chains whose internal vertices all have degree two; a chain may
begin and end at two incidences of the same cut vertex.

Along one chain, the degree-two XOR equations determine every auxiliary bit
from the bit on one chosen edge. There are therefore exactly two assignments,
independent of the charge values on that open chain. Every chain has two end
incidences at degree-not-two vertices. Multiplying their normalization factors
over the whole component gives

`2^{-sum_{v:d_v!=2} d_v/2} = 2^{-number_of_chains}`,

because the degree sum counts two end incidences per chain. The two assignments
per chain cancel this normalization exactly, so the component contributes one.

If every vertex in the component has degree two, the component is a cycle and
has no normalization factors. Propagating one chosen auxiliary bit around the
cycle is consistent exactly when the XOR of the local right-hand sides is
zero, which is the even same-colour charge-parity condition. When consistent,
the initial bit is free and gives two assignments; when inconsistent, there
are none. This proves the proposition.

The blue and green auxiliary sums are independent. Their product is therefore
four for an allowed closed component and zero if either colour parity is odd,
exactly reproducing the two D4 parity multipliers. Multiplication by the
already-validated local support weight `2^{-N_2}` gives the ordinary
nonwinding Eq. A12 candidate likelihood.

## Audit history and limitations

The first R6D derivation used vertex spins and charge characters. It is exact,
but the character `z_v^{q_v}` can be negative; hence it is a signed tensor
network rather than a probability factor graph. It remains useful as an
independent Fourier control but is not the BP-facing representation.

The edge-flow construction above is nonnegative and has binary domains,
`O(V+E)` variables and factors, edge-pin arity two, and vertex scope at most
seven when the public charge bit is counted. Direct enumeration of all 4,096
primitive edge-flow assignments per colour agrees with analytic contraction on
69 registered controls. The complete primitive and paper-`L=2` exactness
matrices also pass.

This proof does not localize the ground-state-relative winding-sector terminal
test. It also proves neither loopy-BP exactness nor convergence, runtime,
correction quality, logical error rate, threshold, or fault tolerance.

