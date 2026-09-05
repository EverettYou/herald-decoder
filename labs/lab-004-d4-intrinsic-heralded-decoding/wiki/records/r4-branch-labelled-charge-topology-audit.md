---
title: 'R4.5a branch-labelled charge topology audit'
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

# R4.5a branch-labelled charge topology audit

Status: **branch_homology_audit_passed**.

## Representation and provenance

Both colours retain twelve physical branches over six endpoint pairs. All 127,136 `(E,A)` pairs were classified; all 6,816 nonterminal pairs and 48,000 relation occurrences have unique branch provenance, with 0 endpoint-projection failures.

## Parallel-branch winding fixtures

- blue: 6 parallel pairs, 0 boundary/displacement/winding failures.
- green: 6 parallel pairs, 0 boundary/displacement/winding failures.

## Exact charge-action quotient

- blue: 512 closed chains; four sectors of 128; 8 even syndromes; 0 quotient and 0 within-class loss failures. The period-cochain oracle agrees with the legacy lift on all 90 cycle-like chains; the legacy component-level Boolean loss disagrees on 107 branched/multicycle chains and is not used for the quotient.
- green: 512 closed chains; four sectors of 128; 8 even syndromes; 0 quotient and 0 within-class loss failures. The period-cochain oracle agrees with the legacy lift on all 90 cycle-like chains; the legacy component-level Boolean loss disagrees on 107 branched/multicycle chains and is not used for the quotient.

## Resource and claim boundary

The full provenance-plus-homology audit took 47.186 seconds and evaluated 4,194,304 registered action-loss comparisons, within the ten-minute and five-million-check guards.

PyMatching was intentionally not called in the quotient audit. Therefore duplicate-branch fidelity of the public second-stage decoder and every sequential-policy risk remain open.

Primitive branch representation, actual-path provenance, parallel-branch winding fixtures, and exact charge homology quotient only. Public decoder branch fidelity, sequential policy risk, LER, threshold, and scalability remain untested.

