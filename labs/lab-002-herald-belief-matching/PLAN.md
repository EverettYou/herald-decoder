# Plan — Herald-aware belief matching

## Motivation and scope

Lab 001 establishes the square/honeycomb observation model and makes individual configurations visually inspectable. This Lab asks the next, separate research question: can the current fusion-remnant herald field improve a scalable decoder when it is retained as probabilistic vertex information rather than consumed by local hard rules?

The herald in this Lab is not an erasure or loss flag. It is a vertex witness left by local syndrome/anyon fusion or cancellation and is correlated with the joint incident error pattern. No herald observation identifies a particular erased or erroneous edge.

## Research question

On identical error samples and with the same observed syndrome, how far is herald-aware BP followed by PyMatching from:

1. a mature syndrome-only PyMatching MWPM baseline; and
2. the exact posterior logical-class decision on graphs small enough to enumerate?

## Generative model

For every retained data edge $e$, sample

\[
x_e\sim\operatorname{Bernoulli}(p),\qquad 0<p<\tfrac12.
\]

At detector vertex $v$, let $d_v=\sum_{e\ni v}x_e$. The measured syndrome and observed herald follow

\[
\tilde s_v=(d_v\bmod2)\oplus m_v,
\qquad m_v\sim\operatorname{Bernoulli}(p_m),
\]

and

\[
P(h_v=1\mid d_v)=
\begin{cases}
q(1-p_h),&d_v\ge2,\\
0,&d_v<2.
\end{cases}
\]

The initial benchmark fixes $p_m=p_h=0$ so it measures the value of the current herald signal before adding extraction noise. Square and honeycomb graphs use the same open-rough/smooth-boundary convention already made explicit in Lab 001.

## Decoder candidates

### Division of labor: soft inference and hard correction

BP is a soft decoder front end. It maps the observation to edge marginals,

\[
(\tilde S,H)\longmapsto \{r_e\},\qquad
r_e\approx P(x_e=1\mid\tilde S,H),
\]

but it does not apply a correction and therefore cannot change the syndrome density. PyMatching is the hard constrained back end: after the marginals are projected to edge weights, it chooses a correction chain whose boundary is the supplied syndrome. Claims that "BP removes errors" must refer either to improved posterior quality or to an explicitly separate hard-decision predecoder, never to soft inference alone.

### A. Syndrome-only PyMatching

Construct the detector-by-edge check matrix and pass it to the maintained `pymatching` package with the static independent-edge weight

\[
w_e=\log\frac{1-p}{p}.
\]

This is the primary baseline. This Lab does not implement Blossom or another MWPM algorithm.

### B. Syndrome-BP plus PyMatching ablation

Run sum-product BP using the parity factors but disable the herald likelihood. The registered default uses probability-space damping. The experimental `recurrence_mode="memory"` ablation instead uses the edge-wise relay search and candidate scorer described below. Convert the BP edge marginals to matching weights and call the same PyMatching back end. This separates any gain caused by the BP front end itself from gain caused by herald information.

### C. Herald-aware BP plus PyMatching

Use the local factor

\[
\psi_v(\{x_e:e\ni v\})
=P(\tilde s_v,h_v\mid\{x_e:e\ni v\})
\]

in sum-product BP. The registered `recurrence_mode="damping"` path mixes each new factor-to-variable message with its previous value using damping coefficient $\lambda$. The opt-in `recurrence_mode="memory"` path begins with a uniform memory coefficient $\gamma_0$; subsequent relay legs preserve the prior leg's edge beliefs while drawing disordered per-edge memory coefficients $\gamma_e$, including a benchmarked negative range. Memory candidates are ranked by an observation-only Bethe-style score with a local pseudomarginal-consistency penalty. Let $r_e$ be the resulting soft edge belief. The corrected weighting rule uses

\[
w_e=\log\frac{1-r_e}{r_e}.
\]

