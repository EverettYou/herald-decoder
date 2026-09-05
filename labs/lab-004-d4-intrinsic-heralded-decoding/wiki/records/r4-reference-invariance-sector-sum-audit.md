---
title: 'R4.1 reference invariance and within-sector sum audit'
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

# R4.1 reference invariance and within-sector sum audit

## Reference relabeling

The four compatible explanations of the registered mask-73 observation were each used as the posterior's reference chain. The named relative winding sectors change, but the sorted posterior probabilities, Bayes logical risk, and conditional entropy are identical for all four choices. The reference is therefore a coordinate convention, not a physical prior.

## Genuine sector summation

A second primitive observation has flux syndrome `(1,0,1,1,1,1,0,1)`, no intermediate charge measurements, and exactly two compatible explanations: masks 98 and 140. Their closed difference is homologically trivial, so both belong to the same relative logical sector.

At `p=0.1`, both configurations have equal joint weight. R4 produces one sector with candidate count two; its log2 evidence is exactly one bit larger than either individual configuration's log weight. The sector posterior is one and Bayes logical failure is zero.

This fixture demonstrates an actual sum over configurations, not merely a one-to-one relabeling of MAP candidates.

Two tests bring the complete Lab suite to 93 passing tests.

## Claim boundary

These are primitive exact fixtures. They establish XOR-relative R4 semantics
but do not estimate LER, a threshold, or paper-normalized scaling. R4.4 later
shows that this sector variable is not sufficient for Appendix-A Boolean-union
first-stage loss, so it is not the practical-stage Bayes oracle.

