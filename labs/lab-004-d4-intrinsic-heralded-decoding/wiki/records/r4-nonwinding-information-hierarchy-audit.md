---
title: 'R4.3 matched nonwinding O0–O2 information audit'
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

# R4.3 matched nonwinding O0–O2 information audit

## Exact matched scope

The primitive channel has 16230 supported O2 `(flux, charge)` observations. Deterministically deleting charge produces 128 O0 flux-only observations. Both layers use the same nonwinding physical ensemble and priors.

Terminal winding status is scoring truth, not decoder input. Its prior mass is reported separately; no winding charge likelihood or truth-revealing terminal symbol is introduced.

## Information supplied by fusion charge

| p | terminal mass | O0 Bayes risk | O2 Bayes risk | risk reduction | H(L|O0) bits | H(L|O2) bits | I(L;charge|flux) bits |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.000401 | 0.135485 | 0.047682 | 0.087804 | 0.436990 | 0.103314 | 0.333676 |
| 0.30 | 0.013186 | 0.599850 | 0.265637 | 0.334213 | 2.090666 | 0.701365 | 1.389301 |
| 0.50 | 0.030029 | 0.776743 | 0.511956 | 0.264787 | 2.604582 | 1.482119 | 1.122463 |
| 0.60 | 0.026930 | 0.730899 | 0.533213 | 0.197686 | 2.622891 | 1.724866 | 0.898025 |

At every registered prior, O2 weakly improves the Bayes decision and weakly lowers conditional logical entropy, as required because O0 is a deterministic coarse-graining of O2.

## Validation

The maximum per-flux, per-sector evidence-conservation error is `1.332e-15`; total nonwinding-mass conservation is `6.917e-14`. The O2 aggregate reproduces R4.2 to `7.050e-14`. O0/O2 posterior normalization and both registered data-processing inequalities pass.

## Claim boundary

Exact O0-versus-O2 information comparison on the primitive nonwinding-conditioned channel only; not a complete physical-channel comparison, LER, threshold, or scalable-decoder result.

Post-R4.4 interpretation: this table concerns the XOR-relative sector variable.
It remains a valid nested-record information hierarchy, but its Bayes risks are
not the Appendix-A Boolean-union first-stage decision risks. R4.4 reports the
matched operational risks separately.

