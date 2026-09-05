# Lab 005 — Spacetime just-in-time fault-tolerant anyonic decoding

## Central question

How should an anyonic decoder schedule measurements and corrections when both the topological syndrome and fusion/herald readout are noisy, so that it corrects quickly enough to prevent error anyons from hiding information but waits long enough to avoid committing on false measurements?

## Relation to the decoder Labs

- Lab 002 develops scalable belief matching for a spatial observation.
- Lab 004 reproduces and benchmarks spatial D4 intrinsic-heralded decoders under ideal measurement.
- Lab 005 treats decoding as a causal spacetime process and decides when a spatial decoder may act.

The interface is deliberate: a **schedule** groups spacetime detector events and issues a commit/defer decision; an **inner spatial decoder** chooses a correction after commitment. A better spatial decoder does not by itself provide fault tolerance, and a good schedule does not make an inaccurate inner decoder optimal.

## Source-method boundary

Lyons and Brown construct a just-in-time scheme for universal anyonic computation in the D(S3) phase. Repeated stabilizer measurements define detectors `D_i(t)` from changes between adjacent rounds. Local physical faults form spatial strings in a 2+1-dimensional record, while measurement faults form time-directed strings. The schedule maintains the causal detector history, defers young/insufficiently isolated clusters, and commits sufficiently old clusters to ungauging, neutrality testing, correction, and re-gauging.

The paper proves a threshold/exponential-suppression statement under sufficiently weak local circuit noise using a chunk-decomposition argument. It does not supply a ready-made numerical threshold benchmark or a complete implementation for the project's D4 herald variable. No such numerical result may be attributed to the source.

## Hypotheses and alternatives

### H1 — Scheduling is independently necessary

Under measurement noise, immediate per-round spatial decoding causes false commits or lets erroneous anyons hide later syndrome information. A causal defer/commit schedule reduces logical failure at bounded latency.

Alternative: for the tested model, a simpler repeated-measurement batch decoder performs equally well; JIT adds complexity without benefit.

### H2 — The paper's age/geometry rule is reproducible

On isolated spacetime clusters, the paper's JIT predicates commit within a bounded spacetime neighborhood while avoiding premature merger of independent clusters.

Alternative: ambiguity in absorber, age, boundary, or cluster-linking conventions prevents an implementation-level reproduction and must be localized.

### H3 — Noisy heralds require a joint schedule

Treating herald/fusion observations as perfect after correcting only syndrome measurement noise is not fault tolerant. Joint temporal inference over syndrome and herald records improves calibration and reduces false commitments.

Alternative: repeated herald measurements carry too little independent information or too much correlated noise to justify their scheduling overhead.

## Registered work packages

### J0 — Source and algorithm audit

Status: complete. Separate the paper's theorem, causal schedule, D(S3) gauging/ungauging operations, and project-specific noisy-herald extension.

Deliverable: `results/lyons2026-jit-method-audit.md`.

### J1 — Versioned spacetime observation schema

Status: binary causal-schema preflight and observation-only D4 spatial-policy adapter implemented and verified; physical D(S3) and noisy D4 measurement adapters remain pending.

Implement a minimal periodic spacetime record with:

- spatial data faults and time-directed measurement faults;
- repeated syndrome readings and detector differences between rounds;
- locations/trajectories of computational anyons, so known motion is removed from detector values;
- repeated herald/fusion observations with explicit false-positive, false-negative, and label-confusion channels;
- ground-truth fault support, detector events, and logical history for testing only.

Verification uses exhaustive tiny volumes to check detector endpoints, causal availability, normalization, and the separation of data versus measurement strings.

The D4 consumer boundary is frozen and implemented in
[`manifests/j1-d4-spatial-policy-interface-manifest-2026-08-29.json`](manifests/j1-d4-spatial-policy-interface-manifest-2026-08-29.json).
It is a two-call observation-only interface: a committed causal prefix produces
the first flux action, and a later physical post-action measurement record may
produce the blue/green charge actions. The schedule owns timing, the physical
adapter owns measurement generation, and simulation truth remains in an
inaccessible scoring sidecar. Eight focused adapter tests pass. The current Lab 004 truth-audited pipeline must
not be called directly because it accepts the hidden physical chain to score
and simulate the post-flux record.

