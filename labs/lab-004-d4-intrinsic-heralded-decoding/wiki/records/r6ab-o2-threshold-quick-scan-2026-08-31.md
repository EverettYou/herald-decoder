---
title: 'R6AB published O2 threshold quick scan'
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

# R6AB published O2 threshold quick scan

The scan uses 1,000 attempted histories per cell on the paper-normalized D4 honeycomb. The primary score is first-stage Boolean-union flux logical failure conditional on nonterminal physical records.

Headline: the paper value is p_c=0.20842 (20.842%). This quick scan supports only a broad transition neighborhood around 0.20--0.22; it does not estimate a replacement threshold.

| L | p_X | failures / nonterminal | conditional flux risk | 90% Wilson interval |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 0.190 | 197 / 1000 | 0.1970 | [0.1771, 0.2185] |
| 5 | 0.200 | 240 / 1000 | 0.2400 | [0.2185, 0.2629] |
| 5 | 0.210 | 301 / 1000 | 0.3010 | [0.2777, 0.3254] |
| 5 | 0.220 | 351 / 1000 | 0.3510 | [0.3266, 0.3762] |
| 7 | 0.190 | 155 / 1000 | 0.1550 | [0.1371, 0.1748] |
| 7 | 0.200 | 213 / 1000 | 0.2130 | [0.1925, 0.2351] |
| 7 | 0.210 | 273 / 1000 | 0.2730 | [0.2505, 0.2968] |
| 7 | 0.220 | 390 / 1000 | 0.3900 | [0.3650, 0.4156] |
| 9 | 0.190 | 144 / 1000 | 0.1440 | [0.1267, 0.1632] |
| 9 | 0.200 | 202 / 1000 | 0.2020 | [0.1819, 0.2237] |
| 9 | 0.210 | 269 / 1000 | 0.2690 | [0.2466, 0.2927] |
| 9 | 0.220 | 396 / 1000 | 0.3960 | [0.3709, 0.4217] |
| 11 | 0.190 | 133 / 1000 | 0.1330 | [0.1163, 0.1517] |
| 11 | 0.200 | 215 / 1000 | 0.2150 | [0.1944, 0.2371] |
| 11 | 0.210 | 292 / 1000 | 0.2920 | [0.2689, 0.3162] |
| 11 | 0.220 | 381 / 1000 | 0.3810 | [0.3561, 0.4065] |

## Crossing diagnostic

- L=5 to L=7: raw linear sign changes 0.21418. Resolved 90% direction bracket [0.190, 0.220].
- L=7 to L=9: raw linear sign changes 0.21400. No 90% direction bracket is resolved.
- L=9 to L=11: raw linear sign changes 0.19458, 0.21605. No 90% direction bracket is resolved.

For audit only, the median raw adjacent-size sign change is 0.21409. The paper reference is 0.20842. The raw value is a small-L interpolation diagnostic, not a threshold estimate.

## Interpretation

The L=5->7 and L=7->9 raw crossings occur near 0.214, but these are upward-biased-capable small-L diagnostics on a 0.01 grid. The L=9->11 pair is statistically unresolved at every grid point and oscillates, so there is no stable size sequence from which to extrapolate. Only L=5->7 has a 90%-resolved change of size direction across the broad registered bracket [0.19,0.22]. The correct conclusion is consistency with a roughly 20%--22% transition window and with the paper's 20.842% value, not a project estimate of 21.4%.

## Claim boundary

This is a quick 1000-shot-per-cell finite-size reproduction check. It can show consistency or tension with a threshold near 0.20842, but cannot reproduce the paper's quoted 2e-5 uncertainty, its L=10--28 scale, or its approximately one-million-sample-per-point analysis.

