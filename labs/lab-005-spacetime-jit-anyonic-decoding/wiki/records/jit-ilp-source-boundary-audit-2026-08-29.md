---
title: 'JIT age-gate and spacetime-ILP source-boundary audit'
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

# JIT age-gate and spacetime-ILP source-boundary audit

## Outcome

The existing modules are useful and their bounded invariants now pass, but
they are two different source-derived pieces rather than a completed
fault-tolerant decoder:

- `spacetime_ilp.py` structurally implements the variable blocks and local
  equalities of Jing *et al.* (2026), Eqs. (18)–(20), with a linear objective
  equivalent to Eq. (21) only after converting the paper's maximized log
  weights into minimized additive costs.
- `jit_schedule.py` implements the bounding-cube age predicate in Jing
  *et al.* Algorithm 1, step 3.1. It does not implement the fuller
  Lyons–Brown absorber-distance and D(S3)/D(Z3) state machine.

This localization matters: calling the current age gate a reproduction of the
Lyons–Brown decoder would be scientifically incorrect.

## What is source matched

The ILP has binary physical-event and measurement-error variables, one local
fusion-channel variable per caller-supplied allowed channel, separate spatial,
incoming-temporal, and outgoing-temporal multiplicity equalities, and exactly
one selected channel at each spacetime site. The Fig. 4(c/d)-type fixture also
checks the source's non-Abelian point that an unchanged defect does not fix the
allowed channel without the measured syndrome.

The age gate computes the side length of the smallest axis-aligned spacetime
cube containing the inferred cluster and defers when any defect or correction
element occurs after `t-Q`. Equality at `t-Q` commits, matching the boundary in
Jing Algorithm 1.

## What remains generic or absent

The caller, not the ILP compiler, still supplies the measured-syndrome-specific
channel set. There is no complete D4 table, D(S3) circuit model, global fusion
constraint, noisy repeated herald channel, or scalable solver benchmark.

For the schedule, commitment currently means only deterministic bookkeeping.
It does not reverse the latest measurement to propagate a deferred event,
execute correction circuits, track nearest absorbers or absorbing regions,
branch across D(S3), ungauged D(Z3), and their boundary, test neutrality,
re-gauge, or manage linked clusters. Those operations are essential parts of
the Lyons–Brown construction and proof.

## Corrections made during audit

The scheduler now has a monotone clock, transactional failure behavior, unique
identifiers, and an exact partition requirement for every unresolved defect.
It rejects negative/future times, overlaps, incomplete cluster sets, and
duplicate new defects without partially changing state. The ILP now rejects
ambiguous labels and non-finite channel costs, and its documentation records
the mandatory objective-sign conversion.

Seven JIT fixtures and six ILP fixtures pass. All 27 current Lab 005 tests pass.
The machine-readable audit is
[`manifests/jit-ilp-source-boundary-audit-2026-08-29.json`](../../manifests/jit-ilp-source-boundary-audit-2026-08-29.json).

## Claim boundary and next gate

This is a verified structural preflight, not a full Jing JIT decoder, a
Lyons–Brown reproduction, a noisy D4 decoder, a numerical schedule comparison,
or fault tolerance. The next bounded gate is to register deferred-record
propagation and an explicit schedule-state layer that keeps the Jing ILP and
Lyons–Brown absorber/ungauging branches separately labelled.

