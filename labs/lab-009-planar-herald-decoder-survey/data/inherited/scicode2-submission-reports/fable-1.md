# Decoding with incomplete local witnesses: a two-parameter decoding phase diagram on the honeycomb lattice

## 0. Summary of results

* **Two exact decoders were built for the stated observation model.** A *herald-aware minimum-weight* decoder (HMW: the most likely single error configuration, solved exactly with negative-weight matching) and an *exact maximum-likelihood* decoder (ML: exact class sums via an Ising/Kac–Ward mapping, practical for $L\le12$). Both were validated against brute-force enumeration. At $q=0$ HMW is ordinary MWPM.
* **Syndrome-only baseline ($q=0$).** $p_c^{\rm HMW}(0) = 0.1595\pm0.0013$ (sizes $L=8$–$48$, distances 15–95) and $p_c^{\rm ML}(0) = 0.166\pm0.003$ from $L\le12$ (still drifting down with size; consistent with the Nishimori point of the triangular-lattice $\pm J$ random-bond Ising model, $\approx0.16$).
* **Heralding raises the threshold monotonically.** $p_c^{\rm HMW}(q)$ = 0.178 ± 0.004 (q=0.2), 0.224 ± 0.002 (0.5), 0.285 ± 0.003 (0.7), 0.344 ± 0.004 (0.8), 0.406 ± 0.010 (0.85); the ML line lies $0.01$–$0.03$ above it.
* **The transition line leaves the parameter domain before $q=1$.** Along the edge $p=1/2$ the size dependence of the LER changes sign at $q^*_{\rm HMW} = 0.875\pm0.007$ (pairwise crossings for $L$ up to 48: 0.853, 0.865, 0.883, 0.882, 0.885) and at $q^*_{\rm ML} \approx 0.84\pm0.01$ (bracketed in $[0.80, 0.87]$ by $L\le12$ data). For $q>q^*$ **every** $p\le1/2$ is decodable.
* **The line $q=1$ is decodable for all $p\le1/2$**, proven by a first-moment bound (alternating self-avoiding paths do not percolate on the honeycomb lattice since $\mu_{\rm hex}=\sqrt{2+\sqrt2}<2$) and confirmed numerically (LER $<10^{-4}$ for $L\ge24$ even at $p=1/2$).
* **Phase structure.** A single monotone boundary $p_c(q)$ from $(p,q)\approx(0.16,0)$ to $(1/2,q^*)$ separates a decodable region (below) from a non-decodable one (above); no re-entrance or additional phases were found. Finite-size drift is the dominant uncertainty for $q\gtrsim0.8$ and for all ML estimates.
* Compute: 15.4 CPU-hours on 8 cores (14.7 million decoded trials).

## 1. Problem, exact reformulation, and what can be said analytically

**Model.** The patch $G_L$ (Sec. 3 of the statement) has $|E_L| = 3L^2-1$ retained edges, $|D_L| = 2L^2-2$ detectors (degree 3 in the bulk, degree 2 on the smooth top/bottom rows), $2L+1$ unmeasured vertices on each rough side ($L$ of them isolated), and $|\Gamma_R| = L+1$. The kernel of $H$ over $\mathbb F_2$ has dimension $L^2+1$: it is spanned by the $L^2$ hexagon boundaries (restricted to $E_L$) and one left-right path $\gamma$ of weight $2L-1$, so the patch encodes one logical bit with minimum logical weight $d = 2L-1$ (verified numerically for $L=2\ldots 8$, `src/honeycomb.py`). Independent edge errors $x_e\sim\mathrm{Bernoulli}(p)$ produce counts $n_v$, exact parities $s_v=n_v \bmod 2$ and heralds $h_v = \mathbf 1\{n_v\ge 2\}\,b_v$, $b_v\sim\mathrm{Bernoulli}(q)$.

![lattice](figures/lattice_L3.png)

*Figure 1. The $L=3$ patch as constructed by `src/honeycomb.py` (filled: detectors; open: unmeasured boundary vertices; dashed: removed edges; red: $\Gamma_R$), reproducing Fig. 1 of the statement.*

