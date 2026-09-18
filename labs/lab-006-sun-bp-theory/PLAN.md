# Plan — SU(N) full-irrep belief propagation

## Final disposition — 2026-09-09

Lab 006 is complete at its numerical evidence boundary. All 600 paired cells
and 12,000,000 paired trials pass the full-data audit; 600 directed replays match
the corrected baseline, and all 4,000,000 SU(2) control trials agree. The three
hidden-orientation figures and short final analysis are integrated. No threshold
or KT/BKT transition is claimed. See the [final interpretation](wiki/interpretation.md)
and [closure delivery audit](results/closure-delivery-2026-09-09.json).

No Lab 006 acquisition remains active. The next scientific deliverable is the
[Lab 007 statistical-mechanics theory plan](../lab-007-decoding-statistical-mechanics/PLAN.md),
with Lab 006 as its parent. The sections below retain the registered protocols
and changes as provenance, not instructions to resume completed sampling.


## Question

For an oriented lattice bond, an elementary error creates an SU(N) pair
\(\bar {\mathbf N}\to\mathbf N\). Can the complete local irrep readout
and binary boundary syndrome be written as a normalized likelihood
\(p(s\mid e)\), and can its posterior be inferred by belief propagation?

## Frozen conventions

* Every edge \(a=(u\to v)\) has a binary error \(e_a\).  When active it
  deposits \(\bar{\mathbf N}\) at \(u\) and \(\mathbf N\) at \(v\).
* At a site \(v\), the ordered incident leaves are fused to a total irrep
  \(R_v\). The complete decoder-visible record is \(s_v=(m_v,R_v)\): the
  binary topological boundary syndrome and complete irrep projector outcome.
* For a leaf list \(L_v(e)\), let \(M^R_{L_v}\) be the multiplicity of
  \(R\) in its tensor product.  An SU(N)-invariant, maximally mixed local
  instrument has \(P(R\mid L)=M^R_L\dim R/N^{|L|}\).  This is normalized by
  the dimension identity for a tensor-product decomposition.
* The full irrep \(R_v\) itself is the representation-resolved heralding
  signal. No lower-resolution binary field or additional readout channel is
  part of this model.

## Acceptance gates

1. State and normalize the SU(N) likelihood, including the \(\mathbf N\otimes
   \bar{\mathbf N}=\mathbf1\oplus\mathrm{Adj}\) channel.
2. Derive sum-product updates from Bayes' rule and prove exactness on a tree.
   Explicitly reject the stronger, false claim that a loopy BP fixed point is
   automatically the global Bayesian posterior.
3. Run a deterministic SU(3) small-lattice enumeration.  Verify BP equals
   exact marginals on a tree and compare it with exact inference on a plaquette.

## Scope boundary

This is a theory-oriented successor of Lab 002, not a replacement for its
phenomenological Z2 decoder. Exact enumeration is restricted to degree-two
SU(3) small graphs. The public explanatory backend covers U(1), SU(2), and
SU(3) product distributions through degree four on the canonical Lab 002
geometries. The derivation itself is for SU(N) and arbitrary fusion
multiplicities (computable, e.g., by Littlewood--Richardson rules).

## Phase A1 — compiled belief-matching decoder

Separate the generalized syndrome explicitly as \(s_v=(m_v,R_v)\).
The measured \(\mathbb Z_2\) endpoint parity \(m_v\) supplies the hard
matching constraint, while the SU(N) irrep reweights the
edge posterior.  This repairs the first prototype's implicit identification
of an irrep label with the binary topological syndrome.

Implement synchronous probability-damped Numba sum-product over cached dense
local factor tables. Convert edge marginals \(r_a\) to the complete Bernoulli
posterior LLR \(w_a=\log[(1-r_a)/r_a]\), then call maintained PyMatching.
The optimized path will reuse topology and work buffers and will expose a
batch inference API so Python dispatch is not the throughput bottleneck.

### A1 acceptance gates

