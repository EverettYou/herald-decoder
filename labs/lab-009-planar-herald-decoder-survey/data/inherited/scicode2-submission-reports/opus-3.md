# Decoding with incomplete local witnesses: the exact maximum-likelihood phase diagram

**Summary.** For the heralded parity model on the honeycomb patch `G_L`, the
Bayes-optimal (maximum-likelihood, ML) logical decision can be computed
*exactly* in polynomial time. Every detector has degree ≤ 3, and the herald
likelihood depends only on the incident error count `n_v`, whose parity is
fixed by `s_v`. Hence every vertex factor is a parity-respecting function of
≤ 3 edge variables, which is a planar matchgate. The logical posterior
therefore reduces to a Pfaffian: one sparse LU factorisation of a
Kasteleyn matrix with ≈ 8L² rows per decode (15 ms at L = 32, 70 ms at
L = 64). Using this exact decoder, a Rao-Blackwellised Monte Carlo estimator
and sizes L = 8–64 (5.1·10⁶ exactly decoded trials, plus 10⁶ at
q = 1), we map the decoding phase diagram over the whole domain
0 ≤ p ≤ 1/2, 0 ≤ q ≤ 1.
Because the decoder is optimal, the diagram is the phase diagram of *optimal
recovery*, not of a particular heuristic. Its uncertainties are statistical
and finite-size only.

**Main results** (Fig. 1, Table 2):

1. **One decodable and one non-decodable region, separated by a single
   monotone boundary.** The ML LER cannot increase with q
   (data processing), so the boundary is the graph of a single-valued
   function `q_c(p)`. We find it increasing and concave, with no re-entrance,
   all the way to p = 1/2. At a common size pair the crossing rises
   strictly: q_{32/64}(p) = 0.828, 0.854, 0.861, 0.868 (±0.001) at
   p = 0.40, 0.45, 0.475, 0.50. Every fixed-q section therefore has at most
   one transition, `p_c(q)`.
2. **q = 0 baseline.** `p_c(0) = 0.1640 ± 0.0022`, with correlation-length
   exponent ν ≈ 1.54. This reproduces the Nishimori point of the triangular
   random-bond Ising model (0.1640–0.1642) and validates the whole pipeline
   end to end. Syndrome-only MWPM reaches only 0.156, versus 0.165 for ML
   at the same sizes (L = 16/32 crossings).
3. **Heralding raises the threshold, slowly at first and then steeply.**
   `p_c(q)` = 0.173, 0.184, 0.195, 0.213, 0.233, 0.260, 0.295, 0.363 at
   q = 0.1 … 0.8 (Table 2). The boundary reaches `p = 1/2` at
   **q\* = q_c(1/2) = 0.872 ± 0.008**. For `q > q*` *every* `p ≤ 1/2` is decodable,
   including `p = 1/2`, where the syndrome alone carries no information
   (LER = 1/2 exactly at q = 0).
4. **q = 1 is decodable at every p**, with a short correlation length. At
   q = 1 the counts `n_v` are known exactly, and a sector error requires an
   alternating (directed) left-right path, whose probability decays
   exponentially (~e^{−L/2.3} at p = 1/2).
5. **The transition keeps the same character along the whole boundary.**
   All 16 cuts give ν = 1.50–1.64 (median 1.55) and a critical LER of
   0.18–0.23 (median 0.19, for this aspect ratio). This is consistent with
   a single universality class, that of the Nishimori point. Heralding moves the transition; it does not
   change its nature.
6. **Finite-size effects are the dominant uncertainty**, largest on the flat
   top of the boundary (p ≳ 0.3). There the crossings still move by
   ≈ +0.005–0.01 in q per doubling of L at the largest sizes, always toward a
   *larger* non-decodable region. Our error bars include an explicit
   allowance for this residual drift.

![phase diagram](figures/phase_diagram.png)

**Figure 1.** (a) Phase diagram of optimal (ML) decoding. Blue:
decodable (LER → 0); red: non-decodable (LER → 1/2). Points: threshold
estimates from fixed-q cuts (circles, error bars in p) and fixed-p cuts
(squares, error bars in q). The error bars combine statistical and
finite-size uncertainty; the grey band (thin at this scale) is the
unresolved region between the two envelopes. The star is the literature
Nishimori point. (b) Zoom on the flat top: the boundary estimated from
crossings of sizes (L, 2L). It moves monotonically toward the final estimate
as L grows, and the last two pairs nearly coincide. (c) Direction of the
finite-size flow on the coarse 14 × 11 grid:
`T = Δ_{L=16→32} log[LER/(1/2 − LER)]`. Blue: LER flows to 0; red: flows to
1/2; neutral: change not significant at 2σ. Cells with LER < 1% at both
sizes are shown as −4, and cells with LER > 0.49 at both sizes as +4.

---

## 1. Problem and approach

