# Current execution — 2026-09-09

The user has reopened Lab 004 compute/sampling planning. Execute `manifests/compute-scaling-2026-09-09.json`: unchanged-decoder serial/process-batch timing, exact equivalence, and a bounded 40/80/160-iteration sensitivity pilot. Use measured throughput and diagnostics to specify a new prospective production campaign. Previously withdrawn/aborted scans stay excluded; the prior R6AJ transfer remains incomplete, not silently completed or replaced by first-stage evidence. Lab 007 remains the theory follow-up.

# Lab 004 — Reproduce and benchmark intrinsic-heralded decoding in the D4 topological order

## Motivation and relation to Lab 002

Lab 002 develops a scalable belief-matching decoder for the project's phenomenological herald model. Lab 004 instead anchors decoder research to the concrete D4 noise and fusion-measurement model of Jing, Sala, Jiang, and Verresen. The two Labs may be compared only after they consume the same D4 observation record.

Lab 005 is the complementary spacetime/scheduling branch. It will invoke a Lab 004 decoder only after a causal commit decision; Lab 004 itself retains ideal-measurement spatial benchmarks so decoder error and schedule error remain distinguishable.

The scientific goal is to separate three quantities that must not be conflated:

1. the performance of the paper's practical intrinsically heralded MWPM decoder;
2. the best constrained minimum-weight explanation on small instances; and
3. the Bayes-optimal logical decision conditioned on the measured fusion record.

## Source-method boundary

The paper does **not** implement a linear/integer-programming decoder for its D4 `[2]` benchmark.

- Its unheralded baseline is unit-weight PyMatching MWPM.
- Its practical heralded decoder is PyMatching with strongly negative weights on edges adjacent to measured intermediate Abelian charges: `w_e = 1 - n_e K`, `n_e in {0,1,2}`, with invariant `K=3E=27L^2` because the source lattice has `E=9L^2` edges.
- Its conditioned optimum sums posterior weight by logical sector and is evaluated through a statistical-mechanics mapping and Monte Carlo.
- A Steiner-tree problem appears in the paper's more general fusion setting and can motivate an ILP formulation, but that is an extension, not the published D4 `[2]` implementation.

Lab 004 will therefore reproduce the published decoder first, then add a clearly labelled MILP oracle and an exact Bayesian oracle on bounded systems.

## Hypotheses and alternatives

### H1 — Reproduction

On the paper's D4 observation model, heralded MWPM reproduces the qualitative and quantitative improvement over syndrome-only MWPM within finite-size and sampling uncertainty.

Alternatives: a convention mismatch, negative-weight matching semantics, or an incorrect observation likelihood prevents reproduction.

### H2 — Optimization versus information

The gap between heralded MWPM and the exact conditioned Bayes decision can be decomposed into an algorithmic gap rather than attributed vaguely to “herald information.”

Alternatives: the finite-size Bayes gap is negligible, or the practical decoder fails for identifiable topological/negative-cycle reasons.

### H3 — Transfer to belief matching

After observation matching, Lab 002 belief matching may approach the small-system Bayes oracle more closely or scale more favorably than exact optimization.

Alternative: belief matching adds no value beyond the published heralded MWPM rule on the physical D4 record.

## Registered work packages

### R0 — Source and method audit

Status: complete. Record the noise model, fusion outcomes, likelihood, decoder objectives, reported thresholds, numerical budgets, and open problems without silently translating one algorithm into another.

Deliverable: `wiki/records/jing2025-decoder-method-audit.md`.

Normalization remediation: `wiki/records/r0-lattice-normalization-remediation.md`. The primitive honeycomb fixtures have `2L^2` vertices and `3L^2` edges, whereas the paper's coloured kagome unit cell induces `6L^2` blue/green vertices and `9L^2` edges. The weight rule is corrected to invariant `K=3E`. The determinant-three paper-normalized quotient is implemented and verified in `wiki/records/r0-paper-supercell-audit.md`; quantitative work remains gated by the matched end-to-end decoder audit.

### R1 — Effective D4 observation model

Status: the local likelihood core, periodic coloured-honeycomb topology, schema-v3 sampler, explicit three-state diagnostic winding policy, and logical-Z-eigenvalue mapping are implemented and verified. Discussion thread 008 is resolved: the primary reproduction starts from an anyon-free ground state, ignores its absolute topological-sector label, and declares any nontrivial winding action a logical error relative to that initial state.

Implement a periodic honeycomb instance generator containing the error set `E`, non-Abelian endpoint syndrome, measured intermediate `e_B/e_G` fusion outcomes, logical sector, and every parity/compatibility constraint used by the paper. Implement the conditioned likelihood independently of the decoders.

Verification:

- normalization and support tests on exhaustively enumerable tori;
- endpoint and fusion-parity identities for every generated observation;
- direct enumeration checks of the closed-form observation likelihood;
- fixed seeds and versioned record schema.

Evidence: `wiki/records/r1-local-likelihood-core-audit.md`.

Periodic topology evidence: `wiki/records/r1-periodic-constraint-generator-audit.md` and `manifests/r1-periodic-constraint-generator-audit.json`.

Sampler evidence: `wiki/records/r1-versioned-sampler-audit.md`.

Winding-policy evidence: `wiki/records/r1-winding-sector-policy-matrix-audit.md`.

Logical-Z mapping evidence: `wiki/records/r1-logical-z-sector-mapping-audit.md`.

Ground-state-relative contract: `wiki/records/r1-ground-state-relative-logical-contract.md`.

### R2 — Published practical decoders

Status: the primitive matching graph, corrected invariant `K=3E` objectives, distinct XOR-residual and Boolean-union homology audits, post-flux DSU accumulator, source-normalized topology, global union-component parity builder, effective blue/green Pauli-Z construction, and bounded second-stage charge MWPM are integrated in one schema-v1 physical-error-to-final-decision record. A 192-record matched truth audit covers both public modes and all applicable stage invariants. Independent exact oracles now certify both MWPM stage objectives on every applicable record in that cohort. The exact A13-A14 parity fixture is reproduced. No LER conclusion is authorized. R3 and R4 remain separate gates before any R5 pilot.

Implement two matched PyMatching paths:

- syndrome-only unit-weight MWPM;
- intrinsically heralded MWPM with `K = 27 L^2` and the published `n_e` rule.

The paper's separate zero-temperature transformed-weight diagnostic must not be presented as the production decoder.

Verification:

- syndrome fidelity and homology tests;
- exact small-graph comparison of PyMatching's negative-weight behavior against enumerated correction chains;
- explicit checks for closed negative cycles and deterministic tie handling.

Evidence: `wiki/records/r2-negative-weight-semantics-audit.md`.

Flux-recovery evidence: `wiki/records/r2-flux-recovery-homology-audit.md`.

Post-flux DSU evidence: `wiki/records/r2-postflux-dsu-a13-audit.md`.

Local-rule matrix evidence: `wiki/records/r2-postflux-local-rule-matrix-audit.md`.

Paper-supercell evidence: `wiki/records/r0-paper-supercell-audit.md`.

Periodic-geometry evidence: `wiki/records/r2-postflux-periodic-geometry-audit.md`.

Second-stage charge-recovery evidence: `wiki/records/r2-second-stage-charge-recovery-audit.md`.

Matched end-to-end evidence: `wiki/records/r2-end-to-end-pipeline-truth-audit.md` and `manifests/r2-end-to-end-pipeline-truth-audit.json`.

#### R2.1 — Source-normalized exhaustive first-stage oracle

Registered question: on the exact paper-`L=2` graph and the matched R2 truth-audit cohort, does each PyMatching flux correction attain the global binary objective minimum, and do all globally optimal corrections agree on the Boolean-union logical decision?

Method: independently solve the GF(2) incidence equations, enumerate the full affine correction space (`2^13=8192` chains per syndrome), and compare both syndrome-only and heralded objectives. For every objective minimizer, classify physical/correction union homology. Use the existing 3 p values, 32 physical seeds, and matched first observations; no new stochastic data are introduced.

Result: every PyMatching objective equals the exhaustive minimum and its correction belongs to the optimal set in 96/96 records per mode. Tied global minima are logically ambiguous in 9 syndrome-only and 5 heralded records, so minimum weight is not promoted to a unique logical or Bayesian oracle. Evidence: `wiki/records/r2-exact-flux-oracle-audit.md` and `.json`.

#### R2.2 — Independent exact charge-stage oracle

Registered question: on every applicable blue/green record in the same matched paper-`L=2` cohort, does unit-weight charge MWPM attain the exact T-join minimum, and can tied optima change charge-residual homology?

Method: enumerate every defect pairing and every shortest path for each pair, combine those paths over GF(2), and retain all globally lightest chains under a one-million-candidate guard. Validate the implementation against complete affine-space enumeration for every even syndrome on an independent bounded graph, then audit all integrated colour records without generating new stochastic data.

Result: all 378 colour objectives are exact and every production correction belongs to the exact minimizing set. The 189 blue and 189 green records are all uniquely minimized; no charge-stage logical tie ambiguity occurs in this cohort. Evidence: `wiki/records/r2-exact-charge-oracle-audit.md` and `.json`. R2 execution-objective validation is complete; R3 fusion-constrained optimization and R4 conditioned posterior inference remain scientifically distinct.

### R3 — Exact constrained MILP oracle

Formulate a bounded-system binary optimization oracle with edge variables, endpoint parity, mandatory compatibility with measured fusion products, and enumerated homology sectors. Validate every solution against exhaustive enumeration before using it beyond tiny graphs.

This is a project extension and must always be labelled as such. It estimates a constrained minimum-weight explanation; it is not automatically Bayes-optimal.

#### R3.0 — Exhaustive fusion-constrained MAP reference

Status: implemented on the primitive 12-edge semantic fixture. The reference enumerates every edge set, enforces flux boundary, degree-two measurement support, candidate-generated fusion parities, the exact Appendix-A likelihood, and a declared Bernoulli prior. Winding candidates requiring an undeclared absolute-sector likelihood fail closed.