### J2 — Offline and naive scheduling baselines

Build three references on the same record:

1. immediate per-round correction;
2. fixed-delay/windowed decoding;
3. full-history offline inference on tiny spacetime volumes.

The full-history method is a noncausal oracle and must not be presented as an online decoder.

### J3 — Reproduce the JIT commit/defer state machine

Status: Jing Algorithm-1 bounding-cube age predicate, abstract split-branch
state transitions, explicit absorber geometry, linked-forest restrictions,
and measured-neutrality interface verified; microscopic ungauging remains
pending.

Implement detector-cluster tracking with explicit age, diameter/separation, absorber, and boundary state. At each time step:

1. form/update causally visible clusters;
2. classify clusters as defer or attempt-to-correct using the paper's age/geometry rule;
3. propagate a deferred event forward by reversing/updating the latest measurement record;
4. for attempted clusters, branch on whether they lie in the gauged phase, ungauged region, or a boundary;
5. commit only a neutral cluster; otherwise defer and permit later linking.

Every state transition must have a deterministic event log and an invariant test. The abstract schedule is implemented before microscopic D(S3) circuit operations.

The source-boundary audit is
[`results/jit-ilp-source-boundary-audit-2026-08-29.md`](results/jit-ilp-source-boundary-audit-2026-08-29.md).
It verifies the bounded Jing Eq. (18)–(21) compiler and Algorithm-1 age gate,
while explicitly rejecting the stronger description “Lyons–Brown
reproduction.” The latter still requires absorber distance, measurement-record
reversal, D(S3)/D(Z3)/boundary state, ungauging, neutrality, re-gauging, and
linked-cluster behavior.

The next J3 preflight now passes under the registered contract
[`manifests/j3-explicit-schedule-state-manifest-2026-08-29.json`](manifests/j3-explicit-schedule-state-manifest-2026-08-29.json).
The Jing branch retains unresolved defects without record mutation. The
Lyons–Brown branch reverses only the latest detector-bearing readout to move a
deferred event forward, tracks D(S3), boundary, and ungauged D(Z3) states, and
distinguishes neutral correction/re-gauging from non-neutral deferral. Six
focused fixtures passed at that gate.

The next J3 gate is now implemented under
[`manifests/j3-absorber-neutrality-manifest-2026-08-29.json`](manifests/j3-absorber-neutrality-manifest-2026-08-29.json).
Nearest-absorber distance comes from causal inclusive spacetime boxes under
the \(L_\infty\) metric; opening and termination are explicit; all three
Theorem-4 direct-link restrictions are enforced; and current-round e/m parity
records update neutrality only for an active, owned D(Z3) region. Seven focused
fixtures and all 40 Lab tests pass. Cluster discovery, the microscopic
gauging/ungauging circuit, the \(Q\ge60\) proof, and noisy-channel performance
remain outside this preflight.

### J4 — Gauging/ungauging correction semantics

Implement the smallest model sufficient to test absorber creation, fusion-outcome preservation, neutrality revelation, re-gauging, and linked-cluster handling. Distinguish this physics layer from the generic cluster schedule so that alternate anyon models can later replace it.

The geometry, absorber lifecycle, linked-forest admissibility, and
measurement handoff are now explicit. The next J4 gate is the deterministic
phase-transition adapter that opens the D(Z3) region on ungauging, preserves a
supplied fusion outcome through the transition, and terminates the region on
re-gauging. It must not be described as a microscopic circuit reproduction.

