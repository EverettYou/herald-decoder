---
title: 'Jing–Sala–Jiang–Verresen decoder-method audit'
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

# Jing–Sala–Jiang–Verresen decoder-method audit

Source: *Intrinsic Heralding and Optimal Decoders for Non-Abelian Topological Order* (2025).

## Model facts relevant to reproduction

- The non-Abelian D4 charge `[2]` obeys `[2] x [2] = 1 + s1 + s2 + s3`; `[2]` is absent from its own two-particle fusion outcomes.
- Errors create `[2]` pairs on honeycomb-lattice edges. The measured record contains the surviving non-Abelian endpoint syndrome and intermediate Abelian fusion products represented by `e_B/e_G` information.
- For an allowed syndrome, the appendix gives a closed-form conditional likelihood of the form `P(s | E) = 2^(C + Y + |m|/2 - |E|)` with support restricted by endpoint and parity/compatibility constraints. Symbols and conventions must be copied into R1 tests before implementation claims.

## Algorithms actually used

### Unheralded practical baseline

PyMatching MWPM with unit edge weights. Reported threshold: `p_c = 0.15860(1)`.

### Intrinsically heralded practical decoder

PyMatching with

`w_e = 1 - n_e K`, where `n_e` counts adjacent measured intermediate Abelian charges and `K = 27 L^2`.

The large negative contribution makes a correction containing the heralded structure favorable. Reported threshold: `p_c = 0.20842(2)`.

### Conditioned optimal decoder

Choose the logical sector maximizing

`P(h | s) proportional to sum_{E in h} P(s | E) P(E)`.

The paper evaluates this object through a statistical-mechanics mapping, Metropolis Monte Carlo, and Binder-cumulant finite-size analysis. Reported threshold: `p_c = 0.218(1)`.

## What is not in the paper

The PDF contains no ILP/MILP implementation of the D4 `[2]` benchmark. A more general case—where the error anyon can occur among its own fusion outcomes—produces a Steiner minimum-tree problem. That motivates a possible project MILP oracle, but the paper marks the corresponding numerical/statistical-mechanics problem as open.

Efficient sampling of the full optimal arbitrary-Pauli model is also presented as open.

## Numerical scale reported by the paper

- Practical MWPM study: even `L = 10, 12, ..., 28`, roughly `10^6` error configurations per point, and `p` increments of `0.001` near threshold.
- Optimal Monte Carlo study: small sizes around `L = 3, 4, 5, 6` with substantial disorder averaging and equilibration/sampling sweeps.

These budgets are source facts, not authorization to reproduce them immediately.

## Reproduction hazards

1. Negative matching weights can change closed-cycle and tie behavior; PyMatching semantics require an exhaustive small-graph audit.
2. Endpoint consistency alone is insufficient; intermediate fusion products impose parity/compatibility constraints.
3. D4 logical failure includes the relevant two-step flux/charge structure and must not be reduced to a single phenomenological bit without proof.
4. A constrained minimum-weight explanation is not the same as the conditioned posterior sum over a homology sector.
5. Threshold agreement is meaningless until lattice conventions, logical operators, record support, and likelihood normalization are independently tested.
6. The first red-X correction changes the parity support of a later e-charge
   measurement. A full exact benchmark is therefore a sequential policy, and
   simulator relation metadata cannot be promoted to a decoder-visible record.

