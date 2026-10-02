---
title: 'Results'
status: current
updated: 2026-08-31
record: true
---

## Scientific correction — 2026-10-01

For the binary incomplete-herald channel, the research domain is **0 <= p <= 1, 0 <= q <= 1**. At interior q, error complementation does not give an observation-preserving p ↔ 1−p symmetry: a zero herald combines an ineligible event and a missed eligible event. Claims below that restrict the physical domain to half, enforce a horizontal boundary tangent at half, or infer an all-p ceiling from p≈0.5 are **withdrawn historical claims**, not current conclusions. B18's constrained guide is withdrawn; measured trial counts remain historical evidence. See [full-prior correction](/wiki?page=methods/binary-herald-full-prior-domain.md). The uniform-prior point p=0.5 remains special, but does not justify truncating the domain. Endpoint q=0 and q=1 symmetries require separate observation relabeling and do not establish interior-q symmetry.



## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# Results

This directory holds Phase 1 $q=0$ calibration, matched $q=1$ ideal-herald
scans, adaptive p-selection logs, and finite-size crossover inference
artifacts.

`final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.json` and
its PNG are the six-panel selected LER artifact cited by `REPORT.md`: rows are
$q=0,0.75,1$, columns are square and honeycomb. Each panel retains its own
immutable cohort and is not a pooled fit or cross-geometry comparison.

`phase-b19-full-prior-evidence-coverage-2026-10-01.png` is the active Report map: the 231 measured B14 honeycomb cells on p,q in [0,1], without an imposed guide. The unmeasured high-p joint grid is blank. B18 is withdrawn because its interior-q complement symmetry and horizontal tangent constraint are invalid. Earlier guide artifacts are historical provenance, not boundaries. The original fixed-q LER context remains separately labeled.

`q075-square-honeycomb-selected-ler-2026-08-28.json` maps the latest
5000-shot/cell $q=0.75$ square and honeycomb LER panels. The two panels use
independent physical-$p$ ranges and must not be read as a same-$p$ performance
comparison between geometries.

**Active methodology notice (2026-08-28).**
`phase-diagram-slope-flow-remediation-2026-08-28.json` supersedes every
crossing count, crossing location, and crossing-derived phase label for active
inference. The raw corrected-LLR observations remain valid. The replacement
analysis fits the sign of the all-distance binomial logit slope beta and will
produce a red/green/gray measured-cell map; historical crossing figures remain
provenance only and are removed from the active Lab result index.

`phase2-residual80-q-skeleton-2026-08-28-analysis.json` is the completed
honeycomb-first full q-skeleton discovery: 21 validated q shards, L=7,9,11,
11 p values, and 693,000 posterior-LLR residual-priority-80 observations. Its
20,000-replicate independent-by-size seed-trajectory bootstrap retains
no/single/multiple-crossing topology and reports conditional central 90%
intervals. Only q=0.95 and 1.00 are ceiling-compatible; q<=0.90 is unresolved,
so no p_c(q) or q_c is promoted. The companion phase-map figure visualizes
the unresolved/multiple-crossing structure. The atomic-recovery audit records
11 exact-hash recoveries and 10 already-final raw files without changing any
scientific content.

`manifests/phase3-residual80-honeycomb-highq-refinement-preflight-2026-08-28.json`
records the next bounded adaptive wave: q=0.85,0.90,0.95; L=7,9,11; seven
high-p points; 20 fresh seed clusters and 4000 shots/cell, for 252,000 planned
observations. The explicit-q/variable-shot analyzer path and three unique
dispatcher jobs pass 21/21 tests and dry-run validation. This is a preflight,
not experimental evidence; q=0.925 and square remain gated.

`phase3-residual80-honeycomb-highq-refinement-validation-2026-08-28.json`
records the completed production validation: three 84,000-row shards,
252,000/252,000 syndrome-faithful corrections, exact gzip hashes/counts, and
one start/end-stable source cohort. All raw files finalized normally. This
artifact validates the data but deliberately contains no crossing or q_c
interpretation; the registered 90% topology-aware analysis remains next.

`phase3-residual80-honeycomb-highq-refinement-4000-2026-08-28-analysis.json`
is the completed 20-cluster analysis. It classifies q=0.85,0.90,0.95 all as
unresolved. L7/L9 has no point crossing; L9/L11 has one crossing at q=0.85,
one topology-unstable crossing at q=0.90, and five crossings at q=0.95. The
q=0.95 bootstrap multiple-crossing rate is 68.7%, so the earlier five-cluster
ceiling label is not confirmed. L11 convergence falls to about 4% at high p,
making a matched convergence-cap diagnostic the next prerequisite before q
midpoint or larger-size expansion.

