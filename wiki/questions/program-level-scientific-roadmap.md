---
title: Program-level scientific roadmap after the finite-window phase map
page_type: question
status: proposed-program
updated: 2026-09-14
source_refs:
  - labs/lab-007-decoding-statistical-mechanics/REPORT.md
  - references/dennis2001-topological-quantum-memory/paper.pdf
  - references/fan2023-mixed-state-topological-memory/paper.pdf
  - references/lessa2024-swssb-mixed-states/paper.pdf
  - references/moharramipour2024-symmetry-enforced-entanglement/paper.pdf
  - references/pattison2021-soft-information-qec/paper.pdf
  - references/temkin2025-charge-informed-qec/paper.pdf
  - references/jing2025-intrinsic-heralding/paper.pdf
  - references/iqbal2023-nonabelian-topological-order/paper.pdf
  - references/lyons2026-anyonic-fault-tolerance/paper.pdf
  - references/sala2025-decohering-nonabelian-topological-order/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Topological Phases, Symmetry-Enriched Systems]
---

# Program-level scientific roadmap after the finite-window phase map

**Summary**: The next flagship problem should ask whether symmetry-resolved
fusion information defines a distinct, physically realizable recoverability
transition in noisy non-Abelian topological memory, and what observation record
is minimally sufficient to reach it. More phase-map smoothing is supporting
analysis, not the scientific center.

**Sources**: [Topological Quantum Memory](/reference?id=dennis2001-topological-quantum-memory); [Diagnostics of Mixed-State Topological Order and Breakdown of Quantum Memory](/reference?id=fan2023-mixed-state-topological-memory); [Strong-to-Weak Spontaneous Symmetry Breaking in Mixed Quantum States](/reference?id=lessa2024-swssb-mixed-states); [Symmetry Enforced Entanglement in Maximally Mixed States](/reference?id=moharramipour2024-symmetry-enforced-entanglement); [Improved Quantum Error Correction Using Soft Information](/reference?id=pattison2021-soft-information-qec); [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec); [Intrinsic Heralding and Optimal Decoders for Non-Abelian Topological Order](/reference?id=jing2025-intrinsic-heralding); [Non-Abelian Topological Order and Anyons on a Trapped-Ion Processor](/reference?id=iqbal2023-nonabelian-topological-order); [Quantum Computing with Anyons Is Fault Tolerant](/reference?id=lyons2026-anyonic-fault-tolerance); [Stability and Loop Models from Decohering Non-Abelian Topological Order](/reference?id=sala2025-decohering-nonabelian-topological-order)

**Last updated**: 2026-09-14

## What the strongest papers treat as a major question

The common pattern is not “implement a decoder and report a threshold.” The
papers make a larger chain of claims:

1. **Define a new physical information structure.** Dennis *et al.* formulate
   topological memory as hidden-string inference under local faults. Pattison
   *et al.* retain analog measurement outcomes. Temkin *et al.* add measurable
   conserved anyon charge. Jing *et al.* exploit nondeterministic non-Abelian
   fusion products as intrinsic heralds.
2. **Identify the information-theoretic or optimal limit.** The question is
   whether the extra record changes what is recoverable, not merely whether one
   heuristic decoder happens to improve. Temkin and Jing therefore construct
   conditioned optimal decoders or statistical-mechanical optima alongside
   practical algorithms.
3. **Explain the transition.** Dennis maps decoding to disordered statistical
   mechanics; Fan connects optimal decoding to intrinsic mixed-state order;
   Lessa supplies recoverability and SW-SSB language; Temkin asks for the phase
   structure and universality of a symmetry-enriched loop model.
4. **Make it fault tolerant.** Jing explicitly identifies noisy measurement,
   hidden internal charge, adaptive measurement, and 3D Steiner/statistical
   mechanics as open problems. Lyons and Brown move to spacetime records,
   just-in-time commitments, active correction, and resource overhead.
5. **Tie the theory to a realizable platform.** Iqbal *et al.* make preparation,
   anyon control, fusion/braiding observables, fidelity, and gate capability the
   scientific targets—not just a numerical threshold.

This synthesis changes the role of Lab 003. Its continuous evidence map is a
useful diagnostic of the current toy observation model, but it does not yet
show that the herald is a consistent fusion measurement, quantify its intrinsic
information value, establish an optimal transition, or survive faulty repeated
measurements.

## Recommended flagship question

> **Does partial symmetry/fusion-channel readout produce a distinct
> recoverability transition in a noisy non-Abelian or symmetry-enriched
> topological memory, and what is the minimal measurement record required to
> attain that transition?**