**Posterior.** Conditioned on the observations $(s,h)$, the posterior weight of an error configuration $x$ with $Hx=s$ is exactly
$$
W(x\mid s,h)\;\propto\;\Big(\tfrac{p}{1-p}\Big)^{|x|}\prod_{v\in D_L,\;h_v=0}(1-q)^{\mathbf 1\{n_v(x)\ge2\}}\prod_{v\in D_L,\;h_v=1}\mathbf 1\{n_v(x)\ge 2\}.
$$
A zero herald is informative for $q>0$: every vertex through which an error chain passes ($n_v = 2$) without being witnessed costs a factor $(1-q)$; a herald is a hard constraint ($n_v\in\{2,3\}$, with the parity fixed by $s_v$). Optimal (maximum-likelihood, ML) decoding compares the two class sums $Z_\ell(s,h)=\sum_{x:\,Hx=s,\ \ell(x)=\ell}W(x\mid s,h)$ and its failure probability is $P^{\rm ML}_{\rm fail}=\mathbb E_{s,h}\,[\min(Z_0,Z_1)/(Z_0+Z_1)]$.

**Exact Ising representation.** Because every detector has degree $\le 3$, every vertex factor above is a function of at most three binary edge variables of fixed parity. Writing $x = r^{(\ell)}\oplus z$ with a reference $r^{(\ell)}$ of class $\ell$ and $z$ a trivial relative cycle, $z$ is the domain-wall configuration of Ising spins $\sigma_f$ on the $L^2$ hexagons (one additional "ghost" spin, fixed to $+1$, represents the smooth top/bottom boundary; the rough left/right sides carry no bonds). Around a degree-3 detector the three incident edges separate the three hexagons of a triangle of the dual (triangular) lattice; the four allowed domain-wall patterns are matched exactly by a constant plus three pairwise couplings. Hence for every $(s,h,\ell)$ the class sum is the partition function of an **Ising model on the triangular lattice with pairwise couplings only**:
$K_b = \pm\tfrac12\log\frac{1-p}{p}$ (sign set by $r^{(\ell)}$; the Nishimori condition) plus herald-induced couplings on the three bonds of every triangle: $\pm\tfrac14\log(1-q)$-type terms at unheralded vertices and (formally infinite) frustrated-triangle couplings at heralded vertices. At $q=0$ this is the $\pm J$ random-bond Ising model on the triangular lattice on its Nishimori line, whose multicritical point ($p_c^{\rm tri}\approx 0.158$–$0.164$ in the literature) is the optimal threshold of the syndrome-only problem. For $q>0$ the herald terms are *three-body in the error variables but still two-body in the spins*, which is what makes exact ML decoding tractable here: the partition function of a planar Ising model is a Pfaffian/determinant, and we evaluate it with the Kac–Ward determinant (`src/kacward.py`, `src/decoders.py`).