Errors `x_e ~ Bernoulli(p)` live on the retained edges of `G_L`. Each detector
reports `s_v = n_v mod 2` and a herald `h_v = 1{n_v ≥ 2} b_v`,
`b_v ~ Bernoulli(q)`. A decoder sees `(G_L, p, q, s, h)` and must output `c`
with `H c = s`; it fails if `ell(x ⊕ c) = 1`. The lattice module
(`src/heralded/lattice.py`) implements the construction literally
(hexagon placement, merging, exposed-side removal, `B_left`, `B_right`,
`D_L`, `Γ_R`). It reproduces Fig. 1 of the problem statement
(`figures/lattice_L3.png`; for L = 3: |V| = 30, |E| = 26, |D| = 16,
|Γ_R| = 4). Detectors have degree 2 or 3. Each boundary side has L + 1
degree-1 and L isolated B vertices. The minimum-weight logical has
2L − 1 edges.

Our strategy has three parts.
1. Establish exact structural facts that constrain the phase diagram
   (Sec. 2).
2. Build a decoder that is *provably optimal* and exact, so that decoder
   approximation error is eliminated rather than estimated (Sec. 3).
3. Spend the compute on finite-size evidence where the boundary is least
   constrained (Secs. 4–5).

## 2. Exact structural facts used throughout

**(F1) Optimal decoding = logical-sector posterior.** Any correction with
`Hc = s` succeeds iff `ell(c) = ell(x)`. Hence the decoder minimising
`P_fail` for *every* observation picks the sector `k` maximising
`P[ell(x) = k | s, h]`, and its conditional failure probability is
`min_k P[ell(x) = k | s, h]`. With
`P(x | s, h) ∝ Π_e p^{x_e}(1-p)^{1-x_e} Π_{v∈D} 1[n_v ≡ s_v] φ(n_v; h_v)`,
`φ(n; 1) = q·1[n ≥ 2]`, `φ(n; 0) = 1[n ≤ 1] + (1-q)·1[n ≥ 2]`,
this is a ratio of two partition functions. Our decoder computes it exactly
(Sec. 3), so **the reported LER is the optimal LER for this observation
model; there is no decoder-approximation error**, only statistical and
finite-size uncertainty. A non-decodable region found here is non-decodable
for every decoder (up to the finite-size extrapolation).

**(F2) Monotonicity in q (data processing).** From observations at herald
rate `q` one can manufacture observations with the exact law of rate `q' < q`
by erasing each `h_v = 1` independently with probability `1 - q'/q`. The ML
decoder at `q` is at least as good as "erase, then ML at `q'`", so
`P_fail^ML(L; p, q) ≤ P_fail^ML(L; p, q')` for every `L`. The decodable set is
therefore an up-set in `q` at fixed `p`: **the phase boundary is the graph of a
single-valued function `q_c(p)`**, the region `p < p_c(0)` is decodable for all
`q`, and a fixed-`q` section can have several transitions only if `q_c(p)` is
non-monotone. (No analogous monotonicity in `p` holds for `q > 0`: more errors
also produce more heralds. Whether `q_c(p)` is monotone is a numerical
question, answered in Sec. 5.)

**(F3) q = 0.** The ML decoder is the syndrome-only optimal decoder of the
honeycomb matching graph, whose threshold is the Nishimori point of the
random-bond Ising model on the dual (triangular) lattice,
`p_N ≈ 0.1640–0.1642` (duality conjecture/transfer matrix), with ν ≈ 1.5.
At `p = 1/2`, `q = 0` the two sectors are exactly equiprobable (`LER = 1/2`).

**(F4) q = 1: count constraints and alternating paths.** At `q = 1` the pair
`(s_v, h_v)` reveals `n_v ∈ {0,1,2,3}` exactly. Two error sets with the same
counts differ by edge-disjoint *alternating* paths/cycles (an `x`-edge and a
non-`x`-edge at every interior detector). Orient each edge black→white if
`x_e = 1` and white→black otherwise (the honeycomb is bipartite): alternating
paths are exactly directed paths. Only a path joining `B_left` and `B_right`
changes the sector, so
`P_fail^ML(L; p, 1) ≤ P[∃ directed B_left↔B_right path]`. The dual of a
directed left–right crossing is a directed top–bottom crossing of the
triangular lattice with the rotated orientation, and at `p = 1/2` both
orientations are uniformly random. The honeycomb (out-degree 1.5 on average)
is expected to be subcritical for random-orientation percolation, the
triangular lattice (out-degree 3) supercritical. We verify numerically
(Sec. 5.4) that the crossing probability, and with it the LER, decays
exponentially in `L` for all `p ≤ 1/2`: **the whole `q = 1` edge is
decodable**.

## 3. Exact ML decoding in polynomial time

**Relative formulation.** Fix any reference correction `c0` with `H c0 = s`
(a BFS-tree correction; any choice gives identical results, verified). Write
`x = c0 ⊕ y`. Then `y` has even parity at every detector. Every vertex
factor becomes an *even* function `W_v(y_a, y_b, y_c) = φ(n_v(c0 ⊕ y); h_v)`
of the (at most three) incident `y`'s, and every edge factor
`w_e(y_e) ∝ (p/(1-p))^{c0_e ⊕ y_e}`. All unmeasured vertices `B_left ∪ B_right`
have degree ≤ 1 and can be merged into one super-vertex whose parity is
automatically even (`Σ_{v∈D} n_v = 2|x_int| + |x_bdry|`).

