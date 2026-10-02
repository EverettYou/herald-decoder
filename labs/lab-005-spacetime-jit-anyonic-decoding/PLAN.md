# Lab 005 — Spacetime just-in-time fault-tolerant anyonic decoding

## Central question

How should an anyonic decoder schedule measurements and corrections when both the topological syndrome and fusion/herald readout are noisy, so that it corrects quickly enough to prevent error anyons from hiding information but waits long enough to avoid committing on false measurements?

### Current exact physical-law controls (2026-09-25)

The next bounded transition is preregistered in
[`manifests/j6s-repeat-transfer-four-site-2026-09-25.json`](manifests/j6s-repeat-transfer-four-site-2026-09-25.json).
It compares unchanged-observable repetition with genuinely new-site readout in
the J6R chain prefixes and completes only the previously censored matched-chain
branch at exactly four random second sites. The fixed ideal L=2 orbit, chain
edges `[0,4,3]`, causal projector order, full public arrays, exact-rational
normalization, source hashes, 60-CPU-second cap, and no stochastic/schedule
sampling are frozen before execution. An effect remains a finite ideal
operator-law statement, not a noisy JIT or general D4 physical-kernel result.

The [registered exact result](results/j6s-repeat-transfer-four-site-2026-09-25.json)
passes both controls. The one-edge first dependence is unchanged site-2
operator repetition; newly eligible site 0 is `1/2` under each first record.
The matched branch has four random second sites but only four positive
joint charge strings, each `1/4`, and its complete second law is identical
for all four first records. The old J6R censor remains on its own three-site
contract. 182 Lab tests pass; no stochastic histories or five-round caller
changes occurred. Next: preregister a separate minimal path/action witness
for *new-site* first-record dependence if one exists, before any noisy
physical integration or schedule-performance proposal.

The next exact diagnostic is registered in
[`manifests/j6t-alternate-action-new-site-law-2026-09-25.json`](manifests/j6t-alternate-action-new-site-law-2026-09-25.json).
It exhausts the four remaining nonempty, non-prefix correction subsets of
the *same* chain `[0,4,3]`, with no change to state, first record, public
second-record schema, or physical error. Before computing, it freezes exact
newly eligible versus changed versus repeated operator-site definitions,
joint conditional-law comparisons across all four positive first records,
four-random-site and 60-CPU-second caps, and zero stochastic schedule budget.
A null result is a bounded negative finding, not a theorem for other paths.

The [four-action exact result](results/j6t-alternate-action-new-site-law-2026-09-25.json)
passes every registered gate. Together with the three earlier nonempty
prefix actions, it covers all seven in-support corrections on this one ideal
chain. No newly eligible second-site joint law depends on the first public
record. The sole additional full-record dependence under action `[3]` is an
unchanged-site-1 repeat, while action `[4]` has no newly eligible site and
is vacuous for that projection. Changed-plus-new joint projections are also
first-independent. 187 Lab tests pass; no histories, schedule arms or
bootstrap replicates were generated, and the frozen caller is unchanged.
This finite negative control does not establish a general D4 transition.
The next scientific question is whether another topology or longer physical
path produces genuine new-site conditional information under the same
public-record boundary; this requires its own bounded registration.

The next discriminating exact matrix is now registered in
[`manifests/j6u-four-edge-path-branch-2026-09-25.json`](manifests/j6u-four-edge-path-branch-2026-09-25.json).
It compares the nonbranching four-edge extension `[0,4,3,7]` with the
four-edge branched tree `[0,4,3,5]` from the same three-edge core. Each
geometry uses the same four public-action types: edge 0, edge 3, both, and
matched correction. This is a two-topology by four-action exact projector
matrix, not a choice of which branch to try first. The fixed L=2 vacuum
orbit, full binary causal public records, private site partition, joint
new-only versus changed-plus-new analysis, support/CPU caps and zero
stochastic budget were frozen before calculation. A censored or null branch
will remain explicitly limited to this matrix.

The [exact two-topology result](results/j6u-four-edge-path-branch-2026-09-25.json)
closes all eight branches without censoring. The path has three random first
sites and eight equiprobable first records; the branched tree has one random
site and two equiprobable records. Three complete second public laws depend
on the first record, but only through unchanged repeated operators. Every
non-vacuous new-only and new-plus-changed joint law is first-independent.
The matched path's five random second sites support only eight correlated
strings per first record, each `1/8`, identically across first records.
The 193-test Lab suite and Wiki/report lints pass; no stochastic work or
five-round caller change occurred. This limits, rather than proves away,
first-record transfer on other topologies. The next bounded design audit
should compare a simple loop fixture with the missing genuinely stateful
multi-round action-feedback prerequisite, instead of extending tree length
without a new discriminating mechanism.

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

Deliverable: `wiki/records/lyons2026-jit-method-audit.md`.

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
[`wiki/records/jit-ilp-source-boundary-audit-2026-08-29.md`](wiki/records/jit-ilp-source-boundary-audit-2026-08-29.md).
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
[`wiki/records/j2-r1-causal-callback-remediation-2026-08-29.md`](wiki/records/j2-r1-causal-callback-remediation-2026-08-29.md).

I1 is now verified at paper \(L=2\). The adapter accepts the schedule's bound
`InnerDecoderRequest`, reads only the final row of its causal prefix, and maps
syndrome/herald membership independently to `m_flux`/`e_charge` at all 24 D4
vertices. Trial and round identity come directly from the invocation. Private-
truth and future-only counterfactuals leave the public record invariant; bad
prefix binding, wrong width, and unverified sizes fail closed. Six focused
tests and all 113 Lab tests pass. The next transition is the complete cheap
I2/I3 matrix—both public modes across all four schedules plus the registered
boundary controls—with no sampling. Evidence:
[`wiki/records/j2-i1-round-local-e1-adapter-2026-08-29.md`](wiki/records/j2-i1-round-local-e1-adapter-2026-08-29.md).

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
[`wiki/records/j2-i2-i3-policy-matrix-2026-08-29.md`](wiki/records/j2-i2-i3-policy-matrix-2026-08-29.md).

The corrected R1/I1/I2/I3 evidence is now consolidated into the registered
machine-readable analysis and narrative report. The report keeps the original
future-sensitive J2 callback claim explicitly invalid, separates unaffected
historical evidence from replacement evidence, and limits the positive result
to deterministic causal information flow plus stage-1 syndrome fidelity. The
next and final contract gate is a downstream consumer audit; only corrected
artifacts may be released, and performance sampling remains blocked. Evidence:
[`wiki/records/j2-e1-causal-integration-remediation-2026-08-29.md`](wiki/records/j2-e1-causal-integration-remediation-2026-08-29.md).

The downstream audit is complete. No executable consumer outside Lab 005 used
the affected callback. Four stale machine-readable E1 `next_gate` pointers
were redirected to the corrected final evidence; historical invalid artifacts
remain labeled and unpromoted. The corrected deterministic stage-1 interface
is released for downstream paper-\(L=2\) work, and this remediation contract is
complete. Any next experiment must restart the research workflow at the
earliest unsupported post-stage-1 dependency; performance sampling remains
blocked. Evidence:
[`wiki/records/j2-downstream-causal-release-audit-2026-08-29.md`](wiki/records/j2-downstream-causal-release-audit-2026-08-29.md).

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
[E2A post-flux adapter result](wiki/records/j2-e2a-post-flux-adapter-2026-08-29.md).

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
[E2B/E2C completion matrix](wiki/records/j2-e2b-e2c-completion-matrix-2026-08-29.md).

The E2A-E2C evidence is now consolidated into the registered machine-readable
analysis and bounded narrative report. The synthesis preserves the necessary
action-conditioned matched-design correction, reports all eight cells and
negative controls, and explicitly prohibits performance, threshold, hardware,
and fault-tolerance inference. The final contract gate is a downstream consumer
and release audit; sampling remains blocked. Evidence:
[E2 causal post-flux completion](wiki/records/j2-e2-post-flux-causal-completion-2026-08-29.md).

The downstream audit passes and closes the E2 contract. No executable consumer
outside Lab 005 imports the E2 adapter or completion runner, and no artifact
uses E2 as performance evidence. Two stale stage-level `next_gate` pointers
were redirected to the final synthesis and audit. Corrected deterministic E2
composition is released for downstream interface work only; every stochastic,
logical-scoring, schedule-comparison, threshold, and fault-tolerance claim
remains blocked pending a fresh research-workflow registration at the earliest
unsupported dependency. Evidence:
[E2 downstream release audit](wiki/records/j2-e2-downstream-release-audit-2026-08-29.md).

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
[E3 transition-kernel audit registration](wiki/records/j1-e3-d4-transition-kernel-registration-2026-08-29.md).

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
Analysis: [E3 completeness report](wiki/records/j1-e3-d4-transition-kernel-completeness-2026-08-29.md).

Discussion thread-009 is resolved. The researcher selected a bounded D4
phenomenological/projector-level translation of the Lyons--Brown repeated-
measurement/JIT structure, with the public D4 instrument and ground-state-
relative scorer replacing D(S3)-specific physical labels. The J1-E4B interface
matrix now passes; this permits a preregistered pilot but does not convert the
translation into a circuit-derived D4 noise model.

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

The [J6 pilot contract](manifests/j6-d4-matched-history-stochastic-pilot-2026-09-19.json)
now freezes the smallest matrix: paper (L=2), five readout rounds, immediate,
fixed-delay-1, JIT and explicitly noncausal offline schedules, both public
modes, and three cells totaling 272 independent matched histories and 2,176
arm evaluations. The primary loss is unconditional Boolean-union logical
failure with aborts and missing scores retained as failures. Pointwise Wilson
intervals and 2,000 whole-history paired bootstrap replicates are registered;
there is no simultaneous-coverage or superiority claim.

The arm-level remediation now passes. A zero-event arm emits a private terminal
score without fabricating a public decoder action. For one or more callbacks,
each public spatial action is frozen as an absolute cumulative Pauli-frame
estimate at its decision round: duplicate cluster callbacks at the same round
must have identical full-snapshot action content and collapse to one commit;
the latest later-round estimate supersedes the earlier frame. Physical,
Boolean-union and charge winding are accumulated over every canonical commit,
while terminal residual is evaluated from the final physical state and latest
cumulative frame. Distinct same-round actions fail closed.

The unchanged readiness matrix now emits exactly eight replayable
unconditional rows on zero-, single- and multi-cluster histories. The zero
fixture has eight successes and zero fabricated invocations; the two-edge
fixture collapses two identical immediate callbacks to one commit. Frozen
provenance, five component groups (22 selected fixtures) and all six
capability gates pass. The added noisy-syndrome fixture verifies that a valid
record rejected by the static periodic decoder is retained as eight
failed-closed unconditional rows instead of disappearing.

The frozen production run is now closed under its preregistered stop rule. All
272 histories and 2,176 unconditional arm rows were retained. Zero control
passed, and the joint-readout-noise cell cleared the event gate with nine
JIT-invoking histories per mode. In the clean-herald cell, immediate and
fixed-delay-1 each invoked on eight histories per mode but JIT invoked on only
seven, below the required eight. The pilot is therefore non-informative and
censored: zero bootstrap replicates are permitted, no paired direction is
interpreted, and rates or sample counts may not be adapted within J6.

The retained rows localize the prerequisite rather than support a performance
claim: 960/1,024 clean-herald rows and 944/1,024 joint-readout rows fail closed
because the static periodic inner decoder requires an even instantaneous flux
syndrome, whereas a valid measurement-noise record often has odd parity at one
round. A future Lab 005 transition must first preregister and test a causal
spacetime-to-spatial handoff for such odd snapshots; it must not repair J6
post hoc or treat the failed rows as a schedule comparison.

That transition is now registered as [J6A causal odd-syndrome/time-boundary
handoff](manifests/j6a-causal-odd-syndrome-time-boundary-handoff-2026-09-22.json).
J6A runs exactly eight deterministic fixtures: even identity, odd snapshot,
two-round reconciliation, unresolved persistence, future invariance,
truth-sidecar invariance, replay/equivariance, and malformed-token rejection.
It permits neither stochastic histories nor schedule comparisons. The spatial
decoder must receive each odd endpoint as an explicit causal temporal-boundary
handoff, not as a fabricated spatial endpoint or a hidden-truth completion.

The dependent [J6B replacement-pilot registration
job](manifests/j6b-replacement-pilot-registration-2026-09-22.json) is also
recorded but blocked. Only a complete J6A pass can release it to freeze a new
disjoint cohort, provenance, event gate, budget, and stop rule. J6 itself
remains closed censored in either outcome.

The J6A pre-execution source audit found that the registered allowed-file list
omitted the scheduler entry point that actually calls the even-only D4 request
validator. A one-vertex public odd request currently fails there with
`periodic D4 flux syndrome must have even cardinality`. The J6A contract now
includes `e1_schedule_integration.py` and its existing test file so the eight
unchanged fixtures can verify the real causal scheduler-to-spatial path,
not a detached handoff helper. This is a source-scope correction within the
same zero-history, zero-arm-evaluation and no-new-dependency budget; J6A has
not run, and J6B remains blocked.

The corrected public-path implementation and the unchanged eight-case J6A
matrix now pass; the machine-readable [J6A result](results/j6a-causal-odd-syndrome-time-boundary-handoff-2026-09-22.json)
pins source/runtime provenance and confirms unchanged J6 raw and analysis
hashes. The complete Lab 005 regression suite passes 154 tests. Odd snapshots
are not coerced into an even spatial syndrome: each visible endpoint is
paired with an explicit decision-time temporal-boundary ledger node, and the
action defers with no physical correction. Persistently odd records still
fail closed in the unconditional integrated caller. This structural pass
releases only the separate J6B *registration task*, not stochastic sampling,
bootstrap, risk comparison, or a performance claim. The next transition must
freeze a disjoint pilot cohort, abort semantics, event gates and budget before
any replacement history is generated.

Before the J6B pilot registration, a deterministic source-impact check found
that the integrated caller still failed an odd-at-round-1, even-at-round-2
history merely because the earlier defer appeared in its invocation list.
This contradicted the intended later-request ledger semantics even though
J6A's public-path tests passed. The bounded [J6B-R0 prerequisite](manifests/j6b-r0-temporal-ledger-reconciliation-2026-09-23.json)
now passes four fixed causal/denominator fixtures and all 158 Lab regressions;
its [machine-readable result](results/j6b-r0-temporal-ledger-reconciliation-2026-09-23.json)
pins source/runtime provenance and unchanged frozen J6 hashes. A defer
generates neither a physical correction nor a second public record. Only a
later even full-snapshot action can supersede it; a terminal unresolved or
conflicting handoff remains a failed-closed unconditional row. This fixes an
interface prerequisite, not the stochastic frequency of resolution or a
schedule-performance result. J6B must still be separately preregistered with
new disjoint seeds, paired semantics, event/resolution gates, budget and stop
rule before any replacement sampling.

The separate [J6B pilot contract](manifests/j6b-disjoint-temporal-handoff-pilot-2026-09-23.json)
is now preregistered, not executed. It freezes the corrected later-even-action
handoff ledger, source/runtime hashes, disjoint seed stream, newly fixed 0.06
stochastic rates, L=2 five-round geometry, both public modes, all four schedules,
272 complete histories/2,176 unconditional arm rows, whole-history uncertainty,
and event plus resolved-handoff gates. This is an independent exploratory
cohort: J6 rows, event counts, and risk cannot be pooled or reinterpreted.
Registration generated zero replacement histories, arm evaluations, or
bootstraps. The next transition is a *separate deterministic preflight* through
the integrated public path; until it passes, production remains unarmed. A
terminal defer still counts as failure, and even a passing pilot cannot by
itself establish a fault-tolerance threshold or universal schedule advantage.

The [separate J6B deterministic preflight](results/j6b-disjoint-temporal-handoff-preflight-2026-09-23.json)
has now passed: 26 selected public-interface/model assertions, three synthetic
histories and 48 direct arm evaluations, with zero stochastic histories, zero
production arms and zero bootstrap replicates. The runner and manifest hashes
are frozen in that result; all declared source/dependency and legacy-J6
quarantine hashes matched. An initial runner smoke attempt stopped before
fixtures because the pinned interpreter lacks `python -m pytest`; the runner
was corrected to use the already validated pytest executable and the same
test matrix passed. The active transition is the one-shot registered J6B
production cohort, whose event and resolved-handoff gates can still censor
any performance inference.

The J6B one-shot cohort has now run at its exact registered size: 272
independent histories and 2,176 unconditional arm rows. Source/runtime,
zero-control, row/key, event and odd-defer-to-later-even-action gates all pass;
each public mode has 158 resolved-handoff histories. The record retains 922
stochastic failed-closed rows from unresolved temporal handoffs. No bootstrap
or paired risk interpretation has been performed. The next bounded transition
is the registered pointwise Wilson and 2,000 fixed-seed whole-history paired
bootstrap analysis, without J6 pooling or adaptive cohort extension.

That fixed analysis is now complete on the frozen rows. All 14 registered
online contrasts used exactly 2,000 whole-history resamples, with pointwise
Wilson arm intervals. Four contrasts meet the exploratory proposal trigger,
but not in one favorable direction: clean-herald JIT has higher unconditional
failure than heralded fixed-delay; joint-noise syndrome-only JIT has higher
failure than immediate; heralded immediate improves on syndrome-only immediate
with clean heralds but worsens it with joint readout noise. Arm failure risks
range from 0.789 to 0.992. These are finite L=2, five-round, unadjusted
pointwise directions dominated by a near-ceiling failure regime, not evidence
of JIT superiority or a threshold. Do not expand the cohort under this
contract. The next program-level question is whether to register a separate
discriminating study that can separate true logical-risk effects from the
unresolved temporal-handoff ceiling, without changing the observation budget.

