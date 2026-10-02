## Scope revision — 2026-10-01
The current task covers p,q in [0,1]. The nine submitted runs were given the previous half-domain version and must retain that historical evaluation scope. Never mirror reference values for interior q.

# SciCode 2 author notes — keep out of the candidate package

This accompanies `../herald_decoding_problem.tex`. Distribute only the problem statement and its PDF to a candidate. Do not provide this repository, its history, lab reports, reference outputs, or this directory. The public statement is self-contained and does not require access to a research dashboard or private files.

## What this version evaluates

The research question is whether incomplete local multiple-error witnesses can improve logical recovery on the exact open honeycomb patches used in Labs 002 and 003. The target is a **two-dimensional decoding phase diagram over the continuous (p,q) domain**, with inferred decodable/non-decodable regions, a transition boundary or supported constraints on it, and uncertainty. The public text defines the limiting behaviors, the meaning of changing lattice size, finite-size crossings, and p_c(q) where a single boundary exists. It leaves decoder construction, sizes, sample placement, statistical treatment, and finite-size inference to the solver. The same decoder at q=0 supplies the syndrome-only baseline; there is no separate baseline decoder or interface. The check matrix is denoted H throughout.

The scientific target is an estimated phase structure, not merely a single-size rate heatmap. Nevertheless, the current Lab 003 report explicitly accepts finite-window directional evidence, not a thermodynamic threshold. Requiring a proven intrinsic phase boundary or precise thermodynamic reference thresholds would exceed existing evidence. Different defensible decoders can have different finite-size curves. Do not grade numerical agreement to the lab's plotted guide. Grade the numerical evidence and scientific support for each claim, accepting informative unresolved regions while rejecting a diagram that provides no meaningful investigation of the transition. The private usefulness gate below is intended to reject ineffective decoders independently of plotting quality.

This revision follows the SciCode 2 criteria supplied in the conversation: specify the scientific objective and practical constraints, and evaluate whether a solver constructs and justifies the procedure. Public mandates for particular q values, p bins, size sequences, L=13 checks, per-cell precision, matched-shot mechanics, preregistration/holdout recipes, and tiny-system oracle code have been removed. Resource allocation is one short scientific-purpose statement. Examiner test coordinates, tolerances, and exact-oracle procedures remain private. The public submission contract requires a documented callable correction decoder and reproducible research artifacts, not a validator or posterior-probability API.

## Source audit

Paths below are relative to the repository root.

- `src/herald_decoder/lattice_model.py`: canonical geometry, observations, and logical cut.
- `src/herald_decoder/herald_bp_decoder.py`: existing inference implementation and exact small-instance reference; keep private.
- `labs/lab-002-herald-belief-matching/PLAN.md`: model and observation boundary; corrected posterior weighting history.
- `labs/lab-003-herald-threshold-phase-diagram/REPORT.md`: accepted finite-window scope.
- `labs/lab-003-herald-threshold-phase-diagram/METHODOLOGY.md`: withdrawn scaling interpretations and current limitations.
- `labs/lab-003-herald-threshold-phase-diagram/results/current-evidence.json`: current archived numerical evidence, including cell counts and provenance.
- `labs/lab-003-herald-threshold-phase-diagram/scripts/run_phase2_scout.py`: all-trial logical scoring and separate convergence diagnostics.

The integer-coordinate geometry in the exam was independently constructed and compared against the current canonical graph at every integer L from 2 through 20: vertex, retained-edge, detector, both rough-boundary, check-matrix, and logical-cut data agree after coordinate-based relabeling. The executable audit is `audit_lattice_construction.py`; exact source hashes and results are in `lattice_construction_audit.json`. L=2,3,4 respectively give (vertices, edges, detectors, logical-cut edges) = (16,11,6,3), (30,26,16,4), (48,47,30,5). At those sizes, H has full row rank and adjoining the logical row increases its rank by one. L counts hexagon rows/columns, not code distance. The audit uses lexicographic ordering internally. The candidate may document a different ordering; evaluator adapters must relabel arrays correctly. The public construction-check formulas and the L=2 example have been removed; the geometry itself is unchanged.

The construction checks also admit a general count derivation. The untrimmed union has L(L−1)+(L−1)(2L−1)=3L²−4L+1 shared sides, hence 6L²−(3L²−4L+1)=3L²+4L−1 distinct edges. Euler's formula for this connected patch with L² bounded hexagonal faces gives 2L²+4L vertices. Exactly 4L exposed edges are removed. Each rough boundary has 2L+1 vertices (L isolated outer tips and L+1 endpoints with a retained edge), and the two boundary sets are disjoint. Consequently E=3L²−1, D=2L²−2, and the right logical cut has L+1 edges for every integer L≥2.