This is the independent-edge MAP objective up to a correction-independent
constant: it includes the likelihood of selected and unselected edges. The
previous $-\log r_e$ projection was removed from executable paths on
2026-08-26. It is documented here only as a corrected historical error: it
omits the $-\log(1-r_e)$ term and therefore does not pin $r_e\to1$ edges.

## LLR remediation rerun

All Lab 002 logical-performance experiments that passed negative-log edge
weights to PyMatching are excluded from inference. The Lab is reopened only
to regenerate those affected comparisons with the corrected posterior LLR,
matched observations, separately reported BP convergence, and an explicitly
bounded shot budget. Existing BP-only convergence, calibration, and runtime
diagnostics may guide the design but cannot be used as corrected-decoder LER
evidence. No rerun begins until its cell grid, seeds, shots, and promotion
criteria are durably registered.

### D. Exact small-graph oracle

Enumerate every edge configuration only when the graph has at most 22 edges. Sum the exact posterior by logical class and choose the more probable class. This is an accuracy oracle, not a proposed scalable decoder.

### E. Hard marginal-MAP diagnostic

For mechanism testing only, threshold the herald-aware BP marginals at $r_e>\tau$, apply those selected edges as a preliminary correction, discard the herald field, and pass the resulting residual syndrome to static syndrome-only PyMatching. This diagnostic asks whether a hard use of the same posterior reduces syndrome density. It is not a hidden stage of candidate C and must not be used to describe how belief matching works.

## BP convergence remediation

The researcher reopened Lab 002 to explain why the herald-aware damping
recurrence can remain unconverged after 80 iterations and to improve its
convergence rate. This is distinct from the corrected LLR interface: matching
weights are downstream of BP and cannot repair a non-fixed-point message
trajectory.

### Phase C0 — measurement-only bottleneck trace

First reproduce the deterministic square-lattice sample
$L=9, p=0.20, q=1, p_m=p_h=0, \mathrm{seed}=12$ with the frozen
probability-damped recurrence and corrected LLR backend. Record at every
iteration:

1. global maximum factor-to-edge and edge-to-factor message change;
2. the residual attributed to every factor vertex and edge;
3. edge-belief drift and the largest factor-variable marginal disagreement;
4. period-2 oscillation amplitude, separated from monotone residual decay;
5. the vertices, edges, syndrome bits, and herald observations attached to
   the largest late-iteration residuals.

Expose the global trajectories and the spatial bottleneck ranking in a
diagnostic artifact. This phase must not alter initialization, damping,
schedule, clipping, tolerance, or maximum iterations, and it makes no
logical-error-rate claim. Merely raising the iteration cap is not evidence of
improved convergence.

**Execution status (2026-08-27): complete.** The independent trace reproduced
the production Python recurrence's iteration-80 edge marginals bit for bit.
The maximum message residual was $1.32\times10^{-2}$ at iteration 20,
$4.69\times10^{-3}$ at 40, and $2.16\times10^{-3}$ at 80, compared with
the $10^{-8}$ tolerance. The iteration-80 two-step residual was
$4.35\times10^{-3}$, about twice the one-step residual, so it does not show
a period-2 orbit. The measured failure mode is continued slow drift. Durable
evidence:
[`results/convergence-trace-seed12.json`](results/convergence-trace-seed12.json)
and
[`figures/convergence-trace-seed12.png`](figures/convergence-trace-seed12.png).

### Phase C1 — complete matched convergence ablation

The researcher directed the project to test all three C0-motivated
intervention directions rather than selecting one family. Phase C1 therefore
uses 64 fixed, matched square $L=9$, $p=0.20$, $q=1$ observations, including
the registered seed-12 bottleneck sample. Every condition uses $p_m=p_h=0$,
the same $10^{-8}$ fixed-point tolerance, and an 80-iteration cap. It reports
per-observation convergence, iterations, final message residual, posterior
log loss, Brier score, and deterministic Python runtime. It does **not** make
a logical-error-rate or decoder-promotion claim: the purpose is to identify a
safe recurrence hypothesis for a later registered end-to-end comparison.

