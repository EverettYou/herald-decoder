# Plan — Herald decoding threshold phase diagram

## Scientific objective

Lab 003 asks whether the current fusion-remnant herald changes the
large-distance decodability of the frozen string-herald model. The primary
decoder is probability-damped sum-product BP followed by posterior-LLR
weighted PyMatching. The output is a **decoder-specific finite-size phase
diagram** in the $(q,p)$ plane, reported separately for square and honeycomb
lattices.

For fixed $(q,p)$, call a point operationally decodable when logical error
rate (LER) decreases with increasing code size over a stable scaling window,
and operationally undecodable when it increases. The boundary $p_c(q)$ is the
large-$L$ extrapolation of the crossover. Finite data can support, resolve,
or censor this boundary; they cannot by themselves establish a thermodynamic
phase transition.

All legacy $q=1$ negative-log pilot results are invalid for this question.
The old $q=0$ 25-shots/cell result is retained only as a historical smoke
test. Every registered result below is regenerated with the promoted
`herald_decoder` core, fixed posterior-LLR projection, accelerated runtime,
matched seeds, and adequate shot counts.

**Corrected-LLR provenance audit (2026-08-27): complete.** All 32 active
Phase 2 shards explicitly record `matching_projection="posterior_llr"` and
share one Numba source hash. Both primary q=1 high-p source shards likewise
record posterior LLR and share their decoder and Numba hashes. The refined
q=1 $L=11/13$ artifact records posterior LLR and matching current decoder and
lattice hashes, although its historical schema omitted the damping-decoder
and Numba-kernel hashes; future runners now record both. The refined q=0
square result is static-prior MWPM with $\log[(1-p)/p]$ and is unaffected by
the BP projection bug. Only `q0-calibration.json` and `q1-herald-scan.json`
remain explicitly negative-log smoke files and are excluded from inference.
Therefore no current primary Lab 003 result needs another rerun solely for
the LLR correction. The active blocker is BP non-convergence.

### Methodology correction — 2026-08-28

The logit-versus-log-size slope model used below is withdrawn as a phase
statistic. It implies power-law logical-error odds but was introduced without
a derivation from the code, noise model, or decoder. Bootstrap sign confidence
does not repair that model error. Accordingly, the S0/S1 color classifications,
counts, and boundary segment are historical exploratory outputs only; they are
not acceptance items and authorize no new compute.

The proof-obligation and model audit are recorded in
[`METHODOLOGY.md`](METHODOLOGY.md). The active existing-data result is now the
Bayesian order-constrained map: independent binomial/Beta posteriors are
integrated over decreasing, increasing, and other-order regions. The map uses
no functional scaling fit and reports full posterior probabilities plus a
0.90 classification gate. It is a finite-window diagnostic, not an asymptotic
phase proof. No new compute is authorized until posterior entropy and
nonmonotone mass distinguish shot limitation from size-window curvature.

**Researcher refinement (2026-08-28): accepted.** The active map score is the
log posterior odds
\(\log[\Pr(H_\uparrow\mid D)/\Pr(H_\downarrow\mid D)]\), while both
directional posterior probabilities and \(\Pr(H_{\rm other}\mid D)\) remain
separate machine-readable fields. Expanding the measured window to
\(L=5,7,9,11,13\) is the next approved evidence direction. Since L=7,9,11
already exist, the next bounded design step must use current posterior entropy
and other-order mass to register the smallest L=5/L=13 addition that
discriminates shot limitation from genuine size curvature; it must not rerun
existing distances or revert to crossing-based inference.

### Phase B1 — Bayesian L=5/L=13 sentinel extension

**Analysis status (2026-08-28): complete; all four cells unresolved.** Existing
posterior entropy and other-order mass select four complementary cells: the
strongest decreasing anchor $(q,p)=(1.00,0.36)$, the strongest increasing
frontier $(0.65,0.45)$, a high-event nonmonotone curvature sentinel
$(0.45,0.20)$, and a near-one-half saturation sentinel $(0.15,0.45)$. Exact
zero-event low-$p$ cells are excluded because new distances would not repair
their shot-limited ordering uncertainty.

Only L=5 and L=13 are added, using five fresh 200-shot seeds per cell and size:
8,000 decodes total. The existing L=7,9,11 observations are not rerun. The
five-distance posterior retains decreasing, increasing, and other-order mass,
uses the requested log posterior odds, and stops without filling the grid or
promoting a boundary. The non-overwriting dispatcher and five-distance
posterior analyzer now pass their focused tests. The dry-run audit expands
exactly four jobs and 8,000 decodes, uses only L=5/13, finds no output
conflicts, and verifies the frozen source/decoder cohort. All four production
jobs then returned zero at the registered 8,000-decode cap. The completion
audit verifies four summary/raw pairs, 8,000/8,000 raw rows, 8,000/8,000
syndrome-faithful corrections, raw SHA-256 integrity, current source/decoder
equality, and start/end source stability. The preregistered five-distance
analysis gives decreasing/increasing/other posterior masses of
0.493/0/0.507 for the decreasing anchor, 0/0.107/0.893 for the increasing
frontier, 0.012/0/0.988 for the curvature sentinel, and
0.004/0.012/0.984 for the saturation sentinel. All remain unresolved at the
0.90 gate under both Jeffreys and uniform priors. Zero QMC directional events
are resolution-censored with one-sided log-odds bounds instead of being
converted into artificial finite values. This result shows that strict order
at every adjacent size is too brittle to supply the requested full-grid phase
classification without a consequential change to the phase statistic.
An all-120-ordering decomposition further identifies the failure modes: the
decreasing anchor is a two-order L=11/L=13 floor ambiguity (2.16 effective
orderings), the frontier is dominated by one L=13 downturn after growth
through L=11 (5.34 effective orderings), curvature is broader (10.39), and
saturation is nearly exchangeable (106.17 of 120). This diagnostic is
independent of the pending choice of replacement phase statistic.
Contract:
[`manifests/phase-b1-honeycomb-l5-l13-sentinels-manifest-2026-08-28.json`](manifests/phase-b1-honeycomb-l5-l13-sentinels-manifest-2026-08-28.json).
Selection evidence:
[`manifests/phase-b1-honeycomb-l5-l13-selection-2026-08-28.json`](manifests/phase-b1-honeycomb-l5-l13-selection-2026-08-28.json).
Preflight:
[`results/phase-b1-honeycomb-l5-l13-sentinels-preflight-2026-08-28.json`](results/phase-b1-honeycomb-l5-l13-sentinels-preflight-2026-08-28.json).
Completion audit:
[`results/phase-b1-honeycomb-l5-l13-sentinels-completion-audit-2026-08-28.json`](results/phase-b1-honeycomb-l5-l13-sentinels-completion-audit-2026-08-28.json).
Five-distance analysis:
[`manifests/phase-b1-honeycomb-l5-l13-sentinels-analysis-2026-08-28.json`](manifests/phase-b1-honeycomb-l5-l13-sentinels-analysis-2026-08-28.json).

**Researcher decision (2026-08-28): Option 2, refined to a Bayesian fuzzy
linear trend.** For each posterior draw of the latent LERs, compute the OLS
projection slope against linear code distance and test \(H_\uparrow:\beta>0\)
versus \(H_\downarrow:\beta<0\). This uses a linear projection to summarize
overall direction; it does not assume that the true LER curve is linear. At a
0.90 posterior gate, the four sentinels become: decreasing anchor decodable
(mean slope -0.00914, 90% interval [-0.01067,-0.00770]); increasing frontier
undecodable (+0.01114, [0.00704,0.01524]); curvature sentinel decodable
(-0.00530, [-0.00837,-0.00222]); and saturation unresolved (+0.00060,
[-0.00352,0.00472]). Uniform-prior sensitivity changes no classification;
endpoint and Kendall-sign diagnostics agree on the three resolved cells.
Evidence:
[`results/phase-b1-honeycomb-l5-l13-bayesian-fuzzy-trend-2026-08-28.json`](results/phase-b1-honeycomb-l5-l13-bayesian-fuzzy-trend-2026-08-28.json).

The next bounded transition is to apply this exact statistic to the existing
L=7,9,11 honeycomb grid, render the red/green/gray map, and register additional
shots or L=5/13 only for the resulting gray cells. No crossing statistic or
unrestricted grid expansion is authorized.

**Full-grid fuzzy-trend status (2026-08-28): analyzed and rendered.** The
existing 231-cell honeycomb skeleton contains 82 decodable/green, 38
undecodable/red, and 111 unresolved/gray cells at the 0.90 posterior gate.
Three Jeffreys-green cells at q=0.80,0.85,0.90 and p=0.12 are conservatively
shown as gray because they become unresolved under the uniform prior. With
equally spaced L=7,9,11, the equal-weight OLS slope is exactly
proportional to theta_11-theta_7; theta_9 contributes to the intercept and the
separate midpoint-curvature diagnostic, not the slope sign. Two gray cells,
(q,p)=(0.20,0.08) and (0.45,0.20), have at least 0.95 posterior curvature and
route to L=5/13 leverage. The other 109 route to additional same-window shots
first. The next design must rank a bounded phase-frontier subset; it must not
launch all gray cells. Evidence:
[`results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json`](results/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.json)
and
[`figures/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.png`](figures/phase2-residual80-honeycomb-bayesian-fuzzy-trend-phase-2026-08-28.png).

### Phase B2 — smallest adaptive gray-frontier cohort

**Analysis status (2026-08-28): complete.** The
two curvature-routed gray cells are both covered: Phase B1 already resolves
$(q,p)=(0.45,0.20)$ as decodable with L=5,7,9,11,13, so it is reused without
duplicate compute; $(0.20,0.08)$ receives new L=5/13 data. Among the nine
shot-routed gray cells with both red and green four-neighbors, select the
highest-confidence upward-leaning cell $(0.75,0.40)$ and downward-leaning cell
$(0.50,0.20)$. Each receives 1000 fresh shots at L=7,9,11. With five fresh
200-shot seeds, the three jobs total exactly 8000 new decodes. Stop before any
other gray cell or grid expansion. Selection:
[`results/phase-b2-honeycomb-gray-frontier-selection-2026-08-28.json`](results/phase-b2-honeycomb-gray-frontier-selection-2026-08-28.json).
Contract:
[`manifests/phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json`](manifests/phase-b2-honeycomb-gray-frontier-manifest-2026-08-28.json).
The tested job-specific dispatcher expands exactly those three jobs and 8000
decodes, refuses existing output pairs, validates the frozen source/decoder
cohort and every selection-evidence hash, and remains gated on an explicit
ready manifest. The completion audit checks raw row counts, SHA-256,
syndrome fidelity, sampling coordinates, and start/end source stability. The
pooled analyzer combines L5/L13 with the existing L7/L9/L11 cohort only for
the distance arm, combines independent counts at matching L7/L9/L11 only for
the shot arms, and reuses the audited Phase B1 cell. The 64-test Lab 003 suite
passes. Preflight:
[`results/phase-b2-honeycomb-gray-frontier-preflight-2026-08-28.json`](results/phase-b2-honeycomb-gray-frontier-preflight-2026-08-28.json).
All three production jobs returned zero at the registered 8000-decode cap.
The completion audit verifies all three summary/raw pairs, 8000/8000 raw
rows, 8000/8000 syndrome-faithful corrections, raw SHA-256 integrity, exact
sampling coordinates, the frozen source/decoder cohort, and start/end source
stability. The preregistered pooling then resolves every targeted cell under
both Jeffreys and uniform priors. The new five-distance cell $(0.20,0.08)$ is
decodable with $P(\beta<0\mid D)=0.99998$; the reused five-distance cell
$(0.45,0.20)$ remains decodable at 0.99770. The added-shot cell
$(0.75,0.40)$ is undecodable with $P(\beta>0\mid D)=0.94800$, while
$(0.50,0.20)$ is decodable with $P(\beta<0\mid D)=0.99216$. Thus the four
previously gray targets become three green and one red; no unregistered cell
is changed. Completion audit:
[`results/phase-b2-honeycomb-gray-frontier-completion-audit-2026-08-28.json`](results/phase-b2-honeycomb-gray-frontier-completion-audit-2026-08-28.json).
Analysis:
[`manifests/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json`](manifests/phase-b2-honeycomb-gray-frontier-analysis-2026-08-28.json).
The verified merged presentation changes exactly these four cell payloads and
deep-compares the other 227 cells against the base map. It contains 85 green,
39 red, and 107 gray cells; all remaining gray cells route to additional
same-window shots first. Presentation:
[`figures/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png)
and
[`results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b2-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json).

### Phase B3 — reuse-first remaining frontier cohort

**Analysis status (2026-08-28): complete.** The
Phase B2 map has six gray cells with both a green and a red four-neighbor.
Five already have audited, source-compatible posterior-LLR measurements from
the withdrawn Phase S1 analysis: one has independent L7/L9/L11 shots and four
have matched L11/L13 extensions. Those measurements remain valid even though
their old logit/log-size interpretation is withdrawn, so Phase B3 reanalyzes
them with the active Bayesian fuzzy-trend statistic instead of duplicating
compute. Only the uncovered cell $(q,p)=(0.55,0.24)$ receives five fresh
200-shot seeds at L=7,9,11: one job and 3000 new decodes. Selection:
[`manifests/phase-b3-honeycomb-frontier-reuse-selection-2026-08-28.json`](manifests/phase-b3-honeycomb-frontier-reuse-selection-2026-08-28.json).
Contract:
[`manifests/phase-b3-honeycomb-frontier-reuse-manifest-2026-08-28.json`](manifests/phase-b3-honeycomb-frontier-reuse-manifest-2026-08-28.json).
The reuse audit verifies five summary/raw pairs and 11,000 syndrome-faithful
Phase S1 rows against the original completion audit, exact SHA-256 values,
the active source cohort, and decoder configuration; it explicitly does not
reuse the withdrawn interpretation. The one-job dispatcher expands exactly
3000 fresh decodes, refuses output conflicts, and validates all selection,
map, reuse-audit, source, analyzer, and completion-audit hashes. The
heterogeneous analyzer has separate tested rules for pooled same-window shots
and L11/L13 distance extension. The full 73-test Lab 003 suite passes.
Preflight:
[`results/phase-b3-honeycomb-frontier-reuse-preflight-2026-08-28.json`](results/phase-b3-honeycomb-frontier-reuse-preflight-2026-08-28.json).
The single production job returned zero at the exact 3000-decode cap. Its
completion audit verifies the summary/raw pair, 3000/3000 raw rows,
3000/3000 syndrome-faithful corrections, raw SHA-256, exact coordinate and
sampling coverage, source/decoder equality, and start/end source stability.
The five reuse shards remain separately verified. The heterogeneous Bayesian
analysis resolves one of the six cells: the pooled L7/L9/L11 counts at
$(q,p)=(0.10,0.20)$ are $[663,687,715]/2000$ and give
$P(\beta>0\mid D)=0.95816$, so the cell becomes undecodable/red. The other
five remain gray with maximum directional probabilities 0.81430, 0.83417,
0.54280, 0.50018, and 0.53763. Jeffreys and uniform priors agree on all six
labels. Completion audit:
[`results/phase-b3-honeycomb-frontier-reuse-completion-audit-2026-08-28.json`](results/phase-b3-honeycomb-frontier-reuse-completion-audit-2026-08-28.json).
Analysis:
[`results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json`](results/phase-b3-honeycomb-frontier-reuse-analysis-2026-08-28.json).
The verified Phase B3 renderer changes only $(q,p)=(0.10,0.20)$ from gray to
red, deep-compares the other 230 cell payloads against the Phase B2 map, and
reports 85 green, 40 red, and 106 gray cells. It uses no crossing statistic
and does not expand the grid. Presentation:
[`figures/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png)
and
[`results/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b3-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json).