1. Local likelihoods include the explicit binary \(m\) report.
2. Optimized and reference BP agree to \(10^{-12}\), including convergence
   state and iteration count, on registered path and plaquette fixtures.
3. Every matching correction reproduces the supplied perfect \(m\)-syndrome.
4. A warmed, matched 64-site degree-two SU(3) ring benchmark reports reference,
   scalar-compiled, and batched-compiled inference time on 256 observations.
5. Exact enumeration remains the small-graph correctness oracle; compilation
   does not change the tree/loopy exactness boundary.

## Phase A2 — U(1)/SU(2)/SU(3) full-irrep belief-matching workbench

Create a Lab Results artifact analogous to the Lab 002 workbench, driven by
the A1 cached/preallocated Numba recurrence. Use the canonical Lab 002 square
and honeycomb geometries with rough left/right and smooth transverse
boundaries, and the same binary edge-error prior for three local fusion models:

* U(1): one-dimensional irreps labelled by integer charge, with fusion by
  addition and an active edge depositing \(-1\to+1\);
* SU(2): the pseudoreal fundamental \(2\cong\bar2\), with
  \(2\otimes2=1\oplus3\) and projector probabilities \(1/4,3/4\);
* SU(3): \(3\otimes\bar3=1\oplus8\),
  \(3\otimes3=6\oplus\bar3\), and its conjugate.

The common visual language assigns cool teal to a fundamental/source-positive
label, magenta to an antifundamental/source-negative label, amber to adjoint
channels, indigo/rose to symmetric conjugate pairs, and renders no mark for a
trivial irrep.  For SU(2), orientation tags may retain source sign but must not
misrepresent \(2\) and \(\bar2\) as inequivalent irreps.

### A2 delivery gates

1. The API payload is deterministic by seed, uses the Numba inference path,
   exposes posterior LLRs and a syndrome-faithful PyMatching correction, and
   validates all three fusion tables.
2. The page exposes observation, posterior, and decoding layers; group changes
   alter the actual backend likelihood rather than only relabelling colors.
3. Every nontrivial irrep has a stable accessible label and color; trivial
   irreps are absent from the lattice marks and explained in the legend.
4. The exact Lab Results embed, API route, responsive layout, group switching,
   edge selection, and light/dark rendering are verified in the browser.

## Phase A3 — full-irrep interface remediation

The corrected model fixes \((m_v,R_v)\) as the unique public record. Remove
the previously introduced auxiliary binary observation and its noise parameter
from the derivation, reference implementation, compiled kernel, evidence files,
API, artifact, metadata, and Wiki. The workbench must compare paired
\(P(e\mid m)\) and \(P(e\mid m,R)\) posteriors. Its original signed
probability-difference layer is historical and is superseded by the A6
error-LLR effect before the full-irrep decoding result. The frozen A3 gates are in the
[A3 manifest](manifests/a3-full-irrep-interface-remediation-manifest-2026-09-04.json).

## Phase A4 — canonical two-dimensional public artifact

Replace the ring on the public surface with the exact square and honeycomb
constructors used in Lab 002. Show the complete \((m,R)\) record, the
full-irrep posterior, the signed heralding effect relative to the matched
\(m\)-only posterior, and the final correction. A6 supersedes the original
probability-difference coordinate with an error-LLR difference. Render rough and smooth boundaries and
expose convergence, iteration, and residual diagnostics. The ring remains only
an exact-enumeration and throughput fixture. See the
[A4 manifest](manifests/a4-two-dimensional-full-irrep-workbench-manifest-2026-09-04.json).

## Phase A5b — frozen two-dimensional convergence scan

Probe failure rather than only an easy fixture. The registered grid contains
square/honeycomb, \(L=5,7\), SU(2)/SU(3), \(p=0.1,0.2,0.3,0.4\), and four
independent seeds per cell, for exactly 128 observations. Pair full-\((m,R)\)
and \(m\)-only inference under the same synchronous, damping-0.25, 80-iteration
schedule. Report nonconvergence without retuning or adaptive extension. No
threshold or logical-performance analysis is permitted. A5 was censored before
result creation because its registered grid product was wrong; A5b is the
corrected prospective contract. See the
[A5b manifest](manifests/a5b-two-dimensional-convergence-scan-manifest-2026-09-04.json).