The frozen synchronous, prior-initialized damping-$0.25$ recurrence is the
matched reference. The complete ablation matrix is:

1. **Damping strength:** old-factor-message weights $0$, $0.10$, $0.25$, and
   $0.50$, with the synchronous schedule and prior initialization unchanged.
2. **Residual-priority schedule:** frozen damping $0.25$ and prior
   initialization, compared between the synchronous sweep and a deterministic
   Gauss-Seidel factor sweep ordered by the preceding iteration's maximum
   incident-message residual (ties by factor row). The first sweep uses row
   order because no preceding residual exists.
3. **Initialization:** frozen damping $0.25$ and synchronous schedule,
   compared between independent-prior initialization and one deterministic
   local-observation bootstrap: factor-to-variable messages are computed once
   from the observed local factor with all other incident messages at the
   independent prior, then variable-to-factor messages are recomputed from
   those factor messages before iteration one.

All non-reference conditions are compared per matched observation to the
frozen reference. A condition is only a candidate for a later end-to-end
decoder test if it increases fixed-point convergence without worsening mean
posterior log loss or Brier score by more than the corresponding paired
uncertainty interval. No condition is silently adopted as the Lab default.

**Execution status (2026-08-27): complete.** The 64-observation matrix finds
that residual-priority Gauss--Seidel scheduling is the only tested direction
with a clear convergence increase: 22/64 (34.4%) fixed points versus 12/64
(18.8%) for the frozen synchronous recurrence, a matched increase of 15.6
percentage points (bootstrap 95% interval [7.8, 25.0] points). Its mean
posterior log-loss difference is -0.000303 (95% interval
[-0.000652, -0.000029]), so the observed acceleration is not accompanied by
a calibration regression in this diagnostic. Damping 0.10 improves log loss
slightly but not convergence; damping 0.50 significantly lowers convergence;
the local-observation bootstrap leaves convergence unchanged and is slower.
The residual-priority implementation is a candidate for a separately
registered corrected-LLR end-to-end decoder test, not the new default.
Durable evidence: [`results/convergence-ablations-c1.json`](results/convergence-ablations-c1.json)
and [`figures/convergence-ablations-c1.png`](figures/convergence-ablations-c1.png).

### Phase C2 — end-to-end residual-priority validation

Phase C2 validates the only C1 candidate through the actual posterior-LLR
matching interface. It compares frozen synchronous damping with explicit
residual-priority Gauss--Seidel damping on the same 64 C1 observations:
square $L=9$, $p=0.20$, $q=1$, $p_m=p_h=0$, seed 12 plus the fixed C1 seed
stream, 80 iterations, and tolerance $10^{-8}$. Both arms must emit clipped
posterior LLR weights, reproduce the observed syndrome after PyMatching, and
record convergence, soft scores, logical failure, paired rescues/harms, and
wall-clock time. Runtime samples are collected after two warm-up decodes per
arm and with arm order alternating for every matched observation, so decoder
construction or thermal drift cannot be mistaken for a scheduling advantage.
It is a correction-interface and mechanism validation, not
a powered logical-error study: its logical counts are descriptive only.

The residual-priority arm remains an experimental opt-in schedule and runs in
the Python recurrence until a separately validated accelerated implementation
exists. Promote it only if every correction is syndrome faithful, its
convergence gain remains present, no proper-score regression is detected, and
the endpoint does not introduce a clear logical regression. The frozen
synchronous default must remain unchanged throughout C2.

**Execution status (2026-08-27): complete.** Both arms passed correction
syndrome-faithfulness on all 64 observations and emitted posterior-LLR weights.
Residual priority retained the C1 gain (22/64 versus 12/64 converged, paired
95% interval +[7.8, 25.0] points), reduced mean iterations by 6.09 (interval
[-8.91, -3.61]), and improved mean log loss by 0.000303 (interval
[-0.000663, -0.000028]). The two arms made identical logical decisions
(12/64 failures each; zero paired rescues and harms); those counts are
descriptive rather than powered LER evidence. With a warmed, alternating-arm
timing protocol, the Python residual-priority endpoint costs 243.6 ms more per
observation (95% interval [183.7, 309.2]), so it cannot be promoted as a
wall-clock acceleration. The next bounded transition is a compiled
residual-priority implementation followed by Python/Numba equivalence and
matched timing validation. Evidence: [`results/residual-priority-c2.json`](results/residual-priority-c2.json)
and [`figures/residual-priority-c2.png`](figures/residual-priority-c2.png).