The post-hoc, read-only [J6B outcome-attribution contract](manifests/j6b-d0-frozen-outcome-attribution-2026-09-23.json)
and [machine result](results/j6b-d0-frozen-outcome-attribution-2026-09-23.json)
close on every frozen row: 16 stochastic arms, 14 original online paired
contrasts, 128 matched histories per stochastic cell, zero new histories,
arms or bootstrap replicates. The four proposal-triggered unconditional
failure-count differences split into failed-closed versus scored-failure
components of (+3,+7), (0,−8), (+1,+8) and (0,+9), respectively. Thus merely
reducing unresolved handoffs would not explain the observed mixed directions.
This is descriptive accounting after the original pilot, not a conditional
LER, causal attribution or additional test. The next bounded scientific gate
should inspect scored-path residual/charge/union composition and timing
semantics under the unchanged public interface before any larger sampling.

The separately registered [J6B-D1 scored-mask/timing audit](manifests/j6b-d1-scored-mask-timing-audit-2026-09-23.json)
passed on immutable J6B rows. All 16 arm tables and 14 matched contrast tables
reconcile against D0, without new histories, arm evaluations or bootstrap.
Terminal residual appears in 57/61, 57/60, 67/68 and 67/70 JIT scored
failures across the two cells and modes. This is descriptive, not causal.
The next candidate is a separately registered deterministic public-interface
trace of residual/frame accounting, not an adaptive sampling extension.

The [J6B-D2 deterministic trace](manifests/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json)
passed its five registered supplied histories, 40 unique public arm rows and
exact full replay. Independent final-chain XOR latest-frame residuals agree
with every scored row. A single late edge fault is corrected by JIT in this
fixture but not by fixed-delay-1; early-plus-late cancellation also exposes
a stale fixed-delay frame. Readout-only odd input is retained as failed-closed
under immediate and later resolved in the other branches. This does not
explain D1's stochastic JIT residual frequency or support a causal mechanism
claim. The next bounded candidate is selected frozen J6B history replay to
localize first public divergence and private residual accounting; no new
cohort, scorer change or schedule-risk inference is authorized by D2.

The [J6B-D3 selected frozen-history replay](manifests/j6b-d3-selected-frozen-history-replay-2026-09-23.json)
then matched all eight registered original seed/key/history digests and all
64 existing mode/schedule rows. Its first diagnostic attempt was censored by
a detector-row indexing error before case interpretation; the corrected
runner changed no selection, model, scorer or frozen input and retained the
failed-attempt record. Among the selected syndrome-only JIT rows, no-commit
cases leave an uncorrected final syndrome. Clean-herald one-/multi-commit
failures acquire later physical transitions after a residual-clearing last
commit, whereas joint-noise one-/multi-commit failures have final-round
readout/hidden-syndrome mismatch and residual already present at commit.
These are deliberately selected overlapping case flags, not mechanism
frequencies. The next bounded candidate is an all-256-stochastic-history
read-only accounting of the same flags, retaining unconditional arm/abort
counts and no new sample, bootstrap, risk comparison or causal attribution.

The [J6B-D4 full frozen-cohort overlap audit](manifests/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json)
is preregistered before replay. It fixes all 256 existing stochastic histories,
2,048 existing stochastic arm rows, the 512 JIT target rows, four overlapping
scored-row flags, the unconditional failed-closed denominator, exact D1/D3
reconciliation, unchanged action-bound public interface and independent
private residual oracle. It permits no new seed, production arm, bootstrap,
conditional risk estimate or causal mechanism label; hash, replay, mass-balance,
time and output gates censor the descriptive result on failure.

The [D4 machine audit](results/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json)
passed in 72.3 seconds: 256 existing histories, all 2,048 stochastic arm rows,
and 512 JIT rows exactly replayed; no new stochastic unit or bootstrap was
created. The two main scored-residual flags often coexist, and all four
cell/mode unconditional outcome counts reconcile with D1. This closes the
frozen-cohort diagnostic sequence without identifying a unique causal
failure mechanism. The next scientific transition is a broader design review
of the channel, outcome and schedule comparison before any separately
registered new sampling, not another J6B micro-audit.

The [action-feedback model-sufficiency review](manifests/j6-model-sufficiency-review-2026-09-24.json)
is registered as that prerequisite. It asks whether an earlier correction can
change later hidden anyon/projector state or first-observation law in the
implemented phenomenological kernel. The alternatives are an exogenous
physical/readout path with action-dependent same-round E2 and scoring versus
an action-to-future-state path able to represent interruption of hidden-charge
accumulation. It freezes source/result hashes, checks both pathways against
the accepted deterministic fixture, and creates no new stochastic data or risk
estimate. A missing action-feedback path would block a mechanism-bearing
JIT claim and redirect work to a tiny explicit model/fixture before any
new noise-rate sweep; it would not invalidate the registered finite
timing-pilot facts.

The [model-sufficiency result](results/j6-model-sufficiency-review-2026-09-24.json)
passed its pinned source and accepted-fixture checks without generating any
new arm. The implemented future hidden chain/projector labels and first record
are exogenous to prior actions; E2 action binding and terminal-frame scoring
do not close that feedback path. The current fixed-cohort schedule comparison
therefore remains a valid finite timing/readout comparison under its declared
toy model but cannot test whether timely active correction prevents later
hidden non-Abelian charge. Keep new rate/sampling work behind a deterministic
no-feedback-versus-feedback transition-model gate.

The [two-round action-feedback counterfactual](manifests/j6c-action-feedback-counterfactual-2026-09-24.json)
is now preregistered as that gate. It fixes one D4-labelled projector site,
three matched exogenous keys, a zero-fault/vacuum-outcome fixture, the exact
four-cell no-feedback/feedback by defer/commit matrix, causal full-binary
first and action-bound second records, private Boolean-union diagnostic,
normalization and replay checks, and a zero-sampling/10-CPU-second budget.
The feedback table is deliberately stipulated, not a derived D4 fusion or
hardware law. Passing it would establish interface capacity only; physical
transition probabilities and any performance interpretation remain open.

The [four-cell machine result](results/j6c-action-feedback-counterfactual-2026-09-24.json)
passes the registered deterministic checks with no stochastic history,
performance-arm evaluation or bootstrap. The null remains action-invariant;
only the deliberately stipulated feedback branch changes the next private
projector label and public first record after commit. This closes the
representability prerequisite but does **not** supply a source-derived D4
transition law or update the five-round integrated caller. Before any new
schedule-risk cohort, derive or otherwise justify the action-conditioned
D4 kernel and register a separate integration/limiting-case gate.

The [J6D state-sufficiency contract](manifests/j6d-projector-state-sufficiency-2026-09-24.json)
registered a zero-sampling, pinned-source exact audit. Its
[result](results/j6d-projector-state-sufficiency-2026-09-24.json) passes:
red-X chain parity has the correct no-fault and cancelling-action limits,
while a generic rank-two projector witness shows why coarse-projector
completeness alone cannot establish a Markov law. This is not a D4
counterexample. The cited D4 projector/density-channel ingredients and
local post-flux sampler do not yet determine a unique numeric
`vacuum/m_flux/e_charge` action-conditioned cross-round table. Next
preregister a geometry-matched two-round D4 projector/density-state
derivation and limiting-case fixture before integrating a kernel or sampling.

The [J6E source-bounded L=2 contract](manifests/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json)
and [exact result](results/j6e-two-round-stabilizer-sector-fixture-2026-09-24.json)
originally claimed to close the stabilizer-sector limiting slice: no-error control,
one- and two-edge red-X faults, defer versus prescribed matching red-X
intervention, post-flux even-parity support, and unchanged ideal-projector
repeatability. The matching intervention is oracle-matched for validation,
not a causal policy. No first-herald-to-postflux joint law, arbitrary-fault
hidden-state channel, or full density operator was inferred. Next register
the first-measurement/correction/postflux *conditional instrument* on the
same geometry, including a state update and a test of any proposed reduced
kernel, before changing the five-round caller or sampling performance.
The later J6G source-image disambiguation below confirms the narrow J6E
postflux support, while leaving the general instrument gate open.

The [J6F preregistration](manifests/j6f-first-herald-green-repeat-audit-2026-09-24.json)
and [four-case exact result](results/j6f-first-herald-green-repeat-audit-2026-09-24.json)
originally alleged a source-semantic contradiction. That claim is **withdrawn**:
it misidentified the `p2`-weighted *dressed* green stabilizer in A13 as the
bare star measured after correction. The [J6G registered source-image audit](manifests/j6g-source-stabilizer-disambiguation-2026-09-24.json)
and [exact four-case check](results/j6g-source-stabilizer-disambiguation-2026-09-24.json)
show that A13 also contains a separate bare green `+1` stabilizer. Blue
measurement replaces the dressed `p2` stabilizer; A14 retains bare green
`+1` and equal blue eigenvalues. J6E's blue `00`/`11`, green-vacuum support
is source-consistent for the fixed L=2 path. The J6F-only invalidation and
sampler freeze are retracted. No stochastic histories or schedule arms were
run. Next derive and validate the explicit first-measurement/correction/
postflux conditional stabilizer or density instrument; do not generalize
this local support to arbitrary geometry or five-round physical schedules.

The [J6H preregistered local conditional instrument](manifests/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json)
and [four-branch exact result](results/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json)
advance the illustrated short-path state update beyond parity support.
Under A6, first green `p2=±1` is equiprobable. Matching red-X correction
produces A13's blue-pair `+1`, bare green `+1`, and `p2`-weighted dressed
green generators. Blue measurement anti-commutes only with the dressed
generator, so its sign `p=±1` is equiprobable conditional on either `p2`;
it replaces that generator and yields A14's equal blue signs with bare green
vacuum. Four `(p2,p)` branches each have joint probability `1/4`, with
full-binary first and second public records and a separate private symbolic
stabilizer trace. Defer has no E2. This is a source-derived *local symbolic*
instrument, not a complete D4 density tableau or evidence about arbitrary
geometry, noisy measurement or five-round schedule risk. Next preregister a
generalization/adapter validation gate before modifying production histories.

The [J6I preregistered readiness matrix](manifests/j6i-general-instrument-readiness-2026-09-24.json)
and [zero-sampling result](results/j6i-general-instrument-readiness-2026-09-24.json)
separate two prerequisites that cannot be resolved by ranking which one to
try first: the paper's A2/A4 operators must be instantiated as an exact
lattice-wide action-conditioned state update, and the public E2 adapter must
accept the first observed record. J6H's four-row local normalization passes;
the existing sampler and its two callers have no first-record input. This is
an interface-readiness result, not a counterexample to independent parity
sampling. Next preregister a small exact operator fixture covering the known
matched path and one distinct correction/geometry, then validate the adapter
against its joint law before any five-round history or risk calculation.

The [J6J exact local representation contract](manifests/j6j-cz-star-factor-representation-2026-09-24.json)
and [eight-cell result](results/j6j-cz-star-factor-representation-2026-09-24.json)
test the first mathematical prerequisite for that operator fixture without
pretending to simulate a D4 ground state. One `X_b CZ_(g,r)` factor of A2
versus an `X_b` truncation is evaluated under a coherent product input and
a Z-fixed control, each at two label permutations. The coherent input has
source-factor `P(+)=3/4` but truncated `P(+)=1`; the control gives `1` for both.
Thus a plain Pauli-only representation is not automatically measurement-law
preserving. A CZ-aware full kagome A2/A4 operator mapping, not this isolated
factor, must next be derived and checked on the pinned L=2 matched path and
one distinct action/geometry before any adapter or five-round history change.

The [J6K full local star/action contract](manifests/j6k-full-local-star-action-algebra-2026-09-24.json)
and [4096-state exact result](results/j6k-full-local-star-action-algebra-2026-09-24.json)
advance from the J6J factor to a complete 12-qubit *single-star* A2/A4
operator. Pinned Jing A2/A4 and Iqbal Fig. 2 define a six-CZ inner ring,
six outer X factors and the two three-site color triangles. The exhaustive
operator checks pass, including an idempotent charge projector of rank 512.
Two red-error pair geometries and no/matched/partial red-X actions give six
exact branches: the uncorrected and partial cases carry the predicted
green-Z dressing, while matched actions restore the undressed local star.
The ring sites have not been mapped to the periodic `L=2` edge IDs and no
global state or public charge distribution was generated. The next gate is
therefore a complete multi-star embedding and physical initial-state/
measurement update on the pinned geometry, not a five-round rerun.

The [J6L periodic incidence contract](manifests/j6l-periodic-kagome-incidence-2026-09-24.json)
and [exact support map](results/j6l-periodic-kagome-incidence-2026-09-24.json)
complete the first, purely combinatorial part of that gate. The source's
nine-star/27-qubit unit-cell count, all 36 periodic star supports, every
red-edge identity and a representative two-edge path pass. This does not
verify the algebra between neighboring stars or the existence/preparation of
a common ground state. Next preregister the smallest operator-state fixture
on this fixed 108-qubit incidence map: check the source's neighboring-star
relations, construct or fail closed on a valid anyon-free state representation,
and only then derive sequential first-observation/action/second-observation
probabilities. The first-record-aware public adapter and five-round schedule
evaluation remain downstream and frozen.

The [J6M exact operator/state contract](manifests/j6m-periodic-operator-ground-orbit-2026-09-24.json)
and [symbolic result](results/j6m-periodic-operator-ground-orbit-2026-09-24.json)
now pass the periodic neighboring-star prerequisite. All adjacent commutators
equal their two local triangle factors and vanish in the triangle vacuum;
nonadjacent stars commute globally. A 33-generator compact orbit from
`|0^108>` has three positive dependent relations and gives one nonzero
common star/triangle `+1` state. The CZ-deleted null loses the nontrivial
fluxful commutators. The 22-fold ground-space degeneracy, absolute logical
sector and a state-preparation circuit were not derived. The next bounded
transition is a separately registered, small sequential projector fixture
using this *same* state and fixed red-edge path: compare no/matched/partial
action, condition the second public record on the actual first result,
verify normalization and source limiting cases, and leave private state and
truth inaccessible to the decoder. Do not generate five-round histories or
schedule-risk estimates until that instrument and its public adapter pass.

The [J6N local sequential-projector contract](manifests/j6n-sequential-local-projector-moments-2026-09-25.json)
is the next bounded physical gate. It fixes the *same* J6M compact vacuum
orbit and the L=2 red-edge error [0,4], measures the actual first green:1
projector, then compares defer, partial [0], and matched [0,4] red-X actions.
Only flux-free blue stars are eligible for local second measurements: none
for defer, blue:0 for partial, and blue:0/blue:2 for matched. Ordered Born
moments are reduced exactly using the orbit's star eigenvalues and diagonal-Z
characters; no 2^33 amplitude list is sampled. Acceptance requires first
green half/half, normalized nonnegative conditioned rows, and the matched
blue-pair parity and half/half source limit. This gate does **not** construct
the joint full 24-site binary E2 record or the first-record-aware public
adapter; those remain separately registered downstream work. Five-round
histories, schedule-arm risks, and bootstraps remain frozen.

The [J6O full-binary sequential-record contract](manifests/j6o-full-binary-sequential-public-record-2026-09-25.json)
is registered before exact execution as the next dependent gate. On the
unchanged J6M state/error path it measures every flux-free first-round
blue/green star, conditions on the actual first green:1 projector, and tests
defer, partial and matched correction before measuring every second-round
eligible star. All 24-site public flux/charge/vacuum arrays follow the
existing membership convention; the action is separate and physical error,
operator relations and state remain private. Exact site marginals are
insufficient by themselves to claim a joint record, so the contract requires
an exact joint table for every nontrivial site (at most two) and fails closed
if that sparsity or normalization gate fails. A pass would establish only this
fixed ideal geometry's full-record law; the first-record-aware production
adapter and five-round noisy schedule remain separate, frozen gates.

The [J6O exact result](results/j6o-full-binary-sequential-public-record-2026-09-25.json)
passes that fixed-geometry gate. All eligible first and second star sets
commute on their actual triangle sectors; only green:1 is random initially,
blue:0 after the partial action, and the correlated blue:0/blue:2 pair after
matched correction. Ten full-binary public-law rows cover the two first
outcomes and three actions, including E2-unavailable defer, with exact
normalization and no private support/relation in the public arrays. This
authorizes a *separate* first-record-aware adapter validation, not a general
physical transition kernel or five-round noisy schedule risk calculation.

The [J6P first-record-aware adapter contract](manifests/j6p-first-record-aware-e2-adapter-2026-09-25.json)
is now registered as the dependent interface gate. A fixed-path adapter must
accept only the complete first public record, its causal digest, a separately
bound red-edge action, and one independent binary second-outcome key. The
exact J6O public law supplies the two equal-weight outcomes for each actual
first record/action; the adapter must reject tampered or future/private
inputs, preserve action and prefix binding, produce only full-binary public
E2 or null defer, and replay. The 12-cell matrix covers both first outcomes,
all three actions and both second bits. This remains an *isolated fixed-path*
adapter: the existing general phenomenological five-round caller is pinned
byte-for-byte, not silently replaced or physically promoted. General D4
operator-state transitions beyond this path and noisy schedule evaluation
remain later gates.

The [J6P deterministic result](results/j6p-first-record-aware-e2-adapter-2026-09-25.json)
passes its 12 registered first-result/action/exogenous-bit cells and eight
negative controls; 170 Lab 005 tests pass. Public completions bind the first
record and correction action by digest and contain only the permitted
full-binary E2 arrays (or null on defer). The first result is required for
binding and law lookup, although the two first-result values happen to give
identical conditional second distributions in this particular geometry.
This isolated fixed-path adapter is not connected to the frozen five-round
caller. The next scientific gate is a separately registered extension of the
operator-derived transition law beyond the single path before any physical
schedule comparison.

