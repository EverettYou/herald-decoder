---
title: 'R6D local auxiliary-spin factor audit'
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

# R6D local auxiliary-spin factor audit

## Result

The nonnegative local edge-flow graph matches all 49855 primitive compatible likelihoods and all 120 registered paper-`L=2` ambiguity probes with zero errors. A direct sum over all 4096 primitive edge-flow assignments per colour matches the analytic contraction on 69 checks. The independent signed vertex-spin Fourier representation also matches after summing all 256 spin assignments per colour on the same controls.

For each charge colour, every physical edge carries a binary auxiliary flow bit. An unselected edge pins it to zero. A degree-two vertex constrains the XOR of its two selected flow bits to the observed same-colour charge (or zero for the other colour); every other vertex contributes the nonnegative normalization `2^{-d/2}`. Cutting a non-cycle component at degree-not-two vertices produces maximal chains, each with two flow assignments and total endpoint normalization one half, so every chain contributes one. A pure loop has two assignments for even parity and none for odd parity. Multiplying the two colour partitions gives the D4 loop factor four without naming the loop.

## Fixed local graph

On paper-`L=2`, the representation uses 72 binary auxiliary edge-flow variables and 120 nonnegative factors, compared with the 1,068 simple-cycle factors required by R6C. Edge-pin factors have arity two; vertex factors have scope at most seven when the public charge bit is counted. Counts grow as `O(V+E)`, and no component label or simple-cycle catalog is supplied to a factor.

## Source and derivation boundary

Jing et al. provide the Eq. A12 likelihood and, in their optimal-threshold statistical-mechanics calculation, retain the nonlocal constraint count through a `2^C` reweighting and graph-search constraint check. The auxiliary-spin localization used here is a Lab 004 derivation independently checked against that exact likelihood; it is not presented as a formula from the paper.

The first vertex-spin derivation is exact but signed because a charge character can equal minus one; it is therefore retained only as an independent tensor-network control. The edge-flow construction is the nonnegative probability-factor representation released by this audit.

## Claim boundary

Exact fixed nonnegative bounded-arity local likelihood representation on the registered nonwinding matrix only. The ground-state-relative winding test remains a separate terminal gate. No BP convergence, polynomial-time decoding, correction, LER, threshold, or fault-tolerance claim is made.