### Phase C3 — compiled residual-priority implementation

Implement the exact C2 factor order and immediate edge-to-other-factor
propagation in the Lab 002 compatible Numba runtime, retaining the frozen
synchronous Numba kernel and all default settings unchanged. Verify Python
and Numba residual-priority marginals, iteration count, convergence flag,
maximum residual, posterior-LLR weights, and correction bit-for-bit on fixed
square and honeycomb observations. Then time the two compiled endpoints with
alternating order and warm-up. C3 makes no logical-benefit claim and does not
promote the schedule until its end-to-end invariants pass.

**Execution status (2026-08-27): complete.** On the full 64-observation C1
square stream, compiled residual priority is bit-identical to the Python
schedule in edge marginals, posterior-LLR weights, correction, convergence
flag, iteration count, and maximum residual. It retains 22/64 convergence and
70.30 mean iterations. The frozen synchronous Numba arm takes 9.43 ms per
observation and compiled residual priority 12.28 ms; their paired difference
is +2.84 ms with bootstrap 95% interval [-1.34, 6.77], so this sample does
not resolve a wall-clock penalty or benefit. A separate eight-seed honeycomb
$L=5$, $p=0.20$, $q=1$ validation also has bit-identical Python/Numba
posterior-LLR corrections and 8/8 syndrome-faithful outputs. The schedule
remains opt-in because its convergence gain has not yet been tested on an
independent multi-geometry sample. Evidence:
[`results/residual-priority-c3.json`](results/residual-priority-c3.json),
[`results/residual-priority-c3-honeycomb.json`](results/residual-priority-c3-honeycomb.json),
and [`figures/residual-priority-c3.png`](figures/residual-priority-c3.png).

### Phase C4 — independent multi-geometry convergence replication

Use fresh, deterministic seed streams to compare synchronous and compiled
residual-priority damping on square $L=9$ and honeycomb $L=5$ at $p=0.20$,
$q=1$, with 64 matched observations per geometry. Record convergence,
iterations, posterior scores, syndrome faithfulness, and alternating-order
compiled timing separately by geometry. This replication tests whether the
C1 convergence mechanism generalizes; it does not pool lattice LERs or change
the default recurrence without a registered result.

**Execution status (2026-08-27): complete.** C4 uses fresh seed streams and
reproduces the square convergence mechanism: residual priority converges on
15/64 (23.4%) versus 5/64 (7.8%) for synchronous updates, a paired +15.6
point increase (95% interval [7.8, 25.0]) while reducing mean iterations by
2.83. At honeycomb $L=5$, both arms converge on 61/64 (95.3%), leaving no
headroom for a convergence-rate gain, but residual priority reduces mean
iterations by 2.72. Every correction is syndrome faithful; posterior scores
show no regression. The compiled residual-priority scheduler costs +2.08 ms
per square observation (95% interval [1.65, 2.49]) and honeycomb timing is
unresolved. It therefore remains opt-in. The next action is to profile and
reduce the scheduler's repeated factor-priority selection overhead, rather
than to alter the posterior model. Evidence:
[`results/residual-priority-c4.json`](results/residual-priority-c4.json) and
[`figures/residual-priority-c4.png`](figures/residual-priority-c4.png).

### Phase C5 — compiled scheduler-overhead profile

Profile the compiled residual-priority recurrence against synchronous Numba
on the C4 square condition, separating factor-message evaluation from the
per-iteration factor ordering. Test only equivalent ordering implementations:
the current deterministic repeated maximum scan and a stable single-sort of
the preceding residual vector. Verify that any optimized ordering is
bit-identical to the validated C3 recurrence before timing it. This phase
does not alter BP factors, damping, or matching weights.

