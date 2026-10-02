# Decoding with incomplete local witnesses

**A two-parameter phase diagram on the stipulated honeycomb patch**  
Configuration-MAP decoding; domain $0\le p\le1/2$, $0\le q\le1$.

Heralding substantially enlarges the inferred decodable region. The baseline transition is near **$p=0.158$**; it rises to about **0.222 at $q=0.5$**, **0.342 at $q=0.8$**, and **0.401 at $q=0.85$**. The boundary reaches the high-error edge $p=1/2$ near **$q=0.885$**, with working range **[0.880, 0.892]**. These are finite-size estimates for the documented decoder, not optimal-recovery impossibility bounds. Perfect heralding is stronger: an analytic argument establishes decodability over the **entire** physical-error interval at $q=1$.

![Two-dimensional decoding phase diagram](figures/phase_diagram.png)

**Figure 1.** Green and purple are inferred phases; gold is the size/fit sensitivity band from fixed-$q$ sections and the $p=1/2$ endpoint. Markers have pointwise statistical intervals; open diamonds are independent fixed-$p$ checks, with gold vertical working ranges. Gray dots show sampled coordinates at $L=32$. The curve interpolates separately fitted sections, without a monotonicity constraint on those fits. The dashed curve bounds a rigorous sufficient decodable region. Interpolation is a guide between sampled sections, not a confidence statement covering every unsampled point.

## Decoder and physical checks

We generated exactly the specified merged hexagons, removed only the designated exposed sides, retained isolated boundary vertices, and measured only $D_L$. The implementation has $|E_L|=3L^2-1$, $|D_L|=2L^2-2$, $|\Gamma_R|=L+1$, and shortest logical path $d=2L-1$. Thus $L$ is not called the code distance. [The geometry figure](figures/geometry.png) shows the full $L=3$ patch.

The decoder maximizes the posterior probability of a complete error configuration. Conditional on syndrome, a degree-at-most-three detector has count $s_v$ or $s_v+2$. A positive herald requires the latter; a zero herald contributes a factor $(1-q)^{(n_v-s_v)/2}$. On configurations obeying the positive heralds, the negative log posterior, up to a constant, is

\[
A|z|+B\sum_{v:h_v=0}n_v(z),\qquad
A=\log\frac{1-p}{p},\quad B=-\frac12\log(1-q).
\]

This is a signed edge-weight matching problem with dominating penalties for hard constraints. At $q=1$, zero heralds are hard constraints too. At $q=0$, the same family reduces to syndrome-only minimum-weight matching. Heralds are vertex observations throughout: no heralded vertex is converted into a known erroneous or erased edge, and marginal herald correlations are never discarded.