The candidate's page-2 geometry figure is an inline TikZ vector diagram of L=3, generated from the canonical repository graph by `build_lattice_figure.py`. It is part of the mathematical setup, not a reference result. Black filled circles are detectors, blue open squares are left-boundary vertices, orange open diamonds are right-boundary vertices, and purple solid edges are Gamma_R. All 30 vertices remain visible, including six isolated boundary tips; 26 retained edges and four logical edges are drawn. Twelve pale dashed construction edges are explicitly excluded from E_L and the error variables. `lattice_figure_audit.json` records exact set checks, counts, and source/TikZ hashes. The generated diagram is embedded in the main TeX so the public source remains standalone.

For an explicit comparison of logical observables, let C=3(L−1) and epsilon=(L−1) mod 2. The retained edges incident to the right boundary are exactly the horizontal coordinate pairs {(C−1,epsilon+2k−1),(C+1,epsilon+2k−1)}, k=0,...,L. They are precisely the edges intersected by the repository's vertical logical line x=C/2. Thus the logical functionals coincide for every edge vector, not only for sampled errors or closed residual chains. The public wording now explicitly defines side indices, determines exposure before any deletion, applies the boundary sets at corners, and defines the logical-edge set by equality rather than containment.

The L=2 patch has 11 edges, permitting an examiner-owned exact oracle over 2,048 error configurations. The joint distribution includes all compatible herald records; conditional sector probabilities are normalized per observation. Implement this independently of the research decoder. Do not distribute it to candidates or require them to implement it. The public decoder accepts physical observations and returns a hard correction, not posterior probabilities.

### A source assumption deliberately omitted

The B18 visual guide imposes p ↔ 1−p symmetry. Do not transfer that constraint into the test. For 0<q<1, the one-sided witness generally does not admit a complement relabeling preserving the observation channel. Independent exact enumeration during this authoring audit found, for L=2 and q=0.5, optimal logical failure 0.2317753424 at p=0.2 versus 0.30442317824 at p=0.8. These are audit findings, not candidate-facing hints or a newly certified reference fixture suite. Recheck them independently before using them in a grader. The original submitted exam stipulated 0≤p≤0.5. The current revision covers 0≤p≤1; earlier runs retain their historical grading scope. This issue affects interpretation of the visual guide, not the recorded in-domain trial outcomes.

## Proposed automated assessment

The accompanying `reference_selection.json` freezes 60 numerical cells from archived evidence with hashes: L=7,9,11; p=0.12,0.24,0.36,0.45; q=0,0.25,0.5,0.75,1. All selected cells retain 1,000 trials per size in the current bundle. It is an **authoring fixture**, not an executed evaluation harness or a validated release manifest. The equal-weight archived mean is 0.2478666667 overall and 0.103375 on the 24 high-q cells. No fitted guide enters this selection.

1. **Deterministic setup gates.** Construct graph fixtures independently, including L=2 and larger patches; check incidence columns, boundary exclusions, logical cut, bit ordering, and error/correction scoring. Check p=0, q=0, q=1, local no-false-positive behavior, and conditional independence through direct probabilities as well as sampling.
2. **Tiny-instance decision and risk gate.** The examiner computes exact sector weights internally and uses them to assess the logical decisions of the submitted correction decoder; details follow below. Include herald endpoints and interior p,q. Test oracle normalization to numerical precision internally, but do not require candidate posterior arrays or compare correction bits with probabilities. Any hard rejection criterion for excess risk must be calibrated against the validated reference and the task's allowance for approximate inference before release.
3. **Information and accounting gates.** Run the decoding entry point in a fresh isolated process with only the graph, p,q,s,h and a decoder RNG. Do not provide simulator RNG state or hidden errors. Use evaluator-generated trials. Require every trial in denominators and independently verify corrections; failures and invalid outputs are distinct counters. Do not treat failure to reach a numerical fixed point as automatic logical failure when a valid correction exists.
4. **Usefulness gate.** Compare equal-weight mean failure probabilities to the frozen practical reference across all selected cells and, separately, the q≥0.75 subset. The proposed allowable gap is +0.03; superior methods pass. This margin is an author-selected proposal, not a calibrated difficulty claim. Keep suite coordinates and reference counts private. Use fresh candidate trials after freezing the submission. No fit to the reference diagram is required.
5. **Rate and uncertainty gate.** Recompute reported rates and differences relative to q=0 using the candidate's data and method. Paired counts can be used when the solver chose a paired design; pairing is not mandatory. Verify the q=0 syndrome-only limit. On independently selected cells, use fresh trials to check statistical claims with a predeclared family-wise error allowance; nominal 95% intervals must not be required to contain every held-out estimate. Test zero-count behavior and any optional-stopping claims. Fixed-seed statistical tests should have deterministic expected decisions or predeclared probabilistic tolerances.
6. **Delivery gate.** Rebuild the actual figures from submitted data. Check axes, sampled sizes, uncertainty, missing cells, censored boundaries, and correspondence to the report. Automated checks can verify numerical artifacts; scientific interpretation and the justification of approximation/scaling assumptions still need expert review or a separately validated structured rubric.

### How a private sector oracle evaluates a hard correction