**Execution status (2026-08-27): complete.** The stable bottom-up merge sort
keeps residuals in descending order and retains the reference scan's
factor-index-ascending tie rule. Across all 64 fresh C4 square observations
it is bit-identical to repeated scanning in BP marginals, LLR weights,
corrections, convergence metadata, and syndrome faithfulness. Its paired
median timing is 2.01 ms lower per observation, with a 95% bootstrap interval
[-4.27, -0.29] ms. Mean compiled inference time falls from 9.62 ms to 7.61 ms
(relative runtime 0.791). This resolves factor-priority selection as a real
overhead in the scan implementation, but C5 did not time the stable-sort path
against synchronous Numba under one common protocol. The stable-sort path is
therefore retained as an opt-in, unpromoted equivalent implementation.
Evidence:
[`results/residual-priority-c5.json`](results/residual-priority-c5.json) and
[`figures/residual-priority-c5.png`](figures/residual-priority-c5.png).

### Phase C6 — fresh end-to-end optimized timing confirmation

Before changing message arithmetic or buffer handling, compare frozen
synchronous Numba with stable-sort residual priority under one common,
alternating-order end-to-end timing protocol. Use fresh deterministic streams
of 64 square $L=9$ observations (seeds 11601--11664) and 64 honeycomb $L=5$
observations (seeds 11701--11764) at $p=0.20$, $q=1$, $p_m=p_h=0$. Record
convergence, iterations, posterior scores, syndrome faithfulness, correction
agreement, and decode time separately by geometry after three warm-ups per
arm. This bounded prerequisite determines whether any further allocation or
cached-product optimization is needed; it does not change the default or make
a powered LER claim.

**Execution status (2026-08-27): complete.** On the fresh square stream,
stable-sort residual priority converges on 21/64 observations versus 11/64
for synchronous Numba, a paired +15.6 point increase (95% interval
[7.8, 25.0]) while reducing mean iterations by 6.58 and mean log loss by
0.000172. It remains 1.63 ms slower per end-to-end decode (95% interval
[1.35, 1.90]). On honeycomb, convergence is 60/64 versus 59/64 and mean
iterations fall by 3.38, but decoding remains 0.29 ms slower (95% interval
[0.23, 0.36]). Every correction is syndrome faithful. Corrections differ on
13 square and three honeycomb observations, but neither geometry has a paired
logical rescue or harm; these logical counts are descriptive only. The
synchronous implementation remains the default. Evidence:
[`results/residual-priority-c6.json`](results/residual-priority-c6.json) and
[`figures/residual-priority-c6.png`](figures/residual-priority-c6.png).

### Phase C7 — allocation-only exact-equivalence optimization

The common-protocol C6 timing confirms that stable factor ordering does not
remove the end-to-end residual-schedule penalty. Before changing multiplication
order or introducing cached products, test the smaller prerequisite: replace
per-iteration temporary array allocation/copying with preallocated alternating
buffers while preserving factor order and every arithmetic operation. Reject
the implementation immediately unless marginals, posterior LLRs, corrections,
convergence metadata, and syndrome fidelity are exactly identical to C6 on
both registered streams. Only after that gate should warmed alternating-order
timing be interpreted. This remains an implementation experiment, not a
decoder-model or default change.

**Execution status (2026-08-27): complete and rejected for performance.**
Across all 64 square and 64 honeycomb C6 observations, the preallocated-buffer
kernel is bit-identical to the validated stable-sort kernel in marginals,
posterior LLRs, corrections, convergence flags, iterations, maximum residual,
and syndrome fidelity. It is nevertheless slower: +0.85 ms per square decode
(95% interval [0.68, 1.02]) and +0.053 ms per honeycomb decode (95% interval
[0.046, 0.060]). Avoiding these small allocations does not remove the runtime
penalty, so buffer reuse remains experimental and disabled by default.
Evidence: [`results/residual-priority-c7.json`](results/residual-priority-c7.json)
and [`figures/residual-priority-c7.png`](figures/residual-priority-c7.png).

