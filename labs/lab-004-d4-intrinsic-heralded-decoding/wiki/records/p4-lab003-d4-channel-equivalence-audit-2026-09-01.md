---
title: 'P4 Lab 003 `q=3/4` versus corrected D4 channel-equivalence audit'
status: current
updated: 2026-09-01
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

# P4 Lab 003 `q=3/4` versus corrected D4 channel-equivalence audit

## Verdict

The channels are **not equivalent**, and no controlled reduction currently
preserves the physical ensemble, public record, decoder, and logical loss.
Lab 003 LERs, crossings, and phase-map boundaries must not be compared
numerically with R6AE or with the paper's D4 threshold.

## Record-level matrix

| Dimension | Lab 003 | Corrected D4 | Audit result |
| --- | --- | --- | --- |
| Physical event | IID Bernoulli-$p$ faults on every retained edge of an open honeycomb patch | IID Bernoulli-$p_X$ red-X faults on a periodic coloured honeycomb | Local prior form only; edge spaces differ |
| Herald condition | Uncoloured $h=1$ with probability $3/4$ for degree $d\ge2$ | Matching-colour $e_B/e_G$ signal with probability $1/2$ only for $d=2$ | Non-equivalent |
| Correlations | Conditionally independent vertex heralds | Colour/component parity-constrained signals | Non-equivalent |
| Geometry | Open rough boundaries and one logical cut | Periodic torus and two winding directions | Non-equivalent |
| Parameter | $p$ on the open phenomenological graph | $p_X$ on the periodic red-X graph, with $p_Z=0$ | No calibrated coordinate map |
| Public record | Parity syndrome plus uncoloured binary $H$ | Flux syndrome plus sublattice-labelled binary $e_B/e_G$; zero hides support | Non-equivalent |
| Decoder | Residual-priority damped BP, 80-iteration cap, posterior-LLR MWPM | D4 coloured-flow dense BP, synchronous 40-iteration cap; separate O0/O2 arms | Non-equivalent |
| Loss | Residual parity across one open-patch logical cut | Paper-unconditional Boolean union of periodic winding failures | Non-equivalent |

Two bounded witnesses already decide the observation-law question. For a
degree-two vertex, Lab 003 has $P(h=1)=3/4$, whereas corrected D4 has
$P(e_{\mathrm{matching}}=1)=1/2$. At degree three, Lab 003 still permits a
herald with probability $3/4$, while D4 permits no e signal. On a six-vertex
closed component, Lab 003 has 64 independent binary records in its support;
D4 parity constraints retain only 16.

The size labels are also not interchangeable. At nominal $L=5$, the Lab 003
open graph has 70 vertices, 74 edges, and 22 boundary vertices; the D4
periodic graph has 150 vertices, 225 edges, and no boundary vertices.

## Candidate reductions

Conditioning on maximum degree two, discarding D4 signal values and
correlations, and setting $q=1$ aligns only a toy support bit. Randomly thinning
D4 signals defines a new hybrid channel. Neither construction licenses reuse
of existing Lab 003 or D4 numerical results.

## Evidence and claim boundary

The executable audit is
`results/p4-lab003-d4-channel-equivalence-audit-2026-09-01.json`; its two
focused tests cover all eight registered dimensions. The earlier R6U audit
remains provenance, while this P4 result uses the corrected signal-only D4
record established by R6AC and the capped R6AE contract. The audit does not
rule out deriving a new common channel in the future; it rules out treating
the existing studies as samples from one.

