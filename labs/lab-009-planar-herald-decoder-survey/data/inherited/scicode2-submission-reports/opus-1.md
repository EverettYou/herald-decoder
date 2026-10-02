# Decoding with incomplete local witnesses: the (p, q) phase diagram of the heralded honeycomb patch

**Short answer.** With an exact, Bayes-optimal decoder, the square 0 ≤ p ≤ ½, 0 ≤ q ≤ 1 splits into
exactly two phases, separated by one smooth, monotone curve q_c(p) (Fig. 1).
- **Decodable phase** (small p or large q): P_fail → 0 as L grows.
- **Non-decodable phase** (large p, small q): P_fail → ½, i.e. the logical information is lost completely.

Along that curve:
- **Syndrome-only end (q = 0):** the threshold is p_c(0) = 0.1634 ± 0.0017. This is the Nishimori point of the
  triangular-lattice random-bond Ising model (0.1640), as it must be for an optimal decoder.
- **Effect of heralds:** the threshold rises continuously with q: p_c = 0.184 at q = 0.2, 0.234 at q = 0.5,
  0.299 at q = 0.7.
- **The corner at p = ½:** the boundary reaches p = ½ at **q\* = 0.869 ± 0.005**. For q > q\* the logical
  bit can be recovered at every p ≤ ½, including p = ½, where the syndrome alone carries exactly zero
  logical information.
- **Complete witnessing (q = 1):** logical errors need a directed ("alternating") crossing of the patch. This
  gives a rigorous upper bound on P_fail, and the crossing probability vanishes quickly with L at every p ≤ ½.
- **Nature of the transition:** it is sharp everywhere. The finite-size crossings converge, and the
  scaling-collapse exponent is ν = 1.44–1.68 on 16 of the 17 scan lines (1.79 ± 0.11 on the weakest one).
  This is consistent with the Nishimori universality class (ν ≈ 1.50) of the q = 0 end point.

Raw numbers: `results/boundary_estimates.csv` (boundary) and `results/ler_table_all.csv` (all LER data).

![phase diagram](figures/phase_diagram.png)

**Figure 1.** (a) Phase diagram of the optimal decoder.
- Open circles: thresholds p_c(q) from fixed-q scans in p. Filled squares: q_c(p) from fixed-p scans in q.
  Error bars are ±2σ_tot (statistical ⊕ finite-size ⊕ method).
- Grey diamonds: the q = 0.85 and 0.86 p-scans of the re-entrance test (§5.4). They agree with the curve but
  constrain it only weakly, because the boundary is nearly parallel to the p axis there.
- Grey band: the region left unresolved by these uncertainties, interpolated along the curve.
- Star: Nishimori point of the triangular random-bond Ising model (RBIM), 0.1640 [Ohzeki 2009].
- Dashed/dotted lines: curves of constant density of *unwitnessed* multi-error vertices,
  (1−q)P(n_v ≥ 2) = 0.060 and 0.072 (§5.5).

(b), (c) Zooms on the two ends of the boundary.

---

## 1. Problem recap and conventions

