---
title: Thermodynamic limits and a robust correctable bias interval
status: current
updated: 2026-09-20
---

# Thermodynamic limits and a robust correctable bias interval

## Summary

With p,q fixed as L grows, there is a nonzero interval of directional biases
on the canonical honeycomb for which optimal LER vanishes exponentially,
uniformly over every p in [0,1]. Thus the all-p directed result is robust to
a small fixed reverse-direction probability, rather than confined to q=1.
We also give sufficient correctability criteria for general patch families
and prove an averaged bulk free-energy-density limit under periodic bulk
arrows. The latter does not determine the logical-sector information.

All statements use independent bounded currents, known arrows, perfect
interior integer charge, rough left/right boundaries and binary logical
parity. They do not apply unchanged to noisy measurements, integer winding
recovery or a specified practical decoder.

## Evidence

### General exponential correctability criterion

Let b_L be the number of rough vertices and d_L the shortest opposite-side
path length. Assume b_L grows at most polynomially and d_L>=c L with c>0.
Suppose simple paths of length n from a vertex are bounded by C_eta eta^n.
On a regular infinite lattice with connective constant mu, any eta>mu has
such a bound. A degree-Delta bound can instead use Delta*(Delta-1)^(n-1).

Put t=sqrt(q(1-q)). The [connected-current proof](connected-current-defects.md)
gives, for 0<q<1,

\[
p\leq p_{\rm cvx}(q):=\frac1{1+t},\qquad
\gamma(p,q)=\sqrt{p(1-p)(1+2t)}.
\]

The first condition is exactly (1-p)^2>=p^2 q(1-q), not an optional
approximation. Each allowed improving unit-path event has probability at
most the product of its edge affinities. Summing both path orientations
therefore gives, when eta gamma<1,

\[
R_{*,L}\leq\min\left\{\frac12,
2b_L C_\eta\frac{(\eta\gamma)^{d_L}}{1-\eta\gamma}\right\}.
\]

Consequently mu gamma<1 and convexity are sufficient for exponential
correctability. At q=0,1 the supported binary current cost is affine and
the endpoint proof applies separately. This criterion is independent of the
assigned arrows, since the edge affinity of a unit shift is orientation
independent. For spatially varying priors the same proof uses edgewise
convexity and the weighted path sum; a uniform affinity bound is sufficient.
The criterion gives a region of proof, not the actual phase boundary.

### A second criterion valid at every directional bias

The activity x_e=|j_e| is Bernoulli(p), independent of q, and j_e mod 2=x_e.
The full observed charge supplies its binary syndrome. If p>1/2, subtract
the known all-active edge pattern and decode y_e=1-x_e instead. This known
pattern also has a known logical parity. The residual activity is
Bernoulli(r), where r=min(p,1-p).

For a minimum-weight binary correction, failure implies a simple logical
path with at least half its edges in the true residual error. Its probability
is at most beta^n, with

\[
\beta(p)=2\sqrt{r(1-r)}=2\sqrt{p(1-p)}.
\]