The [J6Q alternate-path contract](manifests/j6q-alternate-path-operator-law-matrix-2026-09-25.json)
now freezes that next discrimination. On the same J6M state and L=2 lattice,
the two new private red-X pairs `[0,1]` (shared blue endpoint) and `[0,3]`
(disjoint endpoints) each cross defer, one-edge partial and matched actions.
The old `[0,4]` shared-green result is a pinned reference, not a repeated
sample. Exact eligible-star commutation and ordered first/action/second Born
laws must pass before publishing any complete 24-bit public record. If a
branch has more than three nondeterministic first or second sites, the branch
is censored, not approximated. This low-cost two-class matrix tests whether
the J6O law is a symmetry transfer, whether a distinct geometry changes
support, and whether first-outcome dependence appears; none of these is
assumed. No noisy history or schedule-risk calculation is authorized.

The [J6Q exact result](results/j6q-alternate-path-operator-law-matrix-2026-09-25.json)
passes all six registered geometry/action branches without support censoring.
The shared-blue pair has blue:0 as a half/half first charge and a correlated
green:1/green:17 half/half pair after matched correction; the disjoint pair
has deterministic charge vacuum under defer, partial and matched branches.
For each varying first outcome, the conditional second law is identical,
so this finite matrix does not demonstrate first-outcome dependence. It does
show that adjacency changes charge support, while the shared-endpoint color
pattern transfers to a second class. The 173-test Lab 005 suite passes and
the five-round caller is unchanged. A more complex path/branch class is the
next physical-law question, not a noisy schedule or threshold study.

The [J6R three-edge topology contract](manifests/j6r-three-edge-topology-causal-law-2026-09-25.json)
preregisters the smallest next matrix: a nonbranching connected chain
`[0,4,3]` and a three-arm star `[0,1,2]`, each with defer, one-edge prefix,
two-edge prefix, and matched correction. This tests whether a longer path
creates a multi-site first charge record and whether the complete second
public law responds to the actual first result, with the star as a distinct
topology control. Same L=2 state, exact projectors, full 24-bit public arrays,
three-random-site support cap, private physical support, and a 60-CPU-second
zero-sampling budget are frozen before calculation. A null result or censored
branch is still informative; neither licenses a general/noisy D4 channel.

The [J6R exact result](results/j6r-three-edge-topology-causal-law-2026-09-25.json)
closes seven of eight branches with normalized complete public laws. The
connected chain has two random first sites and four equiprobable first
records. With one-edge correction, the second site-2 charge repeats the
first site-2 bit while site 0 remains half/half, so the *complete* second
law depends on the actual first record. With two-edge correction the full
second law is identical across first records. The three-arm star has a
deterministic first record. The matched-chain branch requires four random
second sites and is censored at the preregistered cap; no partial full law
is published. This first dependence may be unchanged-observable repetition,
not hidden non-Abelian feedback. Next, separately register a structural
repeat-versus-transfer diagnostic and the four-site matched completion under
a new exact-compute cap. The frozen five-round caller and schedule sampling
remain untouched.

The [J6V two-branch prerequisite contract](manifests/j6v-loop-stateful-prerequisite-audit-2026-09-25.json)
tests the next independent in-scope forks together, without asking the researcher
to rank them: shortest simple loop geometry on frozen J6L incidence, and whether
the frozen exact/caller interfaces already carry an action-conditioned
postselected state into a third observation. Both are deterministic, zero-sampling
audits with five pinned inputs and a 60-CPU-second cap. The
[result](results/j6v-loop-stateful-prerequisite-audit-2026-09-25.json)
finds a shortest six-red-edge graph loop and an absent stateful multi-round
interface. It neither computes the loop charge law nor licenses a D4 feedback
kernel. Next, separately preregister capped exact loop and three-block
postselection fixtures; noisy five-round sampling stays frozen.

The [J6W local ideal projector contract](manifests/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25.json)
then freezes two independent exact branches at a common 60-CPU-second,
zero-sampling bound. On the J6V six-edge loop, only two selected first stars
and at most two selected second stars are measured per action; all other
eligible stars are *unmeasured*, not silently marginalized from a full
readout. A four-variable-site cap censors any full-public loop inference.
Separately, the fixed two-edge path propagates actual selected-projector
postselection across first, second, and third blocks under no second action
versus correction of the remaining edge. The
[result](results/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25.json)
passes exact rational normalization. The loop has six variable first sites,
so its full record is censored; the selected local loop pair is independent
across the tested first/second sites after one-edge correction. The three-block
third result is an unchanged-site repeat or an equal-bit pair after completing
correction. Neither supplies a general D4 feedback kernel. Next, preregister
an explicit full-record dephasing/computation treatment and a changed/new-site
three-block discriminator before any noisy five-round sampling.

The [J6X full-first/new-third contract](manifests/j6x-full-first-dephasing-new-third-2026-09-25.json)
fixes a two-branch follow-up under one 60-CPU-second zero-sampling cap.
The loop branch measures all six variable first stars and only one selected
second star after edge-0 correction, contrasting the coarse result with J6W's
two-site first instrument. The independent three-edge path branch preregisters
two conditional third-action alternatives but requires exactly two second sites
with nonzero *unconditional* variance before evaluating either. The
[result](results/j6x-full-first-dephasing-new-third-2026-09-25.json)
gives 16 positive full-first loop records. Its second site 17 repeats the
unchanged first operator, so full-first conditioning is deterministic yet the
coarse two-site result remains `1/2`, identical to J6W; no new-site/dephasing
effect is identified by that contrast. The path has only one qualifying
unconditional second site and is censored at its prespecified selection gate.
The next bounded design must condition site selection on actual earlier
measurement outcomes and choose a non-repeated second site; no noisy schedule
work is released.

The [J6Y conditional-site/nonrepeat contract](manifests/j6y-conditional-site-nonrepeat-matrix-2026-09-25.json)
now freezes that next two-branch exact matrix before execution. The independent
three-edge path uses an actually observed first prefix to select one eligible,
conditionally variable, non-repeated second site and then tests both frozen
second actions at a newly eligible third site. The six-edge loop measures its
complete first variable-star block and chooses the lowest-ID eligible
non-repeated second operator without selecting on its measured probability.
The common 60-CPU-second cap and zero stochastic histories, schedule arms,
bootstrap, new dependencies, or five-round caller changes remain fixed.
Branches and prefixes may censor separately; no replacement site or general
D4 feedback interpretation is allowed post hoc.
The [exact result](results/j6y-conditional-site-nonrepeat-matrix-2026-09-25.json)
passes all five pins and both branches within one CPU second. All four
positive first records of the three-edge path select second site 0 under the
conditional rule; its charge and either non-repeated, newly eligible third
charge are exactly fair and first-independent at fixed second result. The
loop's 16 positive complete-first records select non-repeated site 2, whose
second charge is deterministically `+1` in every prefix. Conditional selection
repairs the earlier structural censor but reveals no novel-site transfer in
these exact fixtures. Next audit whether a *full* second public instrument and
an action-conditioned next-round state can be defined on a bounded loop;
do not infer a general physical/noisy D4 feedback kernel from these local laws.

The [J6Z complete-second/stateful-readiness contract](manifests/j6z-full-second-stateful-readiness-2026-09-25.json)
preregisters two independent bounded prerequisites before execution. On the
same six-edge loop and common vacuum orbit, it will verify all eligible first
and second stars, condition every second one-site marginal on each actual
first record, and enumerate the complete 24-site second public law only if
at most six second sites remain variable; a finite Walsh contraction is
capped at 262,144 moment terms, 1,024 public rows and 60 CPU seconds. In
parallel scope, a read-only source audit checks whether the frozen J6P
adapter and five-round caller bind a postselected state to the next first
observation. These branches may pass or censor independently. Neither a
complete ideal second record nor a structural interface can by itself
justify noisy five-round sampling or a general D4 feedback law.

The [J6Z exact result](results/j6z-full-second-stateful-readiness-2026-09-25.json)
passes its six pins and both registered prerequisite branches within the
60-CPU-second cap. The complete six-variable-site first loop record has 16
positive strings. After public edge-0 correction, all 22 eligible second
stars have deterministic charge *conditional on each first record*: the
complete 24-site second public law has exactly 16 positive rows, one per
first record, and no conditionally variable second site. Across first
records, four second-site bits vary, so the second record is not a constant;
it carries only deterministic information from the first in this fixture.
The independent pinned interface audit finds no postselected-state token
carried to a next first observation, and the five-round caller still invokes
its phenomenological second provider rather than the fixed-path exact
adapter. Next preregister an action-bound postselected-state and next-first
law on a tiny exact fixture before any noisy schedule sample.

The [next-first limiting-fixture contract](manifests/j7a-postselected-next-first-limiting-fixtures-2026-09-25.json)
now freezes two independent no-new-fault exact branches before execution.
The prior two-edge path checks defer, partial and matched actions with the
same first/second exogenous keys, complete 24-site public records, a private
action-bound postselected projector sequence, and a fresh next-round first
measurement. The six-edge loop independently checks all 16 complete
first/second public prefixes and one varying-star three-block moment. Seven
tamper/action-binding controls, exact replay, a 60-CPU-second cap and zero
stochastic work gate the result. This is an ideal repeat limit, not a
general next-round noisy D4 density channel or five-round caller release.

The [registered exact result](results/j7a-postselected-next-first-limiting-fixtures-2026-09-25.json)
passes both bounded branches and all six source/input pins in under five CPU
seconds. On the two-edge path, all 10 positive first/action/second prefixes
produce a normalized next-first law: defer repeats the first complete public
record, while partial and matched corrections repeat their respective second
records in the no-new-fault limit. Seven action/prefix/private-field controls
fail closed. On the six-edge loop, all 16 positive complete first/second
prefixes repeat the second record at the next first observation; an independent
three-block calculation checks one site whose bit varies across prefixes.
This is a private state-token prototype and an ideal idempotence control,
not a physical noisy D4 future-state kernel or five-round integration. Keep
the frozen noisy schedule branch closed. The next separately registered gate
must determine a nonzero future-fault, action-conditioned next-first law and
its caller handoff before any further performance sampling.

The [nonzero-future-fault and caller-gate contract](manifests/j7b-future-fault-next-first-and-caller-gate-2026-09-25.json)
preregisters exactly one future red-X edge on the same fixed two-edge path,
crossed with defer, partial and matched correction over all 10 positive
first/second prefixes. Ordered first/second/future-first projector moments
must generate complete 24-site public next records, not a selected-site
surrogate. Its discriminating control compares defer-plus-future-edge-0 to
partial-plus-no-future after marginalizing the latter's second outcome;
both end at red-X support [4], so their exact total-variation difference
tests whether this finite ideal law retains earlier measurement history.
The independently pinned caller audit checks whether the frozen five-round
API can consume that private postselected state and future fault. Four
variable sites, 262,144 ordered moment terms, 128 positive next rows and
60 CPU seconds are strict caps; any exceeded branch is censored, not enlarged.
No stochastic histories, schedule arms, bootstraps or new dependencies are
authorized, and a finite result cannot establish a general D4 kernel.

The [exact result](results/j7b-future-fault-next-first-and-caller-gate-2026-09-25.json)
passes all six pins and both registered branches at their original bounds.
All 10 positive path prefixes have a normalized complete next-first public
law after the fixed future red-X edge: defer has one fair variable charge at
site 0, partial correction one fair variable charge at site 1, and matched
correction a deterministic next record conditional on the second record.
The full law has 16 positive next rows and uses 15,076 ordered moment terms;
six action/prefix/future-key/record controls reject. The same-final-support
contrast between defer-plus-future-edge-0 and partial-plus-no-future has exact
total variation zero for both first records. This is a finite negative
history-sensitivity control on one ideal geometry, not a general theorem.
The independent caller audit confirms precomputed future first records and
phenomenological second generation; the exact stateful law is still not wired
into the frozen five-round caller. Do not resume noisy schedule sampling.

The [three-edge history-memory discriminator contract](manifests/j7c-three-edge-history-memory-discriminator-2026-09-25.json)
now fixes the smallest prior geometry with genuinely random second outcomes.
Two action/history branches end at identical red-X support [3]: correct edge
0, measure the complete second record, then suffer a new physical fault on
edge 4; or correct edges 0 and 4, measure the complete second record, then
have no future fault. The pinned complete J6S laws supply eight and sixteen
positive first/second prefixes respectively. Before seeing the result, the
study requires a complete exact next-first 24-site public law, actual-sector
checks, a no-fault repeat control, and exact total variation after each
branch's second record is marginalized at each of four matched first records.
The strict caps are 4 variable next sites, 262,144 moment terms, 128 positive
next rows and 60 CPU seconds, with zero stochastic histories/arms/bootstraps.
This is a finite ideal-state discrimination; only a validated nonzero
contrast could justify a later physical caller-handoff test, and no schedule
sampling is released here.

The [J7C exact result](results/j7c-three-edge-history-memory-discriminator-2026-09-25.json)
closed this registered matrix: all four matched first records have zero
total-variation distance between the complete next-first public laws after
marginalizing their branch-specific second records. The branches include
different second-measurement sectors and future-fault timing, so this is a
finite negative control, not an isolated causal action effect or a general
state-sufficiency theorem. Thirty-two positive next rows and 58,624 ordered
moment terms stayed within the caps; no stochastic histories, arm evaluations
or bootstrap replicates were generated. The caller remains frozen. The next
bounded prerequisite is a source-grounded structural commutation/eligibility
screen for a fixture capable of discriminating measurement-history memory,
before any larger exact matrix or caller handoff.

The [J7D structural screen](manifests/j7d-cross-round-commutation-screen-2026-09-25.json)
is registered before computation as the cheapest next prerequisite. It covers
the already validated two-, three-, four-edge path and branch, and six-edge
loop supports. For every nonempty in-support correction and zero/one
within-support future red-X fault, it checks complete actual-sector second
and next-first eligibility and the triangle-vacuum cross-time star
commutator. Histories are compared only at identical initial geometry and
final red-X support. A second/next anticommutator is a necessary structural
opening for dephasing to change the marginalized next law, not evidence of a
nonzero public-law contrast. Same-sector commutation, J7C coverage, eight
source pins, a 60-CPU-second/800-history/100,000-pair/500,000-operator-check
cap, and zero stochastic work are predeclared. An opening only licenses a
separately preregistered exact Born-law follow-up; a finite all-commuting
screen does not prove general D4 state sufficiency.

The [J7D machine result](results/j7d-cross-round-commutation-screen-2026-09-25.json)
closes all five fixed supports: 628 histories, 1,624 matched-final-support
pairs, 1,101 pairs with a second/next anticommutator, and 281,960 cross-round
operator checks. The smallest opening is already on the two-edge path, between
correct-edge-0/future-fault-0 and correct-edge-4/future-fault-4 histories.
This is not a Born-law contrast: J7C also had an anticommutator but exact
total variation zero. The next bounded transition must preregister the
two-edge candidate's complete second and next-first public Born-law comparison
with J7C as a null control; no caller integration or noisy schedule sampling
is released by this screen.

The [J7E exact contract](manifests/j7e-two-edge-complete-next-law-2026-09-25.json)
now preregisters the smallest structurally open comparison, without enlarging
the geometry or changing the J7C null: on the shared two-edge physical state
and same complete first public record, branch A corrects edge 0 and later
faults edge 0, while branch B corrects edge 4 and later faults edge 4.
Each branch must independently enumerate its complete action-conditioned
second and next-first 24-site binary public Born laws; the former J6O edge-0
second law is an exact reproduction gate, not a substitute for branch B.
Only after every conditional law and binding gate passes may the two exact
complete-record total variations be calculated after each branch's second
record is marginalized at its matched first record. The 60-CPU-second,
262,144-moment, 16-second-row and 64-next-row caps are strict. An opening
may still yield zero TV; a nonzero finite value is not isolated action
causality or a physical noisy schedule effect. No caller integration,
stochastic history, arm evaluation or bootstrap is released.

The [J7E exact result](results/j7e-two-edge-complete-next-law-2026-09-25.json)
closes the two-edge comparison at its registered bound. Both branches have
four positive first/second prefixes and a fair, but different, second site;
the complete next-first law is normalized and has a fair site 1 at every
positive prefix. After marginalizing second results, exact total variation
is zero for both matched first records. All J6O reproduction, seven pins,
binding, repeat and replay gates pass with 7,568 ordered moment terms and
no stochastic work. The J7D anticommutator was not sufficient for a public
law difference. A next bounded transition should register a state-sensitive
exact influence screen across the previously fixed candidate geometries
before any larger full-law matrix or frozen-caller handoff; do not infer
general history erasure from two finite nulls.

The [J7F state-sensitive screen](manifests/j7f-state-sensitive-influence-screen-2026-09-25.json)
is registered before exact computation. It tests one preselected positive
complete first-record candidate and the first J7D cross-round witness in
each of the same five fixtures. It evaluates the exact unmeasured-second
next-star mean on the first-postselected state, then uses the full
actual-sector second-projector dephasing identity to determine whether that
one-site marginal can change; a two-edge explicit projector sum and J7E
exact null are controls. An opening ranks a later matched-history full-law
test but is not itself such a test; a five-fixture null says nothing about
other first records or next-site correlations. The 60-CPU-second and
262,144-moment-term caps, no-adaptive-replacement rule and zero stochastic
work are fixed before execution.