This question is larger than “does herald-aware BP+MWPM beat MWPM?” It separates
three logically different objects:

- the physical channel that produces the topological syndrome and
  representation/fusion record;
- the information-theoretic optimum conditioned on a specified portion of that
  record; and
- the computational gap between the optimum and scalable decoders.

It also creates a genuine connection between intrinsic heralding, mixed-state
recoverability, non-Abelian symmetry-enforced information, and fault-tolerant
anyon computation.

## Observation hierarchy to compare

For one fixed microscopic noise model, define nested records rather than a
single ad hoc q parameter:

| record | decoder sees | scientific purpose |
|---|---|---|
| \(O_0\) | endpoint/topological syndrome only | matched conventional baseline |
| \(O_1\) | syndrome plus the currently proposed local herald field | practical compressed readout |
| \(O_2\) | syndrome plus physically allowed local fusion outcomes | microscopic representation-resolved record |
| \(O_3\) | complete allowed fusion/history record | information-rich oracle limit |
| \(O_t\) | noisy repeated versions of the chosen record | fault-tolerant spacetime problem |

Data processing requires the optimal Bayes risk not to worsen as the record is
enlarged. Violating this ordering would expose a simulator, likelihood, or
decoder bug. The gaps between levels quantify information that is lost by
measurement compression; the gap between exact and scalable decoding at one
level quantifies algorithmic loss.

## Research sequence

### WP1 — derive the physical observation channel

Choose one concrete model already connected to theory or experiment, preferably
the \(D_4\) model used by Jing and realized by Iqbal, before returning to a
continuous \(SU(2)\) generalization. Derive \(P(E,O_i)\) from its error and
measurement operations, including allowed fusion outcomes and which internal
information is inaccessible. The current degree-threshold herald can remain as
a compressed phenomenological model, but it must be related to \(O_2\) by an
explicit stochastic coarse-graining.

**Gate:** no threshold scan until every simulated observation has a physical
measurement definition and normalization/consistency tests.

### WP2 — measure intrinsic information, independent of BP/MWPM

On small periodic systems, compute exact or tensor-network posterior logical
probabilities for \(O_0,O_1,O_2,O_3\). Report conditional logical entropy,
optimal logical failure probability, and information gained by each refinement
of the record. Compare the current BP+MWPM decoder against the exact optimum on
the same instances.

**Decisive outcome:** establish whether herald advantage is primarily new
information or merely a better weighting heuristic. If \(O_1\) carries little
conditional logical information, stop optimizing its phase map and redesign
the measurement.

### WP3 — derive the transition and its order parameter

Seek a partition-function, replicated, loop, or channel-recoverability mapping
for the optimal \(O_i\)-conditioned problem. Determine which quantity has a
principled thermodynamic meaning: logical Bayes risk, conditional mutual
information, fidelity/Rényi correlator, Wilson-loop sector probability, or a
new representation-resolved diagnostic. Only after this derivation should the
project fit asymptotic critical scaling or make a universality claim.

**Decisive outcome:** a phase transition defined independently of one decoder
implementation, together with a statement of whether additional fusion
information moves the transition or changes its universality class.

Sala and Verresen give a concrete template for the first half of this step: for a fixed non-Abelian anyon-proliferation channel, the quantum dimension enters a loop-model weight and logical-state fidelity can be tied to random loop/spin models. [Sala and Verresen (2025), pp. 1–5](/reference?id=sala2025-decohering-nonabelian-topological-order) The project must still derive its own mapping from its chosen microscopic channel and observable \(O_i\); importing their stability regime without that derivation would conflate a density-matrix property with a herald-conditioned decoder threshold.

### WP4 — make the record noisy and spacetime resolved

Introduce explicit false/missed fusion outcomes and repeated measurement rounds.
Compare batch optimal inference, scalable factor-graph/matching or cluster
decoders, and just-in-time commitment. Test whether internal non-Abelian charge
hides correctable information and whether adaptive measurement bases recover it,
as suggested by the open problems in Jing and the JIT construction of Lyons and
Brown.

**Decisive outcome:** a fault-tolerant threshold surface versus data noise,
topological-syndrome readout noise, and fusion/herald readout noise—not merely a
perfect-measurement 2D threshold.

Lab 005 now owns this work package. Its first implementation separates the
causal schedule from the inner spatial decoder and verifies the local
spacetime-ILP algebra plus bounding-cube age predicate of Jing *et al.* It does
**not** yet reproduce the Lyons–Brown D(S3) JIT state machine: absorber
distance, deferred measurement reversal, ungauging, neutrality, re-gauging,
and linked-cluster behavior remain pending. Repeated noisy D4 herald readout is
a separately labelled project extension linked to Lab 004.

