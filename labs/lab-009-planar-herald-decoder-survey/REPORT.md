# Lab 009 — Planar herald decoder survey and integration

## Overview

### L009.1 Motivation

The reusable decoder collection now includes configuration MAP, planar logical ML, exact transfer and controlled MPS alongside BP plus matching. This lab consolidates their theory, checks the implementations on the same observation law, and reproduces the numerical evidence without rerunning large campaigns. A finite-penalty Kac–Ward implementation remains a research comparison.

### L009.2 Background

The model has IID binary edge errors, exact detector parity and conditionally independent herald coins for local counts at least two. Rough tips are unmeasured. The success criterion is a valid syndrome correction with trivial residual logical parity; reconstructing the sampled errors or reproducing heralds in the correction is unnecessary. The current research domain is **p,q in [0,1]**. Incomplete heralds do not generally possess complement symmetry; inherited studies covering p≤1/2 are restricted-domain evidence. [Model and loss](wiki/model.md).

Lab 002 supplies the BP/LLR baseline, Lab 003 supplies measured finite-window trends, and Lab 007 supplies the sector formulation. The present gap was correlated logical-sector inference and larger-size evidence, not merely faster BP. The [local theory wiki](wiki/index.md) derives the edge/site weights, matching reductions, partition functions and limitations; [source documentation](../../src/herald_decoder/README.md) gives the reusable API.

### L009.3 Question

Which distinct inference methods can become standard algorithms, what performance and efficiency do matched records establish, and what can the existing larger-size evidence support?

### L009.4 Hypothesis

Parity-fixed degree-two/three planar factors admit exact matchgate sector sums. Configuration MAP is useful but need not outperform BP. Transfer independently checks the sums; finite-width MPS and finite-penalty Kac–Ward require approximation qualifications. Existing numeric campaigns can reproduce the important size trends and boundary comparisons without a heavy new sweep.

## Evidence

### L009.5 Reusable methods and system integration

Four new source classes are exposed by `make_decoder(graph, method, p=p, q=q, ...)`. They share the existing geometry and visible record. The common correction API and standard selector are exercised by the [interactive decoder artifact](results/decoder-workbench.html); [method survey](wiki/comparison.md) explains the objective differences.

| Standard method | Optimized quantity | Scope and limitation |
| --- | --- | --- |
| BP + matching | Approximate edge marginals, then LLR projection | Existing square/honeycomb API; convergence and projection loss |
| Configuration MAP | Posterior of one complete configuration | Exact integer minimizers below half; literal floating weights above half, subject to backend precision |
| Planar ML | Sum over each logical sector | Algebraically exact trivalent planar factors; numerical gates |
| Exact transfer | Sum over each logical sector | Independent binary contraction; exponential frontier width with caps |
| MPS | Approximate logical-sector sums | Honeycomb column contraction; finite χ and truncation diagnostics |

MAP returns a hard-valid configuration. Sector methods return a syndrome-compatible representative in the selected absolute sector and a posterior when available. A generic planar binary-factor API also supports a validated full-irrep fixture. It does not claim to solve arbitrary fusion, degree-four factors or noisy spacetime channels.

### L009.6 Correctness and approximation gates

Independent weighted whole-error enumeration checks 283 supported size-two record/parameter cases, including both deterministic priors, q endpoints and extreme priors. Another 216 records at sizes three through five compare planar and transfer posteriors. The generic-factor interface check changes references and edge ordering. Eight regression groups also check batches, resource caps, signed costs, exact q=1 MAP counts, an SU(2) local-factor fixture and BP factory compatibility. No assertion is based on matching a historical phase guide. [Planar derivation and numerical scope](wiki/planar-ml.md).

![Posterior discrepancies under MPS truncation and Kac–Ward finite penalties](figures/approximation-diagnostics.png)
*Figure L009.1. Maximum checked posterior discrepancies; these are sampled diagnostics, not rigorous risk bounds. MPS χ=4 loses accuracy at size five; χ=16 agrees there to roundoff. Finite Kac–Ward penalties soften forbidden configurations. Display floor is 10⁻¹⁷; data: [validation receipt](results/validation.json).*