### Phase B4 — newly exposed frontier cell

**Analysis status (2026-08-28): complete and reported.** Recomputing the
red/green-adjacent gray frontier after the one-cell Phase B3 update yields six
cells. Five are the same cells that Phase B3 just tested and left unresolved;
only $(q,p)=(0.05,0.20)$ is newly exposed. The source audit finds no unused
compatible measurement for that coordinate: the active residual-80
posterior-LLR q=0.05 shard is already consumed by the map, and the older
max-40 cohort plus its orphan temporary raw are excluded. Register exactly
five fresh 200-shot seeds at L=7,9,11, one job and 3000 decodes. Stop before
resampling the five recently tested cells or expanding p, q, L, or lattice.
The non-overwriting dispatcher now verifies the selection and current source
hashes. The completion audit checks all 3000 raw rows and syndrome fidelity;
the pooled analyzer admits only the active base plus fresh counts; and the
renderer updates exactly one payload while deep-preserving the other 230.
Synthetic branch tests, source-drift rejection, a conflict-free public dry
run, and the full 80-test Lab 003 suite pass. The manifest is now `ready` for
its one bounded job, but production was not launched in this transition.
Selection:
[`manifests/phase-b4-honeycomb-new-frontier-selection-2026-08-28.json`](manifests/phase-b4-honeycomb-new-frontier-selection-2026-08-28.json).
Contract:
[`manifests/phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json`](manifests/phase-b4-honeycomb-new-frontier-manifest-2026-08-28.json).
Preflight:
[`results/phase-b4-honeycomb-new-frontier-preflight-2026-08-28.json`](results/phase-b4-honeycomb-new-frontier-preflight-2026-08-28.json).
The single production command subsequently returned zero at the exact
3000-decode cap. The completion audit verifies the declared summary/raw pair,
3000/3000 raw rows, 3000/3000 syndrome-faithful corrections, exact SHA-256,
sampling coordinates, decoder/source equality, and start/end source
stability. Fresh logical-error counts are 342, 361, and 373 out of 1000 at
L=7,9,11. The launch gate is now closed as `closed_data_complete`; no
Bayesian pooling or phase-map update was performed in this transition.
Completion audit:
[`results/phase-b4-honeycomb-new-frontier-completion-audit-2026-08-28.json`](results/phase-b4-honeycomb-new-frontier-completion-audit-2026-08-28.json).
Pooling only the active base and audited fresh counts gives
$[698,720,738]/2000$ at L=7,9,11. The Jeffreys posterior has
$P(\beta>0\mid D)=0.90639$ and the uniform-prior sensitivity has 0.90616;
both classify the target as undecodable at the registered 0.90 gate. The
central 90% slope interval crosses zero, which is reported explicitly; no
unregistered interval-sign gate is introduced. The exact renderer changes
only $(q,p)=(0.05,0.20)$ from gray to red and deep-preserves the other 230
Phase B3 payloads. The reported map contains 85 green, 41 red, and 105 gray
cells. Analysis:
[`results/phase-b4-honeycomb-new-frontier-analysis-2026-08-28.json`](results/phase-b4-honeycomb-new-frontier-analysis-2026-08-28.json).
Presentation:
[`figures/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png)
and
[`results/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b4-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json).

### Phase B5 — persistent five-cell frontier matrix

**Analysis status (2026-08-28): complete.** The Phase B4 update
reduces the red/green-adjacent gray frontier from six cells to five and
exposes no new cell. All five are the cells that Phase B3 left unresolved.
The source inventory covers 12 direct measurement summaries and finds no
unused source-compatible shard. Four cells already have Phase S1 L11/L13
evidence but lack L5; register one fresh 1000-shot L5 job at each of
$(0.30,0.20)$, $(0.35,0.20)$, $(0.40,0.20)$, and $(0.60,0.28)$. The
$(0.55,0.24)$ cell instead receives 1000 additional independent shots at each
of L=7,9,11. This five-job matrix covers every persistent frontier branch at
7000 new decodes. Stop before another cell, p/q midpoint, square lattice, or
distance beyond L5. The five-job dispatcher now proves distinct output paths,
audits the complete prior-evidence source chain, and enforces the four-worker
cap. The completion audit requires exactly 7000 syndrome-faithful raw rows;
the analyzer implements both heterogeneous pooling branches under Jeffreys
and uniform priors; and the renderer updates exactly five payloads while
deep-preserving the other 226. The public dry run and 86-test suite passed,
but the first production call exposed an integration gap: the inherited Phase
2 CLI rejected four registered L5-only jobs before writing output, while the
independent L7/L9/L11 job completed. A source-hashed single-size adapter around
the unchanged `run_shard` kernel and an audited resume path were added and
retested. The completed 3000-row shard was verified and reused; only the four
missing 1000-row jobs ran. The final completion audit verifies five summary/raw
pairs, exactly 7000 rows, all 7000 syndrome-faithful corrections, frozen
sampling/decoder/source hashes, and zero overwritten outputs. The
preregistered heterogeneous Bayesian analysis then uses L=5,7,9,11,13 for
the four distance-extension cells and pooled L=7,9,11 shots for the fifth.
All five classifications are stable between Jeffreys and uniform priors.
Only $(q,p)=(0.40,0.20)$ resolves, becoming decodable with
$P(\beta<0\mid D)=0.95528$; the other four remain unresolved. The renderer
updates exactly the five registered payloads, deep-preserves the other 226,
and changes the map totals from 85/41/105 to 86 decodable, 41 undecodable,
and 104 unresolved. No crossing statistic, interpolation, or grid expansion
is used. Selection:
[`manifests/phase-b5-honeycomb-persistent-frontier-selection-2026-08-28.json`](manifests/phase-b5-honeycomb-persistent-frontier-selection-2026-08-28.json).
Contract:
[`manifests/phase-b5-honeycomb-persistent-frontier-manifest-2026-08-28.json`](manifests/phase-b5-honeycomb-persistent-frontier-manifest-2026-08-28.json).
Preflight:
[`results/phase-b5-honeycomb-persistent-frontier-preflight-2026-08-28.json`](results/phase-b5-honeycomb-persistent-frontier-preflight-2026-08-28.json).
Completion audit:
[`results/phase-b5-honeycomb-persistent-frontier-completion-audit-2026-08-28.json`](results/phase-b5-honeycomb-persistent-frontier-completion-audit-2026-08-28.json).
Analysis:
[`results/phase-b5-honeycomb-persistent-frontier-analysis-2026-08-28.json`](results/phase-b5-honeycomb-persistent-frontier-analysis-2026-08-28.json).
Presentation:
[`figures/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png)
and
[`results/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b5-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json).

### Phase B6 — four-cell balanced-evidence matrix

**Analysis status (2026-08-28): complete.** Recomputing the exact
four-neighbor red/green-adjacent gray frontier on the Phase B5 map leaves four
cells: $(0.30,0.20)$, $(0.35,0.20)$, $(0.55,0.24)$, and $(0.60,0.28)$.
The evidence inventory audits 14 direct summaries and finds no compatible
unused shard. At the first, second, and fourth cells, Phase B5 already has
L=5,7,9,11,13 with 1000 shots except L11 at 2000; register fresh 1000-shot
measurements only at L=5,7,9,13 so all five distances reach 2000 without
oversampling L11. The q=0.55 cell has 3000 shots at L=7,9,11, so register only
the missing L5 and L13 endpoints. This is four jobs and 14000 new decodes,
covering every independent frontier branch. Stop before another cell, p/q
midpoint, square lattice, or distance outside L=5..13. Production remains
closed until the four-job dispatcher, 14000-row completion audit, map-count
pooling analyzer, and exact four-payload renderer pass fail-closed tests. All
four gates now pass the full 92-test Lab 003 suite. In addition, every real
runner command shape is executed with a zero-shot sentinel: all four pass
size/coordinate validation and stop at the later positive-shot guard without
writing any output. This closes the integration-path gap exposed in Phase B5.
The manifest was therefore opened for production. All four jobs completed
within the four-worker cap. The final completion audit verifies four exact
summary/raw pairs, 14000/14000 rows, all 14000 syndrome-faithful corrections,
registered coordinates/sizes/seeds, decoder/source equality, source
stability, and raw hashes. The data are sealed before Bayesian analysis or
map rendering. The preregistered analysis then pools fresh counts directly
into the Phase B5 map vectors and reruns the Jeffreys-primary/uniform-prior
fuzzy linear projection. All four labels are prior-stable but remain below
the 0.90 decision gate: q=0.30,p=0.20 has upward-trend probability 0.80563;
q=0.35,p=0.20 has downward probability 0.77980; q=0.55,p=0.24 has downward
probability 0.85715; and q=0.60,p=0.28 has upward probability 0.83128. The
renderer updates exactly these four evidence payloads, deep-preserves 227,
and changes no classification. Counts remain 86 decodable, 41 undecodable,
and 104 unresolved. No crossing statistic, interpolation, or grid expansion
is used. Selection:
[`manifests/phase-b6-honeycomb-four-cell-frontier-selection-2026-08-28.json`](manifests/phase-b6-honeycomb-four-cell-frontier-selection-2026-08-28.json).
Contract:
[`manifests/phase-b6-honeycomb-four-cell-frontier-manifest-2026-08-28.json`](manifests/phase-b6-honeycomb-four-cell-frontier-manifest-2026-08-28.json).
Preflight:
[`results/phase-b6-honeycomb-four-cell-frontier-preflight-2026-08-28.json`](results/phase-b6-honeycomb-four-cell-frontier-preflight-2026-08-28.json).
Completion audit:
[`results/phase-b6-honeycomb-four-cell-frontier-completion-audit-2026-08-28.json`](results/phase-b6-honeycomb-four-cell-frontier-completion-audit-2026-08-28.json).
Analysis:
[`results/phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json`](results/phase-b6-honeycomb-four-cell-frontier-analysis-2026-08-28.json).
Presentation:
[`figures/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png)
and
[`results/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b6-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json).

### Phase S0 — slope-flow phase-map remediation (withdrawn)

**Researcher correction (2026-08-28): registered and phase-prioritizing.**
The crossing-centered analysis is methodologically superseded. In these noisy
finite-size data, arbitrarily small fluctuations can repeatedly reverse an
adjacent-size LER difference and create multiple crossing locations;
bootstrapping the locations quantifies that instability but does not turn
them into a robust phase statistic. All crossing-derived `finite`, `ceiling`,
$p_c$, and $q_c$ labels are removed from active phase inference. Their raw
posterior-LLR counts and provenance remain valid inputs.

The replacement primary statistic is the all-distance scaling-flow slope

\[
\operatorname{logit} P_{\rm L}(L;p,q)
=\alpha(p,q)+\beta(p,q)\log L.
\]

At every measured $(p,q)$, fit binomial logical-error counts across the full
common-source $L=7,9,11$ honeycomb skeleton. Resample each distance's complete
nested-p seed trajectories for 20,000 replicates and report
$D(p,q)=\Pr[\beta(p,q)<0]$. A cell is green/decodable only when the central
90% beta interval lies below zero and $D\ge0.95$; red/undecodable only when
the interval lies above zero and $D\le0.05$; otherwise it is gray/unresolved.
The operational boundary is the stable $\beta=0$ contour, not an LER-curve
crossing. It is drawn only where bootstrap and leave-one-distance-out checks
support it, with no interpolation through unresolved or unmeasured cells.

The main figure must be a red/green/gray q-p raster whose color directly
represents scaling direction and confidence. Crossing markers and crossing
counts are forbidden from the primary panel. No third cohort, q=0.925, L15,
square, or new threshold simulation may start before this reanalysis and
presentation remediation are complete. Durable contract:
[`results/phase-diagram-slope-flow-remediation-2026-08-28.json`](results/phase-diagram-slope-flow-remediation-2026-08-28.json).

**Stability diagnostic (2026-08-28): complete.** Leave-one-distance-out beta
signs are stable for 65/81 green, 25/36 red, and 36/114 gray cells. The other
78 gray cells are distance-limited rather than merely shot-limited, and 27
colored cells are excluded from boundary support because their sign depends
on the three-distance scaling window. There is no directly observed green/red
adjacency that passes both bootstrap and leave-one-distance-out gates. Of ten
gray cells lying between both resolved colors, four are seed-limited and six
need another distance first. This ranking is diagnostic only and authorizes no
new simulation. Evidence:
[`results/phase2-residual80-honeycomb-slope-flow-stability-2026-08-28.json`](results/phase2-residual80-honeycomb-slope-flow-stability-2026-08-28.json).

### Phase S1 — bounded gray-frontier discrimination (withdrawn interpretation)

**Registration status (2026-08-28): registered, not started.** The smallest
matrix covering all ten gray cells between both resolved colors has two arms.
For the four size-window-stable cells, add five independent 200-shot seed
trajectories at L=7,9,11. For the six size-window-unstable cells, add a matched
L=11,13 cohort with the same five new seeds and 200 shots per seed. This is ten
jobs and 24,000 new decodes in total. The two arms discriminate shot-limited
uncertainty from scaling-window curvature without asking the researcher to
rank runnable diagnostics.

**Preflight status (2026-08-28): passed, production not launched.** The tested
job-specific dispatcher emits exactly ten non-overwriting runner commands and
24,000 planned decodes. It fails closed on budget drift, output conflicts,
analysis-artifact hash drift, source-cohort mismatch, decoder mismatch, or a
manifest not explicitly marked ready. The matrix then stops without p/q
midpoints, unrestricted L15, square expansion, or phase promotion. Contract:
[`manifests/phase-s1-honeycomb-slope-flow-gray-frontier-manifest-2026-08-28.json`](manifests/phase-s1-honeycomb-slope-flow-gray-frontier-manifest-2026-08-28.json).
Preflight:
[`results/phase-s1-honeycomb-slope-flow-gray-frontier-preflight-2026-08-28.json`](results/phase-s1-honeycomb-slope-flow-gray-frontier-preflight-2026-08-28.json).

**Execution status (2026-08-28): data complete, not analyzed.** All ten jobs
returned zero and stopped at the registered 24,000-decode cap. The completion
audit verifies ten summary/raw pairs, 24,000/24,000 raw rows, 24,000/24,000
syndrome-faithful corrections, every raw SHA-256, start/end source stability,
and exact Phase 2 source/decoder equality. No beta refit, classification,
boundary update, or crossing statistic was run in this transition. Evidence:
[`results/phase-s1-honeycomb-slope-flow-gray-frontier-completion-audit-2026-08-28.json`](results/phase-s1-honeycomb-slope-flow-gray-frontier-completion-audit-2026-08-28.json).

