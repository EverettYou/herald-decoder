---
title: Connected current defects and rigorous LER bounds
status: current
updated: 2026-09-19
---

# Connected current defects and rigorous LER bounds

## Summary

A connected-defect argument now bounds the physical Bayes LER directly by
a positive sum over simple paths. It preserves the full observed charge,
rough boundaries and binary logical score, and needs no replica continuation.
It improves finite square bounds at biased noise and proves a stronger
asymptotic statement on the honeycomb: **fully directional noise is optimally
correctable at every physical p**, with exponentially vanishing LER as the
rough boundaries separate. This is a statement about the stipulated classical
charge-observation model, not every auxiliary statistical-mechanics phase.

The square all-p question and the fair/intermediate moderate-p curve remain
open. The earlier Gaussian calibration and contraction rejections remain
valid. This is a new theorem preserving the target, rather than another
compression refinement or a fit to decoder data.

## Evidence

### From posterior failure to a single connected path

Write a=1-p, b=pq, c=p(1-q), and w(0)=a, w(+1)=b, w(-1)=c.
The current cost is C(j)=-sum_e log w(j_e). For interior q it is discretely
convex precisely when

\[
a^2\geq bc.
\]

Let j be the true current and jhat a maximum-weight current having the same
measured integer charge. This is an admissible rule depending only on Q and
the known prior. Its logical risk bounds Bayes risk from above; we do not
equate maximum-current inference with maximum-sector inference.

If their logical parities differ, delta=jhat-j has zero divergence at every
measured vertex and odd net flux across the logical cut. Decompose this
integer flow into conformal unit paths and cycles: each component follows
the sign of delta, with multiplicity where |delta_e|=2. At least one simple
path P joins opposite rough boundaries. Closed cycles and same-side boundary
paths have even cut parity. Write s_P for this path's signed unit current.

Both j+s_P and jhat-s_P are supported currents with the required interior
charge. Discrete convexity and the optimality of jhat give

\[
C(j+s_P)-C(j)
\leq C(\widehat j)-C(\widehat j-s_P)\leq0.
\]

Thus logical failure implies at least one **allowed unit path shift whose
likelihood is no smaller than the true current's**. The first inequality
is an edgewise monotonicity of discrete cost increments; it also covers
edges where delta has magnitude two. This is the missing interface from
the physical charge-record problem to a connected path sum.

For q=1 the supported alphabet is {0,1}; its cost is affine, so this proof
works for every 0<p<1 without the ternary convexity condition. Endpoints
p=0,1 are deterministic and have zero LER. Reversing every current handles
q=0 as well.