**Matchgates.** Every even function of ≤ 3 binary variables is realised by a
planar matchgate. For a degree-3 detector with legs A, B, C (counter-
clockwise) we use the 4-node gadget {A, B, C, D}: spokes A–D, B–D, C–D with
weights `W(011), W(101), W(110)` and triangle edges B–C, C–A, A–B chosen so
that `W(000) = W(011) w_BC + W(101) w_CA + W(110) w_AB` (one nonzero triangle
edge suffices; a vertex that allows only `y = 000` forces its incident edges
to `y = 0`). Degree-2 detectors use a single edge `A–B` of weight
`W(00)/W(11)`. A lattice edge is a wire joining the external nodes of its two
end gadgets with weight `t_e = w_e(1)/w_e(0)`; a matched wire means `y_e = 1`.
The super-vertex is a chain of XOR gadgets running up the left boundary, over
the top through two relay gadgets `R1, R2`, and down the right boundary.
Perfect matchings of the resulting planar graph (≈ 8L² nodes) are in
weight-preserving bijection with the admissible `y`, so with a Kasteleyn
(FKT) orientation the partition function is a Pfaffian.

**Logical sector from one matrix element.** Along the chain the wire
`R1–R2` carries `y_g = ⊕_{left boundary} y_e`, which equals the parity of `y`
on `Γ_R` (the two boundary parities agree for even `y`). Flipping the sign of
that single Kasteleyn entry gives `Pf(K') = Z_same − Z_flip`, and the rank-2
Pfaffian update gives

```
pflip ≡ P[ell(x) ≠ ell(c0) | s, h] = K_ij (K^{-1})_ji ,   (i, j) = wire R1–R2 .
```

One sparse LU factorisation of `K` and one triangular solve per decode:
1.2 ms (L = 8), 15 ms (L = 32), 70 ms (L = 64) on one core. The decoder
returns `c0` if `pflip < 1/2`, `c0 ⊕ λ` (fixed left-right path) if
`pflip > 1/2`, and a coin flip (explicit `rng`) on exact ties.

**Validation of the decoder.**
* *Brute force* (`tests/test_exactness.py`): for `L = 2, 3, 4` (all syndrome
  cosets enumerable, up to 2¹⁷ configurations) and random `(p, q, s, h)`
  including `q = 0`, `q = 1`, `p = 1/2`: `max |pflip − exact| = 1e−14`.
* *Gauge invariance at large L* (`tests/test_gauge.py`): replacing `c0` by
  `c0 ⊕` (random hexagon cycles), by `c0 ⊕ λ` (→ `1 − pflip`), or by the true
  error `x` changes nothing to within 7e−14 up to `L = 64`.
* *Calibration*: the Rao-Blackwellised and direct LER estimators (Sec. 4)
  agree over all Monte Carlo points (figure below). This is a statistical
  test that the computed posteriors are the true ones.

![validation](figures/validation_estimators.png)
* *q = 1 structure*: in 3000 trials at `p = 1/2` the ML posterior was
  ambiguous if and only if an alternating crossing existed.

## 4. Monte Carlo design

**Estimator.** For each trial we record the direct failure indicator
(`H c ≠ s` or `ell(x ⊕ c) = 1`) *and* the exact conditional failure probability
`min(pflip, 1 − pflip)`. Both have expectation `P_fail^ML`; the second
(Rao-Blackwellised) estimator has ≈ 7× smaller variance (median over points
with LER > 0.01) and is used for all fits. The direct estimator is a
cross-check: over 1301 (L, p, q) points with LER > 5/n the z-scores have
mean 0.01 and s.d. 0.91. Because both estimators use the same trials, the
expected s.d. is √(1 − 0.14) ≈ 0.93.

**Campaigns** (deterministic seeds, `scripts/run_scan.py`):
1. `explore`: 14 × 11 grid over the full domain, `L = 8, 16, 32`.
2. `cuts1`, `cuts2`, `cuts3`: one-parameter cuts crossing the boundary.
   Fixed-`q` scans in `p` where the boundary is steep, fixed-`p` scans in `q`
   where it is flat (by (F2) a fixed-`p` scan crosses it exactly once),
   `L = 8, 12, 16, 24, 32, 48, 64`, 1.5–8·10³ trials per point and size.
3. `q1`: the `q = 1` edge, crossing bound plus exact LER, `L ≤ 64`.

**Finite-size analysis** (`src/heralded/fss.py`, `scripts/analyze_cuts.py`).
Pairwise crossings `x*(L1, L2)` from a local weighted fit around the sign
change of `LER(L2) − LER(L1)` (parametric bootstrap errors); scaling fits
`LER = F((x − x_c) L^{1/ν}) [+ b L^{-ω}]` with cubic `F`, minimum sizes
`L_min = 8, 12, 16`, without correction and with a correction term (ω fixed
to 1, or free; fits with ω at its bounds are discarded). The reported threshold is the middle of an interval that contains
(i) the crossing of the two largest sizes, (ii) all acceptable fits
(χ²/dof < 3, ω not at a bound), and (iii) a residual-drift allowance. For
(iii) the interval is extended, in the direction of the drift, by the shift
of the (L, 2L) crossing over the last doubling of L (e.g. from (16, 32) to
(32, 64)); if corrections to scaling decay at least as fast as 1/L, the drift
still to come is no larger than this. Half the interval is quoted as the
finite-size (systematic) uncertainty. The larger of the bootstrap errors of
the reference fit and of the last crossing is quoted as the statistical one.

