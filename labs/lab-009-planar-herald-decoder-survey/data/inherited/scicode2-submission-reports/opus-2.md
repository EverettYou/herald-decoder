# Decoding with incomplete local witnesses: optimal decoding phase diagram of the heralded honeycomb patch

**Principal result.** Optimal (maximum-likelihood) decoding phase diagram over $0\le p\le\tfrac12$,
$0\le q\le1$ (blue: $P_{\rm fail}\to0$; red: $P_{\rm fail}\to\tfrac12$; grey band: statistical plus
finite-size uncertainty of the boundary; details in §5.2):

![phase diagram](figures/phase_diagram.png)

**Findings**

1. **Exact optimal decoder.** The posterior factorises into edge weights and vertex factors of
   arity ≤ 3, so class probabilities are ratios of *planar Pfaffians*. We compute them exactly:
   one sparse LU per trial, 11 ms at $L=32$ and 56 ms at $L=64$. The decoder matches brute force to
   $10^{-15}$. The diagram above is therefore the diagram of *optimal* recovery, with no
   decoder-approximation error.
2. **Two phases, one boundary.** The decodable region is $\{q>q_c(p)\}$. $q_c$ is single-valued
   (proved: heralds can be thinned, so $P_{\rm fail}$ is non-increasing in $q$). It is observed to
   increase monotonically in $p$, with no re-entrance. Selected values:

   | | $q=0$ | $0.1$ | $0.3$ | $0.5$ | $0.7$ | | $p=0.30$ | $0.35$ | $0.40$ | $0.45$ | $0.50$ |
   |---|---|---|---|---|---|---|---|---|---|---|---|
   | $p_c(q)$ | 0.1645(11) | 0.1741(5) | 0.1979(10) | 0.2335(6) | 0.2988(16) | $q_c(p)$ | 0.703(9) | 0.780(4) | 0.8285(40) | 0.854(2) | **0.866(2)** |

3. **Syndrome-only baseline.** $p_c(0)=0.1645\pm0.0011$ agrees with the Nishimori point of the
   triangular random-bond Ising model (0.1633–0.1645 in the literature).
4. **Heralding.** The threshold rises slowly at small $q$ ($dp_c/dq\approx0.1$), then steeply, and
   reaches $p=\tfrac12$ at $q^*=q_c(\tfrac12)=0.866\pm0.002$. **For $q>q^*$ recovery succeeds for every
   $p\le\tfrac12$**, including $p=\tfrac12$ where the prior carries no information. At $q=1$ this is
   proved: the heralds then reveal every vertex degree, and the residual ambiguity (alternating
   paths) cannot percolate on the honeycomb lattice. A Peierls argument further proves decodability
   wherever $\mu\sqrt{p(1-p)}\,(1+\sqrt{1-q})<1$.
5. **Nature of the transition.** All 13 cuts give $\nu=1.48$–$1.61$ (mean 1.56) and the same critical
   LER ($\approx0.20$), consistent with one Nishimori-type universality class along the whole boundary.
   On the non-decodable side $P_{\rm fail}\to\tfrac12$ exponentially in $L$. Empirically the boundary
   sits at an almost constant density ($0.060$–$0.072$) of *unheralded* vertices with $n_v\ge2$.
6. **Practical decoders.** A herald-aware minimum-weight-matching decoder reproduces the $q=0$ threshold (0.160 vs 0.164) but captures only part of the heralding gain: its $(16,32)$ crossing is 0.206 vs 0.234 at $q=\tfrac12$, and at $q=0.9$ it still fails above $p\approx0.35$ where the optimal decoder never does (§5.6). The optimal diagram is thus not a property of any particular practical decoder.

Evidence: 5.4 million exact-decoder trials at $L=8$–$96$ (code distance 15–191), 14.8 CPU-hours on
≤ 8 cores. Uncertainties are split into statistical, finite-size and (zero) decoder-approximation
parts in §6.


## 1. Problem and approach in one paragraph