The [J7F exact result](results/j7f-state-sensitive-influence-screen-2026-09-25.json)
closes that small registered screen on all five supports with 8,512 ordered
moment terms. Four selected tree-geometry first records have unmeasured-second
next-star mean `1` and full-second-dephased mean `0`; the selected loop
witness has `0` in both. This is a one-site measurement-versus-no-measurement
influence, not a nonzero matched-history public-law contrast. J7E remains
TV `0` in both of its measured branches. The next bounded transition must
predeclare a matched-final-support full-public comparison on an additional
fixture or a scientifically justified stopping criterion, and retain the
frozen caller/noisy schedule boundary.

The [J7G three-edge contract](manifests/j7g-three-edge-matched-complete-next-law-2026-09-25.json)
is registered before computation as the smallest next matched-history
discriminator. It fixes the already validated three-edge chain, one J7F
positive complete first record of mass `1/4`, action/future-fault histories
`[0]/0` and `[4]/4`, both ending at the same initial/final support. J7D
shows an eligible second/next anticommutator only in the former branch at
the selected site, while J7F gives a nonzero first-postselected baseline.
The test now requires *both* complete 24-site second and next public laws,
exact marginalization and rational total variation, with J7C/J7E nulls
retained separately. A positive result would be finite ideal history
sensitivity, not isolated action causality: the two branches have different
later physical-fault keys. Strict 60-CPU-second/262,144-term, variable-site
and row caps, binding/replay gates and zero stochastic work are frozen.

The [J7G exact result](results/j7g-three-edge-matched-complete-next-law-2026-09-25.json)
closes this one-record/two-branch matrix at the registered bound. Both
complete action-conditioned second and next-first 24-site public laws
normalize. Branch A has two positive second prefixes and a fair next site
1; branch B has one positive second prefix and next site 1 fixed vacuum.
The exact complete next-public total variation is `1/2` after the second
records are marginalized at their common first record (mass `1/4`). Eight
pins, five binding controls, replay, two focused tests and the J7C/J7E
null controls pass with 8,972 ordered moment terms. This is finite ideal
history sensitivity, not an isolated correction effect: later physical
fault keys differ. The next dependency is to design a same-future-key
action comparison or keep this as a bounded noncausal history result; no
noisy schedule or threshold claim is released.

The [J7H identifiability audit](manifests/j7h-action-future-identifiability-audit-2026-09-26.json)
is registered before computation to resolve the next model gate, not to add
another probability contrast. In the fixed red-X support algebra, final
support is `E xor A xor F`. It freezes the J7G initial support, both public
actions and both later fault keys as a four-cell matrix, then exhausts all
eight in-support correction subsets under no/one later fault as a 32-cell
control. It will verify the exact J7G matched-final diagonal and the general
fact that, for common `E,F`, distinct actions necessarily have distinct
final physical support. This distinguishes the same-future-key *total
action effect* from the same-final-support *history* contrast. The audit
cannot itself establish either Born-law or schedule benefit; it has a
10-CPU-second, zero-sampling bound and five immutable pins.

The [J7H deterministic result](results/j7h-action-future-identifiability-audit-2026-09-26.json)
closes this prerequisite. All four selected cells reproduce the periodic
red-X support/flux map and the J7G diagonal; the other diagonal ends on
single edge 3. All 32 exhaustive control cells and 112 same-future
distinct-action pairs pass the cancellation identity. Five pins, replay,
two tests and both lab lints pass without any Born or stochastic work.
Thus the J7G `1/2` contrast remains finite ideal history sensitivity,
while a causal total action effect must hold `E,F` fixed and allow final
support to change. This is the next separately registered exact-law
question, not a human ranking problem or authorization for the five-round
noisy caller.

The [J7I same-future action-law contract](manifests/j7i-same-future-total-action-law-2026-09-26.json)
is registered before exact computation. It retains the same private initial
red-X support and selected complete first record (mass `1/4`), and crosses
public corrections `[0]`/`[4]` with both predeclared later fault keys `[0]`
and `[4]`. Within each future-key column only the action changes; final
physical support is deliberately *not* matched or conditioned on. Each of
the four cells must enumerate and normalize complete second and next-first
24-site public laws. Both prior diagonal laws are immutable replay controls.
The prespecified readout is exact rational full-public total variation
between actions within each future-key column, with deterministic flux
separation reported separately from any charge-information interpretation.
The 60-CPU-second/262,144-term and row/site caps, seven pins, binding controls,
and zero noisy histories, schedule arms, bootstraps and caller mutations are
hard stops. This finite ideal total-action diagnostic cannot support a JIT
performance, threshold, or general-channel claim.

The [J7I exact four-cell result](results/j7i-same-future-total-action-law-2026-09-26.json)
closes the registered comparison. Every complete second and next-first
public law normalizes, both prior diagonal laws replay exactly, and the
same-future action contrast has full-public total variation `1` for each
later-fault key. This is fully explained by distinct *public next flux*:
the interventions end on supports `{0,3,4}` versus `{3}`. Seven pins,
five negative binding controls, two focused tests and exact replay pass
at 15,724 ordered-moment terms. No noisy history, schedule arm, bootstrap
or caller integration ran. The next scientific question is whether a
charge-specific or matched logical-risk comparison remains after excluding
this deterministic flux distinction; that requires a fresh estimand and
cannot be inferred from this TV result.

The [J7J estimand-feasibility contract](manifests/j7j-charge-risk-estimand-feasibility-2026-09-26.json)
is registered as a two-branch prerequisite before any new Born-law work.
First, toggle the previously verified shortest six-red-edge simple cycle
on the public correction and check a fixed-initial/fixed-future four-cell
support matrix for distinct final physical supports but identical *public
next flux*. This is only a necessary geometric route to a charge-specific
action contrast; its logical winding class, admissible action semantics and
complete measured laws remain unproven. Second, audit whether the existing
single-error, selected-first-record exact law has the physical-error ensemble,
paired denominator and ground-state-relative Boolean-union loss required for
an expected-risk estimand. These branches are independent, reversible and
fit one 10-CPU-second zero-Born/zero-noisy-sampling matrix, so no researcher
ranking decision is needed. Neither branch may convert a structural or
conditional law into herald advantage or schedule performance.

The [J7J deterministic result](results/j7j-charge-risk-estimand-feasibility-2026-09-26.json)
closes both prerequisites. The verified six-red-edge cycle has zero public
flux boundary, so toggling it on the baseline correction produces two
distinct final red-X supports with *identical* next full public flux in
each fixed-future column. This is a geometric charge-law candidate, not
charge evidence: cycle homology/logical action, intervention admissibility
and complete Born laws remain unverified. Independently, J7I's one fixed
private error and selected first record lack an error ensemble,
unconditional paired Boolean-union loss rows and a denominator, so the
expected-risk estimand is not identified there. Five pins, two tests and
replay pass within 10 CPU seconds, with zero Born evaluations and noisy
work. The next prerequisite is the loop-action logical/admissibility and
full-law feasibility gate; a matched-risk program additionally needs its
own registered physical-error ensemble and score.

The [J7K loop-action preflight](manifests/j7k-loop-action-charge-law-preflight-2026-09-26.json)
is registered before exact work as the next cheapest dependency. It
reconciles all 36 red-edge IDs/endpoints against Lab 004's paper-normalized
L=2 topology before classifying the loop's ground-state-relative winding;
checks that baseline and loop-toggled public corrections have the same
boundary while separating a syntactically whitelistable red-X action from
an action actually emitted by the frozen JIT policy; and, at the same
selected first record of mass `1/4`, computes only conditional one-site
second-star marginals for both residual sectors. More than three
non-deterministic second sites censors complete-law readiness at the
registered cap. The 20-CPU-second/32,768-term budget excludes joint second
or next laws, histories, arms, bootstraps and caller mutation. A successful
preflight is still not a charge-specific law or performance result.

The [J7K exact preflight result](results/j7k-loop-action-charge-law-preflight-2026-09-26.json)
closes that registered gate. All 36 red-edge IDs/endpoints reconcile;
the six-edge difference is a nonbranching homologically trivial cycle
with no torus winding, and the two corrections have the same public
flux boundary. The baseline residual has one nondeterministic second
site, but the loop-toggled residual has five (`0,17,20,21,22`), above
the frozen three-site complete-law cap. Thus no joint second or
next-first law was computed, and the charge-specific contrast is
censored rather than estimated. The token interface can whitelist this
declared action, but emission by the frozen JIT policy is unverified.
Seven pins, deterministic replay and two focused tests pass; 1,412
ordered moments used about 0.013 CPU seconds with zero histories,
arms or bootstrap replicates. A new prospective, bounded screen may
seek another same-flux trivial loop within the existing cap; raising
this cap requires a distinct justified contract, not a J7K extension.

The [J7L alternative-loop screen](manifests/j7l-alternative-same-flux-loop-screen-2026-09-26.json)
is now prospectively registered as the smallest in-scope response to that
censor. On the identical physical error, selected complete first record,
vacuum orbit and baseline public action, it exhausts unique simple
six-red-edge cycles on the paper-normalized periodic L=2 graph. Each
cycle is classified by the existing homology rule; every trivial loop
is applied as a relation-free equal-flux public-action toggle and gets
only exact conditional one-site second marginals. It reports all loops,
not just a favorable action, and prospectively names the lexicographically
first loop with at most three variable second sites if any. The old J7K
loop and baseline are replay controls. The 60-CPU-second/65,536-term,
64-cycle cap retains the *same* three-variable-site law limit; no joint
law, histories, arms, bootstraps or caller change is permitted. No passing
candidate by itself supports charge information or schedule-risk benefit.

The [J7L exact screen](results/j7l-alternative-same-flux-loop-screen-2026-09-26.json)
closes this shortest-loop branch without a passing action. The graph has
exactly 12 unique simple six-edge cycles; all 12 are homologically trivial
and each produces the same public correction boundary as baseline. At the
fixed first record, every toggled residual has at least five
nondeterministic eligible second charge sites (five to seven), so none
passes the unchanged three-site full-law gate. Baseline and the prior J7K
cycle replay exactly. The screen used 9,156 ordered moment terms in about
0.034 CPU seconds and no joint law, histories, arms or bootstraps. This is
only a negative result for shortest loops on this one physical/first-record
fixture. The next design question is whether a *new*, prospectively bounded
exact-law feasibility calculation for five variable sites is affordable and
informative; neither cherry-picking a longer loop nor silently raising the
J7K/J7L cap is justified by this result.

The [J7M distinct five-site contract](manifests/j7m-five-site-complete-second-charge-law-2026-09-26.json)
is registered before any joint-law computation. It keeps the *predeclared*
J7K equal-flux loop and baseline, the identical physical red-X error,
positive first record, periodic geometry, vacuum orbit and full-binary
public second-record schema. J7L's exhaustive screen is used only to
justify a separate bounded resource decision, not to cherry-pick a new
action: two first-variable and five second-variable bits imply at most
`2^(2·2+5)=512` ordered moments per joint assignment and 16,384 for
the 32 loop assignments, well below the previous 65,536-term screen
budget. The new 32,768-term/60-CPU-second contract prospectively allows
five second-variable sites *only here*. It computes and compares both
complete second laws at identical public flux, with normalization,
one-site replay and public/private gates. It does not compute a
next-first law, policy risk, noisy history or threshold. Positive total
variation would be a finite ideal charge-record action effect, not an
information or decoding benefit; exact zero would close this fixture
as a charge-null control.

The [J7M exact complete-second result](results/j7m-five-site-complete-second-charge-law-2026-09-26.json)
passes the separate prospectively raised five-site bound. With the same
first record of mass `1/4` and *identical complete second public flux*,
baseline correction `[0]` has two equiprobable full charge records,
whereas the predeclared trivial-loop toggle `[1,30,32,34,35]` has all
32 five-bit charge records equiprobable. Their exact full-public
total-variation distance is `15/16`, wholly a charge-record contrast
because flux is matched. All one-site marginals replay J7K, both laws
normalize, ten pins and two focused tests pass, and 17,868 ordered
moments fit the 32,768-term/60-second contract. This identifies one
finite ideal *total action effect on the second charge record*, not an
information gain about the private error, better logical recovery,
policy-emitted JIT correction or noisy schedule performance. The next
dependent gate is a prospectively bounded fixed-future complete
next-first-law feasibility assessment with the same two public actions;
the five-round caller and risk study remain separate.

The [J7N fixed-future feasibility contract](manifests/j7n-fixed-future-next-first-feasibility-2026-09-26.json)
is registered as the cheapest dependency before trying to propagate the
charge contrast to another round. It crosses the *same* two public
actions with both already frozen single-edge later-fault keys `[0]`
and `[4]`, retains all 34 positive complete second prefixes from J7M,
and checks matched next public flux, next-star eligibility, and the
necessary-only second/next operator anticommutator. It also calculates
the frozen exact engine's denominator-plus-one-site ordered-moment work
from its bit-count rule without evaluating any Born law. This is a
four-cell deterministic structural/resource audit capped at 10 CPU
seconds and 2,500 operator-pair checks, with zero new moments, histories,
arms, bootstraps or caller changes. If the one-site stage itself exceeds
the previous 65,536-term ceiling, no full next law is authorized by
this contract; an analytical reduction must be investigated separately.

The [J7N read-only result](results/j7n-fixed-future-next-first-feasibility-2026-09-26.json)
closes that prerequisite without a Born evaluation. Both later-fault
keys preserve equal complete next public flux across actions. Each of
the four action/future cells has exactly one second/next anticommuting
operator pair, a necessary-only structural opening. However, applying
the unchanged exact full-law implementation to all 34 retained second
prefixes would spend 46,181,504 ordered moments *before* enumerating
next joint outcomes, versus the prior 65,536-term ceiling; each
loop-toggled cell alone projects 23,085,056. The audit made 1,936
bounded operator-pair checks and zero moment evaluations. This is a
cost of the present naive exact implementation, not a mathematical
lower bound or proof that the next-first laws differ. A prospective
symmetry/dephasing reduction focused on the single structural witness
is the next in-scope diagnostic; do not brute-force the full law or
increase the existing ceiling from this result.

The [J7O witness-reduction contract](manifests/j7o-witness-projector-reduction-2026-09-26.json)
prospectively tests the smallest algebraic alternative to that expensive
one-site screen, not a full-law shortcut. It retains both actions, both
fixed future keys and all 34 positive complete second records. For each
of the four cells it verifies same-round second-projector commutation,
Hermitian-involution witnesses and the unique second/next
anticommutator. The identity `P_a B P_a = 0` when `{A,B}=0` makes the
next witness charge fair after *every* positive complete second record,
provided its second-site projector was actually measured. This is an
exact one-site conditional statement only; other next sites and their
correlations remain unknown. The audit is capped at 10 CPU seconds,
3,000 operator-pair and 68 positive-prefix checks, with zero Born
moments, histories, arms, bootstraps or caller changes. A failed
commutation, involution, full-record or pin check censors the claim.

The [J7O algebraic result](results/j7o-witness-projector-reduction-2026-09-26.json)
passes all six pins and four action/future cells. It replays 2/32 positive
complete second records under each later-fault key, 68 prefix checks in
all, and all 2,860 bounded same-round/cross-round operator pairs. Every
eligible same-round second pair commutes; the unique next witness at
site 1 anticommutes with measured second site 0 for future `[0]` and
measured second site 2 for future `[4]`. The latter second outcome is
deterministically positive in the complete record, but is still a
measurement. Thus the projector identity gives exact conditional next
site-1 charge probabilities `1/2,1/2` for every positive prefix in both
actions and both future columns, with no Born moment evaluation. This
eliminates this one-site witness marginal as an action discriminator on
the fixture; it does **not** give the other next-site marginals, joint
correlations, complete next law, information gain or risk. The next
prerequisite is a prospectively bounded reduction or targeted exact test
of those remaining degrees of freedom, within the existing budget.

The [J7P operator-relation contract](manifests/j7p-next-operator-relation-matrix-2026-09-26.json)
prospectively classifies every eligible next-site involution in all
four J7N cells against the complete second-measurement block. A next
operator that anticommutes with a measured second operator has an exact
fair conditional bit; one equal or opposite to a measured operator has
the corresponding deterministic or flipped bit. Mere commutation is
**not** promoted to determinism. The full 24-site next public record
and same-future action total variation may be reconstructed only if
every site is resolved and at most one fair site remains; otherwise
the result is a partial map with explicit unresolved sites and no
full-law or risk claim. The four-cell audit is capped at 10 CPU seconds,
2,000 operator-pair checks, 68 positive-prefix checks, 136 possible
reconstructed public rows and zero Born moments, noisy histories,
schedule arms, bootstraps or caller changes. This distinguishes an
algebraically complete next law from a genuinely remaining numerical
or theoretical dependency without changing the approved compute budget.

The [J7P algebraic four-cell result](results/j7p-next-operator-relation-matrix-2026-09-26.json)
passes all seven pins and the registered zero-Born bounds. In **each**
cell, 21 of 24 next sites are exact signed repeats of measured second
operators, two are flux-ineligible with charge zero, and the remaining
site 1 is J7O's fair anticommuting witness. There are no unresolved
operators or multiple fair bits. Therefore the complete next public
law is reconstructed from every full second record and its J7M exact
mass without a Born expansion: for later fault `[0]`, baseline has two
equiprobable next records and loop-toggled action has 32; for `[4]`,
they have four and 64, respectively. At either held-fixed fault,
the full-public same-future total variation is exactly `15/16` with
matched next flux. The audit uses 1,936 operator-pair checks, all 68
positive second-prefix/future combinations, and 136 conditional
reconstructed rows; it evaluates zero new Born moments, noisy histories,
arms or bootstraps. This is a finite ideal *total action effect on the
next charge record*, not information about an unknown error, a matched
logical-risk reduction, policy-emitted correction or noisy JIT benefit.
An independent bounded Born spot-check of the algebraic reconstruction
is the next prerequisite before its use in any larger inference.

