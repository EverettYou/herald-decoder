---
title: Numerical evidence and experiment design
status: current
updated: 2026-09-18
---

# Numerical evidence and experiment design

## Summary

The decisive evidence is the typical-record logical-sector distribution and
how the existing decoder's decisions differ from it. The completed
[mechanism study](mechanism-results.md) now supplies exact posteriors and
matched decoder comparisons on canonical finite patches. This page retains
the inherited evidence, arrow audit and rationale for the experiment sequence.

## Evidence

### Actual arrows and measured boundaries

The Lab 006 adapter retains the canonical graph's edge order: tail deposits
-1 and head +1. We solve psi_head-psi_tail=1 over every incident vertex of
the actual retained graph. A spanning tree fixes candidate potentials; each
non-tree edge then tests a cycle. The audit uses exact integers and exports
a closed-cycle witness for each failure. No idealized arrow field is substituted.

| Parent graph, L=5,7,9,11 | Arrow audit | Implication at 0<q<1, q != 1/2 |
| --- | --- | --- |
| Square | All four admit a gradient (psi=x+y up to constant). | Bulk tilt can be transferred to observed charges and unmeasured boundary weights, while changing the symmetric prior. |
| Honeycomb | All four have a witnessed cycle circulation -2 in units of h. | The stored-arrow bias has a local gauge obstruction; the full bulk tilt cannot be removed. |

Both graph families have arrows increasing vertex ID and hence are directed
acyclic graphs. Acyclicity does **not** imply a constant-magnitude edge field
is a gradient: the honeycomb witness is an undirected cycle traversed with
both signs. At q=1/2, h=0 and this flux vanishes. This finding suggests an
arrow-pattern control on the same honeycomb graph, not a retrospective proof
that flux caused honeycomb's lower LER. Its ordering comes from generated
vertex IDs; we should not assume it represents a uniform laboratory field.

The [audit data](../results/sector-prediction-audit-2026-09-18.json) contain
eight canonical graphs, fifteen rational motif/channel cases, 171 statewise
effective-prior checks and hashes of the actual source and inherited analysis.
These checks supply the path test absent from the initial migrated script.

### What the inherited curves actually say

The complete parent comparison reports significant increases from directed
to hidden fair noise in 95/100 square U(1) cells and 80/100 honeycomb U(1)
cells under its registered paired tests. The statement about 313/400 cells
combines U(1) and SU(3); it must not be relabeled as a U(1)-only result.
See [Lab 006's paired evidence](../../lab-006-sun-bp-theory/wiki/hidden-orientation.md).

At p=0.30, square hidden-channel LER for L=5,7,9,11 is
0.4105, 0.39775, 0.40175, 0.4052. Corresponding BP nonconvergence fractions
are 0.00005, 0.03145, 0.9705, 1.0. Each LER is an estimate from 20,000 trials,
with the parent's Wilson 95% intervals retained in the copied analysis slice.
The nearly merged LER could be intrinsic, an effect of matching, inaccurate
beliefs, or finite-size drift. Correlated nonconvergence does not choose among
these explanations and must never be added to the logical failure count.

### Original acquisition priorities

| Priority | Required evidence | What it resolves |
| --- | --- | --- |
| 1 | Exact Z0,Z1 and edge marginals on small canonical patches; validate against exhaustive states. | Whether the intrinsic posterior already has the directed/fair contrast; provides an oracle for implementation. |
| 2 | Bayes, exact-marginal MWPM, and parent-schedule BP-MWPM on identical records at each (p,q,L). | Separates intrinsic ambiguity, matching loss and BP contribution. No assumed ordering of the two MWPM decoders. |
| 3 | Intermediate q at sentinel p values, recording DeltaF distributions and conditional decoder risk. | Tests whether the mechanism continuously accounts for the two endpoint curve families; monotonicity is an outcome. |
| 4 | Same graph with controlled arrow patterns, plus a separately labeled revealed-boundary-charge oracle. | Tests flux and boundary explanations separately from coordination, size and observation budget. |
| 5 | Larger canonical sizes or separately labeled strips, then theory-justified scaling. | Distinguishes an intrinsic size trend from finite-width artifacts; cannot infer a 2D transition from fixed-width strips alone. |

The initial proposal used q=0.5,0.75,0.9,1 and p=0.10,0.30,0.46. The authorized
sequence in PLAN narrowed Stage 2 to q=.5,.75,1, then registered the selected
size/near-directed extension after that mechanism decision. Each production
manifest froze sizes, seeds, sample count, contraction resource budget and
uncertainty before acquisition. Where all records could not be enumerated,
sample physical currents and compute each resulting charge record's exact
posterior. Do not sample uniformly over possible records or postselect Q=0.

For each record, report r*, signed/absolute DeltaF, posterior logical entropy,
the actual chosen sector and conditional risk of each practical decoder,
and BP residuals/iteration count. Save full per-record comparison data.
Use record-level paired intervals for decoder differences, and pointwise
Wilson intervals for sampled final-correction failures. Across channel biases,
couple activity streams and orientation uniforms while retaining the changed
charge records. Any formal multi-cell discovery claims need a specified
multiplicity rule; an exploratory pilot need not pretend to be confirmatory.

The primary evidence is the intrinsic LER curve plus the measured excess
risk of the original decoder, reconstructing its LER on the same geometry.
Replacing this with a q-aware versus deliberately mismatched-q comparison
would answer a different question: Lab 006's two decoders were already matched
to their respective channels.

## Status

The bounded mechanism study has acquired 10,944 physical-record comparisons:
5,376 in the first square grid, 3,072 in the honeycomb arrow control, and
2,496 in the square size/bias extension. Square posteriors reach L=9 and
honeycomb reaches L=5. The [results note](mechanism-results.md) distinguishes
these finite-patch findings from unmeasured L=11 behavior and critical parameters.

## Related pages

- [Sector predictions and the LER connection](sector-predictions.md)
- [Direction-biased U(1) current channel](direction-biased-u1-current-channel.md)
- [Registered research plan](../PLAN.md)
- [Intrinsic risk and decoder loss](mechanism-results.md)