Errors $x_e\sim{\rm Bern}(p)$ live on the retained edges of the honeycomb patch $G_L$ (constructed exactly as
specified; `figures/patch_L3.png` reproduces Figure 1: $|V_3|=30$, $|E_3|=26$, $|D_3|=16$,
$|\Gamma_R|=4$). Detectors report the parity $s_v$ and a herald $h_v=\mathbf 1\{n_v\ge2\}b_v$,
$b_v\sim{\rm Bern}(q)$. The code distance is $d=2L-1$ (shortest left–right path). The key observation
is that the posterior $P(x\mid s,h)$ factorises into edge weights and *vertex* factors on vertices of
degree $\le3$; every single-parity tensor of arity $\le3$ is a planar matchgate, so **the optimal
(maximum-likelihood) decoder can be evaluated exactly in polynomial time** as a ratio of planar Pfaffians.
We use this exact decoder for the whole study, so the phase diagram is that of *optimal* recovery and
carries no decoder-approximation error; finite-size effects and statistics are the only uncertainties.
Structural facts (monotonicity in $q$, decodability of the whole line $q=1$, a rigorous inner bound)
are proved and used to organise and cross-check the numerics.

## 2. Decoder: exact maximum-likelihood decoding by planar Pfaffians

**Posterior.** For fixed $(p,q)$ the observation model gives
$$P(x\mid s,h)\;\propto\;\prod_{e}p^{x_e}(1-p)^{1-x_e}\prod_{v\in D_L}\mathbf 1\{n_v\equiv s_v\}\,g(n_v,h_v),\qquad
g(n,1)=q\,\mathbf 1\{n\ge2\},\;\; g(n,0)=1-q\,\mathbf 1\{n\ge2\}.$$
Given $(s,h)$ the success probability of any decoder is $P(\ell(x)=\ell(c)\mid s,h)$, so the decoder that
returns a correction in the logical class of largest posterior weight
$Z_k=\sum_{x:\,Hx=s,\ \ell(x)=k}P(x)P(h\mid x)$ is **optimal** (it minimises $P_{\rm fail}$ for every $L$).
Its phase diagram is therefore the phase diagram of optimal recovery, with no decoder-approximation error.

**Reduction to a planar dimer model.** Fix any reference $c_0$ with $Hc_0=s$ (a BFS forest to the unmeasured
boundary) and write $x=c_0\oplus y$. Then $y$ has even degree at every detector (it may end on unmeasured
vertices), and its posterior weight is
$W(y)=\prod_e r_e^{y_e}\prod_{v\in D_L}F_v(y|_v)$ with $r_e=(p/(1-p))^{1-2c_{0,e}}$ and
$F_v(y|_v)=g\big(n_v(c_0\oplus y),h_v\big)$ — an *even* tensor of arity $\le 3$.
The logical class of $x$ is $\ell(c_0)\oplus\pi(y)$, $\pi(y)=\sum_{e\in\Gamma_R}y_e \bmod 2$.
Every even tensor of arity $\le3$ is a planar matchgate; we use:

* degree-3 detector: a $K_4$ gadget (three terminals, one centre). With $y_e=1\Leftrightarrow$ the external dimer
  of $e$ is present, the internal matchings give $\Gamma(\emptyset)=\sum_i\alpha_i\beta_i=F_v(000)$ and
  $\Gamma(\{j,k\})=\alpha_i=F_v(y_j=y_k=1)$, which realises *any* non-negative even tensor, including the zeros
  forced by heralds ($h_v=1$ forbids $n_v<2$) and by $q=1$;
* degree-2 detector: one internal edge of weight $F_v(00)/F_v(11)$;
* unmeasured boundaries: two chains of EVEN$_3$ gadgets that accumulate the parity of $y$ on
  $\Gamma_L$ and on $\Gamma_R$; the chains are joined by one *virtual* edge of weight $u$ whose occupation
  equals $\pi(y)$.

