# Decoding with incomplete local witnesses: a two-parameter decoding phase diagram on the honeycomb lattice

## Summary

We built an **exact maximum-likelihood (ML) decoder** for the heralded honeycomb model — a
transfer-matrix / tensor-network contraction of the posterior over *all* error configurations
consistent with the syndrome `s` and the herald vector `h` — validated it by brute force, measured
its logical error rate (LER) by Monte Carlo for patch sizes L = 4 … 24 over the whole domain
0 ≤ p ≤ 1/2, 0 ≤ q ≤ 1 (3.76 million decoded trials), and located the decoding transition by
finite-size scaling.

**Result (Fig. 1).** The domain is organised by a *single* transition line that separates one
decodable region from one non-decodable region, and the decodable region grows monotonically with
the herald availability q:

* at q = 0 (syndrome only) the threshold is p_c = 0.166 ± 0.002, consistent with the Nishimori point
  of the ±J random-bond Ising model on the triangular lattice (0.164–0.166);
* p_c(q) increases smoothly and convexly: 0.176 (q=0.1), 0.187 (0.2), 0.199 (0.3), 0.217 (0.4),
  0.237 (0.5), 0.265 (0.6), 0.306 (0.7), 0.381 (0.8) (uncertainties 0.002–0.016, Table 2);
* the line reaches the edge p = 1/2 of the domain at **q\* = 0.858 ± 0.015**; for q ≥ q\* there is no
  threshold at all — the logical bit is recoverable for *every* p ≤ 1/2, even when each edge is an
  unbiased coin;
* at q = 1 this is an exact statement (self-avoiding-walk argument, Sec. 3b), and the LER decays as
  e^{−L/ξ} with ξ ≈ 2.2 at p = 1/2.

The dominant uncertainty is finite-size drift of the crossings (towards smaller p at fixed q, larger q
at fixed p); statistical errors and the decoder-approximation error are one to two orders of
magnitude smaller. No re-entrant or multi-valued behaviour of the boundary was found.

![Figure 1](figures/phase_diagram.png)

**Figure 1.** Decoding phase diagram of the ML decoder. Markers: finite-size trend at every simulated
point (blue: LER decreases between the two largest sizes available there, red: increases, grey:
|z| < 2). Black: transition estimates from the fixed-q sections (◆, p_c(q)) and fixed-p sections (▲,
q_c(p)) with combined statistical+systematic error bars, a monotone interpolant, and its uncertainty
band. Thick blue edges are exactly decodable (p = 0; q = 1; p = 1/2 for q ≥ q\*).

---

## 1. Model, geometry and the structure of the decoding problem

The patch G_L is built exactly as specified (`honeycomb.py`; Fig. 2): L×L hexagons with centres
(3a, 2b + (a mod 2)), exposed sides 2,3 of column 0 and 0,5 of column L−1 removed, B_left / B_right
= endpoints of the removed edges, D_L = V_L \ (B_left ∪ B_right). Every detector has degree 3 (bulk)
or 2 (top/bottom rows), every boundary vertex has degree 1 or 0 (the isolated corner vertices are
kept in V_L), and Γ_R is exactly the set of the L+1 horizontal edges of the last hexagon column.

| L | \|V_L\| | \|E_L\| | \|D_L\| | \|B_left\| = \|B_right\| | \|Γ_R\| | dim ker H | shortest logical |
|---|---|---|---|---|---|---|---|
| 2 | 16 | 11 | 6 | 5 | 3 | 5 | 3 |
| 3 | 30 | 26 | 16 | 7 | 4 | 10 | 5 |
| 4 | 48 | 47 | 30 | 9 | 5 | 17 | 7 |
| 8 | 160 | 191 | 126 | 17 | 9 | 65 | 15 |
| 14 | 448 | 587 | 390 | 29 | 15 | 197 | 27 |
| 24 | 1248 | 1727 | 1150 | 49 | 25 | 577 | 47 |