The path-witness strategy is related to the self-avoiding error-chain bound
in [Dennis et al., Section V](https://arxiv.org/abs/quant-ph/0110143).
The discrete-convex current argument and ternary path probabilities above
are derived here for this channel. Convex network-flow methods provide a
related optimization framework, but their algorithmic theorems alone do not
give our physical LER bound.
[Convex-cost flow reference](https://arxiv.org/abs/1610.04012).

### Exact physical probability of a fixed path witness

Suppose the oriented unit shift has F forward and B backward steps relative
to the assigned edge arrows. On forward steps the allowed true values are
-1 and 0; on backward steps they are 0 and +1. Let u count forward steps
with true value -1, and v count backward steps with true value +1. Their
total physical probability is

\[
\binom Fu\binom Bv c^u b^v a^{F+B-u-v}.
\]

The logarithmic likelihood gain is

\[
\Lambda_{F,B}(u,v)
=F\log(b/a)+B\log(c/a)+(u+v)\log[a^2/(bc)].
\]

Therefore the exact witness probability is the finite positive sum

\[
\Psi_{F,B}(p,q)=\sum_{u=0}^{F}\sum_{v=0}^{B}
 \binom Fu\binom Bv c^u b^v a^{F+B-u-v}
 \mathbf1\{\Lambda_{F,B}(u,v)\geq0\}.
\]

All currents off this one path sum to probability one. Summing over both
orientations of every simple left-to-right geometric path yields

\[
\boxed{\mathcal R_*
\leq\min\!\left\{\frac12,
 \sum_{P:L\to R}[\Psi_{F(P),B(P)}+\Psi_{B(P),F(P)}]\right\}.}
\]

Overlapping witnesses can make this bound loose. It is an upper bound on
the physical sector-partition LER, not an equality or a replacement prior.
Unlike the earlier unrestricted two-current relaxation, it does not count
all background cycles and two-current configurations: convexity extracts
one necessary connected witness, and the unobserved background is integrated
with its original normalized probability.

### Exact overlap correction by a frozen witness forest

For any forest T on events E_i, the pointwise inequality

\[
\mathbf 1_{\cup_iE_i}\leq\sum_i\mathbf 1_{E_i}
-\sum_{(i,j)\in T}\mathbf 1_{E_i\cap E_j}
\]

holds: if k vertices are active, their induced forest has at most k-1 edges.
This retains the preceding physical-LER inequality while subtracting overlap.

For signed paths r,s, define a positive bivariate current-count polynomial

\[
G_{rs}(x,y)=\prod_e\sum_{j\ {\rm compatible}}
\pi(j)x^{[j\ {\rm opposes}\ \delta_r]}
y^{[j\ {\rm opposes}\ \delta_s]}.
\]

Summing coefficients whose two exact likelihood ratios are at least one gives
P(E_r intersection E_s). Shared edges traversed in opposite directions are
handled by their reduced compatible alphabet, rather than discarded. The L5
forest is frozen geometrically before evaluating p,q: within each sign it uses
lexicographic path order and attaches to the earlier path with the most
same-directed shared edges, then the most total shared edges.

| p | q | Path sum | Tree-corrected bound | Strongest prior upper | New strongest upper |
| --- | --- | --- | --- | --- | --- |
| .05 | .50 | .08358071 | .08130492 | .03683883 | .03683883 |
| .05 | .75 | .02620812 | .02560125 | .02620812 | .02560125 |
| .08 | .50 | .29466738 | .28316128 | .13835664 | .13835664 |
| .08 | .75 | .10883990 | .10539805 | .10883990 | .10539805 |

Thus the correction improves every path bound by 2.32%--3.90%, and promotes
the strongest certificate in both q=.75 cells. At fair noise the activity
certificate remains stronger, so pairwise overlap does not solve that band.
The [exact result](../results/connected-defect-overlap-2026-09-19.json) records
all 3,488 intersections. Five cells on L3, including the all-tie prior, give
765 exact pair/cell comparisons with zero discrepancy; opposite shared-edge
directions are explicitly covered. No physical records were sampled.

### A statistical-mechanics bound with an explicit line weight

For either orientation of one edge, the half-Chernoff affinity is

\[
\gamma(p,q)=\sqrt a(\sqrt b+\sqrt c)
=\sqrt{p(1-p)}[\sqrt q+\sqrt{1-q}].
\]

On the event that a path shift improves the likelihood,
w(j)<=sqrt(w(j)w(j+s_P)). Summing independently along the path proves
Psi_(F,B)<=gamma^(F+B). The resulting positive self-avoiding-path partition
sum dominates LER. The path cost is -log gamma, competing with path entropy.
At fixed p, going from fair to fully directional noise lowers gamma by
sqrt(2), increasing this **bounding model's** cost per step by log(2)/2.
This cost is not an asserted renormalized stiffness of the original rotor.

For the canonical square, d=L-1 and each rough starting vertex has one
incident edge. There are at most 2L*3^(n-1) oriented length-n candidates.
Whenever 3 gamma<1,

\[
\boxed{\mathcal R_{*,L}
\leq\min\!\left\{\frac12,
 \frac{2L}{3}\frac{(3\gamma)^{L-1}}{1-3\gamma}\right\}.}
\]

This gives a sufficient exponential-correctability region. On the low-p
branch its endpoints are:

| Direction bias q | Sufficient p below |
| --- | --- |
| .50 | .05904145 |
| .75 | .06358765 |
| .97 | .09115544 |
| 1 | .12732200 |

These are rigorous lower bounds on the extent of a correctable low-noise
region, not estimates of the actual transition. Failure of 3 gamma<1 says
nothing about whether decoding fails there. The convexity condition is
satisfied throughout these displayed regions.

### A directed square refinement retaining the full path geometry

For q=1,p<=1/2 choose, among maximum-weight currents, one minimizing the
total current F_R entering the right rough boundary. For p<1/2 this means
minimizing occupied-edge count N first and F_R second; at p=1/2 minimize
F_R. This uses only observable Q and a fixed tie rule.

Stored square arrows are the gradient of x+y. Every left-to-right unit path
has occupied-count change d+y_end-y_start>=0 and increases F_R by one.
If such a component existed in jhat-j, removing it from jhat would improve
N or its F_R tie break, contradicting optimality. Hence a failed logical
decision has a right-to-left witness.

Count geometric paths in the left-to-right orientation, with F positive and
B negative steps. Then F>=d and F>=B. The reversed path is allowed exactly
when its F negative steps have true current one and its B positive steps
have true current zero. Its physical probability is p^F(1-p)^B. Thus

\[
\boxed{\mathcal R_{*,L}(p,1)\leq
\min\{1/2,\ U_L(p)\},\qquad
U_L(p)=\sum_{F,B}N_L(F,B)p^F(1-p)^B.}
\]

This is a finite positive path partition function with no disorder sampling.
Its p^d coefficient is binom(2d,d), agreeing with the previously proved
exact directed dilute coefficient. Paths with F=d use only rightward and
negative-y steps in the counted orientation; counting their placements
between the rough boundaries gives that coefficient. The finite-p upper
bound does not truncate at that leading term.

The complete path counts are 9, 80 and 1,745 for L=3,4,5. Exact enumeration
of these paths takes milliseconds and is distinct from enumerating every
noise configuration or syndrome.

### An exact two-dimensional patch curve

For the actual L=3 square at q=1, all 256 binary currents give 64 distinct
charge records. Counting each sector by occupied-edge number yields
Z_h(Q)=(1-p)^8 P_h(Q,t), where t=p/(1-p) and each P_h is an integer polynomial.
The sign of P_0-P_1 determines the smaller sector. Exact rational Bernstein
coefficients certify its sign on 0<=t<=1/4 for every record. Summing the
selected smaller sectors gives the **exact**, untruncated curve

\[
\boxed{\mathrm{LER}_{*,L=3}(p,1)
=6p^2-12p^3+13p^4-14p^5+7p^6+2p^7-2p^8,}
\]
\[
0\leq p\leq0.2.
\]

Explicitly, if P_0-P_1=sum_j d_j t^j, substitute t=x/4. Its degree-eight
Bernstein coefficients are sum_(j<=k) d_j 4^(-j) binom(k,j)/binom(8,j).
Each record has coefficients of one sign, certifying that sign for 0<=x<=1.
The total selected activity counts are (0,0,6,24,43,38,13,2,0), and their
sum against p^n(1-p)^(8-n) gives the displayed polynomial.

For example, the exact values are .04916718 at p=.1 and .16078848 at p=.2.
The leading term 6p^2 alone would give .06 and .24. This is a finite
two-dimensional partition-function calculation with all records included,
not a fitted approximation. Current complementation j->1-j shifts Q and
relabels parity, so replacing p by 1-p also gives the p>=.8 branch.

The first attempted sign certificate on the whole interval p<=.5 failed
for 17 record differences. The smaller interval was registered before its
check and all 64 certificates then passed. We retain the failed full-domain
attempt; no extrapolation of this polynomial through p=.5 is claimed.
The asymptotic honeycomb theorem is independent of this finite square result.
L3 is an exact optimal-inference control, not a replacement for the parent's
larger practical-decoder patches or a threshold extrapolation.

### Finite square certificates at p=.08

Intersect the new upper bounds with the frozen positive-activity intervals:

| q | Activity interval | Path upper |
| --- | --- | --- |
| .50 | [.02986755, .13835664] | .29466738 |
| .75 | [.01657508, .12506417] | .10883990 |
| .97 | [.00555390, .11404299] | .03409676 |
| 1 | [.00027766, .10876675] | .00285144 |

The fair cell keeps its existing upper bound; the new bound is looser there.
At q=.75,.97,1 the interval widths shrink by 14.95%, 73.69%, and 97.63%
relative to the frozen activity certificate. These comparisons are with
that explicitly named baseline; prior branch-and-bound methods had already
improved near-directed cells. The full result contains all 72 L,p,q cells,
including p=.30 where bounds can be trivial. There is no fitted curve or
claim that the remaining fair/moderate-noise band has been solved.
Displayed decimals are rounded; the positive finite sums define the bounds.

### Honeycomb theorem: fully directional noise remains correctable

For the infinite honeycomb graph, the self-avoiding-walk growth constant is

\[
\mu_{\rm hex}=\sqrt{2+\sqrt2}.
\]

This is the rigorous result of
[Duminil-Copin and Smirnov](https://arxiv.org/abs/1007.0575).
The defining growth limit implies that for every lambda>mu_hex there is a
finite constant C_lambda with c_n<=C_lambda lambda^n, where c_n counts walks
from a fixed vertex. Finite retained honeycomb patches have no more paths
than the infinite lattice.

Let b_L count rough vertices and d_L be their opposite-side separation.
The connected-witness theorem implies, whenever lambda gamma<1,

\[
\mathcal R_{*,L}\leq
b_L C_\lambda\frac{(\lambda\gamma)^{d_L}}{1-\lambda\gamma}.
\]

For fully directional noise, at every p in [0,1],

\[
\mu_{\rm hex}\gamma(p,1)
\leq\frac{\sqrt{2+\sqrt2}}2
=\cos(\pi/8)<1.
\]

Choose any fixed lambda strictly between mu_hex and two. For canonical
patches b_L=4L+2 and the coordinate separation already gives
d_L>=(3L-1)/2. Hence

\[
\boxed{\sup_{0\leq p\leq1}\mathrm{LER}_{*,L}(p,1)
\longrightarrow0\quad\text{exponentially in }L.}
\]

The bound holds for any fixed assigned arrow field, including the parent's
stored arrows and the bipartite control, because the edge affinity is
independent of the path's local orientation. It is an analytic all-size
result; the finite geometry checks do not establish the limit by a fit.

**Scope:** perfect interior integer-charge observations, independent bounded
binary directed currents, the inherited rough boundaries and binary logical
parity, and optimal inference. This excludes a loss-of-correctability
transition as p varies in this honeycomb channel. It neither proves that
every auxiliary partition function is nonsingular nor guarantees that the
parent BP-MWPM decoder attains the optimal result. No all-p square theorem
follows: its path growth is larger, and the square result above is only a
sufficient low-noise region.

The literature proof of mu_hex uses a parafermionic observable with a
complex winding phase. That gives a concrete use of an exactly solved
statistical-mechanics result here. Our connection is an inequality to that
path model, not an identification of the original decoder's critical CFT.

### Independent validation and provenance

The [registered calculation](../manifests/connected-current-defects-2026-09-19.json)
and [reproducible script](../scripts/check_connected_current_defects.py)
check the theorem before using its bounds:

- Every ternary state on square L3, across the registered grid and directed
  p=.5,.7 controls. Integer prior weights make MAP comparisons and ties exact.
  Every logically wrong MAP decision has the required unit-path witness:
  120,146 supported state/channel cases pass, including 59,904 failures.
- A trivalent cycle with rough tails checks the general directed argument
  at p=.1,.3,.5,.7,.9; no gradient-arrow assumption is used there.
- Explicit current enumeration on paths of length up to six verifies the
  binomial witness formula and q-reflection symmetry.
- Complete square path tables reproduce the directed leading coefficients
  6,20,70 at L=3,4,5 and obey the independent half-Chernoff upper bound.
- All 64 charge-sector sign certificates for the L3 directed polynomial
  use exact rational arithmetic; its registered points agree with the
  independent complete-state Bayes calculation.
- Canonical honeycomb L=3,5,7,9,11 has degree at most three, linearly separated
  rough sides, and a logical cut separating them. The graph retains isolated
  rough vertices after edge deletion; these carry no currents. The first
  geometry-check attempt incorrectly indexed unreachable vertices and was
  repaired to treat their distance as infinite, without altering the model.

The [machine-readable result](../results/connected-current-defects-2026-09-19.json)
contains complete path counts, finite predictions, exact-gate outcomes,
geometry checks and input hashes. No production decoder samples were added.

### A rigorous floor on the witness envelope

Let U_full be the probability that at least one of the existing allowed,
improving-or-equal simple logical-path shifts exists. The preceding theorem
gives R_*<=U_full. Correcting all overlaps computes U_full; it does not make
that event equivalent to a Bayes failure.

Retain two disjoint two-row horizontal strips and the remaining one-row
strip inside the L5 square. A logical path in any strip remains a valid
charge-preserving path of the full graph. Let U_2 and U_1 be their exact
witness-union probabilities. Their edge sets are disjoint, so independence
of the physical edge priors gives

\[
U_{\rm full}\geq U_{\rm floor}
=1-(1-U_2)^2(1-U_1).
\]

This is a **lower bound on a witness-event envelope, not on Bayes LER**.
Combining R_*<=U_full with U_full>=U_floor does not order R_* and U_floor.
It does prove that no exact evaluation or upper approximation of this
unchanged U_full can give a bound below min(1/2,U_floor).

Here U_best denotes the existing Bayes upper bound, while U_floor bounds
the different witness-event quantity:

\[
\begin{array}{cc|cc}
p&q&U_{\rm floor}&U_{\rm best}\\\hline
.05&.50&.03694996&.03683883\\
.05&.75&.00935591&.02560125\\
.08&.50&.09129880&.13835664\\
.08&.75&.02933833&.10539805\\
.30&.50&.68679062&.50000000\\
.30&.75&.42911627&.50000000
\end{array}
\]

The first row rules out beating the existing fair p=.05 certificate through
this envelope. More decisively, at fair p=.30, even complete treatment of
all its overlaps cannot improve on the trivial one-half bound. The other
four rows are inconclusive; they do not prove that a cluster method succeeds
or fails there. This closes an overlap-only approach to the present fair
moderate-noise goal, not all connected expansions or posterior-weighted methods.

There is also a simple asymptotic explanation. For fair noise and even d,
the leading witness configurations consist of half a straight row, all with
the same sign. Their complementary opposite-sign configurations have equal
probability. Both sides count in the witness union, while Bayes counts the
smaller sector only once. Thus, at fixed size and low p,

\[
U_{\rm full}=2L\binom{d}{d/2}2^{-d/2}p^{d/2}
+O(p^{d/2+1}),
\qquad U_{\rm full}/R_*\longrightarrow2.
\]

At the minimal activity, only straight shortest paths contribute and each
configuration belongs to one row, so overlap removal cannot remove this
factor of two. Independently stored exact L3 values at p=.08,q=.5 are
R_*=.19682250, current-MAP risk .19928174 and U_full=.38922715. Most of this
gap is already present in the envelope after all overlaps are removed.

The [registered audit](../manifests/witness-union-floor-2026-09-19.json) and
[exact result](../results/witness-union-floor-2026-09-19.json) use all 177,147
currents of the 11-edge two-row motif and all 81 currents of the one-row
motif. Integer likelihood comparisons and rational probabilities preserve
ties exactly. Full L3 reproduction, q-reflection, normalization, the direct
one-row formula and all embeddings into the original square pass. No full
L5 witness union or new physical-record sample is claimed. The factor-two
explanation was derived during interpretation; the finite-cell decision
rule was registered before the strip probabilities were calculated.

## Status

Connected-defect theorems and the overlap correction remain valid. The
envelope audit above limits what any further overlap correction could do.
The [directional crossover](directional-crossover.md) returns to the physical
sector sums and solves a new low-noise boundary layer. Gaussian calibration
remains rejected; a square critical point and physical CFT remain open.

## Related pages

- [Replica boundary ratios](replica-boundary-ratios.md)
- [Complex weights and the conditional CFT route](complex-weights-and-cft.md)
- [Partition-function prediction and earlier finite certificates](partition-function-ler.md)
- [Earlier theory boundary](theory-boundary-synthesis.md)
- [Research plan](../PLAN.md)