**Analysis status (2026-08-28): complete.** The 20,000-replicate slope-flow
bootstrap and preregistered leave-one-distance-out gates update only the ten
target cells; the other 221 measured cells are byte-for-byte unchanged in the
analysis payload. One target, $(q,p)=(0.10,0.20)$, becomes undecodable/red.
The other nine remain unresolved, so the full map is now 81 green, 37 red,
and 113 gray cells. Exactly one directly observed green/red boundary segment,
at $q=0.10$ between $p=0.16$ and $0.20$, passes both uncertainty gates. No
crossing statistic, interpolation, or new simulation was used. Evidence:
[`results/phase-s1-honeycomb-slope-flow-gray-frontier-analysis-2026-08-28.json`](results/phase-s1-honeycomb-slope-flow-gray-frontier-analysis-2026-08-28.json).

### Phase N0 — bounded high-p convergence-cap diagnostic

Before spending another production-scale shot wave, use square $q=1$ at
$L\in\{7,9,11,13\}$ and $p\in\{0.30,0.40,0.49\}$ with 64 fixed matched
observations per cell. Compare the frozen synchronous 40-iteration decoder,
synchronous damping with an 80-iteration cap, and the validated stable-sort
residual-priority schedule with an 80-iteration cap. Record convergence,
iterations, final residual, posterior scores, correction agreement, logical
outcomes descriptively, syndrome fidelity, and runtime. This matrix
discriminates a simple truncation limit from schedule-sensitive slow drift and
size-dependent noncontraction. It is a diagnostic only: it cannot rewrite the
existing decoder-specific curves or promote a new primary decoder.

**Execution status (2026-08-27): complete.** Across 768 matched observations,
synchronous-40 converges on 16 (2.1%), synchronous-80 on 235 (30.6%), and
stable-sort residual-priority-80 on 353 (46.0%). Both the iteration cap and
schedule therefore contribute materially, but neither produces robust
convergence at every large-size cell: for example at $L=13,p=0.30$ the counts
are 0, 0, and 2/64. The apparent convergence recovery near $p=0.49$ is not
decodability evidence; near-uniform priors can yield weak, easily stabilized
messages. Mean end-to-end runtimes are 3.90, 5.43, and 8.26 ms respectively.
Residual-80 changes many correction representatives but has exactly the same
logical outcome as synchronous-80 on all 768 observations; synchronous-80
has one net additional descriptive failure relative to synchronous-40.
Every correction is syndrome faithful. Evidence:
[`results/n0-square-q1-convergence-cap-2026-08-27.json`](results/n0-square-q1-convergence-cap-2026-08-27.json)
and
[`figures/n0-square-q1-convergence-cap-2026-08-27.png`](figures/n0-square-q1-convergence-cap-2026-08-27.png).

**Researcher decision (2026-08-27): Option 2.** Lab 003 is restarted under
the best tested operational BP arm: compiled damping BP with damping $0.25$,
stable-sort residual-priority updates, a cap of 80 iterations, and
posterior-LLR PyMatching weights. The exact-equivalence C7 buffer-reuse arm
and the C8 cached-product arm are disabled. The prior synchronous-40 shards
remain immutable provenance and are not pooled with this restarted series.
The first bounded production wave is honeycomb $q=1$ at
$L\in\{5,7,9,11\}$ and
$p\in\{0.08,0.12,0.16,0.20,0.24,0.28,0.32,0.36,0.40,0.45,0.49\}$, using five
matched seeds and 200 shots per seed. Its curve and crossing diagnostic are
decoder-specific finite-size evidence only: N0 still prevents an asymptotic
threshold claim.

**First-wave acceptance (2026-08-27): complete.** The honeycomb $q=1$ shard
contains 44,000 gzip JSONL rows and passes its declared SHA-256 check. The
frozen residual-priority-80 and posterior-LLR configuration and all five
source hashes are present. No $L=5/7$ or $L=7/9$ directed crossing is
bracketed; the $L=9/11$ point curves cross once at $p=0.380$. At $p=0.49$,
convergence decreases from 0.768 at $L=5$ to 0.184 at $L=11$, so this is a
refinement target rather than a promoted threshold. The runner did not persist
a correction-syndrome fidelity field or sufficient per-shot correction data
to audit it post hoc. Although the same decoder path was syndrome faithful on
all 768 N0 observations, that earlier test is not a substitute for shard-level
evidence. The prerequisite is now implemented and tested: future shards fail
closed before a mismatched row or atomic finalization and persist fidelity in
raw rows, cell summaries, and a top-level aggregate. The deliberate-failure
and real two-shot honeycomb smoke tests pass, as does the full 11-test combined
runner/analyzer suite. Evidence:
[`results/phase2-syndrome-fidelity-gate-2026-08-27.json`](results/phase2-syndrome-fidelity-gate-2026-08-27.json).

### Phase N1 — bounded honeycomb q=1 crossing refinement

Refine only the isolated $L=9/11$ point crossing with
$p\in\{0.36,0.37,0.38,0.39,0.40\}$. Use five fresh seeds
531001--531005 and 600 shots per seed, giving 3000 shots/cell and 30,000
decodes total. Freeze the researcher-selected compiled residual-priority-80
decoder and the new fail-closed syndrome-fidelity gate. This is a standalone
new-source cohort and is not pooled with the 1000-shot first wave. Stop after
this one balanced matrix; inspect point-crossing stability, seed-cluster
uncertainty, convergence, fidelity, raw integrity, and provenance before any
additional point or size. The result may refine or reject a finite-size
crossing but cannot promote an asymptotic threshold or ceiling-compatible
phase. Registered manifest:
[`manifests/manifests/phase-n1-honeycomb-q1-refinement-manifest-2026-08-27.json`](manifests/phase-n1-honeycomb-q1-refinement-manifest-2026-08-27.json).

**Execution status (2026-08-27): complete.** The 30,000-record raw artifact
passes gzip and SHA-256 checks, records the registered five-file source
cohort, and has 30,000/30,000 syndrome-faithful corrections. The fresh point
curves do not bracket a crossing: $L=11$ has lower LER than $L=9$ at every
registered $p$. In 10,000 independent-within-size seed-cluster bootstrap
replicates, 97.86% preserve that larger-size advantage at all five $p$ values
and only 1.55% contain a directed crossing; every per-$p$ 95% interval for
$\mathrm{LER}_{9}-\mathrm{LER}_{11}$ is positive. Convergence remains limited,
ranging from 0.383--0.427 for $L=9$ and 0.239--0.298 for $L=11$. Thus the
first-wave $p=0.380$ point crossing is not replicated, Phase N1 stops, and no
threshold is promoted. Evidence:
[`results/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27.json`](results/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27.json),
[`results/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27-analysis.json`](results/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27-analysis.json),
and
[`figures/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27.png`](figures/q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27.png).

### Full-domain amendment — honeycomb $q=1$, $0\le p\le1$

The researcher explicitly rejects the former $p\le0.49$ domain restriction
for the earlier full-domain honeycomb diagnostic. The open-boundary honeycomb
graph has predominantly trivalent detectors, so complementing every edge
changes the observed syndrome at the odd-degree detectors. This means the
symmetry uses a known syndrome/logical relabeling rather than identical raw
syndromes; it does not break the researcher-specified phase-diagram relation
$q_c(p)=q_c(1-p)$. The primary honeycomb $q=1$ diagnostic therefore includes a fresh
full-domain BP grid at $p=0.01,0.05,0.10,\ldots,0.95,0.99$ and deterministic
$p=0,1$ endpoints. This series is source-separated from prior $p<0.5$ shards.

**Execution status (2026-08-27): complete.** The 84,000-observation BP shard
is raw-hash verified and 84,000/84,000 syndrome faithful. Its full-domain LER
curve peaks near the unbiased middle and falls again as $p\to1$; all point
LERs at $p=0.99$ are zero. BP convergence nevertheless remains size limited
near the middle, so this is finite-size decoder evidence and not an
asymptotic-threshold claim. The exact endpoint artifact is separate because
the finite-prior BP recurrence is undefined at $p=0,1$.

### Phase N2 — bounded honeycomb q=1 high-p sentinels

Test only $p\in\{0.45,0.49\}$ at $L=9,11,13$ with five fresh seeds
532001--532005 and 600 shots per seed: 3000 shots/cell and 18,000 decodes.
Use the same residual-priority-80 runner/source cohort and fidelity gate as N1,
but independent observations. Inspect both adjacent-size LER trends,
seed-cluster stability, convergence, fidelity, raw integrity, and provenance.
Stop after this matrix; do not add held-out $L=15$ or promote a ceiling claim
until the sentinel result is accepted. Registered manifest:
[`manifests/manifests/phase-n2-honeycomb-q1-highp-manifest-2026-08-27.json`](manifests/phase-n2-honeycomb-q1-highp-manifest-2026-08-27.json).

**Execution status (2026-08-27): complete.** The 18,000-record raw artifact
passes gzip and SHA-256 checks, has 18,000/18,000 syndrome-faithful
corrections, and exactly matches the N1 source hashes. At $p=0.45,0.49$, LER
decreases from $L=9$ to 11 to 13, while convergence also falls sharply: the
rates are 0.326/0.304, 0.192/0.181, and 0.119/0.095 for $L=9,11,13$.
The $L=9/11$ advantage is retained at both points in 100% of 10,000
seed-cluster bootstrap replicates. For $L=11/13$, 95.24% retain the advantage
at both points and 2.50% contain a directed crossing; at $p=0.49$,
$P(\mathrm{LER}_{13}<\mathrm{LER}_{11})=0.9524$ and the 95% delta interval
narrowly includes zero. This misses the preregistered 0.975 sign-stability
target, so held-out $L=15$ remains gated. The next permissible transition is
the registered balanced +100 shots/seed wave at $L=11,13,p=0.49$, after a
tested deterministic shot-start control prevents duplicated observations.
No ceiling or threshold claim is promoted. Evidence:
[`results/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27.json`](results/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27.json),
[`results/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27-analysis.json`](results/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27-analysis.json),
and
[`figures/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27.png`](figures/q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27.png).

### Phase N3 — bounded p=0.49 stability extension

The initially proposed shot-start implementation would change the runner hash
and force a cross-source merge. Correct that design before execution: keep the
N2 runner unchanged and regenerate a self-contained $L=11,13$, $p=0.49$
artifact with the same seeds 532001--532005 and 700 shots/seed. The first 600
shots/seed must reproduce every deterministic N2 raw field exactly; the final
100 shots/seed are the balanced increment. The complete artifact therefore
has 3500 shots/cell and 7000 decodes, remains one source cohort, and requires
no post-hoc merge. Re-evaluate the 0.975 seed-cluster sign-stability target,
then stop without launching $L=15$. Registered manifest:
[`manifests/manifests/phase-n3-honeycomb-q1-p049-extension-manifest-2026-08-27.json`](manifests/phase-n3-honeycomb-q1-p049-extension-manifest-2026-08-27.json).

**Execution status (2026-08-27): rejected before analysis.** N3 produced 7000
raw records with a valid gzip/SHA-256 pair, 7000/7000 syndrome fidelity, and
an exact 600-shot/seed deterministic-prefix match to N2 after excluding the
runtime-only `decode_ms` field. However, the runner, lattice, decoder, and
damping-decoder files changed on disk during execution. The end-of-run hashes
therefore do not match the registered preflight/N2 cohort and cannot identify
the code loaded at process start. The artifact is quarantined under
`results/rejected-source-drift-n3-2026-08-27/`, is excluded from every
scientific inference, and has no crossing analysis. N2 remains the latest
accepted evidence. Before any retry, the runner must fail closed unless
start-of-run and end-of-run source hashes are identical. Rejection audit:
[`results/n3-source-drift-rejection-2026-08-27.json`](results/n3-source-drift-rejection-2026-08-27.json).

**Prerequisite gate status (2026-08-27): complete.** The Phase 2 runner now
captures the five-file source cohort before decoding and recomputes it after
the temporary gzip stream closes but before atomic publication. Any changed,
added, or missing fingerprint deletes the temporary raw file and raises; the
summary is never written. Successful summaries persist the start hashes and
an explicit `source_stability.start_equals_end` assertion. A simulated-drift
integration test verifies that neither final nor temporary raw data survives,
and the complete runner/analyzer suite passes 14/14 tests. This prospective
gate does not rehabilitate N3 or change the completed full-domain result.
Evidence:
[`results/phase2-source-stability-gate-2026-08-27.json`](results/phase2-source-stability-gate-2026-08-27.json).

**Independent Phase 2 completeness audit (2026-08-27): complete.** The
registered q-skeleton expects 42 lattice/q shards. Thirty-two corrected-LLR
summaries are active: 26 have finalized raw files and six have atomic-temp raw
files whose SHA-256 exactly matches the summary declaration, making them
recoverable without recomputation. The ten active gaps all have complete
summary/raw pairs in the explicitly superseded `98deb10d` Numba-source cohort,
but cannot be pooled with the active `8f903ad` cohort. The current runner also
uses a strengthened five-file provenance schema and a newer Numba source hash,
so simply resuming ten cells would create another mixed-source cohort. No
compute, rename, or deletion was performed during that audit. Thread-006 has
since selected the Option 2 full restart, so the 32 active synchronous-40
shards and the superseded cohort remain immutable legacy evidence and are not
pooled with the new residual-priority-80 series. Evidence:
[`results/phase2-completeness-audit-2026-08-27.json`](results/phase2-completeness-audit-2026-08-27.json).

## Physical conjectures and expected phase diagrams

### Conjecture A — finite threshold uplift

The conservative expectation is a smooth boundary beginning near the usual
surface-code-like MWPM threshold at $q=0$ and rising with $q$,

\[
p_c(q)>p_c(0),
\]

while remaining below $1/2$ for all $q\le1$. This would mean heralds improve
the decoder without eliminating the high-noise undecodable phase.

### Conjecture B — a finite herald transition $q_c$

The strong hypothesis is that a finite $q_c<1$ exists such that

\[
p_c(q)=\frac12,\qquad q>q_c.
\]

Here “any $p$ is decodable” means every $0\le p<1/2$ under the registered
noise model. In the phase diagram, the boundary rises from $p_c(0)$ and
terminates on the ceiling $p=1/2$ at $(q_c,1/2)$; the vertical strip
$q>q_c$, $p<1/2$ is decodable.

This is plausible because increasing $q$ reveals more local degree
information. At $q=1$ on a trivalent honeycomb detector, parity and herald
eligibility distinguish local degrees $0,1,2,3$. It is not automatic: local
degree data need not determine the edge configuration or its logical class,
and degree-preserving alternating cycles can retain homological ambiguity.
Square vertices also retain more local degree ambiguity. Moreover, a fixed
BP-to-independent-LLR-to-MWPM projection can fail even when the observation
contains enough information for an optimal decoder.

The finite study therefore cannot literally prove decodability for all
$p<1/2$. It can support a **ceiling-compatible phase** by showing decreasing
LER through $p=0.49$, stable held-out-size scaling, and no contrary small-graph
oracle evidence. The correct claim in that case is $p_c(q)\ge0.49$ and
compatibility with $p_c(q)=1/2$, not an infinite threshold.

### Competing outcomes

1. **Bounded monotone boundary:** $p_c(q)$ rises but stays below $1/2$.
2. **Ceiling transition:** the data favor a finite $q_c$ above which the
   boundary is censored at $1/2$.
