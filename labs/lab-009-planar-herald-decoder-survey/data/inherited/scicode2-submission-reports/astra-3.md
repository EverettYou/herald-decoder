# Decoding with incomplete local witnesses

Computational research report · 26–27 September 2026

**Local count witnesses substantially enlarge the recoverable region.** For the
configuration-MAP matching decoder studied here, the syndrome-only transition is
near **p=0.158**, rising to **p=0.220 at q=0.50** and
**p=0.388 at q=0.85**. The estimated boundary reaches p=1/2 at
**q≈0.886**, with a finite-size sensitivity band
**0.870–0.892** in q.
Above this endpoint, sampled failures decrease with size throughout the physical
error interval. Perfect witnesses (q=1) are provably decodable throughout that
interval. The study uses **1,858,200 unconditional Monte Carlo trials**,
sizes **L=8,16,32,64**, and independent **L=96** checks. The displayed physical-error
domain in the question is interpreted as **0≤p≤1/2**.

![Two-dimensional decoding phase diagram](figures/phase_diagram.png)

Figure 1. The principal result. The line interpolates independently fitted sections;
the grey corridor includes sampling uncertainty and sensitivity to finite size.
These are inferred phases of this decoder. The non-decodable region is not an
impossibility claim about optimal recovery. Dots show the broad pilot design;
diamonds check fixed-p sections. Above the dashed curve, a conservative analytical
condition guarantees ideal configuration-MAP decoding. Intermediate points of the
empirical boundary are interpolations, rather than separately measured thresholds.

<!-- PAGEBREAK -->

## Boundary estimates and size dependence

| Fixed section | Transition estimate | 95% statistical interval | Finite-size sensitivity band |
| --- | --- | --- | --- |
| q=0 | 0.158 | 0.156–0.159 | 0.155–0.161 |
| q=0.1 | 0.167 | 0.165–0.168 | 0.165–0.171 |
| q=0.25 | 0.183 | 0.181–0.185 | 0.180–0.186 |
| q=0.4 | 0.203 | 0.201–0.205 | 0.199–0.210 |
| q=0.5 | 0.220 | 0.218–0.222 | 0.216–0.228 |
| q=0.6 | 0.247 | 0.244–0.250 | 0.243–0.254 |
| q=0.65 | 0.263 | 0.261–0.266 | 0.258–0.271 |
| q=0.7 | 0.282 | 0.278–0.285 | 0.276–0.299 |
| q=0.75 | 0.308 | 0.304–0.311 | 0.301–0.318 |
| q=0.8 | 0.338 | 0.333–0.343 | 0.326–0.353 |
| q=0.825 | 0.367 | 0.363–0.371 | 0.359–0.386 |
| q=0.85 | 0.388 | 0.384–0.392 | 0.377–0.414 |
| p=0.5 (in q) | 0.886 | 0.884–0.888 | 0.870–0.892 |

Statistical intervals are 200-replicate parametric-bootstrap intervals for
the primary finite-size fit, conditional on the final sampling design. The final
column is a **sensitivity envelope, not a rigorous confidence set for the
infinite-size limit**. It combines five fit protocols and the two largest
adjacent-size crossing intervals, with the larger-size endpoint audit described
on page 5. All 16 horizontal and vertical fits,
including endpoint checks at p=0.40,0.45,0.475,0.50, are saved in
[transitions.csv](data/transitions.csv) and [fits.json](data/fits.json).

For each fixed-q section we maximize a binomial likelihood with a local scaling
form logit(P_fail)=A₀+A₁u+A₂u²+B/d, where d=2L−1 and u is proportional to
(p−p_c)dᵃ. For fixed-p sections u is proportional to (q_c−q)dᵃ.
The exponent a is a nuisance parameter fitted separately for every section.
The primary fit includes B/d and all four sizes; alternatives omit B/d and use
either all sizes or L≥16, or replace B/d by B/d^ω with ω=0.5 or 2. We impose no
common critical exponent or monotonic boundary across sections. All corrected fits have binomial-deviance goodness-of-fit p-values above 0.01; the smallest is 0.082. This is a model check, not proof of scaling.
The uncorrected all-size fit becomes inadequate at high q; its displacement is
retained as a conservative sensitivity indicator, rather than an equally plausible
infinite-size estimate.

Independent quadratic-logit fits for each size produce the following crossings
(95% bootstrap intervals). Their motion is why an individual crossing is not
reported as the infinite-size threshold.

| Section | L=8/16 crossing | L=16/32 crossing | L=32/64 crossing |
| --- | --- | --- | --- |
| q=0 | 0.1632 [0.1593, 0.1674] | 0.1584 [0.1559, 0.1613] | 0.1586 [0.1571, 0.1600] |
| q=0.5 | 0.2316 [0.2252, 0.2378] | 0.2246 [0.2205, 0.2285] | 0.2206 [0.2185, 0.2231] |
| q=0.85 | Unresolved in scan | 0.4047 [0.3962, 0.4145] | 0.3939 [0.3885, 0.3998] |
| p=0.5 | Unresolved in scan | 0.8736 [0.8700, 0.8782] | 0.8853 [0.8821, 0.8885] |

