---
title: 'R4.4 matched first-stage loss bridge audit'
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

# R4.4 matched first-stage loss bridge audit

## Exact scope

The audit exhausts 128 O0 flux records, 16230 O2 `(flux, charge)` records, and 32 syndrome-faithful corrections per syndrome on the primitive 12-edge nonwinding channel.

The production syndrome-only and heralded corrections receive only their declared O0 and O2 records. Physical errors are integrated only for posterior scoring. The adaptive second post-flux measurement is excluded.

## Matched Boolean-union decision risks

| p | exact O0 | unit-MWPM O0 | O0 excess | exact O2 | herald-MWPM O2 | O2 excess | exact information gain |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.136159 | 0.141403 | 0.005244 | 0.048061 | 0.096457 | 0.048396 | 0.088097 |
| 0.30 | 0.618746 | 0.636422 | 0.017676 | 0.299160 | 0.514976 | 0.215816 | 0.319586 |
| 0.50 | 0.856028 | 0.856028 | 0.000000 | 0.661717 | 0.840765 | 0.179048 | 0.194312 |
| 0.60 | 0.904742 | 0.905615 | 0.000873 | 0.813879 | 0.930724 | 0.116845 | 0.090864 |

## XOR-sector bridge

XOR-relative sectors fail the complete Boolean-union action-loss sufficiency test on 128/128 O0 observations and 2485/16230 O2 observations. The largest single-observation difference between direct union-loss Bayes risk and XOR-sector Bayes risk is `1`. Therefore the direct action-loss posterior, not the XOR-sector posterior by assumption, is the matched practical-stage comparator whenever this count is nonzero.

## Validation

All action sets are syndrome faithful and both public corrections belong to them. The maximum O0-versus-charge-marginalized-O2 evidence error is `1.388e-15`; global normalization error is `6.439e-14`; R4.3 XOR-risk recovery error is `6.217e-15`. Exact risk never exceeds matched production risk beyond tolerance.

## Claim boundary

Complete exact first-stage primitive nonwinding audit under Appendix-A Boolean-union loss. It excludes the adaptive second measurement and is not a full decoder benchmark, LER, threshold, or scalable result.