3. **No resolved uplift:** $p_c(q)$ is statistically indistinguishable from
   the $q=0$ reference.
4. **Decoder-limited nonmonotonicity:** more herald information improves the
   exact/or soft posterior but the scalable decoder's boundary is flat,
   nonmonotone, or re-entrant.
5. **Unresolved scaling:** adjacent sizes disagree or correction-to-scaling
   effects dominate the available sizes.

More information cannot worsen the Bayes-optimal decoder because it may
ignore the extra record. It can worsen this approximate decoder. Therefore
monotonicity in $q$ is a hypothesis and sensitivity constraint, not an
assumption imposed on the primary fit.

## Frozen model and decoder controls

- Analyze square and honeycomb lattices separately; never pool their
  thresholds or $q_c$ estimates, and never compare their LERs directly at a
  common nominal $p$. Each geometry receives its own physical-error grid,
  calibrated to its effective distance and to an observable-LER range.
- Errors are independent edge Bernoulli variables with $0<p<1/2$.
- The primary campaign fixes $p_m=p_h=0$.
- The herald is the current degree-$\ge2$ witness sampled with efficiency
  $q$, not an erasure location or fusion history.
- Primary herald decoder: `HeraldAwareBpMatchingDecoder` with
  `recurrence_mode="damping"`, `damping=0.25`,
  `update_schedule="residual_priority"`,
  `residual_priority_order="stable_sort"`, `max_iterations=80`, fixed
  `matching_projection="posterior_llr"`, and compiled execution. The
  buffer-reuse and cached-product variants are disabled.
- Primary reference: static-prior syndrome-only PyMatching MWPM.
- Secondary attribution control: syndrome-only BP plus posterior-LLR
  PyMatching, using the same recurrence and matching backend.
- Memory recurrence, legacy negative-log weights, measurement noise, and
  erasure decoding are excluded from the primary phase diagram. They require
  separately labelled follow-up studies.
- All numerical runs use `run_research_python.sh`; artifacts record the
  interpreter, NumPy, Numba, SciPy, PyMatching, source revision, and core-file
  hashes. A fallback runtime invalidates the run.

## Data-generation design

### Nested matched samples

Use common random numbers to make comparisons maximally informative. For a
fixed $(\text{lattice},L,\text{seed},\text{shot})$, generate independent
uniform variates $u_e$ for every edge and $u_v$ for every detector. Define

\[
x_e(p)=\mathbf 1[u_e<p],\qquad
h_v(p,q)=\mathbf 1[d_v(p)\ge2]\mathbf 1[u_v<q].
\]

Thus error configurations are nested in $p$, herald fields are nested in
$q$ conditional on eligibility, and every decoder arm sees the same error and
syndrome. This preserves the correct marginal distribution at every
$(q,p)$ while enabling paired comparisons across decoders and common sampled
locations. Seed-cluster inference must preserve these induced correlations.

### Required raw record

Store one row per shot and decoder arm, not only pooled counts. Each record
contains lattice, $L$, $p$, $q$, seed, shot index, observation identifier,
logical failure, BP convergence/iterations/max delta, decode time, and decoder
identity. Store enough RNG provenance to regenerate $(E,S,H)$ exactly.
Per-cell summaries and figures are derived artifacts.

### Code sizes

- Discovery sizes: $L\in\{5,7,9,11\}$.
- Primary scaling sizes: $L\in\{7,9,11,13\}$.
- Held-out confirmation size: $L=15$, added only at selected boundary,
  high-$p$, and control points and never used to choose those points.
- Tiny exact-oracle sizes: square $L=3$ and honeycomb $L=2$ (or the largest
  exactly enumerable graph supported by the frozen implementation).

### Shot allocation

- Every discovery cell begins with five deterministic seeds and 200 shots per
  seed: 1000 shots/cell. No 25-shot result enters an inference.
- Add balanced waves of 100 shots per seed. Never add shots to only the seed
  or size whose outcome is favorable.
- Boundary and high-$p$ confirmation cells receive at least 3000 shots/cell.
- Continue up to 5000 shots/cell when the 95% binomial interval half-width
  exceeds 0.015 or the sign of an adjacent-size LER difference has posterior
  probability below 0.975.
- A preregistered exceptional cap of 10,000 shots/cell is allowed only when a
  cell directly determines whether the boundary is finite or ceiling-censored.
  Reaching the cap without classification is reported as unresolved.

## Registered sequence

### Phase 0 — implementation and information preflight

1. Verify the accelerated runtime and record all provenance.
2. Confirm correction syndrome faithfulness for every graph and decoder arm.
3. Confirm static MWPM reproducibility and the promoted-core compatibility
   shims.
4. Verify the posterior matching weights exactly equal
   $\log[(1-r_e)/r_e]$, including beliefs on both sides of $1/2$.
5. Verify Python and Numba recurrences give identical marginals, iterations,
   convergence flags, LLR weights, and corrections on registered samples.
6. At $q=0$, verify that the sampled herald is identically zero and document
   the distinction between static MWPM and syndrome-only BP+MWPM.
7. At $q=1$ on honeycomb, verify that $(S,H)$ reconstructs the detector degree
   category $0,1,2,3$; record the remaining edge/logical ambiguity rather than
   treating degree reconstruction as error reconstruction.

On tiny graphs, enumerate the exact posterior over errors and compute:

- Bayes-optimal logical-MAP LER;
- conditional logical entropy $H(\lambda\mid S,H)$;
- posterior edge log loss and Brier score;
- the gap between exact logical MAP and BP+MWPM.

Run this oracle study at $q=0,0.5,0.9,1$ and
$p=0.10,0.30,0.45,0.49$. It is the first direct test of whether high-$q$
observations remove logical ambiguity or whether the scalable projection is
the bottleneck.

### Phase 1 — the two physical anchors

#### Phase 1a: $q=0$ calibration

For each lattice, survey the expected MWPM crossing with discovery sizes.
Use square $p=0.04,0.06,\ldots,0.18$ and the systematically higher honeycomb
$p=0.12,0.16,\ldots,0.36$ as bounded initial grids. Plot LER versus $p$ for
every $L$, locate all adjacent-size crossings, and compare the inferred
$p_c(0)$ with the appropriate surface-code-like reference for the implemented
geometry and noise convention. The numerical $p$ values are selected and
interpreted within geometry; a square--honeycomb LER comparison at the same
$p$ is not an estimator of decoder quality. Disagreement triggers a
geometry/logical-cut audit before any herald claim.

#### Phase 1b: $q=1$ ideal-herald anchor

Repeat the matched scan with the corrected herald decoder. Because the strong
conjecture places the boundary near $1/2$, the initial grid must include
high-noise sentinels $p=0.30,0.40,0.45,0.48,0.49$ in addition to points near
the $q=0$ crossing. Do not retain the old square $p\le0.22$ or honeycomb
$p\le0.30$ bounds if all observed size trends remain decodable there.

Classify the anchor as:

- a bracketed finite crossing;
- ceiling-compatible through $p=0.49$;
- entirely undecodable over the tested range;
- multiple/re-entrant crossings; or
- unresolved finite-size behavior.

Estimate $\Delta p_c=p_c(1)-p_c(0)$ only when both boundaries are finite. If
$q=1$ is ceiling-censored, report a lower bound on the uplift instead.

**Execution status, 2026-08-27.** The 1000-shots/cell discovery wave is
complete for $L=5,7,9,11,13$. Honeycomb is ceiling-compatible through
$p=0.49$ over these tested sizes, giving the finite-size lower bound
$p_c(q=1)\ge0.49$. Square remains unresolved: the nominal $L=5/7$, $7/9$,
and $9/11$ crossings span $0.344$--$0.438$, while $L=11/13$ is not physically
bracketed on the tested grid. No single square threshold may be promoted from
this wave. The next square transition is a balanced 3000-shots/cell boundary
confirmation followed by held-out $L=15$, as already required by the shot
allocation rules; the honeycomb result likewise requires high-$p$ confirmation
before a ceiling claim stronger than the current lower bound.

### Phase 2 — dense two-dimensional scouting

Use the mandatory skeleton

\[
q\in\{0,0.05,0.10,\ldots,0.95,1.00\}.
\]

At each $q$, include:

1. two guard points below the predicted crossing;
2. two guard points above it;
3. the current crossing estimate;
4. high-$p$ sentinels at $p=0.45$ and $0.49$ whenever the predicted boundary
   exceeds $0.35$ or is unbracketed.

Initialize a new $q$ from neighboring completed $q$ values, but impose the
universal domain $0.02\le p\le0.49$. At least three common $p$ points must be
shared by neighboring $q$ values so that changes with $q$ are directly paired
and not inferred only from interpolation.

The scouting output is a cell-classification map, not yet a smooth phase
boundary. Each sampled cell is labelled decodable, undecodable, or unresolved
from adjacent-size trends with uncertainty.

**Registered common-grid execution wave (2026-08-27).** The full skeleton is
run as immutable `(lattice,q)` shards using five seeds and 200 shots per seed.
To make all q shards safely parallel while retaining direct neighboring-q
comparisons, every square shard shares
`p={0.04,0.08,0.12,0.16,0.20,0.24,0.28,0.32,0.36,0.40,0.45,0.49}` and every
honeycomb shard shares
`p={0.08,0.12,0.16,0.20,0.24,0.28,0.32,0.36,0.40,0.45,0.49}`. This broad
wave is explicitly scouting rather than a final threshold fit. It uses the
same damping-BP plus posterior-LLR decoder at q=0 as at intermediate q; the
existing q=0 static-MWPM result remains a separate reference rather than the
q=0 endpoint of this decoder-specific curve. The exact manifest is
`manifests/manifests/phase2-scout-manifest.json`.

**Researcher decision (edited 2026-08-28): resume the full q-skeleton phase
diagram, honeycomb first.** Thread-007 selects $q=0,0.05,\ldots,1.00$ on the
honeycomb lattice at $L=7,9,11$ before any square campaign. The restarted
discovery uses one fresh source cohort, compiled stable-sort
residual-priority-80 BP, posterior-LLR PyMatching, five new seeds, 1000
shots/cell, and the registered common p grid. Its 21 immutable shards contain
693,000 planned raw observations and use unique names; no legacy
synchronous-40 shard or prior residual-80 pilot may be pooled into it.

Crossings are fluctuation-aware: independently resample complete nested-p
seed trajectories within each size, retain no-crossing and multiple-crossing
replicates, and quote a conditional central 90% interval only for the matching
directed crossing topology. A cell trend is signed only when the 90% interval
for $\mathrm{LER}_{L}-\mathrm{LER}_{L+2}$ excludes zero. Adaptive p midpoints
target sign-uncertain cells and crossing intervals wider than 0.01. Promotion
requires both L7/L9 and L9/L11 to have at least 90% single-crossing support,
compatible 90% intervals, and final width at most 0.01; otherwise report the
boundary as unresolved or topology-unstable.

The dispatcher/analyzer are manifest-driven, enforce unique campaign names
plus residual-priority metadata, and fail closed on syndrome fidelity and
start/end source stability. The production wave completed all 21 shards and
693,000 raw observations. All shards passed the analyzer's raw-count,
gzip/SHA-256, syndrome-fidelity, configuration, runtime, and start/end source
checks. Dropbox reverted 11 finalized gzip paths to their hidden atomic names;
the tested recovery tool restored only candidates with the exact
summary-declared SHA-256 and row count. The final combined suite passes 19/19
tests.

The topology-aware 20,000-replicate analysis classifies q=0.95 and q=1.00 as
ceiling-compatible and every q<=0.90 as unresolved. For q<=0.85, point curves
and bootstrap trajectories commonly contain multiple directed crossings; at
q=0.90 neither adjacent pair has a point crossing, but high-p size trends are
not sufficiently sign-stable for the ceiling gate. Therefore this discovery
does not report p_c(q), q_c, or a q_c confidence interval. Its highest-value
adaptive target is the q=0.90--0.95 transition band, with more independent
seed clusters before any q midpoint is added. Registered contract, recovery,
analysis, and figure:
[`manifests/phase2-residual80-q-skeleton-manifest-2026-08-28.json`](manifests/phase2-residual80-q-skeleton-manifest-2026-08-28.json).
[`results/phase2-residual80-honeycomb-q-skeleton-preflight-2026-08-28.json`](results/phase2-residual80-honeycomb-q-skeleton-preflight-2026-08-28.json).
[`results/phase2-residual80-q-skeleton-2026-08-28-atomic-raw-recovery.json`](results/phase2-residual80-q-skeleton-2026-08-28-atomic-raw-recovery.json).
[`results/phase2-residual80-q-skeleton-2026-08-28-analysis.json`](results/phase2-residual80-q-skeleton-2026-08-28-analysis.json).
[`figures/phase2-residual80-q-skeleton-2026-08-28-honeycomb-phase-map.png`](figures/phase2-residual80-q-skeleton-2026-08-28-honeycomb-phase-map.png).

### Phase 3 — adaptive refinement in both p and q

**Registered high-q fluctuation diagnostic (2026-08-28).** The completed
discovery does not support blind midpoint insertion: five seed clusters leave
widespread sign changes and multiple crossing topologies. The smallest
discriminating next matrix therefore uses 20 fresh independent seed clusters
at q={0.85,0.90,0.95}, L={7,9,11}, and
p={0.32,0.36,0.40,0.425,0.45,0.47,0.49}, with 200 shots per cluster. The
three shards contain 252,000 planned observations and are analyzed as a
standalone cohort. q=0.85 guards the inconsistent finite side, q=0.90 tests
the unresolved endpoint, and q=0.95 independently checks the ceiling side.
No q=0.925 midpoint is authorized until the two endpoint classifications pass
the registered 90% gates. The explicit-q/4000-shots analyzer path, dispatcher,
runner, and storage recovery pass 21/21 tests plus a three-job dry run.
Manifest and preflight:
[`manifests/phase3-residual80-honeycomb-highq-refinement-manifest-2026-08-28.json`](manifests/phase3-residual80-honeycomb-highq-refinement-manifest-2026-08-28.json).
[`manifests/phase3-residual80-honeycomb-highq-refinement-preflight-2026-08-28.json`](manifests/phase3-residual80-honeycomb-highq-refinement-preflight-2026-08-28.json).

**Production validation (2026-08-28): complete.** All three workers exited
zero. Each q shard contains 84,000 rows, for 252,000 total observations; all
252,000 corrections are syndrome faithful. All raw gzip hashes and counts,
configuration/runtime fields, common source hashes, and start/end source
stability pass. All three raw files finalized normally, so no storage recovery
was needed. No crossing interpretation was performed in this transition.
Validation:
[`results/phase3-residual80-honeycomb-highq-refinement-validation-2026-08-28.json`](results/phase3-residual80-honeycomb-highq-refinement-validation-2026-08-28.json).