That deterministic gate now passes under
[`manifests/j4-phase-transition-adapter-manifest-2026-08-29.json`](manifests/j4-phase-transition-adapter-manifest-2026-08-29.json).
Six focused fixtures and all 46 Lab tests verify one owned region per cluster,
exact preservation of the supplied fixture outcome, record binding, neutral
termination, non-neutral persistence, and invalid-order rejection. The
adapter remains phase-labelled bookkeeping, not a gauging circuit.

The earliest missing causal dependency is back in J3 step 1: detector clusters
are still hand assembled. The next gate must construct them from causal
observation records with explicit age, extent, separation, and candidate
absorber links before any noisy-measurement comparison is registered.

That snapshot-construction gate now passes under
[`manifests/j3-causal-detector-cluster-manifest-2026-08-29.json`](manifests/j3-causal-detector-cluster-manifest-2026-08-29.json).
The registered radius-one spacetime \(L_\infty\) components report age, extent,
separation, nearest active absorber, and geometric link candidates. Only a
cluster touching the current detector frontier can enter the schedule. Seven
focused fixtures and all 53 Lab tests pass, including the public defer/record-
reversal path.

This is still a snapshot. Before noisy measurements, a persistent tracker must
verify stable identifiers, append-only event ownership, deterministic merges,
and absorber-link updates across successive causal prefixes.

That persistent-state gate now passes under
[`manifests/j3-persistent-cluster-tracker-manifest-2026-08-29.json`](manifests/j3-persistent-cluster-tracker-manifest-2026-08-29.json).
Stable identifiers survive extension, bridge events merge into a canonical
earliest ID with durable aliases, immutable event origins remain distinct from
current ownership, and absorber candidates refresh using persistent-owner
self-exclusion. Seven focused fixtures and all 60 Lab tests pass.

The next transition returns to the registered dependency order: audit J1/J2
and freeze the smallest shared-fault-history contract under which immediate,
fixed-delay, JIT, and offline baselines can be compared. No noisy pilot may run
before all four paths consume the same record and inner-decoder semantics.

That audit is complete and the deterministic harness is registered in
[`manifests/j2-shared-history-baseline-manifest-2026-08-29.json`](manifests/j2-shared-history-baseline-manifest-2026-08-29.json).
J1 is sufficient for supplied deterministic histories but has no registered
stochastic noise generator. Immediate, fixed-delay, and offline runners are
absent; J3 can supply only the abstract JIT timing branch; and the Lab 004 D4
adapter cannot silently serve as a source-neutral D(S3) inner decoder.

The smallest matrix therefore includes all four branches on identical tiny
histories with one truth-free, versioned deterministic callback. It tests
history identity, causal truncation, explicit offline access, invocation time,
and replay—not logical performance. This is a prerequisite implementation
gate, not pilot compute.

That deterministic gate now passes under the same contract. Immediate,
fixed-delay-1, abstract JIT, and offline execute through one public runner with
one visible-history digest and one callback implementation digest. Seven
focused fixtures and all 67 Lab tests verify branch timing, causal truncation,
explicit offline access, truth-field exclusion, private truth/fault
decomposition invariance, and bit-identical replay.

The next gate is not a performance run. J1 must first register and verify the
smallest repeated-measurement history generator with separate data,
syndrome-readout, and herald false-positive/false-negative/label-confusion
channels. Only then may bounded shared-history pilot data be registered.

The source audit corrects the wording of that gate. There is no single
“source-matched” generator covering both Lyons–Brown D(S3) circuit noise and
noisy D4 intrinsic-herald labels. The durable layered contract is
[`manifests/j1-layered-repeated-measurement-generator-manifest-2026-08-29.json`](manifests/j1-layered-repeated-measurement-generator-manifest-2026-08-29.json):

- R is the still-unimplemented D(S3) local-circuit source reproduction;
- G is a generic binary-data/binary-syndrome plus categorical-herald schema
  preflight, registered next;
- E is the future noisy D4 project extension, blocked on G and a derived D4
  spacetime channel.

G must pass exact matrix normalization, false-positive/false-negative/label-
confusion isolation, independent seeded streams, categorical preservation,
causal-prefix, and matched-history tests. It cannot be reported as R or E.