The [J7Q direct Born spot-check contract](manifests/j7q-direct-born-spotcheck-2026-09-27.json)
is registered before evaluating any additional ordered moments. It
selects the first positive complete second row in the pinned J7M result,
not a post-Born outcome choice, and fixes three one-site next probes:
baseline/future `[0]` at fair site 1 and deterministic repeat site 2,
plus the five-variable loop action/future `[4]` at fair site 1. These
cover both structural witness types, both actions and both frozen
future keys without pretending to re-evaluate all four joint laws.
The exact three-block expansion counts `128+128+32,768=33,024`
ordered-moment terms, below the pre-existing 65,536 ceiling, with a
60-CPU-second cap and no new dependency, stochastic history, schedule
arm, bootstrap or caller change. All three registered charge-0
conditional probabilities must replay `1/2`, `1`, `1/2`, respectively.
Any mismatch suspends promotion of J7P's algebraic full-law contrast;
a pass is a limited independent computational-route check, not an
independent physical model or full-law direct-Born proof.

The [J7Q registered direct spot-check](results/j7q-direct-born-spotcheck-2026-09-27.json)
passes all eight pinned inputs and three preselected probes. The
three-block ordered-projector expansion gives conditional next charge-0
probabilities `1/2` (baseline/future `[0]`, fair site 1), `1`
(baseline/future `[0]`, repeat site 2), and `1/2` (loop/future `[4]`,
fair site 1), exactly replaying J7P. Joint masses are `1/16`, `1/8`,
and `1/256` against pinned prefix masses `1/8`, `1/8`, and `1/128`.
The run spent exactly 33,024 ordered terms, below the registered and
prior 65,536 ceilings, with no full next-law Born enumeration or noisy
work. This independently checks representative algebraic cases through
the direct moment-expansion route, not every one of J7P's positive
prefixes or complete joint outcomes. The finite ideal matched-flux
charge-law contrast can remain as an internally validated result at
that stated boundary; the next scientific gate is whether it carries
*private-error information* under a matched error ensemble, which
requires a separate prospective model/estimand and must not be inferred
from total variation alone.

The [J7R two-branch identifiability audit](manifests/j7r-private-error-estimand-identifiability-audit-2026-09-27.json)
is registered before inspecting the frozen sources. It asks separately
whether the J7M/J7P/J7Q ideal selected-record laws contain an unknown
private initial error with a positive-prior competing alternative under
the same first record and actions, and whether any unconditional paired
Boolean-union logical-risk denominator and score exist for that *same*
physical ensemble. Both branches are read-only, capped at five pinned
artifacts and 10 CPU seconds, and use zero new Born terms, physical
errors, histories, schedule arms or bootstraps. The J6 five-round
phenomenological pilot is a scoring-design reference only, never a
numerically pooled ideal-projector cohort. A missing branch requirement
must be recorded as non-identifiability, not filled by assuming a prior
or treating the two fixed future faults as alternative initial errors.

The [J7R two-branch audit](results/j7r-private-error-estimand-identifiability-audit-2026-09-27.json)
passes five frozen pins and closes both estimands as *unidentified from
the existing fixture*. Only one private initial error is represented;
the two later-fault keys are not alternate initial errors, and no
positive-prior competing error has matched complete action laws at
the same first record. The ideal fixture also lacks unconditional
attempted-history risk rows and private paired Boolean-union scores.
J6's phenomenological risk cohort cannot be numerically transferred.
The next prerequisite is to freeze the smallest two-error,
same-first-record information design under one paper-normalized IID
red-X prior, while defining any unconditional full-channel risk target
separately with an ensemble, omitted-mass rule, matched keys, score and
denominator before acquisition. No new data or policy claim follows
from this audit.

The [J7S same-first error-pair preflight](manifests/j7s-same-first-error-pair-preflight-2026-09-27.json)
is prospectively registered as the cheapest prerequisite to that
information study. Under the R6AF paper-normalized IID red-X provenance,
it XORs the J7M private initial error with **all 12** pinned shortest
homologically trivial cycles, retaining the same complete first public
flux and testing exact positivity of the same 24-site full-binary first
charge/vacuum record. The declared `p_X=1/10` only assigns positive
IID weights; if a pair survives, the reported posterior explicitly
conditions this IID prior on the two supports and the selected first
record, not on the full error channel. The first lexicographically
positive candidate is selected only after the complete fixed screen;
no second public law or information score is computed here. Twelve
cycles, ten first-variable sites per candidate, 16,384 ordered moments
and 60 CPU seconds are hard caps; no histories, schedule arms,
bootstraps or new dependencies are authorized. An unconditional risk
estimand remains a separate dependent design with full-channel
denominator, matched keys and private Boolean-union score.

The [J7S exact first-record screen](results/j7s-same-first-error-pair-preflight-2026-09-27.json)
passes all nine pins and covers all twelve frozen cycle candidates.
Every one preserves the complete first flux and assigns positive exact
probability to the same full first charge/vacuum record; the base mass
replays `1/4`. The lexicographically selected candidate is
`[1,3,4,30,32,34,35]`, with first-record mass `1/64`. At the
registered sparse IID `p_X=1/10`, its *two-support-restricted* posterior
weight after the first record is just `1/104977`, giving a binary
entropy ceiling of about `0.000173` bit for any later information about
that selected error identity. The run spent 1,956 ordered moments and
0.013 CPU seconds, no complete second law or stochastic evaluation.
This establishes a same-first-record alternative error but no
information gain. Its extreme prior imbalance means the next bounded
prerequisite should prospectively compare the already screened
candidate weight/cost ceilings before committing the exact matched
second-law budget; the lexicographic candidate remains a structural
control, not an automatically promoted information target. Any
unconditional logical-risk design remains separately dependent on a
full-channel denominator and paired private Boolean-union score.

The [J7T candidate prior/cost matrix](manifests/j7t-candidate-prior-cost-matrix-2026-09-27.json)
is registered before any candidate ranking. It retains *all twelve*
J7S positive same-first alternatives, the same `p_X=1/10` restricted
IID prior, both J7M public actions and their common 22 eligible second
sites. For each candidate it computes the exact binary-error posterior
and entropy ceiling, then projects the frozen exact `full_law` term
cost for every `k_0,k_1=0..5` second-variable-site pair. This is
conditional cost arithmetic, not a second-law evaluation or a
mathematical lower bound on a different algorithm. The registered
selection retains *all ties* at the largest entropy ceiling among
candidate rows with at least one projected cell strictly below the
inherited 65,536-term limit; the original lexicographic pair stays a
structural control. This zero-Born screen has 432 arithmetic cells and
a 10-CPU-second cap. The subsequent information law remains dependent
on measured second-site counts, and any full-channel risk remains a
separate, unregistered scoring study.

The [J7T read-only matrix](results/j7t-candidate-prior-cost-matrix-2026-09-27.json)
passes five pins and evaluates all twelve candidate prior ceilings and
432 hypothetical second-variable-count cost cells with zero new Born
terms. The registered rule retains **both** tied five-edge errors
`[2,3,5,15,16]` and `[0,10,11,33,35]`, each with first-record mass
`1/16`, two-support-conditioned candidate weight `1/325`, and binary
information ceiling `0.030107` bit at `p_X=1/10`. For either error the
frozen two-action full-second engine projects a minimum 23,088 ordered
terms and fits the inherited 65,536-term cap only when the *actual*
second-variable counts in both actions are at most three. The earlier
lexicographic seven-edge control is too rare (`1/104977`) and exceeds
the engine cap even at its minimum 368,832-term projection. The next
prerequisite is a prospectively bounded, two-peer conditional
second-site-count audit, not a human ranking choice or an immediate
full-law run. No private-error information, full-channel logical risk
or policy benefit has yet been measured.

The [J7U four-cell prerequisite](manifests/j7u-conditional-second-site-count-preflight-2026-09-27.json)
is registered before exact one-site evaluation. It retains both
five-edge peers, the same complete first public record, and both public
actions; the private error never selects an online action. On the frozen
periodic ideal D4 orbit, it evaluates the exact first-record mass and
all 22 eligible one-site second-charge marginals in each of four cells.
The declared count is 45,088 ordered moments with a 46,000-term and
60-CPU-second cap. The observed variable-site counts feed only the
existing full-law term projection, strictly compared with 65,536. A
complete second joint law, information about the private error,
unconditional logical risk, policy comparison, stochastic history, or
bootstrap is not part of this preflight. Either peer may pass or fail
the cost gate independently; no human ranking is requested.

The [J7U exact result](results/j7u-conditional-second-site-count-preflight-2026-09-27.json)
closes all four cells and 88 one-site marginals in 45,088 ordered terms,
below the preregistered cap. Both peers have selected first mass `1/16`;
both have second-variable counts `(1,5)` across the two actions. The
frozen complete two-action `full_law` implementation consequently
projects 285,744 terms for either peer, above its inherited 65,536-term
ceiling. No complete second joint law or private-error information was
computed, and matching marginal counts do not imply matching joint
laws. The next distinct bounded transition is a prospectively registered
algebraic joint-law reduction/cost audit for **both** peers, retaining
the existing term ceiling and no human ranking. Full-channel logical
risk remains a separate scoring/denominator study.

The [J7V parity-moment/Walsh reduction](manifests/j7v-joint-second-walsh-reduction-2026-09-27.json)
is registered before any new joint-law computation. The two previous
error peers and both frozen public actions form the four target cells;
J7M's same-first-record base error under both actions is a two-cell
independent complete-law replay control. For each subset of the
non-deterministic eligible second sites, the commuting-star product
is an involution, so one exact parity-projector expectation replaces
the many redundant full-assignment projector expansions. A Walsh
inverse reconstructs every complete binary second public row. The
predeclared direct all-positive row per cell, base-control law
dictionary, exact one-site marginals, positivity, normalization, and
source pins are verification gates. At the frozen `(v,k)` values,
the entire six-cell matrix costs 51,816 ordered terms, below the
inherited 65,536 ceiling; execution is capped at 55,000 terms and
60 CPU seconds. This can establish complete finite ideal conditional
second laws, but it does not calculate private-error information,
unconditional logical risk, or a policy-emitted JIT effect.

The [J7V exact result](results/j7v-joint-second-walsh-reduction-2026-09-27.json)
passes all six cells, twelve pins, two complete base-control law
replays, six directly expanded full-row spot checks, all frozen
one-site marginals, exact positivity and normalization. Each peer
has two positive second public records under action `[0]` and 32
under `[1,30,32,34,35]`, with conditional probabilities `1/2`
and `1/32` respectively. The method spent 51,816 ordered terms;
the earlier 285,744-term figure describes the redundant unreduced
implementation, not a lower bound. The pre-result type-only runner
correction is logged in the manifest. This tick did not compare
the two peer laws or evaluate their binary-error information. The
next bounded transition must prospectively register that exact
conditional law comparison under the frozen restricted-pair prior,
without conflating it with full-IID information or unconditional
logical risk.

The [J7W restricted-pair information audit](manifests/j7w-pair-information-audit-2026-09-27.json)
is registered before comparing J7V's complete laws. Its four cells
cover **both** five-edge candidates separately against the same
three-edge base error, under **both** predeclared public actions and
the identical complete first record. The already declared 36-edge
IID red-X `p_X=1/10` prior is restricted to each two-support set;
first masses `1/4` and `1/16` fix candidate weight `1/325` before
looking at the second record. The analysis uses only full public
second-record keys, exact rational total variation and Bayes binary
error-identity classification risk, and two cross-checked formulas
for conditional mutual information. It is read-only, bounded by
four comparisons, at most 64 public rows per cell and ten CPU
seconds, with zero new Born terms. Equality of full laws is a
predeclared null, not a reason to switch candidate or action.
This finite restricted-pair information and classification estimand
is explicitly not full-IID information, logical-sector information,
unconditional Boolean-union logical risk, a JIT policy result or a
threshold.

The [J7W exact read-only audit](results/j7w-pair-information-audit-2026-09-27.json)
closes its four base-versus-peer/action cells with four pins, exact
normalization and identical full public record/flux gates. In all
four cells the complete base and candidate second likelihood
dictionaries are equal: TV `0`, conditional binary-error mutual
information `0` bit, posterior `1/325` after every second record,
and minimum binary error-identity classification risk unchanged at
`1/325`. Both entropy and KL formulas agree; no new Born terms or
stochastic work were used. This is a finite *restricted-pair,
selected-first-record* negative result. It neither erases the
fixed-error action effect nor establishes a full-IID, logical-risk
or JIT null. The next bounded dependency is a prospective structural
discriminator for genuinely different same-first-record
error-conditioned second laws, covering candidate branches without
human ranking and without promoting this null beyond its scope.

The [J7X all-error one-site operator discriminator](manifests/j7x-all-error-operator-discriminator-2026-09-27.json)
is registered before execution. It crosses all twelve J7T-positive
same-complete-first-record physical-error alternatives with both frozen
relation-free actions, plus a two-action base control. On the same ideal
periodic L=2 D4 orbit it uses projector anticommutation and initial-orbit
stabilizer relations to classify all 22 eligible second charges per
cell as exact `plus`, `minus`, `fair`, or `unresolved`. A *resolved changed
one-site marginal* proves a different complete second public law; a
match or unresolved site does not prove complete-law equality. The two
J7W peers are negative controls. The matrix is capped at 200,000
algebraic relation probes and 60 CPU seconds, with zero ordered Born
projector terms, histories, policy arms, bootstraps, or new errors.
No information, logical risk, schedule benefit, or threshold is an
estimand here. Positive witnesses require separately registered exact
complete-law and restricted-prior follow-up; a negative screen retains
joint-correlation and new-geometry possibilities.

The [J7X exact structural result](results/j7x-all-error-operator-discriminator-2026-09-27.json)
closes all 24 candidate/action cells and two base controls with
7,368 algebraic relation probes, all source/flux/operator and exact
J7M/J7W control checks, and zero ordered Born terms. No resolved
one-site second-charge marginal differs from the base. Under action
`[0]`, every cell has 21 resolved deterministic-plus sites; under
the loop action every cell has 17. Remaining fair/unresolved labels
do not certify complete-law equality or an information null. The
next separate bounded transition should test unresolved one-site
and/or joint-correlation signatures prospectively under the same
fixed candidate/action matrix before considering a new geometry.

The [J7Y low-order parity-moment matrix](manifests/j7y-low-order-second-moments-2026-09-27.json)
is prospectively registered as that next prerequisite. It retains all
twelve candidate errors, both relation-free actions, one selected
complete first record and the same ideal orbit. For each of the 24
candidate/action cells and two base controls it computes every one-site
mean among the one/five unresolved-or-fair second sites and all ten
pairs under the five-site action. The selected-first projector identity
reduces each commuting moment to at most `2^v` exact orbit terms;
anticommuting products have zero mean. The worst-case matrix is 33,252
orbit moment terms versus the inherited 65,536 cap, with a 60-CPU-second
stop. The base and two J7W complete-law peers must replay independent
fair bits; all first masses and public flux must match. A changed exact
singleton or pair moment proves a changed complete second public law,
but matching low orders cannot prove complete-law equality. This tick
does not evaluate higher-order charge correlations, restricted-pair
information, unconditional logical loss or any noisy JIT policy.

The [J7Y exact low-order result](results/j7y-low-order-second-moments-2026-09-27.json)
closes 24 candidate/action and two base cells: all 208 selected-first
singleton and pair parity moments are exactly zero. The previously
unresolved one-site means are therefore fair, and no pair correlation
distinguishes any candidate from the base. All pins, first masses,
public fluxes, commuting-operator and prior two-peer controls pass;
14,252 orbit-moment terms were used, with no ordered Born expansion or
stochastic work. The one-site/pairwise null does not imply equality
of the five-bit second public law. The next separate bounded
transition is a preregistered order-three-to-five joint-moment test
on the same candidate/action matrix before any full-law information
or logical-risk claim.

The [J7Z higher-order joint-moment contract](manifests/j7z-higher-order-second-law-2026-09-27.json)
is registered before computation. It retains the exact thirteen-error
set (base plus all twelve same-first alternatives) and both frozen
relation-free actions. Under the five-variable-charge action it tests
all ten three-site, five four-site and one five-site parity moments
per error, then joins the pinned J7Y low-order moments and inverts
the complete Walsh transform. Under the one-variable-charge action,
J7Y already determines the complete law. The 208 new high-order
moments and 26 complete public-law cells have a conservative
33,252 orbit-moment upper bound, below the inherited 65,536 cap,
and a 60-CPU-second stop. Exact base and two-peer full laws must
replay J7M/J7V; every public row must be rational, nonnegative,
unique and normalized. Equality or difference is restricted to
these thirteen errors, this selected complete first record, two
actions, and one ideal L=2 orbit. Full-IID information, logical
risk, noisy JIT policy and thresholds remain outside this tick.

The [J7Z exact complete-law result](results/j7z-higher-order-second-law-2026-09-27.json)
closes all 208 registered higher-order moments in 7,944 orbit terms:
every moment is zero. Combined with J7Y's lower orders, the exact
complete second public law is identical for the base and all twelve
same-first-record alternatives under each frozen action: two records
of probability `1/2` under `[0]`, and 32 records of probability
`1/32` under `[1,30,32,34,35]`, with identical public keys.
J7M's two base and J7V's four peer complete laws replay exactly,
and all pins, first masses, fluxes, rational positivity and
normalization pass. This rules out *second-record error-identity
discrimination within these thirteen supports on this selected
ideal record*, not full-IID information, logical recovery or noisy
schedule benefit. The next bounded dependency must change a
separately registered first-record/error/geometry fixture while
holding the public-interface and claim boundary fixed; no
threshold or broader prior claim follows from this null.