### Phase C8 — cached-product bounded numerical-equivalence test

The remaining evidence-backed overhead hypothesis is repeated recomputation of
variable-to-factor products after each Gauss--Seidel factor update. Implement
one opt-in cached-product kernel and compare it with the validated C6 stable
sort on both C6 streams. Because caching changes multiplication order, require
maximum marginal error at most $10^{-12}$, maximum posterior-LLR error at most
$10^{-10}$, identical convergence flags and iteration counts, identical
corrections, and syndrome fidelity before timing. Reject the candidate on any
gate failure. If it passes, use the same three-warm-up, five-repeat,
alternating-order end-to-end timing protocol separately by geometry. No
default promotion or logical-performance claim is authorized by C8.

**Execution status (2026-08-27): complete and rejected at the gate.** The
candidate passes syndrome fidelity and preserves convergence flags on all 128
C6 observations, but only 51/64 square and 49/64 honeycomb observations pass
every registered equivalence condition. Square maximum marginal error is
0.0120, maximum LLR error is 0.172, and one correction changes. Honeycomb
maximum marginal error is $2.71\times10^{-10}$, but near clipped posterior
extremes this becomes a maximum LLR error of 1.10; three iteration counts also
change. Timing was therefore skipped. Both bounded implementation hypotheses
have now failed promotion: buffer reuse is exact but slower, while cached
products are not numerically/correction equivalent. Synchronous Numba remains
the default and no further residual-priority optimization is registered.
Evidence: [`results/residual-priority-c8.json`](results/residual-priority-c8.json)
and [`figures/residual-priority-c8.png`](figures/residual-priority-c8.png).

## Hypothesis and alternatives

Primary hypothesis: candidate C lowers logical-error rate relative to candidate A at $q>0$, with a larger benefit on honeycomb because ideal parity plus herald eligibility identifies incident degree $0,1,2,3$ exactly.

Alternatives that must remain distinguishable:

1. C and B improve equally over A, meaning the observed gain comes from BP rather than herald information.
2. BP marginals improve locally but the independent-edge reweighting loses the multi-edge correlation, producing no logical gain.
3. Loopy BP fails to converge or becomes poorly calibrated near dense-error regimes.
4. The independent-edge LLR projection can still lose multi-edge posterior correlations, especially when BP has not converged.
5. Herald information helps finite sizes but does not move an asymptotic threshold.

## Observables

- logical-error rate with a Wilson 95% interval;
- logical prediction disagreement with syndrome-only MWPM;
- mean residual error density and correction weight;
- BP convergence rate and iteration count;
- decoding time per shot, reported separately because reweighted PyMatching currently rebuilds a graph per observation;
- on enumerated graphs, BP edge-marginal mean absolute error and excess logical-error rate above exact logical MAP.

## Attribution design

The contribution study has two levels.

At the soft-information level, score three probability fields against the simulator's latent edge sample: the independent prior, the syndrome-only BP posterior, and the herald-aware BP posterior. Report proper log loss and Brier score. The increments prior → syndrome BP and syndrome BP → herald BP quantify predictive information supplied by parity conditioning and by the herald field, respectively. These edge-level scores are simulation diagnostics and are not gauge-invariant logical observables.

At the logical level, use matched samples for the chain

\[
\text{static MWPM}\rightarrow\text{syndrome-BP+MWPM}
\rightarrow\text{herald-BP+MWPM}.
\]

For each adjacent ablation and for the total comparison, count paired rescued failures and introduced failures, report the net logical-error-rate change, and use the exact McNemar test on discordant shots. This is the primary contribution accounting because BP alone has no logical decision to score.

Define an operational effective physical error $p_{\mathrm{eff}}$ by inverting the finite-size syndrome-only MWPM curve:

\[
P_L^{\mathrm{MWPM}}(p_{\mathrm{eff}};L)
=P_L^{\mathrm{herald}}(p;L).
\]

