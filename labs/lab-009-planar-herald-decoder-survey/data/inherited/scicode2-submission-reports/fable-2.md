# Decoding with incomplete local witnesses: a two-parameter decoding phase diagram on a honeycomb lattice

*SciCode-2 computational research challenge — report. Code, data and figures are in `/app` (see `README.md`).*

## 1. Summary

We study the classical honeycomb "matching" code of the problem statement: every retained edge fails independently
with probability p, every detector vertex reports the parity of its incident errors, and, with probability q, it
additionally *heralds* the event that at least two errors meet at it. We built

* an **exact maximum-a-posteriori (MAP) decoder** for the full observation model. The MAP problem — a minimum-weight
  parity-constrained subgraph problem with hard "degree ≥ 2" constraints at heralded vertices and a herald-miss penalty
  at unheralded ones — is reduced *exactly* to a minimum-weight perfect matching on an auxiliary graph (vertex gadgets)
  and solved with a blossom algorithm in 0.3–4 ms per shot for L = 4–24. At q = 0 it coincides with standard
  minimum-weight perfect matching (MWPM), so the q = 0 section is the syndrome-only baseline of the *same* decoder family;
* an **exact maximum-likelihood (ML) decoder** (transfer-vector contraction, L ≤ 10–12) used to measure the approximation
  error of MAP;
* a Monte-Carlo campaign of 2.1·10⁷ decoded shots on sizes L = 4 … 48 (19.7 CPU-hours, 8 cores), with finite-size crossing
  and scaling analyses.

**Main results (Fig. 2, `report/figures/phase_diagram.png`).**

1. The decodable phase of the MAP decoder is bounded by a threshold line p_c(q) that rises **monotonically and convexly**
   from the syndrome-only value **p_c(0) = 0.1597 ± 0.0005 (stat) ± 0.0015 (syst)** — in agreement with the literature value
   ≈ 0.159 for matching on this lattice and below the optimal (Nishimori-point) value 0.164 — through p_c(0.5) = 0.227,
   p_c(0.7) = 0.288, p_c(0.8) = 0.351, p_c(0.85) = 0.427, p_c(0.875) ≈ 0.48, and reaches the edge p = 1/2 of the parameter
   domain at **q\* = 0.88 ± 0.01** (largest-size crossings 0.875–0.888, extrapolation 0.882 ± 0.006).
2. For **q > q\*** the *entire* range 0 ≤ p ≤ 1/2 is decodable: the logical error rate decreases with L even for
   uniformly random errors (p = 1/2). At q = 1 we prove this analytically for all p ≤ 1/2 (the failure probability of any
   decoder that returns a data-consistent configuration is bounded by the expected number of *alternating* self-avoiding
   crossing paths, which vanishes because the honeycomb connective constant μ = √(2+√2) < 2) and verify it numerically
   (P_fail ∝ e^{−0.42 L} at p = 1/2, q = 1).
3. Heralding therefore changes the physics qualitatively, not just quantitatively: near q = 0 it shifts the threshold
   slowly (dp_c/dq ≈ 0.1), but a large herald rate removes the transition altogether, because the ambiguity that survives
   parity measurement — pairs of errors cancelling at a vertex — is exactly what the herald reports. At p = 1/2 the parity
   information is worthless on its own, and the transition in q is a genuine disorder-driven transition of a new kind
   (Section 4b) with slow finite-size convergence (crossings drift by +0.03 between L ≈ 10 and L ≈ 44), so q\* is the least
   precisely known point of the boundary.
4. The MAP decoder is close to optimal: exact ML lowers the LER by 5–15 % at equal (L, p, q) and moves the finite-size
   crossings up by ≈ +0.01 in p at q = 0 (consistent with the known 0.159 → 0.164 MWPM/ML gap), by ≈ +0.02 at q = 0.5–0.8,
   and by ≤ +0.01 (not significant) in q at p = 1/2. The optimal phase boundary therefore lies slightly to the right of the
   MAP boundary drawn in Fig. 2 but has the same shape and the same exact q = 1 limit.

![Phase diagram](figures/phase_diagram.png)

*Fig. 2. Decoding phase diagram of the MAP decoder. Background: trend statistic [P_fail(L=24) − P_fail(L=12)]/σ on a
25 × 21 grid (N = 1000 / 4000 shots per cell; blue = LER falls with size, red = LER rises; white = no significant trend,
which happens both deep in the decodable phase where both LERs are ~0 and deep in the non-decodable phase where both
saturate near 1/2). Black points: thresholds p_c(q) from the fixed-q sections (Table 1) with statistical + finite-size
errors; diamond: q\* from the p = 1/2 line; the line is a monotone interpolation. The thick bar at p = 1/2 marks the
segment q\* ≤ q ≤ 1 where the whole domain is decodable (proved at q = 1). Dotted contours: LER of L = 24.*