That G gate now passes. `scripts/generic_history.py` uses three deterministic
substreams derived from one master seed, keeps `none`/`blue`/`green` labels
categorical, exposes only causal readout prefixes, and binds one generated
visible-history digest to all four scheduling branches. Eight focused fixtures
and all 75 Lab tests pass. No pilot or logical-performance data were generated.

The next transition must use the registered research workflow to scope the
smallest prerequisite matrix for the still-distinct R and E branches. A
performance pilot remains blocked until a branch supplies physical correction
and logical-scoring semantics; the generic G layer alone cannot support a
fault-tolerance or threshold interpretation.

That workflow gate is now registered in
[`manifests/j1-r-e-prerequisite-matrix-manifest-2026-08-29.json`](manifests/j1-r-e-prerequisite-matrix-manifest-2026-08-29.json).
R0 audits whether the Lyons–Brown source supplies a complete local
single-fault-to-detector catalogue in bulk D(S3), at the gauging boundary, and
inside D(Z3). E0 tests whether the verified perfect-measurement D4 two-call
spatial interface can be composed into a causal maximum-three-round state
transition without truth leakage. These are independent, bounded diagnostics,
so both run; neither requires a human ranking.

The noisy D4 instrument E1 is dependent on E0 and an explicit measurement
state-update basis. It is not part of the initial matrix. No performance pilot
may begin until one physical branch also supplies correction and private
logical-scoring semantics.

The registered matrix has now executed. R0 preserves exact stabilizer-level
relations for a false bulk readout and the boundary detectors in Eqs. (34) and
(35), plus the source's 1-neighborhood locality bound. It also localizes three
missing numerical-reproduction maps: gate-level D(S3) extraction faults,
primitive faults through ungauging/waiting/re-gauging, and index-level known-
motion adjustment. R therefore remains blocked only at exact microscopic
source reproduction; no map was guessed.

E0 passes in both public modes. A deterministic maximum-three-round state now
orders no-action carry-forward, causal flux commitment, physically supplied
post-action observation, charge action, and next-round advance. Direct spatial
and temporally composed actions agree, all public states are digest-bound and
truth-free, and private scoring is unavailable until completion. Eleven matrix
fixtures and all 86 Lab tests pass.

Before any human escalation, the next transition is a bounded primary-source
gap search for the missing D(S3) circuits and an operational repeated D4
measurement instrument. The two searches remain independent; an unresolved
result pauses only its branch.

That search is complete. The R citation chain reaches an exact preparation and
gauging construction for D(S3), but still contains no ancilla-resolved repeated
syndrome-extraction circuit or primitive-fault event table. R therefore pauses
at a circuit-model/external-source choice without blocking D4-first work.

The E citation chain contains a usable, narrower object: Jing *et al.*'s
Supplemental Appendix D gives time-ordered repeated commuting-projector state
updates and an explicit false-negative non-Abelian-flux example, while their
ILP paper supplies complete D(G) anyon projectors and spacetime readout-error
variables. The next transition must invoke the research workflow to register a
source-bounded E1 projector-instrument matrix. It must keep the commuting-
projector reporting channel separate from the quasi-stabilizer time-like-
herald example and must not call either an ancilla circuit or circuit-level
fault tolerance.

That research-workflow registration is now frozen in
[`manifests/j1-e1-projector-instrument-matrix-manifest-2026-08-29.json`](manifests/j1-e1-projector-instrument-matrix-manifest-2026-08-29.json).
E1A checks the hidden projector update and perfect E0 limit; E1B checks
classical false-negative/false-positive reporting after that update; E1C
reproduces the source's five-star quasi-stabilizer false-negative trajectory.
All three run because they test distinct semantics at negligible combined cost.

The implementation is limited to existing paper-L=2 fixtures, at most five
rounds, deterministic cases, five CPU minutes, and 1 GiB. A noisy report that
does not fit the current binary spatial-policy input must remain a typed pre-
translation record or be rejected. It cannot be silently coerced. Performance
sampling remains downstream of matrix verification and a separate translation
gate.