**Topology-aware analysis (2026-08-28): complete, unresolved.** The 20,000
seed-trajectory bootstrap replicates classify q=0.85, 0.90, and 0.95 all as
unresolved. L7/L9 has no point crossing at any q and remains decodable across
the high-p grid. L9/L11 has one point crossing at q=0.85 near p=0.4206
(conditional 90% interval [0.3514,0.4359]), one at q=0.90 near p=0.4686
([0.3860,0.4806]), and five at q=0.95. The q=0.90 L9/L11 bootstrap has 27.1%
no-crossing and 31.7% multiple-crossing outcomes; q=0.95 has 68.7% multiple
crossings. Thus neither endpoint passes the topology gate, and the earlier
five-cluster q=0.95 ceiling label is not confirmed.

The limiting signal is now decoder/finite-size behavior rather than ordinary
cell-count noise. At q=0.95 the L11 BP convergence fraction falls from 8.6%
at p=0.32 to about 4.0% at p=0.47--0.49, compared with 18--24% for L9; q=0.90
L11 reaches only 6.0--10.1%. A q=0.925 midpoint would interpolate between two
unresolved endpoints and is therefore still gated. The next prerequisite is a
bounded matched convergence-cap diagnostic on the high-q L11 bottleneck,
before adding q points or L13. Analysis and figure:
[`results/phase3-residual80-honeycomb-highq-refinement-4000-2026-08-28-analysis.json`](results/phase3-residual80-honeycomb-highq-refinement-4000-2026-08-28-analysis.json).
[`figures/phase3-residual80-honeycomb-highq-refinement-4000-2026-08-28-honeycomb-phase-map.png`](figures/phase3-residual80-honeycomb-highq-refinement-4000-2026-08-28-honeycomb-phase-map.png).

**Registered convergence-cap prerequisite (2026-08-28).** Use 64 fresh
matched observations in each honeycomb L=11 cell at q={0.85,0.90,0.95} and
p={0.40,0.45,0.49}. Compare stable-sort residual-priority BP caps 80, 160,
and 320 while holding every other decoder and observation field fixed. The
matrix contains 576 observations and 1728 decodes. It records convergence,
iterations, final residual, posterior log loss/Brier score, runtime,
correction disagreement, syndrome fidelity, and descriptive logical
rescues/harms with paired central 90% bootstrap intervals. The runner fails
closed on syndrome mismatch or start/end source drift. This is a mechanism
diagnostic only; it cannot change the primary cap or phase boundary. The
combined suite and public-interface smoke test pass 24/24. Preflight:
[`results/phase3-honeycomb-highq-l11-convergence-cap-preflight-2026-08-28.json`](results/phase3-honeycomb-highq-l11-convergence-cap-preflight-2026-08-28.json).

**Completed convergence-cap diagnostic (2026-08-28).** Across 576 matched
observations, fixed-point convergence rises sharply from 67 at cap 80 to 308
at cap 160 and 442 at cap 320, so the cap-80 convergence flag is genuinely
truncation-sensitive. However, every arm has the same 116 logical failures;
the 30 and 22 successive correction disagreements produce zero logical
rescues and zero introduced failures, while aggregate posterior log loss is
stable to about $10^{-5}$. Cap 320 still leaves 134 observations
nonconverged, including 27--34 of 64 in each q=0.95 cell. Therefore retain
residual-priority-80 as the primary registered decoder and do not restore a
crossing or phase claim from the convergence flag alone. The next bounded
prerequisite is a fresh matched L11/L13 correction-to-scaling wave at
q={0.85,0.90,0.95}; q=0.925 and square remain gated. Results and analysis:
[`results/phase3-honeycomb-highq-l11-convergence-cap-2026-08-28.json`](results/phase3-honeycomb-highq-l11-convergence-cap-2026-08-28.json),
[`results/phase3-honeycomb-highq-l11-convergence-cap-2026-08-28-analysis.json`](results/phase3-honeycomb-highq-l11-convergence-cap-2026-08-28-analysis.json).

**Registered L11/L13 correction-to-scaling wave (2026-08-28).** Hold the
primary residual-priority-80 posterior-LLR decoder fixed and run honeycomb
L={11,13} at q={0.85,0.90,0.95} on the same seven-point high-p grid. Twenty
fresh seed trajectories with 200 shots each give 4000 shots/cell and 168,000
planned raw observations across three shards. The cohort is analyzed
independently with 20,000 trajectory-bootstrap replicates and central 90%
intervals, retaining no/single/multiple-crossing topology. This is the
smallest direct check of whether the unresolved L9/L11 behavior persists at
the next size pair; it does not authorize q=0.925, square, a cap change, or a
phase claim. The 26-test suite and three-job dry run pass. Manifest and
preflight:
[`manifests/phase4-residual80-honeycomb-highq-l11-l13-scaling-manifest-2026-08-28.json`](manifests/phase4-residual80-honeycomb-highq-l11-l13-scaling-manifest-2026-08-28.json),
[`manifests/phase4-residual80-honeycomb-highq-l11-l13-scaling-preflight-2026-08-28.json`](manifests/phase4-residual80-honeycomb-highq-l11-l13-scaling-preflight-2026-08-28.json).

**L11/L13 production validation (2026-08-28): complete.** All three q shards
exited zero and contain 56,000 rows each, for 168,000 total observations.
Every correction is syndrome faithful; raw gzip hashes/counts, configuration,
runtime, a common source cohort, and each shard's start/end source stability
all pass. All raw files finalized normally, so no storage recovery was
needed. This transition validates the replacement data only; the registered
crossing analysis remains pending:
[`results/phase4-residual80-honeycomb-highq-l11-l13-scaling-validation-2026-08-28.json`](results/phase4-residual80-honeycomb-highq-l11-l13-scaling-validation-2026-08-28.json).

**L11/L13 topology analysis (2026-08-28): complete, unresolved.** The
20,000-replicate central-90% seed-trajectory bootstrap finds a q=0.85 point
crossing at p=0.4136 with conditional interval [0.3258,0.4512], close to the
earlier L9/L11 estimate 0.4206; however, 25.3% of bootstrap trajectories have
multiple crossings. At q=0.90 the point crossing drifts upward to p=0.4825
with interval [0.3223,0.4875], while 26.7% of trajectories have no crossing
and 17.0% have multiple crossings. At q=0.95 L11/L13 has no point crossing,
but the p=0.49 size trend remains unresolved with delta=0.0025 and central
90% interval [-0.0075,0.01275]. Thus the analyzer's q=0.85/q=0.90 finite
labels do not constitute promoted phase boundaries, q=0.95 is not
ceiling-compatible, and q=0.925 remains gated.

L13 fixed-point convergence is only 1.2--2.4% throughout q=0.90 and
0.65--2.65% throughout q=0.95, reaching 0.825% at q=0.95,p=0.49. Before
spending more shots on adaptive p refinement, the cheapest discriminating
prerequisite is the already in-scope L13 version of the matched cap
diagnostic. Analysis, interpretation, and figure:
[`results/phase4-residual80-honeycomb-highq-l11-l13-scaling-4000-2026-08-28-analysis.json`](results/phase4-residual80-honeycomb-highq-l11-l13-scaling-4000-2026-08-28-analysis.json),
[`results/phase4-residual80-honeycomb-highq-l11-l13-scaling-interpretation-2026-08-28.json`](results/phase4-residual80-honeycomb-highq-l11-l13-scaling-interpretation-2026-08-28.json),
[`figures/phase4-residual80-honeycomb-highq-l11-l13-scaling-4000-2026-08-28-honeycomb-phase-map.png`](figures/phase4-residual80-honeycomb-highq-l11-l13-scaling-4000-2026-08-28-honeycomb-phase-map.png).

**Registered L13 convergence-cap prerequisite (2026-08-28).** Repeat the
matched L11 mechanism design at L=13 using q={0.85,0.90,0.95},
p={0.40,0.45,0.49}, 64 fresh observations per cell, and otherwise-identical
stable-sort residual-priority caps 80/160/320. The 576 observations and 1728
decodes directly test whether near-zero L13 convergence changes corrections
or logical outcomes, rather than assuming the L11 null logical effect
transfers to L13. The runner is parameterized without changing the decoder;
27/27 tests plus an accelerated public-interface smoke run pass. This remains
a mechanism diagnostic and cannot itself change the primary cap or phase
claim. Preflight:
[`manifests/phase4-honeycomb-highq-l13-convergence-cap-preflight-2026-08-28.json`](manifests/phase4-honeycomb-highq-l13-convergence-cap-preflight-2026-08-28.json).

**Completed L13 convergence-cap diagnostic (2026-08-28).** Across 576 fresh
matched observations, convergence rises from 19 at cap 80 to 199 at cap 160
and 342 at cap 320. Nevertheless, all three arms have exactly 87 logical
failures. The 57 and 45 successive correction disagreements produce zero
rescues and zero introduced failures in every cell, while aggregate posterior
scores remain stable at roughly the 1e-6 scale. Even cap 320 leaves 234 cases
nonconverged and reaches only 13--23 of 64 at q=0.95. Thus near-zero cap-80
convergence is a real truncation of the fixed-point flag, but this matched
test provides no logical-performance reason to change the primary cap. Keep
the phase evidence explicitly decoder-operational. The next bounded step is a
fresh, fluctuation-efficient adaptive-p confirmation with more independent
L11/L13 seed clusters. Result and analysis:
[`results/phase4-honeycomb-highq-l13-convergence-cap-2026-08-28.json`](results/phase4-honeycomb-highq-l13-convergence-cap-2026-08-28.json),
[`results/phase4-honeycomb-highq-l13-convergence-cap-analysis-2026-08-28.json`](results/phase4-honeycomb-highq-l13-convergence-cap-analysis-2026-08-28.json).

**Registered cluster-rich adaptive-p confirmation (2026-08-28).** Freeze
residual-priority-80 and run fresh L={11,13} trajectories at
q={0.85,0.90,0.95} on the common p=0.39:0.01:0.49 grid. Forty independent
100-shot seed clusters preserve 4000 shots/cell while doubling the trajectory
count available to the fluctuation-aware bootstrap; the three shards contain
264,000 planned observations. The grid brackets the q=0.85 finite-like
crossing, resolves the q=0.90 ceiling-adjacent region, and repeats q=0.95's
high-p sign test without outcome-dependent q-specific grids. This independent
cohort is compared, not pooled, with the previous wave. The 29-test suite and
three-job dry run pass. q=0.925, L15, and square remain gated. Manifest and
preflight:
[`manifests/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-manifest-2026-08-28.json`](manifests/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-manifest-2026-08-28.json),
[`manifests/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-preflight-2026-08-28.json`](manifests/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-preflight-2026-08-28.json).

**Production validated (2026-08-28).** The three registered shards completed
with 88,000 raw observations each, for 264,000 total. All 264,000 decoded
corrections reproduce their recorded syndrome; gzip record counts and SHA-256
digests pass, every shard is start/end source-stable, all three share one
runtime/source cohort, and no atomic recovery was required. This transition
establishes a valid independent dataset only; it does not inspect or promote
crossing topology. Next run the registered 20,000-replicate central-90%
seed-trajectory analysis before considering q=0.925, L15, or square:
[`results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-validation-2026-08-28.json`](results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-validation-2026-08-28.json).

**Independent topology analysis (2026-08-28): complete, unresolved.** The
registered 20,000-replicate analysis does not pass the cross-cohort
reproducibility gate. At q=0.85 the confirmation has three point crossings
and 68.39% multiple-crossing bootstrap topology, rather than reproducing one
finite crossing. At q=0.90 the point estimate moves from 0.4825 to 0.4575 and
the intervals overlap, but only 33.15% of confirmation trajectories have
exactly one crossing. At q=0.95 all eleven cells are locally decodable and the
p=0.49 delta is 0.01325 with central 90% interval [0.0040,0.0225], whereas
the previous independent cohort's p=0.49 interval crossed zero. The cohorts
are not pooled: none of q=0.85,0.90,0.95 promotes p_c or ceiling status, and
q=0.925, L15, and square remain gated. The next bounded transition is a
trajectory-preserving heterogeneity analysis at the four shared p values
p=0.40,0.45,0.47,0.49:
[`results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-4000-2026-08-28-analysis.json`](results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-4000-2026-08-28-analysis.json),
[`results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-interpretation-2026-08-28.json`](results/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-interpretation-2026-08-28.json),
[`figures/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-4000-2026-08-28-honeycomb-phase-map.png`](figures/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-4000-2026-08-28-honeycomb-phase-map.png).

**Two-cohort heterogeneity diagnostic (2026-08-28): complete.** A fresh
20,000-replicate bootstrap compares the independent cohorts only at their
four actually shared p values, 0.40,0.45,0.47,0.49. Complete seed trajectories
are resampled independently by size and cohort, and the statistic is the
between-cohort change in LER(11)-LER(13). None of the 12 q-by-p intervals
excludes zero. At the disputed q=0.95,p=0.49 cell the confirmation-minus-old
change is 0.01075 with central 90% interval [-0.0030,0.02425]. Thus the
cohort-local topology changes are compatible with seed-trajectory fluctuation,
not resolved systematic drift. This still does not satisfy replication or
authorize pooling. The next bounded step is to register the smallest third-
cohort adjudication matrix covering all three unresolved q branches with p
locations frozen before outcomes:
[`results/phase4-residual80-honeycomb-highq-two-cohort-heterogeneity-2026-08-28.json`](results/phase4-residual80-honeycomb-highq-two-cohort-heterogeneity-2026-08-28.json).

#### Adaptive p rule

For each $(\text{lattice},q)$, fit the discovery LER curves without assuming a
single crossing. If exactly one crossing is bracketed, sample the midpoint of
the interval contributing most to its uncertainty. If the crossing lies
outside the sampled range, extend toward it without exceeding $[0.02,0.49]$.
If all size trends remain decodable, move upward through
$p=0.40,0.45,0.48,0.49$. If all remain undecodable, move downward. Multiple
or inconsistent crossings receive points between every conflicting adjacent
pair and are never collapsed to one threshold by a monotone fit.

Stop p-refinement only when one of the following holds:

- the 90% interval for a finite $p_c(q)$ is narrower than 0.01;
- the point is ceiling-compatible at $p=0.49$ with the required high-$p$
  confirmation;
- the registered shot/location cap is reached and the result is unresolved.

#### Adaptive q rule and q_c search

Retain the full $\Delta q=0.05$ skeleton. Add midpoint values around any
interval where:

- a finite boundary becomes ceiling-censored;
- $p_c(q)$ changes by more than 0.03 between neighbors;
- high-$p$ size trends change sign;
- decoder convergence or performance becomes nonmonotone.

Refine to $\Delta q=0.025$, and to $0.0125$ only for the final interval
containing a candidate $q_c$. A candidate $q_c$ must be bracketed by at least
one $q$ with a finite high-$p$ crossing and two larger $q$ values independently
classified as ceiling-compatible.

### Phase 4 — fresh confirmation and finite-size scaling

Freeze all adaptively selected $(q,p)$ locations. Generate a fresh,
non-overlapping confirmation seed stream at $L=7,9,11,13$, then reveal the
held-out $L=15$ results. Discovery data choose locations; confirmation data
support the primary claims. Report both streams and their consistency.

For each $q$, fit finite-size scaling models of the form

\[
P_L(p,q)=F_q\!\left((p-p_c(q))L^{1/\nu_q},L^{-\omega_q}\right)
\]

with binomial likelihood. Use pairwise crossings as transparent diagnostics
and a low-order logistic/spline response with correction-to-scaling as the
primary model. Do not force $p_c(q)$ or LER to be monotone unless the raw
curves pass monotonicity checks; report monotone fits only as sensitivity
analyses.