The graph is planar and its structure depends only on $L$; $(s,h,p,q)$ enter only the weights.
With a Kasteleyn orientation (FKT algorithm, computed once per $L$),
$\operatorname{Pf}K(u)=\pm\,(Z'_0+uZ'_1)$ where $Z'_\pi=\sum_{\pi(y)=\pi}W(y)$.
A rank-2 update gives the posterior of the class of $c_0$ from **one** sparse LU and one solve:
$$P\big(\ell(x)=\ell(c_0)\mid s,h\big)=\frac{Z'_0}{Z'_0+Z'_1}=1+\big(K(1)^{-1}\big)_{ij}$$
for the oriented virtual edge $i\to j$. The graph has $N\simeq 8L^2$ nodes; with COLAMD ordering the
LU fill is 5–7× and one decode takes 11 ms ($L=32$), 56 ms ($L=64$), 0.24 s ($L=96$) on one core.
The decoder returns $c_0$ or $c_0\oplus z_{\rm log}$ ($z_{\rm log}$: a fixed left–right path), so $Hc=s$ always.

**Validation of exactness.**
(i) Brute-force enumeration of all $x$ with $Hx=s$ ($2^{5}$, $2^{10}$, $2^{17}$ configurations for
$L=2,3,4$): 660 random instances, including $q=0$, $q=1$, $p=1/2$: max $|P_0-P_0^{\rm brute}|=9\times10^{-16}$.
(ii) Invariances at $L=16,48$ at extreme $(p,q)$: changing $c_0$ by a random stabilizer leaves $P_0$
unchanged, changing it by a logical maps $P_0\to1-P_0$, both to $2\times10^{-14}$.
(iii) Small posterior probabilities: agreement with an independent evaluation
$\log Z'_1-\log Z'_0$ from two log-determinants to $\le10^{-6}$ (relative) for probabilities $\ge10^{-10}$.
(iv) At $q=1$ the theory below predicts that the posterior is ambiguous **iff** an $x$-alternating
left–right path exists; over 6000 trials at $p=1/2$ ($L=4,8$) the two events coincided in every trial.

## 3. Exact structural results

**(a) Monotonicity in $q$ — the boundary is a single-valued curve $q_c(p)$.** An observer with herald
rate $q'>q$ can thin its heralds (keep each with probability $q/q'$) and obtain data with exactly the
$q$-distribution. Hence $P^{\rm opt}_{\rm fail}(L;p,q')\le P^{\rm opt}_{\rm fail}(L;p,q)$ for every $L$,
and the optimal decodable region is upward closed in $q$: it is $\{q>q_c(p)\}$ (up to the boundary
itself) for a single-valued $q_c(p)$. No such argument exists in $p$ for $q>0$ (the heralds of added
noise cannot be simulated), so re-entrance in $p$ is not excluded a priori and is tested numerically.

**(b) $q=0$.** The problem is bit-flip decoding with degree-3 checks on the honeycomb lattice; optimal
decoding is governed by the random-bond Ising model on the dual triangular lattice on the Nishimori
line, $p_c(0)=0.1640$ (duality conjecture), $0.1645(5)$ (transfer matrix), $0.1633(3)$ (2026 MC).

**(c) $q=1$: decodable for every $p\le1/2$.** At $q=1$ the pair $(s_v,h_v)$ reveals $n_v$ exactly
($00\!\to\!0$, $10\!\to\!1$, $01\!\to\!2$, $11\!\to\!3$), so the posterior lives on
$\{x':n(x')=n(x)\}$. The difference $x\oplus x'$ has degree $0$ or $2$ at every detector, the two
edges having different $x$-values: it is a disjoint union of $x$-*alternating* cycles and paths
between unmeasured vertices, and a logical error needs an alternating left–right path. Orienting
each edge black→white if $x_e=1$ and white→black otherwise turns alternating paths into directed
paths. A fixed path of $n$ edges is alternating with probability $\le2(p(1-p))^{(n-1)/2}$, and there
are $\le(L+1)\,C_\epsilon(\mu+\epsilon)^n$ self-avoiding left–right paths with
$\mu=\sqrt{2+\sqrt2}$ (honeycomb connective constant), so
$P_{\rm fail}\le C\,L\,(\mu\sqrt{p(1-p)})^{2L-1}\to0$ since $\mu/2<1$.

