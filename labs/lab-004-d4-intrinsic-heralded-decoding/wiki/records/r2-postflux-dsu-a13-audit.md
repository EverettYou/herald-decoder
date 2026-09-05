---
title: 'R2 post-flux DSU accumulation audit'
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

# R2 post-flux DSU accumulation audit

## Source fixture

Appendix A, Eqs. A13-A14, gives an explicit three-star stabilizer example. After a physical red-X string and its flux correction remove both m-fluxes, same-colour stars 1 and 3 are governed by one product stabilizer. Their second-round e-charge outcomes must be equal, equivalently their binary charge parity must be even. Appendix C states that the production simulation accumulated these post-flux constraints with a disjoint-set union data structure.

## Implemented prerequisite

`d4_postflux.py` implements the DSU accumulation layer independently of the lattice-orientation lookup. It accepts the active same-colour star measurements and explicit local entanglement pairs, computes transitive connected components, and applies one independent even charge-parity constraint per component. The charge-record schema is fail-closed: active vertices must be binary, inactive vertices must remain unmeasured (`-1`), and every relation endpoint must be active.

The named A13 fixture reproduces the source's exact result: outcomes `(0,0)` and `(1,1)` are allowed, while `(0,1)` and `(1,0)` are forbidden. Four new tests also verify transitive DSU closure, independent disconnected constraints, and schema rejection. The complete Lab 004 suite now passes 37 tests.

## Claim boundary

This verifies the constraint-accumulation algorithm and one exact stabilizer fixture. It does not yet translate every physical-error/correction orientation into the local entanglement pairs shown in Appendix A's seven-row table, nor does it construct effective blue/green Pauli-Z paths. Those geometry-specific rules remain the next prerequisite. Keeping them outside the DSU input until transcribed and tested prevents a visually inferred orientation convention from becoming an unstated decoder assumption.