Then $p-p_{\mathrm{eff}}$ expresses the decoder gain in physical-error units at fixed lattice and size. It is decoder- and finite-size-relative, must carry uncertainty from both curves, and is not the residual edge density of a chosen error representative.

## Interactive inference artifact

The Lab page must expose more than the final correction. Its workbench uses one deterministic sample and four linked views:

1. **Observation** shows the simulated ground-truth edge error for validation together with the syndrome and fusion-remnant herald record available to the decoder.
2. **BP posterior** maps $P(x_e=1\mid \tilde S,H)$ onto every retained edge.
3. **Herald effect** maps the difference between herald-aware and syndrome-only BP marginals, making visible where the herald factors raise or lower error belief.
4. **Decode vs truth** compares the single herald-aware belief-matching correction with the simulated edge truth: green marks decoder-selected true-error edges, purple marks decoder-only edges, and red marks true-error edges missed by the decoder.

This final view is an edge-level simulation diagnostic, not a comparison between decoders. The control panel reports the herald-aware decoder's logical outcome, proper soft scores, and a syndrome-density flow that explicitly shows the invariance under soft BP. The hard-BP density row is labeled as a separate diagnostic.

Clicking an edge reports its prior, both posterior marginals, herald-induced
change, matching weight, and correction/truth membership. The panel uses the
posterior LLR projection exclusively. It also selects the BP recurrence,
defaulting to damping, and reports the single trajectory or selected memory
candidate, the memory score when applicable, fixed-point state, decoding
runtime, and the herald-aware decoder's logical outcome. Square/honeycomb,
$L,p,q,p_m,p_h$, and the seed remain tunable.

## Matched comparison

**Historical invalidation:** the completed comparisons in this section passed
$-\log r_e$ weights to MWPM. Their logical-error, rescue/harm, McNemar, and
effective-error outputs are excluded from inference. The text below preserves
the preregistration and execution provenance only. Proper BP scores,
convergence, iterations, and runtime remain mechanism diagnostics.

For every Monte Carlo shot, all decoder candidates receive the same underlying $x$ and measured syndrome. Candidate C additionally receives the sampled $H$; candidates A and B do not. Candidate B is required so that the incremental effect of $H$ is not confused with the incremental effect of BP. Random seeds, package version, parameters, and shot counts are stored with every result.

### Registered pre-update versus memory-assisted BP A/B

Before using the updated BP front end in the broader herald-versus-MWPM
replication, freeze the immediately preceding probability-damped BP as an
ablation and compare it directly with the memory-assisted BP. This test
changes only the BP iteration/search mechanism. Both arms receive the same
simulated error, syndrome, herald field, lattice, and physical parameters;
both use the negative-log projection

\[
w_e=-\log r_e
\]

and the same PyMatching construction. The registered immediate cells are
square and honeycomb at $L=5$, $p=0.10$, $q=0.75$, and
$p_m=p_h=0$, using three fixed seeds and matched shots within every seed.
Report pooled and per-seed logical-error rates, paired rescues and harms,
exact McNemar tests, edge log loss and Brier score, convergence, iterations,
and wall-clock decoding time. The legacy arm is the frozen
`damping=0.25`, 40-iteration implementation; the updated arm uses the
current registered memory-search defaults. No truth-dependent candidate
selection is permitted.

This was the historical promotion rule. Because its matcher objective was
wrong, the run cannot establish a corrected-LLR implementation advantage or
regression.

**Execution status:** completed with three seeds and 100 shots per seed in
each cell, then invalidated for all logical interpretation after the LLR
correction. Its BP-only diagnostics did not pass the promotion gate; see
[`results/memory-vs-damping-ab.json`](results/memory-vs-damping-ab.json).

### Registered systematic follow-up to the negative A/B

