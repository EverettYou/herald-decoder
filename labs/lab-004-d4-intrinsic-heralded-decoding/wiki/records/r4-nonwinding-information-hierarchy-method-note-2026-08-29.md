---
title: 'R4.3 nonwinding O0–O2 information hierarchy — registered method'
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

# R4.3 nonwinding O0–O2 information hierarchy — registered method

## Question and matched comparison

R4.3 asks how much logical-sector information the primitive fusion-charge
record adds beyond flux alone. The comparison uses one physical prior and one
nonwinding-conditioned ensemble. O2 is the complete R4.2 `(flux, charge)`
record; O0 is produced from it by deleting the charge record. Thus O0 is a
deterministic coarse-graining of O2, rather than a separately sampled channel.

This restriction is necessary. R4.2 classifies a physical winding mask as a
terminal ground-state-relative logical failure, but that classification is
truth used to score the experiment, not a decoder-visible observation. The
project has not derived an O2 charge likelihood for winding sectors. A naive
full-channel comparison would therefore either invent such a likelihood or
give a decoder an unphysical truth-revealing terminal symbol. R4.3 does
neither: it reports terminal winding prior mass separately and compares O0 and
O2 only on their rigorously shared nonwinding channel.

## Exact construction

Use the complete R4.2 support and the unchanged prior matrix
`p={0.1,0.3,0.5,0.6}`. For each O2 observation, delete the charge vector and
group observations with the same flux vector. Sum the O2 joint evidence within
each relative logical sector to obtain the O0 sector evidence. No resampling,
fit, interpolation, or additional physical model is allowed.

For each observation layer, compute the Bayes logical failure probability and
conditional logical-sector entropy. Average them with the matched
nonwinding-conditioned observation evidence. Report

\[
\Delta R = R_{\mathrm{Bayes}}(O0)-R_{\mathrm{Bayes}}(O2)
\]

and

\[
\Delta H = H(L\mid O0,\mathrm{nonwinding})
          -H(L\mid O2,\mathrm{nonwinding}).
\]

Because O0 is a deterministic function of O2, optimal decision theory and the
data-processing inequality require both differences to be nonnegative. The
entropy difference is the conditional mutual information
`I(L; charge | flux, nonwinding)` for this bounded channel.

## Validation and claim boundary

Every O2 observation must map to exactly one O0 record. For every flux and
logical sector, the O0 evidence must equal the sum over its O2 charge
refinements. Total nonwinding evidence and posterior normalization must be
preserved at each prior, and the O2 aggregate must reproduce R4.2. The two
registered data-processing inequalities must hold to absolute tolerance
`1e-12`.

The strongest authorized claim is the exact incremental information and
Bayes-risk benefit of fusion charge on this primitive nonwinding channel. It
is not a comparison of complete physical channels, a lattice-size scaling
result, an LER estimate, a threshold, or a practical-decoder benchmark. Stop
after the deterministic aggregation, audit, tests, and report update; R5
sampling remains a later gate.