## Phase A6 — LLR heralding-effect remediation

The current public effect coordinate supersedes the raw posterior-probability
difference used in A3/A4. Define the edge heralding effect as the difference of
error log-odds between the matched full-\((m,R)\) and \(m\)-only arms. Equivalently,
it is the log Bayes factor supplied by \(R\), or the \(m\)-only matching weight
minus the full-record matching weight. Color positive shifts red, negative
shifts blue, and encode absolute LLR shift in width. No sampling or comparative
performance claim is part of this remediation. See the
[A6 manifest](manifests/a6-llr-heralding-effect-remediation-manifest-2026-09-04.json).

## Phase A7 — directed, boundary-blind fusion LER and threshold study

The best Lab 006 decoder is the **directed full-record sum-product
belief-matching decoder**: cached local fusion likelihoods, preallocated
batched Numba BP, posterior error LLRs, then syndrome-faithful PyMatching. It
is exact only on a factor tree; on these loopy lattices it is a practical
Bethe-plus-matching decoder, not global MAP.

This claim-bearing finite-size study uses the artifact's accepted default
decoder, rather than selecting a new schedule. Its frozen configuration is
directed sum-product BP, damping `0.50`, `max_iterations=300`, tolerance
`1e-10`, and `measure_boundary_representation=false`. A7a is therefore only a
compatibility and throughput gate for the LER runner; it cannot change these
settings. A7b uses the identical decoder for LER sampling. The directed
channel is first: an active stored arrow deposits antifundamental at its tail
and fundamental at its head. Hidden-orientation/undirected decoding is a later
sensitivity study, never pooled with this channel.

All sampled configurations expose the same perfect binary **interior detector
syndrome** needed for recovery. Rough boundaries expose neither a syndrome nor
a representation herald: both are marginalized in BP, while the boundary is
available only as an allowed correction endpoint. The three matched arms are:
**no herald** (ordinary prior-weighted PyMatching with hard interior-detector
syndrome only); **syndrome-only** (BP conditioned on interior `m`, ignoring all
`R`); and **representation herald** (BP conditioned on interior `(m,R)`).
Compare `None`, U(1), SU(2), and SU(3) actual likelihoods. `None` is the
falsification control: its representation-herald and syndrome-only arms must
be numerically identical.

### A7a — artifact-compatibility and batch-throughput gate

Freeze the above artifact default on every LER arm. On fixed-seed square and
honeycomb fixtures for every group and observation arm, verify that the LER
runner's scalar decoder reproduces the artifact backend's posterior, BP
convergence fields, matching weights, correction, residual, and logical parity.
Then compare scalar and chunks-of-256 Numba BP: posterior entries must agree
within `1e-12` and convergence/iteration fields must agree exactly. Batch BP
may replace only the inference loop; the subsequent PyMatching projection stays
per shot unless a separately validated batched matching implementation exists.
The `None` full-record/syndrome-only identity and no-rough-boundary-record gate
also apply. Any mismatch blocks A7b pending a remediation of the runner, not a
change to the artifact decoder or an adaptive retuning.

**A7a result (2026-09-04):** the calibration ran 16 fixed-seed artifact cells:
all four groups, square/honeycomb, and `L=5,9`, with eight scalar records per
arm and the same records repeated to 256 entries per batch. The artifact and
scalar runner agreed exactly; batch and scalar BP agreed exactly in posterior,
convergence, and iteration count. Batch BP timing was instance-dependent
(0.31–1.73x scalar BP, median 1.00x), so it is correctness-approved but not
claimed as a universal acceleration. See the
[calibration result](results/a7-artifact-default-calibration.json).

