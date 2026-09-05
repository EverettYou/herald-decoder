---
title: 'R2 exact charge-stage oracle audit'
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

# R2 exact charge-stage oracle audit

## Question and bounded protocol

Does the production unit-weight PyMatching charge recovery attain the exact minimum T-join objective on every applicable colour record in the registered paper-`L=2` matched cohort?

The independent oracle enumerates every pairing of syndrome defects and every shortest graph path for each pair, combines paths over GF(2), and retains every globally lightest chain. This is complete for a positive unit-weight T-join: an optimum decomposes into defect-pairing paths, while a cycle or a non-shortest segment cannot be required by a minimum solution. A hard cap of 1,000,000 distinct candidates per case keeps the audit bounded.

Implementation correctness is separately checked on a seven-edge connected graph by comparing the oracle's complete minimizing set against full GF(2) affine-space enumeration for all 16 even syndromes. Paper-supercell tests also compare both charge colours against the production decoder.

## Result

The matched cohort contains 189 decoded records and therefore 378 colour-stage records:

| Colour | Records | 0 defects | 2 defects | Objective exact | Unique optimum | Logical ambiguity |
|---|---:|---:|---:|---:|---:|---:|
| Blue | 189 | 174 | 15 | 189 | 189 | 0 |
| Green | 189 | 172 | 17 | 189 | 189 | 0 |

Every production objective equals the exact minimum, and every PyMatching correction belongs to the exact minimizing set. Unlike the first-stage audit, this bounded cohort contains no tied charge optimum and therefore no charge-stage tie-homology ambiguity.

The full Lab suite passes 72 tests.

## Claim boundary

This certifies the second-stage unit-weight MWPM objective only on the registered paper-`L=2` cohort. It does not certify the joint fusion-constrained explanation proposed for R3, does not compute the conditioned logical posterior required by R4, and is not an LER or asymptotic performance result.

Machine-readable evidence: `manifests/r2-exact-charge-oracle-audit.json`.

