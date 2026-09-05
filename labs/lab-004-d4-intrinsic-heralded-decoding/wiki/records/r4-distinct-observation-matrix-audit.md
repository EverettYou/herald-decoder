---
title: 'R4.2 complete distinct-observation posterior audit'
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

# R4.2 complete distinct-observation posterior audit

## Exact scope

The primitive 12-edge fixture contains 4096 physical masks. Exactly 123 are terminal winding failures; the other 3973 masks generate 16230 distinct supported observations through 49855 candidate-observation pairs.

All allowed records normalize for every nonwinding error, and terminal mass plus nonwinding observation evidence normalizes at every registered prior. No stochastic sample or winding-sector charge record is introduced.

## Prior-weighted exact inference

| p | terminal winding mass | mean nonterminal Bayes risk | combined failure | mean conditional entropy (bits) | forced MAP/Bayes disagreement |
|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.000401 | 0.047682 | 0.048063 | 0.103314 | 0.000000 |
| 0.30 | 0.013186 | 0.265637 | 0.275320 | 0.701365 | 0.000000 |
| 0.50 | 0.030029 | 0.511956 | 0.526611 | 1.482119 | 0.000000 |
| 0.60 | 0.026930 | 0.533213 | 0.545783 | 1.724866 | 0.076290 |

The MAP comparison is set-valued: a tied configuration optimum is not forced into an arbitrary sector. `forced` means every maximum-weight configuration lies outside every maximum-evidence logical sector. The lexicographic convention remains a separately recorded implementation diagnostic.

## Validation

The maximum per-error record-normalization error is 0.000e+00; the maximum global normalization error is 7.772e-16. R4.0 exact fractions, the masks 98/140 one-sector R4.1 sum, and three independently re-evaluated observations all pass.

## Claim boundary

Complete exact audit of the primitive 12-edge fixture only; not an LER, threshold, or scalable-decoder result.

Post-R4.4 interpretation: the reported Bayes risks are exact for the XOR-
relative sector 0–1 loss. XOR sectors fail the Appendix-A Boolean-union loss-
sufficiency test, so these numbers are not practical first-stage Bayes risks.