Validation fixture: one observation has four compatible explanations. At `p=0.1`, three configuration-MAP modes lie in distinct relative homology sectors; at `p=0.6`, the unique five-edge mode wins. This proves that a MAP configuration is prior-dependent and need not define a unique logical-sector decision. Evidence: `wiki/records/r3-exhaustive-fusion-map-fixture.md` and `.json`.

Next gate: compile the same bounded objective and support conditions into the proposed integer program, enumerate relative homology sectors explicitly, and require exact equality of objective and complete optimizer set against R3.0 before any larger graph is attempted.

#### R3.1 — Finite-support MILP compilation

Status: complete on the registered R3.0 fixture. Four pre-enumerated compatible explanations are represented by binary one-hot selectors, linked exactly to 12 explicit binary edge variables. The linear objective is negative `log2[P(s|E)P(E)]`. Four sector-restricted MILPs expose the optimum in every relative homology sector.

Result: at both `p=0.1` and `p=0.6`, solver objective and the complete optimizer set exactly equal R3.0. The low-p three-sector tie and high-p unique diagonal optimum are preserved. Evidence: `wiki/records/r3-finite-milp-compilation-audit.md` and `.json`.

Claim boundary and next gate: fusion support is still pre-enumerated, so this validates finite solver and sector plumbing rather than a scalable structural MILP. The next bounded transition is to encode boundary, degree/support, and fusion compatibility structurally—without one selector per complete explanation—and require equality against both R3.0 and R3.1 before increasing size.

#### R3.2 — Direct edge-variable structural MILP

Status: complete on the two-fixture bounded matrix. The formulation removes complete-explanation selectors and uses binary physical-edge variables plus vertex parity auxiliaries. Incidence equalities structurally impose flux boundary and exact measurement support. Bounded no-good cuts exclude fusion-incompatible structural chains.

Result: the four-explanation fixture reproduces R3.0/R3.1 globally and by homology sector at both priors. A separate constraint-bearing loop fixture accepts its sampled record and fails closed after one charge flip violates the fusion parity. Evidence: `wiki/records/r3-structural-edge-milp-audit.md` and `.json`.

Claim boundary and next gate: fusion cuts are still enumerated, and the direct linear objective currently requires a constant Appendix-A conditional likelihood over compatible chains. Before increasing size, encode fusion-component activity and candidate constraint count with auxiliary variables, eliminate truth-table no-good compilation, and recover all R3.0–R3.2 fixtures exactly.

#### R3.3 — Component-auxiliary fusion parity and likelihood

Status: complete on the bounded primitive graph. One binary auxiliary is assigned to each of four isolated homologically trivial loop components. Exact AND constraints activate it from selected loop edges and absent external incident edges. Observed parity incompatibility forces the auxiliary off; active auxiliaries contribute the source's two fusion constraints directly to the negative-log objective.

Result: R3.3 reproduces both MAP priors and all four relative-sector optima without fusion no-good cuts. On loop mask 238 it independently recovers `log2 P(s|E)=-4` from six measured internal vertices and two active constraints. Evidence: `wiki/records/r3-component-auxiliary-milp-audit.md` and `.json`.

Claim boundary and next gate: the component catalog is still discovered by bounded loop enumeration, and winding-sector likelihood remains separately censored. Replace catalog discovery with a geometry-derived generator and make winding-sector constraints explicit before any size increase.

#### R3.4 — Geometry-derived loop catalog

Status: complete for bounded cycle length. Simple cycles are generated directly by DFS, deduplicated by edge mask, and source-filtered for one trivial nonbranching component with two colour constraints. The `2^E` component-discovery scan is removed.

Result: the primitive catalog exactly matches all four components found by complete 4096-subset enumeration. On the 36-edge paper-`L=2` graph, a guarded length-six run finds 12 trivial hexagons. Evidence: `wiki/records/r3-geometry-loop-catalog-audit.md` and `.json`.

Winding contract and next gate: thread-008 already requires nontrivial winding actions to terminate as logical failures with no invented sector-dependent charge record. Make that terminal gate explicit in the R3 solver interface and exhaust all primitive winding fixtures; do not assign a winding likelihood or enlarge the optimization graph.

#### R3.5 — Terminal winding-failure interface

Status: complete. The record-level R3 interface routes any nontrivial winding component directly to terminal logical failure and never invokes MAP recovery or invents a sector-conditioned charge likelihood. Only sampled nonwinding records enter R3.3.

Result: all 4096 primitive physical edge sets were audited; all 123 terminal winding records take the terminal branch, while the mask-73 nonwinding control reaches the component-auxiliary solver. Evidence: `wiki/records/r3-terminal-winding-gate-audit.md` and `.json`.

Next gate: with the practical-model R3 interface now continuous and bounded-exact, freeze R3 claims and begin the separately preregistered R4 exact conditioned logical-sector posterior on the same primitive nonwinding observation fixture. Do not reinterpret configuration MAP as sector posterior mass.

### R4 — Exact conditioned XOR-relative sector posterior

For enumerable systems compute

`Z(s,h) = sum_{E in h} P(s | E) P(E)`

for each XOR-relative homology sector `h`. Report Bayes risk for sector 0–1
loss, conditional sector entropy, and the posterior/log-evidence gap. R4.4 later
showed that this sector variable is not sufficient for Appendix A's Boolean-
union first-stage loss, so R4.0–R4.3 are exact intrinsic sector-information
results but are not the practical-stage Bayes oracle.

#### R4.0 — Registered primitive posterior fixture

Status: implemented on the same nonwinding mask-73 observation used by R3. All four compatible explanations are grouped into relative homology sectors and their validated joint probabilities are summed.

Result: at `p=0.1`, three sectors tie at `81/244` posterior mass and Bayes logical failure is `163/244`. At `p=0.6`, the unique configuration-MAP sector has only `3/7` posterior mass and Bayes logical failure is `4/7`. Conditional entropy and evidence gaps are recorded. Evidence: `wiki/records/r4-exact-sector-posterior-fixture.md` and `.json`.

Next gate: validate reference relabeling invariance and run a bounded observation matrix that includes multiple explanations within one sector, so R4 demonstrably sums rather than merely renames individual configurations.

#### R4.1 — Reference invariance and genuine sector sum

Status: complete. All four compatible mask-73 explanations were used in turn as reference chains; posterior probability multisets, Bayes risk, and entropy are invariant.

A second observation has compatible masks 98 and 140 in one relative sector. Its sector log2 evidence exceeds either individual log weight by exactly one bit, proving the implementation sums configuration mass. Evidence: `wiki/records/r4-reference-invariance-sector-sum-audit.md` and `.json`.

Next gate: exhaust the complete distinct-observation set on the primitive graph at a small preregistered prior matrix, report the distribution of sector count, Bayes risk, entropy, and MAP-versus-Bayes disagreement, and keep terminal winding records separate.

#### R4.2 — Complete distinct-observation posterior matrix

**Registered and completed 2026-08-29.** Exhaust all 4096 physical
edge masks on the primitive 12-edge fixture. Keep the 123 expected nontrivial-
winding masks as terminal ground-state-relative failures with no charge record.
For every other mask, enumerate all parity-supported charge assignments,
deduplicate the resulting complete `(flux, charge)` observations, and retain
their full compatible-error support.

The fixed prior matrix is `p={0.1,0.3,0.5,0.6}`: the first and last values
preserve the R3/R4 fixtures, `p=0.3` probes the sparse interior, and `p=0.5`
isolates the conditioned observation likelihood. At every observation and
prior, report candidate and sector counts, conditional logical entropy, Bayes
risk, sector evidence gap, and set-valued configuration-MAP versus sector-Bayes
agreement. Report both unweighted structural distributions and distributions
weighted by observation probability; keep terminal mass separate and also
state the combined ground-state-relative Bayes risk.

Acceptance requires complete mask accounting, per-error observation
normalization, global evidence normalization at every prior, exact recovery of
the R4.0/R4.1 fixtures, independent subset agreement with the existing R4
routine, and zero invented winding likelihoods. The incidence table is capped
at one million candidate-observation pairs. No stochastic sample, larger
lattice, LER estimate, or threshold claim is authorized. Contract:
[`manifests/r4-distinct-observation-matrix-manifest-2026-08-29.json`](manifests/r4-distinct-observation-matrix-manifest-2026-08-29.json).
Registered method:
[`wiki/records/r4-distinct-observation-matrix-method-note-2026-08-29.md`](wiki/records/r4-distinct-observation-matrix-method-note-2026-08-29.md).

The exact enumeration finds 3973 nonwinding masks, 123 terminal winding masks,
16,230 distinct supported observations, and 49,855 candidate-observation pairs.
Both per-error observation normalization and prior-weighted global evidence
normalization pass to machine precision. Mean nonterminal Bayes risk rises from
0.04768 at p=0.1 to 0.53321 at p=0.6. At p=0.6, maximum-weight configurations
and maximum-evidence logical sectors are forced disjoint on 216 observations,
carrying 7.63% of the nonterminal observation probability. This is direct
bounded evidence that configuration MAP cannot replace sector evidence sums.
All R4.0/R4.1 fixtures and three independent exact-posterior comparisons pass;
the full Lab suite passes 98 tests. Evidence:
[`manifests/r4-distinct-observation-matrix-audit.json`](manifests/r4-distinct-observation-matrix-audit.json)
and
[`wiki/records/r4-distinct-observation-matrix-audit.md`](wiki/records/r4-distinct-observation-matrix-audit.md).

#### R4.3 — Matched nonwinding O0–O2 information hierarchy

**Registered and completed 2026-08-29.** Compare O2, the complete
R4.2 `(flux, charge)` record, with O0, its deterministic flux-only
coarse-graining, at the unchanged `p={0.1,0.3,0.5,0.6}` priors. The comparison
is conditioned on the rigorously shared nonwinding channel. Terminal winding
prior mass remains outside both posteriors and is reported separately: it is
ground-truth scoring information, not a decoder-visible symbol, and no O2
winding-charge likelihood has been derived.