Cluster-bootstrap seeds and master observations, preserving matched decoder,
$p$, and $q$ structure. Report intervals for every $p_c(q)$, adjacent-size
crossing drift, $\nu_q$ when identifiable, and leave-one-size-out results.

## Testing the finite-qc hypothesis

Fit and compare two explicit boundary families:

1. **Bounded model:** a smooth $p_c(q)<1/2$ for all $q\le1$.
2. **Ceiling model:** a smooth increasing branch below $q_c$ and
   $p_c(q)=1/2$ for $q\ge q_c$, treating high-$q$ observations as censored
   lower bounds when no crossing occurs below $0.49$.

Compare held-out predictive likelihood, bootstrap stability, and sensitivity
to excluding $p=0.49$ or $L=15$. A $q_c$ estimate is reportable only when the
ceiling model predicts held-out data better, the bracketing rule above is
satisfied, and high-$p$ LER decreases across all confirmation sizes. Otherwise
report either a finite boundary or “no resolved $q_c$.”

The small-graph oracle separates two interpretations:

- Oracle improves strongly while BP+MWPM fails: decoder/projection-limited
  boundary.
- Oracle retains large logical entropy at high $q,p$: observation-model
  limitation, evidence against the strong conjecture.

Tiny graphs cannot establish the asymptotic phase, but they prevent an
algorithmic failure from being misreported as an information-theoretic one.

## Phase-diagram output

Produce separate square and honeycomb figures with $q$ on the horizontal axis
and $p$ on the vertical axis. Show:

- every sampled $(q,p)$ location;
- decodable, undecodable, and unresolved cells using distinct markers;
- the inferred finite $p_c(q)$ with 95% uncertainty;
- arrows/lower bounds for ceiling-censored values;
- a candidate $q_c$ band only if its registered criteria pass;
- Phase 1 anchors and high-$p$ sentinels;
- the exact-oracle/scalable-decoder distinction in an accompanying panel.

Never paint an unmeasured region as a phase merely by spline interpolation.
The background shading follows only evidence-supported classifications and is
hatched where extrapolated or unresolved.

## Failure cases and decisions

| Observed pattern | Interpretation | Next action |
|---|---|---|
| One stable crossing | Finite operational boundary | Refine p, then confirm at larger L |
| No crossing; larger L always better through 0.49 | Ceiling-compatible | Add shots, q neighbors, L=15; report lower bound |
| No crossing; larger L always worse | Boundary below range or decoder failure | Extend p downward; audit BP/oracle gap |
| Adjacent-size crossings drift coherently | Corrections to scaling | Add L=13,15 and fit drift |
| Crossings conflict or multiply | Re-entrance or unstable decoder | Add intervening p points; do not quote one pc |
| More q worsens scalable decoder | Projection/BP pathology | Check exact oracle and convergence; retain nonmonotone data |
| Square and honeycomb disagree | Geometry dependence | Report separately; do not average |
| Runtime/provenance gate fails | Invalid experiment | Stop before writing result artifacts |

## Claim boundary and completion criteria

Lab 003 is complete only when:

1. All registered raw shot records, selection logs, runtime provenance, and
   confirmation seeds are preserved in machine-readable artifacts.
2. $q=0$ reproduces a defensible surface-code-like calibration for both
   geometries.
3. Corrected $q=1$ LER-versus-p curves and finite/censored boundary estimates
   are reported with adequate shots and held-out sizes.
4. The full $\Delta q=0.05$ skeleton and all registered adaptive q points are
   measured with adaptive p targeting.
5. Separate square and honeycomb phase diagrams display sampled cells,
   uncertainties, unresolved regions, and any censoring honestly.
6. The bounded-boundary and finite-$q_c$ hypotheses are compared on fresh
   confirmation data.
7. Any claimed $q_c$, threshold uplift, or ceiling-compatible phase satisfies
   the explicit criteria above. Otherwise the report states which hypothesis
   was rejected or remains unresolved.

All reported boundaries remain decoder- and model-specific operational
finite-size results unless subsequent work establishes asymptotic scaling and
physical-model robustness.

### Phase B6 posterior-predictive measurement-design gate

Before registering another campaign, compare three bounded designs on the
four persistent gray cells using the current Jeffreys-Beta posterior as the
predictive distribution: 1000 new shots at L=5/13 only; 1000 new shots at all
five sizes; and balancing every size to 3000 total shots. For every design and
cell, estimate the probability of crossing the existing 0.90 slope-sign gate,
the resolved direction, remaining ambiguity, posterior sign-entropy change,
and latent-direction disagreement. The diagnostic must preserve the exact
Phase B6 source hash, use fixed seeds, expose Monte Carlo standard errors, and
launch no decoder jobs.

**Completed 2026-08-28.** The 8000-decode endpoint design predicts 1.535
resolved cells out of four; the 20,000-decode all-size design predicts 1.754;
and the 19,000-decode balance-to-3000 design predicts 1.797. Their expected
false-direction resolution counts are 0.079, 0.065, and 0.078, respectively.
The endpoint design is the descriptive efficiency leader at 0.192 expected
resolutions per 1000 decodes, but this diagnostic deliberately does not encode
a scientific loss function or register a follow-up campaign. Evidence:
[`results/phase-b6-honeycomb-posterior-predictive-design-2026-08-28.json`](results/phase-b6-honeycomb-posterior-predictive-design-2026-08-28.json).

### Phase B7 — endpoint-only four-cell follow-up

Register the descriptive-efficiency-leading design without selecting among
cells after outcomes: add 1000 fresh shots at L=5 and L=13 for each of the
four Phase B6 cells, using one disjoint five-seed stream and the frozen
posterior-LLR decoder. The matrix is exactly four jobs and 8000 decodes. Stop
without adding another size, cell, p/q coordinate, lattice, or changing the
0.90 classification gate.

**Registered and preflighted 2026-08-28; not launched.** The new seeds have no
overlap with any prior top-level summary seed list. The source map, Phase B6
analysis, posterior-predictive design, selection inventory, and runner source
hashes are frozen. Four output pairs are absent, and all four real command
shapes reach post-size validation under zero-shot sentinel executions without
writing output. Exact 8000-row completion, Bayesian map-count pooling, and
four-payload/227-preservation rendering gates are implemented. The full 99-test
Lab 003 suite passes. Evidence:
[`manifests/phase-b7-honeycomb-endpoint-followup-manifest-2026-08-28.json`](manifests/phase-b7-honeycomb-endpoint-followup-manifest-2026-08-28.json),
[`manifests/phase-b7-honeycomb-endpoint-followup-selection-2026-08-28.json`](manifests/phase-b7-honeycomb-endpoint-followup-selection-2026-08-28.json),
and
[`results/phase-b7-honeycomb-endpoint-followup-preflight-2026-08-28.json`](results/phase-b7-honeycomb-endpoint-followup-preflight-2026-08-28.json).

**Data completed 2026-08-28; not scientifically analyzed.** All four jobs ran
within the registered four-worker cap and produced exactly four summary/raw
pairs. The completion audit observes 8000/8000 raw rows, all 8000 corrections
reproduce their recorded syndrome, every raw digest matches its summary, and
coordinates, seeds, decoder/source fingerprints, and start/end source
stability equal the registered contract. The lifecycle is closed against a
second launch. Next run the preregistered pooled Bayesian analysis as a
separate transition:
[`results/phase-b7-honeycomb-endpoint-followup-completion-audit-2026-08-28.json`](results/phase-b7-honeycomb-endpoint-followup-completion-audit-2026-08-28.json).

**Bayesian analysis and map update completed 2026-08-28.** All four cells are
prior-stable. Only ((q,p)=(0.60,0.28)) resolves: its upward-trend posterior is
0.96611 and its central 90% slope interval is
([0.000254,0.004754]), so it becomes undecodable. The other three favored
direction probabilities are 0.75076 upward, 0.65242 downward, and 0.75523
downward and remain unresolved. Exactly four evidence payloads update, 227 are
deep-preserved, and the active map moves from 86/41/104 to 86/42/103. No
crossing statistic, interpolation, or grid expansion is used. Evidence:
[`results/phase-b7-honeycomb-endpoint-followup-analysis-2026-08-28.json`](results/phase-b7-honeycomb-endpoint-followup-analysis-2026-08-28.json),
[`results/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json),
and
[`figures/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b7-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png).

### Phase B7 frontier posterior-predictive gate

Recompute the exact four-neighbor red/green-adjacent gray frontier after the
Phase B7 label change, then compare three fixed bounded designs under the same
nested Beta-binomial posterior-predictive calculation: add 1000 shots only to
each cell's currently least-sampled distances; add 1000 at every measured
distance; or balance every measured distance to 3000 shots. Record costs,
cellwise probability of crossing the 0.90 gate, false-direction probability,
sign-entropy reduction, fixed seeds, and Monte Carlo errors. Register and
launch no data in this diagnostic transition.

**Completed 2026-08-28.** The frontier remains four cells, but resolved
((0.60,0.28)) exits and ((0.65,0.28)) enters. The 11,000-decode
raise-minimum design predicts 0.786 resolved cells, the 14,000-decode
balance-to-3000 design predicts 0.882, and the 18,000-decode all-size design
predicts 1.116. Raise-minimum has the highest descriptive efficiency at 0.0715
expected resolutions per 1000 decodes. Its cellwise resolution probabilities
are only 0.036 and 0.0049 at ((0.30,0.20)) and ((0.35,0.20)), versus 0.224
at ((0.55,0.24)) and 0.521 at ((0.65,0.28)). This low predicted yield is
part of the result; gray cells do not automatically justify unbounded shots.
Evidence:
[`results/phase-b7-honeycomb-frontier-posterior-predictive-design-2026-08-28.json`](results/phase-b7-honeycomb-frontier-posterior-predictive-design-2026-08-28.json).

### Phase B8 — fixed raise-minimum frontier follow-up

Freeze the Phase B7 descriptive-efficiency leader before observing any Phase
B8 outcome. Add 1000 shots only at each frontier cell's currently
minimum-shot distances: L=7,9,11 for ((q,p)=(0.30,0.20)),
((0.35,0.20)), and ((0.65,0.28)); L=5,13 for ((0.55,0.24)). Use one
disjoint five-seed stream, 200 shots per seed, four jobs, and exactly 11,000
decodes. Preserve—not hide—the low predicted resolution probabilities at the
first two cells. Do not change the 0.90 Bayesian direction gate, add cells or
sizes, or use a crossing statistic.

**Registered and preflighted 2026-08-28; not launched.** The frozen selection
retains the 0.786 expected resolved-cell forecast and 0.029 expected
false-direction resolutions. The seed stream is disjoint from prior top-level
summary seeds; all four output pairs are absent; and four zero-shot CLI-shape
smokes reach post-size validation without writing data. Exact 11,000-row
completion, pooled fuzzy-trend analysis, and exact four-payload rendering
gates are implemented. All 106 Lab 003 tests pass. Evidence:
[`manifests/phase-b8-honeycomb-raise-minimum-manifest-2026-08-28.json`](manifests/phase-b8-honeycomb-raise-minimum-manifest-2026-08-28.json),
[`manifests/phase-b8-honeycomb-raise-minimum-selection-2026-08-28.json`](manifests/phase-b8-honeycomb-raise-minimum-selection-2026-08-28.json),
and
[`results/phase-b8-honeycomb-raise-minimum-preflight-2026-08-28.json`](results/phase-b8-honeycomb-raise-minimum-preflight-2026-08-28.json).

**Data completed 2026-08-28; not scientifically analyzed.** All four jobs ran
within the registered four-worker cap and produced exactly four summary/raw
pairs. The completion audit observes 11,000/11,000 raw rows, all 11,000
corrections reproduce their recorded syndrome, every raw digest matches its
summary, and coordinates, seeds, decoder/source fingerprints, and start/end
source stability equal the registered contract. The manifest and existing
output-conflict guard now reject relaunch. Next run the preregistered pooled
Bayesian analysis as a separate transition:
[`results/phase-b8-honeycomb-raise-minimum-completion-audit-2026-08-28.json`](results/phase-b8-honeycomb-raise-minimum-completion-audit-2026-08-28.json).

**Bayesian analysis completed 2026-08-28; map not rendered or promoted.** All
four cells remain unresolved and all four classifications are prior-stable.
Favored-direction posterior probabilities are 0.7241 upward at
((q,p)=(0.30,0.20)), 0.6723 downward at ((0.35,0.20)), 0.6466 downward at
((0.55,0.24)), and 0.6424 upward at ((0.65,0.28)); every central 90% slope
interval contains zero. The realized zero-of-four resolution count is below
but not logically inconsistent with the preregistered expectation 0.786 from
one four-cell realization. No crossing statistic, interpolation, grid
expansion, renderer, or phase-map mutation is used. Next render the exact
four-payload evidence update as a separate transition:
[`results/phase-b8-honeycomb-raise-minimum-analysis-2026-08-28.json`](results/phase-b8-honeycomb-raise-minimum-analysis-2026-08-28.json).

**Map update reported 2026-08-28.** The renderer updates exactly the four
registered continuous-evidence payloads, and an independent actual-file
comparison verifies all other 227 cells are deep-equal to Phase B7. Because
all four classifications remain gray, the active map stays at 86 decodable,
42 undecodable, and 103 unresolved cells. The generated figure passes visual
inspection; it labels the finite-window Bayesian fuzzy-trend definition and
shows classification separately from directional log odds. Evidence:
[`results/phase-b8-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b8-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json)
and
[`figures/phase-b8-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b8-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png).

### Phase B8 frontier posterior-predictive gate

Recompute the exact red/green-adjacent gray frontier after the four Phase B8
payload updates, then compare three fixed designs that cover every branch
without extrapolating to unmeasured distances: add 1000 shots at each cell's
current finite-window endpoints; add 1000 at every measured distance; or
balance every measured distance to 4000 shots. Use the same nested
Beta-binomial fuzzy-slope posterior predictive model, fixed seeds, and Monte
Carlo error reporting. Register and launch no data in this transition.

**Completed 2026-08-28.** The frontier remains the same four cells. The 8000-
decode endpoint design predicts 0.3125 resolved cells, the 18,000-decode all-
measured-size design predicts 0.4414, and the 21,000-decode balance-to-4000
design predicts 0.5537. Endpoint-only is the descriptive efficiency leader at
0.0391 expected resolutions per 1000 decodes; even the largest design remains
below one expected resolution. No L5/L13 forecast is made for the three-size
cell because the independent-Beta model has no justified cross-distance
extrapolation. No data are registered or launched. Evidence:
[`results/phase-b8-honeycomb-frontier-posterior-predictive-design-2026-08-28.json`](results/phase-b8-honeycomb-frontier-posterior-predictive-design-2026-08-28.json).

### Phase B9 — fixed measured-endpoints follow-up

Freeze the Phase B8 descriptive-efficiency leader before observing any Phase
B9 outcome. Add 1000 shots at each cell's current finite-window endpoints:
L=5,13 for ((q,p)=(0.30,0.20)), ((0.35,0.20)), and ((0.55,0.24)); L=7,11
for the three-distance ((0.65,0.28)) cell. Use one disjoint five-seed stream,
200 shots per seed, four jobs, and exactly 8000 decodes. Preserve the low
0.3125 expected-resolution forecast; do not introduce unmeasured distances,
change the 0.90 gate, or add cells.

