---
title: 'R2 effective Pauli-Z and second-stage charge-recovery audit'
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

# R2 effective Pauli-Z and second-stage charge-recovery audit

Date: 2026-08-28

## Source contract

Appendix A states that once the physical/correction red-X union is homologically trivial, each blue and green post-flux e-charge component has even parity.  Any same-colour Pauli-Z configuration pairing those charges along the union is an acceptable effective error representative because all such configurations are homologically equivalent.  Appendix C then applies another shortest-string MWPM and declares a logical error when the symmetric difference between the effective Pauli-Z string and the correction contains a noncontractible loop.

## Construction

The second stage is implemented separately for blue and green charges.

1. Each colour's honeycomb stars form a periodic triangular lattice. Every opposite-colour center contributes the three edges among its three neighbors.
2. Production relations come from the connected physical/correction union invariant, not an assumed completion of the seven printed local diagrams. For each colour projection, a deterministic spanning forest pairs the measured odd vertices. Leaf elimination selects a subset of verified relation edges whose GF(2) boundary equals the measured e-charge syndrome. An odd component fails closed. A singleton colour projection is retained explicitly and must measure vacuum.
3. Unit-weight PyMatching finds a shortest correction on the complete same-colour triangular lattice.
4. The effective error and correction compose by GF(2) symmetric difference.  A lifted traversal against the determinant-three period matrix classifies every closed residual component; any nonzero winding is a logical charge error.
5. Blue and green results are combined, and the public recovery entry point refuses to run unless the caller certifies that the flux stage found only homologically trivial components.

Inactive stars retain the Lab 004 schema value `-1`; active relation vertices must be binary.  Mixed-colour relations, malformed strings, odd syndromes, open residuals, and invalid flux-stage preconditions fail closed.

## Verification

- For each colour at paper `L=2`, the charge lattice has `3L^2` vertices, `9L^2` edges, degree six, and exact two-endpoint incidence.
- A row-6 three-star relation produces an effective string with exactly the requested `(1,0,1)` boundary.
- Odd charge parity in one relation component is rejected.
- The all-edge closed triangular-lattice chain is detected as homologically nontrivial; a single open edge is rejected.
- A bounded two-colour fixture constructs both effective strings, runs both MWPM decoders, verifies closed residuals, and returns no logical error.
- The charge stage refuses a nontrivial/uncertified flux-stage precondition.

The remediated full Lab 004 suite has **64 passing tests**, including an even-singleton second-stage fixture and the upstream union/XOR decision regression.

## Boundary of the result

This verifies the second-stage mathematical and executable components on bounded source-normalized fixtures.  It is not yet a complete physical-error-to-final-decision simulation: the first-round observation sampler, flux recovery, post-flux charge sampling, relation collection, and two colour recoveries still need one matched public record and an end-to-end truth audit.  No LER data or threshold claim is authorized before that integration gate passes.