**Exploratory immediate-look result (2026-09-05):** to provide a figure before
the registered production acquisition, 32 independent matched shots were run
per cell on the reduced `L={5,9}`, eight-point `p` grid. This figure is an
operational diagnostic only: its wide Wilson intervals make it unsuitable for
an LER comparison or crossing estimate. Its BP nonconvergence counts are a
separate numerical diagnostic and are not logical failures.
It neither replaces nor contributes shots to A7b's registered 20,000-shot
cells. See [preliminary raw aggregates](results/a7-ler-preliminary32.json) and
the [preliminary curve](results/a7-ler-preliminary32.png).

**Exploratory 512-shot result (2026-09-05):** the same reduced grid was
repeated with 512 independent matched shots per cell. The tighter LER figure
still contains strongly group-, geometry-, size-, and record-dependent BP
nonconvergence. The accompanying convergence figure is required context for
every displayed LER point. This result is exploratory and cannot select an A7b
crossing or threshold bracket; it identifies the need for the registered
high-statistics curves to preserve the convergence component explicitly.

### A7b — matched LER curve and threshold analysis

With the A7a compatibility gate passed, sample directed square and honeycomb patches at
`L={5,7,9,11}` and `p={0.02,0.04,...,0.30}`. Draw 20,000 independent physical
errors per `(lattice,L,p)` cell in chunks of 256; share every truth draw,
binary syndrome, seed, and fusion-sampling uniform variate across groups, and
share the resulting group-specific interior `R` record across its three arms.
Store correction, residual syndrome, convergence, and
logical parity of `error XOR correction`. Primary decoder failure requires a
nonzero final detector residual or nontrivial logical parity. BP convergence
is recorded separately and never gates LER: the final BP beliefs always pass
to PyMatching. Plot Wilson 95% intervals. A fresh, separately registered
five-point, 40,000-shot refinement is permitted only when the coarse scan has a
predeclared L=7/L=11 overlap or a signed LER-difference change in an adjacent
`p` interval. Report only a decoder/channel/schedule-specific finite-size
crossing or bracket; no asymptotic, optimal, fault-tolerant, or undirected
threshold claim is allowed.

Acceptance requires 1e-12 scalar/batch posterior agreement for each group and
arm, the `None` equality control, syndrome-faithful corrections, matched truth
and seed hashes, retained nonconvergence counts, and a rendered figure verified
against the exact raw result. The complete prospective contract is the
[A7 manifest](manifests/a7-directed-boundary-blind-ler-threshold-plan-2026-09-04.json).

## Phase A8 — artifact-default full-record LER curves

Supersede A7's reader-facing comparison matrix. The only decoder record is the
artifact's complete interior ((m,R)) record. Fix directed sum-product BP,
damping 0.5, 300 iterations, posterior-LLR PyMatching, and no rough-boundary
record. Measure U(1), SU(2), and SU(3) on honeycomb and square lattices, but
render one lattice/group per figure—not a combined matrix. Each figure carries
only its four size curves, p=0 to 0.5, and Wilson intervals; its BP
nonconvergence curve is a separate companion. Begin with honeycomb SU(3), the
artifact default. See the [A8 manifest](manifests/a8-artifact-full-record-ler-curves-2026-09-05.json).

**A8 scoring correction (2026-09-05):** the original A7/A8 contract
incorrectly counted a BP tolerance miss as a logical failure. This contradicted
the two-stage belief-matching semantics already implemented in Lab 002 and the
Lab 006 profiling scorer. All results produced under that rule are invalid for
LER inference and must be reacquired. The corrected score depends only on the
final PyMatching correction: detector syndrome must be cleared and
`logical_parity(error XOR correction)` must vanish. BP convergence remains a
companion diagnostic only.

