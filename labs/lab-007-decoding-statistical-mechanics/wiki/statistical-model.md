---
title: Exact spin and current models, and the limits of loop reductions
status: current
updated: 2026-09-14
---

# Exact spin and current models, and the limits of loop reductions

## Summary

The full SU(N) problem is a positive vertex model with shared edge states,
quenched irrep factors and relative binary sectors. It has an exact binary-spin
parameterization coupled to orientation variables. U(1) additionally has an
exact constrained integer-current/height description. A simple loop gas exists
on a restricted all-singlet trivalent record, but its fugacity is **not N**.

## Evidence

### 1. Positive vertex Hamiltonian for arbitrary SU(N)

Use the variables of the [sector formulation](partition-function.md). At β=1,

\[
\mathcal H_s(x)=\sum_a[-\ln\pi_a(x_a)]
+\sum_{v\in M}\left[k_v\ln N-\ln\{\dim R_v M_{L_v(x)}^{R_v}\}\right],
\tag{1}
\]

with infinite energy for a syndrome mismatch or a vanishing multiplicity.
Then Z_h is exactly the sum of exp(−H_s) in sector h. There is no contribution
from unmeasured rough vertices. Retaining x gives local interactions of bounded
arity; eliminating all signs can induce nonlocal activity interactions.
The record-dependent energy is disordered, even when p is spatially uniform.

### 2. Binary spins and sector twists

Let B₀ be a full-column-rank binary basis for ker(A)∩ker(ℓ), and choose a
relative cycle z with Az=0, ℓ(z)=1. Every compatible activity in sector h
is uniquely

\[
e=c_0\oplus hz\oplus B_0b,\qquad b\in\mathbb F_2^r.
\tag{2}
\]

If the graph has no logical bit, omit hz. With σ_i=(−1)^{b_i}, define
τ_a^h=(−1)^{c₀,a+h z_a}. Then

\[
(-1)^{e_a}=\tau_a^h\prod_i\sigma_i^{(B_0)_{ai}}.
\tag{3}
\]

Substitute (2) into (1) and sum one orientation per active edge. This is an
exact spin representation with nonnegative weights. For SU(2), orientations
cancel entirely; its partition function reduces to

\[
Z_h=\sum_b\prod_a p_a^{e_a}(1-p_a)^{1-e_a}
\prod_{v\in M}f_{R_v}(k_v).
\tag{4}
\]

The prior alone yields couplings K_a=½ ln[(1−p_a)/p_a] multiplying the spin
products in (3), up to a sector-independent constant. The f factors remain.
For a planar cellulation, face boundaries plus suitable rough-boundary
relative generators give a geometric version of these spins. If redundant
face generators are used, divide by their kernel multiplicity; an independent
basis avoids this issue. A generic algebraic basis need not be local.
Thus (4) is **not** a proof of a nearest-neighbor random-bond Ising model:
local fusion factors produce extra interactions and hard constraints.

The exact SU(2) weights illustrate what geometry adds. R is labeled by its
dimension 2j+1; omitted entries are zero.

| Active degree k | Nonzero irrep probabilities |
| --- | --- |
| 0 | R=1: 1 |
| 1 | R=2: 1 |
| 2 | R=1: 1/4; R=3: 3/4 |
| 3 | R=2: 1/2; R=4: 1/2 |
| 4 | R=1: 1/8; R=3: 9/16; R=5: 5/16 |

The degree-four singlet weight is 1/8, not the product (1/4)² for a specified
pair of independent singlets. Fusion multiplicity remains observable even
when conjugacy disappears. Trivalent and four-valent graphs therefore have
different microscopic interactions without requiring different universality.

### 3. U(1): exact bounded currents and relative heights

Write j=x. The full charge record imposes Dj=q exactly. Since j mod 2=|j| mod 2,
m=q mod 2 and the binary syndrome is redundant for this group. Define

