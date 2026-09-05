---
title: 'J1 E1 typed-policy translation result'
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

# J1 E1 typed-policy translation result

The translation gap is resolved without extending the public schema. Six registered translation cases pass; the combined E1 fixture file passes 20 tests, and all 106 Lab 005 tests pass. No performance sample was generated.

For `syndrome_only`, the adapter preserves reported flux membership and withholds charge membership exactly as required by that mode's information budget. A charge-only change still changes the combined scheduler/report provenance digest, but it does not change the mode-visible syndrome or decoded action.

For `heralded`, the adapter losslessly factorizes the two reported membership bits. A site reporting both `m_flux` and `e_charge` appears in `flux_syndrome_vertices` and receives charge outcome one. Explicit zeros preserve measured vacuum/no-charge reports. The resulting request and action equal a manually constructed request and action from the same visible bits; the perfect limit also agrees with the earlier restricted adapter.

The old adapter remains a useful negative control: it rejects the same multi-label record that the current two-field request schema accepts. The localized gap was therefore an implementation restriction, not a representational impossibility. Combined provenance binds the scheduler prefix, exact E1 report, mode, and schema version while exposing no private projector state.

This result validates interface semantics only. It does not establish an optimal translation, channel calibration, schedule advantage, LER, threshold, or fault tolerance. The next prerequisite is deterministic integration of the verified typed request with the matched-history scheduling harness before any stochastic pilot is registered.

Machine-readable evidence: [`manifests/j1-e1-typed-policy-translation-2026-08-29.json`](../../manifests/j1-e1-typed-policy-translation-2026-08-29.json).