For this particular patch, the finite objective can be written as a positive multiple of $N-\theta T$, where $N$ counts error edges, $T$ counts boundary edges, and $0<\theta<1/2$ in the open parameter rectangle. A path-component argument shows that the minimizing configurations are unchanged throughout that interval. We therefore use **exact integer costs** (4 on bulk edges, 3 on boundary edges, plus hard penalties); the parameter endpoints are handled explicitly. [THEORY.md](THEORY.md) gives the likelihood reduction, its proof, and the integer range check. Matching uses [PyMatching's sparse blossom solver](https://quantum-journal.org/papers/q-2025-01-20-1600/).

`decode(G,p,q,s,h)` receives only the allowed inputs, including zero heralds. It tracks the MAP configuration's logical sector and returns a full canonical correction with that syndrome and logical parity. This is equivalent under the stipulated success criterion to returning the MAP configuration itself. Every trial checks the correction syndrome; an exception or invalid correction counts as failure. Production recorded **zero invalid or missing corrections**.

Validation included graph ranks, distances, and boundary sublattices for $L=2,\ldots,12$; exhaustive enumeration of all $2^{11}$ errors and all possible observations at $L=2$; and full enumeration of the 1,024 syndrome-compatible configurations for 960 sampled $L=3$ observations. Every tested MAP objective matched the independent enumeration. A further 540 large-patch checks agreed between full configuration tracking and the callable decoder, and 513,000 paired preliminary/production trials had no logical disagreements. The validation data and executable checks are included.

## Numerical evidence and transition inference

Production used **2,706,054 trials**, at sizes **$L=8,16,24,32,48,64$** (up to $d=127$). The broad survey sampled 18 herald probabilities and physical-error probabilities spaced by 0.05 across the whole interval, using three sizes and 1,000 trials per nonzero-$p$ cell. It also checked $p=0$ explicitly. Fifteen fixed-$q$ sections were refined near their crossings; most original cells have 3,000 trials. Larger-size and edge scans use 1,800–6,000 trials per cell. All counts are fixed within each saved plan row; no result is conditioned on herald count, solver convergence, or a selected outcome.

![Finite-size logical-error curves](figures/ler_sections.png)

**Figure 2.** Representative sections, with Wilson 95% binomial intervals. The endpoint has its own scan in $q$. Lines connecting observations are guides. All additional sections and exact counts are in [the aggregated data](data/ler_aggregated.csv).

For transition estimates we fit the binomial counts to

\[
P_{\rm fail}=\tfrac12\operatorname{logistic}(a_0+a_1u+a_2u^2),
\qquad u=\frac{t-t_c}{\Delta}\left(\frac{d}{d_{\rm ref}}\right)^{1/\nu},
\]

where $t=p$ on fixed-$q$ sections, and $t=q$ on the fixed-$p$ edge scans. The primary fits use $L\ge16$; $\nu$ is a fitted nuisance parameter, not a claimed universal exponent. Statistical intervals use 400 parametric binomial bootstrap replicates. Separate quadratic binomial curve fits estimate pairwise crossings. We compare $8/16$, $16/32$, $24/48$, and, where sampled, $32/64$, rather than identifying any one crossing with an infinite-size threshold.

The working band combines the primary statistical interval, acceptable fits with different minimum sizes and added corrections proportional to $d^{-\omega}$, with $\omega=0.5,1,2$, and intervals from the larger size-doubling crossings. It is a **sensitivity envelope**, not a rigorous or simultaneous confidence bound. Individual fits, fit-quality diagnostics, unsuccessful crossing bootstraps, and all variants remain available in [scaling_fits.csv](data/scaling_fits.csv) and [crossings.csv](data/crossings.csv).

| Fixed section | Transition estimate | Statistical 95% interval | Size / fit working range |
|---|---:|---:|---:|
| q = 0 | p ≈ 0.158 | [0.158, 0.159] | [0.154, 0.162] |
| q = 0.2 | p ≈ 0.178 | [0.177, 0.179] | [0.174, 0.181] |
| q = 0.4 | p ≈ 0.206 | [0.204, 0.207] | [0.195, 0.211] |
| q = 0.5 | p ≈ 0.222 | [0.221, 0.224] | [0.214, 0.229] |
| q = 0.6 | p ≈ 0.250 | [0.248, 0.253] | [0.248, 0.259] |
| q = 0.7 | p ≈ 0.284 | [0.282, 0.286] | [0.281, 0.292] |
| q = 0.8 | p ≈ 0.342 | [0.339, 0.344] | [0.333, 0.355] |
| q = 0.85 | p ≈ 0.401 | [0.397, 0.405] | [0.390, 0.424] |
| q = 0.865 | p ≈ 0.429 | [0.423, 0.435] | [0.404, 0.447] |
| q = 0.875 | p ≈ 0.456 | [0.449, 0.465] | [0.432, 0.471] |
| q = 0.885 | not located inside domain | not quoted | high-p edge unresolved |
| p = 0.45 | q ≈ 0.874 | [0.871, 0.876] | [0.859, 0.883] |
| p = 0.49 | q ≈ 0.882 | [0.879, 0.884] | [0.870, 0.888] |
| p = 0.5 | q ≈ 0.885 | [0.884, 0.886] | [0.880, 0.892] |

At $q=0.885$, the scaling fit extrapolates outside the physical-error domain and is therefore not quoted as a threshold; the high-$p$ edge remains unresolved by that section alone. Near the high-error edge, shallow $p$ sections give much weaker localization than the separate scans at $p=0.45,0.49,0.5$. The $p=0.49$ scan gives $q_c\approx0.882$, with working range [0.870, 0.888]; it checks the approach to the endpoint without relying on its extra MAP ties.

![Finite-size crossing drift](figures/crossing_drift.png)

**Figure 3.** Crossing motion with size. The horizontal bands are the reported sensitivity envelopes, not a proof of an extrapolation law. The increasing uncertainty near the high-error edge is retained in the phase diagram.

The following independent interior points show the practical size trends. Entries give LER and failures/trials. For zero observed failures, the final number is the Wilson 95% upper limit; zero counts are not treated as proof of zero risk.

| (p, q) | L = 16 | L = 32 | L = 64 |
|---|---:|---:|---:|
| (0.13, 0) | 0.0408 (163/4000) | 0.0100 (40/4000) | 0.0008 (3/4000) |
| (0.19, 0) | 0.3942 (1577/4000) | 0.4562 (1825/4000) | 0.4975 (1990/4000) |
| (0.2, 0.5) | 0.1082 (541/5000) | 0.0562 (281/5000) | 0.0243 (97/4000) |
| (0.27, 0.5) | 0.3945 (1578/4000) | 0.4572 (1829/4000) | 0.4853 (1941/4000) |
| (0.5, 0.85) | 0.3104 (1552/5000) | 0.3620 (1810/5000) | 0.4368 (1747/4000) |
| (0.5, 0.9) | 0.1808 (1627/9000) | 0.1464 (1318/9000) | 0.1120 (448/4000) |
| (0.5, 0.95) | 0.0540 (270/5000) | 0.0126 (63/5000) | 0.0005 (2/4000) |
| (0.5, 1) | 0.0008 (4/5000) | 0/5000; <0.00077 | 0/4000; <0.00096 |

The decreasing rates support recovery in the green region; increasing or persistently large rates support the purple region for this decoder. At $(p,q)=(0.5,0.9)$, the largest patch has LER 0.1120 with 95% interval [0.1026, 0.1221]. This is finite-size evidence for suppression, not an assertion that currently accessible patches already have negligible risk. [Size-trend plots](figures/size_trends.png) include further high-herald points and the perfect-herald limit.

No reentrant phase was resolved by the two-dimensional survey or the refined sections. The observed organization is one connected low-$p$/high-$q$ decodable region and one high-$p$/low-$q$ non-decoding region. Narrow unsampled structure and residual crossing drift are not excluded. Finite-size LER itself need not be monotone, especially at $p=1/2$, where the tie convention changes; that edge was measured separately.

## Analytic constraints and limitations

There is a useful continuous-domain check on this organization. A MAP failure requires a left-to-right difference path of at least $2L-1$ edges. The joint error/herald likelihood overlap along a path of length $m$ is

\[
2[p(1-p)]^{m/2}(1+\sqrt{1-q})^{m-1}.
\]

Using the honeycomb connective constant $\mu=\sqrt{2+\sqrt2}$, proved by [Duminil-Copin and Smirnov](https://arxiv.org/abs/1007.0575), a self-avoiding-path union bound gives the sufficient condition

\[
\mu\sqrt{p(1-p)}(1+\sqrt{1-q})<1.
\]

This guarantees recovery for $p<0.07955179$ at every $q$, and for every $p\le1/2$ when $q>0.99321153$. In particular, at $q=1$ the exact local counts restrict ambiguous paths to alternating paths, whose crossing probability vanishes with size. At the opposite corner, $p=1/2,q=0$, the two logical sectors are exactly equiprobable, so even optimal decoding has logical error probability $1/2$. These statements constrain the whole continuous domain and do not come from fitting crossings.

**Statistical, finite-size, and decoder errors are distinct.** Sampling uncertainty is shown by binomial and bootstrap intervals. Size and scaling-window effects motivate the broader working band, particularly near the endpoint. Integer matching eliminates numerical weight-rounding error in production, but choosing one most probable configuration is an approximation to *logical-sector* maximum likelihood. For example, exact $L=2$ enumeration at $(p,q)=(0.5,0.9)$ gives LER 0.395974 for this decoder versus 0.373514 for optimal sector decoding. At $(p,q)=(0.3,0.9)$, where the MAP logical sector is unique, the corresponding rates are 0.272839 and 0.267432. Small-patch comparisons do not bound the resulting large-size threshold shift. Consequently the purple region is not evidence of an optimal-recovery limit, except at the explicitly proved corner.

## Resources and reproduction

The production simulations used an eight-CPU allocation, one native thread per worker, no GPU, and approximately **2.81 GiB peak container memory**, below the 32 GiB limit. Recorded production job CPU time is **5.41 core-hours**. End-to-end work through report generation took about **67 minutes**, including setup, preliminary runs, validation, analysis, and figures. Pools shared the same eight allowed CPUs. Preliminary runs are retained as diagnostics and excluded from the phase fits.

[README.md](README.md) documents the callable decoder, graph/array conventions, environment, seeds, and reproduction commands. [THEORY.md](THEORY.md) supplies the longer derivations. CSV plans, aggregate counts, per-trial compressed records, executable source, and resource logs are included. [phase_boundary.csv](data/phase_boundary.csv) contains every reported section, including those unresolved within the physical domain. 