\[
w_a(j)=\begin{cases}1-p_a&j=0,\\p_a/2&j=\pm1,\\0&\text{otherwise},\end{cases}
\qquad
Z_h(q)=\sum_{j:\,Dj=q}\prod_a w_a(j_a)
\mathbf1\{\ell((j-j_0)\bmod2)=h\}.
\tag{5}
\]

Here j₀ is any feasible reference current and c₀=j₀ mod 2. The directed case
uses w(+1)=p, w(−1)=0. Changing to an arbitrary binary c₀ only relabels h.
Choose an integral basis C for ker_Z(D); for graph incidence one can obtain
it from fundamental cycles after identifying all unmeasured boundary vertices
with an auxiliary root. Then j=j₀+C n, n∈Z^r, parametrizes each feasible
current exactly once. The single-edge potential is

\[
V_a(t)=\begin{cases}
0&t=0,\\\ln[2(1-p_a)/p_a]&t=\pm1,\\+\infty&\text{otherwise}.
\end{cases}
\tag{6}
\]

Thus Z_h=(∏_a(1−p_a))∑_n exp[−∑_a V_a(j₀,a+(C n)_a)] with the sector
parity restriction. In a planar interior, contractible generators are dual
height differences. Rough-boundary generators allow endpoints at B; deleting
these generators would delete the logical sectors. On a torus, extra integer
winding generators must be included. Although j is bounded, n is best regarded
as an integer field constrained by the finite support of j₀+C n.

This is a quenched constrained height/current model, not a quadratic Gaussian
height action. Its logical sectors sum all current windings of the same parity.
That differs from selecting a single integer winding in a rotor model.
An open rough-boundary patch also does not have the torus winding/helicity
observable without an explicitly registered geometry change.

The exact compact Fourier identity for the hidden current evidence is

\[
Z(q)=\int\prod_{v\in M}\frac{d\theta_v}{2\pi}
 e^{-i\sum_vq_v\theta_v}\prod_{a=(u,v)}
 \left[1-p_a+p_a\cos(\theta_v-\theta_u)\right],
\tag{7}
\]

where θ=0 at unmeasured vertices. Sector projection inserts (−1)^{λℓ_a}
in the active cosine term, then takes the two-point Fourier sum over λ,
including the reference sign. For q≠0 the charge insertion is complex; for
p>1/2 even the untwisted edge factor can be negative. Consequently this exact
integral does not by itself define a clean positive XY magnet.

### 4. SU(N) character representation, with the projection retained

Character orthogonality gives

\[
M_L^R=\int_{SU(N)}dg\,\overline{\chi_R(g)}\prod_{\ell\in L}\chi_\ell(g).
\tag{8}
\]

This follows by decomposing the product character and taking its inner product
with χ_R. Introduce η_v∈{±1} to project m_v and λ∈{0,1} to project h.
For measured vertices let U_v=χ_F(g_v), Ū_v=χ_F̄(g_v); at unmeasured
vertices set both symbols to 1 (not χ_F(identity)=N). Set η=1 there and
b_a=number of measured endpoints. Then the hidden edge factor is

\[
K_a=1-p_a+\frac{p_a}{2N^{b_a}}(-1)^{\lambda\ell_a}\eta_u\eta_v
\left[\bar U_u U_v+U_u\bar U_v\right].
\tag{9}
\]

The exact sector integral is

\[
Z_h=\frac{\prod_{v\in M}\dim R_v}{2^{|M|+1}}
\sum_{\lambda=0}^1(-1)^{\lambda(h+\ell(c_0))}
\sum_{\{\eta\}}\prod_{v\in M}\eta_v^{m_v}
\int\prod_{v\in M}\left[dg_v\,\overline{\chi_{R_v}(g_v)}\right]
\prod_a K_a.
\tag{10}
\]

For directed edges replace the bracket/2 by Ū_u U_v. Expanding every K_a,
performing the parity sums, then applying (8) recovers the original positive
vertex sum term by term. Character insertions and Fourier projectors can have
signs or phases; (10) is not an ordinary positive ferromagnetic SU(N) spin model.
For SU(2), χ_F=χ_F̄ reproduces the orientation quotient immediately.
The general integral is proved algebraically; the executable checks use the
positive vertex and binary/current representations, not numerical Haar integration.