The [J8A alternative-first-record contract](manifests/j8a-alternate-first-record-mass-matrix-2026-09-27.json)
prospectively freezes the cheaper prerequisite matrix: four complete
first binary charge/vacuum records (all-plus replay plus all three
nonempty assignments on base-variable sites 1 and 2) crossed with
the base and all twelve pre-existing same-flux errors. It retains the
same ideal L=2 D4 orbit, remediated public boundary and two relation-free
actions for a later comparison, while capping this tick at 8,192
ordered first-projector terms and 60 CPU seconds. The alternative
first-record and error-support branches are both covered; different
geometry needs a separately pinned state/cost and does not gate this
cheaper test. A first mass is only a support/conditioning gate, never
second-record discrimination.

The [J8A exact feasibility result](results/j8a-alternate-first-record-mass-matrix-2026-09-27.json)
closes all 52 cells in 7,760 ordered terms. The base's four first
records each have mass `1/4`; the selected all-plus candidate masses
replay prior evidence. The three alternate records retain 11, 11 and
10 positive alternative-error supports, respectively. Therefore a
matched second-law discriminator is identifiable on each branch,
but its value is not yet known. No second laws, histories, arms,
bootstraps, full-IID posterior, logical risk or noisy JIT test ran.
The next bounded transition is to preregister an exact second-public-law
matrix for every positive alternative-record/error pair and both fixed
actions, with a new cost bound and all-zero-mass cells explicitly excluded.

The [J8B complete-second-law contract](manifests/j8b-alternate-first-complete-second-laws-2026-09-27.json)
is registered before execution. It freezes all thirteen errors, all four
first public records (including all-plus replay), both relation-free
actions, and the ideal L=2 orbit. J8A's 48 positive error/first-record
cells imply 96 exact second-law cells; the four zero-mass pairs are
excluded under both actions. The method shares signed first-projector
orbit moments across the records, audits all 22 eligible second-charge
sites per cell, reconstructs the full variable-site Walsh law (at most
five sites), and requires exact replay of all 26 all-plus J7Z laws.
It retains the inherited 65,536 orbit-moment, 200,000 algebraic-probe
and 60-CPU-second caps, with zero new ordered projector expansions,
histories, schedule arms or bootstraps. A conditional-law difference is
not a full-IID information or logical-risk result; a gate failure
censors the matrix rather than licensing a narrower post hoc selection.

The [J8B exact complete-law result](results/j8b-alternate-first-complete-second-laws-2026-09-27.json)
closes the full registered matrix: 96 positive exact second-public-law
cells, eight action cells excluded by zero first mass, and all 26
all-plus laws replaying J7Z. Every one of the 64 positive
alternative-first candidate/action cells has total variation zero
from the base law at the same complete first record and action.
The full 22 eligible second sites were checked in each branch,
including deterministic repeated charge bits; the one/five
variable-site Walsh laws are rational, nonnegative and normalized.
The calculation used 20,240 orbit moments and 20,628 algebraic
relation probes under the registered caps. No histories, arms or
bootstraps ran. This is a conditional thirteen-support ideal-orbit
null only; first-record masses themselves differ and some candidate
outcomes fall outside the four base-positive records. The next
bounded discriminator must prospectively change the private-error
support or geometry, or explicitly scope a full-IID channel study,
before any broader information or logical-risk conclusion.

The [J8C new-support/geometry cost contract](manifests/j8c-support-geometry-cost-matrix-2026-09-27.json)
is registered before execution. It covers two reversible L=2 error-support
branches—every graph-simple four- and eight-edge cycle toggled onto the
same base physical error, including both trivial and nontrivial winding—
and an independent source-normalized L=3 graph/readiness check. The
existing twelve six-edge cycles must replay exactly. Every L=2 candidate
must have the same full first flux; the all-zero first charge mass is
evaluated for *all* candidates only if their combined first-projector
cost fits 65,536 terms and no candidate exceeds ten variable sites.
If not, the result is structural/cost-only, not a selected subset of
exact masses. The L=3 branch does not inherit an L=2 quantum orbit or
public instrument and will not generate a physical law. No second
record, risk, noisy history, schedule arm or threshold is evaluated.

The [J8C exact support/cost result](results/j8c-support-geometry-cost-matrix-2026-09-27.json)
replays the twelve old six-edge cycles and finds zero four-edge and
54 eight-edge graph-simple cycles at L=2. All 54 eight-edge cycles
are homologically nontrivial: 18 each in winding directions `(1,0)`,
`(0,1)` and `(1,-1)`. Their toggled private errors preserve the same
complete first flux and have positive exact all-zero first-charge
mass (four `1/16`, four `1/64`, 46 `1/256`). The full set costs
28,992 first-projector terms, below its 65,536 cap, with no more than
ten variable first sites. This supplies winding-distinct matched-record
candidate supports, not second-record discrimination or a scored
logical-risk effect. At L=3, the source graph has 54 vertices and
81 red edges, but J6L/J6M physical-state and sequential-instrument
pins exist only at L=2. The next bounded transition is a preregistered
L=2 second-law cost/witness design covering all three winding classes
under the same public actions. A larger-geometry physical comparison
remains gated on a new state/instrument derivation, not human ranking
of these reversible diagnostics.

The [J8D winding-class witness contract](manifests/j8d-winding-class-second-law-witness-2026-09-27.json)
is registered before its exact calculation. To cover all three reversible
L=2 winding branches within the existing ideal-orbit cap, it freezes one
representative per class using only J8C projected first-projector cost,
with loop-edge lexicographic tie-break, plus the prior base. The three
selected loop supports are `[0,1,3,4,7,8,31,32]`,
`[0,1,3,4,9,11,24,26]`, and `[0,2,12,14,19,20,34,35]` for
winding `(1,-1)`, `(1,0)`, and `(0,1)` respectively. All four private
errors share the same positive complete first record, and each is
crossed with both frozen relation-free actions. The eight exact full
second-public-law cells must account for all 22 eligible second sites,
replay both prior base laws, normalize, and fit 65,536 orbit terms,
200,000 relation probes, five variable second sites per cell, and 60
CPU seconds. Equality for a representative cannot close its entire
winding class; no full-IID information, logical risk, noisy JIT or
larger-geometry result is authorized by this test.

The [J8D exact witness result](results/j8d-winding-class-second-law-witness-2026-09-27.json)
passes every registered gate. Eight full second-public-law cells
normalize, all 22 eligible second sites per cell are accounted for,
and both base laws replay the prior exact control. All six selected
candidate/action laws equal the matched base law (total variation
zero); each action retains two or 32 positive complete records as
appropriate. The run used 292 first plus 1,212 second orbit moments
and 1,726 relation probes, with zero histories, arms or bootstraps.
This is a one-representative-per-winding-class negative witness, not
an all-54-support class null. The next bounded dependency is to cost
the remaining 51 supports prospectively before any broader second-law
matrix; first-record information and full-IID/logical-risk questions
remain distinct.

The [J8E remaining-support cost contract](manifests/j8e-remaining-support-second-law-cost-2026-09-27.json)
is registered before any new singleton calculation. It includes all
51 previously untested eight-edge supports and the three J8D controls,
each under both fixed public actions, with the same selected first
record and ideal L=2 orbit. Exact first masses and every one of 22
eligible second-site one-bit expectations per cell are verified;
pair/higher groups are classified only for operator-relation and
prospective orbit-expansion cost, not evaluated as second-law moments.
The inherited caps are 65,536 orbit terms, 200,000 relation probes,
five variable second sites per cell and 60 CPU seconds. A complete
108-cell cost matrix can authorize a separately registered exact-law
run only if every site and combined cost gate passes. A truncated
prefix is explicitly censored. This step cannot itself establish a
class-wide second-law or full-IID/risk result.

The [J8E preflight result](results/j8e-remaining-support-second-law-cost-2026-09-27.json)
is cost-censored at its registered singleton orbit-term gate. Forty
of 51 new support rows close under both actions, with 80 exact
one-site/structural cost cells; the next row completes only its first
action before stopping partway through the second. Actual first plus
singleton second orbit work reaches 64,544 of 65,536 allowed terms,
and the relation-aware projected full-law work on the processed
prefix already reaches 187,936 terms. No complete second law is
computed, and 11 candidate rows plus all three controls remain
unresolved in this cost audit. The current expansion cannot cover
all 54 supports under one inherited cap. The next bounded transition
is an operator/symmetry-reuse cost diagnostic or fixed nonselective
batch design *without increasing total authorized compute*; no
class-wide negative inference or human ranking of winding directions
follows from this censor.

The [J8F prospective cost contract](manifests/j8f-orbit-character-reuse-audit-2026-09-27.json)
registers both in-scope alternatives before evaluation. It tests exact
Z-character reuse and first-relation indexing on all 54 eight-edge
supports under both fixed actions, against the 40 J8E singleton rows
and three J8D controls. The separate fixed-batching branch uses the
existing J8E expanded-work prefix as a lower bound; batching cannot
reset the combined cap. Inherited ceilings remain 65,536 actual unique
orbit-character evaluations, 65,536 legacy expanded terms for the
nonreuse branch, 200,000 relation lookups and 60 CPU seconds. This
audit computes first masses, singleton second means and prospective
higher-group character costs only; it creates no complete law, history,
schedule arm or bootstrap. A favorable cost projection would require a
new preregistration before any complete-law run.

The [J8F machine audit](results/j8f-orbit-character-reuse-audit-2026-09-27.json)
closed cost checks for 45 of 54 supports and 90 paired action cells,
including all 40 J8E singleton replays and three J8D controls. Its 512
direct moment checks passed, but distinct orbit-character work hit
65,536 on the next support. The processed-prefix projection for any
later full laws already has 179,885 distinct Z-mask characters, beyond
the same cap. The older nonreuse expanded prefix alone costs 187,936
terms, so fixed batching cannot meet an unchanged aggregate budget.
Nine supports remain uncosted; no new complete laws were generated.
Both tested approaches are closed at their bounds. The next transition
is a separately preregistered, more compact exact identity or symmetry
diagnostic with an unchanged total cap, or a genuine resource/scope
decision if no bounded in-scope diagnostic can discriminate.

The [J8G prospective binary-constraint preflight](manifests/j8g-binary-constraint-rank-preflight-2026-09-27.json)
tests a smaller analytic prerequisite before any further full-law
attempt. The exact orbit-character identity turns nonzero Z-character
terms into binary linear constraints on first-projector subsets. For
all 54 supports and both fixed actions, it records the constraint rank,
affine preimage size and a conservative count for at most five variable
second charges, while replaying J8F's known nonzero singleton support.
It evaluates no character, moment, complete law or stochastic history.
The inherited 65,536-term and 60-second ceilings remain unchanged.
Equal ranks do not certify action-preserving physical symmetry or equal
second laws; signed cancellation is a separate unvalidated alternative.

The [J8G rank result](results/j8g-binary-constraint-rank-preflight-2026-09-27.json)
closes all 54 support rows and 108 action cells without any orbit
expectation or complete-law evaluation. Rank 4/6/8 occurs in 4/4/46
supports; affine first-subset classes have size one, two or four. The
conditional upper count for all nonempty variable-second groups is
4,920 terms, assuming the nine unmeasured supports satisfy the
inherited five-variable-site bound. This does not certify their site
counts or the signed affine sum. The next bounded prerequisite is to
register and validate that exact signed solver against earlier full-
law controls, while resolving the nine singleton/site-count cells;
only then may a separate all-support law contract be considered.

The [J8H prospective signed-solver gate](manifests/j8h-signed-affine-solver-gate-2026-09-27.json)
registers four existing complete-law supports as exact replay controls
under both fixed actions, plus only the nine J8F-unresolved supports
for first-mass and 22-site singleton/site-count checks. Binary Gaussian
elimination selects the affine first-projector subsets; their ordered
signs are summed exactly. Control law reconstruction is replay only;
no new complete law is calculated for the nine supports. The combined
work and CPU ceilings remain 65,536 terms and 60 seconds, with 512
direct-moment spot checks, and all old public-record/action gates
frozen. A pass would license separate all-support-law registration,
not same-tick execution or a scientific information claim.

The [J8H exact gate result](results/j8h-signed-affine-solver-gate-2026-09-27.json)
replays all eight existing control laws exactly and closes all 18
formerly unresolved singleton/site-count cells. Each of the nine
supports has one variable second site under action one and five under
action two; the combined work is 1,560 signed terms plus 512 direct
moment checks, below the inherited cap. No new complete law is in this
result. The next bounded transition is a *new* preregistration for all
54 exact second public laws, with frozen first record, action binding,
law normalization, direct replay, total work cap and strict absence of
full-IID/risk/noisy-JIT/threshold interpretation.

The [J8I prospective all-support law contract](manifests/j8i-all-support-complete-second-laws-2026-09-27.json)
freezes all 54 J8C eight-edge error supports (18 per winding class)
and the base, the same selected full-binary first record, both
relation-free public red-charge actions, the action-bound full-binary
second record, and exact rational total variation versus matched base
laws. The J8H signed affine solver computes all 22 singleton moments
and every group of at most five variable sites; Walsh inversion must
produce nonnegative normalized public rows. Eight prior base/class-
representative laws, public fluxes, first masses and site sets replay.
The combined 65,536-term and 60-CPU-second ceilings remain unchanged;
no histories, arms, bootstraps or new dependencies are authorized.
This matrix asks only whether *these 54 errors* differ in the second
public law after *this one first record* under each fixed action. It
cannot answer full-IID information, unconditional/logical risk, noisy
JIT, L=3 or threshold questions.

The first J8I attempt wrote a withheld machine result but failed its
integrity acceptance: the direct-moment spot-check loop executed zero
checks. The prospective contract now records a narrow integrity
amendment—one admissible direct signed-product/moment check in each of
110 action cells—and writes a separately named replacement result.
No scientific question, support set, action, compute cap or prior result
is changed. Only the replacement may support the all-support law claim.

The [verified J8I replacement](results/j8i-all-support-complete-second-laws-verified-2026-09-27.json)
closes all 54 candidate supports under both actions, plus base, with
110/110 direct checks and eight old laws replayed. Every one of 108
candidate/action complete-law total-variation values versus the
matched base is exactly zero; action one has two positive public rows
and action two has 32. The signed-affine work is 4,719 terms, safely
under the original cap. This is a selected-first-record equality over
the frozen finite error set, not a full-IID information or logical-
risk result. The next discriminating transition should freeze an
actual physical-error prior and all relevant first records, then test
whether second-public-record information remains absent after proper
mixture weighting; no adaptive schedule or threshold inference follows
directly from this law matrix.

The [J8J prospective coverage prerequisite](manifests/j8j-full-prior-coverage-feasibility-2026-09-27.json)
first tests whether that mixture is even identified by available laws.
At the already frozen J7S exact rational rate `p_X=1/10`, it enumerates
the entire GF(2) preimage of J8I's first public flux on the same 36-edge
L=2 physical channel. Both independent, reversible checks run together:
the prior weight of exact-law supports versus every compatible private
error, and the structural count/cost of all possible first-charge
records in that flux sector. The prospective 60-CPU-second and 65,536-
term limits are unchanged. No first-record probability, second law,
posterior mixture, logical score, history, schedule arm or bootstrap is
computed here. If positive-prior supports remain, J8I cannot by itself
justify a full-prior information null, whatever its selected-record
conditional laws show.

The [J8J verified audit](results/j8j-full-prior-coverage-feasibility-verified-2026-09-27.json)
finds boundary rank 23, hence 8,192 compatible private errors. Only 67
have known complete second laws and 8,125 remain. At `p_X=1/10`, the
known 67 carry about 99.8804% of the selected-*flux*-sector prior
weight, but first-charge conditioning can reweight the omitted tail.
Across all compatible errors, 2,872,423,652 per-error first-charge
strings are structurally possible; this is an upper count, not a
positive-law count, and it exceeds the 65,536-term limit. The first
runner invocation failed closed on an input-field name and wrote no
result; the next machine file was withheld for lacking the explicit
IID-normalization assertion. The separately named verified replacement
closed both branches. No full-prior
mixture, information or risk calculation has run. A separately
registered selected-first-record tail certificate or stronger symmetry
reduction is the next affordable prerequisite; full-channel claims
also need the other first-flux sectors.

Before that tail certificate, the [J8K public-record remediation contract](manifests/j8k-first-public-vacuum-remediation-2026-09-27.json)
addresses a newly identified upstream defect: J8A encoded first-record
`vacuum=not(flux or charge)`, whereas the frozen J6O independent-membership
public interface requires `vacuum=1-charge`. J8B embedded all 52 such
first records. The two fluxful bits disagree in every case. The
prospectively bounded matrix regenerates all 52 first-record cells and
all 104 error/first/action cells through their pinned original runners;
it then corrects only the public first-record projection and checks
all exact masses, 96 complete second laws, eight zero-mass exclusions,
26 old-law replays and both actions. A third branch audits the only
two J8B fields consumed by J8C and the J8J 67-support union. Original
J8A/J8B public-record payloads remain withdrawn provenance; no tail,
full-prior information, risk or noisy-JIT inference proceeds until
the replacement passes. The inherited 60-CPU-second and exact-work
ceilings are unchanged.