For every O0 flux record, sum the sector evidence of all O2 charge refinements.
Report matched nonwinding-conditioned Bayes risk and logical-sector entropy,
their O0-minus-O2 differences, and verify the registered data-processing
inequalities. The entropy reduction is the conditional mutual information
provided by fusion charge given flux on this bounded channel. Acceptance also
requires exact per-flux, per-sector evidence conservation, total nonwinding
mass conservation, posterior normalization, R4.2 aggregate recovery, and
source-hash agreement. No stochastic sample, larger lattice, LER, or full-
physical-channel claim is authorized. Contract:
[`manifests/r4-nonwinding-information-hierarchy-manifest-2026-08-29.json`](manifests/r4-nonwinding-information-hierarchy-manifest-2026-08-29.json).
Registered method:
[`wiki/records/r4-nonwinding-information-hierarchy-method-note-2026-08-29.md`](wiki/records/r4-nonwinding-information-hierarchy-method-note-2026-08-29.md).

The 16,230 O2 observations coarse-grain to 128 O0 flux records. Fusion charge
strictly lowers both optimal logical risk and conditional logical entropy at
all four priors. The Bayes-risk reduction is 0.08780, 0.33421, 0.26479, and
0.19769 for increasing p; the corresponding conditional mutual information is
0.33368, 1.38930, 1.12246, and 0.89802 bits. The largest sector-evidence,
total-mass, or R4.2-recovery discrepancy is `7.1e-14`; both registered data-
processing inequalities pass. Evidence:
[`manifests/r4-nonwinding-information-hierarchy-audit.json`](manifests/r4-nonwinding-information-hierarchy-audit.json)
and
[`wiki/records/r4-nonwinding-information-hierarchy-audit.md`](wiki/records/r4-nonwinding-information-hierarchy-audit.md).

#### R4.4 — First-stage loss bridge and matched excess Bayes risk

**Registered and completed 2026-08-29.** A direct full-pipeline
comparison is not yet valid: the practical decoder receives a second adaptive
post-flux charge record that is absent from the R4.2 O2 posterior. Even at the
first stage, R4 groups XOR-relative homology sectors while Appendix A scores
the Boolean physical/correction union. R4.4 therefore verifies this loss bridge
before interpreting an algorithmic gap.

On the complete primitive nonwinding support, exhaust all syndrome-faithful
corrections (expected 32 per flux). Directly minimize posterior expected
Boolean-union failure at O0 and O2, compare those exact risks with unit-weight
and published herald-weight first-stage MWPM respectively, and decompose exact
information gain from O0/O2 algorithmic excess risk. Independently test whether
R4 XOR sectors are sufficient for the complete correction-action loss vector;
report equality with direct union-loss Bayes risk rather than assuming it.

Acceptance requires complete unique action sets, syndrome fidelity, public-
action membership, observation-only decoder inputs, O2-to-O0 evidence
conservation, posterior normalization, and exact risk no greater than matched
production risk. No adaptive second measurement, stochastic sample, larger
lattice, LER, or threshold claim is authorized. Contract:
[`manifests/r4-first-stage-loss-bridge-manifest-2026-08-29.json`](manifests/r4-first-stage-loss-bridge-manifest-2026-08-29.json).
Registered method:
[`wiki/records/r4-first-stage-loss-bridge-method-note-2026-08-29.md`](wiki/records/r4-first-stage-loss-bridge-method-note-2026-08-29.md).

All 128 O0 and 16,230 O2 observations were evaluated against all 32 corrections
per syndrome, for 127,136 candidate-action evaluations. XOR sectors fail the
complete union-loss sufficiency test on 128/128 O0 observations and 2,485/
16,230 O2 observations, with a maximum single-observation risk gap of one.
Thus R4.0–R4.3 remain correct for the declared XOR-sector variable, but direct
posterior expected union loss is the required practical-stage oracle.

Exact O2 union-loss risk is lower than exact O0 at every prior by 0.08810,
0.31959, 0.19431, and 0.09086, so fusion charge still supplies operational
first-stage information. The published herald-weight rule has excess risk
0.04840, 0.21582, 0.17905, and 0.11684; unit-weight O0 excess is at most
0.01768. At p=0.6 the heralded first-stage rule is worse than the unit-weight
rule despite O2's strictly better exact limit, directly separating information
gain from heuristic quality. All normalization, action, membership, source,
and lower-bound gates pass. Evidence:
[`manifests/r4-first-stage-loss-bridge-audit.json`](manifests/r4-first-stage-loss-bridge-audit.json)
and
[`wiki/records/r4-first-stage-loss-bridge-audit.md`](wiki/records/r4-first-stage-loss-bridge-audit.md).

Next gate: before R5 or a full optimality claim, register a bounded sequential
model for the adaptive second post-flux observation. It must derive that
action-dependent likelihood and distinguish a fixed practical policy from an
exact policy that anticipates future information.

#### R4.5 — Sequential post-flux observation and policy value

**Registered 2026-08-29; preflight failed before policy computation.** The first correction
is an intervention as well as a recovery: together with the hidden physical
error it determines immediate Boolean-union failure and, on surviving
branches, the parity support of the second e-charge record. The full exact
comparator must therefore optimize a policy rather than reuse the isolated
R4.4 first-stage minimizer.

For a nonterminal hidden `(E,A)` branch with `N` active stars and `C`
independent even-parity components, register
`P(Y=y|E,A)=2^(C-N)` on the allowed affine support and zero elsewhere. The
decoder-visible `Y` is a full binary star record with zero outside the active
support. Internal `-1` sentinels, the active mask, relation components,
physical truth, and effective-Z representatives are forbidden from decoder
keys.

At each O0/O2 layer, compare the public two-stage policy, public first action
with exact continuation, the R4.4 myopic first action with exact continuation,
and the future-aware exact policy. The second action is the complete `4 x 4`
pair of blue/green charge-correction homology classes, verified against
exhaustive affine charge chains. Report exact O0/O2 final risk, public excess,
first-stage and second-stage gap decomposition, myopia cost, and the mass on
which first actions differ.

Acceptance requires exact second-channel normalization, conservation through
immediate and continued branches, complete first and second action spaces,
observation-only policies, public-action membership, and the registered risk
orderings. A hidden-active/relation-aware policy is allowed only as a labeled
leak sensitivity bound. Preflight must remain below 120 million streamed
transition contributions, 30 projected minutes, and 4 GiB. Contract:
[`manifests/r4-sequential-postflux-policy-manifest-2026-08-29.json`](manifests/r4-sequential-postflux-policy-manifest-2026-08-29.json).
Registered method:
[`wiki/records/r4-sequential-postflux-policy-method-note-2026-08-29.md`](wiki/records/r4-sequential-postflux-policy-method-note-2026-08-29.md).

The likelihood and resource gates passed: 127,136 hidden `(E,A)` pairs reduce
to 2,320,936 streamed second-record contributions, every second channel
normalizes exactly, and the conservative four-prior projection remains under
the 30-minute/4-GiB contract. The exact charge-action gate does not pass. For
each colour on the primitive R4 torus, twelve physical triangular edges
collapse to six endpoint pairs, and every pair has two distinct periodic
displacements. The current post-flux relation object retains only endpoints;
the production charge lattice correctly rejects this parallel-edge
degeneracy. Consequently the sixteen joint homology actions and public second
MWPM are undefined on this primitive topology.

No sequential risk was computed. Before re-registering the policy matrix,
R4.5a must derive a branch-labelled primitive charge multigraph, retain
relation-to-edge provenance, and verify boundary and homology against explicit
periodic fixtures. Evidence:
[`manifests/r4-sequential-postflux-policy-preflight.json`](manifests/r4-sequential-postflux-policy-preflight.json)
and
[`wiki/records/r4-sequential-postflux-policy-preflight.md`](wiki/records/r4-sequential-postflux-policy-preflight.md).

#### R4.5a — Branch-labelled primitive charge topology remediation

**Registered and provenance-preflight passed 2026-08-29; no policy risk computed.** Preserve all twelve physical triangular edges per charge colour as a multigraph. A branch is identified by a stable edge id, its charge endpoints, the opposite-colour centre of the two-step path, and its primitive periodic displacement. Infer post-flux relation provenance from the actual union paths; endpoint pairs are only the branch-forgetting projection and must never select a branch.

The smallest discriminating audit first catalogs both colours and then streams all 127,136 primitive `(E,A)` pairs. It requires each relation to map to exactly one physical branch while forgetting labels reproduces the existing DSU parity partition. It then checks every parallel pair has equal boundary but distinct displacement, that the branch XOR closes with the expected relative winding, and that exhaustive affine chains quotient to exactly four homology classes per colour. Public PyMatching branch fidelity is a separate required gate because duplicate incidence columns need not imply distinct decoder fault identities.

Fail closed before the homology quotient if any relation has zero or multiple branch provenance; fail closed before a public second-stage claim if PyMatching collapses branches. Do not switch to the larger paper-normalized lattice, choose an arbitrary branch, or replace the exact primitive posterior with an approximation. Those alternatives change the model or erase winding rather than repair it. No new samples or lattice sizes are authorized; the audit is bounded by 127,136 provenance pairs, five million checks, ten minutes, and 2 GiB. Contract: [`manifests/r4-branch-labelled-charge-topology-manifest-2026-08-29.json`](manifests/r4-branch-labelled-charge-topology-manifest-2026-08-29.json). Method: [`wiki/records/r4-branch-labelled-charge-topology-method-note-2026-08-29.md`](wiki/records/r4-branch-labelled-charge-topology-method-note-2026-08-29.md).

The prerequisite preflight classified all 127,136 pairs and audited all 6,816 nonterminal pairs. Both colours contain twelve stable branches over six endpoint pairs, with no duplicate provenance labels. The 48,000 projected relation occurrences each map to exactly one physical branch, and forgetting labels recovers the old endpoint relation set and DSU partition with zero failures.

