---
title: 'R6N default-cell matched flux-policy comparison'
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

# R6N default-cell matched flux-policy comparison

Paper-normalized D4 (L=2), (p=0.20), 100 fixed trajectories.
All three policies share each nonterminal physical/fusion record. The score is first-stage Boolean-union logical failure; terminal physical windings are excluded from the decoder-contingent denominator.

| policy | decoded / nonterminal | flux failures | conditional flux failure | mean wall time |
| --- | ---: | ---: | ---: | ---: |
| O0_unit_weight_MWPM | 100 / 100 | 50 | 0.5000 | 0.87 ms |
| O2_published_herald_weight_MWPM | 100 / 100 | 27 | 0.2700 | 0.68 ms |
| R6D_local_BP_posterior_LLR_MWPM | 100 / 100 | 3 | 0.0300 | 408.80 ms |

R6D-BP completed 100/100 nonterminal records; 97 converged within the default 40 iterations and 3 were decoded from their finite final iterate.

| paired contrast | right improves | right regresses | ties | right minus left flux-failure rate |
| --- | ---: | ---: | ---: | ---: |
| O2_published_herald_weight_MWPM vs O0_unit_weight_MWPM | 25 | 2 | 73 | -0.2300 |
| R6D_local_BP_posterior_LLR_MWPM vs O0_unit_weight_MWPM | 47 | 0 | 53 | -0.4700 |
| R6D_local_BP_posterior_LLR_MWPM vs O2_published_herald_weight_MWPM | 25 | 1 | 74 | -0.2400 |

## Interpretation boundary

The BP branch transfers the posterior-LLR matching principle to the R6D D4 local factor graph. It is not the Lab 002 phenomenological likelihood, and its unscreened 40-iteration loopy marginal is not an exact D4 posterior. This pilot is therefore a matched feasibility/performance observation, not a validation of a scalable D4 BP decoder.