**Registered and preflighted 2026-08-28; not launched.** The fixed selection
retains 0.3125 expected resolved cells and 0.0234 expected false-direction
resolutions. The seed stream is disjoint from prior top-level summaries, all
four output pairs are absent, and four real zero-shot CLI-shape smokes reach
post-size validation without writing data. Exact 8000-row completion, pooled
Bayesian analysis, and exact four-payload rendering gates are implemented.
All 113 Lab 003 tests pass. Evidence:
[`manifests/phase-b9-honeycomb-measured-endpoints-manifest-2026-08-28.json`](manifests/phase-b9-honeycomb-measured-endpoints-manifest-2026-08-28.json),
[`manifests/phase-b9-honeycomb-measured-endpoints-selection-2026-08-28.json`](manifests/phase-b9-honeycomb-measured-endpoints-selection-2026-08-28.json),
and
[`results/phase-b9-honeycomb-measured-endpoints-preflight-2026-08-28.json`](results/phase-b9-honeycomb-measured-endpoints-preflight-2026-08-28.json).

**Data completed 2026-08-28; not scientifically analyzed.** All four jobs ran
within the registered four-worker cap and produced exactly four summary/raw
pairs. The completion audit observes 8000/8000 raw rows, all 8000 corrections
reproduce their recorded syndrome, every raw digest matches its summary, and
coordinates, seeds, decoder/source fingerprints, and start/end source
stability equal the contract. The manifest and output-conflict guard reject
relaunch. Next run the preregistered pooled Bayesian analysis as a separate
transition:
[`results/phase-b9-honeycomb-measured-endpoints-completion-audit-2026-08-28.json`](results/phase-b9-honeycomb-measured-endpoints-completion-audit-2026-08-28.json).

**Bayesian analysis completed 2026-08-28; map not rendered or promoted.** One
cell resolves: ((q,p)=(0.65,0.28)) has posterior downward-trend probability
0.90820 and is decodable; the uniform-prior result is 0.90849 and agrees. The
other three remain unresolved with favored-direction probabilities 0.66599
upward, 0.82971 downward, and 0.87880 downward. All four classifications are
prior-stable. The realized one-of-four resolution is recorded alongside the
preregistered 0.3125 expected-resolution forecast. No crossing statistic,
interpolation, grid expansion, renderer, or map mutation occurs. Next render
the exact four-payload evidence update as a separate transition:
[`results/phase-b9-honeycomb-measured-endpoints-analysis-2026-08-28.json`](results/phase-b9-honeycomb-measured-endpoints-analysis-2026-08-28.json).

**Map update reported 2026-08-28.** The renderer updates exactly the four
registered continuous-evidence payloads, and an independent actual-file
comparison verifies all other 227 cells are deep-equal to Phase B8. The sole
classification change is ((q,p)=(0.65,0.28)) from unresolved to decodable, so
the active map becomes 87 decodable, 42 undecodable, and 102 unresolved. The
figure passes visual inspection and continues to separate conservative class
labels from continuous directional log odds. Evidence:
[`results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json`](results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json)
and
[`figures/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png`](figures/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.png).

### Phase B9 frontier posterior-predictive gate

Recompute the exact four-neighbor red/green-adjacent gray frontier after the
Phase B9 label change, then compare three bounded designs over measured
distances only: add 1000 shots at current finite-window endpoints, add 1000 at
every measured distance, or balance measured distances to 4000 shots. Use the
same nested Beta-binomial fuzzy linear-distance-slope diagnostic, fixed seeds,
and Monte Carlo error reporting. This is a measurement-value calculation, not
a power-law LER model or an asymptotic phase-boundary fit. Register and launch
no data in this transition.

**Completed 2026-08-28.** Resolved ((q,p)=(0.65,0.28)) leaves the frontier
and unresolved ((0.65,0.32)) enters; the other three cells remain. The 8000-
decode endpoint design predicts 1.1768 resolved cells, versus 1.3154 for the
18,000-decode all-size design and 1.0713 for the 18,000-decode balance design.
Endpoint-only is the descriptive efficiency leader at 0.1471 expected
resolutions per 1000 decodes. Its four cellwise resolution probabilities are
0.0293, 0.2861, 0.4727, and 0.3887, so the stubborn ((0.30,0.20)) branch is
reported explicitly. The three-distance cell is evaluated only at measured
L=7,9,11. No data are registered or launched. Evidence:
[`results/phase-b9-honeycomb-frontier-posterior-predictive-design-2026-08-28.json`](results/phase-b9-honeycomb-frontier-posterior-predictive-design-2026-08-28.json).

### Phase B10 — fixed measured-endpoints follow-up

Freeze the Phase B9 descriptive-efficiency leader before observing Phase B10
outcomes. Add 1000 shots at each exact frontier cell's current finite-window
endpoints: L=5,13 for ((q,p)=(0.30,0.20)), ((0.35,0.20)), and
((0.55,0.24)); L=7,11 for the three-distance ((0.65,0.32)) cell. Use one
disjoint five-seed stream, 200 shots per seed, four jobs, and exactly 8000
decodes. Preserve the 1.1768 expected-resolution forecast and explicitly retain
the 0.0293 low-yield forecast at ((0.30,0.20)). Do not introduce unmeasured
distances, change the 0.90 gate, or add cells.

**Registered and preflighted 2026-08-28; not launched.** The fixed selection
retains 1.1768 expected resolved cells and 0.0625 expected false-direction
resolutions. Seeds 890001–890005 are disjoint from 125 existing summary
inventories; all four output pairs are absent; source and decoder hashes match;
and four real zero-shot CLI-shape smokes reach post-size validation without
writing data. Exact 8000-row completion, pooled Bayesian analysis, and exact
four-payload rendering gates are implemented and frozen. All 119 Lab 003 tests
pass. Evidence:
[`manifests/phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json`](manifests/phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json),
[`manifests/phase-b10-honeycomb-measured-endpoints-selection-2026-08-28.json`](manifests/phase-b10-honeycomb-measured-endpoints-selection-2026-08-28.json),
and
[`results/phase-b10-honeycomb-measured-endpoints-preflight-2026-08-28.json`](results/phase-b10-honeycomb-measured-endpoints-preflight-2026-08-28.json).

**Data completed 2026-08-28; not scientifically analyzed.** All four jobs ran
within the frozen four-worker cap and produced exactly four summary/raw pairs.
The completion audit observes 8000/8000 raw and syndrome-faithful rows; raw
digests, coordinates, seeds, decoder/source fingerprints, and source stability
all match the registered contract. The manifest and existing-output guard now
reject relaunch. Next run only the preregistered pooled Bayesian fuzzy-trend
analysis as a separate transition, without rendering or promoting a map:
[`results/phase-b10-honeycomb-measured-endpoints-completion-audit-2026-08-28.json`](results/phase-b10-honeycomb-measured-endpoints-completion-audit-2026-08-28.json).

**Bayesian boundary analysis completed 2026-08-28; no map rendered or
promoted.** One of four cells resolves: ((q,p)=(0.65,0.32)) has posterior
upward-trend probability 0.97292, a positive central 90% slope interval
[0.00106,0.01344], and is prior-stably undecodable. The other three remain
prior-stably unresolved with favored-direction probabilities 0.57753 upward,
0.83788 downward, and 0.82361 downward; all three central 90% intervals contain
zero. The realized one resolution remains distinct from the preregistered
expectation 1.1768. Under the boundary-focused correction, gray labels do not
trigger another endpoint campaign. Next preregister the three-layer
floor/saturation/transition reanalysis using existing Phase B9/B10 evidence;
launch no new data and do not render the legacy slope-only map. Evidence:
[`results/phase-b10-honeycomb-measured-endpoints-analysis-2026-08-28.json`](results/phase-b10-honeycomb-measured-endpoints-analysis-2026-08-28.json).

### Boundary-focused sampling correction

**Researcher direction applied 2026-08-28.** Retire “gray trend cell implies
more samples” as an acquisition rule. The fuzzy linear-distance slope remains
useful only in the lower transition band. Low-p/high-q cells with zero or rare
logical failures are floor-limited decodable anchors; high-p/low-q cells near
the order-one random-logical plateau are saturation-limited undecodable
anchors. Their size trends can be statistically unresolved without making the
physical phase genuinely ambiguous.

The current binary logical observable empirically saturates near LER 0.5, not
1: for example Phase B9 q=0,p=0.32–0.40 gives LERs about 0.49–0.53 across
L=7,9,11, whereas q=1,p=0.08–0.12 gives zero or nearly zero failures. These
are precisely the regimes where resolving a slope sign is a poor use of
shots. By contrast the Phase B10 targets lie on the lower red/green boundary
band and have moderate LERs: the Phase B9 source rates are about 0.24 at
((0.30,0.20)), 0.20–0.22 at ((0.35,0.20)), 0.22–0.23 at
((0.55,0.24)), and 0.32–0.35 at ((0.65,0.32)). The completed B10 data remain
valid boundary evidence, but their analysis must not automatically trigger
another same-cell campaign.

After the preregistered B10 analysis, replace the presentation and acquisition
logic with three layers: posterior floor/saturation anchors from absolute LER,
finite-window direction only inside the transition band, and uncertainty in
the row-wise lower boundary (p_c(q)). New shots are allowed only when they
reduce boundary-location uncertainty; remote interior gray cells receive zero
routine priority. Cutoffs and posterior gates must be frozen from the logical
observable and validated anchors before the redesigned map is promoted.

### Phase B11 — preregistered three-layer no-new-data reanalysis

Freeze a calibration matrix before inspecting its classifications. Under
independent Beta-binomial posteriors, test floor events in which every measured
latent LER is below epsilon for epsilon in 0.01, 0.02, 0.03, 0.05, and
saturation events in which every latent LER is within delta of the binary
random-logical limit 0.5 for delta in 0.03, 0.05, 0.075, 0.10. Cross these
with posterior gates 0.80, 0.90, 0.95. Validation anchors and the four B10
transition-exclusion cells are fixed in the manifest before analysis.

For floor and saturation separately, a rule qualifies only if it classifies
every corresponding interior validation anchor and none of the transition
cells. Select the highest qualifying posterior gate, then the smallest
tolerance; fail closed if no rule qualifies. Promote only anchors that remain
classified under both Jeffreys and uniform priors. At each q, report only the
first lower bracket between a decodable anchor and a higher-p undecodable
anchor. Direction evidence is applicable only inside that bracket. Report
bracket width as the first boundary-uncertainty object; do not interpolate a
continuous curve or select new samples in the same transition.

**Completed 2026-08-28 without new data or rendering.** Immutable hashes froze
the Phase B9 map, Phase B10 boundary update, corrected methodology, and
analyzer before classification. The deterministic calibration selected the
0.95 gate with epsilon=0.01 for the floor and delta=0.075 around 0.5 for
saturation. It promotes 25 prior-stable decodable and 64 prior-stable
undecodable anchors among 231 cells, leaving 142 cells outside the interior
anchor layers. Sixteen q rows have a discrete lower-boundary bracket; widths
are 0.04 (seven rows), 0.08 (two), 0.12 (six), and 0.16 (one). Rows q=0.80
through 1.00 have no valid two-sided bracket. Zero new decoder runs, zero new
decodes, and no map or sampling decision were produced. Three focused tests
and the full 122-test Lab 003 suite pass. Evidence:
[`manifests/phase-b11-honeycomb-three-layer-reanalysis-manifest-2026-08-28.json`](manifests/phase-b11-honeycomb-three-layer-reanalysis-manifest-2026-08-28.json)
and
[`results/phase-b11-honeycomb-three-layer-reanalysis-2026-08-28.json`](results/phase-b11-honeycomb-three-layer-reanalysis-2026-08-28.json).

### Phase B12 — presentation-only three-layer phase map

Replace the active legacy slope-only phase-map presentation using only the
hash-frozen Phase B11 output. The primary q-p raster has four direct physical
layers: green below the lower endpoint of each valid row bracket, amber
strictly inside the observed bracket, red at or above its upper endpoint, and
neutral where no two-sided bracket exists. On rows without a bracket, only
posterior-stable absolute floor/saturation anchors receive green/red color.
Absolute anchors use a cell outline rather than point or crossing markers.

The renderer must not show crosses, crossing counts, or continuously
interpolate p_c(q). It must print the finite-window claim boundary. Historical
B5-B9 slope-only files remain as provenance, but after visual verification
they are removed from active Lab-page presentation and the Phase B9 report
embed is replaced. Dashboard visibility is a separate final acceptance item.

**Reported 2026-08-28; dashboard verification pending.** The
preflight exhaustively classifies all 231 cells into 70 displayed decodable,
17 discrete-boundary, 101 displayed undecodable, and 43 no-two-sided-bracket
cells while preserving the 25/64 absolute-anchor counts. The bounded
transition contains zero decoder runs, zero decodes, and no sample selection.
The first backend invocation exited before output; the same frozen renderer
then ran under the noninteractive Agg backend. Visual inspection found and
corrected one footer/x-axis overlap without changing classification semantics;
the final figure has legible axes, legend, cell-level anchor outlines, and
claim boundary. The active report is reduced from the prior 800-line
iteration log to a 145-line current-evidence narrative and embeds only the
Phase B12 map as its phase diagram. The legacy B5-B9 phase figures remain
provenance downloads but are demoted from Lab-page presentation. Dashboard
visibility remains a separate acceptance item. Contract and evidence:
[`manifests/phase-b12-honeycomb-three-layer-map-manifest-2026-08-28.json`](manifests/phase-b12-honeycomb-three-layer-map-manifest-2026-08-28.json).
[`results/phase-b12-honeycomb-three-layer-map-preflight-2026-08-28.json`](results/phase-b12-honeycomb-three-layer-map-preflight-2026-08-28.json).
[`results/phase-b12-honeycomb-three-layer-map-render-audit-2026-08-28.json`](results/phase-b12-honeycomb-three-layer-map-render-audit-2026-08-28.json).
[`figures/phase-b12-honeycomb-three-layer-phase-map-2026-08-28.png`](figures/phase-b12-honeycomb-three-layer-phase-map-2026-08-28.png).

**Researcher interpretation correction, 2026-08-28.** Withdraw the Phase B12
categorical map from active presentation. The visualization must not decide
which phase a point belongs to. Replace it with a single continuous heatmap of
$\log[\Pr(\beta>0\mid D)/\Pr(\beta<0\mid D)]$, using a green-to-red color bar
labelled downward/upward trend evidence only. Do not draw a boundary, classify
cells, or label colors decodable/undecodable. Preserve uncensored probabilities
in machine-readable output and explicitly label any finite display clipping of
infinite or resolution-censored log odds. Phase B11/B12 artifacts remain
provenance, not active interpretation.

### Phase B13 — continuous posterior trend-evidence presentation

Use the hash-frozen Phase B9 21x11 honeycomb grid as the base and replace only
the four exact Phase B10 measured-endpoint cells. Preserve
$\Pr(\beta>0\mid D)$, $\Pr(\beta<0\mid D)$, the uncensored log odds when
available, and the original QMC censoring relation and bound. Render only