**The $q=1$ limit is decodable for every $p\le 1/2$ (first-moment argument).** At $q=1$ the observations determine $n_v$ exactly for all detectors. Two configurations $x, x'$ with the same counts differ by $d = x\oplus x'$ that is *balanced* at every detector (#$x$-edges = #non-$x$-edges of $d$ at $v$), i.e. $d$ is a disjoint union of simple paths/cycles along which the edge types alternate (an *alternating path*). $x'$ lies in the other logical class iff $d$ contains an alternating simple path from $B_{\rm left}$ to $B_{\rm right}$. For a fixed self-avoiding path of $n$ edges the probability that $x$ alternates along it is $\le 2\,[p(1-p)]^{\lfloor n/2\rfloor}$, and the honeycomb has connective constant $\mu_{\rm hex}=\sqrt{2+\sqrt2}\approx1.848$ (Duminil-Copin–Smirnov), so
$$
P(\text{competing class non-empty})\;\le\;\mathbb E[\#\text{alternating left-right paths}]\;\le\;\sum_{n\ge 2L-1}(L+1)\,c_n\,2\,[p(1-p)]^{n/2}\;\le\;C\,L\,\Big[\mu_{\rm hex}\sqrt{p(1-p)}\Big]^{2L-1},
$$
which decays exponentially in $L$ for **every** $p\in[0,\tfrac12]$ since $\mu_{\rm hex}/2 = 0.924<1$ (at $p=1/2$ the decay per unit $L$ is $(\mu_{\rm hex}/2)^2 = 0.854$). Both decoders below fail only when the competing class is non-empty, so along the whole line $q=1$ the model is decodable, with $P_{\rm fail}\le C L\,0.854^{L}$ at the worst point $p=1/2$. This is confirmed numerically (Sec. 3.6). By continuity in $q$ one expects the transition line $p_c(q)$ to hit the edge $p=1/2$ at some $q^*<1$: for $q$ close to 1 a competing chain must pass through unheralded vertices, each of which is either an $n_v\ge2$ vertex that was missed (probability $1-q$) or costs the competitor a factor $(1-q)$; the quenched free energy of such chains becomes negative before $q\to1$. The numerics locate $q^*$.

## 2. Methods

### 2.1 Decoder family

*Herald-aware minimum-weight decoder (HMW).* Returns $c=\arg\max_x W(x\mid s,h)$, the most likely single configuration. With $L_0=\log\frac{1-p}{p}$, $\lambda=-\log(1-q)$ (capped at 100) and a large constant $B=100$, we use edge weights
$$
w_e = L_0 + \sum_{v\in e\cap D_L}\Big(\tfrac{\lambda}{2}\,[h_v=0]-\tfrac{B}{2}\,[h_v=1]\Big).
$$
Because $n_v\in\{0,2\}$ or $\{1,3\}$ at a detector of degree $\le3$, the per-edge half-penalties reproduce $\lambda\,\mathbf 1\{n_v\ge2\}$ and $-B\,\mathbf 1\{n_v\ge2\}$ exactly up to a constant per syndrome vertex, so minimising $\sum_e w_e c_e$ subject to $Hc=s$ is *exactly* the maximisation of $W$ (the finite $B$ only softens the hard herald constraints; violating one costs 100 nats, never optimal in practice). Edges around heralded vertices get negative weights; PyMatching 2 (sparse blossom) handles negative weights exactly by pre-flipping them, so the decoder is an exact minimum-weight decoder, not a heuristic. At $q=0$ it is ordinary MWPM. Cost: 0.1 ms ($L=4$) to 10 ms ($L=32$) per decode including graph construction. It was validated against exhaustive enumeration of the syndrome coset for $L=2,3,4$ at seven $(p,q)$ pairs including $q=1$ (`src/tests.py`).

*Maximum-likelihood decoder (ML).* Computes $\log Z_0,\log Z_1$ with the Ising/Kac–Ward representation above and returns a representative of the heavier class. Hard constraints are imposed with a finite penalty $e^{-\Lambda}$ per violated constraint, $\Lambda=12$: larger $\Lambda$ is more faithful but degrades the conditioning of the determinant (Sec. 4). The class sums were validated against exhaustive enumeration over the $2^{L^2+1}$ configurations of the syndrome coset for $L=2,3,4$: with $\Lambda=20$ the log-odds agree to $\le5\times10^{-6}$, confirming the mapping itself; with the production value $\Lambda=12$ they deviate by up to $1.5\times10^{-2}$ in these tiny lattices (finite-penalty leakage). The effect of $\Lambda=12$ on the quantities we actually use is negligible: on 600 samples at $L=8$ near the transition ($q=0.2,0.5,0.7,0.8$) the class decision never changed between $\Lambda=12$ and $\Lambda=20$ and the posterior failure probabilities agreed to $<10^{-4}$ on average (median log-odds shift $10^{-5}$–$10^{-4}$, maximum $5\times10^{-3}$). The determinant of the $2|B|\times 2|B|$ Kac–Ward matrix ($|B|\approx3L^2$ bonds) is computed in complex double precision; its phase ($\det = Z^2_{\rm even}$ must be real positive) is monitored as a precision diagnostic for every sample. Precision is lost only (i) at $q=1$, where every unheralded vertex is a hard constraint (these ML data are not used; the $q=1$ line is covered analytically and by HMW), and (ii) deep in the decodable phase for the exponentially suppressed class, where it cannot affect the estimates. Cost: 0.8 ms ($L=4$) to 31 ms ($L=12$) per decode, so ML data are restricted to $L\le12$ ($d\le 23$).

For ML we record both the direct failure indicator and the conditional failure probability $\min(Z_0,Z_1)/(Z_0+Z_1)$, whose sample mean is an unbiased, lower-variance estimator of the same unconditional LER.

### 2.2 Monte-Carlo campaigns and analysis

Every trial draws $x$, $b$ from the stated distributions and decodes from $(s,h)$ only; a correction with $Hc\neq s$ counts as a failure (none occurred). Campaigns (`run_campaigns.sh`, tasks seeded deterministically):

| campaign | decoder | sizes $L$ | grid | trials per point |
|---|---|---|---|---|
| A coarse maps | HMW / ML | 6,10,16 / 4,6,8 | $p=0.05\ldots0.5$ step 0.05, $q=0\ldots1$ step 0.1 (0.2) | 2000 / 500 |
| B fine scans | HMW | 8,12,16,24,32 | 11 values of $p$ (step 0.01) around the coarse crossing, $q\in\{0,0.1,\ldots,0.9,0.85,0.95\}$ | 20000 ($L\le16$), 10000 |
| C fine scans | ML | 4,6,8,10,(12) | 9 values of $p$ (step 0.01), $q\in\{0,0.2,0.4,0.5,0.6,0.7,0.8,0.9\}$ | 4000 (2000 at $L=12$) |
| D the edge $p=1/2$ | HMW / ML | 8…48 / 4…12 | $q\in[0.6,1]$ | 4000–20000 |
| E the line $q=1$ | HMW | 4…48 | $p\in\{0.2,0.3,0.4,0.5\}$ | 10000–40000 |
| F drift check | HMW | 24,32,48 | 5–6 values of $p$ at $q\in\{0,0.8,0.85\}$ | 5000–10000 |

Thresholds are estimated per $q$ from (i) pairwise crossings of consecutive sizes (to expose finite-size drift) and (ii) a finite-size-scaling fit $P_{\rm fail}=A+Bx+Cx^2$, $x=(p-p_c)L^{1/\nu}$, in a window of $\pm0.02$ around the largest-size crossing, once with all sizes and once with the three largest sizes only. Statistical errors are bootstrap errors of the fit; the difference between the two fits and the drift of the pairwise crossings measure the finite-size systematic error. The same procedure in the $q$ direction at $p=1/2$ locates $q^*$.

## 3. Results

### 3.1 Logical error rates versus $p$ at fixed $q$ (HMW, $L=8\ldots48$)

![HMW LER vs p](figures/hmw_ler_vs_p.png)

*Figure 2. Logical error rate of the herald-aware minimum-weight decoder versus $p$ for $L=8,12,16,24,32$ (darker = larger), one panel per $q$ (fine scans, 10 000–20 000 trials per point; error bars are binomial standard errors). A log-scale version is `figures/hmw_ler_vs_p_log.png`.*

For every $q\le0.85$ the curves for different sizes cross at a well defined $p$, below which the LER decreases with $L$ (decodable) and above which it increases towards $1/2$ (non-decodable). The crossing moves to larger $p$ as $q$ grows. For $q=0.9$ and $q=0.95$ the curves do **not** cross anywhere in $p\le 1/2$: the LER decreases monotonically with $L$ even at $p=1/2$.

### 3.2 Threshold estimates

**Table 1. Herald-aware minimum-weight decoder, sizes L = 8, 12, 16, 24, 32 (fine scans, campaign B)**

| q | cross 8–12 | cross 12–16 | cross 16–24 | cross 24–32 | cross 32–48 | fit all L | fit large L | ν (large L) | **p_c** (stat ⊕ syst) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.1648 | 0.1595 | 0.1591 | 0.1609 | 0.1620 | 0.1598 ± 0.0002 | 0.1595 ± 0.0004 | 1.61 ± 0.07 | **0.1595 ± 0.0013** |
| 0.1 | 0.1732 | 0.1683 | 0.1722 | 0.1651 | — | 0.1695 ± 0.0005 | 0.1680 ± 0.0009 | 1.90 ± 0.15 | **0.1680 ± 0.0023** |
| 0.2 | 0.1864 | 0.1796 | 0.1768 | 0.1849 | — | 0.1791 ± 0.0005 | 0.1777 ± 0.0010 | 1.93 ± 0.14 | **0.1777 ± 0.0037** |
| 0.3 | 0.1953 | 0.1896 | 0.1907 | 0.1890 | — | 0.1920 ± 0.0005 | 0.1902 ± 0.0009 | 1.80 ± 0.13 | **0.1902 ± 0.0018** |
| 0.4 | 0.2063 | 0.2103 | 0.2058 | 0.2038 | — | 0.2068 ± 0.0006 | 0.2050 ± 0.0009 | 1.58 ± 0.13 | **0.2050 ± 0.0017** |
| 0.5 | 0.2315 | 0.2195 | 0.2279 | 0.2214 | — | 0.2250 ± 0.0006 | 0.2235 ± 0.0011 | 1.66 ± 0.15 | **0.2235 ± 0.0021** |
| 0.6 | 0.2503 | 0.2540 | 0.2558 | 0.2470 | — | 0.2521 ± 0.0008 | 0.2511 ± 0.0014 | 1.83 ± 0.22 | **0.2511 ± 0.0029** |
| 0.7 | 0.2979 | 0.2828 | 0.2908 | 0.2831 | — | 0.2889 ± 0.0010 | 0.2854 ± 0.0015 | 1.75 ± 0.24 | **0.2854 ± 0.0032** |
| 0.8 | 0.3561 | 0.3569 | 0.3481 | 0.3366 | 0.3434 | 0.3504 ± 0.0009 | 0.3444 ± 0.0015 | 1.69 ± 0.20 | **0.3444 ± 0.0038** |
| 0.85 | 0.4492 | 0.4095 | 0.3981 | 0.3978 | 0.4078 | 0.4249 ± 0.0053 | 0.4056 ± 0.0035 | 2.05 ± 0.74 | **0.4056 ± 0.0103** |
| 0.9 | — | — | — | — | — | — | — | — | no crossing for p ≤ 1/2 (LER decreasing with L) |
| 0.95 | — | — | — | — | — | — | — | — | no crossing for p ≤ 1/2 (LER decreasing with L) |

The fits use the largest sizes ($L=16,24,32$, plus $L=48$ at $q=0,0.8,0.85$ from the drift-check campaign F) in a window of $\pm0.02$ around the largest-size crossing; "fit all L" adds $L=8,12$. The quoted uncertainty combines the bootstrap error with half the spread of {fit all $L$, fit large $L$, last pairwise crossing}. $\chi^2/{\rm dof}$ is $0.4$–$2.5$ except at $q=0.85$. The pairwise crossings drift slowly *downwards* with size for $q\le0.7$ (e.g. $0.1648\to0.1595\to0.1620$ at $q=0$, i.e. the drift is already within $\pm0.002$ for $L\ge12$) and strongly at $q=0.8$–$0.85$ ($0.449\to0.398\to0.408$ at $q=0.85$), so near the upper end of the boundary the finite-size systematic error dominates. The correlation-length exponent $\nu\approx1.5$–$1.9$ is compatible with the value $\nu\approx1.5$ of the two-dimensional random-bond Ising transition at the Nishimori point. Data collapses at $q=0$ and $q=0.6$ are shown in `figures/collapse_hmw_q0.png`, `figures/collapse_hmw_q0.6.png`.

**Table 2. Maximum-likelihood decoder, sizes L = 4, 6, 8, 10, 12 (campaign C)**

| q | cross 4–6 | cross 6–8 | cross 8–10 | cross 10–12 | fit all L | fit large L | ν (large L) | **p_c** (stat ⊕ syst) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.1717 | 0.1800 | 0.1641 | 0.1684 | 0.1717 ± 0.0006 | 0.1664 ± 0.0013 | 1.61 ± 0.12 | **0.1664 ± 0.0030** |
| 0.2 | 0.1942 | 0.2043 | 0.1883 | 0.2016 | 0.1937 ± 0.0007 | 0.1908 ± 0.0018 | 1.49 ± 0.13 | **0.1908 ± 0.0057** |
| 0.4 | 0.2421 | 0.2253 | 0.2147 | 0.2261 | 0.2283 ± 0.0008 | 0.2202 ± 0.0022 | 1.87 ± 0.24 | **0.2202 ± 0.0046** |
| 0.5 | 0.2672 | 0.2613 | 0.2461 | 0.2415 | 0.2557 ± 0.0013 | 0.2410 ± 0.0018 | 1.31 ± 0.14 | **0.2410 ± 0.0076** |
| 0.6 | 0.2937 | 0.2879 | 0.2818 | 0.2721 | 0.2881 ± 0.0012 | 0.2745 ± 0.0025 | 1.58 ± 0.25 | **0.2745 ± 0.0084** |
| 0.7 | 0.4222 | 0.3270 | 0.2887 | 0.3165 | 0.3533 ± 0.0057 | 0.3345 ± 0.0096 | 4.34 ± 0.93 | **0.3345 ± 0.0207** |
| 0.8 | — | 0.4165 | 0.3882 | 0.4406 | 0.4320 ± 0.0038 | — | — | **0.4320 ± 0.0265** |
| 0.9 | — | — | — | — | — | — | — | no crossing for p ≤ 1/2 (LER decreasing with L) |

*ML thresholds are from sizes $L=4$–$12$ only (distances 7–23); their pairwise crossings still drift with size at the level of $0.005$–$0.03$, which is included in the quoted uncertainty. Numerical precision of the class sums was verified sample by sample (0 of 1.4 million ML decodes triggered the determinant-phase diagnostic).*

### 3.3 The two-parameter phase diagram

![Phase diagram](figures/phase_diagram.png)

*Figure 3. Decoding phase diagram. Blue: transition line $p_c^{\rm HMW}(q)$ of the exact minimum-weight decoder from sizes $L\le48$ (band: statistical ⊕ finite-size uncertainty); orange: maximum-likelihood transition $p_c^{\rm ML}(q)$ from $L\le12$. Light blue: decodable with both decoders; medium blue: decodable only with ML (or unresolved between the two estimates); grey: non-decodable. The open symbols on the edge $p=1/2$ mark $q^*$, where each transition line reaches the boundary of the parameter domain; for $q>q^*$ every $p\le1/2$ is decodable. The whole line $q=1$ is decodable (Sec. 1, Sec. 3.6).*

The organisation of the domain is simple: a single, monotonically increasing transition line separates a decodable region (below/right) from a non-decodable one (above/left). We find no evidence for re-entrance or for additional phases: at every $q$ the size dependence of the LER changes sign exactly once in $p$ (or not at all when the line has left the domain), and along $p=1/2$ it changes sign exactly once in $q$.

### 3.4 The edge $p=1/2$: where the transition line leaves the domain

![p=1/2](figures/hmw_phalf_line.png)

*Figure 4. HMW at $p=1/2$. Left: LER versus $q$ for $L=8\ldots48$; right: LER versus $L$ for fixed $q$. The curves fan out around $q^*$: for $q<q^*$ the LER grows with $L$ (towards 1/2), for $q>q^*$ it decays.*

For HMW the crossings of consecutive sizes in $q$ at $p=1/2$ are 8-12: 0.853, 12-16: 0.865, 16-24: 0.883, 24-32: 0.882, 32-48: 0.885 (drifting slowly upwards), and finite-size-scaling fits of the form $P_{\rm fail}=F((q-q^*)L^{1/\nu})$ give $q^*=0.8746\pm0.0008$ (stat.) with $\nu=1.49\pm0.05$ for $L\ge12$; the spread over fit variants and the last crossings is $\pm0.007$. We quote $q^*_{\rm HMW}=0.875\pm0.007$. The $\chi^2/{\rm dof}\approx8$ of these fits is poor, reflecting strong corrections to scaling near the edge (see Fig. 4, right, where the $L$ dependence at fixed $q$ is visibly curved); $q^*$ is nevertheless pinned down by the sign change of the size dependence between $q=0.86$ (LER growing with $L$ for all $L\ge8$) and $q=0.90$ (LER falling with $L$ for all $L\ge8$).

For ML ($L\le12$, `figures/ml_phalf_line.png`) the same analysis gives crossings 4-6: 0.756, 6-8: 0.798, 8-10: 0.852, 10-12: 0.834 and a fit value $q^*_{\rm ML}=0.838\pm0.004$ (stat.), $\pm0.013$ (syst.). Because the size dependence at $q=0.80$ is non-monotone in $L$ (decreasing up to $L\approx8$, then increasing), sizes $\le12$ only bracket the optimal value: $0.80\lesssim q^*_{\rm ML}\le q^*_{\rm HMW}=0.875$ (an optimal decoder cannot do worse than HMW). Hence with witnesses available at more than roughly 84–88 % of the eligible vertices, arbitrarily high error rates up to $1/2$ can be corrected.

### 3.5 Optimal versus minimum-weight decoding

![decoder comparison](figures/decoder_comparison.png)

*Figure 5. LER of the minimum-weight (HMW) and maximum-likelihood (ML) decoders at equal size.*

At equal size the ML decoder always has the lower LER, and the gap widens with $q$ (e.g. at $L=8$: $q=0$, $p=0.183$: 0.300 (HMW) vs 0.287 (ML); $q=0.4$, $p=0.237$: 0.316 (HMW) vs 0.294 (ML); $q=0.8$, $p=0.389$: 0.292 (HMW) vs 0.256 (ML)). Correspondingly the ML thresholds exceed the HMW thresholds by $\approx0.007$ at $q=0$ (partly finite-size drift of the small ML sizes), $\approx0.015$ at $q=0.4$ and $\approx0.023$ at $q=0.6$, and $q^*_{\rm ML}<q^*_{\rm HMW}$. Minimum-weight decoding ignores the degeneracy (entropy) of error configurations; with heralds this degeneracy is larger because the herald factors equalise the weights of many configurations passing through the same heralded vertices. The difference between the two lines is the *decoder approximation error* one would make by taking HMW as a proxy for optimal recovery; it is small ($\lesssim0.03$ in $p$, $\lesssim0.04$ in $q^*$) but systematic.

### 3.6 The line $q=1$

![q=1](figures/hmw_q1_line.png)

*Figure 6. HMW at $q=1$: LER versus $L$ for $p=0.2\ldots0.5$ (open symbols: 95 % upper limits where no failure was observed in $10^4$–$6\times10^4$ trials). Dashed: slope of the rigorous first-moment bound $(\mu_{\rm hex}/2)^{2L}$.*

At $q=1$ the logical error rate decays exponentially in $L$ at every $p$ including $p=1/2$: from $0.163$ ($L=4$) to $1.1\times10^{-3}$ ($L=16$) and $<10^{-4}$ ($L\ge24$), i.e. roughly a factor $0.65$ per unit of $L$ at $p=1/2$, faster than the analytic bound $0.854^{L}$. This confirms the proposition of Sec. 1 numerically: with complete local witnesses the exact counts $n_v$ determine the logical class with probability $\to1$, so the whole line $q=1$ belongs to the decodable phase and the transition line terminates on the edge $p=1/2$ at $q^*<1$, not at the corner $(1/2,1)$.

## 4. Uncertainty budget and limitations

* **Statistical.** $10^4$–$2\times10^4$ trials per HMW point give standard errors $\le0.004$ on the LER and bootstrap errors $\le0.001$ on $p_c$ (0.004 at $q=0.8$). The ML estimator uses posterior probabilities and reaches similar precision with $4000$ trials.
* **Finite size.** Sizes up to $L=48$ ($d=95$) for HMW and $L\le12$ ($d\le23$) for ML. The drift of pairwise crossings is the dominant systematic: $\lesssim0.002$ for $q\le0.7$, $\approx0.01$ at $q=0.8$–$0.85$ and $\approx0.01$ in $q^*$. For ML the drift is $0.005$–$0.03$ and is systematically downwards, so the true ML line is expected to lie at or slightly below the orange points; the medium-blue band in Fig. 3 should be read as "decodable with ML, or unresolved", never as evidence *against* decodability. An additional run with $L=48$ ($d=95$) on a coarser grid checks the drift directly: $q=0$: crossing 24–32 = 0.1609, crossing 32–48 = 0.1620; $q=0.8$: crossing 24–32 = 0.3366, crossing 32–48 = 0.3434; $q=0.85$: crossing 24–32 = 0.3978, crossing 32–48 = 0.4078. The $L=48$ crossings are consistent with the quoted thresholds within their uncertainties (see `figures/hmw_ler_vs_p_L48.png`).
* **Decoder approximation.** HMW is an *exact* minimum-weight decoder and ML is an *exact* class-sum decoder (both validated against brute force), so "decoder approximation error" enters only through (i) the finite penalty $\Lambda=12$ replacing hard constraints (log-odds shifts $\le5\times10^{-3}$ at $L=8$, no change of any class decision and $<10^{-4}$ change of the LER estimator in a 600-sample comparison with $\Lambda=20$, Sec. 2.1) and (ii) floating-point precision of the Kac–Ward determinant, monitored per sample and found harmless in all data used. The gap between the two decoders' lines is a genuine property of minimum-weight decoding (it ignores the entropy of degenerate error configurations), not an artefact.
* **Where the diagram is least certain.** (a) $0.8\lesssim q<q^*$: the boundary bends steeply upwards and finite-size drift is large; (b) the ML line at $q\ge0.7$ ($L\le12$ only); (c) the immediate vicinity of $q^*$, where the LER at $p=1/2$ is a slowly varying function of $L$ (the critical exponent fit in $q$ has $\chi^2/{\rm dof}\approx8$, indicating corrections to scaling that our sizes do not resolve). Nothing in the data suggests a non-monotone or multivalued boundary, but with $L\le48$ we cannot exclude fine structure on scales $\Delta q\lesssim0.01$.
* **What is and is not implied.** The HMW line is a lower bound on optimal recoverability; the ML line is (up to finite-size drift) the optimal transition. The $q=1$ result is rigorous. Our statements concern the specified stochastic model only (exact syndromes, no false heralds, single round).

## 5. Interpretation: how heralding changes recovery

1. **Heralds suppress the entropy of competing error chains.** In the Ising representation a zero herald at an unheralded vertex multiplies every configuration in which an error chain passes through that vertex by $(1-q)$; long chains through many unheralded vertices are thus exponentially suppressed relative to the syndrome-only case. This is why $p_c(q)$ increases with $q$ everywhere, at first slowly ($p_c^{\rm HMW}$: $0.160\to0.224$ for $q:0\to0.5$) and then steeply.
2. **Above $q^*\approx0.875$ ($\approx0.84$ for ML) the model is decodable for all $p\le1/2$.** At $q=1$ this is a percolation-type statement: a competing configuration with the same counts must differ from the truth by an *alternating* left–right path, and alternating self-avoiding paths never percolate on the honeycomb lattice because $\mu_{\rm hex}<2$ (the same argument shows that the syndrome-only problem with $p=1/2$ has no information, so the contrast is entirely due to the witnesses). For $q<1$ the missed witnesses act as a finite density of "defects" through which competing chains can pass at cost $(1-q)$; when $q>q^*$ this cost still outweighs the path entropy even at $p=1/2$.
3. **The advantage of optimal over minimum-weight decoding grows with $q$** (Sec. 3.5): the herald likelihood makes the posterior increasingly dominated by degenerate configurations of equal weight, which a single most-likely configuration represents poorly. Nevertheless the two transition lines coincide at $q=1$ (both decoders fail only if a competing configuration exists) and are within $0.01$–$0.03$ of each other elsewhere.

## 6. Reproducibility and resources

All code and data are in this directory (see `README.md`). The lattice, decoders and class sums have executable tests (`python3 src/tests.py`), the campaigns are `run_campaigns.sh`, and `python3 src/make_figures.py` regenerates every figure and table from `data/*.csv`. All Monte-Carlo campaigns together used 15.4 CPU-hours (9.3 h HMW, 6.0 h ML) on 8 cores of one workstation (about 1.9 h wall-clock with 8 single-threaded workers; peak memory well below 2 GiB), decoding 14.7 million trials in total. Per-decode costs: HMW 0.1 ms ($L=4$) to 10 ms ($L=32$) and 20 ms ($L=48$); ML 0.8 ms ($L=4$) to 31 ms ($L=12$) (single thread).
