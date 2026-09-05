---
title: 'R1 ground-state-relative logical contract'
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

# R1 ground-state-relative logical contract

## Researcher decision

The initial state is an anyon-free ground state. Its absolute topological-sector label is not part of the primary reproduction contract. A logical error occurs whenever the physical error and recovery act by a nontrivial topological operator relative to that initial ground state.

This selects a sector-agnostic, relative-homology criterion rather than an all-plus state or a prior over the 22 ground-state sectors. It matches the practical decoder's logical scoring: a nonzero winding component changes the encoded sector and is therefore a failure regardless of which ground state was prepared.

## Schema-v3 application

The primary observation sampler now returns any physical winding component immediately as `status="logical_failure"`, with `logical_error=true`. It preserves the sampled physical error and winding vectors, does not redraw the error, and does not invent sector-dependent charge outcomes. Non-winding records have `logical_error=false`.

The existing even/odd/unconstrained winding policies remain callable only as bounded source-likelihood diagnostics. If one is supplied explicitly, the record may be sampled for that diagnostic, but `logical_error` remains true because the winding operator is nontrivial.

Seven sampler tests and the complete 41-test Lab 004 suite pass under schema version 3.

## Claim boundary

This resolves the practical reproduction's logical-failure convention. It does not claim that the sector-dependent fusion probabilities derived in Appendix A are identical across all ground states. Any future observable requiring those absolute-sector-dependent probabilities must state a separate conditioning contract; the primary LER and recovery comparisons use only the researcher-selected relative-homology criterion.

