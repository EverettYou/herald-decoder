---
title: 'R4.0 exact conditioned logical-sector posterior'
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

# R4.0 exact conditioned logical-sector posterior

## Operation

For every compatible nonwinding error explanation, R4 computes the validated joint weight `P(s|E)P(E)`, classifies its closed difference from a canonical reference error, and sums weights within each relative homology sector. The reported Bayes logical failure probability is `1-max_h P(h|s)`; conditional entropy and the top-two log-evidence gap quantify residual ambiguity.

Changing the reference error relabels sectors but leaves the evidence multiset, entropy, and Bayes risk unchanged.

## Registered fixture

The mask-73 observation has four compatible explanations in four relative sectors.

At `p=0.1`, the sorted sector posterior is

`{1/244, 81/244, 81/244, 81/244}`.

Three sectors tie for maximum evidence. Bayes logical failure probability is `163/244 = 0.66803`, conditional entropy is `1.61687` bits, and the top-two evidence gap is zero.

At `p=0.6`, the sorted posterior is

`{4/21, 4/21, 4/21, 3/7}`.

The sector containing the unique five-edge configuration-MAP mode has the largest mass, but only `3/7`; Bayes logical failure probability remains `4/7 = 0.57143`. Conditional entropy is `1.89092` bits and the top-two log2 evidence gap is `log2(9/4)=1.16993`.

Three tests verify exact fractions, normalization, entropy, gap, and risk.

## Scientific conclusion and boundary

The low-p configuration-MAP tie becomes a three-way sector-evidence tie. More importantly, even the unique high-p configuration-MAP solution corresponds to only 42.9% posterior sector mass. This directly demonstrates why R3 MAP optimization cannot be called Bayes-optimal for the XOR-relative sector variable.

Post-R4.4 interpretation: the XOR-relative sector is not sufficient for
Appendix-A Boolean-union first-stage loss. These exact fractions remain valid
sector posteriors, but they are not the practical first-stage Bayes oracle.

This is a one-observation primitive fixture, not an LER, threshold, or paper-normalized performance result.

