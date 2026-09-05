---
title: 'R1 logical-Z sector mapping audit'
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

# R1 logical-Z sector mapping audit

## Source-backed mapping

For the single red-Pauli-X channel, intermediate charges live on blue and green stars.  Let `z[c,d]` be the eigenvalue of the logical Z string of charge colour `c` in torus direction `d`.  The winding-loop charge parity bit is

`parity[c,d] = (1 - z[c,d]) / 2`.

Thus `z=+1` maps to even parity and `z=-1` maps to odd parity.  If the protected state is not a logical-Z eigenstate for that colour/direction, the parity is not fixed and maps to the explicit unconstrained branch rather than to even parity.

This is the stabilizer interpretation of the examples in Jing et al., Appendix A: a horizontal blue logical `-Z` state gives odd blue and even green charge parity on a horizontal winding loop; a vertical blue logical-X eigenstate leaves the anticommuting horizontal blue logical-Z parity unconstrained.  Colour and direction permutations give the corresponding mappings.

Iqbal et al. define the six colour/direction logical-Z strings of the same kagome D4 model and prepare a unique ground state with all six eigenvalues `+1`.  For the red-X channel, only the four blue/green values enter; the resulting candidate policy is even for both colours in both directions.

## Implementation and verification

`LogicalZSectorDescriptor` records the four relevant eigenvalues as `+1`, `-1`, or indefinite and converts them to the existing winding policy.  `all_plus_logical_z_policy()` exposes the Iqbal all-logical-Z-plus state as a named candidate, with a docstring stating that Jing et al. did not specify it as their threshold-simulation state.

Three new tests verify:

- the Appendix-A `-Z` odd/even example and the logical-X unconstrained example;
- the all-logical-Z-plus candidate in both colours and both torus directions; and
- fail-closed rejection of values outside `{-1,+1,None}`.

The complete R1 suite passes 22 tests.

## Claim boundary and unresolved choice

The descriptor implements the parity/eigenvalue correspondence; it does not certify that an arbitrary four-entry assignment is one of the 22 physical D4 ground states.  Jing et al. explicitly leave their initial threshold-simulation state unspecified because no isolated nonbranching homologically nontrivial loop appeared in over `10^8` matching configurations.  Therefore the paper does not determine whether this reproduction should select the experimentally prepared all-plus state, average over a declared physical sector ensemble, or preserve a sector-conditioned comparison.

No initial sector was selected and no published decoder was run in this transition.

