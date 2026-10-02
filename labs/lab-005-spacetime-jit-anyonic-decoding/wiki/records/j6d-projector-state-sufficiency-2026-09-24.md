---
title: D4 cross-round projector-state sufficiency audit
status: current
updated: 2026-09-24
record: true
---

## Summary

The registered zero-sampling J6D audit passed its exact provenance and
necessary-condition checks. The published projector and post-flux rules give
an operator-level route to a repeated-round model, but the currently cited
material and pinned local code do not specify a unique numerical
action-conditioned transition among only `vacuum/m_flux/e_charge`. This is
an unresolved derivation, not evidence that D4 necessarily violates a
three-label Markov model.

## Evidence

The [contract](../../manifests/j6d-projector-state-sufficiency-2026-09-24.json),
[exact runner](../../scripts/audit_j6d_projector_state_sufficiency.py), and
[machine result](../../results/j6d-projector-state-sufficiency-2026-09-24.json)
pin the J6C result and three physical/integrated source hashes. All pinned
inputs and J6C's deterministic-interface-only status matched. No new
stochastic history, schedule arm or bootstrap was generated.

The red-X chain bookkeeping gives `0`, `1`, `0` for no fault/no action,
one fault/no action, and one fault/cancelling action, respectively. That
identity concerns Pauli-X flux-chain parity only; it is not a D4 hidden-fusion
transition. A separate *generic*, non-D4 projector example has a rank-two
current coarse subspace and two internal states with the same coarse label.
After an action unitary, their probabilities for a future projector are `0`
and `1`. Thus projector completeness alone is insufficient to infer a closed
coarse-label Markov law. The necessary condition is
`Pi_x U† Pi_y U Pi_x = k Pi_x` for each target, action and fault over the
admitted current subspace. The example does not test whether actual D4
projectors satisfy or violate this condition.

In [Jing et al., Appendix A.4 and D](https://arxiv.org/html/2507.23765),
the post-flux charge constraints depend on the physical-plus-correction
union and the repeated-measurement expression is time ordered. In
[Jing et al., Appendix B and D.2](https://arxiv.org/html/2608.18512),
the local D(G) projector family and ordered density-channel composition
provide a route to explicit state propagation. Neither citation supplies
the numerical cross-round, arbitrary-action, three-label D4 table used in
J6C. Lab 004's post-flux sampler is same-episode; Lab 005's five-round
history is precomputed before the actions.

## Status

The sufficiency audit passes, but the physical-kernel gate remains open and
performance sampling remains frozen. Next derive a geometry-matched two-round
D4 projector/density-state fixture with explicit red-X action, no-action and
cancelling-action limits, first/second public records and propagated private
state. Only then test whether a reduced numeric kernel is valid and whether
the integrated caller implements it. No JIT advantage or threshold follows.

## Related pages

[[schedule-state|Schedule state]] · [[records/index|Research-record index]]