**Operational handoff — fastest validated decoder (2026-09-05):** For all new
Lab 006 LER acquisition, use `run_a7_ler.py` (or A8's wrapper) with its default
optimized runner: pretabulated, Numba-generated fusion records; cached
topology/Numba sum-product BP; posterior-LLR PyMatching for the full-record
arm; and prebuilt fixed-weight `decode_batch` only for the no-herald control.
Do not restore the Python record-generation loop or per-shot fixed-weight
no-herald decode. The candidate is accepted because fixed-seed records,
corrections, and complete LER rows matched the legacy runner exactly while
end-to-end cells improved by 1.23--7.41x; see
`results/a7-runner-optimization-ab.json`. Full-record posterior weights remain
shot-specific, so its weighted PyMatching construction/decode must remain
per-shot unless a replacement supplies a new exact A/B proof; PyMatching's
current public API has no supported bulk in-place weight update.

**Authorized resumption (2026-09-07):** Acquire U(1), SU(2), SU(3) on both lattices concurrently; None deferred. Rough-boundary m and R remain unmeasured. Whole-cell process scheduling preserves the registered seed and 256-shot batch stream. Retain the 40 inherited final-correction-v2 cells with original backups and record their missing historical source hashes; checkpoint each new completed cell atomically. Publish explicitly partial figures during acquisition, then verify all 600 cells, six LER panels with Wilson 95% intervals, six convergence companions, report integration, registry, and rendered dashboard before completion.

**Completed delivery (2026-09-07):** All six panels have 100 sampled cells each: 12,000,000 shots in total, including 800,000 inherited corrected shots and 11,200,000 newly acquired shots. Count, interval, seed, inherited-count preservation, and new-source stability audits passed. Six final LER panels, six companion diagnostics, report embeds, active registry entries, and all rendered result pages passed delivery verification. See `results/a8-completion-audit-2026-09-07.json`, `results/a8-delivery-audit-2026-09-07.json`, and `wiki/ler-curves.md`. This completes the authorized curve delivery; None remains deferred and no threshold estimate is promoted.

**Presentation revision (2026-09-07):** Replace the six standalone LER images with one 3×2 figure: Square left, Honeycomb right; U1/SU2/SU3 top to bottom. Share x, retain independent y scales, and place one size legend below all panels. Use the unchanged audited counts. Replace report and registry entries, remove the six old PNGs, and verify the exact rendered surface.

## Phase A9 — Hidden pair orientation as a controlled mechanism test

The researcher hypothesizes that fixed fundamental/antifundamental ordering explains the contrast between SU2 and U1/SU3. The directed curves show finite-size behavior, not a proof of threshold absence. The new intervention randomizes each active pair direction with probability 1/2, hidden from inference, while keeping activity noise, geometry, full interior observation, rough-boundary marginalization, and final correction score fixed. The existing Wiki ternary channel supplies the model. Competing explanations are useful fixed-orientation information, weak/no orientation effect, and numerical/algorithmic degradation in loopy ternary BP.

The [A9 contract](manifests/a9-hidden-orientation-ler-2026-09-07.json) freezes six 20,000-shot, L=5,7,9,11, p=0.02..0.50 paired scans. A separate orientation RNG preserves the A8 activity/fusion stream; baseline replays must match A8 counts. Store paired joint failures and convergence diagnostics. SU2 uses its exact orientation quotient so an irrelevant duplicate state cannot alter the damped BP schedule; validate its local-channel invariance and shotwise identity. U1/SU3 use a verified ternary batch path, because the existing undirected class inherits a binary-only batch method that is unsuitable for production. Scalar/batch, tree enumeration, boundary, charge conservation, directed replay, and resource pilot gates precede production.

Analysis uses Wilson intervals, paired discordance confidence bounds, exact McNemar tests with Holm correction, and explicitly descriptive finite-size ordering. The experiment can identify orientation effects for this decoder but cannot separate all BP approximation effects from intrinsic recoverability or establish a thermodynamic threshold. Deliver the requested red six-panel undirected figure, retain the directed comparison, add effect/convergence diagnostics, and verify data → figure → report → registry → rendered page. None remains deferred.