## 2. Model, code and statistical-mechanics interpretation

**Lattice.** `hexcode/lattice.py` implements the construction literally (hexagon centres (3a, 2b + a mod 2), the six
corner offsets, merging of coincident vertices/edges, removal of the exposed sides 2,3 in column 0 and 0,5 in column L−1,
B_left/B_right = endpoints of the removed edges, D_L = the rest). Figure 1 (`figures/patch_L3.png`) reproduces the L = 3
patch of the statement (|V| = 30, |E| = 26, |D| = 16, 7 + 7 boundary vertices of which 6 are isolated, |Γ_R| = 4). In general
|V_L| = 2L² + 4L, |E_L| = 3L² − 1, |D_L| = 2L² − 2, |B_left| = |B_right| = 2L + 1, |Γ_R| = L + 1; all boundary vertices have degree
0 or 1 and the L + 1 horizontal edges touching B_right form Γ_R. The shortest left–right path has d = 2L − 1 edges, so a
syndrome-free nontrivial error needs ≥ 2L − 1 errors and a minimum-weight decoder fails only for errors of weight ≥ L.

**Code.** Vertices are parity checks on their incident edges; syndrome-free error patterns are cycles of the graph in
which all boundary vertices are merged into one. The cycle space is spanned by the L² hexagons, the 2L "half-hexagons"
along the two rough boundaries (all trivial) and one left–right crossing path (nontrivial); ℓ(z) is exactly the homology
class, so the code stores one bit.

**Stat-mech mapping.** Writing x = x₀ ⊕ ∂S for a set S of faces (Ising spins on hexagons and boundary faces),
P(x)P(h|x) becomes the Boltzmann weight of a ±J Ising model on the *triangular* lattice (faces = spins, honeycomb edges =
bonds, K = ½ log((1−p)/p)) times a **three-spin vertex factor** for every honeycomb vertex (the three faces around a vertex
form a dual triangle; the factor depends on whether the domain wall through that triangle moves n_v across the threshold
n_v ≥ 2). The two homology classes are the two relative orientations of the top and bottom boundary spins, and ML decoding
compares the two sector partition functions. At q = 0 this is the random-bond Ising model on the triangular lattice on the
Nishimori line, whose multicritical point is at p ≈ 0.164 (Nishimori–Ohzeki conjecture 0.1642, Ohzeki 2009: 0.1640,
transfer-matrix numerics of de Queiroz agree); minimum-weight matching on this lattice is quoted at ≈ 0.159 by Fujii and
Tokunaga. These numbers are external checks of our q = 0 baseline.

## 3. Decoders

### 3.1 The MAP decoder (production decoder, `hexcode/decoder.py`, callable `hexcode.decode`)

Given (G_L, p, q, s, h) the decoder returns the most probable error pattern,

  c = argmax_x P(x) P(h | x) 1[Hx = s],  P(h|x) = Π_v [ h_v : q·1(n_v ≥ 2) ; 1 − h_v : 1 − q·1(n_v ≥ 2) ].

Taking −log and using n_v ≡ s_v (mod 2), the objective is linear in x:

  cost(x) = Σ_e x_e [ log((1−p)/p) + (λ/2) m_e ],  λ = −log(1−q),

subject to n_v ≡ s_v at every detector and n_v ≥ 2 at heralded detectors, where m_e is the number of *unheralded* detector
endpoints of e (the miss penalty λ·1(n_v ≥ 2) equals λ(n_v − s_v)/2 on the allowed parity class, hence is linear in the edge
variables). This is a minimum-weight T-join with additional hard constraints "n_v = 2 exactly" (heralded, s_v = 0) and
"n_v = 3" (heralded, s_v = 1). A T-join alone is solvable by the usual syndrome-graph MWPM, but the hard constraints cannot be
imposed on a matching of syndrome vertices. We therefore use the classical *vertex-gadget* reduction of parity- and
degree-constrained subgraphs to **perfect matching**: every edge e = (u,v) becomes an auxiliary edge between nodes (u,e) and
(v,e) of cost w_e (matched ⇔ x_e = 1); a detector with allowed degrees {n ≡ s_v} gets one extra dummy node if d_v ≢ s_v (mod 2)
and a cost-0 clique on its d_v (+1) nodes; a detector with exactly known degree f gets d_v − f dummies joined to its edge
nodes (Tutte's f-factor gadget); each boundary vertex (degree ≤ 1, unmeasured) gets a private cost-0 partner, and all
partners form a cost-0 clique plus one parity node when |{v : s_v = 1}| is odd (the number of used boundary edges has the
parity of |s| by the handshake lemma, so this imposes nothing). A minimum-cost perfect matching of the auxiliary graph is
exactly a minimum-cost consistent x. It is solved with LEMON's `MaxWeightedPerfectMatching` (blossom algorithm, integer
costs = 10⁸ × log-likelihood). Exact cost ties (ubiquitous at p = 1/2, where log((1−p)/p) = 0) are broken by an
infinitesimal random perturbation drawn from the decoder's explicit `rng` argument. Limits: q = 0 → plain MWPM;
q = 1 → λ = ∞, every detector degree is known exactly and the decoder returns a minimum-weight configuration with those
degrees (an f-factor). The variant `decode(..., ell=0|1)` restricts the matching to one homology class (separate boundary
cliques for the left and right boundary edges with individual parity nodes) and is used to test whether an observation is
*ambiguous* (both classes non-empty).