The patch G_L, the check matrix H, the set Γ_R and the sampling rules are built exactly as in the problem
statement (`src/honeycomb.py`; Fig. `figures/patch_L3.png` reproduces the problem's Figure 1). Sizes:
- |E_L| = 3L² − 1 retained edges.
- |D_L| = 2L² − 2 detectors (all of degree 3, except 2L − 2 degree-2 vertices on the top and bottom rows).
- Γ_R and Γ_L each contain L + 1 horizontal boundary edges.
- The minimum weight of a logical operator is 2L − 1.

Array conventions (sorted vertex, edge and detector orders) are documented in `README.md` and `src/honeycomb.py`.

The public decoder is `decode(G, p, q, s, h, rng=None) -> c` in `src/decoder_api.py`. It returns a uint8
correction c with Hc = s. The optional `rng` only breaks exact ties between the two logical sectors (e.g. at
p = ½, q = 0). A coordinate-keyed wrapper, `decode_coords`, lets the decoder be evaluated without adopting our
index conventions.

## 2. Computational approach: an exact optimal decoder

### 2.1 Posterior, and why ML decoding settles the "decoder" question

Let w = p/(1−p). The joint law of errors and observations is P(x, s, h) = (1−p)^|E| W(x), where

  W(x) = Π_e w^{x_e} Π_{v∈D} φ_v(n_v(x)),
  φ_v(n) = [n ≡ s_v mod 2] · ( q·[n ≥ 2]  if h_v = 1;   1 − q·[n ≥ 2]  if h_v = 0 ).

Given (s, h), the success probability of a correction depends only on its logical sector. It is therefore
maximised by the sector with the larger posterior weight Z_ℓ = Σ_{Hx = s, sector ℓ} W(x) (Bayes rule).

Consequences:
- The maximum-likelihood (ML) decoder has the lowest possible LER at every (L, p, q).
- Its phase diagram is the information-theoretic one, valid for every decoder.
- "Decoder approximation error" is zero by construction. What remains is floating-point error, which we
  measure (§3).

### 2.2 Reduction to planar perfect matchings

Write x = x0 ⊕ y, with Hx0 = s and y ∈ ker H.

**Vertex factors are matchgates.** As a function of its 2 or 3 incident y-bits, every detector factor is
supported only on even-parity patterns. It is therefore a parity-respecting signature of arity ≤ 3, which is
precisely the class realisable by planar matchgates (Valiant; Cai et al.).

**The gadget.** Each detector becomes one 4-node gadget {c, o1, o2, o3}: a K4 drawn with c inside the
triangle, with weights a_i on c–o_i and t_ij on o_i–o_j. Removing the o-nodes of occupied edges gives
- Γ(000) = a1t23 + a2t13 + a3t12;
- Γ(011) = a1, Γ(101) = a2, Γ(110) = a3;
- Γ(odd pattern) = 0.

This reproduces any even signature, including hard constraints: q = 1, and heralded vertices, which require
n_v = 2 or 3.

**Edges and boundaries.**
- Each retained edge becomes a connecting edge between the o-nodes of its endpoints, with weight
  w^{1−2x0_e}.
- Each unmeasured boundary is replaced by a "rail": a chain of even-parity gadgets through its degree-1
  vertices.
- The tops of the two rails are joined by a three-edge path whose first edge carries a weight κ. Parity
  forces that path to be used exactly when ℓ(y) = 1.

Hence the planar perfect-matching polynomial is PM(κ) ∝ Z_A + κ Z_B.

**How the heralds enter.** The heralds become purely local weights:
- A heralded s = 0 vertex must carry exactly two errors.
- A heralded s = 1 vertex forces all three incident edges.
- Every unheralded vertex suppresses a pass-through (n = 2 or 3) by a factor 1 − q.

At q = 0 the construction reduces to the known planar-Ising/Pfaffian ML decoder of the surface code
(Bravyi–Suchara–Vargo 2014).

### 2.3 One sparse LU per syndrome

**Fixed orientation per L.** For a given L the gadget graph has a fixed topology, with N = 4(|D| + 2L + 2) + 2
≈ 8L² nodes. A Kasteleyn orientation is computed once per L from a straight-line planar embedding:
- faces are traced from the rotation system;
- the orientation is propagated along a dual spanning tree;
- every inner face is checked for an odd number of clockwise edges.

Zero weights (deleted edges) preserve the Kasteleyn property.

**Pfaffian ratio from one factorisation.** Then Pf K(κ) = ±PM(κ), with a sign independent of κ. Because κ
occupies a single matrix entry (i, j), the rank-2 Pfaffian identity gives the exact sector bias

  Δ = (Z_A − Z_B)/(Z_A + Z_B) = Pf K(−1)/Pf K(+1) = 1 − 2σ_ij [K(+1)⁻¹]_{ji}.

This needs one sparse LU factorisation (SuperLU, COLAMD ordering) and one triangular solve. The decoder
returns x0 or x0 ⊕ λ (λ a fixed logical representative), according to the sign of Δ. The exact posterior
probability of the returned sector is (1 + |Δ|)/2.

**Cost (one core):**

| L | 16 | 32 | 48 | 64 | 96 |
|---|---|---|---|---|---|
| time per syndrome | 2.3 ms | 9 ms | 25 ms | 50 ms | 120 ms |

Empirically this scales as ≈ N^1.15. This speed is what made it possible to map the whole plane with the
*optimal* decoder up to L = 96.

## 3. Validation (why the numbers can be trusted)

1. **Exactness against brute force.** For L = 2, 3, 4 the posterior was enumerated over all 2^(L²+1)
   elements of ker H (`tests/test_exact_small.py`). Across 450 random syndromes — p ∈ {0.02, …, 0.5},
   q ∈ {0, 0.3, 0.7, 0.95, 1}, including hard-constraint cases — max |Δ_Pfaffian − Δ_exact| ≤ 1.5·10⁻¹⁴.
   The public API returns the sector with the larger exact weight in every test (`tests/test_api.py`).
2. **Floating-point accuracy at large L.** Δ was compared with log Z_A − log Z_B computed from two
   independent sector-restricted determinants (`tests/test_precision.py`). Agreement is to < 10⁻¹² in
   log-likelihood ratio at L = 16. At L = 48 it is < 10⁻⁷ for |LLR| < 20 and ≈ 10⁻³ at |LLR| ≈ 25–30. Such
   samples carry min(π) ≈ 10⁻¹¹, so this has no effect on any LER quoted here.
   No run ever produced a non-finite or out-of-range Δ; the driver raises an error if one does.
3. **Calibration of the posterior on the Monte-Carlo data** (Fig. 8):
   - Among trials where the decoder reports posterior π, the truth lies in the favoured sector with
     frequency π, in every |Δ| bin (reliability diagram over all 6.03·10⁶ trials).
   - The hard failure frequency and the Rao–Blackwellised estimator E[min(π_A, π_B)] agree point by point:
     z-scores have mean −0.02 and s.d. 0.90 over 2027 (L, p, q) points.
   - Both tests would fail if the posterior were wrong.
4. **Physics benchmark.** At q = 0 the optimal threshold must equal the Nishimori point of the RBIM on the
   dual (triangular) lattice, 0.1640 [Nishimori–Ohzeki 2006, Ohzeki 2009, de Queiroz 2006]. We find
   p_c(0) = 0.1634(4)(16) from crossings, and 0.1643(1) with ν = 1.47(3) from the scaling collapse.
5. **Exact identities.**
   - At (p, q) = (½, 0) the decoder returns Δ = 0 exactly for every syndrome, as it must.
   - Along all fixed-p scans the measured LER never increases with q: 0 of 392 adjacent pairs are
     violated. This is required by the garbling argument of §5.4.

![validation](figures/validation.png)

**Figure 8.** (a) Reliability diagram of the exact posterior over all 6.03·10⁶ Monte-Carlo trials.
(b) Hard failure frequency versus the Rao–Blackwellised soft estimate at 2027 (L, p, q) points.

## 4. Monte-Carlo design and finite-size analysis

**Estimators.** For each (L, p, q) we record the hard failure frequency (the definition of P_fail) and the
soft estimator S = E[min(π_A, π_B)].
- S is unbiased for the ML LER, because P(fail | s, h) = min(π_A, π_B) for the exact posterior.
- Near the transition S has ≈ 14× smaller variance.
- All crossings and fits use S. Hard and soft agree within errors everywhere (§3).

**Sampling plan** (all seeds derived from `sha256(master|L|p|q|batch)`):
- *Exploration:* coarse grid, L = 8, 16, 32, 48.
- *Production:* 8 fixed-q scans in p (q = 0, 0.1, …, 0.7) and 7 fixed-p scans in q
  (p = 0.30, 0.35, 0.40, 0.44, 0.46, 0.48, 0.50). Each scan has 9 points around the transition, at
  L = 8, 12, 16, 24, 32, 48, 64, with 6000/6000/6000/5000/5000/3000/2000 trials per point.
- *Refinement:* L = 96 (1800 trials/point) on the q = 0 line and the p = 0.40, 0.46, 0.50 lines; plus
  fixed-q scans at q = 0.85, 0.86, 0.87 over p ∈ [0.40, 0.50] (L = 16, 32, 64) to test re-entrance.
- *Full-domain map:* 20 × 11 grid (p = 0.025…0.5, q = 0…1) at L = 16, 32, 48.

**Crossings.**
- Each LER curve is fitted locally: a cubic through the 7 points nearest the crossing. The difference from
  a quadratic through 5 points is kept as an estimator uncertainty.
- Statistical errors come from a parametric bootstrap.
- A global quadratic over the full window was tried first and rejected: it biases the crossings of the
  steep large-L curves (it gave a spurious 0.161 at q = 0).

**Boundary estimate and error budget** for each scan line:
- *Estimate:* the crossing of the largest doubling pair (48/96 where available, otherwise 32/64).
- *σ_stat:* bootstrap.
- *σ_sys* combines three terms:
  - the last observed drift |x(L, 2L) − x(L/2, L)|;
  - the local-fit estimator difference;
  - the difference from an independent scaling-collapse estimate, P = F((t − t_c)L^{1/ν}) with F quadratic,
    fitted to 0.08 < P < 0.38 for L ≥ 32.
- We deliberately do *not* extrapolate the drift. At q = 0, where the answer is known, a geometric
  extrapolation overshoots (it predicts 0.162), whereas the largest-pair crossing is within 0.0006 of
  0.1640. Collapse fits with an explicit correction-to-scaling term were unstable (ω runs to its bounds).

Figure 3 shows the drift. Crossings move monotonically. On the four lines with L = 96, x(48, 96) differs
from x(32, 64) by ≤ 0.0013. On the other lines, x(32, 64) differs from x(16, 32) by 0.001–0.003 in p and
0.003–0.011 in q.

## 5. Results

### 5.1 The boundary

| fixed | scan | estimate | σ_stat | σ_sys | pair | collapse t_c | ν (collapse) | ρ_h |
|---|---|---|---|---|---|---|---|---|
| q = 0.0 | p | p_c = 0.1634 | 0.0004 | 0.0016 | 48/96 | 0.1643 | 1.47(3) | 0.071 |
| q = 0.1 | p | 0.1733 | 0.0004 | 0.0016 | 32/64 | 0.1737 | 1.51(5) | 0.072 |
| q = 0.2 | p | 0.1842 | 0.0005 | 0.0019 | 32/64 | 0.1846 | 1.44(5) | 0.071 |
| q = 0.3 | p | 0.1974 | 0.0005 | 0.0023 | 32/64 | 0.1970 | 1.50(7) | 0.071 |
| q = 0.4 | p | 0.2124 | 0.0005 | 0.0015 | 32/64 | 0.2123 | 1.55(4) | 0.070 |
| q = 0.5 | p | 0.2335 | 0.0007 | 0.0028 | 32/64 | 0.2330 | 1.57(4) | 0.069 |
| q = 0.6 | p | 0.2596 | 0.0006 | 0.0034 | 32/64 | 0.2588 | 1.50(5) | 0.067 |
| q = 0.7 | p | 0.2990 | 0.0011 | 0.0033 | 32/64 | 0.2975 | 1.68(7) | 0.064 |
| q = 0.85 | p | 0.438 | 0.003 | 0.015 | 32/64 | 0.434 | 1.51(7) | 0.061 |
| q = 0.86 | p | 0.466 | 0.004 | 0.022 | 32/64 | 0.466 | 1.79(11) | 0.063 |
| p = 0.30 | q | q_c = 0.704 | 0.002 | 0.009 | 32/64 | 0.703 | 1.59(9) | 0.064 |
| p = 0.35 | q | 0.783 | 0.001 | 0.011 | 32/64 | 0.783 | 1.65(8) | 0.061 |
| p = 0.40 | q | 0.8301 | 0.0010 | 0.0040 | 48/96 | 0.8294 | 1.62(4) | 0.060 |
| p = 0.44 | q | 0.8506 | 0.0012 | 0.0061 | 32/64 | 0.8496 | 1.59(5) | 0.061 |
| p = 0.46 | q | 0.8587 | 0.0009 | 0.0034 | 48/96 | 0.8584 | 1.56(4) | 0.062 |
| p = 0.48 | q | 0.8629 | 0.0009 | 0.0073 | 32/64 | 0.8628 | 1.50(5) | 0.064 |
| p = 0.50 | q | **q\* = 0.8685** | 0.0008 | 0.0051 | 48/96 | 0.8663 | 1.56(4) | 0.066 |

(ρ_h = (1 − q)(3p² − 2p³) evaluated on the boundary; see §5.5.)

The two scan directions agree where they overlap:
- the q = 0.7 p-scan gives (0.299, 0.70), and the p = 0.30 q-scan gives (0.30, 0.704);
- the q = 0.85 and 0.86 p-scans agree with the q-scans at p = 0.44–0.48.

The p-scans near the corner have large σ_sys only because the boundary is almost parallel to the p axis
there; the q-scans resolve the same region to ±0.003–0.007 in q.

![LER curves](figures/ler_curves.png)

**Figure 2.** LER of the optimal decoder for the five largest sizes available on each line (up to L = 96).
Top row: fixed-q scans in p. Bottom row: fixed-p scans in q. Grey band: ±2σ_tot around the estimated boundary. All curves cross in a single point up to a small
drift, the hallmark of a continuous decoding transition.

![crossing drift](figures/crossing_drift.png)

**Figure 3.** Crossing points x(L, 2L) of doubling pairs, relative to the final estimate, versus
1/√(L·2L). p-crossings drift slightly downward and q-crossings slightly upward, both converging. At the
largest pairs the drift per doubling is ≤ 0.002 on the lines with L = 96, and ≤ 0.003 (p) or ≤ 0.011 (q)
elsewhere.

### 5.2 Phase assignment over the whole domain

A 20 × 11 grid over the entire square (Fig. 5a) shows the sign of the LER trend between L = 16 and
L = 48. Every grid point falls into one of four classes:
- clearly decreasing (blue — decodable);
- already below 10⁻³ at both sizes (dark blue — deep in the decodable phase);
- clearly increasing towards ½ (red — non-decodable);
- saturated at ½ at both sizes (grey dots at large p and small q — deep in the non-decodable phase).

The few points with an insignificant trend that are not saturated lie on the estimated boundary.

There is no second region, island or re-entrant pocket anywhere.

In the non-decodable phase the LER approaches ½ (Fig. 6; e.g. q = 0, p = 0.25 gives 0.468, 0.496, 0.4999
at L = 8, 16, 32): the logical information is lost completely, not merely degraded. In the decodable phase
it decays exponentially in L (Fig. 6).

![size trend](figures/size_trend_map.png)

**Figure 5.** (a) Size trend of the LER from L = 16 to 48 on the whole domain.
- Colour: the relative decrease ΔP/P₁₆ where the LER falls, or the fraction of the remaining gap to ½
  closed where it rises.
- Dots: changes below 2σ. Dark-blue squares: both LERs < 10⁻³.

(b) LER at L = 48 versus p for several q: heralding lowers the logical error rate at every p, also well
inside the decodable phase.

![LER vs L](figures/ler_vs_L.png)

**Figure 6.** LER versus L at representative points: exponential decay inside the decodable phase, and
convergence to ½ inside the non-decodable phase.

### 5.3 The two edges of the domain: p = ½ and q = 1

**p = ½.** Here the prior is uniform. At q = 0 the posterior of the logical is exactly ½ for every syndrome,
so P_fail = ½ at every L. Heralds alone restore recoverability, once q exceeds
q\* = 0.8685 ± 0.0008 (stat) ± 0.0051 (sys).

The L = 96 data narrows the range: the crossings are 0.8672 (32/64), 0.8652 (48/64), 0.8685 (48/96) and
0.8682 (64/96). A residual upward creep of a few 10⁻³ is possible; q\* < 0.88 is safe.

**q = 1.** All n_v are known, so any two configurations with the same (s, h) differ by alternating cycles and
alternating boundary-to-boundary paths (each vertex along the path uses one error edge and one non-error
edge).
- Orient error edges black→white and the other edges white→black on the bipartite honeycomb. Alternating
  paths are then exactly the directed paths.
- The wrong sector has non-zero posterior weight *iff* a directed B_left–B_right crossing exists. This
  equivalence was checked against the ML decoder in 1200/1200 trials.
- Hence P_fail^ML(q = 1) ≤ P(directed crossing).

The crossing probability was estimated by BFS up to L = 128 (Fig. 7). At p = 0.5 it is 0.37, 0.082,
0.014 and 0.0035 at L = 4, 8, 12, 16, i.e. ∝ e^{−L/ξ} with ξ ≈ 2.5. There was *no* crossing in 4000
trials at L = 24, 32, 48, 64, nor in 1000 trials at L = 128, for any of p = 0.3, 0.4, 0.5.

So the whole line q = 1 is decodable, with a *rigorous* bound on the LER. Consistently, the ML posterior was
certain (min π ≈ 10⁻¹⁶) in every q = 1 trial at L = 48 over the whole p range. The q = 1 decoding problem
is a random oriented-percolation problem on the honeycomb, and it is subcritical for every p ≤ ½.

For q < 1 this support argument fails. Unheralded vertices can hide an extra pass-through, so the wrong
sector always has non-zero weight, and decodability becomes a genuine thermodynamic question. That is why
q\* lies strictly below 1.

![q1](figures/q1_crossing_bound.png)

**Figure 7.** q = 1: probability of a directed left–right crossing, which upper-bounds the ML LER.

### 5.4 Is the boundary single-valued and monotone?

**In q: yes, provably.** For q' > q, the q-observation can be simulated from the q'-observation by deleting
each herald independently with probability 1 − q/q'. So the optimal LER is non-increasing in q for every L
and p. The decodable region is therefore upward-closed in q, and the boundary is the graph of a
single-valued function q_c(p). The data obey this exactly (§3, item 5).

**In p: not guaranteed.** Increasing p adds errors but also adds heralds, so the problem forbids assuming
monotonicity in p. We tested it directly where it is most delicate: fixed-q scans at q = 0.85, 0.86, 0.87
over p ∈ [0.40, 0.50] (Fig. 4).
- At q = 0.85 and 0.86 the size trend changes sign exactly once, at p = 0.438 and p = 0.466. The LER then
  grows with L all the way to p = ½.
- At q = 0.87 > q\* the LER decreases with L at every p in the range (marginally at p = ½).

Together with q_c(p) increasing through p = 0.44 → 0.46 → 0.48 → 0.50 (0.8506, 0.8587, 0.8629, 0.8685), this
shows:
- q_c(p) is monotone increasing on [p_c(0), ½];
- every fixed-q section with q < q\* has exactly one transition, p_c(q);
- sections with q > q\* have none.

A maximum of q_c(p) inside (0.48, 0.50) shallower than ≈ 0.005 cannot be excluded, but nothing points to one.

![reentrance](figures/reentrance_test.png)

**Figure 4.** Re-entrance test near the corner. The string in each title gives the sign of the LER change
from L = 32 to 64 along p (−: decreasing, +: increasing, 0: within 2σ).

### 5.5 How heralding changes recovery relative to q = 0

**The mechanism.** A parity check cannot see errors that meet in pairs, so every syndrome-free vertex might
hide a chain passing through it. A herald exposes such pass-throughs and triple points (n_v = 2, 3). In the
posterior this has two local effects:
- a heralded vertex *forces* a pass-through or triple point;
- an unheralded vertex *suppresses* one by the factor 1 − q.

As q grows, this removes the entropy of error chains that the decoder cannot distinguish.

**Quantitatively:**
- The threshold rises from 0.1634 to 0.2335 at q = ½ (+43 %) and to 0.299 at q = 0.7 (+83 %). The initial
  slope is dp_c/dq ≈ 0.1.
- The boundary then bends over and reaches p = ½ at q\* ≈ 0.87.
- Below threshold the herald also improves the finite-size LER strongly (Fig. 5b). At L = 48 and
  p = 0.15 the LER is 5.5·10⁻² at q = 0, 5·10⁻³ at q = 0.2 and ≈ 10⁻⁵ at q = 0.4. For q ≥ 0.7 it is at
  the floating-point floor.

**A simple phenomenological rule.** On the whole measured boundary, the density of unwitnessed multi-error
vertices,

  ρ_h = (1 − q) P(n_v ≥ 2) = (1 − q)(3p² − 2p³),

stays between 0.060 and 0.072, while p_c runs from 0.16 to 0.5 and q from 0 to 0.87. It is 0.0714 at
q = 0, dips to 0.060 near p = 0.4, and recovers to 0.066 at p = ½. The rule "decodable iff ρ_h ≲ 0.065 ±
0.006" reproduces the boundary to within ≈ 0.03 in q (the dashed/dotted curves in Fig. 1).

Most of the information the heralds add is thus the location of hidden pass-throughs. Residual ambiguities,
such as which two of three edges are used at a heralded vertex, matter much less.

**Universality.** The scaling collapse gives ν between 1.44 and 1.68 on 16 of 17 lines, with no trend along
the curve. The exception is the weakly constraining corner p-scan at q = 0.86, with 1.79 ± 0.11. This is consistent with a single universality class along the whole line, that of the
q = 0 Nishimori point (ν = 1.49(2) [de Queiroz 2006]).

This is natural: the posterior is always a planar free-fermion (Pfaffian) model with random real weights,
sitting on its own Nishimori manifold (the decoder knows the true p and q). That is the setting of the
Nishimori/class-D multicritical point.

### 5.6 Sub-optimal decoders (decoder dependence)

For comparison we ran two PyMatching decoders (Fig. 9, `results/mwpm_crossings.csv`):
- **Syndrome-only MWPM (q = 0).** Crossings are 0.1604 (8/16), 0.1590 (16/32) and 0.1587 (32/64), so
  p_c^MWPM ≈ 0.159. That is 0.005 below the optimal 0.1634–0.1640, the known MWPM-vs-Nishimori gap.
- **Herald-reweighted MWPM.** This heuristic uses the exact (1−q) per-pass-through factor as an edge weight,
  applies n_v = 3 heralds deterministically, and replaces the prior of edges at heralded s = 0 vertices by
  their marginal 2/3. Its crossings (16/32, at most L = 32) versus the exact ML boundary:

  | fixed | herald-reweighted MWPM | exact ML |
  |---|---|---|
  | q = 0.25 | p ≈ 0.181 | p_c ≈ 0.190 |
  | q = 0.5 | p ≈ 0.223 | p_c = 0.2335 |
  | q = 0.75 | p ≈ 0.303 | p_c ≈ 0.33 |
  | p = ½ | q ≈ 0.899 (still rising with L) | q\* = 0.8685 |

  The heuristic captures most, but not all, of the herald gain, and the loss grows with q.

MWPM can impose parity but not "exactly two incident errors". A MWPM-based phase diagram would therefore
underestimate recoverability, which is why this study uses the exact decoder.
(Numbers: `results/mwpm_crossings.csv`.)

![decoders](figures/decoder_comparison.png)

**Figure 9.** Exact ML versus MWPM decoders.

## 6. Uncertainty budget

- **Statistical.** Bootstrap errors on crossings are 0.0004–0.001 in p and 0.001–0.003 in q, obtained from
  4.8·10⁶ decoded trials in the designed scans (6.0·10⁶ in total).
- **Finite-size.**
  - This is the dominant term. We quantify it by the last observed drift of the doubling-pair crossings,
    0.0012–0.0033 in p on the fixed-q lines, and 0.003–0.011 in q on the fixed-p lines.
  - It also includes the spread between crossing and collapse estimates, ≤ 0.002.
  - Where L = 96 exists (q = 0, p = 0.40, 0.46, 0.50) the drift has nearly stopped: ≤ 0.0013 between
    32/64 and 48/96.
  - The q = 0 benchmark is reproduced to within 0.0006 (crossing) and 0.0003 (collapse).
- **Decoder approximation.** None: the decoder is exactly optimal. Floating-point error is < 10⁻⁷ in the
  log-likelihood ratio wherever it can affect a decision (§3).
- **Unresolved regions.** The grey band in Fig. 1 is ±2σ_tot. It is narrowest at small q (±0.003–0.005 in
  p). It is widest around p ≈ 0.30–0.35 (±0.02 in q), where the crossings still drifted most between 16/32
  and 32/64, and it is ±0.010 in q at p = ½. Everything outside the band is assigned with confidence.

## 7. Limitations

- **Finite sizes.** Phase assignments are finite-size inferences: L ≤ 96, i.e. code distance ≤ 191. The
  small monotone drift near the corner (q-crossings still creeping upward by ≲ 0.002 per doubling) means
  q\* could be a few 10⁻³ above our central value.
- **Scan resolution.** Between the 17 scan lines the curve is an interpolation. The size-trend map confirms
  it on a coarser grid but has lower statistics.
- **Exponent ν.** The effective ν values include corrections to scaling. Our evidence for a single
  universality class is consistency, not a precision measurement.
- **Scope of the model.** Results apply to the stipulated model: i.i.d. edge errors, perfect syndromes,
  heralds with no false positives, and a decoder that knows p and q.
  - A mis-specified decoder (wrong p or q) is outside the optimality argument.
  - Its errors would move the curve for that decoder, not the information-theoretic boundary.
- **Returned correction.** The correction is a valid representative (path construction) of the optimal
  sector, not the single most likely error configuration. This does not affect the success criterion.

## 8. Reproducibility and computational resources

- **Code:** `src/`. Run instructions are in `README.md`. Environment: Python 3.11, numpy 2.1.3,
  scipy 1.14.1, pandas 2.2.3, matplotlib 3.9.2, PyMatching 2.4.0 (comparison only). No compiled
  extensions.
- **Data:** `data/*.jsonl` holds one JSON line per batch (L, p, q, n, hard/soft sums, Δ histogram, seed
  info). `results/` holds the aggregated tables.
- **Figures:** `python3 src/make_figures.py` regenerates all figures and tables from `data/`.
- **Resources:** one workstation, 8 CPU cores (cgroup-limited), ≤ 32 GiB RAM (peak use < 1 GiB per
  process), no GPU. Wall-clock times on 8 cores:

  | run | trials | wall-clock |
  |---|---|---|
  | exploration (two runs) | 0.42 M | 6 min |
  | production | 4.46 M | 84 min |
  | refinement (L = 96 + re-entrance) | 0.36 M | 25 min |
  | full-domain map | 0.79 M | 13 min |
  | MWPM comparison | 1.35 M | 3 min |
  | q = 1 crossing bound (1 core) | 0.10 M | 1 min |

  Total ≈ 2.2 h of 8-core wall-clock, or 17.5 CPU-hours (17.0 of them for the exact decoder). Development,
  tests and benchmarks added about 1 CPU-hour.

### References
- H. Nishimori, M. Ohzeki, J. Phys. Soc. Jpn. 75, 034004 (2006); M. Ohzeki, Phys. Rev. E 79, 021129
  (2009): triangular-lattice ±J RBIM Nishimori point 1 − p_c = 0.1640.
- F. D. de Queiroz, Phys. Rev. B 73, 064410 (2006): ν = 1.49(2) at the triangular/honeycomb Nishimori
  points.
- S. Bravyi, M. Suchara, A. Vargo, Phys. Rev. A 90, 032326 (2014): exact ML decoding of the planar code
  via matchgates.
- L. G. Valiant, SIAM J. Comput. 31, 1229 (2002); J.-Y. Cai, P. Lu, M. Xia (planar Holant/matchgate
  signatures).
- P. W. Kasteleyn, Physica 27, 1209 (1961).