The full-domain pilot sampled twelve physical-error values, nine witness values,
and three sizes. Refinement then concentrated independent trials around the
boundary. No additional boundary or reentrant region was resolved; the inferred
organization is one decodable region extending from low p and high q, separated
from a region with persistent failure. Finer structures between sampled sections
remain untested. The high-p end is flat within uncertainty: q_c(0.475)≈0.886 and
q_c(0.5)≈0.886. A shallow turn inside the grey band remains unresolved. The broad scan and crossing
drift are also shown in [pilot_scan.pdf](figures/pilot_scan.pdf) and
[crossing_drift.pdf](figures/crossing_drift.pdf).

<!-- PAGEBREAK -->

## Quantitative finite-size evidence

![Logical-error curves and size dependence](figures/finite_size_evidence.png)

Figure 2. Points are unconditional failure fractions with pointwise Wilson 95%
intervals; smooth lines are the primary finite-size fits. Grey vertical strips
show the transition sensitivity band. Panel f probes the high-error edge of the
domain. A downward triangle denotes zero observed failures and its exact 95%
one-sided upper limit, 1−0.05^(1/N). Zero failures are not asserted to mean zero
underlying probability.

Selected phase-interior checks below give **failures/trials (LER)**. L=96 results
are held out of the primary boundary fits. They test the inferred direction of
size dependence beyond the fitted range. Full counts and intervals at every
sampled point are in [ler.csv](data/ler.csv).

| (p, q) | L=16 | L=32 | L=64 | L=96 |
| --- | --- | --- | --- | --- |
| (0.15, 0) | 860/6600 (0.1303) | 490/4600 (0.1065) | 103/2000 (0.0515) | 100/2000 (0.0500) |
| (0.17, 0) | 1605/6000 (0.2675) | 1258/4000 (0.3145) | 798/2000 (0.3990) | 841/2000 (0.4205) |
| (0.212, 0.5) | 878/6000 (0.1463) | 496/4000 (0.1240) | 169/2000 (0.0845) | 122/2000 (0.0610) |
| (0.24, 0.5) | 1642/6000 (0.2737) | 1329/4000 (0.3322) | 778/2000 (0.3890) | 866/2000 (0.4330) |
| (0.36, 0.85) | 316/2000 (0.1580) | 229/2000 (0.1145) | 143/2000 (0.0715) | 86/2000 (0.0430) |
| (0.45, 0.85) | 3525/12600 (0.2798) | 2761/8600 (0.3210) | 1458/4000 (0.3645) | 849/2000 (0.4245) |
| (0.5, 0.9) | 996/6000 (0.1660) | 775/6000 (0.1292) | 307/3000 (0.1023) | 158/2000 (0.0790) |
| (0.5, 1) | 6/6000 (0.0010) | 0/6000 (0.0000) | 0/3000 (0.0000) | — |

At the low-p controls, failure decreases with distance; at the high-p controls
below the boundary in q it grows towards a substantial value. Along p=0.5,
q=0.90 shows decreasing failure beyond the fitted sizes, while q=1 suppresses
failure much faster. At (p,q)=(1/2,0), failure is exactly 1/2 for every valid
decoder and every size by a logical-sector symmetry.

<!-- PAGEBREAK -->

## Geometry, decoder, and validation

The generator implements the specified merged hexagons, exposed-side removal,
unmeasured boundary endpoints, and corner rule. Isolated vertices remain in the
graph. It gives V=2L²+4L, E=3L²−1, |D|=2L²−2, and distance d=2L−1.
The logical mask contains exactly the L+1 retained edges meeting the right
boundary. No syndrome or herald is generated at an unmeasured vertex.

![Exact lattice construction](figures/geometry.png)

Figure 3. The L=3 implementation. Dashed construction edges are absent from the
error vector. Filled vertices receive both observations; isolated open boundary
vertices remain present. Array ordering and a callable example are in
[README.md](README.md).

The decoder maximizes the posterior of an **entire error configuration** subject
to the exact syndrome. Degree at most three is crucial: at fixed parity,
eligibility is (n_v−s_v)/2. A positive herald fixes n_v=s_v+2; a zero herald
contributes (1−q)^((n_v−s_v)/2). Thus, for 0<q<1 the negative log posterior is a
linear edge cost on its support. With λ=log[(1−p)/p] and τ=−½log(1−q), an edge
cost is λ plus τ for each zero-herald endpoint, with a dominating negative
penalty for each positive-herald endpoint. Signed minimum-weight matching
optimizes this cost. Constraints are checked and the penalty is increased if
needed. At q=1 both herald values fix counts; at q=0 the same family reduces to
ordinary minimum-weight syndrome decoding. This treatment includes every zero
herald and retains the conditional observation law; it does not assume that
heralds are unconditionally independent.