**Validation.** (i) L = 2 (11 edges): 3 600 random observations at 12 (p,q) points including q = 1 and p = 1/2 — the
decoder's cost equals the brute-force minimum over all 2¹¹ patterns in every case and no invalid correction is ever
returned; the per-class variant was checked the same way (3 000 class-decodes, 0 errors). (ii) L = 3, 4: 640 observations
compared with an integer-linear-programming solution of the same MAP problem (HiGHS with presolve disabled — with
presolve enabled HiGHS returned provably suboptimal "optimal" solutions in this SciPy build): 0 mismatches. (iii) q = 0:
minimum weights agree with PyMatching. (iv) Hc = s is asserted on every decode in the Monte-Carlo code. Cost per shot:
0.3 ms (L = 4), 1.5 ms (L = 16), 3–4 ms (L = 24), 13 ms (L = 32), 40 ms (L = 48).

### 3.2 Exact ML decoder (`hexcode/mldecoder.py`)

Z_ℓ = Σ_{x: Hx = s, ℓ(x) = ℓ} P(x)P(h|x) is computed exactly by a column-by-column transfer-vector contraction of the planar
factor graph (dense vector over the ≤ L + 3 edges crossing the cut plus one bit carrying the parity of the Γ_R edges already
summed out). It agrees with brute force to 10⁻¹⁵ at L = 2 and costs 12 ms (L = 8), 70 ms (L = 10), 0.4 s (L = 12) per shot. It
yields not only the ML decision but the *conditional* failure probability min(Z₀,Z₁)/(Z₀+Z₁), whose sample mean is a
low-variance estimator of the ML logical error rate. The ML decoder is used only for the decoder-approximation study
(Section 6.5).

## 4. Analytic results used to anchor the diagram