\[
\log\frac{\Pr(\beta>0\mid D)}{\Pr(\beta<0\mid D)}
\]

on a zero-centered green-neutral-red scale with $p$ horizontal and $q$
vertical. Negative/green means evidence favors a downward finite-window LER
trend; positive/red means evidence favors an upward trend. The $\pm6$ color
limit is display-only; no probability or censoring bound is altered. Do not
assign phase labels, infer a boundary, interpolate, or add point markers.

**Completed 2026-08-28 without new data.** The merge contains exactly 231
cells: 227 unchanged Phase B9 cells and the four registered Phase B10 updates.
Thirty-eight extreme cells are clipped only in the PNG color scale. The
companion JSON retains all raw probabilities and censoring metadata. Four
focused tests pass, visual inspection confirms legible axes/colorbar/footer,
and the active report/Lab metadata now promote this evidence-only figure while
B5-B12 categorical maps remain provenance downloads. Dashboard end-to-end
verification is the next independent acceptance item. Contract and evidence:
[`manifests/phase-b13-honeycomb-continuous-log-odds-map-manifest-2026-08-28.json`](manifests/phase-b13-honeycomb-continuous-log-odds-map-manifest-2026-08-28.json),
[`results/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.json`](results/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.json), and
[`figures/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.png`](figures/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.png).

**Dashboard acceptance verified 2026-08-28.** The live public route, Lab API,
report embed, and PNG asset all pass. The served PNG SHA-256 is
`416fa2e3151c7b90ae444bec91e8a7ed26b4f096857a16d2cd69ba45c453d66b`,
identical to the Phase B13 render audit. Every B5–B12 categorical figure
matched by the verifier is a provenance download, not a page result. The
dashboard Python suite passes 22/22, including three new Lab 003 presentation
contracts; the two directly relevant frontend contracts pass. The full
frontend suite still has one unrelated pre-existing Wiki math-markup failure
in `wiki/methods/fault-tolerant-anyonic-decoding.md`, which does not affect the
Lab route, API, or asset. The in-app browser runtime itself could not initialize
because its filesystem glob parser rejected the square brackets in the
workspace path, so the audit exercised the same live HTTP endpoints directly.
Evidence:
[`results/phase-b13-dashboard-e2e-audit-2026-08-28.json`](results/phase-b13-dashboard-e2e-audit-2026-08-28.json).

### Phase B14 — lower-transition two-branch acquisition matrix

The next fork is experimental design, not a human ranking question. Comparing
same-window shots with new distance leverage by posterior prediction would
require an unproved cross-size generative model. Instead, register the
smallest empirical matrix that measures both branches at the same cells.

The deterministic no-new-data selector uses the current B13 continuous trend
evidence and the frozen B9 count vectors. It requires an existing L=7,9,11
window, mean observed LER in [0.05,0.45], binary trend-sign entropy at least
0.5 nats, p<=0.32, and an adjacent-p log-odds sign contrast on the same q row.
It then chooses the maximum-combined-entropy adjacent pair in each of the
predeclared q strata [0,0.4] and [0.6,0.8].

**Preflight passed 2026-08-28; no data launched.** The selected cells are
(q,p)=(0.20,0.16),(0.20,0.20),(0.70,0.28),(0.70,0.32). At every cell the
matrix measures two independent branches:

- distance leverage: 500 fresh shots at each of L=5 and L=13;
- same-window precision: 500 fresh shots at each of L=7,9,11.

The eight-job matrix costs exactly 10,000 decodes and uses disjoint five-seed
streams. Analysis will compare posterior trend-sign entropy reduction per
1000 new decodes, continuous log-odds change, and the 90% slope interval for
each branch and their combination. It will not classify a cell, infer a
boundary, or adapt the matrix after seeing outcomes.

The non-overwriting dispatcher, exact eight-pair completion auditor, and
branch-separated analyzer are implemented and tested. Distance and precision
branches have distinct output stems and job-local seed streams. The analyzer
keeps base, distance-only, precision-only, and combined posterior evidence
separate and emits no cell/phase label or boundary. Source, selection,
designer, seed-overlap, branch, budget, and output-conflict gates pass. Because
the B13 evidence file is reproducibly regenerated with a fresh timestamp, its
gate hashes canonical JSON excluding only `generated_at`; every scientific
value and provenance field remains protected. All eight zero-shot public-CLI
shape checks reach the registered post-size validation, fail at the intended
positive-shot guard, and write no output. The full Lab 003 suite passes
137/137 tests. A valid hash-bound preflight artifact now makes the fixed
eight-job launch eligible, but this transition launched zero production jobs
and zero decodes.

**Rerun complete and audited 2026-08-28; analysis not yet performed.** The
dispatcher executed exactly the eight registered jobs with at most four
workers and stopped at 10,000 decodes. All eight summary/raw pairs are present.
The completion audit verifies 10,000/10,000 raw rows, 10,000/10,000
syndrome-faithful corrections, exact branch-specific coordinates, size
windows, seed streams and shot counts, raw SHA-256 values, posterior-LLR
decoder configuration, frozen source hashes, and start/end source stability.
No cell, branch, size, seed, shot, decoder, or matrix parameter changed, and
no scientific result was inspected or interpreted in this execution
transition. The next bounded transition is the preregistered branch-separated
continuous-evidence analysis. Before authorizing any further phase-map
sampling after that analysis, perform a program-level priority review: compare
the herald-aware decoder against matched syndrome-only controls and separate
herald-information limits from BP/MWPM approximation or convergence limits.
Evidence:
[`results/phase-b14-honeycomb-two-branch-selection-2026-08-28.json`](results/phase-b14-honeycomb-two-branch-selection-2026-08-28.json) and
[`manifests/phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json`](manifests/phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json), and
[`results/phase-b14-honeycomb-two-branch-preflight-2026-08-28.json`](results/phase-b14-honeycomb-two-branch-preflight-2026-08-28.json), and
[`results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json`](results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json).

### Phase B15 — constrained neural versus spline comparison

**Researcher decision recorded 2026-08-28.** Run both the
constrained single-valued width-three neural boundary summary and the
interval-constrained penalized cubic-spline summary, then show their results
side by side. Neither branch is privileged in advance. Both must use identical
eligible q rows, B11/B14-compatible brackets, transition evidence, bootstrap
resamples, hold-out folds, and display censoring. Compare held-out sign log
loss, bracket violations, roughness, envelope width, valid-row coverage,
instability, runtime, and pairwise curve displacement.

B14 analysis and the resulting data-currency merge are a hard prerequisite:
B15 must not fit the superseded B13-only field. After that prerequisite, freeze
one no-new-decoder-data comparison manifest, implement and verify both public
branches, produce a machine-readable score table and side-by-side figure, and
report disagreements without automatically choosing a physical boundary.
Neither curve may be called a thermodynamic phase boundary or extrapolated
into unbracketed q rows. Full method and acceptance contract:
[`results/phase-b15-neural-boundary-method-note-2026-08-28.md`](results/phase-b15-neural-boundary-method-note-2026-08-28.md).

**Completed and visually audited 2026-08-28.** The B14 analysis first merged
the four registered combined posteriors into the current 231-cell field. B15
then fit both peer branches to the same 80 transition observations and sixteen
audited two-sided q-row brackets. The neural branch has held-out weighted log
loss 0.260 +/- 0.017 versus 0.287 +/- 0.021 for the spline, is smoother by the
registered curvature functional, is about 67 times slower, and has a slightly
wider propagated envelope. Their full curves differ by 0.0067 in p on average
and at most 0.026. No winner, cell phase, or thermodynamic boundary is declared.
The 90% bands propagate independent Jeffreys-Beta measurement uncertainty and
model refitting; they are explicitly not seed-cluster bootstrap intervals or
asymptotic-boundary confidence intervals. The active report now shows the B15
collaborator figure; prior phase-map figures remain provenance only. Evidence:
[`results/phase-b14-honeycomb-two-branch-analysis-2026-08-28.json`](results/phase-b14-honeycomb-two-branch-analysis-2026-08-28.json),
[`results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json`](results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json),
[`results/phase-b15-neural-spline-comparison-2026-08-28.json`](results/phase-b15-neural-spline-comparison-2026-08-28.json), and
[`figures/phase-b15-neural-spline-boundary-comparison-2026-08-28.png`](figures/phase-b15-neural-spline-boundary-comparison-2026-08-28.png).

### Phase B16 — strong-smoothing and domain-closure correction

**Researcher correction recorded and applied 2026-08-28.** Both B15 curves
contain visible kinks on scales below the approximately 0.05 p/q measurement
resolution, use an unnecessarily dense 151-point support, and terminate at
q=0.75 rather than closing on plot boundaries. They are therefore withdrawn
from active presentation.

B16 replaces them with one cubic Bézier graph p(q). The physically motivated
edge intercepts are fixed at (p,q)=(0.18,0) and (0.5,0.82), and the q controls
are fixed at 0, 0.2733, 0.5467, and 0.82. Only the two interior p controls are
fitted, so the model has no degree of freedom at or below the data-grid scale.
The objective follows the first downward-to-upward row-wise LLR zero crossing
through q=0.80, which captures the outward red lobe, while retaining the 16
audited B11 brackets as a penalty. Jeffreys-Beta uncertainty is propagated
through 64 refits. The dashed line is rendered as the exact Bézier path; the
light 90% band uses only 18 q support levels.

The fitted p controls are 0.18, 0.26313, 0.04582, and 0.5. The guide therefore
starts at the q=0 intercept near p=0.18, follows the measured middle red bulge,
and closes on the right edge at q_c=0.82 rather than being forced to q=1. Both
closure checks pass, and the collaborator figure has no explanatory line
legend. The guide remains a regularized finite-window LLR=0 visual summary,
not a thermodynamic boundary. B16 was briefly the active presentation, but B17
subsequently withdrew it because of the unsupported low-q reversal and
understated uncertainty; B15 and B16 now remain provenance downloads. Evidence:
[`manifests/phase-b16-strong-smooth-boundary-manifest-2026-08-28.json`](manifests/phase-b16-strong-smooth-boundary-manifest-2026-08-28.json),
[`manifests/phase-b16-strong-smooth-boundary-2026-08-28.json`](manifests/phase-b16-strong-smooth-boundary-2026-08-28.json), and
[`figures/phase-b16-strong-smooth-boundary-2026-08-28.png`](figures/phase-b16-strong-smooth-boundary-2026-08-28.png).

### Phase B17 — resolution-aware guide and directional bracket region

**Researcher correction registered 2026-08-28.** B16 is withdrawn from active
presentation because its unconstrained interior controls create an unsupported
low-q right-then-left reversal, while its 64-refit conditional envelope is much
narrower than the finite-grid and model uncertainty. Its method footer also
overexplains a line that is intended only as a guide.

B17 uses no new decoder data. The scientific uncertainty object is the existing
0.90 directional finite-grid bracket, not the selected B16 row roots. All sixteen
non-null B11 brackets through q=0.75 are retained. B14 high-p evidence supplies
right-censoring brackets at q=0.80, 0.85, and 0.90. The displayed region is the
narrowest nondecreasing lower/upper envelope containing every registered
bracket. It is explicitly not a pointwise or simultaneous confidence/credible
set for a physical boundary.

The dashed curve is a separate low-complexity visual guide. Its bottom and
right-edge intercepts are derived from the q=0 and p=0.49 central log-odds zero
crossings. A single cubic Bézier is fit to bracket midpoints subject to ordered
p controls, which guarantees nondecreasing p(q) and removes the unsupported
low-q reversal. No inferential interval is attached to the guide itself. The
figure contains no curve legend or method footer.

Acceptance requires monotonicity, containment of all nineteen measured/censored
brackets, a materially wider region than B16, current source hashes, zero new
decodes, focused tests, full Lab 003/dashboard regressions, and visual audit.
Contract:
[`manifests/phase-b17-resolution-aware-guide-manifest-2026-08-28.json`](manifests/phase-b17-resolution-aware-guide-manifest-2026-08-28.json).
Registered method:
[`results/phase-b17-resolution-aware-guide-method-note-2026-08-28.md`](results/phase-b17-resolution-aware-guide-method-note-2026-08-28.md).

**Completed 2026-08-29.** The data-derived intercepts are
`(p,q)=(0.17693,0)` and the right edge at `q=0.85544`. The ordered p controls
are `[0.17693, 0.17693, 0.17693, 0.5]`, so the rendered guide is nondecreasing
and contains no low-q reversal. The envelope contains all sixteen measured and
three censored brackets; through q=0.75 its mean width is 0.115, 23.8 times the
withdrawn B16 conditional-envelope width. Focused tests and the visual audit
pass with zero new decoder runs or decodes. The active report now shows B17;
B16 remains provenance only.

### Phase B18 — p↔1-p symmetry and full fundamental-domain display

**Researcher correction registered 2026-08-28.** The physical phase diagram
obeys $q_c(p)=q_c(1-p)$. With p horizontal and q vertical, differentiability
therefore requires $dq_c/dp=0$ at $p=0.5$. B17 violates this endpoint condition
because its linearly spaced q controls produce a nonzero terminal slope.

B18 changes only the existing-data presentation. It retains the B14 field,
all nineteen B17 measured/censored brackets, the data-derived bottom intercept,
and the p=0.49-derived estimate of the high-q intercept. A parametric cubic
Bezier uses $q_2=q_3=q_c$ and $p_2<p_3=0.5$, enforcing the horizontal tangent
analytically. Ordered controls prohibit folds and low-q reversal.

The visible p domain becomes exactly $[0,0.5]$. The current all-q honeycomb
grid has measured centers only at p=0.08 through 0.49, so unmeasured portions
remain blank; no p=0 or p=0.5 evidence column is fabricated. Acceptance
requires exact endpoint slope, monotonicity, unchanged bracket evidence,
zero added cells, zero decodes, regressions, and visual audit. Contract:
[`manifests/phase-b18-symmetry-constrained-guide-manifest-2026-08-28.json`](manifests/phase-b18-symmetry-constrained-guide-manifest-2026-08-28.json).

**Completed 2026-08-28.** The fitted controls are
`p=[0.17693,0.17693,0.27121,0.5]` and
`q=[0,0.28515,0.85544,0.85544]`. Hence the analytic terminal derivative is
exactly zero; sampled p and q are nondecreasing and the low-q reversal remains
absent. The 231-cell raster and all nineteen B17 brackets are unchanged, the
axis is exactly `[0,0.5]`, and no unmeasured cell or decoder sample was added.

### Data-currency rule for Phase B12–B14 figures

**Researcher instruction, 2026-08-28.** Before rendering or promoting any
active LER curve or phase/evidence map, compare its declared inputs against
the latest completed, source-compatible B12–B14 analysis. If a later audited
analysis changes a displayed cell or curve, regenerate the active PNG and its
machine-readable companion from that newer data; do not leave an earlier plot
as the active report or dashboard image. The update must hash-freeze the new
inputs and deep-compare every unchanged cell. Older figures remain provenance
downloads only. A newer artifact with an incompatible decoder, lattice, or
sampling contract is not silently pooled: it must be labelled incompatible and
requires its own comparison or presentation decision.
