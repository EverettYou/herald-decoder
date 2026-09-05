---
title: 'Negative-log result invalidation'
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

# Negative-log result invalidation

**Effective 2026-08-27.** The archived artifacts listed below passed
`-log P(error)` edge costs to PyMatching. MWPM requires posterior
log-likelihood-ratio weights, `log[(1-r)/r]`. Therefore every downstream
logical result from a reweighted arm is excluded from inference.

| Artifact family | Invalid fields and conclusions | Retained provenance |
|---|---|---|
| `bp-matching-benchmark` | Herald/syndrome-BP+MWPM LER, disagreement, rescue/harm, effective-error claims | sampled observations, static MWPM arm, BP marginals/scores, convergence, iterations, runtime |
| `soft-attribution-benchmark` | Reweighted LER, rescue/harm, McNemar, effective-error claims | BP marginals, log loss, Brier score, convergence, iterations, runtime |
| `memory-vs-damping-ab` | Both reweighted arms' LER and paired logical comparison | BP log loss, Brier score, convergence, iterations, candidate metadata, runtime |
| `systematic-ab-pilot` | Reweighted pilot LER and any grid justification based on it | observation and runtime provenance only |
| `systematic-memory-vs-damping-ab` | Both reweighted arms' LER, rescue/harm, McNemar, pooling, promotion/regression claims | BP log loss, Brier score, convergence, iterations, candidate metadata, runtime |

Exact logical-MAP outputs that do not call the reweighted matcher remain
valid as oracle provenance. Static syndrome-only MWPM outputs remain valid
when their weights were constructed directly as `log[(1-p)/p]`; they do
not rescue a comparison against an invalid reweighted arm.

Executable decoder paths do not retain a negative-log selector. Historical
JSON is preserved only to make the mistake auditable and must not be loaded
as active corrected-decoder evidence.