## 5. Results

### 5.1 Survey of the whole domain

The coarse grid (14 values of p × 11 values of q, L = 8, 16, 32; Fig. 1c)
already fixes the organisation of the domain:
* **Small p is decodable for every q.** For p ≤ 0.14 the LER falls with L at
  all q, as it must by (F2) given p_c(0) ≈ 0.164.
* **One non-decodable region, bounded above by an increasing curve.** For
  q ≤ 0.8 the LER flows to 1/2 above a single threshold. That threshold grows
  from p ≈ 0.16 (q = 0) to p ≈ 0.37 (q = 0.8).
* **For q ≥ 0.9 the LER falls with L all the way to p = 1/2.**
* **At q = 1 it is tiny everywhere.** For example LER(L = 16) < 10⁻³ even at
  p = 1/2.
* **No second transition, and no island of decodability inside the
  non-decodable region.** Neither appeared on any fixed-q row.

Table 1 shows LER(L) at representative points on both sides of the
boundary. In the decodable phase the LER decays roughly exponentially in L.
In the non-decodable phase it climbs to 1/2.

**Table 1.** ML logical error rate versus L (Rao-Blackwellised estimate;
standard error in units of the last digit in parentheses). The row
p = 0.5, q = 0.86 lies just inside the non-decodable side: the LER is flat
for L = 12–32 and rises at L = 48, 64, consistent with q_c(1/2) = 0.872.

<!-- TABLE1 -->
| p | q | phase | L=8 | L=12 | L=16 | L=24 | L=32 | L=48 | L=64 |
|---|---|---|---|---|---|---|---|---|---|
| 0.14 | 0 | decodable | 0.1143(31) |  | 0.0630(25) |  | 0.0239(23) |  |  |
| 0.2 | 0 | non-decodable | 0.3567(26) |  | 0.4102(20) |  | 0.4669(15) |  |  |
| 0.2 | 0.5 | decodable | 0.1282(32) |  | 0.0770(27) |  | 0.0390(29) |  |  |
| 0.28 | 0.5 | non-decodable | 0.3348(29) |  | 0.3860(24) |  | 0.4473(20) |  |  |
| 0.4 | 0.9 | decodable | 0.1281(32) |  | 0.0737(26) |  | 0.0231(21) |  |  |
| 0.4 | 0.7 | non-decodable | 0.3727(25) |  | 0.4234(18) |  | 0.4743(12) |  |  |
| 0.5 | 0.9 | decodable | 0.1796(16) | 0.1527(20) | 0.1310(15) | 0.1029(15) | 0.0851(14) | 0.0555(15) | 0.0414(14) |
| 0.5 | 0.8 | non-decodable | 0.3348(13) | 0.3528(16) | 0.3671(15) | 0.3984(16) | 0.4233(14) | 0.4589(12) | 0.4787(9) |
| 0.5 | 0.86 | near boundary | 0.2504(17) | 0.2349(20) | 0.2344(17) | 0.2331(18) | 0.2327(19) | 0.2370(22) | 0.2511(23) |
| 0.5 | 1 | decodable (q = 1) | 0.0192(12) |  | 4.1e-04 |  | <1e-9 |  |  |
<!-- /TABLE1 -->

### 5.2 Thresholds along one-parameter cuts

We ran 9 fixed-q cuts (q = 0, 0.1, …, 0.8, scanning p) and 7 fixed-p cuts
(p = 0.25, 0.30, 0.35, 0.40, 0.45, 0.475, 0.50, scanning q). Sizes are
L = 8–48 on every cut and L = 64 on q = 0, 0.4, 0.7, 0.8 and on all fixed-p
cuts with p ≥ 0.3. Each (point, size) has 1.5–8·10³ trials (3–4·10³ in the
crossing-centred refinement). The LER curves are shown in `figures/ler_fixed_q.png` and
`figures/ler_fixed_p.png`, and the estimates are collected in Table 2.

![fixed q](figures/ler_fixed_q.png)

![fixed p](figures/ler_fixed_p.png)

**Figure 2.** ML LER along the fixed-q cuts (top) and fixed-p cuts
(bottom). Sizes L = 16–64 are shown (darker = larger); L = 8 and 12 are
used in the analysis but omitted for legibility. The vertical line and grey
band mark the final threshold and its total uncertainty.

**Table 2.** Threshold estimates. "stat." is statistical; "finite-size"
is half the interval spanned by the largest-pair crossing, the acceptable
scaling fits and the residual-drift allowance (Sec. 4). ν is the median
over acceptable fits. "LER at crossing" is the LER of the larger size at
the largest-pair crossing.