The [verified J8K remediation](results/j8k-first-public-vacuum-remediation-summary-2026-09-27.json)
passes all three branches: 52 corrected first records, 52 corrected
embedded copies, all 96 second laws and eight exclusions, 26 replayed
all-plus laws, and no changed numeric mass or total variation. J8C
uses only two unchanged J8B aggregate fields; corrected J8B and J8I
revalidate J8J's 67 known-law supports. The old J8A/J8B artifacts are
retained only as invalid public-record provenance. The next authorized
prerequisite returns to the selected-first-record omitted-tail bound;
this representation repair itself yields no full-prior information,
logical-risk, noisy-JIT or threshold result.

The [J8L prospective tail certificate](manifests/j8l-first-record-tail-certificate-2026-09-27.json)
freezes the smallest four-branch matrix before execution: all four
corrected base-positive complete first public records sharing the selected
first flux. At the inherited exact `p_X=1/10` prior, each branch uses its
known-law supports to calculate exact first-record joint mass `A` and a
worst-case omitted prior tail `T`; `T/(A+T)` bounds the omitted posterior
weight without evaluating an unknown first law. The all-plus branch uses
67 known supports, while the other three each use 13, including zero-mass
exclusions. Both fixed public actions are checked for equality within the
known positive-law subsets. The registered work is at most 106 known
error/record cells, zero new Born terms and 60 CPU seconds; no other flux
sector, physical rate, size, history, arm or bootstrap is added. A loose
bound is a negative/censored answer, never license for full-prior inference.

The [J8L verified result](results/j8l-first-record-tail-certificate-2026-09-27.json)
closes all four registered branches with exact rational arithmetic and
zero new Born terms. The worst-case omitted posterior mass is at most
`0.005031330054` for the selected all-zero-charge record and at most
`0.169854320857`, `0.169854320857` and `0.170289281145` for the other
three tested records. The first runner invocation failed closed on a
manifest-key path and wrote no result; a reader-path-only amendment was
re-pinned before the successful run. The all-plus bound is tight enough
for a limited bounded-observable robustness statement on that record,
not a measured full mixture. The alternate-record bounds are much looser.
Next separately register a symmetry/likelihood tail-tightening feasibility
check for those records; all other first records and first-flux sectors
remain outside the audited prior, so no full-IID information claim follows.

The [J8M prospective structural-tail and cost screen](manifests/j8m-structural-tail-and-cost-screen-2026-09-27.json)
registers the next two reversible prerequisites together before evaluation.
First, on all 8,192 selected-flux private errors, the complete first-record
projector is bounded by every one-site first-star projector. A deterministic
conflict sets an omitted likelihood upper bound to zero; otherwise any fair
site caps it at `1/2`. Exact IID prior weights then give four improved
worst-case posterior bounds using J8L's fixed known joint masses. Second,
the 54 eight-edge supports are crossed with all three alternate first
records in a *read-only* direct-projector cost projection. The combined
65,536-term and 60-CPU-second ceilings are inherited. If that direct
matrix exceeds the term cap, censor it without calculating any new first
mass, second law, history, action arm or bootstrap. A structural bound is
not a measured omitted likelihood or a full-channel information claim.

The [J8M verified replacement](results/j8m-structural-tail-and-cost-screen-verified-2026-09-27.json)
closes both branches. All 8,192 same-flux errors pass the direct
pairwise first-star commutation gate, and every reused exact known first
mass lies below its one-site bound. At `p_X=1/10`, the four omitted
posterior upper bounds become `0.002522009558`, `0.000702020018`,
`0.000702020018` and `0.000067384877`, in all-zero, site-1, site-2
and sites-1-plus-2 charge order. The 54-support alternate-record direct
exact-work projections are 28,800, 28,800 and 28,672 terms, totaling
86,272; the full three-record matrix is therefore cost-censored.
The first arithmetic file lacked direct commutation verification and
is withheld; adding that assertion changed no core number and kept
the verified run within the inherited 60-second limit. No new Born
mass, second law, posterior mixture, history, schedule arm or bootstrap
was evaluated. The next separately registered prerequisite must cover
other first records/flux sectors before any full-IID information claim,
or justify a narrower reader-facing inference from these four records.

The [J8N prospective channel-coverage envelope](manifests/j8n-four-record-channel-coverage-2026-09-27.json)
registers the smallest next two-branch prerequisite before arithmetic.
The first branch sums the four *disjoint* corrected complete first-record
events: their exact known joint masses give a lower probability and the
J8M one-site omitted bounds give an upper probability. Subtracting
both endpoints from the exact J8J selected-flux prior bounds all
remaining first-charge records in that flux sector. The second branch
uses the normalized 36-edge IID prior to calculate the exact mass of
all *other* first-flux sectors. This separates within-sector record
coverage from full-channel coverage, and tests whether the four-record
conditional null can possibly represent the physical ensemble. It
adds zero Born terms, laws, histories, arms, bootstraps or dependencies,
stays under the inherited 60-CPU-second/65,536-term ceilings, and
cannot establish information or logical risk in the missing records.

The [J8N verified coverage result](results/j8n-four-record-channel-coverage-2026-09-27.json)
closes both registered arithmetic branches. The four disjoint complete
first records account for `93.485256%`–`93.579376%` of their selected
first-flux sector at the frozen prior; other first-charge records in
that sector still hold at least `6.420624%`. The four records together
have full-channel prior mass only between `3.1094830537e-5` and
`3.1126136499e-5`, while all other first-flux sectors have exact
complementary mass `0.999966738251852`. Distinct public arrays,
vacuum convention, IID normalization, interval partition, input hashes
and zero-new-compute counters pass. This closes the registered coverage
prerequisite, not a full-IID information/risk question. The next
separately registered prerequisite is a bounded other-flux public-law
representative or symmetry-feasibility test, not a threshold fit or
unbounded full-channel law enumeration.

The [J8O prospective two-representative feasibility matrix](manifests/j8o-other-flux-representative-feasibility-2026-09-28.json)
freezes the next prerequisite before computation. It tests the vacuum
physical error and one-edge physical error as two distinct other-first-flux
sectors under the same ideal L=2, p_X=1/10, complete full-binary
pre-action observation. Each branch enumerates its 8,192 compatible IID
errors, calculates an exact sector prior and one base first-record Born
mass, then applies commuting one-site projector domination to bound the
omitted-error posterior. Their fixed public actions are unchanged and not
run. The inherited 60-CPU-second and 65,536-term caps apply jointly;
there are at most two new first masses and no second laws, histories,
schedule arms, bootstraps, dependencies, full-IID information/risk claim,
or threshold fit. Loose or censored bounds are retained as feasibility
findings, not a reason to silently expand scope.

The [J8O verified result](results/j8o-other-flux-representative-feasibility-2026-09-28.json)
closes both branches: vacuum and one-edge first-flux prior masses are
`0.022528937220256` and `0.002504026482110`; their complete
all-zero-charge first-record base likelihoods are one. The one-site
omitted-error posterior upper bounds are `0.000011933136` and
`0.000173945568`, respectively. Distinct-flux, all-error commutation,
prior-normalization, full-binary public-record and pinned-hash gates
pass at 6.061271 CPU seconds with only two one-term first masses.
This does not identify the other flux sectors' public laws or a
full-channel information/risk result. Next separately register a
bounded flux-symmetry or uncovered-sector-mass/cost prerequisite.

The [J8P prospective low-weight flux-coset matrix](manifests/j8p-low-weight-flux-coset-screen-2026-09-28.json)
registers that next bounded prerequisite before arithmetic. It takes
every 0-, 1- and 2-edge physical red-X support, deduplicates the
resulting public first-flux sectors, sums each complete 8,192-error
coset under the same IID p_X=1/10 prior, and reports reached versus
unreached channel mass. A second branch groups sectors by minimum
support weight, flux Hamming weight and exact prior; this tests only
simple *prior* equivalence, not geometric or public-law symmetry.
The direct lower bound of one first-law term per compatible private
error is projected against the inherited 65,536-term ceiling. Both
branches share a 60-CPU-second, 5,464,064 integer-weight-evaluation
cap and add no Born law, histories, arms, bootstraps or dependencies.
Weight-three supports, symmetry promotion, full-channel
information/risk and thresholds are outside this tick.

The first J8P execution failed its replay assertion before any result
was written: the stored decimal numerator string needed explicit
integer conversion for the two-argument rational constructor. The
registered integrity amendment changes only that assertion type and
re-pins the runner; the experimental matrix and caps remain frozen.

The [J8P verified result](results/j8p-low-weight-flux-coset-screen-2026-09-28.json)
closes both branches. All 667 weight-at-most-two supports reach
distinct first-flux sectors; their complete coset priors total
`0.288680551769476`, leaving `0.711319448230524` in other sectors.
The 36 one-edge priors match, while the two-edge/four-flux-bit class
has nine distinct prior values, rejecting flux-weight-only prior
symmetry. Direct first-law evaluation for every compatible error in
these sectors has a one-term-per-error floor of 5,464,064, over the
inherited 65,536-term ceiling. Exact IID normalization, 8,192-error
kernel, J8O replay, hashes and 0.583655-CPU-second cap pass with zero
new Born laws, histories, arms, bootstraps or dependencies. This does
not rule out a genuine operator-law reduction. Next separately test
a bounded geometry/operator-law symmetry or targeted prior-weighted
information bound before any full-channel inference.

The [J8Q prospective base-first-law matrix](manifests/j8q-low-weight-base-first-laws-2026-09-28.json)
tests the next cheapest operator-law prerequisite over all 667 frozen
J8P sectors, not a post-data subset. Each sector retains its J8P
minimum-weight private base error and complete pre-action first public
record with sector flux, all-zero charge and complementary vacuum.
One branch preflights the combined exact first-projector work and, only
if it fits 65,536 terms, evaluates each base likelihood. The second
compares those likelihoods within exact-prior groups and forms a
worst-case omitted-error posterior bound using sector prior minus
base prior; no omitted law is evaluated. Both branches share 60 CPU
seconds and zero second laws, histories, arms, bootstraps or new
dependencies. Equal prior or equal one-record likelihood would be
only a necessary witness, never an operator-law symmetry proof or
full-IID information/risk claim.

The [J8Q verified base-first-law census](results/j8q-low-weight-base-first-laws-2026-09-28.json)
closes both registered branches. The 667 canonical base likelihoods
are one in 595 sectors and one-half in the 72 two-edge/two-flux-bit
sectors. All 12 exact-prior groups have only one base likelihood;
this is a necessary witness, not a geometry/operator-law symmetry
proof. Disjoint prior-weighted base-record contributions sum to
`0.277850261054250`, between zero and the `0.288680551769476`
total prior in the reached sectors. All 667 eligible-site,
commutation, J8O replay, prior and hash gates pass; the cost
preflight and evaluation use 739 exact terms in 0.224622 CPU seconds,
with zero second laws or stochastic work. The remaining private-error
laws, other first records and 71.1319% channel prior in other fluxes
remain unresolved. Next separately test a valid geometry/operator
action on matched first/second public records or a high-mass group's
prior-weighted omitted law, without promoting the base witness to a
full-channel information claim.

The [J8R prospective action-binding and high-prior tail matrix](manifests/j8r-action-binding-and-two-edge-tail-2026-09-28.json)
covers two independent, reversible forks within the inherited budget.
First, all 36 one-edge sectors are checked against both frozen public
action sets and their action-conditioned second-flux masks. Because
the singleton action must keep edge 0 fixed, a strict
action-preserving relabeling has at least three edge-membership
classes; this is only a necessary obstruction, not an automorphism
classification. Second, the highest-exact-prior two-edge J8P sector
is selected prospectively (lexicographic tie break), its exact J8Q
base first mass is reused, and all 8,192 compatible errors receive
the commuting one-site omitted-likelihood upper screen. The joint
60-CPU-second cap allows no new Born law, second charge law,
history, arm, bootstrap or dependency. Loose bounds and failed
fixed-action pooling are valid outcomes, not grounds to expand the
matrix or infer full-IID information/risk.

The [J8R verified result](results/j8r-action-binding-and-two-edge-tail-2026-09-28.json)
closes both branches under 2.777636 CPU seconds. The one-edge cases
have three necessary fixed-action membership classes of sizes 1, 5
and 30; both actions yield 36 distinct second-flux masks. The
prospectively selected highest-prior two-edge base is `[0,1]`; its
complete first-record base likelihood is `1/2`, and all 8,191 omitted
same-flux errors have a fair one-site first-star marginal. The
omitted posterior upper bound tightens from `0.026546923919` to
`0.013452016793`. All-error commutation, sector-prior replay,
first-record and hash gates pass with zero new Born/second laws,
histories, arms or bootstraps. This is a fixed-action obstruction
and one-record bound, not a geometry/operator automorphism or
full-channel information result. The next bounded test must carry
the action under any proposed relabeling, or target the remaining
high-mass omitted public laws directly.

The prospective [J8S matched-law contract](manifests/j8s-high-prior-pair-second-laws-2026-09-28.json)
chooses the unique maximum-prior omitted error `[30,32,34,35]`
within the J8R `[0,1]` first-flux sector, before evaluating its law.
It crosses those two private errors with both unchanged relation-free
public actions, freezes the same complete all-zero-charge first record,
and requires four normalized complete action-conditioned second public
laws plus exact paired total variations. Action-covariant operator
relabeling is a possible later cost reduction, not needed to test this
one pair; no symmetry or full-IID inference is preregistered. The
inherited 60-CPU-second and 65,536-term ceilings, source/hash,
commutation, direct-moment and normalization gates stop the run if
any cell fails. No history, schedule arm or bootstrap is allowed.

The [J8S verified matrix](results/j8s-high-prior-pair-second-laws-2026-09-28.json)
passes all four cells. The selected omitted support is uniquely
`[30,32,34,35]`; its complete first likelihood is `1/8`, versus
`1/2` for base `[0,1]`. Both complete action-conditioned second laws
have exact paired total variation zero. This is a finite null
second-record contrast for one pair, not a full-IID null or an
operator-symmetry proof. The next bounded transition should test a
prospectively selected higher-information error/record pair or a
validated action-covariant operator reduction before broadening any
claim; keep the inherited caps and no noisy schedule sampling.

The [J8T prospective prerequisite](manifests/j8t-weight-three-prior-and-law-cost-2026-09-28.json)
tests whether direct channel coverage is tractable before seeking an
action-covariant operator reduction. It enumerates all 7,140
weight-three physical supports, deduplicates their first-flux sectors
against the 667 lower-weight sectors, sums each new sector's exact
IID prior over 8,192 compatible errors, and projects the cost of one
complete all-zero-charge base-first law per new sector. Two reversible
branches—prior coverage and public-law cost—are in one matrix, with
no Born law evaluated. The 60-CPU-second, 58,490,880 integer-prior
evaluation and inherited 65,536 exact-term bounds are frozen; no
operator symmetry, public-law pooling or full-IID inference is
assumed. If direct base laws exceed the term cap, a separate validated
reduction remains necessary rather than a budget extension.

The [J8T exact preflight](results/j8t-weight-three-prior-and-law-cost-2026-09-28.json)
passes both branches in 8.536158 CPU seconds. Weight-three supports
add 7,020 distinct first-flux sectors, lifting exact reached-sector
prior from `0.288680551769476` to `0.512938052191612`; 120 of the
7,140 supports collide with another new sector, none with the old
667. The 7,020 canonical new-base all-zero-charge first laws project
to only 9,360 terms, below the inherited 65,536 ceiling. This is
cost feasibility, not those laws themselves. The next bounded
transition should register and run that exact new-base census, with
no same-flux private-error pooling, second laws or full-IID claim.

The [J8U prospective exact census](manifests/j8u-weight-three-base-first-laws-2026-09-28.json)
now freezes all 7,020 J8T new first-flux sectors and their
lexicographic three-edge private bases. It evaluates each complete
all-zero-charge first public record using the commuting ideal D4
projectors, then sums only the disjoint base-error/record joint masses
and compares with the exact reached-sector prior. One-site and
zero-site controls, source hashes, 9,360-term and 60-CPU-second caps
are mandatory. The competing possibility that equal structural
classes have different exact base likelihoods remains open until
this run; even equality would not authorize operator-law symmetry,
same-flux error pooling, second-law or full-IID inference.

The [J8U verified census](results/j8u-weight-three-base-first-laws-2026-09-28.json)
closes all 7,020 registered canonical-base first laws in 9,360 exact
terms and 2.14531 CPU seconds. Their complete all-zero-charge first
likelihoods are `1` in 4,896 sectors, `1/2` in 2,016 and `1/4`
in 108. The new disjoint base-error/record contribution is
`0.183286608643394` of the full physical channel; with the
at-most-two base cohort it is `0.461136869697644`, below the
reached-sector prior `0.512938052191612`. No other same-flux
private-error or second law was inferred. A next bounded transition
must test a validated algebraic reduction or prospectively selected
high-prior nonbase-law matrix before channel-wide inference; an
equal-prior/base-likelihood pattern is not operator symmetry.

The [J8V prospective equal-prior collision matrix](manifests/j8v-equal-prior-collision-second-laws-2026-09-28.json)
now targets the missing same-flux private-error laws, rather than
expanding only canonical-base coverage. All 120 first-flux sectors
with two distinct three-edge supports are partitioned by the J8U
canonical-base likelihood `1`, `1/2` or `1/4`; the maximum exact
J8T sector prior in each stratum, with lexicographic tie break,
selects one sector before any new Born law. Both equal-prior private
errors are crossed with the same full all-zero-charge first record
and both unchanged relation-free public actions. Complete second
laws and exact paired total variations are evaluated only after a
positive first mass; a zero-mass alternative is retained as a
first-record exclusion, not replaced. The 60-CPU-second and
65,536-term bounds, direct first/second checks and action-binding
gates apply. This direct matched matrix is a prerequisite to decide
whether a general algebraic/operator reduction is worth pursuing;
it does not assume or prove one, and cannot yield full-IID risk.