**Table 1.** Lattice statistics (`python3 honeycomb.py`). Generally |B_left| = 2L+1, |Γ_R| = L+1,
dim ker H = L²+1, and the shortest left–right path has 2L−1 edges.

![Figure 2](figures/fig_lattice.png)

**Figure 2.** The L = 3 patch (left, with (X,Y) labels) and L = 6 (right). Filled circles: detectors;
open circles/squares: B_left / B_right; dashed: removed construction edges; red: Γ_R.

*Sectors.* H has full row rank and dim ker H = L² + 1 (verified for L ≤ 8). The L² "hexagon elements"
(the boundary of a hexagon restricted to E_L — a closed loop in the bulk or a B_left–B_left /
B_right–B_right path in the outer columns) are independent, all have ℓ = 0, and together with one
left–right path γ (ℓ(γ) = 1) they span ker H (`validate.py`). Hence the solutions of Hx' = s form
exactly two cosets distinguished by ℓ: the model is a planar code with rough left/right and smooth
top/bottom boundaries, ℓ measures the left–right homology, and success means choosing the right coset.

*Posterior.* Given (s, h), the posterior weight of a candidate x' is

    W(x'|s,h) = ∏_e p^{x'_e}(1−p)^{1−x'_e} · ∏_{v∈D} 1{n_v(x') ≡ s_v (mod 2)} · f(n_v(x'); h_v),
    f(n; 1) = q·1{n ≥ 2},      f(n; 0) = 1 − q·1{n ≥ 2}.

The herald factor depends on the *count* n_v ∈ {0,1,2,3}, not only on its parity: (h_v, s_v) = (1, 0)
forces n_v = 2 (exactly one of the three edges is error-free), (1, 1) forces n_v = 3 (all three edges
are errors), and h_v = 0 down-weights n_v ≥ 2 by a factor 1 − q. The zero entries of h therefore
carry information as soon as q > 0, and at q = 1 the pair (s_v, h_v) determines n_v exactly.

## 2. The decoder

**Decision rule.** The decoder computes the two sector weights
Z_ℓ = Σ_{x': Hx' = s, ℓ(x') = ℓ} W(x'|s,h) and returns a correction in the heavier sector:
c = x₀ if Z₀ ≥ Z₁, else c = x₀ ⊕ γ. Here x₀ is a canonical solution of Hx₀ = s (XOR of the tree paths
from every flagged detector to B_left in a fixed spanning forest, so ℓ(x₀) = 0) and γ is the
bottom-row left–right path. Hc = s holds by construction, so P_fail = P[ℓ(x ⊕ c) = 1] =
P[argmax_ℓ Z_ℓ ≠ ℓ(x)]. Exact ties (Z₀ = Z₁; they occur systematically only at p = 1/2, q = 0, where
every trial is a tie and the LER is exactly 1/2) go to sector 0 or are broken by the optional
randomness input.

**Computing Z_ℓ.** Z_ℓ is a tensor network on the honeycomb lattice: a two-valued index on every
edge, a symmetric 3-leg (2-leg at the top/bottom rows) tensor T_v[x₁,x₂,x₃] = 1{Σx ≡ s_v} f(Σx; h_v)
at every detector, edge weights p^x(1−p)^{1−x}, free sums at the unmeasured B vertices, and a parity
projector onto ℓ on Γ_R. It is contracted column by column in the X direction. The cut between two
hexagon columns crosses the L+1 horizontal edges of a column, and the transfer operator from column a
to a+1 is a matrix-product operator of bond dimension 2 assembled from the 2(L+1) detectors between
the cuts (`decoder.build_step_mpo`); the diagonal edges are the MPO bonds. Two back-ends share it:

* *exact*: dense boundary vector over the 2^{L+1} cut configurations, cost O(L² 2^L) per trial
  (0.3 ms at L = 6, 6 ms at L = 10, 0.2 s at L = 14 on one core);
* *MPS*: the boundary vector is a matrix-product state of bond dimension χ, re-compressed after every
  column (QR sweep, then SVD truncation), cost O(L² χ³) (8 ms at L = 12, 40 ms at L = 20, 60 ms at
  L = 24 for χ = 16).

Both are batched over trials. The q = 0 limit (h ≡ 0, f ≡ 1) runs through the same code, so the
syndrome-only baseline and the heralded decoder are one consistently specified decoder family.

**Validation.**
1. *Brute force.* For L = 2, 3, 4 the full kernel of H (32, 1024 and 131 072 elements) was
   enumerated and Z₀, Z₁ summed directly for random (p, q, s, h), including q = 0 and q = 1. The
   transfer matrix and the MPS (χ = 64 and χ = 4) reproduce log Z₀ and log Z₁ to 10⁻¹⁵, including
   cases where one sector has zero weight (`python3 validate.py` → "ALL CHECKS PASSED").
2. *Correction validity.* Returned corrections satisfy Hc = s in all tests.
3. *MPS truncation.* Against the exact contraction at L = 10, 12, 14 (400/160 trials at each of seven
   (p, q) points spanning the domain, including p = 1/2), and against χ = 48 at L = 20, χ = 16
   reproduces log(Z₁/Z₀) to 10⁻⁷–10⁻¹⁰, changes **no** decision in ≈ 6 000 compared trials, and shifts
   the per-trial posterior failure probability by < 10⁻⁷ (`data/chi_convergence.txt`,
   `data/chi_check_L14_L20.txt`, `data/chi_check_L20.txt`). Even χ = 8 changed no decision.

We use the exact back-end for L ≤ 10 and χ = 16 for L ≥ 12. The decoder-approximation error of every
LER reported below is at least three orders of magnitude below its statistical error, so the phase
diagram is that of **optimal recovery** for this observation model, not of a heuristic decoder.

**API.** `decode(patch, p, q, s, h, rng=None, chi=None)` → `c` (uint8 over `patch.edges`), plus
`class_log_weights` (batched) and `reference_solution`; graph and array conventions are documented
in `README.md` and the module docstrings.

## 3. Analytical results that frame the numerics

**(a) Effective statistical-mechanics model.** Writing x' = x_ref ⊕ z with z ∈ ker H and Ising spins
σ_f = ±1 on the hexagons (z = domain walls), Z_ℓ is the partition function of a random-bond Ising
model on the *triangular* lattice (hexagon centres) with equal (ℓ = 0) or opposite (ℓ = 1) fixed
boundary spins on the top and bottom rows and free left/right boundaries. The wall pattern at a
degree-3 vertex takes only four values (none, or one of three pairs), so every herald factor is exactly
representable by two-spin couplings on the three triangular bonds around the vertex,
J_e = ¼ ln[F₀ F_{e'e''} / (F_{ee'} F_{ee''})] in terms of the four local weights. The ML decoder thus
evaluates a planar RBIM on its Nishimori surface (it uses the true p and q). At q = 0 this is the
standard ±J model on the triangular lattice whose multicritical point, p_c ≈ 0.164–0.166 in the
literature, is the syndrome-only ML threshold; our estimate 0.166 ± 0.002 agrees. Heralded vertices
with s_v = 1 pin the chain (all three surrounding spins equal), heralded s_v = 0 vertices forbid one
of the three wall patterns (the one that would erase both error edges), and unheralded vertices at
p = 1/2 carry couplings of magnitude ¼ ln(1/(1−q)) with signs fixed by the local error pattern. The
herald is a local, error-correlated *stiffening* of the effective ferromagnet — this is why p_c grows
with q — and at p = 1/2 (no prior information, all edge couplings zero) the *only* couplings are
those generated by the heralds, which is why a sharp corner q\* exists.

**(b) q = 1 is decodable for every p ≤ 1/2 (exact).** With q = 1 the observations determine every
n_v. A wrong-sector configuration x' consistent with the same counts differs from x by z = x ⊕ x'
with z-degree 0 or 2 at every detector and, at every z-vertex, exactly one of the two z-edges in x:
z is a vertex-disjoint union of *alternating* cycles and boundary paths, and ℓ(z) = 1 requires an
alternating left–right self-avoiding walk of length k ≥ 2L − 1. A given walk is alternating with
probability ≤ 2 (p(1−p))^{⌊k/2⌋} ≤ 2^{1−k}, and the number of honeycomb walks of length k from a
given vertex is μ^{k+o(k)} with μ = √(2+√2) = 1.8478 < 2 (Duminil-Copin–Smirnov). Hence
P_fail^{ML}(L; p, 1) ≤ (2L+1) Σ_{k ≥ 2L−1} 2 (μ/2)^{k+o(k)} → 0 exponentially, uniformly in
p ≤ 1/2: the entire line q = 1 is decodable, and the transition line must reach p = 1/2 at some
q\* ≤ 1. The numerics confirm the exponential decay with a shorter decay length (ξ ≈ 2.2 at p = 1/2
versus the bound's 1/(2 ln(2/μ)) = 6.3), Fig. 7.

**(c) Monotonicity in q (exact).** Discarding each herald independently with probability 1 − q/q'
turns the q' observation model into the q model, so the ML failure probability is non-increasing in q
at every (L, p): the decodable region is an up-set in q. No analogous argument exists in p (adding
errors changes h non-locally), so single-valuedness in p is a numerical finding (Sec. 5).

**(d) p = 1/2, q < 1.** In the loop language a competing left–right path z carries weight
(1−q)^{#DE(z) − #DF(z)} if all of its "double-full" vertices (both z-edges are errors) are unheralded,
and 0 otherwise (DE = double-empty). A union bound over honeycomb walks proves decodability at
p = 1/2 for q > 1 − (2/μ − 1)² = 0.9932. The bound is loose (it counts all walks and ignores the
entropy of the correct sector); the numerical corner is q\* = 0.858 ± 0.015.

## 4. Numerical method

**Sampling and estimators.** For each (L, p, q) we draw independent trials x ~ Bern(p)^{E_L},
b ~ Bern(q)^{D_L}, form (s, h), and run the ML decoder. Two unbiased estimators of the same LER are
recorded: the *hard* estimator (fraction of trials with argmax Z_ℓ ≠ ℓ(x) — the LER as defined in the
problem) and the *soft* estimator, the trial average of min(Z₀,Z₁)/(Z₀+Z₁) = P(ML decoder fails |
s, h). Since the posterior is exact both have the same mean, but the soft estimator's standard error
is 3.0× smaller (median 0.0022 at 4000 trials). Their consistency over all 1333 (L,p,q) points is
shown in Fig. 8 (z-score spread 0.89 — below 1 because the two estimators share the trials). All
finite-size analysis uses the soft estimator; hard LERs are tabulated alongside in
`data/ler_table.csv`.

**Runs.** (i) Coarse map: q ∈ {0, 0.2, 0.4, 0.6, 0.8, 0.9, 1}, 19 values of p ∈ [0.05, 0.5], L = 4–10,
1000 trials/point. (ii) Refined sections: 11 values of p in a window around the coarse crossing for
q = 0, 0.1, …, 0.8, and 9–13 values of q for p = 0.40, 0.45, 0.50, with L = 4, 6, …, 14 and 4000
trials/point. (iii) Large sizes L = 16, 20 (2000/1000 trials) and 24 (600 trials) near the boundary
of the q = 0, 0.3, 0.6, 0.8 and p = 0.45, 0.5 sections. Total: 3 761 200 decoded trials, 6.4 core-h.

**Finite-size analysis.** In the decodable phase the LER decreases with L, in the non-decodable phase
it increases towards 1/2, so the curves LER(x; L) for the control parameter x (p at fixed q, or q at
fixed p) cross. For every section we compute
(a) pairwise crossings x_×(L, L') of consecutive sizes (local quadratic fits in logit space; bootstrap
errors);
(b) plain scaling-collapse fits LER = A + B u + C u², u = (x − x_c) L^{1/ν}, in the window where the
largest fully-scanned size has 0.02 < LER < 0.45, for minimum sizes 6, 8, 10, with ν free or fixed;
(c) collapse fits with a corrections-to-scaling shift of the finite-size critical point,
u = (x − x_c − E L^{−2}) L^{1/ν};
(d) extrapolations x_×(L̄) = x_c + a L̄^{−w}, w = 1, 2, of the pairwise crossings.
The plain fits (b) are biased towards the small-L crossings, the shifted fits (c) towards the large-L
ones; at q = 0 the two (0.1676 and 0.1645) bracket the literature Nishimori value, and at p = 1/2 they
bracket the size at which the LER becomes L-independent (Sec. 5.2). We therefore quote the *midpoint
of (b, L ≥ 8) and (c, L ≥ 6)* as the central value, the larger of their bootstrap errors as the
statistical uncertainty, and half their difference (or the spread of all estimates (a)–(d), if
larger) as the finite-size systematic. Error bars in Fig. 1 are the quadrature sum.

## 5. Results

### 5.1 Fixed-q sections: the threshold p_c(q)

![Figure 3](figures/ler_vs_p_sections.png)

**Figure 3.** LER (soft estimator, ±1 s.e.) versus p for all sizes in the refined windows, one panel per
q (the q = 0.9 panel shows the coarse grid: the LER decreases with L for every p, including p = 1/2).

Every section with q ≤ 0.8 shows a single crossing region: below it the LER falls with L, above it
the LER rises towards 1/2, and the sign of dLER/dL changes exactly once across the whole range
0.05 ≤ p ≤ 0.5 (Fig. 3, coarse panels). The crossings drift to lower p with increasing size (Fig. 5):
by ≈0.01 between the (4,6) and (20,24) pairs at q = 0, and by ≈0.05–0.07 between the (4,6) and
(12,14)/(16,20) pairs at q = 0.7–0.8 — finite sizes *overestimate* the decodable region, increasingly
so at large q, where the relevant excitations (alternating or partially heralded chains) are longer.

| section | control | estimate | stat | syst (finite size) | ν (plain fit) | pairwise crossings (L,L′) |
|---|---|---|---|---|---|---|
| q = 0 | p | **0.1660** | ±0.0012 | ±0.0019 | 1.85±0.14 | (4,6) 0.1736; (6,8) 0.1728; (8,10) 0.1664; (10,12) 0.1720; (12,14) 0.1627; (16,20) 0.1703; (20,24) 0.1626 |
| q = 0.1 | p | **0.1755** | ±0.0019 | ±0.0021 | 1.84±0.05 | 0.1861; 0.1805; 0.1821; 0.1799; (12,14) 0.1721 |
| q = 0.2 | p | **0.1869** | ±0.0018 | ±0.0028 | 1.79±0.05 | 0.2048; 0.1928; 0.2018; 0.1959; (12,14) 0.1888 |
| q = 0.3 | p | **0.1992** | ±0.0014 | ±0.0030 | 1.69±0.04 | 0.2217; 0.2136; 0.2010; 0.2083; (12,14) 0.1984; (16,20) 0.2087 |
| q = 0.4 | p | **0.2169** | ±0.0022 | ±0.0040 | 1.78±0.05 | 0.2366; 0.2279; 0.2234; 0.2133; (12,14) 0.2269 |
| q = 0.5 | p | **0.2369** | ±0.0028 | ±0.0041 | 1.76±0.05 | 0.2734; 0.2495; 0.2468; 0.2423; (12,14) 0.2434 |
| q = 0.6 | p | **0.2652** | ±0.0022 | ±0.0049 | 1.56±0.08 | (6,8) 0.2845; 0.2719; 0.2691; (12,14) 0.2724; (14,16) 0.2564; (16,20) 0.2644 |
| q = 0.7 | p | **0.3058** | ±0.0041 | ±0.0076 | 1.67±0.04 | 0.3780; 0.3351; 0.3259; 0.3059; (12,14) 0.3127 |
| q = 0.8 | p | **0.3811** | ±0.0050 | ±0.0149 | 1.70±0.11 | (6,8) 0.4182; 0.4202; 0.4172; (12,14) 0.3785; (14,16) 0.4103; (16,20) 0.3635 |
| p = 0.40 | q | **0.8229** | ±0.0058 | ±0.0171 | 2.23±0.05 | (4,6) 0.7088; 0.7740; 0.7949; 0.7859; (12,14) 0.8079 |
| p = 0.45 | q | **0.8462** | ±0.0040 | ±0.0105 | 1.90±0.04 | (6,8) 0.7985; 0.7908; 0.8376; (12,14) 0.8263; (14,16) 0.8272; (16,20) 0.8475 |
| p = 0.50 | q | **0.8581** | ±0.0029 | ±0.0147 | 2.02±0.08 | (8,10) 0.8318; 0.8491; (12,14) 0.8445; (14,16) 0.8527; (16,20) 0.8644 |

**Table 2.** Transition estimates per section (`data/boundary_summary.md`, `data/fss_all.txt`).
Crossings are listed in order of increasing size (individual bootstrap errors 0.002–0.02). The fitted
ν (1.6–1.9 for the p-sections, 1.9–2.2 for the q-sections) is a finite-size effective exponent; the
Nishimori-point value ν ≈ 1.5 of the 2D RBIM lies within the systematic spread of the fits
(fixing ν = 1.5 in the plain fits shifts x_c by ≤ 0.002 in p and ≤ 0.009 in q).

At q = 0 the estimate 0.1660 ± 0.0023 agrees with the triangular-lattice Nishimori point. The
independent MWPM decoder on the same graph (pymatching, unit weights, 20 000 trials/point, L ≤ 20) has
a lower threshold, 0.158 ± 0.002 (Fig. 9), as expected for a minimum-weight decoder, and its
crossings drift the same way.

![Figure 5](figures/crossing_drift.png)

**Figure 5.** Pairwise crossings versus 1/L̄ for every section (labels (L, L′)); the horizontal band is
the final estimate ± combined uncertainty. Note the systematic drift, downward in p and upward in q.

![Figure 6](figures/collapse.png)

**Figure 6.** Plain scaling collapses (L ≥ 8) for q = 0, q = 0.6 and p = 1/2. The collapses are good
along the data (χ²/dof ≈ 1 at q = 0, 1.6 at q = 0.6), but at p = 1/2 (χ²/dof ≈ 6) corrections to
scaling are clearly resolved — the reason for the shift-corrected fits and the larger systematic error
of the corner.

### 5.2 Fixed-p sections and the corner q\*

![Figure 4](figures/ler_vs_q_sections.png)

**Figure 4.** LER versus q at p = 0.40, 0.45 and 0.50, all sizes (L = 24 only at p = 0.5).

Along the fixed-p sections the LER decreases monotonically with q at every size, as guaranteed by the
data-processing argument, and the curves of different L cross once. At p = 1/2 the crossing moves
from q = 0.77 (L = 4,6) through 0.81, 0.83, 0.85, 0.845, 0.853 to 0.864 ± 0.012 for (16,20), and the
LER table itself shows where the drift ends:

| q | L=10 | L=12 | L=14 | L=16 | L=20 | L=24 | trend |
|---|---|---|---|---|---|---|---|
| 0.84 | 0.2765 | 0.2788 | 0.2810 | 0.2826 | 0.2904 | – | increasing → non-decodable |
| 0.86 | 0.2416 | 0.2372 | 0.2344 | 0.2334 | 0.2359 | 0.2339 | flat within ±0.005 → critical |
| 0.88 | 0.2026 | 0.1943 | 0.1851 | 0.1811 | 0.1787 | 0.1561 | decreasing → decodable |

**Table 3.** Soft LER at p = 1/2 (s.e. 0.0025 for L ≤ 14, 0.0035–0.006 for L = 16–24).

The plain collapse fits give q_c(0.5) = 0.843–0.849 (L ≥ 8 / L ≥ 10), the shift-corrected fits
0.873–0.878, the L̄^{−2} extrapolation of the crossings 0.870 ± 0.013, the largest crossing pair
0.864 ± 0.012, and the direct trend q ≈ 0.86; our combined estimate is

    q* = 0.858 ± 0.003 (stat) ± 0.015 (finite size).

The two other fixed-p sections lie on the smooth continuation of the fixed-q curve:
q_c(0.40) = 0.823 ± 0.018 and q_c(0.45) = 0.846 ± 0.011 (Fig. 1). For q > q\* the LER at p = 1/2
decreases with L at all sizes studied (q = 0.88–0.98, Fig. 4), and at q = 1 it decays exponentially
for every p (Fig. 7; hard LER 0.142, 0.063, 0.018, 0.008 for L = 4, 6, 8, 10 at p = 1/2).

![Figure 7](figures/q1_decay.png)

**Figure 7.** q = 1: LER versus L for p = 0.2 … 0.5 (log scale) and the slope of the SAW bound. Fitted
decay lengths ξ = 1.5 (p = 0.3), 2.1 (0.4), 2.2 (0.5).

### 5.3 The two-dimensional phase diagram

Figure 1 assembles the evidence. The organisation of the domain is:

* **One decodable region** {p < p_c(q)} ∪ {q ≥ q\*} — it contains the axis p = 0, the whole line
  q = 1 and the segment {p = 1/2, q ≥ q\*} — and **one non-decodable region** {p > p_c(q), q < q\*}
  in which the LER approaches 1/2 (exactly 1/2 for all L at p = 1/2, q = 0, where every trial is an
  exact tie). Within the resolution of our grid there is no re-entrance: along each fixed-q section
  the sign of dLER/dL changes once, and the trend map (markers in Fig. 1, based on the two largest
  sizes at each point) is consistent with a single boundary everywhere it is resolved.
* **p_c(q) is single-valued, monotone and convex.** It rises slowly at first (0.166 → 0.176 between
  q = 0 and 0.1, slope ≈ 0.1) and steepens (0.265 → 0.306 → 0.381 for q = 0.6, 0.7, 0.8), then bends
  over to meet p = 1/2 at q\* ≈ 0.86 with a finite slope (dq_c/dp ≈ 0.35 between p = 0.4 and 0.5).
* **How heralding changes recovery.** Relative to the syndrome-only baseline p_c = 0.166, a herald
  that flags 20 % of the ≥2-error vertices buys 13 % more tolerable error rate (0.187), a 50 % herald
  43 % (0.237), an 80 % herald 130 % (0.381), and above q\* ≈ 0.86 the very notion of a threshold
  disappears: the logical bit is recoverable at p = 1/2, where the syndrome alone carries *no*
  information about the sector. The mechanism is the one identified in Sec. 3: a herald reveals the
  interior vertices of error chains (each with probability q), converting the entropic competition
  between the two homology classes into a pinned-chain problem; at q = 1 the only surviving
  ambiguity are alternating chains, whose number is exponentially smaller than their inverse
  probability (μ < 2). The missing heralds (1−q) act as hidden crossing points; the corner q\* is the
  point at which their density at p = 1/2 becomes too large for the pinned chains to remain rigid.
* **Decoder dependence.** The diagram is for optimal recovery. A simple herald-aware matching
  heuristic (fix the three edges at heralded s_v = 1 vertices, give negative weight to edges at
  heralded s_v = 0 vertices; `mwpm_baseline.hmwpm`, `data/hmwpm.jsonl`) captures little of the
  herald information: at q = 0.9, p = 0.30 its LER *increases* with L (0.24 → 0.25 for L = 6 → 12)
  where the ML decoder's decreases (0.088 → 0.041 for L = 6 → 10). Sub-optimal decoders thus have much
  smaller decodable regions, but, as the problem statement stresses, this says nothing about optimal
  recovery — which is why the phase diagram was built with an (numerically) exact ML decoder.

## 6. Uncertainties and limitations

**Statistical.** Soft-estimator standard errors are 0.002–0.003 per point at 4000 trials (0.003–0.006
for L ≥ 16); the bootstrap uncertainty of every threshold estimate is ≤ 0.005 in p and ≤ 0.006 in q.
Trials are independent; all seeds are recorded in the data files.

**Finite-size effects (dominant).** Sizes up to L = 24 (distance 47) at a few points and L ≤ 14
(distance 27) everywhere show clear crossings but also a monotone drift with L, towards smaller p at
fixed q and larger q at fixed p; the plain collapse fits have χ²/dof between 1 and 7 (12 at p = 0.4),
i.e. corrections to scaling are resolved by the data. Our central values are midpoints between fits
that are biased in opposite directions and the quoted systematic error (0.002–0.005 in p for q ≤ 0.6,
0.008–0.015 for q = 0.7–0.8, 0.01–0.017 in q for the corner) covers all individual estimates (a)–(d)
except the w = 1 crossing extrapolations, which at q = 0 undershoot the known Nishimori value and are
therefore regarded as over-corrections. The least certain feature is the corner: taking the extreme
estimates literally, q\* lies between 0.84 (plain fits) and 0.88 (shift-corrected fits), with the direct
large-size trend (Table 3) at 0.86. Since the drift is monotone, if our central curve is biased it is
towards the *outer* side (too large p_c, too small q\*).

**Decoder approximation.** Exact for L ≤ 10; for L ≥ 12 the χ = 16 MPS changed no decision and shifted
the per-trial failure probability by < 10⁻⁷ in all direct comparisons (Sec. 2). Negligible.

**Model scope.** The results are for the stipulated model: independent edge errors, exact syndromes,
heralds with false-negative probability 1 − q and no false positives, one measurement round.

**What is established versus inferred.** Exact: the sector structure (dim ker H = L² + 1), the
decodability of the whole line q = 1 and of p = 1/2 for q > 0.9932, and monotonicity in q. Numerical
inference from finite sizes: the location and shape of the boundary (single-valued, monotone,
convex), the value of q\*, and the absence of re-entrance in p. A proof of the infinite-size limit is
not attempted.

## 7. Computational resources

One workstation, 8 CPU cores of a shared host (single-threaded numpy/OpenBLAS per worker, 8 worker
processes), < 4 GiB RAM in total. CPU time: coarse map 0.31 core-h, refined sections 5.1 core-h,
large sizes 1.0 core-h, MWPM/heuristic baselines and validation ≈ 0.3 core-h (total 6.7 core-h);
wall time ≈ 50 min for the Monte Carlo (the shared host was heavily loaded, roughly halving
per-trial throughput relative to the isolated benchmarks quoted in Sec. 2). No GPU.

## 8. Reproduction

`bash run_all.sh` regenerates every number and figure (`README.md` lists the environment). Individual
steps: `validate.py` (correctness tests, seconds), `make_tasks.py` + `mc.py` (Monte Carlo, resumable
JSONL output), `mwpm_baseline.py` / `hmwpm_compare.py` (baselines), `fss.py` (finite-size analysis →
`data/boundary.csv`, `data/fss_all.txt`), `make_figures.py` and `final_analysis.py` (figures,
`data/boundary_summary.md`). Raw results: `data/results_{coarse,refined,large}.jsonl`; aggregated LER
table with both estimators: `data/ler_table.csv`.

![Figure 8](figures/hard_vs_soft.png)

**Figure 8.** Consistency of the hard (0/1) and soft (posterior) LER estimators over all 1333 data
points. **Figure 9** (`figures/mwpm_vs_ml.png`): ML versus MWPM at q = 0 and their crossing drifts.