The matrix has now executed. E1A passes the hidden projector-update, physical-
event, action-binding, perfect-E0, and truth-exclusion fixtures. E1B passes as
a normalized typed report channel whose readout-only faults leave hidden state
unchanged. E1C reproduces the source five-star table and its \(q_m\),
\(p_m^3\), and \(p_m^2p_e\) explanations while remaining explicitly localized.
Fourteen focused fixtures and all 100 Lab 005 tests pass.

Execution also localizes the next dependent gate: a simultaneous multi-label
report cannot enter the current binary D4 policy request. The restricted
adapter rejects it instead of coercing it. The next experiment must therefore
register and test a typed E1-to-policy translation for both public modes;
performance sampling remains blocked.

That dependent experiment is now registered in
[`manifests/j1-e1-typed-policy-translation-manifest-2026-08-29.json`](manifests/j1-e1-typed-policy-translation-manifest-2026-08-29.json).
It tests every cheap branch rather than asking which mode to prioritize. T1A
preserves flux membership while intentionally withholding charge information
from `syndrome_only`. T1B factorizes both observed membership bits into the
existing heralded request, including a site carrying both reports. T1C checks
combined scheduler/report provenance, replay, truth exclusion, and the old
rejecting adapter as a negative control. A new schema is allowed only if a
concrete registered record cannot pass these invariants.

The translation matrix has now executed. T1A preserves flux membership and
withholds charge fields in `syndrome_only`; charge-only report changes still
alter provenance but not the mode-visible fields or action. T1B represents a
multi-label site in both existing heralded fields and agrees exactly with a
manual public request and action. T1C verifies replay, independent scheduler/
report digest binding, truth exclusion, and the old rejection as a negative
control. Six translation cases, 20 focused E1 tests, and all 106 Lab tests pass.

No schema extension is required: the gap was the old restricted adapter. The
next prerequisite is deterministic causal-trace integration with the existing
matched-history schedule harness, not a stochastic performance pilot.

Registration of that integration exposed an upstream defect in the existing
J2 callback. `InnerDecoderRequest` carries the digest of the complete visible
history, so a causal request and its response digest change when only future
rows change. A minimal counterfactual has identical immediate prefix digests
but different immediate request digests. The prior causal callback-isolation
claim is therefore invalidated; branch timing, outer shared-history identity,
explicit offline noncausality, and truth-field exclusion remain usable.

The remediation and integration matrix is registered in
[`manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json`](manifests/j2-e1-causal-integration-remediation-manifest-2026-08-29.json).
R1 removes full-history identity from causal callbacks and proves future-only
counterfactual invariance for immediate, fixed-delay, and JIT before any
dependent work. I1 then derives each round-local E1 record from the same public
syndrome/herald prefix; I2 covers both modes across all four schedules; I3
checks future, truth, odd-parity, multi-label, and offline boundaries. No
stochastic or post-action study may start until R1-I3 pass.

R1 is now verified. The callback request and digest no longer contain the
complete visible-history digest; that identity remains only in enclosing
event, branch, and run provenance. A last-round herald counterfactual leaves
the immediate, fixed-delay, and bounded JIT request/response digests unchanged
after their respective invocation horizons, while the explicitly noncausal
offline result changes. Eight focused tests and all 107 Lab tests pass. I1
round-local E1 derivation is the next dependency; I2/I3 and sampling remain
blocked. Evidence:
[`results/j2-r1-causal-callback-remediation-2026-08-29.md`](results/j2-r1-causal-callback-remediation-2026-08-29.md).