### WP5 — connect to experiment and resources

Translate \(O_1\) or \(O_2\) into a measurement protocol compatible with the
trapped-ion \(D_4\) operations demonstrated by Iqbal *et al.* Estimate added
measurements, feed-forward depth, classical latency, and logical-error reduction.
Compare resource cost with a matched conventional surface-code architecture,
following the program-level comparison advocated by Lyons and Brown.

## Secondary big questions

1. **Universality across symmetry data.** Which group/category properties—quantum
   dimension, fusion multiplicity, conserved representation labels, or ability
   to hide charge—control the information gain and universality class?
2. **Measurement design.** Which adaptive basis or compressed local statistic
   maximizes logical information per measurement and per unit latency?
3. **Complexity versus information.** Does intrinsic heralding only raise the
   optimal threshold, or can it also change the computational complexity of
   approaching optimal recovery?
4. **Decoder-independent experimental diagnostics.** Can the same measured
   record estimate a fidelity/conditional-information observable that diagnoses
   recoverability without relying on a particular decoder?

## Immediate next experiment

The next bounded lab should be **Exact information hierarchy on small \(D_4\)
or physically derived herald instances**, not another global phase-map sweep.
Start with a finite set of small tori, enumerate or tensor-contract the posterior
under \(O_0,O_1,O_2\), and compare exact Bayes risk with the current scalable
decoder. This experiment is small enough to falsify the central mechanism and
large enough to determine whether the present herald variable deserves further
large-scale threshold work.

Lab 003 should receive only two remaining maintenance items: preserve the B15
collaborator figure and, if publication-strength use is requested, replace the
current independent posterior propagation with a preregistered seed-cluster or
fresh-confirmation uncertainty analysis. Neither item should monopolize the
scientific program.

### 2026-08-29 evidence update — primitive hierarchy closed, transfer test next

Lab 004 R4.5c now completes the exact noiseless primitive sequential comparison.
For four registered priors, optimal O2 retains lower risk than optimal O0, so
the physically allowed fusion record carries real decision-relevant
information on the primitive channel. The published public O2 policy remains
far above that limit, and its larger contribution comes from the first
herald-weight action rather than the unit-weight second charge recovery.
Future-aware selection improves over the matched myopic first action by zero or
at most `9.75e-4` for O2 on this fixture. These are exact finite-channel facts,
not scaling or fault-tolerance evidence.

This result advances WP2 from “is there intrinsic information?” to “does the
public algorithmic gap persist beyond the primitive?” Lab 004 therefore
registers R5a, a matched paper-normalized `L={2,3}` finite-size pilot of the
syndrome-only and published heralded public policies. It reports risk and stage
decomposition with 90% intervals and forbids threshold/crossing fits. The D4
inner-decoder interface to Lab 005 follows only after this transfer check;
Lab 005's source-matched D(S3) JIT state-machine work remains independently
runnable.

R5a produced a 20,000-trajectory historical cohort, but R6AH has now withdrawn
its complete-pipeline interpretation. The frozen first record exposes inactive
support, the second record retains sentinels, and the legacy charge boundary
mixes public action with private relation/effective-error truth. Physical draws
and lattice/topology records remain provenance; the numerical risks, policy
differences, stage mechanism, size directions, and Lab 005 baseline promotion
are not current evidence. R6AF is the corrected replacement only at its own
registered four-cell pilot scope.

### Researcher decision — D4-first decoder program

On 2026-08-28 the researcher selected the D4-first branch. Lab 004 now owns the
bounded reproduction of Jing *et al.*: first the physical D4 observation model
and published heralded PyMatching rule, then an exhaustive/MILP small-system
oracle and the exact conditioned logical posterior. Lab 002 remains the scalable
belief-matching branch and will be compared only after both decoders consume the
same validated D4 record. Neural decoding is deferred to a separate future Lab.

R6A now registers the observation-likelihood gate for that comparison. It does
not map D4 charge outcomes onto the old binary degree-threshold herald. Instead,
it tests exact-oracle, local-support, and support-plus-public-parity factor
graphs on the complete primitive-size-2 public support (8 vertices, 12 edges,
not the 24-vertex/36-edge paper-normalized `L=2` supercell). Only an exact,
observation-only representation may release later BP work; otherwise the
project must identify a richer factor graph or explicitly label an approximate
likelihood before measuring an algorithmic gap.

