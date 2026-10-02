---
title: Deterministic action-feedback interface counterfactual
status: current
updated: 2026-09-24
record: true
---

## Summary

A preregistered, two-round, one-site D4-labelled fixture tested whether the
existing projector instrument can carry an action-to-future-hidden-state path.
It can under an explicitly stipulated feedback table; a matched no-feedback
null remains action-invariant. This is an interface-capacity result, **not** a
physical D4 transition law, a code logical-error rate, or evidence that a
just-in-time schedule outperforms another schedule.

## Evidence

The [frozen contract](../../manifests/j6c-action-feedback-counterfactual-2026-09-24.json),
[runner](../../scripts/run_j6c_action_feedback_counterfactual.py), and
[machine result](../../results/j6c-action-feedback-counterfactual-2026-09-24.json)
define and retain all four unique model-by-action cells. The result SHA-256 is
`2ee9127c39cab9e7a5f4ddc173cd2f95d35fe44ce88f4f0fea2fe231cd3928e7`.
The prior model-sufficiency audit's pinned hash and accepted status matched.
Zero stochastic histories, performance-arm evaluations, and bootstrap
replicates were generated; measured CPU time was 0.000958 seconds, below the
registered 10-second limit.

All four cells shared the same round-0 public `[flux, herald]=[1,1]` record
and the same three fixed exogenous keys. The exact categorical kernel over
`vacuum/m_flux/e_charge` is nonnegative and sums to one in every cell. `defer`
has no second measurement; `commit` has the same full-binary public
`[charge,vacuum]=[0,1]` second record bound to its public action digest in
both models. A substituted digest fails binding. A round-1-only public-bit
perturbation leaves the earlier first record, action, action digest and second
record untouched. Exact replay matches all four cells. Public serialization
contains neither private label/state nor score.

| Stipulated path | Defer: next hidden / first record | Commit: next hidden / first record |
| --- | --- | --- |
| No-feedback null | `m_flux` / `[1,1]` | `m_flux` / `[1,1]` |
| Action-feedback fixture | `m_flux` / `[1,1]` | `vacuum` / `[0,0]` |

The private Boolean-union diagnostic is true for the three terminal
`m_flux` cells and false for the stipulated feedback-commit `vacuum` cell;
the relative-winding bit is fixed false. These are exact fixture values, not
sampled failure probabilities.

## Status

The registered deterministic interface gate passed. It did not modify or
validate the five-round integrated J6/J6B history generator: its hidden future
remains precomputed and action-invariant. The action-sensitive transition was
chosen solely to test representability and has no source-derived D4 fusion
probability or microscopic circuit interpretation. Before any new performance
cohort, a separate physical-model/adapter gate must connect a justified
action-conditioned D4 kernel to the integrated repeated-history caller and
verify normalization, the public/private boundary and independent limiting
cases. No rate sweep, threshold fit, or JIT-superiority claim follows here.

## Related pages

[[schedule-state|Schedule state]] · [[spatial-policy-boundary|Spatial-policy boundary]] · [[records/index|Research-record index]]