The fresh size-nine cohort agrees between planar and exact transfer to numerical precision. χ=16 MPS also agrees closely in this cohort, but remains approximate. Equal-risk sector ties can give different failure vectors even when total counts coincide. Numerical failures are explicit; records must not be silently dropped. Kac–Ward is excluded from the standard selector because its current finite penalty changes the likelihood support.

### L009.7 Assessment of the nine SciCode2 runs

The [complete independent run evaluation](wiki/scicode2-run-evaluation.md) is part of this lab, including the original run-by-run assessment and examiner lessons. All nine submissions reconstructed the stipulated lattice and produced substantive decoding studies; at least six have strongly supported completion. They answered the original restricted-domain task, p≤1/2, and are not retrospectively graded against the current full-domain revision. The pipeline metadata were ungraded; this is scientific audit judgment, not a calibrated pass rate.

![Original named-run comparison of repository evidence and submitted boundaries](figures/scicode2-run-boundary-comparison.png)
*Figure L009.2. Original evaluation figure with Fable, Opus and Astra run labels. The left panel shows the 231 repository BP trend cells; the other panels separate MAP and sector-inference estimates. All panels concern the historical p≤1/2 task. Connecting lines are not new fits or pooled uncertainty, and no B18 guide or reflected high-p values are used. The current full-domain coverage remains separately displayed below; data: [evaluation provenance](results/run-evaluation-integration.json).*

| Run | Main method and elapsed hours | Independent assessment |
| --- | --- | --- |
| Fable 1 | MAP + finite-penalty Kac–Ward; 2.85 h | Substantial completion; p=0 API defect reproduced, fixed herald penalty fails at extreme prior, endpoint fit unstable |
| Fable 2 | Hard-constraint MAP gadgets; 2.59 h | Strong formulation; native Linux backend not rerun here, failed fits require explicit rejection status |
| Fable 3 | Transfer + finite-χ MPS; 1.53 h | Substantial logical inference; sampled convergence does not justify all-record exactness |
| Opus 1 | Planar logical ML; 2.74 h | Strong completion; categorical phase and universality claims exceed finite-size evidence |
| Opus 2 | Planar logical ML; 2.61 h | Strong completion; very narrow systematic errors and weak matching comparator need scrutiny |
| Opus 3 | Planar logical ML; 2.52 h | Strong completion with explicit crossing drift; uniqueness and universality remain empirical |
| Astra 1 | Configuration MAP; 1.16 h | Strong completion; clearly separates statistics, size sensitivity and decoder objective |
| Astra 2 | Integer-cost configuration MAP; 1.14 h | Strong completion; useful structural reduction and canonical-correction treatment |
| Astra 3 | Adaptive-penalty configuration MAP; 1.11 h | Strong completion; careful uncertainty and independent size checks |

The original audit independently checked all nine geometries at L=2/3/4, 50,661 size-two observation/parameter cases in total, and 23 larger coset records per run. The planar ML and exact transfer posteriors agree with independent sums within 1.8×10⁻¹³ on the checked records. MAP's excess logical risk is an objective difference, not automatically a coding defect; ties and canonical corrections need appropriate grading. These audit cohorts are distinct from the new package validation and benchmarks.

For scientific judgment, the strongest lessons are the value of exact sector sums, the degree-three planar structure, and the need to examine crossing drift rather than add shots only at small sizes. For SciCode2 design, this pilot does not support the intended <10% frontier success target or the 10–20-hour active-work target: the recorded 1.11–2.85 hours include computation and do not measure active effort. Preserve algorithmic freedom, use independent geometry/channel/loss checks and held-out matched records, and do not grade by resemblance to a BP diagram. The full assessment also records prompt-format damage, rejected fits, endpoint defects and limits of the audit.

### L009.8 Reproduced large-size evidence

The lab snapshots sufficient-statistic vectors for **5,114,000 inherited planar-ML trials in 1,430 cells**, and retains ten reported boundary curves from nine studies separately. Source hashes and numeric snapshots make analysis independent of downloaded campaign executables. The 6,704 imported chunks have no duplicate (size,p,q,seed) cohort within the aggregate. [Cohort definitions and interpretation](wiki/comparison.md).

![Measured repository trends and reported decoder-family boundary estimates](figures/survey-boundaries.png)
*Figure L009.3. Left: 231 measured BP trend cells, mainly sizes 7/9/11; blue favors decreasing LER and red increasing LER. Empty high-p space is unmeasured inherited coverage. Other panels connect separate reported estimates on their original domain, without new fits, mirrored points or pooled confidence intervals; data: [boundary vectors](data/reported-boundaries.csv).*