I1 is now verified at paper \(L=2\). The adapter accepts the schedule's bound
`InnerDecoderRequest`, reads only the final row of its causal prefix, and maps
syndrome/herald membership independently to `m_flux`/`e_charge` at all 24 D4
vertices. Trial and round identity come directly from the invocation. Private-
truth and future-only counterfactuals leave the public record invariant; bad
prefix binding, wrong width, and unverified sizes fail closed. Six focused
tests and all 113 Lab tests pass. The next transition is the complete cheap
I2/I3 matrix—both public modes across all four schedules plus the registered
boundary controls—with no sampling. Evidence:
[`results/j2-i1-round-local-e1-adapter-2026-08-29.md`](results/j2-i1-round-local-e1-adapter-2026-08-29.md).

I2/I3 are now verified on one immutable four-row paper-\(L=2\) trace. All eight
cells—two public modes by immediate, fixed-delay, JIT, and offline—invoke the
actual stage-1 D4 policy and return syndrome-faithful flux corrections. The
modes share history, timing, scheduler request, and implementation; only the
declared charge-information budget differs. Multi-label input is preserved,
future-only changes leave causal cells fixed while changing offline, private-
truth changes leave all cells fixed, odd parity fails closed, and replay is
bit identical. Fourteen focused tests and all 121 Lab tests pass. The next gate
is final R1/I1/I2/I3 synthesis and downstream release audit, not sampling.
Evidence:
[`results/j2-i2-i3-policy-matrix-2026-08-29.md`](results/j2-i2-i3-policy-matrix-2026-08-29.md).

The corrected R1/I1/I2/I3 evidence is now consolidated into the registered
machine-readable analysis and narrative report. The report keeps the original
future-sensitive J2 callback claim explicitly invalid, separates unaffected
historical evidence from replacement evidence, and limits the positive result
to deterministic causal information flow plus stage-1 syndrome fidelity. The
next and final contract gate is a downstream consumer audit; only corrected
artifacts may be released, and performance sampling remains blocked. Evidence:
[`results/j2-e1-causal-integration-remediation-2026-08-29.md`](results/j2-e1-causal-integration-remediation-2026-08-29.md).

The downstream audit is complete. No executable consumer outside Lab 005 used
the affected callback. Four stale machine-readable E1 `next_gate` pointers
were redirected to the corrected final evidence; historical invalid artifacts
remain labeled and unpromoted. The corrected deterministic stage-1 interface
is released for downstream paper-\(L=2\) work, and this remediation contract is
complete. Any next experiment must restart the research workflow at the
earliest unsupported post-stage-1 dependency; performance sampling remains
blocked. Evidence:
[`results/j2-downstream-causal-release-audit-2026-08-29.md`](results/j2-downstream-causal-release-audit-2026-08-29.md).

The research workflow now identifies and registers the earliest unsupported
post-stage-1 dependency: E2 causal post-flux completion. The dependency order
is strict. E2A must first translate an action-bound typed charge/vacuum report
and supplied physical measurement layout into the existing post-flux public
observation. Only then may E2B/E2C exercise both public modes across immediate,
fixed-delay, JIT, and explicitly noncausal offline branches, including
next-round ordering and negative controls. Stochastic histories, private
logical scoring, schedule comparison, and all performance sampling remain
blocked. Contract: manifests/j2-e2-post-flux-causal-completion-manifest-2026-08-29.json.

E2A now passes. The public adapter accepts only an action-bound charge/vacuum
report, combines it with an explicitly supplied physical layout, and produces
the existing digest-bound post-flux observation without hidden-state access.
It is identical to the manual E0 observation on the perfect fixture. Wrong
action binding, post-action flux/multi-label records, layout mismatch, and
predating reports fail closed. Four new E2A tests, all 24 projector-instrument
tests, and all 125 Lab tests pass. E2B/E2C is now the next contract item; no
sampling follows from E2A. Evidence:
[E2A post-flux adapter result](results/j2-e2a-post-flux-adapter-2026-08-29.md).

Before E2B execution, the registered fixture falsified one wording-level
invariant: syndrome-only and heralded choose different flux actions in all four
branches, so a single action-independent post-action record would violate
causal intervention semantics. The matrix therefore keeps the same pre-action
history, measurement layout, and report rule across modes, while binding each
post-action record to its own physical action. This is a scope-preserving
registration correction, not a new model or a favorable post-data selection.

