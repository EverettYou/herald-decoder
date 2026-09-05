---
title: 'R1 winding-sector policy matrix audit'
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

# R1 winding-sector policy matrix audit

## Result

The versioned D4 observation channel now represents logical-sector-dependent winding-loop measurements without collapsing “unconstrained” into even parity.  A policy supplies, for each primitive torus winding direction and charge colour, one of three explicit branches: even parity, odd parity, or no parity constraint.  Missing rules and components with more than one independent winding direction fail closed.

The diagnostic policy branch was introduced in schema version 2 and records the policy label. Schema version 3 supersedes the primary behavior: without an explicit diagnostic policy, a winding physical error is preserved with status `logical_failure` and `logical_error=true`. When a complete policy is supplied for a bounded likelihood audit, the sampler draws uniformly from its affine parity subspace and independently rechecks Appendix A Eq. A12, but the record still has `logical_error=true` because its winding action is nontrivial.

## Bounded branch matrix

For one vertical nonbranching winding loop on the L=3 periodic coloured honeycomb, the test matrix exhausts the Cartesian product

`blue parity in {even, odd, unconstrained}` × `green parity in {even, odd, unconstrained}`.

All nine representation branches pass.  Fixed-seed sampling reaches both parities for every unconstrained colour, satisfies every required parity, and returns `log2 P(s|E) = C - 6`, where `C` is the number of active colour constraints.  Direction normalization is exercised in both torus directions by specifying `(0,2)` for the primitive vertical `(0,1)` branch and `(2,0)` for the primitive horizontal `(1,0)` branch; an omitted colour rule is rejected.

The complete R1 suite passes 19 tests.

## Claim boundary

This audit verifies the three-state winding-parity representation and its likelihood/sampling semantics.  It does **not** assert that all nine abstract combinations are distinct physical D4 ground states, nor does it derive a complete map from the D4 logical-operator basis to policy keys.  Appendix A supplies examples—odd/even and unconstrained branches depending on the protected logical operator—but the source does not specify the initial sector used in its threshold simulations because such isolated winding error loops were not observed there.  Selecting a physical sector for reproduction therefore remains a separate source-mapping gate.

No published decoder or threshold simulation was run in this transition.

