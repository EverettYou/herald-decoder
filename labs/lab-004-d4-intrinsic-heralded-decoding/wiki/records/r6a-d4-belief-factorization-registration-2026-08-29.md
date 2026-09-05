---
title: 'R6A public D4 likelihood factorization registration'
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

# R6A public D4 likelihood factorization registration

## Why this gate comes before a decoder benchmark

R6 asks whether the scalable Lab 002 belief-matching method can consume the
validated D4 record. The current Lab 002 factor is not such an adapter: it
models a binary degree-threshold herald, whereas the D4 record has exact flux
boundary, degree-two charge support, and independent parity constraints. Using
the old factor would silently change the physical observation model.

The earliest unsupported step is therefore factor-graph expressibility. R6A
asks whether a truth-free factor graph can reproduce the exact D4 conditional
likelihood before BP, PyMatching, runtime, or logical performance is evaluated.

## Registered exact matrix

The complete primitive-size-2 oracle contains 4,096 physical masks, 16,230 distinct
nonwinding public observations, and 49,855 compatible observation/error pairs.
This fixture has 8 vertices and 12 edges. It is not the paper-normalized
`L=2` supercell, which has 24 vertices and 36 edges; exhaustive `2^36`
enumeration was never registered or run.
R6A runs three deterministic branches on that frozen support:

1. **F0 exact oracle** replays the validated likelihood and posterior as the
   control.
2. **F1 local support** encodes flux boundary and degree-two charge support but
   omits independent parity structure. It localizes whether support alone is
   sufficient.
3. **F2 support plus public parity auxiliaries** adds explicit parity factors
   constructed from the fixed lattice and public observation. It is accepted
   only if every oracle weight and zero-support decision agrees exactly.

The current binary degree-threshold factor is retained only as a structural
negative control because it changes the observation semantics. All registered
branches are cheap, reversible, and independently informative, so there is no
researcher ranking question.

## Gates and limits

Before the complete matrix, exact fixtures must cover vacuum, open string,
branch, trivial loop, winding terminal, parity violation, and hidden-field
rejection. Positive likelihoods must agree within (10^{-14}); posterior rows
must normalize at the four frozen R4.2 priors; and no public serialization may
contain the physical error, component decomposition, fusion history, or logical
sector.

The budget is ten CPU minutes, 2 GiB, and zero Monte Carlo samples. Failure of
F2 is a useful result: it means a D4 belief-matching adapter needs a richer
representation or an explicitly approximate likelihood. This registration
does not authorize BP performance, logical-error, scaling, threshold, or
fault-tolerance claims.