E2B/E2C now pass on the complete deterministic paper-\(L=2\) matrix. All eight
cells—two public modes by four schedules—preserve the shared pre-action history,
layout, and report rule, bind the post-action report to the cell's actual flux
action, and return a nonempty blue charge correction. Causal branches advance
only after charge completion; the offline branch remains explicitly noncausal.
Future-only changes preserve causal cells while changing offline, private truth
changes no public cell, replay is bit identical, and parity-inconsistent support
fails closed. Six new matrix tests, all 20 focused integration tests, and all 131
Lab tests pass. No stochastic or performance sample was taken. The next gate is
the registered final machine-readable analysis and bounded report. Evidence:
[E2B/E2C completion matrix](results/j2-e2b-e2c-completion-matrix-2026-08-29.md).

The E2A-E2C evidence is now consolidated into the registered machine-readable
analysis and bounded narrative report. The synthesis preserves the necessary
action-conditioned matched-design correction, reports all eight cells and
negative controls, and explicitly prohibits performance, threshold, hardware,
and fault-tolerance inference. The final contract gate is a downstream consumer
and release audit; sampling remains blocked. Evidence:
[E2 causal post-flux completion](results/j2-e2-post-flux-causal-completion-2026-08-29.md).

The downstream audit passes and closes the E2 contract. No executable consumer
outside Lab 005 imports the E2 adapter or completion runner, and no artifact
uses E2 as performance evidence. Two stale stage-level `next_gate` pointers
were redirected to the final synthesis and audit. Corrected deterministic E2
composition is released for downstream interface work only; every stochastic,
logical-scoring, schedule-comparison, threshold, and fault-tolerance claim
remains blocked pending a fresh research-workflow registration at the earliest
unsupported dependency. Evidence:
[E2 downstream release audit](results/j2-e2-downstream-release-audit-2026-08-29.md).

The research workflow locates the next unsupported dependency before J6 at the
physical transition-kernel level. Existing evidence does not yet prove a joint
normalized law \(P(X_{t+1},O_{t+1}\mid X_t,F_t,A_t)\): Lab 004 supplies a
static spatial sampler and scorer, E1 supplies local projector/report semantics,
and E2 consumes an externally supplied post-action record. The registered E3
K1-K4 audit therefore checks physical-state evolution, public measurement,
action-conditioned post-flux generation, and private logical scoring
separately. This is one cheap completeness matrix, not a human-ranking fork.
No stochastic generator or schedule-performance sample is authorized.
Contract: `manifests/j1-e3-d4-transition-kernel-completeness-manifest-2026-08-29.json`.
Registration note:
[E3 transition-kernel audit registration](results/j1-e3-d4-transition-kernel-registration-2026-08-29.md).

The K1-K4 matrix is now verified and returns a localized negative. K2 has exact
normalized classical report kernels only after truth is supplied, and K4 can
score one completed spatial cycle privately. K1 lacks a normalized cross-round
hidden D4 state law, while K3 still requires an external physical post-flux
provider. Consequently, independent per-round fusion resampling and a noisy
schedule pilot remain invalid. Six focused tests and all 137 Lab tests pass;
no sample was taken. The next contract item is the bounded completeness
analysis/report and physical-model gate decision. Matrix:
`manifests/j1-e3-d4-transition-kernel-matrix-2026-08-29.json`.

The registered completeness analysis now formalizes that negative result. K1
is the earliest missing dependency and K3 depends on it; neither normalized K2
report noise nor the partial K4 scorer can close the physical transition. A
phenomenological Markov model, a stateful projector/density model, and a
circuit-derived channel can all satisfy the present exact checks, but they
change physical interpretation, dependencies, and compute budget. The checks
therefore cannot choose among them. The next contract item is an evidence-backed
researcher consultation; stochastic generation and sampling remain blocked.
Analysis: [E3 completeness report](results/j1-e3-d4-transition-kernel-completeness-2026-08-29.md).

