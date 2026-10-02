---
title: Full-binary sequential public record on one periodic D4 path
status: current
updated: 2026-09-25
record: true
---

## Summary

For one fixed ideal two-red-edge path on the periodic L=2 D4 lattice, the
same-state sequential projector calculation now yields complete 24-site
binary first and action-conditioned second public records. This closes the
fixed-geometry joint-record gate, not the general noisy D4 transition or
production adapter.

## Evidence

The [preregistered contract](../../manifests/j6o-full-binary-sequential-public-record-2026-09-25.json),
[exact machine-readable law](../../results/j6o-full-binary-sequential-public-record-2026-09-25.json),
[runner](../../scripts/run_j6o_full_binary_sequential_public_record.py), and
[public-record tests](../../scripts/test_j6o_full_binary_sequential_public_record.py)
pin Jing Appendix A.1/A.2/A.4 and the previous periodic state and local
Born-moment results. The physical red-X error is fixed to edge IDs `[0,4]`;
the actual first green:1 projector outcome is applied before the red-X action.

At the first observation, only vertices 0 and 2 carry flux, and among the
22 flux-free blue/green stars only green:1 has a nondeterministic charge:
its ± outcomes each occur with probability `1/2`. All 231 eligible first-star
pairs commute on the actual triangle sector. After the partial action `[0]`,
flux is at vertices 1 and 2; among 22 eligible second stars only blue:0 is
random, with ± equally likely conditional on either first outcome. After
the matched action `[0,4]`, flux is absent; among 24 eligible second stars
only blue:0 and blue:2 are random, with joint `++` and `--` each conditional
probability `1/2`. Their opposite outcomes have zero weight. The other 22
second stars are deterministic vacuum. Deferring has no second E2 record.
All first-conditioned joint rows normalize and the local projection matches
the prior fixed-path result.

The public record is exactly three 24-bit arrays: `flux`, `charge`, and
`vacuum=1-charge` under the established independent-membership convention;
fluxful unmeasured sites have charge bit 0. The public action carries only
correction edge IDs. Physical-error support, projector algebra and the
compact quantum state remain in private provenance/diagnostics, not in any
public record. The result contains ten public-law rows across the two first
outcomes and three actions, and passes 167 Lab 005 tests.

## Status

This is a *single ideal geometry* and one compact initial-state sector.
It is not a general action-conditioned D4 sampler, does not test measurement
noise or future hidden-state updates, and is not yet wired through the
first-record-aware production E2 interface. No five-round histories,
schedule-arm evaluations, bootstrap risks or thresholds were produced.
The next gate is to bind this physical joint law to a public adapter with
strict first-record/action/causal and private-boundary checks.

## Related pages

[[schedule-state|Schedule state]] · [[records/j6n-sequential-local-projector-moments-2026-09-25|Local sequential moments]] · [[records/index|Research-record index]]