The larger planar-ML studies report p estimates around 0.163–0.165 at q=0, versus about 0.158–0.160 for configuration MAP. At p=1/2, reported q estimates are around 0.866–0.872 for planar ML and roughly 0.88–0.89 for MAP. These are descriptive ranges of reported finite-size estimates, not a joint statistical interval or a new full-domain phase diagram.

![Inherited planar-ML risk curves and perfect-herald direct counts](figures/inherited-ml-curves.png)
*Figure L009.4. First three panels show unconditional mean conditional ML risk with ±1.96 sample SE. The last uses direct failure proportions at perfect heralding; a zero count is shown as a 95% one-sided exact upper limit, not zero risk. Only one identical source campaign is aggregated; data: [ML cell vectors](data/inherited-ml-cells.csv).*

![Pairwise crossing drift with increasing lattice sizes](figures/inherited-crossing-drift.png)
*Figure L009.5. Inherited L versus 2L crossing estimates and their source error convention. Shading denotes the source working range combining fit and size sensitivity, not a rigorous confidence band. The endpoint visibly drifts with size; data: [crossing vectors](data/inherited-crossings.csv).*

Small-size endpoint shifts therefore cannot be attributed solely to algorithm defects. More shots on small patches do not remove extrapolation bias. Failed/out-of-domain fits are excluded from the active curve comparison; no universality or unique-transition theorem is inferred.

### L009.9 Fresh matched performance over the full prior range

The two completed pilot cohorts contain **3,200 independent records**, 200 per cell at sizes 5/9, shared by five methods: 16,000 decoder evaluations. High-p records are independently sampled. There are zero invalid corrections and zero runtime exceptions. Synchronous BP uses 40 iterations and default damping/tolerance; its 2,218 nonconverged records remain in the denominator. [Comparison and scoring](wiki/comparison.md).

![Shared-record logical failure rates at low and high prior probabilities](figures/fresh-matched-ler.png)
*Figure L009.6. Wilson 95% intervals for each 200-record cell. Planar/transfer counts coincide; MPS χ=16 has the same counts in this cohort. The original and independent high-p cells are discrete measurements, without interpolation. Exact ML need not win every realized sample; data: [fresh matched results](results/benchmark.json).*

![Excess conditional logical risk relative to exact sector inference](figures/fresh-conditional-regret.png)
*Figure L009.7. Mean selected-sector expected loss minus the exact planar conditional Bayes risk, with ±1.96 sample SE over records. This exposes the objective gap when realized counts favor another decoder; it is not an asymptotic uncertainty estimate. Exact reference regret is zero; data: [posterior-weighted comparison](results/benchmark.json).*

MAP does not consistently improve on BP. At L=9, p=.49,q=1 it has 9/200 failures versus 2/200 for BP, planar ML, transfer and MPS. At p=.95,q=.8 all methods have 0/200 failures at both sizes; the Wilson upper limit is about .0188, so zero observed failures does not establish zero limiting risk. The current wrappers reproduce saved decisions/posteriors on three held-out saved records per cell/method, with tie allowances.

### L009.10 Separate inherited comparison with the stronger BP setting

An earlier independent audit supplies 4,000 common-record trials at sizes 7/11 using residual-priority BP with an 80-iteration cap and separate MAP/ML implementations. Its settings and timings are distinct from the new synchronous-40 cohort. [BP method and projection loss](wiki/bp-matching.md).

![Paired MAP and ML failure differences versus residual-priority BP](figures/inherited-matched-differences.png)
*Figure L009.8. Candidate-minus-BP failure proportion for separate 500-record cells; error bars are ±1.96 paired SE, pointwise rather than simultaneous-domain intervals. Negative favors the candidate. This inherited cohort is not pooled with the fresh implementation benchmark; data: [audit matched results](data/inherited/audit_matched_comparison.json).*

At size eleven, inherited ML improves observed failure by .048 at (.24,.5) and .056 at (.40,.8), with paired SE about .0159 and .0168. This is encouraging local evidence for sector inference, not a universal measured advantage over every BP configuration.