**(a) q = 1 is decodable for every p ≤ 1/2, for the MAP decoder and for any decoder that returns a consistent
configuration.** At q = 1 the pair (s_v, h_v) reveals n_v exactly at every detector (n_v ∈ {0,1} ↔ h_v = 0, n_v ∈ {2,3} ↔ h_v = 1).
Two configurations x, x' consistent with the same data differ by C = x ⊕ x' with |C ∩ δv| ∈ {0,2} at every detector and,
where |C ∩ δv| = 2, exactly one of the two C-edges in x: C is a vertex-disjoint union of simple cycles and
boundary-to-boundary simple paths along which the edges *alternate* between x and non-x. A wrong homology class therefore
requires an alternating self-avoiding left–right crossing path. For a fixed path of n edges the probability of alternation
is 2(p(1−p))^{n/2} ≤ 2^{1−n}, and the number of n-step self-avoiding walks on the honeycomb lattice is c_n = μ^{n+o(n)} with the
(rigorous, Duminil-Copin–Smirnov) connective constant μ = √(2+√2) = 1.8478 < 2. Hence

  P(ambiguous) ≤ E[# alternating crossing SAWs] ≤ (L+1) Σ_{n ≥ 2L−1} c_n 2^{1−n} ≤ C L (μ/2)^{2L} e^{o(L)} → 0.

Any decoder that returns a data-consistent configuration is correct whenever no alternating crossing path exists, so
P_fail(L; p, 1) → 0 exponentially for all p ∈ [0, 1/2], including the uniformly random point p = 1/2. The bound is loose in
the rate ((μ/2)² = 0.85 per unit L) but the mechanism is confirmed numerically: the measured ambiguity probability decays
as e^{−0.42 L} at p = 1/2 (Section 6.3).

**(b) Why there is a genuine transition at p = 1/2 for q < 1.** At p = 1/2 all error configurations are a priori equally
likely and the posterior is P(x | s,h) ∝ 1[Hx = s] Π_{v heralded} 1[n_v ≥ 2] · (1−q)^{M(x)}, where M(x) is the number of unheralded
detectors with n_v(x) ≥ 2 ("missed heralds"). A crossing path C changes M by −1, 0 or +1 at each vertex it passes: 0 for an
alternating step, +1 for a non-alternating step at an unheralded vertex with n_v(x) ≤ 1, and −1 for a non-alternating step
through a missed-herald vertex (density (1−q)/2 at p = 1/2); heralded vertices admit alternating steps only. The MAP
decoder compares the minimum of M over the two classes, i.e. the zero-temperature energy of a domain wall in a random
medium with local energies −1, 0, +1; the ML decoder compares free energies at "temperature" 1/log(1/(1−q)).
Decodability requires the crossing-wall (free) energy to grow with L. As q → 1 the negative sites disappear and the
positive ones become forbidden, giving the alternating-path problem of (a); as q decreases the entropy of cheap walls wins.
The location q\* of this disorder-driven transition is not known analytically; the annealed count of walls
Σ_n c_n [(1 + (1−q))/2]^n diverges for q < 2 − 2/μ = 0.918, a rough upper bound for q\* (annealed averages over-count rare
favourable disorder). The measured q\* = 0.88 is indeed below it.

**(c) Monotonicity of the optimal boundary.** A decoder for herald rate q can simulate any q' < q by discarding heralds
independently with probability 1 − q'/q, so the optimal (ML) decodable region can only grow with q and p_c^{ML}(q) is
non-decreasing. The MAP decoder is not guaranteed to be monotone, but is observed to be.

**(d) Information-theoretic consistency at p = 1/2.** A syndrome carries |D| ≈ 2L² bits about 3L² random edge bits, so
syndrome-only decoding at p = 1/2 is impossible (LER → 1/2). Perfect heralds add H(n_v) − H(s_v) = H(1/8,3/8,3/8,1/8) − 1 ≈ 0.81 bit
per bulk detector, i.e. ≈ 1.6 L² bits, so the total information ≈ 3.6 L² bits exceeds the 3L² bits of entropy of x: recovery
of the class at p = 1/2 is information-theoretically possible only because of the heralds, consistent with (a).

## 5. Numerical procedure and error budget

*Sampling.* Independent shots (x, b) per (L, p, q); the decoder receives the true (p, q). A shot fails if the correction is
missing or x ⊕ c has a nontrivial class (Hc = s is guaranteed by construction and asserted). Sizes L ∈ {4, 6, 8, 12, 16, 24}
(distances d = 2L − 1 = 7 … 47) plus L = 32, 40, 48 on the p = 1/2 line. Per point: N = 2·10⁴ shots for L ≤ 16 and 10⁴ for L = 24
on the fixed-q sections (9 or 8 values of p in a window bracketing the coarse crossing; 13 values of q), 4·10³ (L = 6, 12) and
10³ (L = 24) on the 25 × 21 (p,q) grid, and 4·10³ – 2·10³ for L ≥ 32. Seeds are recorded per chunk.

*Crossings.* For each section and each consecutive size pair (L₁, L₂) we fit logit P_fail against the control parameter
with a weighted quadratic over the window and solve for the intersection; errors are bootstrap (binomial resampling).

*Scaling fits.* Following Wang–Harrington–Preskill we fit P_fail = Σ_{k ≤ 3} a_k u^k, u = (p − p_c) L^{1/ν}, within ±18 % of the
largest-size crossing, for three size sets (all L; L ≥ 8; L ≥ 12). The central estimate is the mean of the L ≥ 8 and L ≥ 12 fits;
the error combines the bootstrap error, half the difference of the two fits and half the drift of the two largest-size
crossings (finite-size systematic). χ²/dof ≈ 1 for q ≤ 0.8. At the p = 1/2 endpoint the scaling ansatz fails (χ²/dof ≈ 100,
running ν) and we rely on the crossings and their extrapolation in 1/L and 1/L².

*Decoder approximation.* MAP ≠ ML; the exact ML decoder on the same samples (L ≤ 10) quantifies the shift of the optimal
boundary relative to the MAP boundary (Section 6.5). The q = 1 result is decoder-independent.

*Distinguishing the three uncertainties.* Statistical errors are ≤ 0.001 in p_c for q ≤ 0.8 (they are quoted separately in
Table 1); finite-size systematics grow from 0.001 (q = 0) to 0.005 (q = 0.8), 0.014 (q = 0.85) and ≈ 0.01 in q at the p = 1/2
endpoint; the decoder-approximation shift of the *optimal* boundary is +0.01 … +0.02 in p (ML lies to the right of MAP) and
≲ 0.01 in q at p = 1/2.

## 6. Results

### 6.1 Fixed-q sections and the threshold line p_c(q)  (Fig. 3 `figures/sections.png`, Fig. 4 `figures/crossing_drift.png`)

Table 1 lists, for every section, the finite-size crossings of consecutive sizes and the scaling-fit thresholds. For
q ≤ 0.5 the crossings are size-independent within errors and the scaling fits have χ²/dof ≈ 1 and ν = 1.5–1.7 (the q = 0 value
ν = 1.53 ± 0.05 is compatible with ν ≈ 1.5 of the two-dimensional random-bond Ising model). For q ≥ 0.6 the crossings drift
*downwards* with size (q = 0.8: 0.397 → 0.372 → 0.356 → 0.350 for mean sizes 7, 10, 14, 20), which is absorbed in the
systematic error. The section at q = 0.85 is only partially resolved (crossings 0.423, 0.416; fits 0.414–0.440); at
q = 0.875 the L = 24 curve crosses the L = 16 curve at p = 0.471 ± 0.008 and the fit gives 0.484 ± 0.010; at q = 0.9 the curves
do not cross anywhere in 0.36 ≤ p ≤ 0.5 — the LER decreases with L at every p.

| q | ×(8,12) | ×(12,16) | ×(16,24) | p_c (L ≥ 8 fit) | p_c (L ≥ 12 fit) | ν | χ²/dof | **p_c final** |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.1594 | 0.1598 | 0.1624 | 0.1597 ± 0.0005 | 0.1599 | 1.53 | 0.85 | **0.1598 ± 0.0014** |
| 0.10 | 0.1719 | 0.1685 | 0.1675 | 0.1688 ± 0.0006 | 0.1673 | 1.59 | 1.39 | **0.1680 ± 0.0010** |
| 0.20 | 0.1808 | 0.1831 | 0.1776 | 0.1792 ± 0.0005 | 0.1787 | 1.53 | 0.99 | **0.1790 ± 0.0029** |
| 0.30 | 0.1951 | 0.1934 | 0.1891 | 0.1920 ± 0.0006 | 0.1901 | 1.57 | 1.37 | **0.1911 ± 0.0024** |
| 0.40 | 0.2110 | 0.2072 | 0.2092 | 0.2081 ± 0.0008 | 0.2071 | 1.66 | 0.58 | **0.2076 ± 0.0014** |
| 0.50 | 0.2323 | 0.2290 | 0.2258 | 0.2278 ± 0.0008 | 0.2262 | 1.64 | 1.31 | **0.2270 ± 0.0019** |
| 0.60 | 0.2563 | 0.2572 | 0.2491 | 0.2521 ± 0.0008 | 0.2500 | 1.50 | 2.14 | **0.2511 ± 0.0042** |
| 0.70 | 0.2931 | 0.2944 | 0.2878 | 0.2893 ± 0.0011 | 0.2864 | 1.68 | 1.36 | **0.2878 ± 0.0037** |
| 0.75 | 0.3323 | 0.3142 | 0.3134 | 0.3161 ± 0.0012 | 0.3093 | 1.63 | 3.19 | **0.3127 ± 0.0036** |
| 0.80 | 0.3719 | 0.3561 | 0.3499 | 0.3547 ± 0.0017 | 0.3478 | 1.62 | 1.55 | **0.3513 ± 0.0050** |
| 0.85 | — | 0.4230 | 0.4162 | 0.4395 ± 0.0062 | 0.4144 | (2.7) | 2.24 | **0.427 ± 0.014** |
| 0.875 | — | — | 0.4706 | 0.4906 ± 0.0071 | 0.4778 | 1.49 | 3.53 | **0.484 ± 0.010** |
| 0.90 | — | — | none | — | — | — | — | **> 0.5 (no transition)** |
| 1.00 | — | — | none | — | — | — | — | **> 0.5 (proved)** |

*Table 1. Crossings p_×(L₁,L₂) (bootstrap errors 0.001–0.003 for q ≤ 0.8, 0.005–0.01 above), scaling-fit thresholds
(statistical errors) and the final estimate with the combined error. All size pairs: `data/thresholds_sections.csv`.*

The threshold line is monotone and convex in q: the gain is slow at first (≈ +0.01 per 0.1 of q up to q = 0.4), then
accelerates (+0.024 from q = 0.5 to 0.6, +0.037 to 0.7, +0.064 to 0.8, +0.076 to 0.85) and the line meets p = 1/2 at
q\* ≈ 0.88 with a finite slope (dp_c/dq ≈ 2–3), i.e. not tangentially. Along the whole line the transition is a single sharp
crossing of the P_fail(L) curves for each q; no evidence of a multi-valued or re-entrant boundary was found in the 25 × 21 grid.

![sections](figures/sections.png)

*Fig. 3. Fixed-q sections: P_fail vs p for L = 4 … 24 (N = 2·10⁴ shots per point, 10⁴ for L = 24). Dashed line: final p_c.*

### 6.2 The p = 1/2 line and the endpoint q\*  (Fig. 5 `figures/line_p05.png`)

At p = 1/2 the syndrome alone is useless (Section 4d), so this line isolates the herald information. Table 2 shows the LER
against size for the herald rates near the transition.

| q | L=4 | 6 | 8 | 12 | 16 | 24 | 32 | 40 | 48 | trend |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.84 | 0.336 | 0.316 | 0.312 | 0.319 | 0.325 | 0.355 | 0.379 | 0.391 | — | rises |
| 0.86 | 0.318 | 0.288 | 0.275 | 0.270 | 0.281 | 0.289 | 0.310 | 0.328 | 0.337 | rises for L ≥ 12 |
| 0.88 | 0.303 | 0.261 | 0.245 | 0.227 | 0.226 | 0.223 | 0.220 | 0.218 | 0.230 | flat for L ≥ 12 |
| 0.90 | 0.282 | 0.238 | 0.209 | 0.185 | 0.167 | 0.146 | 0.134 | 0.113 | 0.098 | falls |
| 0.92 | 0.265 | 0.202 | 0.170 | 0.135 | 0.109 | 0.080 | 0.059 | 0.044 | 0.035 | falls |
| 0.96 | 0.220 | 0.140 | 0.095 | 0.054 | 0.031 | 0.012 | 0.005 | 0.001 | < 0.0005 | falls fast |
| 1.00 | 0.170 | 0.074 | 0.031 | 0.0053 | 0.0007 | < 1e-4 | < 2.5e-4 | < 3e-4 | — | ∝ e^{−0.4L} |

*Table 2. LER at p = 1/2 (N = 2·10⁴ for L ≤ 16, 10⁴ at L = 24, 4·10³ at 32, 3·10³ at 40, 2·10³ at 48; statistical errors
0.003–0.01 for the top rows). Full table: `data/line_p05_table.csv`.*

The crossings of consecutive sizes in q drift upwards and slow down: 0.859 ± 0.003 (8,12), 0.865 ± 0.003 (12,16),
0.873 ± 0.002 (16,24), 0.875 ± 0.004 (24,32), 0.877 ± 0.010 (32,40), 0.888 ± 0.014 (40,48). Extrapolating the crossings in
1/L̄ gives 0.886 ± 0.004, in 1/L̄² 0.877 ± 0.002; the raw data at q = 0.88 are flat within errors from L = 12 to 48 while
q = 0.86 rises and q = 0.90 falls by a factor 1.9 from L = 12 to 48. We therefore quote **q\* = 0.88 ± 0.01**. The approach to
this transition is unusually slow: at q = 0.90 the LER decays roughly as L^{−0.35} for 12 ≤ L ≤ 24 and L^{−0.6} for 24 ≤ L ≤ 48,
i.e. the asymptotic exponential decay is only beginning to set in at L ≈ 40 (compare the clean exponential at q = 1). A
one-parameter scaling collapse fails on this line (χ²/dof ≈ 100 with apparent ν ≈ 2.6–3.9 running with size), which is
what one expects for a percolation-like transition of a random path problem with strong corrections to scaling, but it also
means that we cannot exclude q\* being as high as 0.90 on the basis of L ≤ 48 alone.

![p=1/2 line](figures/line_p05.png)

*Fig. 5. p = 1/2: LER vs q for nine sizes (left) and vs L for fixed q (right). The fan of curves pivots at q ≈ 0.88.*

### 6.3 The q = 1 line: decodable everywhere  (Fig. 6 `figures/q1_ambiguity.png`)

With perfect heralds we decoded each shot separately in both homology classes. Table 3 gives the probability that *both*
classes contain a configuration consistent with (s, h) — the ambiguity probability, an upper bound on the LER of *every*
decoder including ML — together with the MAP LER.

| p | L=4 | L=6 | L=8 | L=12 | L=16 | L=24 |
|---|---|---|---|---|---|---|
| 0.2 ambiguous | 0.118 | 0.021 | 0.0034 | 1.5e-4 | < 5e-5 | < 1e-4 |
| 0.3 ambiguous | 0.247 | 0.080 | 0.024 | 0.0023 | 1e-4 | < 1e-4 |
| 0.4 ambiguous | 0.347 | 0.147 | 0.058 | 0.0096 | 0.0015 | 1e-4 |
| 0.5 ambiguous | 0.375 | 0.172 | 0.080 | 0.0149 | 0.0022 | 1e-4 |
| 0.5 MAP LER | 0.183 | 0.088 | 0.039 | 0.0074 | 0.0009 | < 1e-4 |

*Table 3. q = 1, N = 2·10⁴ shots per point (10⁴ at L = 24); statistical errors ≈ √(P/N).*

The ambiguity probability decays exponentially at every p, with rate 0.83 (p = 0.2), 0.64 (0.3), 0.41 (0.4) and 0.42 (0.5) per
unit L — much faster than the rigorous first-moment rate 2 ln(2/μ) = 0.16 of Section 4a, whose mechanism (an alternating
self-avoiding crossing path must exist) is nevertheless exactly what is observed: at p = 1/2 *all* ambiguous shots are exact
cost ties (all consistent configurations have zero cost), so the MAP decoder fails on exactly half of them (LER/ambiguity
= 0.49), while at smaller p the boundary-edge weights break some ties (LER/ambiguity = 0.24 at p = 0.2). The exact ML decoder
(L ≤ 10) lowers the LER further to ≈ 0.7 × the MAP value (0.0094 vs 0.0147 at L = 10, p = 1/2) but cannot beat the ambiguity
bound. The whole segment q = 1, 0 ≤ p ≤ 1/2 is therefore decodable, and already the smallest sizes show it (the LER falls by
≥ 2× per ΔL = 2 at every p).

### 6.4 The two-dimensional map  (Fig. 2; `figures/coarse_heatmap.png`)

The 25 × 21 grid (L = 6, 12, 24) confirms that the sections capture the whole structure: the sign of the size trend changes
exactly along the interpolated threshold line, the "no-trend" white band along the line is narrow (one grid cell, 0.02 in
p) for q ≤ 0.6 and widens towards the endpoint (where the transition becomes slow), and the entire strip q ≥ 0.9 is blue
(LER falls with L at every p, including p = 1/2). Inside the decodable phase heralding suppresses the LER strongly even far
from threshold: at p = 0.14, L = 24, the LER is 0.054 (q = 0), 0.028 (0.1), 0.013 (0.2), 0.004 (0.3), < 0.001 (q ≥ 0.4); at
p = 0.16 it is 0.204 (q = 0), 0.130 (0.1), 0.070 (0.2), 0.013 (0.4). Roughly, each 0.1 of herald rate halves the LER at fixed
(p, L) in this regime.

### 6.5 Decoder-approximation error: MAP versus exact ML  (Fig. 7 `figures/map_vs_ml.png`)

On identical samples (N = 6 000 per point for L = 4, 6, 8; 3 000 for L = 10) the exact ML decoder has a lower LER than MAP
everywhere: by 3–8 % (relative) at q = 0, 8–15 % at q = 0.5 and 0.8, 10–15 % on the p = 1/2 line and ≈ 30 % at q = 1. The
finite-size crossings computed from the same paired data (`data/ml_vs_map_crossings.csv`) quantify the shift of the
*optimal* boundary:

| section | pair | MAP crossing | ML crossing | shift |
|---|---|---|---|---|
| q = 0 (in p) | (4,6) | 0.163 ± 0.004 | 0.177 ± 0.006 | +0.013 |
| q = 0 (in p) | (6,8) | 0.164 ± 0.006 | 0.173 ± 0.005 | +0.009 |
| q = 0.5 (in p) | (6,8) | 0.230 ± 0.006 | 0.249 ± 0.008 | +0.020 |
| q = 0.8 (in p) | (6,8) | 0.41 ± 0.03 | 0.45 ± 0.03 | +0.05 ± 0.04 |
| p = 1/2 (in q) | (6,8) | 0.805 ± 0.012 | 0.812 ± 0.012 | +0.007 ± 0.017 |

At q = 0 the ML shift (+0.01 at these sizes) is consistent with the known 0.159 (matching) → 0.164 (Nishimori point) gap of
this lattice; at intermediate q the ML gain is larger, ≈ +0.02 in p_c, i.e. the optimal boundary lies to the right of the MAP
boundary by roughly 5–10 % of p_c. At the p = 1/2 endpoint the two decoders' crossings coincide within errors: the endpoint
is essentially decoder-independent (the ML gain there is a uniform factor in the LER, not a shift of the transition), so
the statement "for q ≳ 0.9 every p ≤ 1/2 is decodable" holds for the optimal decoder as well. These ML data are limited to
L ≤ 10, so the shifts carry finite-size uncertainty of the same order as the shifts themselves for q ≥ 0.8.

## 7. Interpretation and limitations

*How heralding changes recovery.* A parity check sees an odd number of errors; the herald sees the complementary event
(≥ 2 errors, i.e. an even pair or a triple). The failure mechanism of matching decoders at q = 0 is a chain of errors whose
interior vertices all have n_v = 2 and are therefore invisible; a herald exposes every interior vertex with probability q.
At small q this only re-weights the decoder's costs (hence the slow initial rise of p_c, ≈ 0.1 in p per unit q); at large q
the invisible chains must be *alternating* (errors only every other edge), which is a much more entropy-poor object: the
number of alternating crossing paths grows like (μ/2)^n → 0 whereas the number of arbitrary chains grows like μ^n. That
is why a moderately imperfect herald (q ≳ 0.88) suffices to make the code decodable up to the maximal error rate p = 1/2,
where no syndrome-only strategy can work at all.

*Phase structure.* The MAP decodable region is {(p, q) : p < p_c(q)} with a single-valued, monotone, convex boundary that
terminates on the domain edge p = 1/2 at q\* = 0.88 ± 0.01; above q\* the whole edge is decodable and there is no transition.
We found no reentrance and no second transition (e.g. no non-decodable island at large p and large q). The transition
along the boundary is a sharp crossing with ν ≈ 1.5–1.7 for q ≤ 0.8; near the endpoint its finite-size behaviour changes
character (slow drifts, no one-parameter collapse), consistent with the different (random-path) mechanism at p = 1/2.

*Limitations.* (i) The diagram is the MAP decoder's; the optimal boundary is shifted right by ≈ 0.01–0.02 in p (Section 6.5)
and shares q\* within ± 0.01. (ii) p_c values for q ≥ 0.75 are upper-biased by residual crossing drift; we included the drift
in the error but cannot exclude a further downward shift of ≈ 0.005 at q = 0.8 and ≈ 0.01 at q = 0.85. (iii) q\* is inferred
from L ≤ 48 with slow convergence; values between 0.875 and 0.90 are compatible with the data if the drift continues.
(iv) Statistical errors are subdominant everywhere except at q = 1 and at the deepest decodable points, where the LER is
below 10⁻⁴ and only upper bounds are quoted. (v) The problem's q = 0 baseline is reproduced to within 0.001 of the
published matching threshold, which we take as evidence that the lattice, boundary and logical conventions were
implemented as specified.

## 8. Resources and reproducibility

All simulations ran on one machine with 8 CPU cores (Python 3.11, numpy/scipy/pandas, C++ matching solver via LEMON) and
< 2 GiB of RAM; no GPU. Total: 2.09·10⁷ decoded shots, 19.7 CPU-hours (≈ 2.3 h wall clock including analysis and
concurrent ML runs; `data/resources_summary.csv`). Every CSV row records L, p, q, N, failures, seed and CPU time of one
chunk, so any point can be regenerated with `scripts/run_scan.py`. `README.md` lists the exact commands that produced every
data file and figure; `scripts/validate_*.py` re-run the decoder validations (≈ 3 min).

**Files.** Decoder: `hexcode/decoder.py` (+ `hexcode/mwpm_lemon.cpp`, `hexcode/mwpm.py`), callable `hexcode.decode(G, p, q, s, h, rng)`;
lattice: `hexcode/lattice.py`; ML decoder: `hexcode/mldecoder.py`; data: `data/*.csv`; figures: `report/figures/`.

**References.** H. Nishimori and M. Ohzeki, J. Phys. Soc. Jpn. 75, 034004 (2006); M. Ohzeki, Phys. Rev. E 79, 021129 (2009);
S. L. A. de Queiroz, Phys. Rev. B 73, 064410 (2006) and 79, 174408 (2009); K. Fujii and Y. Tokunaga, Phys. Rev. A 86, 020303
(2012); H. Duminil-Copin and S. Smirnov, Ann. Math. 175, 1653 (2012) (connective constant of the honeycomb lattice);
C. Wang, J. Harrington and J. Preskill, Ann. Phys. 303, 31 (2003) (finite-size scaling of thresholds); W. T. Tutte, Canad. J.
Math. 6, 347 (1954) and G. Cornuéjols, J. Combin. Theory B 45, 185 (1988) (degree-constrained subgraphs via perfect matching).
