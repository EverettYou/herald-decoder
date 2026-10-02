---
title: J1 E4C remediated D4 charge-source compatibility audit
status: current
updated: 2026-09-19
record: true
---

## Summary

The remediated Lab 004 charge source is behaviorally compatible with the frozen
Lab 005 public contract across the registered interface dimensions. This audit
does not claim that the unavailable old source body is internally equivalent.

## Evidence

The [machine-readable audit](../../results/j1-e4c-d4-charge-semantic-compatibility-2026-09-19.json)
verifies both registered hashes and changes exactly one value in test-process
memory: Lab 005's frozen `d4_charge.py` hash. It then replays the full spatial
policy, projector instrument, temporal composition, two-mode/four-schedule
integration, charge action, remediated two-stage preflight and winding-score
test files. All 77 tests pass.

The suite covers public function signatures and exact fields, syndrome
fidelity, full-binary relation-free charge action, wrong-action/support
rejection, action-conditioned second records, truth/future exclusion, causal
ordering, deterministic replay, matched schedule execution and ground-state-
relative winding. Production histories, performance evaluations and bootstrap
replicates remain zero.

## Status

Public-contract compatibility is established; line-level and internal-
algorithm equivalence are not. A later transition may update only the Lab 005
frozen hash and rerun the unchanged J1-E4B matrix. Stochastic work remains
blocked until that full matrix passes.

## Related pages

- [[spatial-policy-boundary|Spatial-policy boundary]]
- [[records/j1-e4b-translation-interface-matrix-2026-09-19|J1 E4B interface matrix]]
- [[records/j1-e4-d4-lyons-brown-translation-registration-2026-08-29|J1 E4 translation registration]]