**(d) A rigorous inner bound for all $q$.** $P^{\rm ML}_{\rm fail}\le P^{\rm MAP}_{\rm fail}$, and a MAP
failure implies a left–right self-avoiding path $\gamma$ (a component of $x\oplus\hat x$; the posterior
ratio factorises over the vertex-disjoint components) with
$\Lambda(\gamma)=P(x\oplus\gamma\mid s,h)/P(x\mid s,h)\ge1$. By Markov's inequality
$P(\Lambda\ge1)\le\mathbb E\,\Lambda^{1/2}$, and a $2\times2$ transfer matrix gives exactly
$$\mathbb E\,\Lambda(\gamma)^{1/2}=2\,(p(1-p))^{n/2}\,(1+\sqrt{1-q})^{\,n-1}\qquad(n=|\gamma|),$$
(the third edge at each vertex drops out: a non-alternating passage turns $n_v\le1$ into $n_v\ge2$,
factor $1-q$, or $n_v\ge2$ into $n_v\le1$, factor $0$ if heralded and $(1-q)^{-1}$ otherwise). Summing over
self-avoiding paths: **the model is decodable whenever $\mu\sqrt{p(1-p)}\,(1+\sqrt{1-q})<1$.** This
region contains $p<0.0798$ at $q=0$ and the whole range $p\le1/2$ for $q>0.9932$; it is a
guaranteed-decodable region, much smaller than the numerically determined one.

## 4. Numerical design

**Trials and estimators.** Each trial samples $x$, $b$ exactly as stipulated, forms $(s,h)$, decodes, and
records the failure indicator $\mathbf 1\{\ell(x\oplus c)=1\}$ (the correction always satisfies $Hc=s$;
this is asserted in the code). Because the decoder computes the *exact* posterior $P_0$ of the class it
returns, the conditional failure probability of a trial is $\min(P_0,1-P_0)$, and
$\hat P_{\rm RB}=\frac1N\sum_t\min(P_0^{(t)},1-P_0^{(t)})$ is an unbiased (Rao–Blackwellised) estimator
of the same unconditional $P_{\rm fail}$ as the indicator mean, with ~8× smaller variance near
threshold. Both are stored; they agree everywhere (e.g. 627 coarse points: mean pull $-0.08$,
$\max|{\rm pull}|=2.5$). Fits use $\hat P_{\rm RB}$. Nothing is conditioned on outcomes or
convergence; there were zero numerical anomalies ($P_0\notin[-10^{-7},1+10^{-7}]$) in all runs.
Random streams are `numpy` `SeedSequence(20260926, spawn_key=(L, 10^6 p, 10^6 q, chunk[, stream]))`,
so every number is reproducible.

**Sampling plan (adaptive, 3 stages).**
1. *Coarse map* of the whole square: $p\in\{0.05,0.075,\dots,0.5\}$ × $q\in\{0,0.1,\dots,1\}$,
   $L=8,16,32$, 1500 trials each; plus a fixed-$p$ scan $q\in\{0.62,\dots,0.96\}$ at
   $p=0.30,\dots,0.50$ where the boundary is shallow in $q$.
2. *Refined cuts through the boundary*, 9 points each, $L=8,12,16,24,32,48,64$
   (code distance $2L-1$ = 15 … 127) with 6000/6000/6000/6000/4000/2500/2000 trials:
   fixed-$q$ cuts at $q=0,0.1,\dots,0.7$ (window $\pm0.016$ in $p$; $\pm0.02$ at $q=0.7$) and fixed-$p$
   cuts at $p=0.30,0.35,0.40,0.45,0.50$ (window $\pm0.04$ in $q$) — each cut is chosen roughly
   transverse to the boundary.
3. *Deep-phase points*: 11 points on both sides of the boundary, $L=8$–96 (4000 trials for $L\le32$,
   2000/1500/600 at $L=48/64/96$), and an $L=96$ extension (800 trials per point) of the cuts
   $q=0,0.4,0.7$ and $p=0.4,0.5$.

Auxiliary runs: the $q=1$ alternating-path crossing study ($L=4$–24, up to $4\times10^5$ trials per point)
and the MWPM baseline on the coarse grid (3000 trials per point).

**Finite-size analysis.** For each cut (scanned variable $x=p$ or $q$):
(i) pairwise crossings $x_\times(L_a,L_b)$, from weighted quadratic fits of both curves on the five grid
points nearest the crossing, with a parametric bootstrap; (ii) global scaling fits
$P=\sum_{k\le3}a_k u^k$, $u=(x-x_c)L^{1/\nu}$, restricted to the critical window $P>0.03$ (below it a
cubic turns over and biases $\chi^2$ and $\nu$), for size sets $L\ge8,12,16,24,32$, plus a fit with a
correction term $+bL^{-\omega}$ ($\omega\ge0.5$) on all sizes. The quoted $x_c$ is the $L\ge24$ fit
($\chi^2/{\rm dof}=0.7$–$1.5$ on every cut). Its statistical error is the bootstrap standard deviation;
the *finite-size systematic* error is the largest shift among the $L\ge16$, $L\ge32$ and corrected fits
and the largest doubling-pair crossing. The drift of $x_\times(L,2L)$ with $L$ is shown explicitly.
Away from the boundary, phases are assigned from the sign and significance of the size trend.