The consequential model gate is now open as Discussion thread-009. It presents
the finite-state phenomenological Markov, stateful projector/density, and
ancilla/circuit-derived options with their interpretation, dependency, compute,
and reversibility consequences. The suggested path is the explicit finite-state
Markov kernel under a phenomenological-only claim boundary, retaining the
transition interface for later circuit-derived replacement. No model has been
selected on the researcher's behalf. The dependent stochastic D4 generator and
schedule sampling remain blocked while the thread awaits a reply.

### J5 — Connect an inner spatial decoder

At commit, call a declared inner decoder:

- source-matched D(S3) correction rule for reproduction tests;
- Lab 004 D4 heralded MWPM or exact oracle only in an explicitly translated D4 spacetime model;
- Lab 002 belief matching only after the same observation interface is established.

Cross-model reuse without a derived translation is prohibited.

For the D4 branch, the registered J1 interface gates now pass: forbidden-field
rejection, causal-prefix truncation, correction-syndrome fidelity,
action/observation digest binding, post-action support, deterministic replay,
and truth-sidecar separation. This establishes only a spatial interface under
ideal supplied observations; it does not establish a noisy D4 model or fault
tolerance.

### J6 — Bounded noisy-measurement pilot

On small spacetime volumes, compare immediate, fixed-delay, JIT, and offline schedules across a bounded matrix of data-fault, syndrome-readout, and herald-readout rates. Use matched fault histories.

Primary observables:

- logical failure probability and interval;
- false-commit and missed/late-commit rates;
- probability that an erroneous anyon survives long enough to hide syndrome information;
- commit latency and tail latency;
- active spacetime volume, number of repeated measurements, and classical work;
- calibration of the inner decoder at commit time.

### J7 — Schedule optimization, only after reproduction

Only after J3–J6 pass may the project compare adaptive Bayesian commit policies, learned schedules, or hardware-latency-aware policies. These are extensions, not substitutes for reproducing the causal baseline.

## Stop conditions

### Researcher model decision — D4 translation of Lyons–Brown

**Decision applied 2026-08-29.** The repeated-measurement and JIT structure
from Lyons–Brown is adopted as the Lab 005 schedule model, while D(S3)-specific
states are replaced by the audited D4 projector/fusion interface. The mapping
uses `vacuum/m_flux/e_charge`, categorical `none/blue/green` herald reports,
the action-bound E2 post-flux transition, and ground-state-relative
nontrivial-winding logical scoring. This is a phenomenological/projector-level
D4 translation, not an exact D(S3) circuit reproduction. Contract:
[`manifests/j1-e4-d4-lyons-brown-translation-manifest-2026-08-29.json`](manifests/j1-e4-d4-lyons-brown-translation-manifest-2026-08-29.json).

The next bounded gate is the translation-interface matrix. It must pass
normalization, perfect/zero-noise limits, action binding, causal-prefix
separation, identical histories across the four schedule branches, and the
ground-state-relative logical criterion before any stochastic pilot.

- Do not model measurement noise as independent flips on a single static snapshot.
- Do not let an online decoder access future detector events or ground truth.
- Do not treat syndrome-readout correction as sufficient while herald readout remains perfect by assumption.
- Do not claim the Lyons–Brown threshold numerically; the source establishes existence under weak local circuit noise.
- Stop if immediate, fixed-delay, JIT, and offline paths do not share identical fault histories and inner-decoder semantics.
- Do not launch a large spacetime threshold surface before tiny-volume enumeration and a bounded runtime pilot pass.

## Completion criteria

The Lab requires separately accepted source reproduction, causal-state implementation, invariant verification, bounded data, schedule comparison, resource analysis, report, and visual spacetime traces. A useful negative result localizes whether failure belongs to the observation model, schedule, inner decoder, or gauging/ungauging layer.
