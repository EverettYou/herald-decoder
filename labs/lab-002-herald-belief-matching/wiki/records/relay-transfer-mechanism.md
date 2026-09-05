---
title: 'Relay-transfer mechanism audit'
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

# Relay-transfer mechanism audit

This diagnostic does not modify or evaluate the production soft decoder.  It
thresholds each Relay leg at 0.5 only to ask whether the criterion used by
conventional Relay-BP—``H e_hat = syndrome``—would have a candidate to rank.
Truth is used solely for the reported audit log loss and LER.

Settings: L=5, q=0.75, p_m=p_h=0, gamma0=0.15, later gamma values sampled
uniformly from [-0.24, 0.66].  The default transfer has 40 iterations in leg
0 and six later legs of 20 iterations.  The longer-budget rows are an
exploratory 20-shot check with 80 plus 60x60 iterations; they are not a
precision LER estimate.

| Case | Shots | Any valid hard leg | Valid legs / shot | First leg valid | Proxy-selected valid | Proxy log loss | Best-leg log loss (truth audit) | Relay-compatible hard LER |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Square, p=0.08, default | 200 | 100.0% | 6.715 | 86.0% | 85.0% | 0.1957 | 0.0736 | 0.070 |
| Honeycomb, p=0.18, default | 200 | 100.0% | 6.515 | 73.5% | 78.0% | 0.3884 | 0.2125 | 0.050 |
| Square, p=0.08, longer | 20 | 100.0% | 58.6 | 95.0% | 65.0% | 0.1325 | 0.0015 | 0.000 |
| Honeycomb, p=0.18, longer | 20 | 100.0% | 57.4 | 55.0% | 90.0% | 0.3521 | 0.0447 | 0.100 |

"Relay-compatible hard" chooses, among syndrome-valid thresholded legs, the
smallest original-prior hard correction.  With uniform p this is the candidate
with the fewest selected edges.  It is a mechanism test only: it is not used
by Herald-aware belief matching, and it cannot establish a scalable LER claim.

The strongest result is structural.  Conventional Relay's feasibility test is
usually already satisfied here—often by the first leg—and almost every leg is
valid under the longer budget.  The current observation-only Bethe proxy can
nevertheless select a syndrome-invalid thresholded candidate.  That proxy is
therefore not a substitute for Relay-BP's valid-correction selection rule.

Machine-readable records: [relay-transfer-mechanism.json](../../results/relay-transfer-mechanism.json).

