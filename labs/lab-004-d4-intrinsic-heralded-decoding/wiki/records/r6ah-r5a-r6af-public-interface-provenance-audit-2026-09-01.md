---
title: R6AH legacy R5a/R6AF public-interface provenance audit
status: current
updated: 2026-09-01
record: true
---

## Summary

The legacy R5a cohort is **incompatible** with the remediated R6AF complete public-interface contract.
Its frozen physical and lattice records remain provenance, but its numerical complete-pipeline claims are withdrawn.

## Status

Current provenance boundary. R6AF is the replacement complete-pipeline evidence only at its own registered four-cell scope.

## Evidence

[Machine-readable audit](../../results/r6ah-r5a-r6af-public-interface-provenance-audit-2026-09-01.json)
and [registered contract](../../manifests/r6ah-r5a-r6af-public-interface-provenance-audit-manifest-2026-09-01.json).

## Interface matrix

| Dimension | Verdict | Witness |
|:---|:---|:---|
| artifact identity and status | compatible | All 10 frozen file hashes and all five status gates pass; the R5a gzip contains exactly 40000 records. |
| physical channel and geometry | compatible_scope_difference | Both use the paper-normalized periodic honeycomb IID red-X channel, but R5a uses L=2,3 and p=0.14..0.22 whereas R6AF uses L=3,5 and p_X=0.19,0.21; no numerical comparison is allowed. |
| first observation and timing | incompatible | The legacy first-record domain is [-1, 0, 1] and 40000 records expose inactive -1 support; R6AF requires a full binary signal-only field where zero is ambiguous. |
| matched randomness | compatible_with_limited_provenance | All 20000 legacy pairs match physical errors, first records, and decoder seeds, with 3323 pairs recording distinct post-action second outcomes; R5a does not expose R6AF's three keys separately. |
| second public record | incompatible | All 28253 stored legacy second records use domain [-1, 0, 1]; 28253 contain -1 and zero are full binary. R6AF requires one binary value on every star. |
| charge action information budget | incompatible | The legacy record couples 28253 relation-bearing records and 28253 effective-error scoring records at the old combined boundary; R6AF records that this boundary accepted hidden relations and replaced it with a relation-free public action plus private scorer. |
| action-conditioned support | incomplete_gate | R5a records policy-dependent post-action supports and passed own-support proxies, but it has no wrong-action rejection or action-binding fixture equivalent to R6AF. |
| logical scorer and denominator | compatible_with_unexercised_branch | Stored R5a final-loss flags equal the OR of available physical/flux/charge loss fields in all records (0 mismatches), but its cohort contains no physical-winding histories and cannot exercise that denominator branch. |
| anti-leak and replay gates | incomplete_gate | R5a stores zero explicit public transcripts and lacks relation-perturbation invariance, wrong-action binding, and first/middle/final deterministic replay gates required by R6AF. |
| claim usability | provenance_only | R5a physical/lattice records remain provenance, but its O2 policy differences, final-loss risks, stage mechanism, size directions, and Lab 005 baseline promotion are withdrawn as evidence for the remediated complete public pipeline. |

## Decisive boundary

All 40,000 frozen R5a records were inspected without resampling. The first and second records use the support-revealing domain `(-1, 0, 1)`; no second record is full binary. The old combined charge boundary also carries private relation/effective-error truth, whereas R6AF separates a relation-free public action from private generation and scoring.

R5a additionally lacks the remediated wrong-action binding, relation-perturbation anti-leak, explicit public-transcript, and deterministic replay gates. These are implementation-contract failures, not adverse numerical comparisons.

## Claim usability

Retained as provenance: frozen physical-error draws, lattice/topology records, and historical implementation trace.

Withdrawn for the remediated complete pipeline: all R5a O0/O2 final-loss risks and paired differences, the O2 stage-mechanism claim, size directions, and promotion as a validated Lab 005 baseline. R6AF remains the current replacement evidence only at its own four-cell pilot scope.

## Claim boundary

This is a deterministic provenance verdict. It performs no R5a/R6AF numerical risk comparison and does not register or imply a rerun, crossing, threshold, scaling, noisy-measurement, or fault-tolerance claim.
Zero new histories, arm evaluations, or bootstrap replicates were generated.

## Related pages

[[decoder-validation|Decoder validation]] · [[records/r5a-paper-lattice-public-decoder-analysis|Withdrawn R5a pilot record]] · [[records/r6af-two-stage-public-charge-preflight-2026-09-01|R6AF public-interface remediation]] · [[records/index|Research-record index]]
