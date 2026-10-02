---
title: Action-feedback sufficiency of the five-round D4 pilot
status: current
updated: 2026-09-24
record: true
---

## Summary

The frozen phenomenological pilot tests timing and noisy-readout behavior on a
shared, precomputed physical history. It does **not** contain an action-to-next-
hidden-state path, so its schedule contrasts cannot test whether timely active
correction prevents non-Abelian anyons from hiding or absorbing later charge.
This narrows interpretation; it does not retract the finite-pilot row counts,
paired directions, or exact replay under their registered model.

## Evidence

The [preregistered review](../../manifests/j6-model-sufficiency-review-2026-09-24.json)
and [machine audit](../../results/j6-model-sufficiency-review-2026-09-24.json)
pin the model source and the accepted deterministic and full-cohort audits.
No new stochastic history, arm evaluation or bootstrap was made.

In the implemented generator, `physical[round]` is the preceding physical
edge chain XOR an exogenous fault row. The hidden projector labels and first
public record are then constructed from that complete chain before a schedule
is evaluated. Neither history-generation function takes a correction/action
argument, and the hidden projector update in this path has no bound action.
The later action-conditioned E2 function does bind a same-round public charge
record to a realized flux action; it returns a completion, not an updated
hidden history. The private terminal score uses the final exogenous physical
chain and the latest public cumulative frame. See the frozen
[integrated-history implementation](../../scripts/d4_integrated_history.py)
and the precise checks in the machine audit.

| Implemented path | Consequence |
| --- | --- |
| Exogenous faults → hidden physical chain → first public record | All schedules see one fixed history; future hidden labels and first records do not depend on earlier schedule actions. |
| Causal schedule → same-round action-bound E2 charge record | The public post-flux observation can differ with the action; the action-binding gate is real. |
| Latest public action → private residual and Boolean-union score | Timing can change this finite pilot's score, but it does not make future hidden dynamics action-dependent. |

The accepted [five-history deterministic trace](../../results/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json)
contains four fixtures in which online branches choose different commit paths
on a single fixed physical history and first-record digest. The accepted
[full-cohort overlap audit](../../results/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json)
retains all 256 existing stochastic histories and 512 JIT rows. Its later-
physical-change and last-commit-readout-mismatch flags often coexist, but
they cannot supply the missing action-to-future-state intervention.

The literature's stronger mechanism is different. Lyons and Brown motivate
rapid *active* correction and ungauging because erroneous anyons can hide
other excitations; their theorem concerns a D(S3) circuit model
([paper, Introduction and Methods](https://arxiv.org/html/2602.11258)).
Jing and collaborators specify spacetime ILP and a just-in-time protocol with
noisy syndrome, but leave numerical JIT implementation and its threshold
proof open ([paper, §VII](https://arxiv.org/html/2608.18512)). Neither
supplies a ready-made cross-round D4 feedback kernel for this project.

## Status

This is a passed structural **model-sufficiency limit**, not a performance
failure or a demonstration that JIT physics has no benefit. The currently
identifiable claim is only causal timing/readout behavior under an exogenous
phenomenological history and its specified score. A hidden-charge-revelation
or fault-tolerance claim needs an explicit causal transition of the form
`next hidden state and next first record | current hidden state, exogenous
faults, realized action`, plus its private logical accounting. The next
bounded gate is to register two tiny deterministic counterfactual branches—a
no-feedback null and a correction-sensitive phenomenological branch—holding
fault and readout keys fixed. It must validate normalization, action binding,
causal prefixes, and ground-state-relative score before any new rate sweep.
The already approved projector-level D4 scope permits this design exercise;
it does not authorize silently claiming a circuit-derived transition law.

## Related pages

[[schedule-state|Schedule state]] · [[spatial-policy-boundary|Spatial-policy boundary]] · [[records/index|Research-record index]]