The [J8V exact matched result](results/j8v-equal-prior-collision-second-laws-2026-09-28.json)
closes all three strata with six positive complete first laws and 12
normalized complete second laws. Both private errors in each pair
have the same first likelihood. In the deterministic-first stratum,
their second-public laws have total variation `3/4` under both fixed
actions; in the `1/2` stratum the singleton/five-edge contrasts are
`0`/`1/2`, and in the `1/4` stratum both are zero. Thus the earlier
one-pair null is not universal, and a full second record can carry
extra information for a restricted equal-prior, same-first-record
pair. This is not full-IID information or logical-risk improvement.
The [J8W prospective posterior certificate](manifests/j8w-same-flux-posterior-certificate-2026-09-28.json)
freezes the same three pairs, complete first records and two public actions.
It admits every omitted error in each selected first-flux sector through
its exact sector prior, bounding its unknown specified-first-record likelihood
between zero and one; no omitted second law or new Born term is inferred.
The registered output is a lower bound on selected-pair posterior mass and
a reverse-triangle lower bound on one selected error's second-public-law
contrast against its complete private-error complement. Its exact
5-CPU-second arithmetic matrix is a prerequisite to larger reductions.

The [J8W exact certificate](results/j8w-same-flux-posterior-certificate-2026-09-28.json)
finds selected-pair posterior lower bounds `0.9990296503`, `0.9974504520`
and `0.9477533523` across the three first-likelihood strata. For the
deterministic-first witness, either fixed action yields a conservative
one-error-versus-full-complement second-law TV lower bound `0.746607`;
the `1/2` stratum's five-edge action yields `0.492371`, while its singleton
action and both `1/4` actions remain zero-bound. All are conditional on the
specified complete first public record and first-flux sector. The next
bounded question is whether a validated operator-law reduction can cover
other records and sectors within the inherited exact-term budget; none of
these bounds is a full-IID information, logical-risk or noisy-JIT result.

The [J8X prospective deterministic-first collision census](manifests/j8x-deterministic-first-collision-census-2026-09-28.json)
tests the simplest possible operator-law reduction prerequisite: evaluate
all 12 double-support three-edge sectors whose canonical first record is
deterministic, with both same-weight private errors and both unchanged
public actions. This is a direct 24-first-law/48-second-law matrix within
the inherited 60-CPU-second and 65,536-term caps. A homogeneous TV pattern
would only support a finer symmetry search; a heterogeneous pattern would
falsify pooling by weight, flux and first likelihood alone. No post-result
sector selection, stochastic history or operator automorphism is allowed.

The [J8X exact census](results/j8x-deterministic-first-collision-census-2026-09-28.json)
closes the complete class: all 24 first likelihoods are one, but the
two-action exact second-law TV patterns split into eight `(0,0)`, two
`(3/4,3/4)` and two `(0,1/2)`. All 48 complete second laws normalize;
the earlier J8V positive row replays exactly. Thus the coarse structural
invariants do not support second-law pooling. The next bounded step must
identify and validate additional action/operator structure before any
attempt to reduce laws across other sectors or first records. No full-IID
information/risk, noisy schedule or threshold follows.

The [J8Y prospective two-branch reduction diagnostic](manifests/j8y-action-overlap-and-low-order-witness-2026-09-28.json)
keeps all 24 J8X sector/action cells frozen. It tests action/error
support-overlap signatures for conflicting exact TVs and compares the
complete-law TV with the best one-bit and two-bit public-charge marginal
TV. Both diagnostics use only already evaluated complete public laws,
with 7,200 exact marginal contractions and no new Born term.

The [J8Y exact result](results/j8y-action-overlap-and-low-order-witness-2026-09-28.json)
finds two overlap-signature conflicts, four full-TV cells exceeding every
single-charge marginal, and one full-TV `3/4` cell where *all* one- and
two-charge marginals have TV zero. This falsifies both proposed coarse
reductions on the restricted class and shows a genuinely higher-order
joint public-charge contrast in one fixed witness. The next bounded
question is the minimum joint charge order for that witness, not a
full-channel or logical-risk inference.

The [J8Z prospective marginal-order contraction](manifests/j8z-minimum-joint-charge-order-2026-09-28.json)
freezes the unique J8Y cell where complete second-public TV is `3/4`
but every one-/two-charge-bit TV is zero. All 64 subsets of its six
variable charge sites are contracted exactly, along with parity moments;
outside sites must be fixed identically under both private errors. No
new Born law, public action, private pair or first record is introduced.

The [J8Z exact contraction](results/j8z-minimum-joint-charge-order-2026-09-28.json)
finds minimum positive joint-marginal and parity order three. Only two
disjoint triples, `[0,20,22]` and `[1,17,21]`, have positive three-site
TV (`1/2` each); the six-site TV is `3/4`. This narrows the finite
mechanism to joint public-charge correlations without establishing
operator symmetry, law reuse or any channel-wide risk gain. A next
bounded test may audit the two triple-parity operator relations against
the direct public laws before any broader inference.

The [J9A prospective operator-relation audit](manifests/j9a-triple-parity-operator-relation-2026-09-28.json)
freezes those two triples, both private errors and the same public action.
It compares six orbit-operator products with exact public-law parity moments,
then tests whether the two parity bits jointly retain the six-site TV.
It permits no new Born laws, histories or sector selection and has a five-CPU-second cap.
Either a two-stabilizer explanation, an incomplete relation or an integrity
censor is reported without extrapolating to other sectors or logical risk.

The [J9A exact operator audit](results/j9a-triple-parity-operator-relation-2026-09-28.json)
closes the selected cell: both triple products are `+1` orbit stabilizers
for one private error and zero-mean nontrivial orbit characters for the other.
The former six-charge law is uniform on the 16 strings satisfying both
even-parity constraints; the latter is uniform on all 64 strings. The two
parity bits retain the complete-law TV `3/4`. This local explanation does
not supply a sector-wide automorphism, other-record law reuse or full-IID
information/risk. Any broader inference requires a separately registered
cross-sector operator-character test.

The [J9B prospective cross-sector character census](manifests/j9b-cross-sector-character-census-2026-09-28.json)
retains all 12 J8X deterministic-first sectors and both frozen public
actions. It replays every active-charge orbit character, exact signed
affine support and pairwise TV against all 48 stored direct second laws,
then tests whether parity-rank pairs alone classify the heterogeneous
contrasts. Null and positive cells are included without post-result
selection. Its five-CPU-second, 3,072-character bound permits no new
Born law, history, action or scope expansion; no law reuse follows unless
a later operator automorphism is independently validated.

The [J9B exact class census](results/j9b-cross-sector-character-census-2026-09-28.json)
replays all 48 direct second laws with 424 orbit-character products and
uniform signed-parity affine supports. Among 24 paired cells, 18 are null,
two have TV `1/2` and four have TV `3/4`. Parity-rank pairs have no TV
conflict inside this restricted class: rank zero on both laws is null,
one-sided rank one gives `1/2`, and one-sided rank two gives `3/4`.
Five positive cells first differ at one bit; only the frozen J9A cell
first differs at order three. These patterns do not validate an
operator automorphism or support new-law reuse. The next prerequisite
is a specific action-preserving signed-character map with held-out
direct-law validation, not another broad unverified reduction.

The [J9C prospective spatial-map prerequisite](manifests/j9c-action-preserving-spatial-map-2026-09-28.json)
enumerates every color-preserving red-edge graph map that fixes the
singleton public action and preserves the five-edge action set, then
requires an induced 12-face/108-qubit bijection preserving all D4
star, CZ and triangle operators. Any survivor mapping frozen J8X pairs
back into the evaluated class must replay their complete public laws
under both unchanged actions. Graph-only maps cannot license law reuse;
absence of a nontrivial map closes only this restricted spatial route.
The preregistered caps are five CPU seconds, 10,000 search nodes,
256 graph maps and zero new Born terms, histories or dependencies.
The first pre-data invocation failed at a geometry-label assertion:
Lab 004 flux-boundary vertex labels are not kagome star-center labels.
The pinned red physical-qubit endpoints now supply the latter; no map
was enumerated or result written before this source-schema correction.

The [J9C completed spatial-map gate](results/j9c-action-preserving-spatial-map-2026-09-28.json)
finds only identity among maps preserving blue/green colors and both
frozen public actions. Identity passes the full 108-qubit/36-star
operator geometry and all 48 stored-law replays; there is no
nonidentity member of this restricted family to validate or reuse.
This closes the spatial-symmetry route under fixed actions, not any
nonspatial operator relation. A next bounded prerequisite can assess
whether such a relation has an affordable, falsifiable search under
the inherited character-work cap before evaluating new laws.

The [J9D prospective affine-relabeling gate](manifests/j9d-affine-relabeling-gate-2026-09-28.json)
tests the cheapest nonspatial necessary condition on all 24 already
evaluated deterministic-first pair/action cells. It compares exact
affine parity ranks and support cardinalities from J9B, with all 18
equal-law cells retained as controls. An invertible affine public-bit
map—including sign flips and site permutations—cannot change support
cardinality. The five-CPU-second gate adds no operator characters,
Born terms, public laws, histories, schedule arms or bootstrap draws.
It cannot exclude non-bijective operator identities or establish
uncomputed first-record mixtures and full-IID risk. A failed source,
action, count or rank integrity check censors the conclusion.

The [J9D exact rank gate](results/j9d-affine-relabeling-gate-2026-09-28.json)
passes all 24 rank/support checks: 18 equal-law cells are controls,
and every six unequal-law cells has unequal parity rank and support
cardinality. Thus no invertible affine public-charge relabeling can
map either paired law to the other in this finite class. This is not
a no-go for non-bijective signed-character identities or a new-law
calculation. The remaining in-scope prerequisite is to identify a
specific falsifiable non-bijective relation and bound its cost before
any broader first-record mixture; if none exists within the inherited
cap, seek a genuine resource/scope decision rather than pool laws.

The [J9E prospective quadratic-character quotient](manifests/j9e-quadratic-character-quotient-2026-09-28.json)
specifies one non-bijective exact reduction before new-law evaluation.
Ordered Pauli-product signs are quadratic on the affine preimage of
the ground-orbit Z-character condition, so an exact GF(2) Gauss sum
can replace subset enumeration if its phase convention replays direct
controls. The registered matrix exhausts synthetic width-0–3 forms,
replays 55 J8I first masses and all 2,420 second-site singleton means,
and stresses one deterministically chosen high-variable private error
from only the first 256 J8J coset masks. The diagnostic mass is not a
new public law. The inherited 65,536 signed-phase and 60-CPU-second
ceilings, fixed actions, source hashes and zero new histories/arms/
bootstraps remain frozen. Failed phase, replay or cap checks censor
the quotient; passing does not authorize pooling or full-IID risk.

The [J9E exact replay gate](results/j9e-quadratic-character-quotient-2026-09-28.json)
passes 150 synthetic forms, 55 known first masses, 2,420 known second
single-site means and 4,727 held-out affine-phase checks with 9,453
signed-phase evaluations in 0.473167 CPU seconds. The fixed-prefix
stress error has 19 variable first sites but affine-kernel dimension
three; the 55 old controls have kernel dimension at most two. Thus
the quotient is validated for these controls, but this run does not
show that the 8,192-error selected-record mixture fits the cap or
that it improves on the earlier small-k solver. Next register a
bounded full selected-first-record *mass-only* census of those errors
before any complete second-law or risk calculation.

The [J9F prospective mass-only census](manifests/j9f-selected-first-mass-census-2026-09-28.json)
now fixes that dependent test: enumerate the entire 8,192-error same-
flux coset for J8I's one all-zero-charge first public record at exact
`p_X=1/10`, using the J9E quotient or cheaper direct affine sum under
one aggregate 65,536 signed-phase, 200,000 first-site and 60-CPU-
second budget. Replay all 55 old masses, the high-variable stress
fixture, J8J's complete site histogram and selected-flux prior mass.
Only full completion licenses the selected-record probability and
the old 55 errors' posterior weight share. A capped prefix is
censored; no second public law, other first record, history, arm,
bootstrap, logical-risk or full-IID claim is authorized here.

The [J9F exact mass-only result](results/j9f-selected-first-mass-census-2026-09-28.json)
completes all 8,192 same-flux errors with 19,862 signed-phase and
180,224 first-site checks in 3.552997 CPU seconds; 55 known masses,
the J9E stress fixture, J8J variable-site histogram and total flux
prior replay exactly. All errors have positive likelihood for the
selected public first record. Its exact probability is about
`7.8699080e-6`; the 55 errors with previously computed second laws
carry `99.3845%` of the posterior at this record, leaving `0.6155%`
uncomputed second-law weight. This is a selected-record denominator,
not a complete second-law mixture or full-IID risk. The next bounded
test should derive worst-case omitted-law contamination bounds for
the already evaluated finite second-law contrast under fixed actions;
new second laws remain separately gated.

The [J9G prospective omitted-law certificate](manifests/j9g-omitted-second-law-bound-2026-09-28.json)
combines the completed J9F selected-record denominator with all 110
stored J8I complete second laws under the two unchanged public
actions. It first replays every full flux/charge/vacuum law and exact
prior weight. Only if the 55 known-error laws coincide separately
under each action may the remaining 8,137 errors be represented by
an arbitrary unknown law of exact weight `epsilon`. For each fixed
action it then bounds full-mixture total variation from the common
known law, any fixed-target 0-1 Bayes-risk improvement, and private-
error information using `h2(epsilon)+epsilon log2(8137)`. This
five-CPU-second, zero-new-law calculation supplies worst-case
selected-record bounds, not actual information gain, a per-outcome
posterior guarantee, unconditional Boolean-union loss or full-IID risk.

The [J9G exact two-action certificate](results/j9g-omitted-second-law-bound-2026-09-28.json)
replays all 110 complete public laws and all 8,192 first-record
weights. The 55 known-error laws are identical separately under each
action (two versus 32 positive public rows). Omitted-error weight is
exactly `809314423250142987013913/131483716067635033072123673`
(`0.61552445%`), so any full second-law mixture is within that TV
distance of its action's common known law. For a fixed hidden target
with observation-independent 0–1 loss, the possible second-record
Bayes-risk improvement at this first record is at most the same
`0.6155` percentage points; private-error information gain is at
most `0.134015031978` bits. These are worst-case bounds, not actual
gains, adaptive JIT decisions or unconditional Boolean-union scores.
The next higher-information branch is to give the separate positive
same-flux witness an absolute prior weight and seek a rigorous
physical-prior information lower bound without inventing missing laws.

The [J9H prospective physical-prior information-floor contract](manifests/j9h-physical-prior-information-floor-2026-10-01.json)
now freezes that smallest follow-up. It replays all three previously
selected, distinct complete first records and all 12 known conditional
second public laws, crosses their six pair/action contrasts under the
two unchanged globally fixed public actions, and checks exact IID
three-edge prior weights against J8W. Equal pair priors and first
likelihoods give a binary equal-posterior subproblem at each record;
the information chain rule and binary Pinsker inequality bound the
full-prior `I(E;O2|O1,a)` below by the sum of exact pair joint masses
times squared second-law TV, divided by `2 ln 2`. The three records
are disjoint, so their nonnegative contributions may be added. A
five-CPU-second, zero-new-law/zero-history cap and source/action/full-
public-law replay gates apply. Positive results may establish only a
strictly positive conservative ideal private-error information floor,
not the actual channel information, a logical-risk improvement,
adaptive JIT benefit, noisy fault tolerance, size scaling or threshold.

The [J9H exact six-cell result](results/j9h-physical-prior-information-floor-2026-10-01.json)
replays all twelve full second laws, six pair TVs, three disjoint full
first records and exact pair joint masses in `0.00887` CPU seconds.
The two globally fixed actions have conservative full-prior
`I(E;O2|O1,a)` floors `2.5078403×10^-5` and `3.0651381×10^-5`
bits. This is a strict positive *private-error* information lower
bound with unknown-error contributions retained as nonnegative, not
an actual full-channel information value or action ranking. The
next prerequisite is to test whether this information distinguishes
logical classes rather than only private errors within one class;
no logical Bayes-risk or noisy JIT claim is released.

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

The translation-interface matrix is registered and fully executed. It passes
normalization, perfect/zero-noise limits, action binding, causal-prefix
separation, identical histories across the four schedule branches, and the
ground-state-relative logical criterion: all eight groups and 20 fixtures pass.
The only disk change was the J1-E4C-audited `d4_charge.py` hash in the public
adapter and source contract. The 77-test compatibility audit establishes public
behavioral compatibility, not internal implementation equivalence. Production
histories, performance evaluations and bootstrap replicates remain zero. The
next transition may preregister the smallest matched-history stochastic pilot;
it must freeze cells, histories, schedules, uncertainty and stop rules before
generating any history.

- Do not model measurement noise as independent flips on a single static snapshot.
- Do not let an online decoder access future detector events or ground truth.
- Do not treat syndrome-readout correction as sufficient while herald readout remains perfect by assumption.
- Do not claim the Lyons–Brown threshold numerically; the source establishes existence under weak local circuit noise.
- Stop if immediate, fixed-delay, JIT, and offline paths do not share identical fault histories and inner-decoder semantics.
- Do not launch a large spacetime threshold surface before tiny-volume enumeration and a bounded runtime pilot pass.

## Completion criteria

The Lab requires separately accepted source reproduction, causal-state implementation, invariant verification, bounded data, schedule comparison, resource analysis, report, and visual spacetime traces. A useful negative result localizes whether failure belongs to the observation model, schedule, inner decoder, or gauging/ungauging layer.