## 5. Results

### 5.1 Global organisation of the $(p,q)$ square

![coarse](figures/coarse_trend_map.png)

*Coarse map (284 distinct $(p,q)$ points, $L=8,16,32$). Left: significance of the size trend
$[P(32)-P(8)]/\sigma$; right: $\log_{10}[P(32)/P(8)]$. LER curves per $q$: `figures/coarse_ler_small_multiples.png`.*

* The square splits into two regions: an upper-left region where $P_{\rm fail}$ falls with $L$
  (142 points) and a lower-right region where it rises or sits at $1/2$ (134 points). The 8 points
  whose trend is below $3\sigma$ all lie next to the boundary.
* **Monotonicity.** At every size $P_{\rm fail}$ is non-increasing in $q$ (0 of 570 neighbouring steps rise by
  $>2\sigma$), as proved in §3a, and non-decreasing in $p$ (0 of 594 steps fall by $>2\sigma$), which
  is *not* guaranteed a priori for $q>0$. So there is no re-entrance at the resolution of the grid
  ($\Delta p=0.025$; $\Delta q=0.1$, or $0.02$ for $p\ge0.3$). Each fixed-$q$ section with $q<q_c(1/2)$
  has exactly one transition; for $q>q_c(1/2)$ there is none.

### 5.2 The transition boundary

![phase diagram](figures/phase_diagram.png)

**Table 1 — boundary estimates** (exact ML decoder; $L=8$–$64$, plus $L=96$ on the cuts
$q=0,0.4,0.7$ and $p=0.4,0.5$). The central value is the $L\ge24$ scaling fit; *stat.* is its
bootstrap error; *finite-size sys.* is the largest shift among the $L\ge16$, $L\ge32$ and
correction-to-scaling fits and the largest doubling-pair crossing.

| cut | estimate | stat. | finite-size sys. | total | ν (central fit) | χ²/dof | P_fail at x_c | largest doubling-pair crossing |
|---|---|---|---|---|---|---|---|---|
| q = 0.00: p_c | 0.1645 | 0.0002 | 0.0011 | 0.0011 | 1.57 ± 0.03 | 1.00 | 0.199 | 0.1634 ± 0.0006 |
| q = 0.10: p_c | 0.1741 | 0.0002 | 0.0004 | 0.0005 | 1.55 ± 0.03 | 0.66 | 0.203 | 0.1746 ± 0.0006 |
| q = 0.20: p_c | 0.1850 | 0.0002 | 0.0007 | 0.0007 | 1.55 ± 0.04 | 0.91 | 0.204 | 0.1846 ± 0.0006 |
| q = 0.30: p_c | 0.1979 | 0.0002 | 0.0010 | 0.0010 | 1.56 ± 0.04 | 1.33 | 0.205 | 0.1981 ± 0.0005 |
| q = 0.40: p_c | 0.2131 | 0.0002 | 0.0018 | 0.0018 | 1.61 ± 0.04 | 1.07 | 0.200 | 0.2123 ± 0.0007 |
| q = 0.50: p_c | 0.2335 | 0.0003 | 0.0006 | 0.0006 | 1.53 ± 0.05 | 0.89 | 0.204 | 0.2331 ± 0.0007 |
| q = 0.60: p_c | 0.2601 | 0.0003 | 0.0017 | 0.0017 | 1.58 ± 0.07 | 1.06 | 0.206 | 0.2598 ± 0.0006 |
| q = 0.70: p_c | 0.2988 | 0.0003 | 0.0016 | 0.0016 | 1.59 ± 0.04 | 1.49 | 0.205 | 0.2974 ± 0.0014 |
| p = 0.30: q_c | 0.7025 | 0.0008 | 0.0084 | 0.0085 | 1.49 ± 0.06 | 0.95 | 0.205 | 0.7056 ± 0.0023 |
| p = 0.35: q_c | 0.7804 | 0.0006 | 0.0037 | 0.0037 | 1.48 ± 0.05 | 1.05 | 0.209 | 0.7806 ± 0.0019 |
| p = 0.40: q_c | 0.8285 | 0.0005 | 0.0040 | 0.0040 | 1.52 ± 0.03 | 1.09 | 0.203 | 0.8296 ± 0.0017 |
| p = 0.45: q_c | 0.8535 | 0.0005 | 0.0021 | 0.0022 | 1.61 ± 0.04 | 1.12 | 0.208 | 0.8549 ± 0.0016 |
| p = 0.50: q_c | 0.8664 | 0.0004 | 0.0018 | 0.0019 | 1.55 ± 0.02 | 1.46 | 0.208 | 0.8651 ± 0.0017 |

