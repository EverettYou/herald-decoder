---
title: 'R4.5 registered sequential post-flux policy audit'
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

# R4.5 registered sequential post-flux policy audit

## Why a sequential model is necessary

R4.4 supplies the correct immediate Boolean-union loss, but the published
decoder does not end after that decision. Appendix A section 4 states that a
homologically trivial physical/correction union determines parity constraints
for a second simultaneous e-charge measurement, and Appendix C section 2 then
applies another MWPM correction. The first correction therefore changes both
the chance of immediate failure and the distribution of later information. It
cannot be assessed as an isolated classification if the target is final
two-stage logical loss.

This is a bounded sequential-decision problem, not a request for human ranking.
The first-stage actions, observation layers, likelihood, continuations, priors,
and primitive lattice are all reversible and already inside the approved Lab
004 scope.

## Exact channel

Let `O` be either the flux-only record O0 or the flux-plus-first-charge record
O2, `E` a compatible nonwinding physical error, and `A` one of the 32 red-X
corrections with the observed boundary. A winding component in the Boolean
union `E union A` incurs immediate loss one and produces no second record.

Otherwise the union induces same-colour parity components. If `N(E,A)` active
stars are partitioned into `C(E,A)` independent even-parity components, the
second charge record satisfies

`P(Y=y | E,A) = 2^(C(E,A)-N(E,A))`

when `y` is zero off the active support and has even parity on every component,
and has probability zero otherwise. This is the direct affine-support
likelihood implemented by the validated sampler.

The observation boundary matters. Production currently represents unmeasured
inactive entries by `-1` and retains the inferred component relations for
truth scoring. Neither is a physical decoder input. R4.5 converts the measured
record to a full binary vector with deterministic zero outside the active
support and groups posterior evidence by `(O,A,Y)` only. The hidden active mask,
relation partition, physical error, and effective-Z representative are
forbidden from decoder keys.

## Actions and loss

For each colour, all charge corrections with boundary `Y` fall into four torus
homology classes. Corrections inside one class differ by a trivial closed chain
and therefore have identical XOR-residual homology against any compatible
effective error. R4.5 uses the resulting sixteen joint blue/green class pairs
as the exact second-action space and verifies this quotient against exhaustive
affine chains before using it.

For observable history `(O,A,Y)`, the exact continuation selects the joint
class pair with minimum posterior probability that either colour retains a
nontrivial residual. The future-aware first decision minimizes immediate
failure plus this optimal continuation risk:

`Q(O,A) = P(first failure | O,A) + sum_y P(y,continue | O,A) min_B P(final failure | O,A,y,B)`.

## Smallest discriminating policy matrix

At both O0 and O2, the audit evaluates four policies:

1. the published fixed pipeline: public first action and unit-weight charge
   MWPM;
2. the public first action followed by an exact continuation;
3. the R4.4 myopic immediate-loss action followed by an exact continuation;
4. the fully future-aware exact sequential policy.

This matrix distinguishes second-stage MWPM loss, first-stage heuristic loss,
and the cost of ignoring how a first action changes later information. It also
tests whether O2 still improves the exact final decision limit relative to O0.

## Validation and claim boundary

Every per-`(E,A)` second-channel likelihood must normalize; evidence must be
conserved through immediate and continued branches; all public actions must
belong to the registered spaces; the sixteen-class charge quotient must match
exhaustive chain loss; and the exact risk orderings must hold. A deliberately
leaky active/relation-aware oracle is reported only as a sensitivity bound.

The implementation must stream at most 120 million candidate transition
contributions, use no more than 4 GiB, and project to at most 30 minutes after a
deterministic subset preflight. No stochastic samples, larger lattice, noisy
measurements, LER, threshold, or scalable optimality claim are authorized.

Contract:
[`../manifests/r4-sequential-postflux-policy-manifest-2026-08-29.json`](../../manifests/r4-sequential-postflux-policy-manifest-2026-08-29.json).

## Preflight outcome

The 2026-08-29 preflight stopped before policy computation. The second-record
channel itself passed: all 127,136 hidden `(E,A)` branches normalized exactly,
observable keys contained no hidden metadata, and the 2,320,936 projected
second-record contributions fit the registered resource guards.

The charge-action quotient failed an earlier topology gate. On
`periodic_honeycomb(2)`, each colour has twelve physical triangular edges but
only six endpoint pairs. Every endpoint pair has two periodic branches with
different displacement, while `PeriodicPostFluxRelations` stores only endpoint
pairs and `ChargeLattice` deliberately rejects duplicates. Thus the registered
four homology classes and public charge MWPM are not defined on the primitive
R4 topology. Computing a risk anyway would silently discard winding
information.

R4.5 is therefore **preflight-failed**, not computed. The next prerequisite is
a separately registered branch-labelled primitive charge multigraph and
relation provenance audit. Evidence:
[`manifests/r4-sequential-postflux-policy-preflight.json`](../../manifests/r4-sequential-postflux-policy-preflight.json).

