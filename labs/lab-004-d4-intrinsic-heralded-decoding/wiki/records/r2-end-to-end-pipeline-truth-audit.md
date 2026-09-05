---
title: 'R2 matched end-to-end pipeline truth audit'
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

# R2 matched end-to-end pipeline truth audit

Date: 2026-08-28

## Integrated record

The new schema-v1 pipeline follows one fixed physical red-X error through every applicable source stage:

1. sample the first intermediate e-charge observation conditional on the physical error;
2. run either syndrome-only unit-weight MWPM or the published herald-conditioned `1-n_e K` MWPM on that same observation;
3. retain XOR as the Pauli residual, but use Boolean physical/correction union homology to decide whether charge recovery is allowed;
4. derive one blue and one green even-parity component from every homologically trivial union component;
5. sample the second commuting star measurements uniformly on that affine even-parity support;
6. construct effective same-colour Pauli-Z strings and run both unit-weight charge MWPM decoders; and
7. report the final logical decision with all truth fields and intermediate supports preserved in a JSON-safe record.

Physical winding failures and union-homology failures short-circuit before the downstream stages whose preconditions they violate. Independent deterministic seed streams separate the first and second measurement rounds.

## Bounded branch matrix

The machine audit uses the paper-normalized `L=2` periodic honeycomb (`36` red edges), `p in {0,0.05,0.10}`, 32 fixed physical seeds per p, and both public modes on matched physical errors and matched first observations. This gives 192 complete mode records without estimating an LER.

- 96/96 mode pairs have identical physical errors and first observations.
- All 192 first-stage XOR residuals have zero boundary and their decisions agree with Boolean-union homology.
- 189 records reach the second stage; every sampled post-flux record satisfies all DSU parity constraints.
- All 378 blue/green charge residuals have zero boundary.
- All 189 final decisions agree with the two colour-recovery results.
- Three syndrome-only records short-circuit at a nontrivial union component; their early-failure flags are consistent. The audit's 3-versus-0 count is not interpreted as a performance comparison.

Four integration tests additionally cover exact zero-error decoding in both modes, deterministic post-flux support sampling, explicit physical-winding short-circuiting in both modes, JSON serialization, matched inputs, and final residual invariants. The complete Lab 004 suite passes 68 tests.

## Evidence and claim boundary

Machine-readable protocol, invariant counts, representative records, and source hashes are in `manifests/r2-end-to-end-pipeline-truth-audit.json`. This verifies executable continuity and branch invariants only. It does not estimate a logical error rate, reproduce a threshold, validate an asymptotic scaling law, or authorize R5. The next R2 gate is a small exhaustive oracle comparison of the integrated record where tractable, before any statistical performance experiment.

