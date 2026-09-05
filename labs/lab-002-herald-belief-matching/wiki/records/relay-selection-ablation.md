---
title: 'Relay-leg soft-selection ablation'
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

# Relay-leg soft-selection ablation

Every Relay arm returns only selected soft marginals to MWPM. A hard threshold is used only to select an eligible leg; no BP hard correction is applied.

| Case | Arm | LER | Edge log loss | Edge Brier | Selected hard valid |
|---|---|---:|---:|---:|---:|
| square p=0.08 | legacy_damped | 0.0630 | 0.0783 | 0.0217 | -- |
| square p=0.08 | proxy | 0.0750 | 0.1694 | 0.0261 | 85.0% |
| square p=0.08 | first_leg | 0.0630 | 0.1152 | 0.0239 | 86.4% |
| square p=0.08 | first_valid | 0.0630 | 0.2236 | 0.0293 | 100.0% |
| square p=0.08 | min_prior_valid | 0.0600 | 0.2210 | 0.0288 | 100.0% |
- square p=0.08, proxy vs legacy: rescued 12, introduced 24, LER delta +0.0120, exact McNemar p=0.06525.
- square p=0.08, first_leg vs legacy: rescued 1, introduced 1, LER delta +0.0000, exact McNemar p=1.
- square p=0.08, first_valid vs legacy: rescued 16, introduced 16, LER delta +0.0000, exact McNemar p=1.
- square p=0.08, min_prior_valid vs legacy: rescued 17, introduced 14, LER delta -0.0030, exact McNemar p=0.7201.
| honeycomb p=0.18 | legacy_damped | 0.0480 | 0.0841 | 0.0247 | -- |
| honeycomb p=0.18 | proxy | 0.0460 | 0.4093 | 0.0307 | 74.2% |
| honeycomb p=0.18 | first_leg | 0.0410 | 0.3206 | 0.0302 | 70.1% |
| honeycomb p=0.18 | first_valid | 0.0440 | 0.4914 | 0.0354 | 99.8% |
| honeycomb p=0.18 | min_prior_valid | 0.0430 | 0.4899 | 0.0354 | 99.8% |
- honeycomb p=0.18, proxy vs legacy: rescued 7, introduced 5, LER delta -0.0020, exact McNemar p=0.7744.
- honeycomb p=0.18, first_leg vs legacy: rescued 9, introduced 2, LER delta -0.0070, exact McNemar p=0.06543.
- honeycomb p=0.18, first_valid vs legacy: rescued 7, introduced 3, LER delta -0.0040, exact McNemar p=0.3438.
- honeycomb p=0.18, min_prior_valid vs legacy: rescued 7, introduced 2, LER delta -0.0050, exact McNemar p=0.1797.

This is a selection-mechanism experiment, not a new production decoder or threshold estimate.