`phase3-honeycomb-highq-l11-convergence-cap-preflight-2026-08-28.json`
registers the next mechanism diagnostic: honeycomb L=11 at q=0.85,0.90,0.95
and p=0.40,0.45,0.49, with 64 fresh matched observations per cell and
otherwise-identical residual-priority caps 80, 160, and 320. The 1728 planned
decodes change only the iteration cap, use paired central 90% intervals, and
fail closed on syndrome or source drift. The combined suite passes 24/24; no
phase-boundary claim follows from preflight.

`phase3-honeycomb-highq-l11-convergence-cap-2026-08-28.json` and its compact
analysis complete that matched mechanism test. Convergence increases from
67/576 at cap 80 to 308/576 at cap 160 and 442/576 at cap 320, but all three
arms retain exactly 116 logical failures. The 30 and 22 successive correction
disagreements yield no rescues or harms, posterior scores barely move, and
cap 320 still leaves 134 cases nonconverged. This establishes cap sensitivity
of the fixed-point flag, not a phase-boundary correction; residual-priority-80
remains the primary decoder pending a fresh L11/L13 correction-to-scaling
wave.

`manifests/phase4-residual80-honeycomb-highq-l11-l13-scaling-preflight-2026-08-28.json`
registers that next wave: q=0.85,0.90,0.95; L=11,13; seven high-p values; 20
fresh seed trajectories; and 4000 shots/cell, totaling 168,000 planned raw
observations. The 26-test suite and three-job dry run pass. This is production
authorization only, not scientific evidence; q=0.925 and square remain gated.

`phase4-residual80-honeycomb-highq-l11-l13-scaling-validation-2026-08-28.json`
records the completed production gate: three 56,000-row shards,
168,000/168,000 syndrome-faithful corrections, exact raw hashes/counts, and a
single start/end-stable source cohort. No recovery was needed. Crossing
topology and confidence intervals remain uncomputed until the registered
analysis transition.

`phase4-residual80-honeycomb-highq-l11-l13-scaling-4000-2026-08-28-analysis.json`
and its interpretation complete the registered 20,000-replicate analysis.
q=0.85 has a broadly L9/L11-consistent crossing near p=0.4136, q=0.90 has a
topology-unstable point crossing near p=0.4825, and q=0.95 has no point
crossing but an unresolved p=0.49 size trend. L13 convergence is below 3%
throughout q=0.90 and q=0.95. Therefore no p_c(q), q_c, q=0.925 midpoint, or
square expansion is promoted; an L13 matched cap diagnostic is the next
mechanism gate.

`manifests/phase4-honeycomb-highq-l13-convergence-cap-preflight-2026-08-28.json`
registers the next matched mechanism test: 576 fresh L13 observations and
1728 otherwise-identical cap-80/160/320 decodes at q=0.85,0.90,0.95 and three
representative p values. The parameterized runner passes 27/27 tests and an
accelerated syndrome-faithful smoke run. No production result or cap change
follows from this preflight.

`phase4-honeycomb-highq-l13-convergence-cap-2026-08-28.json` and its compact
analysis complete the L13 mechanism test. Convergence rises
19→199→342/576 at caps 80/160/320, but every arm has exactly 87 logical
failures. The 57 and 45 successive correction disagreements cause no rescues
or harms, and posterior scores barely change. Cap 320 still leaves 234 cases
nonconverged. The fixed-point flag is cap-sensitive, while the registered
logical outcome is not on this matched sample; cap 80 remains primary.

`manifests/phase4-residual80-honeycomb-highq-adaptive-p-confirmation-preflight-2026-08-28.json`
registers the next independent wave: q=0.85,0.90,0.95; L=11,13; a common
p=0.39:0.01:0.49 grid; and 40 fresh 100-shot trajectory clusters, totaling
264,000 planned observations. Doubling cluster count at fixed 4000 shots/cell
targets topology fluctuation directly. The 29-test suite and three-job dry run
pass; this is production authorization, not phase evidence.

`phase4-residual80-honeycomb-highq-adaptive-p-confirmation-validation-2026-08-28.json`
records completed production validation: three 88,000-record shards, 264,000
raw observations total, 264,000/264,000 syndrome-faithful corrections, valid
gzip counts and SHA-256 digests, one stable runtime/source cohort, and no
recovery. It is dataset-integrity evidence only; the registered 20,000-
replicate central-90% topology analysis remains the next transition.