Interpolated boundary (monotone PCHIP through Table 1; files `data/boundary_qc_of_p.csv`, `data/boundary_pc_of_q.csv`):

| $q$ | 0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.75 | 0.8 | 0.85 | 0.866 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $p_c(q)$ | 0.1645 | 0.1741 | 0.1850 | 0.1979 | 0.2131 | 0.2335 | 0.2601 | 0.299 | 0.328 | 0.367 | 0.44 | 0.5 |

* **Syndrome-only baseline ($q=0$):** $p_c(0)=0.1645\pm0.0011$, in agreement with the Nishimori point of the
  triangular-lattice random-bond Ising model (0.1640 conjectured; 0.1645(5), 0.1633(3) numerically). This is
  an end-to-end check of lattice, decoder and analysis. At $q=0$ the crossings keep drifting slowly
  downward up to $L=96$ ($(48,96)$: 0.1634(6)), a known feature of the Nishimori point; this is what sets the
  larger error at $q=0$.
* **Heralding raises the threshold monotonically:** slowly at first ($dp_c/dq\simeq0.095$ at $q=0$), then
  faster: $p_c=0.2335$ at $q=\tfrac12$, $0.299$ at $q=0.7$. The boundary reaches the edge of the domain,
  $p=\tfrac12$, at
  $$q^*\equiv q_c(\tfrac12)=0.8664\pm0.0004\,({\rm stat})\pm0.0018\,({\rm finite\ size}).$$
  For $q>q^*$ every $p\le\tfrac12$ is decodable. Near $p=\tfrac12$ the boundary is flat
  ($dq_c/dp\approx0.25$ versus $\approx2$ at $p=0.3$), so fixed-$q$ thresholds for $0.85\lesssim q<q^*$
  are poorly determined in $p$ (e.g. $p_c(0.85)\approx0.44$), even though $q_c(p)$ is sharp.
* **Independent cuts agree:** the fixed-$q$ cut at $q=0.7$ gives $p_c=0.2988(16)$; the fixed-$p$ cut at
  $p=0.30$ gives $q_c=0.703(9)$. These are the same boundary point reached from two directions.
* **One universality class along the whole boundary:** all 13 cuts give $\nu=1.48$–$1.61$ (mean 1.56,
  $\chi^2/{\rm dof}=0.7$–$1.5$), close to the 2D random-bond-Ising Nishimori value $\nu\simeq1.50$. The LER at
  the critical point is also the same everywhere, $P_{\rm fail}(x_c)=0.198$–$0.209$.
* **Finite-size drift** (`figures/cut_crossing_drift.png`): within errors, crossings of $(L,2L)$ approach the
  fitted values from above in $p$ and from below in $q$, so the decodable region shrinks slightly as
  $L$ grows. At the largest sizes the drift is $\lesssim0.002$ in $p$ and $\lesssim0.005$ in $q$, inside the
  quoted finite-size errors. LER curves and data collapse for all cuts: `figures/cut_curves_{0,1,2,3}.png`.

![cuts](figures/cut_curves_2.png)

### 5.3 Inside the phases

![deep](figures/deep_phase_scaling.png)

* **Decodable side** (D1–D5 up to $L=96$): $P_{\rm fail}$ falls monotonically, and faster with $L$. Examples:
  $(0.14,0)$: $0.109\to1.7\times10^{-4}$; $(0.5,0.92)$: $0.149\to2.4\times10^{-3}$; $(0.35,0.85)$:
  $0.154\to5.2\times10^{-3}$ between $L=8$ and $96$. The mean posterior log-odds of the true class grows
  linearly in $L$ (a finite domain-wall tension: ordered phase).