For each physical observation o=(s,h), independently compute w_lambda(o)=P(o,ell(x)=lambda). For a deterministic candidate correction c(o), first check Hc=s. If admissible, it chooses logical sector d(o)=ell(c(o)); its conditional failure probability is w_(1−d)/(w_0+w_1). Its exact average failure rate is

    R_candidate = sum_o w_(1−d(o))(o),
    R_optimal   = sum_o min(w_0(o), w_1(o)).

An invalid or missing correction instead contributes w_0+w_1 for that observation. Impossible records have zero weight; ties permit either sector. This gives a private excess-risk diagnostic R_candidate−R_optimal. A randomized decoder can be assessed by averaging the oracle-weighted risks of its decisions over its randomness, with statistical uncertainty as necessary.

This tests the decoder's decisions, not numerical accuracy of an unreported posterior. Demanding exact MAP decisions on every small record is a stronger constraint than a useful approximate decoder and may reject the existing lab method; it cannot silently substitute for the performance task. Validate the intended tolerance or rejection rule before benchmarking. Also, the returned correction is a representative of a logical sector: it need not itself reproduce the herald record or be a posterior-supported error configuration. Its required physical constraint is Hc=s, and its logical success is scored against the actual error sector.

### Private large-system performance comparison

For an implementable distribution-free usefulness test, let each gate contain m independent cells with n_i trials, k_i failures, and mean R=(1/m)∑k_i/n_i. For one arm, a one-sided Hoeffding radius is

    r = sqrt[ log(1/delta) * ∑(1/n_i) / (2 m²) ].

For each of the two gates, use delta=0.0025 for the candidate upper bound and reference lower bound. A union bound over the four one-sided events gives at least 99% joint coverage, even though the two gates overlap. Accept the usefulness gate when

    R_candidate - R_reference + r_candidate + r_reference <= 0.03

for both averages. At least 2,000 fresh candidate trials per selected cell is a sensible initial design; verify the exact radii and false-failure rate before release. This derivation assumes fixed sample sizes and independent trials within and across cells. Archived adaptively stopped or selectively pooled counts do not automatically satisfy it. Reacquire fixed-design reference trials where provenance does not establish those assumptions. The final release must freeze reference hashes, trial budgets, statistical rules, and hardware before any candidate evaluation.

## Readiness against the requested SciCode 2 criteria

| Criterion | Evidence and remaining work |
| --- | --- |
| Scientific objective, open approach | Continuous 2D phase structure, large-size recovery behaviors, crossing/threshold meanings, and uncertainty are explicit; sizes, methods, sampling and validation strategy remain open. |
| New, non-searchable numerical result | The requested artifact concerns a stipulated two-parameter channel and exact finite geometry. Withhold data and solutions, use fresh evaluation trials, and check public exposure. A private result is not automatically demonstrably novel. |
| Substantive scientific judgment | Posterior objective, logical rather than configuration recovery, correlated observations, approximation diagnostics, finite-size inference, uncertainty, and comparison with the q=0 baseline. |
| Solvable with a reference | Existing Lab 002/003 computations establish a practical route and finite-window results. Package and replay an independently validated executable reference under the revised scientific contract. Accepted threshold claims must stay within evidence supported by that reference; no precise thermodynamic reference boundary is established. |
| 10–20 active hours | Intended workload only. Time at least one capable scientist using coding assistance; exclude waiting time and document actual interventions. |
| Workstation resources | The 693,000-decode base honeycomb sweep reports about 1.464 aggregate hours of measured decoding time; the mean was about 7.606 ms per decode. This excludes development, compilation, plotting, and other overhead. Portable hardware/RAM and end-to-end bounds were not recorded. Pilot the public 8-core, 32-GiB allocation. The prior arbitrary 24-hour computation cap is removed. |
| Robust evaluation | Only a documented callable correction decoder and reproducible scientific outputs are required publicly. Build and validate examiner-owned oracles, candidate adapters, reference replay, privacy isolation, statistical gates, and artifact checks before release. |
| Frontier success rate below 10% | Unmeasured target. Freeze rubric first, run multiple independent model attempts, and report uncertainty for the observed success rate. Do not assert this difficulty from the lab history. |

## Literature and leakage

A targeted search during authoring found related work, including Temkin et al., *Charge-Informed Quantum Error Correction*, https://arxiv.org/abs/2512.22119, which studies local U(1) charge information. It is not this binary degree-threshold/thinning channel. It demonstrates why the author should avoid claiming that information-assisted decoding has no literature. The search did not establish an exhaustive absence result for this exact problem.

The candidate document deliberately has no lab links, historical plots, fitted boundary values, decoder implementation details, or bibliography leading into the private research workflow. Candidates may use general scientific literature. Their numerical answer must be computed for the stated model rather than imported from a neighboring model. Before public benchmark release, audit whether any of the exact setting, archived answers, or code has already been made public.

## Status of this delivery

This delivery is an English exam statement in LaTeX with a compiled, visually checked PDF, plus private author notes and an archived-evidence selection for evaluation design. It does not claim that a full hidden grader has been executed, that an intrinsic phase transition is known, or that the intended working-time and model-success targets have been measured. The repository's active research plans and lab registries are not changed by this document-authoring task.