`phase4-residual80-honeycomb-highq-adaptive-p-confirmation-4000-2026-08-28-analysis.json`
and `phase4-residual80-honeycomb-highq-adaptive-p-confirmation-interpretation-2026-08-28.json`
record the completed 20,000-replicate independent analysis and its
cross-cohort gate. q=0.85 is multiple-crossing dominated, q=0.90 has only
33.15% exactly-single topology, and q=0.95 is ceiling-compatible only in the
new cohort. None reproduces a promotable cross-cohort boundary; the cohorts
remain separate and all downstream phase gates stay closed.

`phase4-residual80-honeycomb-highq-two-cohort-heterogeneity-2026-08-28.json`
compares L11/L13 size trends at the four common p values using 20,000
independent-by-size-and-cohort trajectory bootstrap replicates. All 12
between-cohort central-90% intervals include zero, including q=0.95,p=0.49
at [-0.0030,0.02425]. This is evidence that the label changes are compatible
with cluster fluctuation, not evidence that either cohort should be pooled or
promoted.

`corrected-llr-provenance-audit-2026-08-27.json` verifies that all 32 active
Phase 2 shards and both primary q=1 high-p shards use posterior LLR. It marks
`q0-calibration.json` and `q1-herald-scan.json` as invalid negative-log smoke
files and identifies fixed-cap BP non-convergence as the remaining blocker.

`n0-square-q1-convergence-cap-2026-08-27.json` and its figure compare
synchronous-40, synchronous-80, and stable-sort residual-priority-80 on 768
matched high-p observations. Convergence rises from 16 to 235 and 353, but
runtime also rises and the two 80-iteration arms have identical logical
outcomes. It is a mechanism diagnostic, not a threshold update.

`phase2-completeness-audit-2026-08-27.json` inventories the 42 expected
Phase 2 shards. It finds 32 active corrected-LLR summaries, 26 finalized raw
pairs, six exact-hash atomic-temp raw files recoverable without recomputation,
and ten active gaps covered only by a verified superseded source cohort. It
also records why a current-code partial resume would create mixed provenance.

`q1-honeycomb-residual80-discovery-1000-2026-08-27.json` is the first clean
researcher-selected Option 2 shard: 44,000 raw-backed observations using
compiled stable-sort residual-priority BP, 80 iterations, and posterior-LLR
PyMatching. Its analysis companion finds one $L=9/11$ point crossing at
$p=0.380$ while convergence at $p=0.49$ falls to 18.4% for $L=11$; no
asymptotic threshold is promoted. The raw count, gzip integrity, and declared
SHA-256 pass. A future shard is gated on persisting an in-run
correction-syndrome fidelity aggregate, which this first-wave runner version
omitted. `phase2-syndrome-fidelity-gate-2026-08-27.json` records the completed
fail-closed implementation and its 11/11 passing runner/analyzer tests; it
applies prospectively and does not rewrite the immutable first wave.

`q075-honeycomb-residual80-discovery-1000-2026-08-27.json` is the matched
current-source honeycomb $q=0.75$ discovery curve: residual-priority-80,
$L=5,7,9,11$, eleven $p$ values through $0.49$, 1000 shots/cell, and
44,000/44,000 syndrome-faithful corrections. Point crossings drift from
$p=0.290$ to $0.392$ across adjacent sizes and have broad seed-bootstrap
intervals, so the artifact establishes a finite-size crossing region rather
than a single promoted threshold.

`q075-honeycomb-residual80-confirmation-5000-2026-08-27.json` is the
standalone higher-statistics confirmation on the same $L=5,7,9,11$ and
eleven-point $p$ grid, using five fresh seeds and 5000 shots/cell. Its raw
gzip contains 220,000 records; all corrections are syndrome faithful, source
hashes are stable and match the discovery cohort, and the declared SHA-256
passes. The median per-cell 95% LER interval width shrinks from 0.0460 to
0.0204. First directed adjacent-size crossings occur at $p=0.3904$, $0.3473$,
and $0.2643$, with seed-cluster intervals $[0.3048,0.4664]$,
$[0.3324,0.4243]$, and $[0.2457,0.4625]$. The remaining size drift and low
$L=11$ convergence prevent promotion of a single threshold.