* **Close to $q^*$** ($p=0.5$, $q=0.88$, i.e. $q-q^*\approx0.014$): a slow but steady decrease,
  $0.214\to0.104$ over $L=8\to96$, as expected just inside the decodable phase.
* **Non-decodable side** (N1–N4): $\tfrac12-P_{\rm fail}$ decays exponentially in $L$ (rates 0.031–0.042 per
  unit $L$) and reaches $0.487$–$0.495$ at $L=96$; the log-odds of the true class goes to 0. So
  $P_{\rm fail}\to\tfrac12$ throughout the red region, not merely a nonzero limit.

### 5.4 The line $q=1$

![q1](figures/q1_crossing.png)

The ML posterior at $q=1$ is ambiguous exactly when an $x$-alternating left–right path exists (§3c;
checked trial by trial). The crossing probability decays as $e^{-0.44L}$ at $p=\tfrac12$ (and faster for
smaller $p$), much faster than the rigorous first-moment rate $0.158$. The ML failure rate at $p=\tfrac12$ is
$2.1\times10^{-2}$, $2.8\times10^{-3}$, $4.2\times10^{-4}$ at $L=8,12,16$, and **exactly zero** for all
$L\ge24$ (no competing class: the posterior weight of the other class vanishes identically).

### 5.5 How heralding changes recovery — interpretation

* **LER at fixed size.** At $p=0.15$, $L=32$: $P_{\rm fail}=7\times10^{-2}$ ($q=0$), $3.5\times10^{-3}$
  ($q=0.3$), $9\times10^{-5}$ ($q=0.6$), $<10^{-10}$ ($q\ge0.7$). At $p=0.2$ (above the $q=0$ threshold):
  $0.47\to0.22\to8\times10^{-3}\to3\times10^{-7}$ for $q=0,0.3,0.6,0.8$
  (`figures/herald_effect_L32.png`).
* **Mechanism.** A herald at an even-syndrome vertex certifies that an error chain *passes through* it; a
  herald at an odd vertex reveals all three incident errors. With all heralds present ($q=1$) the decoder
  knows every vertex degree $n_v$, and the only remaining ambiguity is $x$-alternating paths. On the
  honeycomb lattice these cannot percolate (connective constant $\mu=1.848<2$), so recovery succeeds even
  at $p=\tfrac12$, where the prior is uninformative. Missed heralds ($b_v=0$ at $n_v\ge2$) restore
  non-alternating passages of logical domain walls.
* **An empirical rule.** Along the entire boundary the density of *unheralded multi-error vertices*,
  $\rho_{\rm hidden}=(1-q)\,P(n_v\ge2)=(1-q)(3p^2-2p^3)$, stays in the narrow band
  $0.060$–$0.072$ (mean 0.067), from the syndrome-only point ($\rho=0.072$ at $p=0.1645$) to $q^*$
  ($\rho=0.067$ at $p=\tfrac12$) (`figures/boundary_hidden_density.png`). The one-parameter curve
  $q=1-\rho_{\rm hidden}(p_c(0),0)/P(n\ge2)$ reproduces $q_c(p)$ to within 0.01–0.04. Heralded weight-2
  vertices are thus almost harmless, and recovery is lost when unseen chain links reach roughly 7% of
  the vertices. This rule is empirical and interpretive; it is not used to draw the diagram.

![hidden](figures/boundary_hidden_density.png)

### 5.6 A practical decoder: decoder-approximation error made visible

![mwpm](figures/mwpm_vs_ml.png)

For contrast we ran a simple **herald-aware MWPM** decoder (`src/mwpm.py`) on the coarse grid. Its edge
weights are $\log[(1-\pi_e)/\pi_e]$, with $\pi_e$ the local posterior marginal of $x_e$ given the
observations at the two endpoints; at $q=0$ this is plain MWPM. Its $(16,32)$ crossings versus those of
the exact decoder at the *same* sizes:

| $q$ | 0 | 0.3 | 0.5 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|
| MWPM | 0.160 | 0.188 | 0.206 | 0.255 | 0.296 | 0.349 |
| exact ML | 0.162 | 0.198 | 0.234 | 0.298 | 0.377 | none (all $p$ decodable) |