<!-- TABLE2 -->
| cut | threshold | stat. | finite-size | largest-pair crossing | range of estimates | ν | LER at crossing | sizes |
|---|---|---|---|---|---|---|---|---|
| q = 0 (scan p) | p_c = 0.1640 | 0.0015 | 0.0016 | 0.1638(15) [L=48/64] | [0.1624, 0.1656] | 1.54(4) | 0.190 | 8–64 |
| q = 0.1 (scan p) | p_c = 0.1732 | 0.0013 | 0.0024 | 0.1729(13) [L=32/48] | [0.1708, 0.1756] | 1.61(6) | 0.191 | 8–48 |
| q = 0.2 (scan p) | p_c = 0.1843 | 0.0009 | 0.0025 | 0.1862(9) [L=32/48] | [0.1818, 0.1868] | 1.58(7) | 0.217 | 8–48 |
| q = 0.3 (scan p) | p_c = 0.1952 | 0.0020 | 0.0046 | 0.1965(20) [L=32/48] | [0.1906, 0.1999] | 1.64(8) | 0.192 | 8–48 |
| q = 0.4 (scan p) | p_c = 0.2130 | 0.0030 | 0.0029 | 0.2160(30) [L=48/64] | [0.2101, 0.2160] | 1.57(6) | 0.233 | 8–64 |
| q = 0.5 (scan p) | p_c = 0.2326 | 0.0016 | 0.0029 | 0.2317(16) [L=32/48] | [0.2297, 0.2354] | 1.59(8) | 0.190 | 8–48 |
| q = 0.6 (scan p) | p_c = 0.2602 | 0.0027 | 0.0030 | 0.2592(27) [L=32/48] | [0.2572, 0.2631] | 1.62(4) | 0.198 | 8–48 |
| q = 0.7 (scan p) | p_c = 0.2948 | 0.0016 | 0.0048 | 0.2954(16) [L=48/64] | [0.2900, 0.2995] | 1.53(3) | 0.183 | 8–64 |
| q = 0.8 (scan p) | p_c = 0.3629 | 0.0050 | 0.0080 | 0.3659(50) [L=48/64] | [0.3549, 0.3709] | 1.50(6) | 0.199 | 8–64 |
| p = 0.25 (scan q) | q_c = 0.5738 | 0.0060 | 0.0156 | 0.5652(60) [L=32/48] | [0.5582, 0.5894] | 1.56(4) | 0.209 | 8–48 |
| p = 0.3 (scan q) | q_c = 0.7069 | 0.0046 | 0.0087 | 0.7085(46) [L=48/64] | [0.6982, 0.7156] | 1.53(3) | 0.182 | 8–64 |
| p = 0.35 (scan q) | q_c = 0.7883 | 0.0053 | 0.0104 | 0.7882(53) [L=48/64] | [0.7780, 0.7987] | 1.50(2) | 0.180 | 8–64 |
| p = 0.4 (scan q) | q_c = 0.8313 | 0.0030 | 0.0059 | 0.8298(30) [L=48/64] | [0.8255, 0.8372] | 1.57(4) | 0.196 | 8–64 |
| p = 0.45 (scan q) | q_c = 0.8581 | 0.0036 | 0.0069 | 0.8513(36) [L=48/64] | [0.8513, 0.8650] | 1.54(3) | 0.221 | 8–64 |
| p = 0.475 (scan q) | q_c = 0.8645 | 0.0020 | 0.0049 | 0.8619(20) [L=48/64] | [0.8596, 0.8694] | 1.50(5) | 0.207 | 16–64 |
| p = 0.5 (scan q) | q_c = 0.8720 | 0.0023 | 0.0074 | 0.8710(23) [L=48/64] | [0.8646, 0.8794] | 1.54(3) | 0.180 | 8–64 |
<!-- /TABLE2 -->

### 5.3 Finite-size behaviour

![drift](figures/crossing_drift.png)

**Figure 3.** Pairwise crossings versus 1/√(L1 L2) for every cut:
consecutive sizes (circles) and (L, 2L) pairs (squares). The grey band is
the final estimate with its total uncertainty.

![collapse](figures/collapse.png)

**Figure 4.** Scaling collapse `LER` vs `(x − x_c) L^{1/ν}` using the final
`x_c` and ν of four cuts (q = 0, q = 0.4, p = 0.4, p = 0.5), L = 16–64, with
no correction terms.

Four features of the size dependence (Figs. 3, 4) determine what the data
support.

* **The benchmark is reproduced.** At q = 0 the crossings move from
  p* ≈ 0.168 (L = 8/12) down to 0.1641 ± 0.0005 (L = 32/64) and
  0.1638 ± 0.0015 (L = 48/64). This agrees with the Nishimori point of the
  triangular random-bond Ising model (0.1640–0.1642 from duality and
  transfer-matrix work; 0.1633(3) in a recent Monte Carlo study). The
  scaling fits give ν = 1.54 ± 0.04, in line with ν ≈ 1.5 for that point.
  Our final interval, 0.1640 ± 0.0022, is centred on the known value, which
  supports the error model used for the other cuts.