### L009.11 Efficiency of the integrated implementations

![Warmed single-shot median and p95 latency by decoder and lattice size](figures/warm-runtime.png)
*Figure L009.9. Median warmed wall time, upper whisker p95, on one CPU thread. Each size/method has 1,600 timings from an equal-size mix of eight cells. Setup and the independent first call are excluded. Values describe these Python wrappers, not inherited native implementations; data: [runtime vectors](data/warm-runtime-summary.csv).*

| Method | L=5 median / p95 ms | L=9 median / p95 ms |
| --- | ---: | ---: |
| BP + matching | 0.76 / 1.45 | 2.03 / 4.27 |
| Configuration MAP | 1.04 / 1.98 | 6.19 / 12.94 |
| Planar ML | 4.71 / 11.31 | 26.25 / 31.83 |
| Exact transfer | 4.15 / 9.25 | 47.60 / 75.76 |
| MPS χ=16 | 3.50 / 4.96 | 15.20 / 24.21 |

Transfer/MPS batch 16 records through vectorized tensor operations; planar/MAP batch paths currently loop. Setup and warm-call receipts are retained per cell. The environment is Python 3.13.2, NumPy 1.26.4 on arm64 macOS. MAP graph reconstruction and repeated graph-property access contribute overhead. This backend is sufficient for the survey; a separate optimization project is not a prerequisite to the scientific conclusion. [Contraction complexity and resource caps](wiki/transfer-mps.md).

### L009.12 Full-domain correction and analytical structure

The complete joint-record size-two oracle gives optimal risks .231775342400 at (.2,.5) and .304423178240 at (.8,.5): an exact counterexample to intermediate-q complement symmetry. At q=0 and q=1 the corresponding endpoint symmetries pass, as do zero risk at deterministic p=0/1. [Complete symmetry audit](results/full-prior-symmetry-audit.json), [current observation model](wiki/model.md).

Perfect heralding fixes each detector count. Logical ambiguity then needs an alternating path joining the rough sides. The honeycomb walk-growth constant is below two, producing a sufficient exponential recovery bound across the full p interval. More generally, the derived sufficient region is μ√(p(1−p))(1+√(1−q))<1. It is conservative and is not the fitted boundary. Herald thinning proves optimal Bayes risk cannot worsen with q; it proves neither p monotonicity nor a unique fixed-q transition.

## Analysis

### L009.13 Implications

The main integration is correlated sector inference with a reusable exact planar formulation, backed by an independent contraction oracle. Integer MAP is an efficient structural baseline below half; MPS offers controlled numerical flexibility; Kac–Ward contributes a useful limiting construction but is not promoted with an exactness claim. [Partition functions and recovery bounds](wiki/statistical-mechanics.md) explain the assumptions behind each conclusion.

The survey has unified duplicate algorithms into named methods, made their code callable, reproduced the persuasive curves in PNG plus vector SVG/PDF, and retained fresh/inherited numerical vectors and hashes. The [data and vector export guide](data/README.md) provides formats and figure downloads. These results supersede the partial full-prior diagnostic as the lab synthesis; historical correction receipts remain provenance. No heavy threshold campaign was repeated.

### L009.14 Limitations

Algebraic exactness does not certify floating-point stability at every size or extreme parameter. Above half, MAP uses literal floating weights and the matching backend's finite numerical resolution. Finite χ is approximate; discarded weight is not a rigorous risk certificate. Finite Kac–Ward penalties soften support. Timings are warmed measurements on this machine with heterogeneous per-cell cost, not an asymptotic speed comparison. [Method and evidence boundaries](wiki/comparison.md).

Inherited restricted-domain estimates cannot establish the full-domain phase topology. Finite-size drift, fit-window sensitivity and different decoder objectives remain separate uncertainties. The broader project's historical tests have known archived-manifest/dependency failures; this lab reports its relevant passing checks rather than claiming the entire repository suite passes. The classical results do not establish decoding performance for hidden-orientation quantum fusion or noisy spacetime channels.

### L009.15 Next question

A separately registered follow-on can compare planar ML with full-irrep binary local factors under an independently validated observation law, or study large-size/full-domain convergence where fresh evidence is missing. The survey/integration deliverable ends here; neither a new phase sweep nor a physical-channel extension is required to reuse these standard methods.