The R6A exact fixtures and complete finite-support matrix now confirm why this
gate matters. A trivial-loop
record has local-support weight (1/64), while two independent parity factors
produce the oracle value (1/16); a parity-violating charge record is positive
under support-only factors but impossible under the oracle. Across all 16,230
supported public observations and 49,855 compatible pairs, F1 has exact support
but 64 likelihood-weight errors; candidate-ledger F2 has none. All compatible
candidates for a given observation share at most one parity-scope signature,
establishing finite primitive-size-2 public-scope consistency. The remaining
gate is both constructive and scale-validating: derive those scopes from the
fixed lattice and public record, then test them on bounded paper-normalized
geometry without an exponential observation or candidate lookup before
promoting the representation to decoder-visible BP.

R6B resolves that direct-scope branch negatively on the paper-normalized
24-vertex/36-edge `L=2` graph. An exact degree-CSP matrix fully enumerates all
compatible assignments for 1,000 fresh-seed public records with zero censoring:
991 records have one nonwinding scope signature, but 9 have two. All 12
isolated-hex controls pass. Therefore the public flux and measured-support
record does not uniquely determine a direct charge-parity scope list. Exact D4
belief matching, if possible, requires a fixed graph whose factors retain
latent edge/connectivity structure rather than preprocessing the observation
into one scope list.

R6C verifies one such fixed finite-graph representation. Geometry-fixed factors
activate from latent cycle and boundary edge bits and then enforce public
charge parity. They reproduce all 49,855 primitive likelihoods and 120 probes
covering all nine paper-`L=2` ambiguous records with zero error. This closes
finite-graph expressibility but not scalability: the paper-`L=2` catalog has
1,068 simple-cycle factors, some spanning all 36 edges. The next decoder gate
is therefore an exact local connectivity-auxiliary compression, not BP tuning
or performance sampling.

R6D now supplies that compression as a nonnegative local edge-flow graph. Two
binary auxiliary bits per physical edge, one per charge colour, turn loop
charge parity into local edge pins, degree-two XOR constraints, and
degree-dependent normalizations. Direct sums over all primitive edge-flow
assignments, the complete primitive likelihood matrix, and every registered
paper-`L=2` ambiguity probe agree exactly. Paper-`L=2` needs 72 binary
auxiliaries and 120 bounded-arity factors rather than 1,068 simple-cycle
factors, with `O(V+E)` growth. This releases exact BP message construction as
the next scientific gate; it does not yet localize the winding-sector terminal
test or establish BP convergence, decoder performance, a threshold, or fault
tolerance.

R6E now separates exact representation from inference quality. Exact
table-message updates pass factor-tree controls, but a single factor cycle is
already biased after convergence. On 32 matched primitive-D4 rows, raw BP
converges on none and produces six hard-message contradictions; damping 0.25
converges on 10, yet no row both converges and matches exact marginals within
`1e-8`, with error as large as `0.5`. Ordinary loopy BP on the R6D graph is
therefore rejected as an exact posterior solver. The next scalable-decoder
question is structural—region/cluster inference, graph refactorization, or a
controlled approximation—not correction or LER benchmarking of the rejected
fixed point.

R6F resolves the first structural fork with a matched exact-preserving matrix.
Merging edge pins and vertex factors reduces hard contradictions from six to
two and the median converged maximum marginal error from `0.5` to
`9.146e-3`, so the original redundant short loops were a real source of bias.
The bounded graph still converges on only `8/32` rows and is exact on `0/32`.
By contrast, exact elimination of all flow auxiliaries into one primitive
physical-likelihood factor gives a tree that converges and is exact on
`32/32`. The next decoder question is therefore the minimal region/junction
or elimination width needed to retain that exactness with controlled growth;
more damping and LER sampling are not scientifically licensed by this result.

R6G now quantifies the structural cost of exactness. On the primitive graph,
the best registered min-fill order has a 16-variable maximum cluster and exact
bucket contraction matches independent evidence to `1.780e-15`. Reducing the
factor count from 48 to 20 via R6F superfactor merging does not reduce maximum
cluster size. At paper-normalized `L=2`, the best registered order for either
representation needs a 36-variable cluster, corresponding to `2^36` dense
entries. Thus the next scalable-decoder question is no longer “which damping
value?” or “which local merge?” but which controlled region, cutset, or tensor
approximation gives the best primitive marginal accuracy per structural cost.
The widths are registered-order upper bounds, not optimal-treewidth results.

R6H measures exact cutset conditioning rather than guessing a larger-region
decoder. Eighteen primitive contractions recover independent evidence to
`1.780e-15`. On paper-`L=2`, auxiliary-only conditioning reaches residual
cluster 20 at `k=12` unclustered and `k=13` superfactor, earlier than
physical-only and, nontrivially, the registered unrestricted heuristic.
Crossing still carries a `k+cluster` work proxy of 32--44. Exact cutsets solve
the registered peak-memory constraint by moving cost into branches; they do
not yet supply a scalable decoder. The next controlled question is
approximation accuracy per structural cost against the exact primitive
posterior and this frontier.