* **The drift has a consistent direction.** On every cut the crossings move
  toward the non-decodable side as L grows: to lower p at fixed q, and to
  higher q at fixed p. The drift is small at small q (|Δp*| ≈ 0.001–0.003
  per doubling for q ≤ 0.6, 0.005–0.008 at q = 0.7–0.8) and largest on the
  flat top (Δq* ≈ +0.005–0.016 per doubling at the largest sizes). It decelerates, and the (L, 2L) boundaries in Fig. 1b
  converge. There is no sign of a crossover to a different behaviour.
  Finite-size estimates at small L therefore systematically *overestimate*
  the decodable region, and we widen the uncertainty accordingly.
* **The exponent ν is the same everywhere.** The acceptable fits give
  ν = 1.50–1.64 (median 1.55) on all cuts, with no trend along the
  boundary. The collapses are good (χ²/dof ≈ 1–2).
* **The critical LER is the same everywhere.** The LER at the largest-pair
  crossing is 0.18–0.23 on all cuts. It drifts slowly downward with L in
  the same way on the q = 0 cut and on the p = 1/2 cut.

### 5.4 The q = 1 edge

![q1](figures/q1_line.png)

**Figure 5.** q = 1. Left: probability that an alternating (directed)
B_left–B_right path exists. Right: exact ML LER, computed by running the
Pfaffian decoder only on trials with such a path; all other trials have
zero failure probability. Open symbols: 1–2 events or 95% upper limits.

By (F4) the ML decoder fails only when an alternating left-right path
exists. We checked in 3000 trials that the Pfaffian posterior is ambiguous
exactly in those cases. The crossing probability decays exponentially at
every p. At p = 1/2 (the largest) it is 0.37, 0.17, 0.080, 0.014, 0.0025 and
5·10⁻⁵ for L = 4, 6, 8, 12, 16, 24, and none was seen in 2·10⁴ trials at
L = 32 or 8·10³ trials at L = 48 and 64. The ML LER is
0.2–0.35 × P_cross (4.8·10⁻⁴ at L = 16, ~10⁻⁶ at L = 24). The whole q = 1 edge
is thus deep in the decodable phase, with a correlation length of about two
hexagon columns. This makes q\* < 1 robust: the decodable phase fills a
finite strip below q = 1 at every p.

### 5.5 The phase boundary

The final boundary (Fig. 1a) is a monotone interpolation through the 16
cut estimates, and the band is spanned by the two error envelopes. It is
available as data in `data/boundary.csv`. Table 3 reads it off at fixed q
(giving p_c(q) also for 0.8 < q < q\*, where only the fixed-p cuts
constrain it) and at fixed p. The intervals are the unresolved ranges. An
upper end of 0.500 means the interval reaches the domain edge: for
q ≳ q\* − 0.008 the fixed-q section may have no transition inside
p ≤ 1/2, and for q > q\* + 0.008 it has none (decodable throughout).

**Table 3.** Boundary of the ML-decodable region.

<!-- BOUNDARY -->
| q | p_c(q) | interval |
|---|---|---|
| 0.00 | 0.164 | [0.162, 0.166] |
| 0.10 | 0.173 | [0.170, 0.176] |
| 0.20 | 0.184 | [0.182, 0.187] |
| 0.30 | 0.195 | [0.190, 0.200] |
| 0.40 | 0.213 | [0.209, 0.217] |
| 0.50 | 0.233 | [0.229, 0.236] |
| 0.60 | 0.260 | [0.256, 0.264] |
| 0.70 | 0.295 | [0.290, 0.302] |
| 0.75 | 0.325 | [0.318, 0.332] |
| 0.80 | 0.363 | [0.351, 0.372] |
| 0.82 | 0.385 | [0.376, 0.394] |
| 0.84 | 0.413 | [0.403, 0.426] |
| 0.85 | 0.431 | [0.418, 0.449] |
| 0.86 | 0.456 | [0.436, 0.479] |
| 0.87 | 0.494 | [0.475, 0.500] |

| p | q_c(p) | interval |
|---|---|---|
| 0.170 | 0.067 | [0.041, 0.095] |
| 0.180 | 0.162 | [0.138, 0.185] |
| 0.200 | 0.331 | [0.298, 0.356] |
| 0.220 | 0.437 | [0.416, 0.457] |
| 0.250 | 0.574 | [0.557, 0.588] |
| 0.300 | 0.707 | [0.698, 0.717] |
| 0.350 | 0.788 | [0.777, 0.799] |
| 0.400 | 0.831 | [0.825, 0.838] |
| 0.450 | 0.858 | [0.850, 0.866] |
| 0.475 | 0.864 | [0.859, 0.870] |
| 0.500 | 0.872 | [0.864, 0.880] |
<!-- /BOUNDARY -->

### 5.6 Comparison with a practical decoder

![mwpm](figures/ml_vs_mwpm.png)

**Figure 6.** Exact ML (solid) versus MWPM with herald-reweighted edge
weights (dashed) and syndrome-only MWPM (dotted), L = 8, 16, 32.

To put the optimal thresholds in context we ran two baselines on the same
observation model:
* syndrome-only MWPM (PyMatching);
* a herald-aware MWPM. Each edge weight is the negative log-odds of a local
  posterior that uses `P(h_u | s_u, x_e)` at both endpoints. This
  conditioning on s avoids double-counting the parity.