The winding and quotient gate also passes. All twelve parallel-pair fixtures close with the expected relative winding. For each colour, all 512 closed branch chains split into four equal GF(2) homology sectors of 128; every one of eight even syndromes has four action classes of 128, with zero within-class loss failures across 2,097,152 comparisons. The linear period-cochain oracle agrees with the legacy lift on all 90 cycle-like closed chains. It also exposes why the first attempted aggregation failed: the older component-level Boolean classifier disagrees on 107 branched/multicycle chains per colour and is not a linear homology map. That failed output is preserved explicitly. Public PyMatching branch fidelity remains deliberately unrun. Evidence: [`manifests/r4-branch-labelled-charge-topology-audit.json`](manifests/r4-branch-labelled-charge-topology-audit.json), [`wiki/records/r4-branch-labelled-charge-topology-audit.md`](wiki/records/r4-branch-labelled-charge-topology-audit.md), and [`manifests/r4-branch-labelled-charge-homology-failed-component-classifier-2026-08-29.json`](manifests/r4-branch-labelled-charge-homology-failed-component-classifier-2026-08-29.json).

The public PyMatching branch-fidelity matrix fails topology preservation while passing its numerical oracle. Across both colours, thirteen positive-weight profiles, and all eight even syndromes, all 208 returned objectives, boundaries, primitive minimizer memberships, and targeted cheap-branch identities are correct. Nevertheless each matching object has six edges rather than twelve and never retains both physical fault ids of a parallel pair simultaneously. Evidence: [`manifests/r4-public-decoder-branch-fidelity-audit.json`](manifests/r4-public-decoder-branch-fidelity-audit.json) and [`wiki/records/r4-public-decoder-branch-fidelity-audit.md`](wiki/records/r4-public-decoder-branch-fidelity-audit.md).

#### R4.5b — Private-auxiliary expanded branch MWPM

**Registered, implemented, and exhaustively verified 2026-08-29.** Replace each physical branch `(u,v)` with a private two-edge path `u-a_e-v`, where auxiliary detector `a_e` has deterministic zero syndrome. Split the physical branch weight equally across the two segments and attach its fault id to exactly one segment. Zero parity at the degree-two auxiliary forces a valid correction to select the whole branch or neither half, retaining the original boundary, total weight, and one physical branch id without parallel matching edges.

Validate one sixteen-node, twenty-four-edge, twelve-fault-id graph per colour against exhaustive primitive chains for the same thirteen profiles and eight even syndromes. Require exact objective agreement, minimum-chain membership, branch boundary, targeted parallel identity, and period-cochain sector. Stop before sequential-policy integration on any half-branch, missing id, objective mismatch, or non-minimizer. Contract: [`manifests/r4-expanded-branch-mwpm-adapter-manifest-2026-08-29.json`](manifests/r4-expanded-branch-mwpm-adapter-manifest-2026-08-29.json).

Both colour graphs pass all 208 registered cases. Every graph has sixteen nodes, twenty-four distinct edges, and all twelve fault ids; every private auxiliary has degree two and zero syndrome; no decoded solution contains a half branch. Exact objectives, physical boundaries, exhaustive minimizer membership, targeted parallel branch selection, and period-cochain sectors have zero failures. Maximum PyMatching/exhaustive objective discrepancy is `7.64e-7`, below the registered `1e-6` tolerance. Evidence: [`manifests/r4-expanded-branch-mwpm-adapter-audit.json`](manifests/r4-expanded-branch-mwpm-adapter-audit.json) and [`wiki/records/r4-expanded-branch-mwpm-adapter-audit.md`](wiki/records/r4-expanded-branch-mwpm-adapter-audit.md).

Next gate: re-register the R4.5 sequential policy computation against the corrected branch-labelled relation object, linear four-sector quotient, and expanded public charge decoder. The failed R4.5 source freeze must not be silently reused.

#### R4.5c — Corrected branch-resolved sequential policy

**Registered, corrected preflight passed, and final exact audit completed 2026-08-29.** Preserve the R4.5 scientific question and policy matrix, but replace every invalid representation layer with its verified branch-resolved counterpart. Post-flux relations retain actual-path branch ids; exact homology uses the linear period cochain; public unit-weight charge recovery uses the private-auxiliary expanded PyMatching graph; and exact second actions use the four equal affine homology classes per colour.

Before risk, prove that the deterministic effective-error representative cannot choose a logical sector. For every nonterminal `(E,A)` branch and colour, form the relation-subgraph incidence map `H_rel` and period cochain `W_rel`, and require `W_rel c = 0` for every `c` in `ker(H_rel)`. Also require every constructed representative to have exactly the supported measured boundary `Y`. Any nontrivial relation-cycle winding or boundary mismatch censors the complete policy result.

The corrected preflight must reproduce the original channel normalization, anti-leak boundary, terminal/nonterminal counts, and 2,320,936 streamed contributions; verify unique branch provenance and endpoint projection; re-establish the four-sector quotient; and check expanded public corrections against exhaustive affine chains. Only then may a later tick compute the public fixed, public-first/exact-continuation, myopic-first/exact-continuation, and future-aware exact risks at O0 and O2. No new stochastic samples, lattice sizes, noisy-record model, LER, threshold, or scalability claim is authorized. Contract: [`manifests/r4-corrected-sequential-policy-manifest-2026-08-29.json`](manifests/r4-corrected-sequential-policy-manifest-2026-08-29.json). Method: [`wiki/records/r4-corrected-sequential-policy-method-note-2026-08-29.md`](wiki/records/r4-corrected-sequential-policy-method-note-2026-08-29.md).

All corrected gates pass. The scan exactly reproduces 127,136 hidden pairs, 120,320 terminal pairs, 6,816 nonterminal pairs, and 2,320,936 streamed contributions. Across 322 distinct colour/relation signatures, all 458 closed kernel chains have zero period-cochain sector. All 514,040 colour-resolved supported-record representatives have the requested boundary and belong to the exhaustive affine action set. Both colours retain four sectors of 128 actions for all eight even syndromes, while expanded public boundary, membership, sector, and objective failures are all zero.

The first wall projection is preserved as a failed accounting attempt: it multiplied the complete one-time representative precompute by observation multiplicity and four priors, yielding 2176.8 seconds. The registered cache-aware amendment adds the measured one-time corrected precompute to the source-frozen R4.5 four-prior streaming projection, yielding 1196.9 seconds under the unchanged 1800-second guard. Evidence: [`manifests/r4-corrected-sequential-policy-preflight.json`](manifests/r4-corrected-sequential-policy-preflight.json), [`wiki/records/r4-corrected-sequential-policy-preflight.md`](wiki/records/r4-corrected-sequential-policy-preflight.md), and the preserved failed projection [`manifests/r4-corrected-sequential-policy-preflight-failed-overcounted-resource-projection-2026-08-29.json`](manifests/r4-corrected-sequential-policy-preflight-failed-overcounted-resource-projection-2026-08-29.json).

The final audit evaluates 8,564,264 observable-history/action aggregations at `p={0.1,0.3,0.5,0.6}`. Every channel, mass-conservation, O2-to-O0 marginalization, information-ordering, and policy-ordering gate passes; maximum global normalization error is `6.44e-14`. Exact O2 sequential risk is lower than exact O0 by 0.08848, 0.33047, 0.22301, and 0.11788 on the nonwinding channel.

The public O2 full-policy excess is 0.08269, 0.33726, 0.25431, and 0.14980. In every prior, the public first-action excess after exact continuation exceeds the second-stage MWPM excess, so the herald-weight first action—not unit-weight charge MWPM—is the dominant primitive public-policy gap. By contrast, the future-aware advantage over the R4.4 myopic first action is zero at p=0.1, 0.3, and 0.6 and only 0.000975 at p=0.5 for O2; it is at most 0.001550 for O0. Thus this primitive channel strongly supports fusion-information value and first-stage algorithmic deficiency, but gives little evidence for a large active information-gathering effect.

Evidence: [`manifests/r4-corrected-sequential-policy-audit.json`](manifests/r4-corrected-sequential-policy-audit.json) and [`wiki/records/r4-corrected-sequential-policy-audit.md`](wiki/records/r4-corrected-sequential-policy-audit.md). The result remains exact only for the primitive noiseless L=2 channel; it is not an LER, threshold, larger-lattice, noisy-measurement, or scalable-optimality result.

### R5 — Bounded reproduction pilot

Only after R1–R4 gates pass, run a small preregistered pilot around the paper's reported unheralded and heralded transition regions. Use matched seeds and report binomial uncertainty, decoder failures, and runtime. The pilot decides whether a publication-scale sweep is justified.

#### R5a — Matched paper-lattice public-decoder transfer pilot

Status: **retrospectively withdrawn for complete-pipeline use by R6AH**. The
physical draws and lattice records remain provenance only.

R4.5c changes the purpose of the first larger-lattice experiment. The next
question is not to estimate a threshold, but to test whether the exact
primitive fusion-information advantage and the first-action-dominated public
gap transfer at all to paper-normalized lattices. The smallest discriminating
matrix uses paper `L={2,3}`, `p={0.14,0.16,0.18,0.20,0.22}`, and 2,000 matched
seeded trajectories per `(L,p)`. Syndrome-only and published heralded MWPM
share the same physical error and initial fusion record; their action-dependent
second records remain distinct and are generated by fixed seed streams.

The primary output is a finite-size logical-risk and paired-difference table
with two-sided 90% intervals and stage-resolved failure counts. A cell is called
directional only when the paired interval excludes zero. No crossing,
threshold, phase label, or extrapolation is fitted. A 200-history preflight
must first verify source hashes, paper topology, matched initial records,
syndrome/support invariants, observation-only decisions, exhaustive status
accounting, and a production projection below 30 minutes and 4 GiB. `L=4`,
adaptive refinement, and publication-scale sampling require a new contract.

This pilot precedes exporting a D4 inner decoder to Lab 005 because it tests
whether the public spatial policy is a meaningful baseline beyond the exact
primitive. Lab 005's source-matched D(S3) JIT schedule remains independent and
need not wait. Contract:
[`manifests/r5a-paper-lattice-public-decoder-pilot-manifest-2026-08-29.json`](manifests/r5a-paper-lattice-public-decoder-pilot-manifest-2026-08-29.json).

The manifest-driven preflight and production runners plus the frozen paired
analyzer are implemented. The preflight executes all 200 registered histories
and 400 public decoder evaluations with zero failures. Paper `L=2,3` topology,
source hashes, shared initial records, syndrome fidelity, post-flux support,
charge residual closure, stage-status accounting, and observation-boundary
proxies all pass. The 1.741-second measurement projects production to 174.1
seconds, with 0.081 GiB peak RSS; both are below their registered guards.
Evidence:
[`results/r5a-paper-lattice-public-decoder-preflight.json`](results/r5a-paper-lattice-public-decoder-preflight.json)
and
[`wiki/records/r5a-paper-lattice-public-decoder-preflight.md`](wiki/records/r5a-paper-lattice-public-decoder-preflight.md).