### 5. A derived loop gas in a restricted observation sector

Take a trivalent graph, the special record m_v=0 and R_v=singlet everywhere
measured, and degree-one unmeasured rough endpoints. The occupied graph then
consists of disjoint loops and rough-to-rough paths: measured degree is 0 or 2.
For SU(2), each occupied degree-two site contributes 1/4, with no orientation
constraint and no per-loop multiplicity. On a closed graph,

\[
Z_{\rm singlet}^{SU(2)}=(1-p)^{|E|}
\sum_{e\ \rm loops}\left[\frac{p}{4(1-p)}\right]^{|e|}.
\tag{11}
\]

For SU(N), N≥3, a degree-two singlet requires opposite leaves. Signs must
therefore circulate consistently around each occupied loop. There are exactly
two choices per loop, each with weight 2^{−|e|} from the edge prior, giving

\[
Z_{\rm singlet}^{SU(N),hidden}=(1-p)^{|E|}
\sum_{e\ \rm loops}2^{C(e)}
\left[\frac{p}{2N^2(1-p)}\right]^{|e|},\qquad N\ge3.
\tag{12}
\]

Here C counts loop components. U(1) at q=0 has the same expression with N=1
in the edge tension. Thus in this restricted trivalent ensemble the loop
fugacity is 1 for SU(2) and 2 for complex fundamentals; N enters the tension.
This is an explicit derivation, not an assignment of dim(F) as fugacity.
Directed complex-fundamental loops must follow the stored arrows and carry
no twofold orientation sum.

For a rough-to-rough path of length l, only l−1 vertices are measured. Its
factor is [p/(1−p)]^l 4^{−(l−1)} for SU(2), and
2[p/(2(1−p))]^l N^{−2(l−1)} for hidden N≥3. Boundary weights are therefore
different from closed-loop weights. Sector h selects the parity of paths
joining opposite rough sides.

This simplification fails for typical nontrivial records and for unqualified
four-leg intersections. At a balanced four-leg SU(3) singlet the factor is
2/81, so occupancy alone requires a local intersection weight and a correlated
orientation sum. SU(4) also allows a four-fundamental singlet with divergence
±4. At trivalent SU(3), an odd-syndrome singlet allows divergence ±3 and
prevents the divergence-free reduction, as shown in [conjugacy](conjugacy.md).
These facts obstruct importing the restricted loop gas as the typical posterior.

### Verification and source transfer

The [exact enumeration](../results/exact-model-checks-2026-09-14.json) verifies
870 binary-basis sector contractions, 16,764 U(1) record/current equalities,
all five SU(2) joint-law quotients, and the four-edge singlet-loop weights.
The [independent supplement](../results/mapping-supplement-2026-09-14.json)
reconstructs 7,817 currents using an integral fundamental-cycle basis.
Independent SU(3) Dynkin-label tensor recursion and SU(2) spin addition agree
with all 45 parent local fusion distributions through degree four.

[Sala–Verresen](https://arxiv.org/html/2409.12230v2) derives loop weights from
quantum-state overlaps; our factors are classical conditional measurement
probabilities. [Temkin et al.](https://arxiv.org/html/2512.22119v1) uses
unbounded Gaussian integer errors, periodic geometry, and integer winding
sectors. Here the current support is {−1,0,1}, the boundary is open, and the
score is binary. The current/height construction transfers; their transition
location or universal jump does not. See [the source audit](source-context.md).

## Status

Exact positive vertex model, binary-spin parameterization, U(1) constrained
height/current model, and restricted trivalent loop reduction established.
A typical-record continuum action, stiffness, and transition remain open.

## Related pages

- [Sector normalization](partition-function.md)
- [Conjugacy and SU(3) source obstruction](conjugacy.md)
- [Discriminating predictions](predictions.md)