R6I adds a bounded mini-bucket baseline with explicit maximum scope `i`.
Exact-ceiling controls pass, but tighter evidence bounds do not guarantee more
accurate marginals: one branch worsens from maximum error `0.090` to `0.126`
as `i` grows from 10 to 14, while another shows exact normalized clamped
pseudo-marginals despite a very loose evidence bound. At paper-`L=2`, the
registered branches still differ by 6.623 decades at `i=20`. This makes the
next high-information step a multi-observation exact-reference validation of
the approximation, not decoder correction or LER benchmarking.

R6J repeats that approximation on four observation strata and two priors. All
56 exact-ceiling controls pass, but no representation/order branch at `i<=14`
meets a 0.01 maximum-marginal-error gate on all eight conditions. Favorable
clamped-bound cancellation occurs in only 20/32 auxiliary-first low-`i` rows;
three evidence-bound sequences and 14 marginal-error sequences are nonmonotone
because the greedy partitions are not nested across `i`. The next method must
therefore improve the bounded region/partition construction on this exact
cohort before any decoder-performance study.

R6K separates nonmonotone bound selection from inadequate region content. A
cumulative envelope of valid total and clamped evidence bounds removes all
three evidence monotonicity violations, but marginal-error violations only
change from 14 to 13, useful low-`i` coverage stays at 20 rows, and zero
representation/order branches become uniformly accurate. The negative result
rules out further bound-selection cleanup as the main research direction: the
next discriminating experiment must change bounded factor coupling—through a
content-aware partition or explicit region construction—on the same exact
cohort before selecting GBP/tensor machinery or generating decoder LER data.

R6L completes the content-aware partition test. Its zero-safe local tightening
heuristic changes 38 matched rows and reads nontrivial factor content in all
128 candidate rows, yet low-scope marginals split evenly between 17
improvements and 17 regressions. Useful coverage stays at 20 rows and no
branch becomes uniformly accurate, even though 25 low-scope evidence bounds
tighten. This closes mini-bucket packing as the next scientific lever. The
remaining affordable fork is now an approximation-family question: compare a
bounded explicit region/join graph and a bounded tensor contraction against
the same exact primitive posterior before choosing an implementation for
paper-scale decoding.

R6M now tests whether both families even have valid matched constructions.
Every registered bounded join graph passes factor assignment, cap, separator,
and running-intersection checks, and exact COPY-tensor contractions reproduce
independent partition functions below `1e-15` relative error. Generic
compressed contraction nevertheless fails the prospective zero-safety gate:
the bounded-superfactor representation is finite at all three bonds and exact
at bond 8 on the scalar, but the unclustered representation reproducibly fails
QR normalization at bond 4 and 8 because its deterministic zeros generate
nonfinite intermediates. The program therefore does not silently compare IJGP
only with the successful tensor representation. A zero-safe tensor smoke on
the same target is the next prerequisite; posterior accuracy and LER remain
blocked.

## SU(N) formulation gate completed; typical-record scaling remains open

Lab 007 supplies an exact sector partition function for the inherited classical
full-irrep instrument, its SU(2) orientation quotient, a constrained U(1)
current/height model, and explicit SU(3) source and decoder-hardening
obstructions. Its restricted trivalent singlet loop weights cannot be used as
an unqualified typical-record transition theory. This advances WP2/WP3 from
formulation to controlled intrinsic inference; it does not resolve the
microscopic quantum-channel gate or thermodynamic universality.
[Lab 007, formulation and checks](/lab?id=lab-007-decoding-statistical-mechanics).

The next discriminating direction is an exact finite-width sector contraction
with the same physical channel, full record, rough boundaries and binary score,
paired with exact-marginal and BP-marginal matching. A periodic integer-winding
or BKT study requires a separately specified geometry, observable and effective
theory. See [[models/representation-informed-sector-model|the sector model]]
and [Lab 007, follow-on design](../../labs/lab-007-decoding-statistical-mechanics/wiki/predictions.md).

## Related pages

- [[thesis|Herald Decoder research program]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
- [[methods/fault-tolerant-anyonic-decoding|Fault-tolerant anyonic decoding]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [Lab 004 — D4 intrinsic-heralded decoder reproduction](/lab?id=lab-004-d4-intrinsic-heralded-decoding)
- [Lab 005 — Spacetime just-in-time anyonic decoding](/lab?id=lab-005-spacetime-jit-anyonic-decoding)