Without heralds MWPM is nearly optimal. With heralds it captures about two thirds of the threshold gain
at $q=\tfrac12$ ($+0.046$ versus $+0.072$), and much less at large $q$. At $q=0.9$ it still fails above
$p\approx0.35$, and at $q=1$ its LER at $L=32$ is 0.004–0.07 for $p=0.3$–$0.5$, where the exact decoder
is error-free. Exploiting the heralds needs the *global* degree constraints, which only the exact
decoder enforces. This is the decoder-approximation error the problem warns about: a limitation of
MWPM, not of recoverability.

## 6. Uncertainty budget and limitations

| source | size | how it is controlled |
|---|---|---|
| decoder approximation | **none** | the decoder is the exact ML (optimal) decoder: brute force to $10^{-15}$ ($L\le4$), invariances to $2\times10^{-14}$ ($L\le48$) |
| floating point | $<10^{-6}$ relative on posteriors $\ge10^{-10}$ | independent two-determinant evaluation; LERs below $\sim10^{-10}$ are quoted only as bounds |
| statistical | $\le0.0003$ in $p_c$, $\le0.0008$ in $q_c$ | Rao–Blackwellised estimator (≈8× variance reduction, validated against the indicator mean), parametric bootstrap |
| finite size | 0.0004–0.0018 in $p_c$; 0.0018–0.008 in $q_c$ | seven sizes $L=8$–64 (+96), fits with different $L_{\min}$ and a correction term, largest doubling-pair crossing; drift shown explicitly |
| interpolation between cuts | small | 13 boundary estimates in both cut directions plus a 284-point grid; monotonicity observed at every size |

**Limitations.**
1. *Finite sizes.* Phase assignment near the boundary is an extrapolation from $d\le127$ ($d\le191$
   for five cuts). The fits assume a single scaling variable with ν common to all sizes. The data support
   this ($\chi^2/{\rm dof}\approx1$ for $L\ge24$), but a crossover beyond $L=96$ cannot be excluded. The
   systematic column is the defensible error; the statistical column is not.
2. *Resolution of fine structure.* Monotonicity of $P_{\rm fail}$ in $p$ was tested on the grid; features
   narrower than the grid spacing (e.g. a re-entrant sliver thinner than $\Delta p=0.025$) are not
   excluded by the numerics. The optimal region is monotone in $q$ by proof.
3. *Near $p=\tfrac12$ the boundary is flat*, so for $0.85\lesssim q<q^*$ the fixed-$q$ threshold
   $p_c(q)$ is uncertain by several hundredths in $p$, although $q_c(p)$ is determined to $\pm0.002$.
4. *Scope.* The diagram is that of optimal decoding with the true $(p,q)$ known to the decoder, which is
   what the model stipulates. A practical decoder (§5.6) has a smaller decodable region; conversely, a
   limitation of any practical decoder does not move the optimal boundary.
5. *Rigorous parts.* Monotonicity in $q$, decodability of the line $q=1$ for every $p\le\tfrac12$, and the
   inner region $\mu\sqrt{p(1-p)}(1+\sqrt{1-q})<1$ are proved (asymptotically in $L$). The
   non-decodability of the red region is established numerically only.

## 7. Reproducibility and computational resources

* Everything is produced by `run_all.sh` (resumable). Plans are in `data/plans/*.json` and raw chunk
  results in `data/*.jsonl`; each chunk is reproducible from its seed
  `SeedSequence(20260926, spawn_key=(L, 10^6p, 10^6q, chunk[, stream]))`.
  `data/ler_table_ml.csv` lists every LER estimate behind every figure.
* Environment: Python 3.11, numpy 2.1.3, scipy 1.14.1 (SuperLU), pandas 2.2.3, matplotlib 3.9.2, PyMatching 2.4.0
  (baseline only). Hardware: one workstation, 8 worker processes (cgroup limit of 8 CPUs, Intel Xeon
  Platinum 8559C), peak memory < 4 GB; no GPU.
* Cost: 5.36 million exact-decoder trials (14.8 CPU-hours), 1.88 million MWPM trials (1.4 CPU-hours) and 6.2 million $q=1$ crossing tests (0.5 CPU-hours); about 2.2 h of wall time on 8 cores for all simulations. The exact decoder takes 1.2 ms ($L=8$), 11 ms ($L=32$), 56 ms ($L=64$) and
  0.24 s ($L=96$) per trial on one core.