`q1-honeycomb-residual80-l9-l11-crossing-refined-3000-2026-08-27.json`
contains the standalone Phase N1 refinement: 30,000 records over
$L=9,11$ and $p=0.36$--$0.40$, with 3000 fresh shots/cell and 30,000/30,000
syndrome-faithful corrections. Its analysis finds no point crossing; 97.86%
of 10,000 seed-cluster bootstraps retain lower $L=11$ LER at every sampled
$p$, and only 1.55% contain a directed crossing. The first-wave $p=0.380$
crossing is not replicated and no threshold is promoted.

`q1-honeycomb-residual80-l9-l13-highp-3000-2026-08-27.json` contains the
Phase N2 $p=0.45,0.49$ sentinel for $L=9,11,13$: 18,000 raw records,
18,000/18,000 syndrome fidelity, and source hashes matching N1. The L9/L11
size advantage is bootstrap-stable, while L11/L13 reaches only 0.9524
probability of lower L13 LER at $p=0.49$, below the registered 0.975 target.
Held-out L15 and any ceiling claim remain gated.

`n3-source-drift-rejection-2026-08-27.json` records why the attempted N3
extension is excluded before analysis. Although its 7000 raw rows, fidelity,
and deterministic N2 prefix pass, four source files changed during execution,
so end hashes cannot identify the loaded code. The raw and summary are
quarantined in `rejected-source-drift-n3-2026-08-27/`; N2 remains the latest
accepted evidence.

`phase2-source-stability-gate-2026-08-27.json` records the prospective fix:
new Phase 2 shards freeze all five source hashes before decoding, recheck them
before atomic raw publication, and delete the temporary raw shard on any
drift. The simulated-drift integration test and complete runner/analyzer suite
pass 14/14. It does not rehabilitate quarantined N3 data.

`q0-square-refined-5000-2026-08-27.json` is the current q=0 square calibration.
It contains 220,000 raw shot records from 5000
shots/cell on a 0.005-spaced grid through $p=0.10$--$0.14$. Adjacent-size
intersections span $p=0.1134$--$0.1153$.

`q075-square-l11-l13-refined-5000-2026-08-27-analysis.json` is the current
square $q=0.75$ refinement. It combines 210,000 corrected posterior-LLR
observations at 5000 shots/cell over $p=0.12$--$0.32$ and gives a directed
$L=11/13$ crossing at $p=0.1725$ with conditional bootstrap interval
$[0.1514,0.2120]$. Fixed-point convergence is effectively absent, so this is
not an asymptotic threshold.

`q1-square-l11-l13-refined-5000-2026-08-27.json` contains the fresh-seed
square $q=1$ largest-size refinement: 5000 shots/cell, 0.01 spacing over
$p=0.20$--$0.32$, and 130,000 raw observations with BP convergence fields.
Its analysis companion records the point crossing $p=0.2956$, conditional
seed-bootstrap interval $[0.2944,0.2987]$, 30.2% multiple-crossing bootstrap
rate, and the near-zero fixed-point convergence limitation.

`q1-square-l3-l9-highp-refined-5000-2026-08-27.json` and
`q1-square-l11-l13-highp-refined-5000-2026-08-27.json` are matched dense
high-p source shards covering $L=3,5,7,9,11,13$, $p=0.30$--$0.49$ in 0.01
increments, and 5000 shots/cell. Their gzip JSONL files contain 600,000
immutable observations in total. The unified
`q1-square-l3-l13-highp-refined-5000-2026-08-27-analysis.json` finds no
$L=3/5$ crossing, multiple $L=5/7$, $L=7/9$, and $L=11/13$ crossings, and
one point $L=9/11$ crossing at $p=0.3471$. Bootstrap and convergence evidence
do not support a common high-p threshold.

`q1-square-l5-l13-crossing-refined-10000-2026-08-27.json` is the requested
no-$L=3$ synchronous-40 refinement: $L=5,7,9,11,13$, 0.005 spacing over
$p=0.28$--$0.42$, 10,000 shots/cell, and 1,450,000 raw observations. Its
analysis companion supplies separate adjacent-size delta-LER panels and
seed-bootstrap bands. Only $L=5/7$ has a single point crossing, at
$p=0.3566$, and its stable-topology fraction is 75.3%; all larger adjacent
pairs retain multiple crossings. This is a legacy-decoder diagnostic, not the
residual-priority-80 primary series, and is not pooled with the
different-source 5000-shot shards.