The first A/B exposed three possible failure channels at once: the selected
memory candidate rarely reaches the fixed-point tolerance, its soft scores
are worse, and the honeycomb $p=0.10$ cell has too few logical failures to
resolve LER. The follow-up therefore profiles and optimizes the two frozen
arms before increasing sample size. Optimizations must preserve the decoder
outputs and remain entirely inside Lab 002. Validate the legacy arm against
the archived pre-update bytecode and the memory arm against a frozen
pre-optimization executable on representative square and honeycomb samples.
Record steady-state before/after timing. Prefer specialized NumPy operations,
precomputation, deterministic observation caching, and process-level
parallelism; add a new runtime only if profiling shows that the added
dependency is justified.

A legacy-only pilot chooses the physical-error grids without inspecting the
old-versus-new effect. Square candidates are $p=0.08,0.10,0.12,0.14$ and
honeycomb candidates are $p=0.12,0.14,0.16,0.18,0.20$. Retain three points
per lattice whose pilot legacy LERs best cover observable low, middle, and
high rates; square must include $p=0.10$. This selection rule prevents the
final grid from being chosen for a favorable A/B difference.

The final study uses five deterministic seeds and 200 matched observations
per seed, totaling 1000 observations in every selected lattice--$p$ cell.
Both arms receive identical errors, syndromes, and heralds and retain the
same negative-log projection and PyMatching settings. Report per-cell and
per-seed LER with Wilson intervals, paired rescues and harms with exact
McNemar tests, proper soft-score paired intervals, selected-candidate
convergence and distribution, iterations, cache behavior, worker count,
runtime, and optimization equivalence checks. This is systematic finite-size
evidence at $L=5$, not threshold estimation.

**Pilot grid decision:** the 100-shot legacy-only pilot observed square LERs
of 0.06, 0.11, 0.16, and 0.24 at $p=0.08,0.10,0.12,0.14$, respectively,
and honeycomb LERs of 0.02, 0.02, 0.03, 0.05, and 0.10 at
$p=0.12,0.14,0.16,0.18,0.20$. The final grids are square
$p=0.08,0.10,0.12$ and honeycomb $p=0.16,0.18,0.20$. This keeps the square
points local to the original cell and moves honeycomb into a regime with
observable failures. The selection used only the legacy arm.

**Systematic execution status:** completed with five seeds and 200 shots per
seed in all six selected cells. All logical comparisons are invalidated; the
retained BP-only result is worse soft calibration with no selected converged
memory candidate. See
[`results/systematic-memory-vs-damping-ab.json`](results/systematic-memory-vs-damping-ab.json).

### Post-A/B backend decision

The researcher selected the frozen probability-damped recurrence as the
registered Lab 002 backend. This is a durable backend direction, not a
corrected-LLR performance conclusion from the invalidated A/B. The unified
decoder and the interactive artifact therefore default to
`recurrence_mode="damping"`; `recurrence_mode="memory"` remains an explicit
experimental ablation. This decision does not promote the existing
finite-shot herald comparison to a threshold claim. The separately registered
finite-size threshold and $q$-scan work belongs to
[Lab 003](../lab-003-herald-threshold-phase-diagram/PLAN.md).

## Stop conditions

Stop and diagnose before scaling if any correction fails to reproduce the supplied syndrome when $p_m=0$, if the exact tree-graph marginal check fails, or if an observation has zero likelihood under the stated model. Do not reinterpret herald vertices as erased edges to work around a failure.

The first experiment stops after a reproducible finite-shot comparison at selected $L,p,q$ values plus exact small-graph checks. It does not claim a threshold or phase diagram.

## Completion criteria

1. All research code and dependencies are owned by this Lab.
2. Unit tests verify graph boundaries, syndrome faithfulness, the herald degree condition, and BP against exact marginals on a tree factor graph.
3. A deterministic command writes machine-readable benchmark data and a human-readable summary under `results/`.
4. The report distinguishes measured findings from hypotheses and records uncertainty, convergence, and runtime limitations.
5. Lab 001 remains independent of this posterior/BP pipeline.
6. The interactive result makes the posterior reweighting and correction-path change inspectable on the same sample.
