---
title: 'R4.5b expanded branch MWPM adapter audit'
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

# R4.5b expanded branch MWPM adapter audit

Status: **expanded_branch_adapter_passed**.

- blue: 104 exhaustive comparisons; topology/auxiliary/half-branch failures 0/0/0; objective/boundary/minimizer/target/sector failures 0/0/0/0/0.
- green: 104 exhaustive comparisons; topology/auxiliary/half-branch failures 0/0/0; objective/boundary/minimizer/target/sector failures 0/0/0/0/0.

Each colour uses one 16-node, 24-edge matching graph with twelve private degree-two auxiliary detectors and all twelve physical branch fault ids. Auxiliary syndrome bits are always zero, and every decoded solution selects both segments of a branch or neither.

All 208 registered profile/syndrome cases match exhaustive primitive objectives and minimum branch masks. The adapter is now eligible for integration into a re-registered R4.5 sequential-policy computation; that integration and risk are not part of this audit.

Expanded primitive public charge-MWPM representation equivalence only. No sequential policy risk, LER, threshold, noisy-measurement, or scalability result is computed.