Production and the corrected preregistered analysis are complete. All ten
`(L,p)` cells favor the heralded public policy: paired risk differences range
from `-0.1050` to `-0.2680`, and every two-sided 90% interval excludes zero.
For the heralded policy, `L=3-L=2` risk is negative through `p=0.20` and
unresolved at `p=0.22`. Syndrome-only risk decreases at `p=0.14`, is unresolved
at `p=0.16`, and increases at `p=0.18,0.20,0.22`. These are finite-size
directions only. Stage counts show the heralded advantage is dominated by
fewer first-stage Boolean-union winding failures. No terminal physical winding
occurs in the cohort.

A pre-promotion completeness audit corrected the analyzer's omission of the
registered size-difference and terminal-winding sensitivity outputs. The raw
40,000 records, grid, sample count, confidence level, and decision rules were
unchanged; size cohorts are correctly resampled independently because their
physical seed streams differ. Evidence (the raw cohort was checksum-validated
and compacted after analysis):
[`results/r5a-paper-lattice-public-decoder-sufficient-statistics.json`](results/r5a-paper-lattice-public-decoder-sufficient-statistics.json),
[`results/r5a-paper-lattice-public-decoder-analysis.json`](results/r5a-paper-lattice-public-decoder-analysis.json),
and
[`wiki/records/r5a-paper-lattice-public-decoder-analysis.md`](wiki/records/r5a-paper-lattice-public-decoder-analysis.md).

R6AH later inspected all 40,000 stored arm records and found that the first
record exposes inactive `-1` support, every stored second record carries the
same sentinel convention, and the legacy charge action/scoring boundary
couples private relations and effective-error truth. R5a also lacks the
remediated anti-leak, wrong-action binding, public-transcript, and replay gates.
Accordingly, the numerical risks, paired differences, size directions, stage
mechanism, and Lab 005 baseline promotion above are historical outputs, not
evidence for the corrected complete public pipeline. See R6AH below.

### R6 — Matched Lab 002 comparison

Adapt belief matching to the validated D4 record without changing the observation channel. Compare syndrome-only MWPM, published heralded MWPM, belief matching, MILP, and the exact logical posterior where tractable.

#### R6A — Public D4 likelihood factorization gate

**Registered and complete-matrix verified 2026-08-29; bounded interpretation pending.** The current Lab 002 binary
degree-threshold herald factor is not a D4 likelihood adapter. Before any BP or
logical comparison, test whether the validated public D4 observation likelihood
has an exact truth-free factor graph on the complete primitive-size-2 support.
This exhaustive control has 8 vertices and 12 edges; it is not the
paper-normalized `L=2` supercell with 24 vertices and 36 edges.

Run F0 exact-oracle control, F1 local flux/degree support, and F2 support plus
explicit public parity auxiliaries in one deterministic matrix. Require exact
zero support, conditional weights within (10^{-14}), posterior normalization
at the four R4.2 priors, marginalized O2/O0 evidence agreement, and hidden-field
rejection. All branches are cheap and reversible, so their order is not a human
decision. Stop before BP, PyMatching, timing, or logical sampling if no exact
public candidate passes. Contract:
[`manifests/r6a-d4-belief-factorization-manifest-2026-08-29.json`](manifests/r6a-d4-belief-factorization-manifest-2026-08-29.json).

The public-input factor-ledger implementation, exact fixtures, and complete
primitive-size-2 matrix now pass their registered numerical gates.
Vacuum, open path, and branched records agree in F1/F2/oracle. A six-internal-
vertex trivial loop gives F1 weight (1/64) but F2 and the oracle (1/16),
and flipping one parity bit leaves F1 positive while F2/oracle become zero.
Winding is terminal and truth-bearing public fields fail closed. This verifies
the necessity and value of the registered parity factors, but the current F2
scope is derived while evaluating a latent candidate and is diagnostic-only.
Across all 16,230 supported public observations and 49,855 compatible
observation/error pairs, F0 replays the frozen digest, F1 has exact support but
64 conditional-weight errors (all smaller by a factor four), and F2 has zero
likelihood errors. Moreover, every public observation has at most one parity-
scope signature across its compatible candidates. This proves finite-support
scope consistency on the 8-vertex, 12-edge primitive fixture, not on
paper-normalized `L=2`, and not a scalable construction. The next gate must
derive the scopes from the fixed lattice and public record and validate them on
bounded paper-normalized geometry without exhaustive `2^36` enumeration. BP
remains blocked until that representation is explicit. Evidence:
[`wiki/records/r6a-d4-belief-factorization-fixture-2026-08-29.md`](wiki/records/r6a-d4-belief-factorization-fixture-2026-08-29.md).
Complete matrix:
[`wiki/records/r6a-d4-belief-factorization-audit.md`](wiki/records/r6a-d4-belief-factorization-audit.md).

#### R6B — Paper-normalized public-scope identifiability

**Registered and reported 2026-08-29.** After correcting the primitive/paper
scale label, R6B asks the narrower constructive prerequisite: on the actual
24-vertex, 36-edge paper-normalized `L=2` graph, does the public flux plus
measured-charge-support record uniquely determine one direct charge-parity
scope signature?

An exact degree-CSP enumerator tests 1,000 fresh-seed distinct nonwinding public
records across `p={0.05,0.10,0.20,0.35,0.50}` and all 12 isolated-hex positive
controls. Every record is fully enumerated below the 100,000-assignment cap.
Nine records have two compatible nonwinding scope signatures, while all twelve
controls pass. Therefore a single direct parity-scope list derived only from
the public observation is rejected on paper-normalized geometry. This does not
reject a fixed exact graph whose factors include latent edge or connectivity
variables; deriving that richer representation is the next gate. Contract:
[`manifests/r6b-paper-scope-identifiability-manifest-2026-08-29.json`](manifests/r6b-paper-scope-identifiability-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6b-paper-scope-identifiability-audit.md`](wiki/records/r6b-paper-scope-identifiability-audit.md).

#### R6C — Fixed cycle-activation factor control

**Registered and reported 2026-08-29.** R6C replaces the rejected
observation-only scope preprocessing with fixed geometry factors. For every
homologically trivial simple cycle and charge colour, one factor contains the
latent cycle edges, all boundary edges incident to the cycle, and the public
charge bits. It contributes one when inactive, two when active with even
parity, and zero when active with odd parity. Candidate component labels are
not decoder inputs.

This graph reproduces all 49,855 primitive compatible likelihoods and all 120
even/parity-violation probes from the nine paper-`L=2` ambiguity records with
zero error. It is an exact finite-graph representation, but not yet scalable:
the primitive catalog has 4 cycles whereas paper-`L=2` already has 1,068, with
edge scopes up to all 36 edges and per-colour charge scopes up to 11 vertices.
The next gate is a local connectivity-auxiliary compression that must preserve
the same exact likelihood without enumerating every simple cycle. Contract:
[`manifests/r6c-fixed-cycle-factor-manifest-2026-08-29.json`](manifests/r6c-fixed-cycle-factor-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6c-fixed-cycle-factor-audit.md`](wiki/records/r6c-fixed-cycle-factor-audit.md).

#### R6D — Bounded local auxiliary-spin compression

**Registered and reported 2026-08-29.** R6D replaces the simple-cycle catalog
with two binary auxiliary edge-flow variables per physical edge, one for each
charge colour. Unselected edges pin their flow to zero. At a degree-two vertex,
the two selected flows have XOR equal to the observed same-colour charge; other
vertices contribute the nonnegative normalization `2^{-d/2}`. Cutting a
non-cycle component at degree-not-two vertices produces chains whose two flow
assignments cancel their endpoint normalization, so they contribute one. A
pure loop has two assignments for even parity and zero for odd parity. The two
colour sums reproduce the D4 loop multiplier four without identifying or
enumerating the loop.

The analytic contraction has zero error on all 49,855 primitive likelihoods
and all 120 registered paper-`L=2` ambiguity probes. Sixty-nine independent
small-graph checks explicitly sum all 4,096 nonnegative edge-flow assignments
per colour and also have zero error. The earlier 256-state vertex-spin sum is
an exact signed Fourier control, not the probability representation.
Paper-`L=2` now requires 72 binary edge-flow auxiliaries and 120 bounded-arity
nonnegative factors, growing as `O(V+E)`, rather than 1,068 simple-cycle
factors. This releases implementation of exact BP message updates as the next
gate, but the ground-state-relative winding test remains a separate nonlocal
terminal branch and no convergence, runtime, correction, LER, threshold, or
fault-tolerance result exists yet. Contract:
[`manifests/r6d-local-spin-factor-manifest-2026-08-29.json`](manifests/r6d-local-spin-factor-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6d-local-spin-factor-audit.md`](wiki/records/r6d-local-spin-factor-audit.md).
Proof note:
[`wiki/records/r6d-local-edge-flow-method-note-2026-08-29.md`](wiki/records/r6d-local-edge-flow-method-note-2026-08-29.md).

#### R6E — Exact messages and small-loopy marginal gate

**Registered and reported 2026-08-29.** R6E implements exact table-based
sum-product messages for every nonnegative R6D factor, then separates message
arithmetic from loopy-graph approximation. Both raw synchronous updates and
the Lab 002 probability-space damping value `0.25` reproduce brute-force
factor-tree marginals; the largest tree error is `2.853e-11`. On a single
factor cycle, both converge but retain maximum marginal error `1.277e-2`,
confirming that convergence alone is not exactness.

The primitive D4 matrix covers four deterministic observation strata, two
physical error rates, local-only versus finite terminal-screened graphs, and
both schedules. Raw synchronous BP converges on `0/16` rows and six rows abort
with a zero-probability hard-constraint message. Damped BP converges on `10/16`
rows, but none of the 32 total rows both converges and matches exact physical-
edge marginals within `1e-8`; the largest error among converged rows is `0.5`.
Thus R6D remains an exact likelihood representation, while ordinary loopy BP
on this factorization is rejected as an exact posterior solver. Correction and
LER sampling remain blocked. Contract:
[`manifests/r6e-bp-marginal-gate-manifest-2026-08-29.json`](manifests/r6e-bp-marginal-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6e-bp-marginal-gate.md`](wiki/records/r6e-bp-marginal-gate.md).