The path counting bound therefore proves exponential Bayes correctability
whenever mu beta<1, for every q and every fixed arrow field. The admissible
binary rule only discards information; Bayes with full charges is at least
as accurate. This is the standard minimum-chain/Peierls reasoning adapted
to the present activity score; compare
[Dennis et al., Section V](https://arxiv.org/abs/quant-ph/0110143).

For honeycomb this includes p<.07955179 and p>.92044821 at every q.
Using only the degree bound on square includes p<.02859548 and p>.97140452.
The current criterion is stronger in part of the low-p region. These numbers
are sufficient bounds, not threshold estimates. At p=1 the activity pattern
is known exactly, so binary logical risk is zero even though current signs
and charge records can remain random. Hence monotonicity in p on the entire
interval [0,1] must not be presumed for this score.

### An open all-p correctable interval on honeycomb

The exact honeycomb constant is mu=sqrt(2+sqrt(2)), proved by
[Duminil-Copin and Smirnov](https://arxiv.org/abs/1007.0575).
Define

\[
t_0=\frac{3-2\sqrt2}{2},\qquad
q_* =\frac{1+\sqrt{1-4t_0^2}}2
=0.9925857155\ldots.
\]

For every fixed q>q_* (or q<1-q_*), there are constants C(q),k(q)>0
independent of p,L such that, for the canonical honeycomb family,

\[
\boxed{\sup_{0\leq p\leq1}R_{*,L}(p,q)
\leq C(q)L e^{-k(q)L}\longrightarrow0.}
\]

Here is the join between the two criteria; omitting it would incorrectly
apply ternary convexity at high p. Take t=sqrt(q(1-q))<t_0. For
p<=p_cvx, the maximum current affinity is

\[
g_1=\frac{\sqrt{1+2t}}2,\qquad \mu g_1<1,
\]

since mu^2(1+2t_0)=4. For p>=p_cvx>1/2, beta(p) decreases, so its maximum
on that interval is

\[
g_2=\frac{2\sqrt t}{1+t}.
\]

It also obeys mu g_2<1. The left side increases with t<1, and at t=t_0
the strict margin is exactly

\[
(1+t_0)^2-4\mu^2t_0=t_0^2
=\frac{17-12\sqrt2}{4}>0.
\]

Choose one eta between mu and 1/max(g_1,g_2). Both path bounds now have
a common ratio rho=eta max(g_1,g_2)<1, uniformly in p. The canonical
geometry has b_L=4L+2 and d_L>=(3L-1)/2, proving the boxed result. These
geometric inequalities follow from the two zigzag rough sides: their
horizontal separation is (3L-1)/2 and every edge changes x by at most one.
Isolated rough vertices only enlarge the harmless boundary prefactor.

The interval is strict: this proof does not include q=q_*. The endpoints
q=0,1 use the preceding binary-current theorem. Constants can be chosen
uniformly on any closed bias subinterval lying strictly inside the proved
window. No gradient-arrow or complex-gauge assumption is needed.

This excludes a loss-of-correctability transition as p varies in that
honeycomb window for optimal binary inference. It does not prove analyticity
of every auxiliary partition function. No corresponding all-p square result
follows: its degree/path-growth criterion already fails at p=1/2,q=1.

### A precise thermodynamic order parameter

For each finite patch let Delta F=log(Z_0/Z_1), using infinite absolute gap
when only one sector is supported. The exact Bayes functional gives

\[
\Pr(|\Delta F|\leq K)\leq(1+e^K)R_{*,L},
\qquad
R_{*,L}\leq\frac12\Pr(|\Delta F|\leq K)+\frac1{1+e^K}.
\]

Thus R_*->0 if and only if |Delta F| diverges in probability under the
physical charge-record distribution. If R_*<=C L^s exp(-k L), then for
every 0<a<k,

\[
\Pr(|\Delta F|\leq aL)
\leq2CL^s e^{-(k-a)L}.
\]

In the certified region, the two logical sectors therefore acquire a
free-energy separation at least linear in size with probability tending
to one. This is a positive lower bound on the logical interface cost in
probability; it does not assert existence of a limiting mean interface
tension, which can be problematic when one sector has zero weight.

Writing S for the logical bit and h_2 for binary entropy in natural units,

\[
2\log2\,R_{*,L}\leq H(S\mid Q)\leq h_2(R_{*,L}).
\]

The lower bound is the chord bound on binary entropy; the upper bound is
concavity applied to the conditional Bayes risk. Hence vanishing conditional
logical entropy is an equivalent thermodynamic correctability criterion.
This complements the earlier equivalent M_2->1 criterion.

### What bulk free-energy limit can actually be proved?

Assume a periodic bulk arrow pattern and regular planar boxes (a finite unit
cell is allowed). The infinite bulk charge field is a stationary finite-
alphabet function of independent edge currents. Its entropy density exists:

\[
h_Q=\lim_{L\to\infty}\frac{H(Q_{\Lambda_L})}{|\Lambda_L|}.
\]

An elementary proof suffices for this averaged statement. Tile a large box
by translates of any fixed m-by-m block. Entropy subadditivity bounds the
large-box entropy by the sum of block entropies plus O(mL) times the log
alphabet size. Stationarity makes every translated block entropy the same.
Taking L->infinity gives a limsup bounded by each normalized block entropy;
the infimum of those block entropies bounds the liminf. They coincide.
For periodic arrows, tile by unit cells and then convert to per-vertex units.

The actual rough patch and this bulk box can be coupled to have identical
charges away from O(L) boundary sites. By the entropy chain rule, modifying
or removing these finite-alphabet sites changes total entropy by O(L), so
the same density limit holds for the measured patch record. The general
existence claim is not extended to arbitrary nonstationary arrow patterns.

Because the normalized evidence partition sum is Z_0(Q)+Z_1(Q)=P(Q),
its disorder-averaged free energy is exactly H(Q). Moreover,

\[
0\leq\mathbb E[-\log\max_s Z_s(Q)]-H(Q)\leq\log2,
\]
\[
\mathbb E_{Q,S}[-\log Z_S(Q)]-H(Q)=H(S\mid Q)\leq\log2.
\]

The dominant-sector and posterior-selected-sector free-energy densities
therefore have the same limit h_Q, regardless of whether LER vanishes.
The first statement even follows pointwise from P(Q)/2<=max Z_s<=P(Q).
These are positive sector sums; the signed twist A_1 is not logged here.
An unsupported fixed sector can have log Z_s=-infinity, so no blanket
finite limit for each fixed-sector free energy is asserted.

If the real current Hamiltonian is normalized instead by factoring out
(1-p)^E, its averaged free-energy density differs by the known term
(E/|Lambda|) log(1-p) at fixed p<1. This normalization does not restore the
lost logical information. We prove an averaged density limit, not its
explicit value, differentiability, or almost-sure convergence.

### Checks and remaining boundary

The [registered study](../manifests/thermodynamic-limits-2026-09-20.json)
and [script](../scripts/check_thermodynamic_limits.py) verify the radical
identities exactly in Q(sqrt(2)); positivity reduces to 17^2>2*12^2.
All 6,561 square L3 current states are included in each of 28 parameter
controls, covering high-p nonconvex priors and deterministic endpoints.
The parity-complement rule has no missing path witnesses, is independent
of q, and never beats full-charge Bayes. Entropy/free-energy identities and
gap-probability inequalities pass. Canonical honeycomb L=3,4,5,7,9,11
geometry checks also pass. These finite checks support the algebra and
implementation; the analytic path-growth and entropy arguments establish
the limits. No decoder samples or scaling fits were added.

The [result](../results/thermodynamic-limits-2026-09-20.json) includes all
controls, margins, exact binary risks and source hashes. The remaining
question is necessity outside the proved region, especially the square
directed midpoint. Failure of a sufficient criterion is not evidence of
uncorrectability, a transition or a CFT.

## Status

General sufficient criteria, the robust all-p honeycomb interval, the
gap/entropy characterization and the averaged bulk-density limit are proved
under the stated assumptions. A full phase classification and general
square thermodynamic LER remain unresolved. Fixed-size crossover expansions
and failed finite contractions are retained as separate evidence.

## Related pages

- [Connected-current proof](connected-current-defects.md)
- [Sector free energies and LER](sector-predictions.md)
- [Complex weights and the CFT question](complex-weights-and-cft.md)
- [Fixed-size directional crossover](directional-crossover.md)
- [Research plan](../PLAN.md)
