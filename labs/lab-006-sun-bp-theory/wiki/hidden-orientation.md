---
title: Hidden pair orientation and decoding
status: current
updated: 2026-09-09
---

# Hidden pair orientation and decoding

## Summary

This study tests the researcher's hypothesis that a fixed fundamental/antifundamental
pair orientation contributes to the different finite-size behavior of U(1), SU(2),
and SU(3). The directed curves exhibit SU(2) crossings and no obvious U(1)/SU(3)
crossing on the registered grid; this is not evidence of an absent asymptotic
threshold. The new six-panel study changes only the prescribed physical pair
orientation law and uses inference matched to that law.

## Evidence

The [registered study](../manifests/a9-hidden-orientation-ler-2026-09-07.json)
uses the same square/honeycomb patches, L=5,7,9,11, p=0.02,0.04,...,0.50,
and 20,000 matched shots per cell as the directed study. On every active edge,
a fresh fair hidden bit swaps the deposited fundamental and antifundamental
between endpoints. Both endpoints share that single bit. The binary error and
syndrome are unchanged; the full interior irrep record can change. Rough-boundary
m and R remain unmeasured. The bit, error truth, pairing, and fusion history are
not decoder inputs.

The edge prior is (1-p,p/2,p/2) on (off,forward,reverse). U(1)/SU(3) sum-product
BP marginalizes the hidden orientation, then passes the total active belief to
the same posterior-LLR matcher. Damping is 0.5, the iteration cap is 300, and
tolerance is 1e-10. Only the final measured residual and logical parity determine
failure. BP nonconvergence is retained separately.

For SU(2), all local fusion probabilities in this model depend on the number of
active incident edges, not on their orientation. Summing the two redundant
active states gives the original binary activity model exactly. The primary
SU(2) control uses this quotient before BP, preserving the directed finite-iteration
schedule; merely duplicating states would change normalized damping coordinates
and introduce an irrelevant algorithmic difference. Both orientation channels
are still sampled and their records and final decisions are checked shotwise.
This invariance is a statement about the present local classical fusion model,
not every possible microscopic quantum instrument.

The [validation](../results/a9-validation.json) compares three-state batch and
scalar inference, verifies a nontrivial tree posterior by independent enumeration,
checks U(1) latent charge conservation and boundary marginalization, exhausts
SU(2) local orientation products through degree four, and replays the directed
baseline. The [36-cell pilot](../results/a9-pilot.json) covers all six groups/lattices
at L=5,9 and p=0.1,0.3,0.5; pilot shots are not pooled into production.

Each production cell stores paired directed/hidden failure and convergence
indicators, their 2x2 counts, activity/record hashes, seeds, and frozen source
hashes. A separate orientation RNG preserves the original directed activity/fusion
stream. Every directed replay must match the original corrected counts.
[Acquisition status](../results/a9-acquisition-progress.json) reports current
coverage. The full output comprises six paired checkpoint files and their
compressed per-shot indicator records.

Primary-source context:

- [Temkin et al., Charge-Informed Quantum Error Correction](https://arxiv.org/abs/2512.22119)
  studies a charge-conserving U(1) model with a decoding transition. It motivates
  testing the noise/observation law instead of inferring no threshold from a finite scan.
- [Higgott et al., Improved decoding of circuit noise and fragile boundaries of tailored surface codes](https://arxiv.org/abs/2203.04948)
  provides the BP-to-matching precedent and illustrates decoder/boundary dependence.
- [Atkins, SU(2)'s Double-Covering of SO(3), section 9](https://www.sas.rochester.edu/pas/assets/pdf/undergraduate/su-2s_double_covering_of_so-3.pdf)
  derives fundamental pseudoreality, the representation-theoretic basis for the SU(2) control.

The [hidden-orientation LER figure](../figures/a9-hidden-orientation-ler.png),
[paired LER difference](../figures/a9-hidden-orientation-paired-effect.png), and
[BP nonconvergence diagnostic](../figures/a9-hidden-orientation-nonconvergence.png)
now contain all 600 cells, with 100/100 per panel. The
[figure input record](../results/a9-figure-inputs.json) binds the complete figures
to the six checkpoint hashes. The directed figure remains the baseline.

### Completed paired comparison

The registered exact McNemar tests use Holm correction across the 400 U(1)/SU(3)
cells. All 313 significant changes increase LER when orientation is randomized
and hidden; no significant decrease is observed. The remaining cells do not
establish equivalence. SU(2) is an exact quotient control rather than a powered
null-significance claim.

| Group | Square: significant increases / cells | Honeycomb: significant increases / cells |
| --- | --- | --- |
| U(1) | 95/100 | 80/100 |
| SU(2) | 100/100 cells have zero paired discordance | 100/100 cells have zero paired discordance |
| SU(3) | 88/100 | 50/100 |

The size curves show SU(2) crossing-like reversals on both geometries, unchanged
between channels. U(1)/SU(3) do not share one universal shape. In the hidden
channel, square U(1) has size curves that approach one another around
p=0.28–0.32; L=5 and L=11 then reverse ordering on the grid. Square SU(3) and
honeycomb U(1) approach more gradually near the upper end, while honeycomb SU(3)
continues to improve strongly with size through p=0.50. These are descriptions
of the registered grid, not crossing fits or proofs of threshold absence.

The researcher's KT/BKT-like interpretation of hidden-orientation square U(1)
is retained as a hypothesis: merging/drifting curves could reflect a critical
regime, a conventional transition with finite-size corrections, or decoder
approximation. At p=0.30 the L=5,7,9,11 LERs are 0.4105, 0.39775, 0.40175,
0.4052; corresponding BP nonconvergence fractions are 0.00005, 0.03145,
0.9705, 1.0. These numerical diagnostics do not themselves count as failures,
but make a universality inference from this slice particularly unsafe.

For the same nominal L=11 and p=0.30, hidden-channel LER is lower on honeycomb
than square for U(1) (0.0953 vs 0.4052), SU(2) (0.24705 vs 0.47765), and
SU(3) (0.00015 vs 0.0917). The directed comparison has the same ordering at
this slice. The underlying degree, edge count, path structure, and boundary
geometry differ; equal L is not a matched-resource theorem of lattice superiority.
All quoted counts, intervals, and diagnostics are in the
[paired analysis](../results/a9-orientation-analysis.json).

### What the orientation intervention tests

In the U(1) model, a fixed reference incidence matrix B maps an integer edge
current j to the observed charge q=Bj. Directed active edges have j=+1;
hidden-orientation edges have j=+1 or -1. The binary error is e=|j|.
Only detector rows of B are observed. Charge-compatible differences can include
cycles and paths ending at the unmeasured rough boundaries. Randomizing the sign
changes both the distribution over such currents and the charge likelihood of
an activity pattern; it is not merely a relabeling of the matching graph.

A local two-edge example prevents overinterpreting this as a universal
information-ordering theorem. If two active U(1) leaves have fixed equal signs,
their charge is ±2 and distinguishes them from no error. If the fixed signs
are opposite, their charge is zero and does not. Under independent hidden signs,
the charge is zero with probability 1/2 and ±2 with probability 1/4 each.
Thus the effect on local ambiguity depends on the fixed arrow configuration;
the complete lattice comparison is needed. This is algebra of the registered
fusion law, not an additional Monte Carlo finding.

For SU(2), the local singlet/triplet probabilities of two active fundamentals
are 1/4 and 3/4 regardless of orientation. For SU(3), a fundamental–antifundamental
pair yields the singlet/adjoint probabilities 1/9 and 8/9, whereas two fundamentals
yield different nontrivial irreps. Both conjugacy and the richer full-irrep
record matter. The scan can test the practical consequence of randomizing pair
orientation; it cannot isolate a universal explanation from conjugacy alone.

## Status

The complete production audit passes: 600 cells, 12,000,000 paired trials,
600/600 directed replays matching the corrected baseline, and 4,000,000
SU(2) trials with identical records, logical-failure flags, and convergence
flags. Current checkpoint, per-shot indicator, baseline, and scientific-source
hashes were rechecked on 2026-09-09. See the
[full-data analysis and integrity audit](../results/a9-orientation-analysis.json).
Pilot shots and quarantined stale-validation startup files remain excluded.

LER intervals are pointwise Wilson 95%. The paired difference uses discordant
counts with conservative 95% bounds from two 97.5% Clopper–Pearson intervals.
Exact McNemar tests use Holm correction over the 400 U(1)/SU(3) cells. No
simultaneous-curve or threshold claim follows from pointwise bars. A practical
LER change supports an orientation effect for this decoder, but cannot alone
separate intrinsic information loss from loopy BP approximation or establish a
thermodynamic transition. The two channel-specific R records are intentionally
different, so this is a physical-channel intervention, not a nested-record theorem.

## Related pages

- [Directed logical-rate evidence](ler-curves.md)
- [Method overview](overview.md)
- [Scoring correction](a8-ler-scoring-correction-2026-09-05.md)

- [Interpretation, limits, and theory handoff](interpretation.md)