#### R6F — Exact-preserving structural inference matrix

**Registered and reported 2026-08-29.** R6F does not tune the rejected R6E
fixed point. It compares three matched representations on the same 32
primitive rows: the frozen unclustered R6E graph; an exact nonnegative bounded
superfactor graph that merges both colour pins on each edge and all three
local factors at each vertex; and a deliberately non-scalable single
12-edge physical-likelihood factor obtained by exactly eliminating every flow
auxiliary.

Both new representations pass their identity gates with zero table error. The
global physical factor is a tree and converges to the exact posterior on
`32/32` rows. Bounded clustering reduces hard-message failures from six to two
and reduces the median maximum error among converged rows from `0.5` to
`9.146e-3`, showing that redundant local factor splitting was a real source of
pathology. It nevertheless converges on only `8/32` rows and reaches the
`1e-8` exact-marginal gate on `0/32`. This particular bounded clustering is
therefore rejected as an exact posterior solver. The next bounded gate is a
structural region/junction or elimination-width study, not more damping and
not correction or LER sampling. Contract:
[`manifests/r6f-structural-inference-matrix-manifest-2026-08-29.json`](manifests/r6f-structural-inference-matrix-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6f-structural-inference-matrix.md`](wiki/records/r6f-structural-inference-matrix.md).

#### R6G — Exact elimination-width and junction feasibility gate

**Registered and reported 2026-08-29.** R6G follows the exact-inference
literature rather than assuming that fewer factors imply easier inference.
For both the unclustered R6D graph and the R6F superfactor graph, it completes
the factor scopes into a primal interaction graph and measures three
prospectively fixed min-fill orders: auxiliary-first, physical-first, and
global. The matrix covers the 12-edge primitive fixture and paper-normalized
`L=2`. Reported induced widths are deterministic upper bounds for these
orders—not proofs of optimal treewidth.

On the primitive graph, the smallest maximum cluster has 16 binary variables
and comes from the unclustered auxiliary-first order. Four of six branches fit
the registered cap of 20 and their exact bucket partitions agree with the
independent 4,096-mask evidence to relative error at most `1.780e-15`; the two
physical-first branches are censored before allocating a 28-variable table.
On paper-`L=2`, global min-fill is best for both representations but still
requires 36 variables in the largest cluster, or `2^36` entries for one dense
binary table. Every other order requires 44 to 80 variables.

H1 is rejected: superfactor compression never lowers maximum cluster size in
the registered matrix, even though it reduces factor count and sometimes fill
edges. H2 is geometry-dependent: global min-fill is best at paper-`L=2`, but
not on the primitive graph. H3 is supported: every paper-`L=2` branch exceeds
the numeric cap. The next gate must compare controlled region/cutset/tensor
approximations against exact primitive marginals; naive dense junction-tree,
more damping, correction, and LER sampling remain blocked. Contract:
[`manifests/r6g-elimination-width-gate-manifest-2026-08-29.json`](manifests/r6g-elimination-width-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6g-elimination-width-gate.md`](wiki/records/r6g-elimination-width-gate.md).

#### R6H — Cutset-conditioning exact time-space gate

**Registered and reported 2026-08-29.** R6H follows exact hybrid
conditioning/elimination before choosing an approximate region method. It
compares physical-only, auxiliary-only, and unrestricted cutsets. All 18
primitive controls (`k=0,2,4`) enumerate every assignment and reconstruct the
independent evidence with maximum relative error `1.780e-15`.

At paper-`L=2`, unclustered auxiliary-only reaches the 20-variable memory cap
at `k=12`, versus unrestricted `k=18` and physical-only `k=24`. On the
superfactor graph, auxiliary-only and unrestricted cross at `k=13`, while
physical-only does not cross through `k=24`. The crossing `k+cluster` proxy
remains 32--44: exact conditioning trades memory for branching rather than
removing exponential complexity. Contract:
[`manifests/r6h-cutset-conditioning-gate-manifest-2026-08-29.json`](manifests/r6h-cutset-conditioning-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6h-cutset-conditioning-gate.md`](wiki/records/r6h-cutset-conditioning-gate.md).

#### R6I — Mini-bucket bounded-approximation gate

**Registered and reported 2026-08-29.** R6I implements the lowest-cost
literature-grounded approximation that reuses the verified bucket engine.
Each bucket is split so no created scope exceeds `i`; the complete matrix
crosses both exact representations, global/auxiliary-first orders, and
`i=10,14,18,20` on one exact-reference primitive observation and paper-`L=2`.

All seven rows whose `i` reaches the registered exact cluster reproduce exact
evidence and physical marginals to `1.998e-15` and `1.110e-16`. Evidence upper
bounds tighten monotonically, but marginal accuracy does not: the
superfactor/global maximum error worsens from `0.090` at `i=10` to `0.126` at
`i=14`. Conversely, auxiliary-first pseudo-marginals cancel to the exact value
on this one primitive observation despite evidence bounds being 16--65,536
times loose. Paper-`L=2` retains 6.623 decades of cross-branch bound spread at
`i=20`. Thus mini-bucket is verified as a controlled baseline but not selected
as a decoder. A multi-observation exact-reference validation is required
before deciding whether GBP or tensor structure earns implementation cost.
Contract:
[`manifests/r6i-mini-bucket-approximation-gate-manifest-2026-08-29.json`](manifests/r6i-mini-bucket-approximation-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6i-mini-bucket-approximation-gate.md`](wiki/records/r6i-mini-bucket-approximation-gate.md).

#### R6J — Multi-observation mini-bucket validation

**Registered and reported 2026-08-29.** R6J expands the exact-reference cohort
without changing the approximation: four registered observation strata,
`p=0.10,0.30`, two exact representations, two orders, and four `i` values form
128 deterministic rows. All 56 exact-ceiling rows pass with evidence-ratio
error at most `1.998e-15` and marginal error at most `2.220e-16`.

The favorable R6I cancellation is not robust. Auxiliary-first low-`i`
cancellation occurs in `20/32` rows, and no representation/order branch at
`i<=14` meets the `0.01` maximum-marginal-error gate on all eight conditions.
Moreover, the registered greedy partitions are not nested as `i` changes:
three of 32 condition/representation/order sequences have nonmonotone evidence
bounds and 14 have nonmonotone marginal error. Mini-bucket remains a useful
negative baseline, but the next experiment must compare richer or explicitly
nested partition/region constructions against the same exact cohort; no
correction or LER sampling is licensed. Contract:
[`manifests/r6j-multi-observation-mini-bucket-validation-manifest-2026-08-29.json`](manifests/r6j-multi-observation-mini-bucket-validation-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6j-multi-observation-mini-bucket-validation.md`](wiki/records/r6j-multi-observation-mini-bucket-validation.md).

#### R6K — Monotone valid-bound envelope gate

**Registered and reported 2026-08-29.** R6K isolates whether R6J's
nonmonotone independently repacked bounds explain the poor low-scope
pseudo-marginals. For each total and clamped evidence query, it takes the
minimum valid upper bound available through the current `i`, then normalizes
the two clamped envelopes only as a diagnostic. This is a monotone valid-bound
selector, not a nested mini-bucket algorithm or posterior bound.

Across the same 128 matched greedy rows and 128 envelope rows, evidence-bound
monotonicity violations fall from `3` to `0`, while marginal-error violations
fall only from `14` to `13`. Useful low-`i` rows remain `20`, and no
representation/order branch is uniformly within `0.01` error on all eight
conditions. The envelope improves 4 matched rows, leaves 124 unchanged, and
worsens none beyond numerical tolerance. Bound ordering was therefore a real
implementation-level issue but is not the principal cause of low-`i`
posterior error. The next gate must change factor content or region coupling;
correction and LER sampling remain blocked. Contract:
[`manifests/r6k-monotone-bound-envelope-gate-manifest-2026-08-29.json`](manifests/r6k-monotone-bound-envelope-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6k-monotone-bound-envelope-gate.md`](wiki/records/r6k-monotone-bound-envelope-gate.md).

#### R6L — Factor-content-aware mini-bucket gate

**Registered, replayed, and reported 2026-08-29.** R6L tests the smallest
literature-grounded change to bounded coupling after R6K: it holds the full
R6J exact cohort fixed and replaces scope-first-fit packing with a greedy
factor-content traversal. Because the D4 graph contains deterministic zeros,
the merge score is a zero-safe normalized local absolute sum-product
tightening rather than Rollon and Dechter's logarithmic score.