The deterministic API `decode(GL,p,q,s,h)` returns the full edge correction.
It receives no sampled error counts or hidden microscopic variables. Each
Monte Carlo trial checks the returned binary shape, Hc=s, and herald support.
Exceptions or invalid corrections are included as failures. Across the study,
there were **0 invalid corrections, 0 exceptions,
0 herald-support violations**, and
**0 penalty retries**.

Validation enumerated all **2,048 error vectors** and all possible herald
outcomes on L=2, checking **39,660
positive-probability observations across 25 parameter pairs**. Every correction
had maximum posterior configuration weight. Independent GF(2) enumeration
checked another **5,400 sampled observations at L=3,4**, with up to 131,072
syndrome-compatible configurations per observation. A larger-patch penalty audit
compared 600 trials at L=16,32,64: **0 posterior-cost differences**.
This last test checks conditioning, not exact optimality on large patches.

<!-- PAGEBREAK -->

## Analytical constraints, approximations, and resources

At q=1, the observations fix every detector count: n_v=s_v+2h_v. The residual
between any two compatible configurations consists of cycles and boundary paths.
A logical failure requires a left-to-right path on which errors alternate.
A fixed m-edge path alternates with probability at most 2^(1−m). The number of
honeycomb self-avoiding walks grows with constant μ=√(2+√2)<2, so summing over
paths of length at least 2L−1 gives exponentially vanishing failure. This proves
decodability of the entire q=1 edge, including p=1/2, for any count-consistent
correction, independently of sector degeneracy.

A pairwise posterior-affinity bound extends this to a sufficient open region
for ideal configuration-MAP inference:

```text
μ sqrt[p(1−p)] (1 + sqrt[1−q]) < 1,     μ = sqrt(2+sqrt(2)).
```

It includes all p≤1/2 when q>0.993212, and all q at sufficiently small p
(the q=0 endpoint is approximately 0.079552). This bound is conservative; it is
not fitted to the observed transition. Its derivation averages the correlated
herald process through its exact conditional law. The full proof, including
boundary factors, is in [ANALYTICAL_NOTES.md](ANALYTICAL_NOTES.md).

Three uncertainties must be kept separate. **Statistical error** comes from
finite trial counts, with binomial intervals and bootstrap estimates supplied.
**Finite-size error** comes from extrapolation and fit assumptions; the displayed
envelope exposes size-window and correction sensitivity but cannot rule out later
drift. At p=0.5 the band also includes fits with L=16–96 and the 64/96 crossing;
these larger-size diagnostics are saved in [endpoint_audit.json](data/endpoint_audit.json)
and [holdout.csv](data/holdout.csv). **Decoder approximation** comes from choosing one configuration instead
of the most probable logical sector. For example, exact L=2 enumeration at
(p,q)=(0.4,0.9) gives LER 0.361586 for this decoder and
0.335263 for optimal sector inference. The gap is not a
bound on large-size threshold error. The phase band describes this decoder only;
optimal recovery may succeed farther into the plotted non-decodable region.
PyMatching's finite-precision weights are an additional audited numerical issue.

The physical picture is that parity hides cancelling pairs, while positive
witnesses impose count constraints and absent witnesses change likelihoods.
Increasing q makes logically spanning ambiguity progressively harder to sustain.
At perfect witness availability, finite alternating ambiguities can remain but
their spanning probability vanishes. Optimal decoding cannot be harmed by larger
q because thinning positive heralds reproduces any smaller-q observation law;
that information ordering alone does not prove monotonic risk for this particular
decoder or monotonicity in p.

The experiment ran on one Intel(R) Xeon(R) Platinum 8559C workstation allocation with
**at most eight CPU cores**, normally seven simulation workers and single-threaded
numerical libraries; no GPU was used. The raw Monte Carlo jobs consumed
**4.81 CPU-hours**.
The sampled peak aggregate RSS of the experiment and analysis processes was 1.11 GiB (summing RSS double-counts shared pages). The largest recorded worker RSS was **111.9 MiB**,
well below the 32 GiB limit. Source, manifests, seeds, raw counts, timings,
validation records, and pinned Python dependencies are included. Reproduce the
analysis with `python3 reproduce.py --out-dir reproduced`; add `--resimulate`
to rerun every trial. See [README.md](README.md) for conventions and commands.

The matching implementation and signed-weight interface are documented by
[PyMatching](https://pymatching.readthedocs.io/en/stable/) and
[Higgott and Gidney, Sparse Blossom](https://arxiv.org/abs/2303.15933).
The self-avoiding-walk constant is due to
[Duminil-Copin and Smirnov](https://arxiv.org/abs/1007.0575).
All phase estimates and Monte Carlo results in this report are from the supplied
computation, rather than thresholds imported from a different lattice or noise model.
