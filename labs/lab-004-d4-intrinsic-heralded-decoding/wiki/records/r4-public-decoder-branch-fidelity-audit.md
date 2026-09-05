---
title: 'R4.5a public decoder branch-fidelity audit'
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

# R4.5a public decoder branch-fidelity audit

Status: **public_branch_fidelity_failed**.

- blue: 12 physical branches become [6] matching edges. Across 104 profile/syndrome comparisons, objective, boundary, minimizer-membership, and targeted-ID failures are 0, 0, 0, and 0.
- green: 12 physical branches become [6] matching edges. Across 104 profile/syndrome comparisons, objective, boundary, minimizer-membership, and targeted-ID failures are 0, 0, 0, and 0.

The exhaustive oracle shows that reconstruction-time minimum-weight selection is numerically correct and can choose either parallel fault id when that id is made cheaper. However, a single matching graph retains only one of the two physical branches for each endpoint pair: twelve branches collapse to six edges. The public primitive graph therefore loses simultaneous branch topology and cannot yet be called reproduced.

A bounded private-auxiliary-node expansion is required. Each physical branch will become a two-edge path through its own zero-syndrome auxiliary detector, with one branch fault id and split total weight. That adapter must reproduce every exhaustive objective and branch mask before sequential-risk work resumes.

Deterministic primitive PyMatching representation audit only. It does not validate an expanded adapter, compute sequential policy risk, or establish LER, threshold, or scalability.