The new traversal is consequential—it changes 38 matched rows and makes a
positive local-tightening merge in all 128 candidate rows—but it does not
improve the decision target. At `i<=14`, 17 rows improve, 17 worsen, and 30
tie; useful rows remain `20`, and uniformly useful branches remain `0`.
Evidence bounds tighten on 25 low-`i` rows and loosen on 10, reinforcing that
bound quality is not a posterior-accuracy surrogate. All 56 exact ceilings
pass, and an independent replay reproduces every scientific field. Per the
registered stop rule, mini-bucket packing optimization ends here. The next
experiment must compare approximation families—explicit bounded regions/join
graphs and bounded tensor contraction—on this same cohort before any decoder
correction or LER work. Contract:
[`manifests/r6l-content-aware-mini-bucket-gate-manifest-2026-08-29.json`](manifests/r6l-content-aware-mini-bucket-gate-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6l-content-aware-mini-bucket-gate.md`](wiki/records/r6l-content-aware-mini-bucket-gate.md).

#### R6M — Approximation-family construction preflight

**Registered, executed, and reported 2026-08-29.** R6M tests the common
construction prerequisite for the two remaining bounded-inference families on
one matched maximum-observation primitive target. The region branch constructs
arc-labeled mini-cluster join graphs; all eight registered representation,
order, and scope rows pass unique factor assignment, scope cap, separator-label,
and running-intersection audits.

The tensor branch replaces every variable hyperedge with an explicit binary
COPY tensor. Exact greedy contraction reproduces independent bucket-elimination
partition functions for both representations below `1e-15` relative error.
Compressed contraction is not representation-agnostic: the bounded-superfactor
network is finite and deterministic at `max_bond=2,4,8`, reaching the exact
scalar at 8, while the unclustered network reproducibly raises a zero-induced
QR `LinAlgError` at 4 and 8; its bond-2 scalar error is `0.548`. H1 is supported
and H2/H3 are rejected. Per the prospective stop rule, no survivor is silently
selected and no marginal-accuracy matrix is released. The next gate is the
smallest zero-safe tensor remediation on the same scalar smoke. Contract:
[`manifests/r6m-approximation-family-construction-preflight-manifest-2026-08-29.json`](manifests/r6m-approximation-family-construction-preflight-manifest-2026-08-29.json).
Evidence:
[`wiki/records/r6m-approximation-family-construction-preflight.md`](wiki/records/r6m-approximation-family-construction-preflight.md).

### Lab 005 interface handoff

Status: observation-only consumer contract registered; adapter implementation
pending.

Lab 005 may consume the validated public D4 policy only through
[`../lab-005-spacetime-jit-anyonic-decoding/j1-d4-spatial-policy-interface-manifest-2026-08-29.json`](../lab-005-spacetime-jit-anyonic-decoding/j1-d4-spatial-policy-interface-manifest-2026-08-29.json).
The contract separates the committed causal prefix, first flux action,
physically generated post-action record, second charge action, and private
truth scorer. The existing `decode_physical_error` routine remains a
truth-audited simulation entry point and is not a causal online policy API.
The handoff does not authorize noisy D4 measurements, JIT scheduling, or a
fault-tolerance claim.

## Primary observables

- logical error rate with interval estimates;
- conditional XOR-sector entropy and posterior sector log odds;
- excess Bayes risk of each practical decoder;
- exact sequential policy risk, myopia cost, and stage-resolved excess risk;
- exact-agreement rate and failure mode by homology sector;
- wall time, scaling, and solver termination status.

## Stop conditions

- Do not infer D4 performance from existing Lab 002 or Lab 003 phenomenological samples.
- Do not call a minimum-weight solution Bayes-optimal without the posterior
  expected loss for the exact operational decision rule; XOR-sector sums alone
  are insufficient for Appendix-A Boolean-union loss.
- Do not expose post-flux relation components, active-set metadata, simulator
  `-1` sentinels, or truth-derived effective strings to an exact decoder.
- Do not describe the paper's D4 `[2]` decoder as ILP/MILP.
- Stop downstream work if the R1 likelihood/support audit or negative-weight PyMatching audit fails.
- Do not launch the paper-scale roughly million-sample sweep without a measured pilot cost and researcher approval.
- Preserve disagreements between practical, MILP, and Bayesian decoders as scientific results.

## Completion criteria

Lab 004 is complete only when implementation, verification, bounded data, analysis, report, and visual acceptance are separately documented. A successful reproduction includes uncertainty and convention checks; a failed reproduction includes a localized discrepancy rather than an unexplained threshold mismatch.

## Deferred branches

- A neural decoder is a separate future Lab, justified only if R4 supplies trustworthy labels and R6 establishes a meaningful scalable-decoder gap.
- Noisy repeated fusion measurements and spacetime decoding belong to a later fault-tolerant extension.

## 2026-08-30 scientific-priority reset

The active objective is not further BP micro-optimization. The dense-template
implementation is retained as a research prototype; CPU tuning is frozen
unless it blocks a registered finite-size experiment. The next work follows
four ordered packages.

### P1 — Reproduction boundary and source decoder

Keep the paper's D4 benchmark distinct from the bounded MILP and Bayes
oracles. The production comparison uses only: (O0) flux-only unit-weight
MWPM, and (O2) the paper's `w_e=1-n_e K` herald-weight MWPM, followed by the
common unit-weight charge stage. ILP/MILP remains a bounded diagnostic oracle,
not a claimed scalable or paper-production decoder.

### P2 — Matched three-decoder flux experiment

On exactly the same X-only physical D4 trajectories (`p_X` varied, `p_Z=0`)
and public D4 records, compare
O0, O2, and D4-likelihood BP posterior-LLR matching. Hold charge recovery,
logical-loss scorer, lattice, boundary convention, and stopping policy fixed.
Report first-stage flux Boolean-union failure, paired differences, convergence,
and runtime separately. Charge recovery is deliberately excluded from this
phase; the existing default-cell 25-win/1-loss signal is a mechanism pilot,
not a threshold claim.

### P3 — Mechanism and finite-size survival

Stratify O2/BP disagreements by fusion-charge pattern, topological correction
difference, convergence and confidence diagnostics. Then test whether the
paired improvement survives across a preregistered multi-p/multi-L matrix.
A benefit that vanishes, reverses, or tracks nonconvergence remains a result;
it must not be promoted as a decoder advantage.

#### R6V — Gated X-only flux finite-size scan

**Registered; large sampling is blocked on the R6U integrity report.** The
first threshold-validation allocation is deliberately D4-native, X-only, and
first-stage-only: paper (L=5,7,9,11,13),

\[
p_X \in \{0.14,0.16,0.18,0.20,0.22,0.24,0.26,0.28,0.30\},\qquad p_Z=0.
\]

Each of the 45 cells begins with 1,000 attempted *matched* physical/fusion
histories. O0, published O2, and D4-local BP posterior-LLR MWPM must consume
the same serialized physical error and public D4 record; charge recovery is
not run. Every row must retain seeds, physical edge set, flux syndrome, charge
record, corrections, terminal status, BP convergence, and final residual.

The Stage-1 output reports conditional Boolean-union flux failure with 90%
Wilson intervals, paired decoder contrasts, terminal-winding frequency, and
finite-iterate BP as the primary decoder.  The convergence flag is a diagnostic
only: BP-to-MWPM always returns a syndrome-consistent correction, so fixed-point
convergence is neither an acceptance gate nor a prerequisite for a curve.  A
matched 40-versus-160-iteration replay reports correction and logical-score
disagreement on the same trajectories. It makes no threshold fit until the
multi-size LER curves have sufficient precision. Stage 2 is precommitted: add matched 1,000-history increments,
up to 5,000 attempted histories/cell, only at a policy/adjacent-size pair's
grid points whose 90% independent size-difference interval contains zero and
the immediately neighboring grid points. The same added trajectories feed all
three policies. Stop a pair when no selected grid point remains or the cap is
reached; finite-iteration sensitivity is reported rather than used to veto
the scan.

The runner must refuse execution unless
`results/r6v-r6u-integrity-audit-2026-08-30.json` explicitly sets
`integrity_gate_passed=true`; this prevents an anomalous zero-failure pilot
from being amplified into a threshold claim before its scorer/provenance gate
passes. Contract:
[`manifests/r6v-x-only-flux-threshold-validation-manifest-2026-08-30.json`](manifests/r6v-x-only-flux-threshold-validation-manifest-2026-08-30.json).

#### R6AE — Corrected signal-only paper-region scan

**Stages 1–5 completed and analyzed at the registered cap on 2026-09-01.**
R6AE supersedes the earlier support-revealing BP campaign for performance
interpretation. It uses only the public binary $e_B/e_G$ signal, the paper
red-X channel with $p_Z=0$, sizes $L=5,7,9,11,13$, and
$p_X=0.19,0.20,0.21,0.22$. All 20 cells completed 1,000 matched attempted
histories and all three policies consumed identical physical and observation
records.

At 5,000 histories/cell, signal-only BP resolves all four negative
adjacent-size differences at $p_X=0.19$ and two at $p_X=0.20$. The other two
$p_X=0.20$ intervals and every interval at $p_X=0.21,0.22$ remain unresolved.
The frozen interval-plus-neighbor rule would retain 19 cells, but the
registered cap ends allocation. R6AE therefore closes without a stable
multi-size crossing bracket, threshold fit, or threshold estimate. Evidence:
[`wiki/records/r6ae-signal-only-bp-threshold-stage1-2026-09-01.md`](wiki/records/r6ae-signal-only-bp-threshold-stage1-2026-09-01.md),
[`wiki/records/r6ae-signal-only-bp-threshold-stage2-2026-09-01.md`](wiki/records/r6ae-signal-only-bp-threshold-stage2-2026-09-01.md),
[`wiki/records/r6ae-signal-only-bp-threshold-stage3-2026-09-01.md`](wiki/records/r6ae-signal-only-bp-threshold-stage3-2026-09-01.md),
[`wiki/records/r6ae-signal-only-bp-threshold-stage4-2026-09-01.md`](wiki/records/r6ae-signal-only-bp-threshold-stage4-2026-09-01.md), and
[`wiki/records/r6ae-signal-only-bp-threshold-stage5-2026-09-01.md`](wiki/records/r6ae-signal-only-bp-threshold-stage5-2026-09-01.md).

### P4 — Lab 003 q=3/4 versus D4 channel-equivalence audit (first action)

**Completed 2026-09-01 with a non-equivalence verdict.** The updated audit
uses the corrected signal-only D4 record rather than the earlier
support-revealing representation. Lab 003 and D4 differ in herald
conditioning, joint correlations, geometry, size meaning, decoder-visible
record, BP schedule/factorization, and logical-loss observable. Their local
edge priors share a Bernoulli form, but equal numeric $p$ and $p_X$ do not
define a common channel coordinate. Direct LER, crossing, phase-boundary, or
threshold comparison is prohibited. Evidence:
[`wiki/records/p4-lab003-d4-channel-equivalence-audit-2026-09-01.md`](wiki/records/p4-lab003-d4-channel-equivalence-audit-2026-09-01.md)
and
[`results/p4-lab003-d4-channel-equivalence-audit-2026-09-01.json`](results/p4-lab003-d4-channel-equivalence-audit-2026-09-01.json).

Do not compare Lab 003's phenomenological `q=3/4` finite-window curves with
the D4 threshold until a record-level channel map is derived and tested. Audit
whether the herald attaches to the same latent event, whether it is conditional
on degree-two fusion, whether its correlations and charge-type resolution
match, and whether geometry, error parameter, visible record, decoder, and
logical-loss convention coincide. The audit has three possible outcomes:

1. exact equivalence — register a shared-channel O0/O2/BP finite-size curve;
2. a controlled reduction — state the additional conditioning/coarse-graining
   and compare only under that reduction; or
3. non-equivalence — localize the mismatch and prohibit numerical comparison
   of `0.2084` with a Lab 003 crossing.

The current Lab 003 report supplies finite-window, decoder-specific crossing
evidence, not a promoted q=3/4 threshold of 0.35. Any value near 0.35 must be
traced to its exact lattice, size pair, decoder schedule, and error parameter
before it is used.

#### R6AF — Two-stage public-charge reproduction gate

**Registered and preflighted 2026-09-01; passed after one fail-closed interface
remediation.** The
frozen source model joins the corrected signal-only O0/O2 flux record to the
action-conditioned second charge channel. Paired arms share physical truth,
the first-observation key, and the second-round exogenous key, but the second
record is generated separately under each realized first correction. The
unconditional scorer is the Boolean union of physical winding, first-stage
physical/correction-union winding, and blue or green charge-residual winding.

The discriminating $L=2$ fixture now passes the corrected first-record,
ambiguous-zero, matched-history, first-action-disagreement,
action-conditioned-support, own-support, zero-error, full-binary second-record,
relation-free public charge-action, wrong-action binding, explicit public
transcript, and scorer gates. The initial two public-information failures were
remediated without changing the channel or score. No finite-size histories
were allocated. The next bounded transition is registration of the smallest
paired O0/O2 pilot, with grid, paired uncertainty, budget, and stop rule frozen
before execution. Contract:
[`manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json`](manifests/r6af-two-stage-public-charge-reproduction-manifest-2026-09-01.json);
evidence:
[`wiki/records/r6af-two-stage-public-charge-preflight-2026-09-01.md`](wiki/records/r6af-two-stage-public-charge-preflight-2026-09-01.md).

**Pilot registered 2026-09-01; no sampling in the registration transition.**
The smallest execution grid is $L\in\{3,5\}$ and
$p_X\in\{0.19,0.21\}$ with 512 matched attempted histories per cell: 2,048
independent physical histories and 4,096 O0/O2 arm evaluations. Each pair
shares physical, first-observation, and second-exogenous keys, while the second
record remains separately conditioned on the realized first action. Only
first-stage flux weights differ; the full-binary public charge action and
unconditional Boolean-union scorer are common.

Primary output is the per-cell paired difference $R_{O2}-R_{O0}$ with a
two-sided 90% paired-history bootstrap interval; arm risks use 90% Wilson
intervals, and discordant pairs receive an exact McNemar/binomial diagnostic.
All four cells are pilot diagnostics with no multiplicity-adjusted discovery
claim. The run stops at 512 histories/cell even when unresolved and may not
fit a crossing or threshold. Execution requires a checkpointed fail-closed
runner and deterministic first/middle/final replay in every cell.

**Pilot completed and analyzed at its registered cap on 2026-09-01.** All
2,048 independent histories, 4,096 arm evaluations, structural gates, and 12
registered replays pass. O2 has lower unconditional final loss in all four
cells, with pointwise 90% paired intervals for $R_{O2}-R_{O0}$ of
$[-0.2676,-0.1934]$, $[-0.3027,-0.2227]$, $[-0.4258,-0.3477]$, and
$[-0.4160,-0.3340]$ for $(L,p_X)=(3,0.19),(3,0.21),(5,0.19),(5,0.21)$.
The stage counts localize most of the difference to fewer first-stage
Boolean-union failures under O2; the public charge decoder is identical in
both arms. The registered stop is enforced: no refinement, crossing, or
threshold fit follows. Evidence:
[`wiki/records/r6af-two-stage-public-charge-pilot-2026-09-01.md`](wiki/records/r6af-two-stage-public-charge-pilot-2026-09-01.md).

#### R6AG — R4.5c/R6AF source-consistency synthesis

**Completed 2026-09-01 with zero new sampling.** This retrospective gate
compares only qualitative direction and mechanism across the completed
studies. R4.5c is exact, primitive $L=2$, branch-resolved, and conditioned on
the nonwinding initial channel at $p=0.1,0.3,0.5,0.6$; R6AF is paired Monte
Carlo on paper-normalized $L=3,5$, unconditional, and sampled at
$p_X=0.19,0.21$. Risk magnitudes, deltas, p-values, stage counts, size trends,
and exact-policy excesses are therefore incommensurate.

The allowed synthesis asks whether both studies support the qualitative value
of fusion information and identify the first-stage policy as a major lever.
It must preserve R4.5c's slight public-fixed O2 regression at $p=0.6$ as a
counterexample to universal O2 dominance. Opposite signs on incommensurate
ensembles would be tension, not a contradiction; contradiction is reserved for
mutually exclusive structural claims under the same policy and conditioning.
The deterministic extraction reproduced all frozen source values, classified
every quantity, and passed all six evidence/status gates. The verdict is
**qualitatively consistent with a nonuniversal boundary**: R6AF agrees with
the low/intermediate-prior R4.5c public direction, and both studies localize
material leverage to the first action. The $p=0.6$ R4.5c regression prevents
universal O2 dominance. No new histories, arm evaluations, bootstrap
replicates, interpolation, pooling, or downstream pilot were produced.
Evidence:
[`wiki/records/r6ag-r4-r6af-source-consistency-synthesis-2026-09-01.md`](wiki/records/r6ag-r4-r6af-source-consistency-synthesis-2026-09-01.md).
Contract:
[`manifests/r6ag-r4-r6af-source-consistency-synthesis-manifest-2026-09-01.json`](manifests/r6ag-r4-r6af-source-consistency-synthesis-manifest-2026-09-01.json).

#### R6AH — Legacy R5a/R6AF public-interface provenance audit

**Completed 2026-09-01: incompatible.** R5a's 20,000-history cohort
predates the R6AF fail-closed discovery that inactive `-1` sentinels and hidden
post-flux relations crossed the combined charge-action/scoring boundary. R6AH
therefore freezes the R5a contract, preflight, raw cohort, analysis, declared
source hashes, and the remediated R6AF interface before deciding whether any
legacy final-loss result remains usable as corrected complete-pipeline
evidence.

The deterministic matrix audited artifact identity, physical channel,
first-record timing and content, matched randomness, action-conditioned second
support, full-binary public charge records, charge-action inputs, Boolean-union
scoring and denominator, anti-leak fixtures, replay gates, and claim usability.
Stored private provenance will be distinguished from decoder-visible inputs.
All ten frozen hashes and five evidence-status gates pass, all 40,000 records
were inspected, and every dimension was classified. The decisive
incompatibilities are the support-revealing first record, sentinel-bearing
second record, and old combined public/private charge boundary. Physical and
lattice records remain provenance; complete-pipeline numerical claims are
withdrawn. No risk/interval/stage-count comparison, new history, bootstrap, or
rerun registration was produced. Evidence:
[`wiki/records/r6ah-r5a-r6af-public-interface-provenance-audit-2026-09-01.md`](wiki/records/r6ah-r5a-r6af-public-interface-provenance-audit-2026-09-01.md).
Contract:
[`manifests/r6ah-r5a-r6af-public-interface-provenance-audit-manifest-2026-09-01.json`](manifests/r6ah-r5a-r6af-public-interface-provenance-audit-manifest-2026-09-01.json).

#### R6AJ — Corrected complete-public-interface transfer test

**Registered 2026-09-01; zero sampling and zero analysis in this transition.**
This is the smallest corrected replacement for the withdrawn R5a transfer
question. It freezes the remediated R6AF interface rather than reusing any R5a
decoder record or numerical result. The only retained R5a provenance is the
paper-normalized red-X physical channel and periodic coloured-honeycomb
lattice/topology definition.

The prospective matrix is $L\in\{7,9\}$ and
$p_X\in\{0.17,0.21\}$, with 512 matched attempted histories per cell:
2,048 independent histories and 4,096 paired O0/O2 arm evaluations at the hard
cap. This is the smallest wholly new 2-by-2 matrix that discriminates both size
and rate transfer without restarting any closed R6AF cell. Both arms share physical, first-observation, and
second-exogenous keys; each arm nevertheless receives a separately generated
full-binary second record conditioned on its realized first action. The common
charge action sees only the known first correction and public second record.
Private relations, active support, effective truth, sentinels, and homology
remain generation/scoring data only.

The primary estimand is the per-cell paired difference in unconditional final
Boolean-union loss, with every attempted history retained in the denominator.
Pointwise 90% Wilson arm intervals, 10,000-replicate paired-history bootstrap
intervals, discordances, and the four predeclared size/rate effect-heterogeneity contrasts are frozen.
The run stops at 512 histories/cell even when unresolved. Hash, anti-leak,
action-binding, support, scorer, completeness, and first/middle/final replay
gates must all pass before future analysis can be armed. No crossing,
threshold, numerical cross-study pooling, universal O2 claim, or downstream
Lab 005 promotion is authorized.

An off-frontier R6AI crossing-refinement smoke produced one first-stage
trajectory in each of 24 cells before this durable transition was reasserted.
That branch is now marked aborted and superseded; those 24 records are excluded
from all analysis and are not inputs to R6AJ. Contract:
[`manifests/r6aj-corrected-public-interface-transfer-manifest-2026-09-01.json`](manifests/r6aj-corrected-public-interface-transfer-manifest-2026-09-01.json).

### Closed or deprioritized directions

- Fixed-arity BP micro-optimization and GPU speculation: frozen; no current
  scientific decision depends on them.
- Mini-bucket packing optimization: closed by R6L's registered negative gate.
- Generic tensor/region comparison: open as a numerical-inference method
  branch, but deprioritized until P2–P4 establish whether it changes a decoder
  decision on the physical D4 channel.
- MILP scaling: open only as a bounded reference; it is not on the path to
  reproducing the paper's large-L decoder or resolving the q=3/4 discrepancy.