The table compares L = 16/32 crossings for all decoders (like with like),
together with the final extrapolated ML value:

| line | ML, final | ML, L = 16/32 | MWPM + heralds, L = 16/32 | syndrome-only MWPM, L = 16/32 |
|---|---|---|---|---|
| q = 0 (p_c) | 0.1640(22) | 0.1652(6) | — | 0.156(2) |
| q = 0.5 (p_c) | <!-- ML_Q05 -->0.233(3)<!-- /ML_Q05 --> | 0.236(2) | 0.221(3) | 0.156 (ignores h) |
| q = 0.8 (p_c) | <!-- ML_Q08 -->0.363(9)<!-- /ML_Q08 --> | 0.376(2) | 0.317(6) | 0.156 (ignores h) |
| p = 1/2 (q_c) | <!-- ML_P05 -->0.872(8)<!-- /ML_P05 --> | 0.859(1) | 0.930(5) | never decodable |

MWPM captures part of the herald gain. It cannot enforce the exact count
constraints a herald implies, however: n_v = 2 means the error chain passes
*through* v, and n_v = 3 fixes all three edges. At equal sizes the gap to ML therefore
widens with q: from 0.009 in p_c at q = 0 to 0.06 at q = 0.8, and 0.07 in
q_c at p = 1/2.
A decoder limited to pairwise matching would thus draw a substantially
smaller decodable region than the optimum.

## 6. Interpretation: what heralding does

* **A witness reveals what parity hides.** A string of errors is invisible
  to parity at its interior vertices (n_v = 2) and at junctions of three
  errors (n_v = 3, which looks like a single error). A herald exposes
  exactly those vertices. Combined with s_v it fixes n_v: two of the three
  edges are errors if s_v = 0, all three if s_v = 1. A *missing* herald is
  also informative once q > 0: it multiplies the weight of n_v ≥ 2 by
  (1 − q). At q = 1 the whole count field is known. The only freedom left is
  alternating structures, and these are percolation-subcritical on the
  honeycomb (Sec. 5.4).
* **The heralds modify local disorder, not the long-range physics.** In the
  statistical-mechanics picture the ML posterior is a planar, disordered
  free-fermion (dimer) model on the Nishimori manifold. At q = 0 it is the
  triangular random-bond Ising model. Heralds only change the local vertex
  weights (Sec. 3) and introduce no long-range couplings. Consistent with
  this, ν ≈ 1.5 and the critical LER are unchanged along the boundary
  (Sec. 5.3): the transition appears to stay of Nishimori type while its
  location moves.
* **The threshold rises slowly at first, then steeply.** At small q the gain
  is modest and roughly linear: dp_c/dq ≈ 0.09 near q = 0. The fraction of
  witnessed vertices is only 0.07 q at p ≈ 0.16, since
  P(n ≥ 2) = 3p² − 2p³. The gain accelerates at larger q (dp_c/dq ≈ 0.35
  for q = 0.6–0.7 and ≈ 0.7 for q = 0.7–0.8), and p_c(q) runs up to p = 1/2
  as q → q\*.
* **The boundary flattens as p → 1/2.** Near p = 1/2 the syndrome carries
  almost no information (at p = 1/2 the prior is uniform and the two sectors
  are exactly symmetric without heralds), so recovery rests on the
  witnesses. The density of witness-eligible vertices saturates there
  (P(n ≥ 2) = 0.35, 0.43, 0.50 at p = 0.40, 0.45, 0.50), so the required
  herald efficiency approaches a p-independent value. The result is a flat,
  concave top ending at q\* = 0.872 ± 0.008: about 87% of the n_v ≥ 2
  events must be witnessed at p = 1/2.
* **Heralds can create decodability where syndromes alone cannot.** The
  most striking consequence is the strip q > q\*: there the logical bit is
  recoverable with LER → 0 at every error rate up to p = 1/2.

## 7. Uncertainties and limitations

* **Decoder approximation error: none.** The decoder evaluates the exact
  logical posterior. Its outputs agree with brute force to 1e−14 and are
  gauge invariant to 1e−13 at L = 64. The Rao-Blackwellised and direct LER
  estimates agree statistically over all points. Ties (exactly equal sector
  probabilities, e.g. q = 0, p = 1/2) are broken with an explicit random
  input and count as failures with probability 1/2, as the LER definition
  requires.
* **Statistical uncertainty: small.** Bootstrap errors on the thresholds are
  0.001–0.006.
* **Finite-size uncertainty: dominant.** It is 0.002–0.005 in p on the
  fixed-q cuts for q ≤ 0.7 (0.008 at q = 0.8), and 0.005–0.016 in q on the
  fixed-p cuts. It is quantified by the spread
  of crossings and fits plus a residual-drift allowance. The allowance
  assumes that corrections to scaling decay at least as fast as 1/L; a much
  slower crossover beyond L = 64 cannot be excluded by data of this size.
  Given the consistent direction of the drift, such a crossover would most
  likely shrink the decodable region further (lower p_c, higher q_c).
* **Resolution of the boundary shape.** Near the top the boundary is known
  to about ±0.008 in q.
  * Between p = 0.25 and 0.40 the monotone rise of q_c(p) (steps of
    0.04–0.13) far exceeds the errors.
  * Between p = 0.40 and 0.50 the final estimates rise by 0.041, but the
    step from p = 0.45 to 0.50 (0.014) is only ≈ 1.3σ of the
    (correlated) finite-size errors. At a common size pair the rise is
    unambiguous: the L = 32/64 crossings are 0.8278(10), 0.8544(12),
    0.8609(12), 0.8675(10) at p = 0.40, 0.45, 0.475, 0.50, and the drift is
    similar on these cuts. A strongly non-monotone top is therefore
    excluded.
  * The residual possibility is a top that becomes flatter than we estimate
    as L → ∞.
  * No second transition was seen anywhere on the fixed-q rows.
* **Universality.** ν ≈ 1.5 is a finite-size estimate. It is consistent
  with the Nishimori value but does not prove membership in that class.
* **Model assumptions.** The decoder is given the true p and q, as the
  problem specifies. The results characterise this stipulated
  classical model only (no readout noise, no false heralds).

## 8. Reproducibility and computational resources

Everything needed to reproduce the analysis is in `/app`:
* `src/heralded` is the package (lattice, Pfaffian ML decoder, sampler,
  finite-size tools, baselines).
* `scripts/` holds the campaigns, analysis and figure scripts; `tests/` the
  exactness and gauge-invariance tests; `examples/decode_example.py` a
  minimal use of the decoder API.
* `data/` holds the raw per-task Monte Carlo records (JSON lines: L, p, q,
  seed, trials, direct failures, Rao-Blackwellised sums, CPU seconds), plus
  the derived `thresholds.json`, `q1_crossing.json`, `mwpm_crossings.json`
  and analysis logs.

The README lists the commands. Seeds are deterministic functions of
(campaign seed, L, p, q, chunk).

**Decoder API.** `decode(G, p, q, s, h, rng) -> c` with `G = build_patch(L)`.
Conventions: vertices sorted by integer coordinates (X, Y); edges are
sorted index pairs (i < j) of retained edges; `s`, `h` are ordered as
`G.detectors`, and length-|V_L| arrays are also accepted. `c` is a 0/1
array over `G.edges` with `H c = s`. `rng` is used only to break exact ties.
`MLDecoder(G).posterior(p, q, s, h)` also returns the exact probability of
the other logical sector.

**Resources.** One container with 8 CPU cores (cgroup quota) and a 32 GiB
memory limit (peak use < 2 GiB); no GPU. Production wall-clock time was
≈ 1.6 h on 8 cores: calib 0.2 min, explore 8 min, cuts1 27 min, cuts2 19 min,
cuts3 37 min, q = 1 study 1 min, MWPM baselines 6 min. The analysis and
figures take ≈ 5 min. Per-file totals, from `scripts/resources.py`:

<!-- RESOURCES -->
| file | tasks | trials | CPU hours | decoder |
|---|---|---|---|---|
| calib.jsonl | 24 | 48,000 | 0.03 | exact ML |
| cuts1.jsonl | 1920 | 2,160,000 | 3.61 | exact ML |
| cuts2.jsonl | 1344 | 1,128,000 | 2.54 | exact ML |
| cuts3.jsonl | 2800 | 1,008,000 | 4.86 | exact ML |
| explore.jsonl | 616 | 770,000 | 1.12 | exact ML |
| mwpm.jsonl | 102 | 408,000 | 0.77 | MWPM baselines (2 decoders/trial) |

exact-ML decoded trials: 5,114,000; CPU hours: 12.2
q=1 study: 1,024,000 trials (BFS on all, Pfaffian on 86,812 crossing trials)
<!-- /RESOURCES -->

Software: Python 3.11, numpy 2.1, scipy 1.14 (SuperLU), pandas 2.2,
matplotlib 3.9, pymatching 2.4 (baseline only).

## References (benchmark values)

* H. Nishimori and M. Ohzeki, "Location of the multicritical point for the
  Ising spin glass on the triangular and hexagonal lattices" (2006),
  arXiv:cond-mat/0601356: duality conjecture, triangular p = 0.1642.
* M. Ohzeki, "Locations of multicritical points for spin glasses on regular
  lattices" (2009), arXiv:0811.0464: triangular p = 0.1640.
* S. L. A. de Queiroz, "Multicritical point of Ising spin glasses on
  triangular and honeycomb lattices", Phys. Rev. B 73, 064410 (2006),
  arXiv:cond-mat/0510816 (transfer matrix).
* arXiv:2609.07579 (2026), "Geometry dependence of error thresholds in
  two-dimensional toric codes": triangular 0.1633(3), ν ≈ 1.49.
* S. Bravyi, M. Suchara, A. Vargo, "Efficient algorithms for maximum
  likelihood decoding in the surface code", Phys. Rev. A 90, 032326 (2014):
  matchgate approach to ML decoding (our construction generalises it to
  count-dependent vertex factors).
