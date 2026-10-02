---
title: Decoding transitions and correction thresholds
status: current
updated: 2026-09-22
---

# Decoding transitions and correction thresholds

## Current theory priority (2026-09-22)

The researcher has stopped further size acquisition, including the L13
preflight and production described below. Those paragraphs are provenance,
not executable next actions. The active [thermodynamic theory](thermodynamic-decoding-theory.md)
audits the existing data, derives exact gap and gluing identities, and targets
a size-uniform estimate for physical posterior ambiguity. L13 histories remain
zero; method validation does not change this scientific priority.

## Historical L13 evidence boundary (stopped 2026-09-22)

The next computation adds exactly one size at p=.30 and q=.90,.94,.97. The
primary chi=16 posterior was selected before L13 data from the completed exact
validation; a fixed modulo-eight subset compares chi=16/32 and both sweep
directions. All three q cells share latent activity/orientation streams, while
L13-versus-L11 uncertainty remains independent across size.

This registration authorizes no production history until a zero-history L13
preflight passes. Numerical-sensitivity failure censors the whole L13 matrix.
Even a fully passing result can describe only finite-size contraction,
plateau, or tail behavior through L13; it cannot locate a threshold or
establish a thermodynamic phase.

The earlier per-vertex L13 preflight passed its twelve numerical and interface
checks, but its measured throughput prevented production arming. That
implementation projected the minimum registered primary+sensitivity matrix to
89,337 ideal four-worker seconds, versus the 7200-second cap. This is an
engineering feasibility failure, not L13 scientific evidence. No production
record was generated. It motivated the contraction-method comparisons below.

Two engineering-equivalent candidates have been rejected. Row-boundary
truncation is fast enough but changes frozen sector posteriors by up to
0.001006, above the 1e-10 replay gate. A top-chi PROPACK solver retains the
per-vertex schedule but is unstable on structured low-rank frontiers. Neither
failure changes the scientific model, and neither supplies L13 evidence. The
fast row schedule was subsequently tested as a new approximation on a fresh,
unseen exact-control cohort, with the completed result below.

The [fresh validation](../results/row-boundary-mps-fresh-validation-2026-09-22.json)
is now complete. It excludes every prior selected record and freezes eight
unused exact-gap strata per L9/L11 and q=.90/.94/.97 cell before evaluation.
All 192 evaluations pass, including each of the 24 chi/sweep/cell blocks.
Worst-block errors are median gap 7.52e-6, p95 gap 1.78e-5, p95 risk 2.80e-6,
and low-gap risk share below 5.28e-7, with no cutoff misclassification. Source
hashes, charge replay, exact identities and exclusion all pass. The run uses
30.51 seconds and a conservative 0.621 GiB; the frozen L13 throughput
projection remains 1,759 four-worker seconds. This promotes the row method
as a distinct approximation and leaves the earlier replay rejection intact.
There are still zero L13 histories and zero new bootstraps. The proposed next
preflight was withdrawn by the researcher on 2026-09-22; neither it nor
production is authorized under this historical acquisition contract.

## Beyond-L11 evidence boundary (2026-09-21)

Exact frontier contraction does not extend to L13 under the current caps. The
metadata-only sketch finds 583,522,191 candidate transitions and a 15.22 GiB
ungrouped-array lower proxy, versus 50,000,000 and 8 GiB. Bravyi, Suchara and
Vargo's boundary-MPS contraction is therefore treated only as a candidate
numerical method: its fixed bond dimension is approximate, and the source does
not provide an accuracy theorem for the present ternary-current posterior.

The active contract calibrates both sweep directions and a fixed bond ladder
against exact per-record L9/L11 sector probabilities. It cannot contribute an
L13 point, a fixed-gap limit, a phase classification or a threshold until one
common bond dimension passes all held-out gap, risk and CDF gates and a
separate production contract is registered.

The exact-ceiling tensorization prerequisite now passes at L5/L7 for both
sweep directions: the maximum sector error over twenty evaluations is
`3.54e-14`, with charge-only anti-leak, normalization, nonnegativity,
risk-gap, sector relabeling and replay checks passing. This validates the
local tensor network, not any finite bond dimension. The fixed-chi accuracy
matrix remains unrun and L13 evidence remains prohibited.

The finite-chi validation is now complete on 96 frozen L9/L11 records. All
four bond dimensions pass every held-out gate in both sweep directions; the
smallest, chi=16, has worst-cell 95th-percentile gap error 0.00388 and risk
error 0.000384, with no fixed-cutoff misclassification at 0.5,1,2,4. This is
a method result, not evidence about L13 or the thermodynamic limit. It permits
only a separately registered L13 acquisition with explicit chi sensitivity.

## Summary

The researcher's priority is the decoding phase boundary: where optimal
logical error vanishes as size grows, where it remains nonzero, and how
direction bias moves that boundary. Existing sufficient regions are rigorous
threshold bounds. Bulk-pressure existence and a possible CFT are supporting
tools; a transition claim must control the physical logical-sector ratio.

The directed square midpoint now has an exact residual-graph interpretation.
Critical bond percolation proves that ambiguous records remain present at
large size. The remaining quantity is the average posterior balance on those
records. Exact L3 counts reject the shortcut of assuming equal sector weights.
A boundary-flux polynomial represents that balance exactly, but the first
real-stability route stops at explicit all-size closure and recurrence
obstructions. Canonical L4 remains real-rooted, but the charge family has no
single common interlacing.

## Evidence

### Define the threshold without assuming monotonicity

Keep the canonical geometry, known arrows, independent bounded currents,
perfect interior integer charges and binary logical parity fixed. Let
R_L(p,q) denote optimal Bayes LER, and define

\[
\mathcal C(q)=\{p:\lim_{L\to\infty}R_L(p,q)=0\},\qquad
\mathcal B(q)=\{p:\liminf_{L\to\infty}R_L(p,q)>0\}.
\]

The initial correctable threshold is

\[
p_{\rm th}(q)=\sup\{p_0\in[0,1]:[0,p_0)\subseteq\mathcal C(q)\}.
\]

This does not assume a single transition or existence of a limit everywhere.
At p=1 every edge is active and its logical activity parity is known, so
R_L(1,q)=0. A monotone uncorrectable phase extending to p=1 cannot be presumed.
For q=1, current complementation gives R_L(p,1)=R_L(1-p,1), with a known
record shift and sector relabeling; no arbitrary-q symmetry is assumed.
A practical decoder has a different threshold: at matched noise, record and
score its risk is at least R_L and its initial threshold is at most p_th.

### Current rigorous threshold information

The square current-path theorem gives

\[
p_{\rm th}(q)\geq p_{\rm suff}(q)
=\frac{1-\sqrt{1-4/[9(1+2\sqrt{q(1-q)})]}}2.
\]

Convexity holds on this low-p interval. The factor three is a degree bound
on path growth, not the exact square connective constant.

| Geometry and bias | Established information | Unresolved |
| --- | --- | --- |
| Square, q=1/2 | p_th >= .05904145 | Nonzero-risk phase and sharp threshold |
| Square, q=1 | p_th >= .12732200 | Midpoint LER limit and threshold upper bound |
| Honeycomb, q>q_* or q<1-q_* | Every p is correctable; p_th=1 | Sharp endpoint of the bias window |
| Honeycomb, every q | Correctable for p<.07955179 and p>.92044821 | Intervening phase structure |

The exact q_*=.9925857155... is defined in the
[thermodynamic proof](thermodynamic-limits.md). It is a sufficient bias bound,
not an identified critical q. Square entries are lower bounds, not threshold
estimates. The high-p honeycomb result uses the activity-complement rule.

### Exact residual graph at the directed midpoint

At q=1, j_e belongs to {0,1}. Orient an edge along its assigned arrow when
j_e=0 and against it when j_e=1. This residual graph records the allowed
unit current changes. For every 0<p<1,

\[
Z_0(Q)Z_1(Q)>0
\quad\Longleftrightarrow\quad
\text{a residual directed path joins opposite rough sides.}
\]

Subtract the true current from any opposite-sector supported current. The
difference is divergence-free at measured vertices, follows residual arrows
and has odd cut parity. Conformal path decomposition therefore includes an
opposite-side path: cycles and same-side paths have even parity. Conversely,
flipping a simple residual path preserves measured charge and support while
changing logical parity. This proves support equivalence, without a weight
comparison between sectors.

At p=1/2 all residual orientations are independent fair coins, regardless
of assigned arrows. The reachable vertex set from the entire left rough
side has the same law as the connected seed set in bond percolation at 1/2.
The single-seed result is [Linusson, Lemma 2.1](https://arxiv.org/pdf/0905.2881),
following [McDiarmid](https://doi.org/10.2307/1426466). For multiple seeds,
explore unexamined edges from reached to unreached vertices. Every edge
allows discovery with independent probability 1/2, exactly the transition
of bond exploration. Edges with both endpoints reached need not be read.
This couples vertex clusters, not the full edge law or both crossing directions.

Write h_L for the bond left-to-right crossing probability and A_L for the
event that both logical sectors are supported. Direction reversal symmetry
and a union bound give

\[
h_L\leq\Pr(A_L)\leq\min\{1,2h_L\}.
\]

Deleting vertical edges on the rough sides does not change a bond crossing:
trim a path to its last left-side visit and first right-side visit. Thus the
canonical graph has the standard square-box crossing probability. Critical
RSW gives liminf h_L>0; see [Duminil-Copin, Theorem 4.6](https://www.ihes.fr/~duminil/publi/2017percolation.pdf).
Hence liminf Pr(A_L)>0. No numerical limiting crossing value or conformal-
invariance assumption is used. These are percolation statements; they do not
identify a decoding critical point.

### The posterior quantity needed for a decoding transition

Define r(Q)=min(Z_0,Z_1)/(Z_0+Z_1). Then exactly

\[
b_L=\mathbb E[r(Q)\mid A_L],\qquad R_L=\Pr(A_L)b_L.
\]

At the midpoint Pr(A_L) is bounded away from zero. Thus R_L->0 if and only
if b_L->0. A positive size-independent lower bound on b_L would prove a
noncorrectable midpoint and p_th(1)<=1/2. It is not yet proved. This target
is a physical-record average; no every-record balance assumption is needed.

More generally constants K,delta>0 independent of L with

\[
\liminf_{L\to\infty}\Pr(|\log(Z_0/Z_1)|\leq K)\geq\delta
\quad\Longrightarrow\quad
\liminf_{L\to\infty}R_L\geq\frac{\delta}{1+e^K}>0
\]

certify a noncorrectable regime. This is the missing counterpart to the
existing correctability upper bounds; failure of an upper bound does not
supply it.

### Exact finite control and a rejected shortcut

The [registered study](../manifests/square-midpoint-thermodynamics-2026-09-20.json)
uses all 256 directed L3 currents and all 256 bond configurations on the
same eight-edge graph. Complete seed-set cluster distributions agree and
every current obeys the support equivalence. The
[script](../scripts/check_square_midpoint.py) and
[result](../results/square-midpoint-thermodynamics-2026-09-20.json) retain
all 64 record-sector counts.

| L3 midpoint quantity | Exact value |
| --- | --- |
| Optimal LER | 7/16 |
| Probability that both sectors are supported | 119/128 |
| One-direction residual crossing / bond crossing | 43/64 |
| Conditional average b_3 | 8/17 |

Of 46 ambiguous records, 14 have unequal sector counts. For example,
Q=(-2,0,1) has counts (3,2), risk 2/5 and probability 5/256. Hence
R_L=Pr(A_L)/2 is already false on the original L3 geometry. This rejects
exact balance, not a weaker size-uniform bound. No decoder samples or
finite-size extrapolations enter this calculation.

### Boundary-flux polynomial and the stability obstruction

For fixed physical charge record Q define

\[
F_Q(t)=\sum_{j:D_Mj=Q}t^{K(j)},
\]

where K is the number of active currents on the logical cut. If N_0,N_1 are
the even/odd sector counts, then

\[
F_Q(1)=N_0+N_1,\quad F_Q(-1)=N_0-N_1,\quad
r(Q)=\frac{1-|F_Q(-1)/F_Q(1)|}{2}.
\]

Thus this is the original physical posterior, not a typical-record or
percolation surrogate. If every F_Q had only real nonpositive roots, the
conditional cut activity would be Poisson-binomial. Writing its variance as
V_Q would give

\[
|F_Q(-1)/F_Q(1)|\le e^{-2V_Q},\qquad
r(Q)\ge\frac{1-e^{-2V_Q}}2.
\]

The [exact control](../results/posterior-balance-polynomial-2026-09-20.json)
reuses the same 256 L3 currents. All 64 polynomials have real nonpositive
roots; all parity projections and risk identities pass. On the 46 ambiguous
records, V_Q ranges from 1/4 to 7/12, its physical conditional average is
48/119, and the variance bound has no failures. These are finite L3 facts.

The all-size inference is blocked. Borcea, Brändén and Liggett's
[primary stability theorem](https://arxiv.org/abs/0707.2340) preserves
multiaffine stability under coordinate conditioning, projection, external
fields and suitable specialization. Fixing D_Mj=Q is instead a joint signed
linear constraint, equivalently a Laurent-coefficient extraction; the
reviewed closure theorems do not cover it. Even all-size real-rootedness alone
would not prevent roots from approaching zero or minus infinity, so it would
not supply a size-uniform lower bound on V_Q over positive physical record
mass. The [registration](../manifests/posterior-balance-2026-09-20.json),
[script](../scripts/check_posterior_balance_polynomial.py), and result retain
the exact boundary and zero-new-sample audit.

### Exact transfer and why the direct interlacing induction fails

Let C_(s,Q)(t) count partial binary currents after processing s edges. If d_s
is the measured-incidence column of the next edge and ell_s indicates whether
that edge lies on the logical cut, exact coefficient extraction gives

\[
C_{s+1,Q}(t)=C_{s,Q}(t)+t^{\ell_s}C_{s,Q-d_s}(t).
\]

Grouping the edge updates from left to right is the desired fixed-charge
column transfer. The [registered L4 check](../manifests/posterior-polynomial-closure-2026-09-20.json)
matches an independent exhaustive table of all 262,144 currents and 44,494
charge records. All 44,494 final polynomials have real nonpositive roots, and
all 34,721 actual two-summand updates with both terms nonzero pass a numerical
interlacing check. Exact L4 values are

| Quantity | Exact value |
| --- | --- |
| Optimal LER | 11849/32768 |
| Ambiguous-record probability | 116411/131072 |
| Conditional average b_4 | 47396/116411 |
| Ambiguous-record cut variance range | 6/49 to 7/11 |

These finite facts do not close the induction. The final L4 charge family
contains both F_Q(t)=t and F_Q'(t)=1+5t+t^2. The root zero of the first is not
between the two roots (-5±sqrt(21))/2 of the second. Hence the full family is
not a common-interlacing family, so the standard global compatibility argument
cannot prove that every later transfer sum is real-rooted. The observed local
pair structure may be stronger and charge-dependent, but no all-size invariant
is established. The [script](../scripts/check_posterior_polynomial_closure.py)
and [machine result](../results/posterior-polynomial-closure-2026-09-20.json)
retain every check and the exact counterexample.

### Direct path switching: valid local move, invalid global selector

At the midpoint all binary currents have equal probability. Flipping any
simple residual directed path between rough sides preserves the full measured
charge and changes logical parity. Therefore any disjoint collection of such
cross-sector pairs gives the exact finite bound

\[
\sum_Q\min(N_0(Q),N_1(Q))\geq\#\{\text{disjoint switched pairs}\}.
\]

The [registered switching audit](../manifests/midpoint-switching-pairing-2026-09-20.json)
tests two deterministic selectors: order all simple boundary-to-boundary paths
by their left-to-right height sequence and choose the lower or upper extreme
that is residual-directed. The underlying path move passes every charge and
parity check, but reversing the chosen path can make another path extremal.

| Exact audit | L3 | L4 |
| --- | ---: | ---: |
| Crossing states | 238 | 232822 |
| Selector-stable states | 172 | 113412 |
| Stable fraction given crossing | 86/119 | 56706/116411 |
| Finite LER pairing lower bound | 43/128 | 28353/131072 |
| Maximum full-map multiplicity | 3 | 16 |

Both extremal full-event maps have collisions; only the selector-stable subset
is an injective involution. A standalone directed plaquette flip also fails:
all 86,528 eligible L4 states preserve charge but none changes logical parity.
The [script](../scripts/check_midpoint_switching_pairing.py) and
[machine result](../results/midpoint-switching-pairing-2026-09-20.json) retain
the exact collision witnesses and checks.

Ordinary RSW controls the probability that a crossing exists, not the event
that an extremal selector is unchanged after every edge of its crossing is
reversed. The observed stable fraction decreases between L3 and L4; that is
not an asymptotic trend claim. A proof now needs either a size-uniform bound
for a selector-stability/multi-arm event or a fractional matching/mass-
transport construction that does not choose one deterministic path.

### Full switching graph: finite saturation, asymptotic capacity still open

The [registered full-graph audit](../manifests/midpoint-fractional-switching-2026-09-20.json)
connects opposite-sector currents within each charge record whenever one
residual-directed simple path flip maps them. Exact bipartite matching gives

| Exact capacity audit | L3 | L4 |
| --- | ---: | ---: |
| Unique switching edges | 352 | 580608 |
| Maximum matching pairs | 112 | 94792 |
| Bayes numerator | 112 | 94792 |
| Extra pairs over stable selector | 26 | 38086 |
| Exact finite Bayes LER | 7/16 | 11849/32768 |

Every charge record's smaller sector is saturated. This is certified on both
sides: weight one on the matched edges is a symmetric fractional flow, and
the union of each record's smaller sector is a same-size vertex cover. By
bipartite matching-polytope integrality, a fractional relaxation cannot exceed
this integral optimum. Disconnected switching components create no additional
finite deficit: the sum of their minority sizes equals the Bayes numerator.
The [script](../scripts/check_midpoint_fractional_switching.py) and
[machine result](../results/midpoint-fractional-switching-2026-09-20.json)
retain the matching, component, path-degree and dual-certificate checks.

This closes the finite selector-collision issue but not the thermodynamic
problem. Positive switching degree is only crossing existence; path count by
itself does not give every-subset Hall expansion. An all-size matching theorem
would still need a separate size-uniform lower bound on normalized matching
mass.

### Orientation-lattice audit: exact NMP, missing restricted theorem

Contracting all rough-boundary vertices to one outer root maps each binary
current to a full planar orientation. For an interior vertex,

\[
\operatorname{outdeg}(v)=\deg(v)-\operatorname{storedTail}(v)-Q(v),
\]

so fixed charge fixes every outdegree: each record is an alpha-orientation
class. Every registered opposite-rough-side path flip becomes a directed
cycle reversal through the contracted root. Exact normalized transport gives
uniform marginals on both logical sectors:

| Size | Transport | Split | Internal |
| --- | ---: | ---: | ---: |
| L3 | 456 / 456 | 0 | 0 |
| L4 | 1,253,808 / 1,253,808 | 578 | 86,528 |

Thus every L3/L4 record graph has the normalized matching property (NMP), a
scaled Hall condition stronger than simple minority saturation. The
[registered audit](../manifests/midpoint-all-size-matching-theorem-2026-09-20.json)
also deletes every one and every pair of the 18 canonical L4 edges. All
18+153 variants retain full Bayes-numerator saturation; this is bounded
robustness evidence, not an all-size theorem. The
[machine result](../results/midpoint-all-size-matching-theorem-2026-09-20.json)
retains the transport and fragmentation certificates.

The primary-source boundary is precise. Felsner and Propp prove distributive
lattices for planar fixed-outdegree orientations, and Khuller, Naor and Klein
do so for planar integral circulations, using the full internal cycle/face-flip
structure. Our public graph keeps only root cycles whose original endpoints
lie on opposite rough arcs; internal and same-side root cycles are absent and
do not change logical parity. The random/pseudorandom NMP theorem of
Balachandran and Kush also does not apply to this deterministic,
charge-conditioned graph without a discrepancy estimate. Distributivity alone
therefore does not prove the required restricted Hall inequalities.

Two separate lemmas remain. Structurally, the restricted opposite-rough-arc
root-cycle graph must have NMP for every size and charge. Probabilistically,
\(2^{-E}\sum_Q\min(N_0(Q),N_1(Q))\) must have a positive size-uniform lower
bound. Only the second statement implies midpoint noncorrectability, even if
the first is granted. The next registered study targets this minority-mass
bound, or the proof that ordinary crossing/RSW information cannot supply it,
without L5 enumeration or threshold extrapolation.

### Why crossing plus NMP is still insufficient

The [registered minority-mass audit](../manifests/midpoint-minority-mass-lower-bound-2026-09-20.json)
tests all three zero-sampling branches. First, a fixed rough-to-rough path has
length at least \(d=L-1\) and is coherently directed in either direction with
probability \(2^{1-d}\). For any polynomial-size prechosen path family, the
union bound therefore vanishes. This rejects fixed spanning gadgets, not an
adaptive critical construction.

Second, neither RSW nor normalized matching contains the missing posterior
information. RSW controls \(\Pr(A_L)\), while the Bayes risk also contains the
charge-fiber factor \(\min(N_0,N_1)/(N_0+N_1)\). The complete bipartite graph
\(K_{1,M}\) has NMP and ambiguity probability one, but minority fraction
\(1/(M+1)\to0\). This is a logical countermodel to the inference, not a claim
that this graph is realized by the square current channel. Reimer's
disjoint-occurrence inequality is also an upper bound on product-space events;
it does not compare charge-fiber sector multiplicities.

Third, a precise sufficient replacement is available. If a charge-preserving
sector-switching map covers every ambiguous state and every image has at most
\(C\) preimages, then within each charge fiber

\[
\begin{aligned}
N_0&\le C N_1,\\
N_1&\le C N_0,\\
R_L&\ge\frac{\Pr(A_L)}{C+1}.
\end{aligned}
\]

| Size | \(C\) | Congestion | Stable |
| --- | ---: | ---: | ---: |
| L3 | 3 | 119/512 | 43/128 |
| L4 | 16 | 116411/2228224 | 28353/131072 |

These are exact finite certificates, not a trend. They identify the missing
physical theorem: uniformly bounded switching congestion, conditional sector
balance, or an equivalent conditional-entropy estimate on positive physical
mass. The [machine result](../results/midpoint-minority-mass-lower-bound-2026-09-20.json)
retains the proofs, source applicability and zero-sample audit. The next
registered study tests those charge-fiber mechanisms directly, or constructs a
canonical analytic imbalance family.

### Exact finite fiber imbalance and the averaged target

The [registered charge-fiber audit](../manifests/midpoint-charge-fiber-balance-theorem-2026-09-20.json)
separates a poor path selector from intrinsic imbalance. For a fiber with
sector sizes \(n_0,n_1\), record-wise NMP and capacitated Hall transport prove
that the least possible deterministic image congestion is
\(\lceil\max(n_0/n_1,n_1/n_0)\rceil\): pigeonhole gives the lower bound and NMP
supplies the capacity-constrained assignment.

| Size | Optimal \(C\) | Selector \(C\) | Max ratio | Max-ratio mass | \(H(H\mid Q)\), bits |
| --- | ---: | ---: | ---: | ---: | ---: |
| L3 | 2 | 3 | 3/2 | 5/32 | .92345967 |
| L4 | 6 | 16 | 6 | 21/8192 | .85140822 |

Canonical L4 contains 96 maximum-ratio records; a minority-one witness has
switching graph \(K_{1,6}\). This is a physical finite star fiber, unlike the
earlier abstract countermodel, but two sizes do not establish an unbounded
family. It rejects exact or near-unity every-record balance without deciding
the physical average.

Entropy gives an exact equivalent asymptotic target. With conditional Bayes
risk \(r_Q\leq1/2\),

\[
2r_Q\leq h_2(r_Q)\leq2\sqrt{r_Q},\qquad
2R_L\leq H(H\mid Q)\leq2\sqrt{R_L}.
\]

Thus a uniform entropy lower bound \(\eta\) would imply \(R_L\geq\eta^2/4\).
Reviewed flow-polytope/Kostant results count unrestricted integral flows, but
do not compare the bounded binary logical sectors inside a fixed rough-boundary
charge fiber. No uniform congestion theorem, entropy lower bound or analytic
unbounded-imbalance family is established. The [machine result](../results/midpoint-charge-fiber-balance-theorem-2026-09-20.json)
therefore records an explicit missing lemma: positive physical mass must lie on
fibers with a size-uniform positive minority ratio. The next registered step
targets that average through two-copy overlap or multiscale block events.

#### Why two-copy overlap and local gluing do not yet close the average

Write p(Q) for the physical charge-record probability, r(Q) for the
conditional minority ratio and m(Q) for the posterior sector magnetization.
The exact identities are

\[
R_L=\sum_Q p_Qr_Q.
\]

\[
\frac{1-\mathbb E[m_Q^2]}4=\mathbb E[r_Q(1-r_Q)].
\]

and for two independent currents,

\[
O_L=\Pr(Q_1=Q_2,H_1\ne H_2)
=\sum_Qp_Q^2\,2r_Q(1-r_Q).
\]

Thus the normalized overlap Psi(L) = O(L)/C(L), with C(L) the same-charge
collision probability, averages under a collision-size-biased charge law
rather than the physical law p(Q). One always has

\[
R_L\geq\frac{O_L}{2p_{\max,L}}
=\frac{\Psi_L}{2}\frac{C_L}{p_{\max,L}}.
\]

Exact controls give Psi(L) = 57/116 and 313452/653081, while
C(L)/pmax(L) = 29/56 and 653081/4423680 for L3/L4. These are controls,
not a trend. Two abstract probability constructions show the missing logic:
unnormalized overlap may vanish at risk 1/2, and normalized overlap may tend to
1/2 while physical risk tends to zero. A conversion therefore needs charge-law
regularity in addition to a two-copy signal.

The multiscale branch fails at the same interface. Harris-FKG and RSW glue
increasing connectivity events; full-charge posterior balance is not such an
event. Every charge-preserving sector change contains a rough-to-rough path,
while the exact L4 standalone-plaquette audit has zero logical flips. Local
blocks therefore cannot be promoted to a global balance theorem without a
positive-probability event carrying uniformly bounded full-fiber congestion.
The [machine result](../results/midpoint-averaged-charge-balance-2026-09-20.json)
records the exact identities, finite balance-mass profiles, countermodels and
source boundary. The next registered audit asks only whether local-limit or
anti-concentration results can supply the missing collision-to-physical
charge-law comparison.

#### Why collision-to-physical conversion is not dimension-free

The bounded source/theorem matrix now closes that conversion route. Classical
lattice local-limit theorems do not supply an atom estimate uniform in the
growing dimension of the divergence record. A reviewed bounded-dependence CLT
controls convex-set probabilities rather than lattice atoms, while the
reviewed orientation enumeration assumes average degree at least
\(n^{1/3+\epsilon}\) and strong mixing, excluding the bounded-degree square
family.

There is also a structural warning independent of those hypothesis failures.
For a \(d\)-dimensional Gaussian density \(f\),

\[
\frac{\int f(x)^2\,dx}{\max_x f(x)}=2^{-d/2}.
\]

Thus even ideal high-dimensional Gaussian regularity predicts loss with the
number of measured charges, not a positive constant lower bound on
\(C_L/p_{\max,L}\). Exact total-charge counts pass every coordinate-neighbor
log-concavity check—88 at L3 and 125616 at L4—but product log-concave laws
still have this dimensional loss, and total counts do not control the logical
sector split.

The second factor is not structural either. Bitwise complement swaps logical
sector for the odd L3 cut but preserves it for the even L4 cut and generally
changes the charge record. More abstractly, two equal-mass records with sector
counts \((1,M)\) and \((M,1)\), exchanged by a complement-style involution,
satisfy normalized matching while

\[
\Psi=\frac{2M}{(M+1)^2}\longrightarrow0.
\]

The [machine audit](../results/midpoint-charge-collision-comparison-2026-09-20.json)
therefore closes only the proxy conversion: it does not show that physical
risk vanishes. The next registered route returns to \(\mathbb E_{Q\sim p}r_Q\)
directly via a full-record renormalized switch, a conditional-entropy
martingale, or a compatible physical obstruction.

#### Direct physical risk reduces to average selector multiplicity

The direct route does yield a sharper exact lemma. On each ambiguous
full-charge fiber, choose its majority logical sector and apply one fixed
residual-crossing selector to every majority state. Let \(A_L\) be the total
number of these domain states, and let \(m_y\) count how many selected states
map to the same minority target \(y\). Two applications of
Cauchy–Schwarz give

\[
R_L\geq\frac{A_L^2}{2^E\sum_y m_y^2}
=\frac{A_L/2^E}{\kappa_L}.
\]

Here \(\kappa_L=(\sum_y m_y^2)/A_L\) is a size-biased average preimage
multiplicity under the physical majority domain, not worst-case congestion
and not a collision-reweighted charge law. Since RSW gives positive ambiguous
mass and \(A_L\) is at least half that mass, a size-uniform upper bound on
\(\kappa_L\) would prove positive midpoint Bayes risk directly.

The exact controls are nontrivial but finite. The lower extremal selector has
\(\kappa_3=110/63\) and \(\kappa_4=76181/23005\), giving risk lower bounds
3969/14080 and 1587690075/9985196032. Reversing the path order changes the L4
value slightly to \(76171/23005\) and the bound to
1587690075/9983885312. These values certify the reduction, not a size trend.

The entropy alternative does not localize automatically. In the frozen
natural charge order, exact Bayes risk remains 1/2 after every proper prefix at
L3 and L4, and all observed logical information appears at the final charge;
conditional entropy similarly remains one bit until that step. Thus the chain
rule is exact but supplies no local entropy floor without an additional
geometric bound on total information gain. Canonical L4's 96 physical
\(K_{1,6}\) fibers show finite imbalance but do not construct an asymptotic
physical obstruction family.

The [direct-risk audit](../results/midpoint-direct-risk-renormalization-2026-09-20.json)
therefore promotes \(\kappa_L\), not entropy increments or two-copy overlap,
as the next precise target. The registered successor classifies pairs of
states contributing to \(\sum_y m_y^2\) and asks whether their geometry is
controlled by summable square-lattice arm events.

#### The second moment is an exact collision-pair count

For any deterministic selector on the physical majority domains,

\[
\sum_y m_y^2=A_L+2N_{\mathrm{collision}},
\]

where \(N_{\mathrm{collision}}\) counts unordered distinct majority-state
pairs sent to the same minority target. Every exact off-diagonal pair uses two
different selected rough-to-rough paths; the XOR of the two input states is
exactly the symmetric difference of those paths and has even degree at every
measured interior vertex. This identity replays the earlier lower and upper
extremal second moments exactly.

A four-order matrix on identical physical domains shows that path choice is
scientifically material even before the all-size question. At L3,
shortest-then-lexicographic has \(\kappa=11/9\) and direct risk certificate
567/1408, compared with \(110/63\) and 3969/14080 for the lexicographic
extreme. At L4 it has \(\kappa=3113/1605\) and certificate
110769075/408027136, compared with about 3.311 and .159 for the two extremes.
Longest-first lies between them. Finite-family averaging guarantees that one
registered order is no worse than the family mean, but does not give a
uniform-in-size selector.

The exact geometry also rejects a direct standard-arm shortcut. At L4 the
shortest selector's collision differences have zero, two or four odd rough
endpoints and one or two connected components; other registered orders reach
three components. Kesten-type RSW and quasi-multiplicativity control specified
arm events, and exact polychromatic exponents are available for triangular
site percolation, but no reviewed theorem dominates these state-dependent,
full-charge-conditioned collision classes by a summable square-bond arm event.
No positive-mass square family forcing \(\kappa_L\) to diverge was constructed
either.

The [collision matrix](../results/midpoint-selector-second-moment-renormalization-2026-09-20.json)
therefore selects shortest-then-lexicographic only as the best finite control.
The next registered question is whether first path divergence and reconnection
admit a geodesic-exchange encoding with bounded average multiplicity, or a
physical collision ladder defeats that route.

#### Why ordinary geodesic exchange does not cover the collisions

Let (X) be uniform on the physical majority domain, let (T(X)) be the
selected target and set (M=m_{T(X)}). The exact tail identity

\[
\kappa_L=\mathbb E[M]=\sum_{r\geq1}\Pr(M\geq r)
\]

shows the weakest sufficient target: dominate this tail by one summable
sequence uniformly in (L). Such a proof must control both the number of
exchange witnesses and their physical probabilities under the majority-domain
law, not merely count paths on an unconditioned lattice.

The registered exchange matrix replays (kappa_3=11/9) and
(kappa_4=3113/1605). After each rough side is collapsed to one virtual
vertex, every collision pair has a first divergence and reconnection and all
charge-preservation, logical-flip, target and selector checks pass. But the
usual closed exchange between paths with the same physical endpoints covers
none of the 14 L3 pairs and only 4,170 of the 64,844 L4 pairs. Only 7,586 L4
pairs even have equal path length. The two paths are shortest-selected in two
different preimage states, so a same-environment geodesic subpath swap does
not preserve the selector conditions.

The finite obstruction is an open boundary fan, not yet an asymptotic ladder.
At L4, targets of multiplicity at least four contain 7,528 of 138,030 majority
preimages and contribute 33,900 of 267,718 to the second moment. Eight targets
have multiplicity eight; each mixes eight rough-endpoint pairs and path lengths
spanning three edges around one common core edge. These exact masses do not
construct a nested event whose probability remains large enough as (L)
grows.

The [exchange audit](../results/midpoint-shortest-selector-geodesic-exchange-2026-09-20.json)
therefore closes the naive closed-geodesic argument and names the remaining
lemma: prove a summable physical tail for open boundary-fan multiplicity across
the two selector environments, or construct a nested fan whose multiplicity
growth defeats its probability suppression. No uniform (kappa_L) bound,
midpoint classification or threshold follows.

#### The fan witness is finite-injective, but BK/Reimer has the wrong law

The size-biased tail was replayed directly: its sum is (11/9) at L3 and
(3113/1605) at L4. For a fixed base preimage and selected target, the tuple
consisting of the alternate path's two rough endpoints and its first virtual
divergence/reconnection uniquely identifies every alternate path in the exact
controls—all 28 ordered alternates at L3 and 129,688 at L4. This is a useful
finite encoding, not a uniform bound: the endpoint and bulk-vertex signature
space grows with (L).

The probability shortcut fails at two separate hypotheses. BK, and Reimer's
extension to arbitrary events, bounds disjoint reasons in one configuration
under a product measure. Here the alternate path is selected in a different
preimage configuration, while (kappa_L) uses the globally defined
majority-domain law and size-biases it by common-target multiplicity. Lifting
to two independent copies does not fix this: conditioning the copies to have
the same selected target destroys the product law. The fixed-cardinality BK
extension also does not apply because a full-charge fiber-majority law is not
a k-out-of-n measure.

A bounded diamond-chain matrix confirms that multiplicity growth is
combinatorially compatible with the selector. Chains of one through four
diamonds have (2^n) candidate paths and exact maximum multiplicities
(1,2,4,8) on (4n) edges. Yet this isolated graph omits every outside
square path and the physical charge-majority filter, so its finite target
weights are neither a physical nested event nor evidence that
(kappa_L) diverges.

The [tail audit](../results/midpoint-boundary-fan-tail-2026-09-21.json)
therefore closes the direct BK/Reimer shortcut. The next bounded diagnostic is
an exact width-three square-strip transfer that must include the missing edges,
full charge, majority denominator and selector second moment. Even a resolved
strip rate would remain fixed-width evidence, not a two-dimensional threshold.

#### The physical strip keeps finite fan multiplicity, but selector memory is nonlocal

The exact height-three square-strip embedding includes every strip path, full
interior charge, the physical majority-domain filter, rough boundaries and the
frozen shortest-then-lexicographic selector. Direct enumeration gives
`A=126`, `S=154`, `kappa=11/9` at W=3 and `A=3926`, `S=7968`,
`kappa=3984/1963` at W=4; maximum multiplicity grows from two to five. Thus
outside square paths and physical conditioning do not destroy the finite fan
at the first nontrivial embedding. Two widths do not determine a rate.

An exact column transfer for full charge and majority membership reproduces
those controls and reaches W=5 with 144,464 prefix/frontier states, 80,182
charge fibers, majority-domain denominator 108,978 and Bayes numerator 55,496.
It fails closed during W=6 when the state count first reaches 2,000,001, above
the registered cap. More importantly, equal charge/frontier states can disagree
on whether an earlier path was available, so this transfer cannot compute the
nonlocal selector second moment. An unreduced ordered path-pair description
already exceeds two million channels at W=8.

The [strip-transfer audit](../results/midpoint-boundary-fan-strip-transfer-2026-09-21.json)
therefore establishes finite embedded multiplicity but no fixed-width growth
rate, divergence of `kappa`, midpoint noncorrectability or square threshold.
The registered prerequisite is an exact reduced selector-availability
automaton, validated at W=3/W=4 before any W=5 evaluation.

#### The W=5 exact selector moment is feasible, but no rate follows

That prerequisite now passes at its registered bound. An exact multi-terminal
decision diagram compiles physical majority membership and the complete
shortest-selector target map with zero truth-table replay mismatches. It uses
326 states at W=3, 7,842 at W=4 and 179,446 at W=5, all below the cap. An
independent target-key pair accumulator reproduces the same second moments.

At W=5 the exact values are `A=108978`, `S=336814`,
`kappa=168407/54489` (about 3.09), maximum multiplicity 12, and 227,836
ordered alternate pairs. This establishes the missing finite strip value, not
its asymptotic behavior: the decision diagram is compiled from the complete
`2^18` truth table and is not yet a width-recursive frontier construction.

The [selector-automaton audit](../results/midpoint-selector-automaton-feasibility-2026-09-21.json)
therefore moves the frontier to a genuine rate certificate. The next bounded
matrix must either produce a symbolic width recursion, an all-width embedded
family with its physical probability, or a uniform summable fan-tail bound.
No fit to W=3,4,5 and no threshold interpretation are allowed.

#### The three all-width routes stop at different exact obstructions

The local recursion fails before W=6. On the W=4 strip, full states 79 and 106
have the same full charge, the same processed-column charge and frontier bits,
and the same unprocessed suffix. Nevertheless the shortest selector chooses
path indices 0 and 2 and produces targets 68 and 7274. Thus the ordinary
charge/frontier transfer key is not a congruence for the selector language.
The extensional W=6 truth table would already contain 8,388,608 inputs, above
the registered two-million-state cap, and was not constructed.

The simplest constructive lower-bound family also fails physically. The 9,
29 and 95 path-only configurations at W=3,4,5 would all map to the zero target
combinatorially, but none lies in the physical majority domain; its exact
probability numerator is zero at all three controls. Conversely,
`M_W<=P_W`, the number of simple crossings, is a correct pointwise upper
cutoff, but there are already `3^(W-1)` x-monotone paths. Its width supremum
therefore gives no summable envelope for the multiplicity tail.

The [rate-certificate audit](../results/midpoint-selector-rate-certificate-2026-09-21.json)
closes this bounded matrix without a rate or threshold claim. The next step is
not a larger enumeration: it is a primary-source theorem-interface audit of
the physical posterior law, after which the selector route is either grounded
in a hypothesis-complete result or demoted in favor of a larger question.

#### No reviewed theorem closes the selector interface

The bounded primary-source audit checked nine results across three families.
BK/Reimer and planar random-cluster crossing or arm estimates act on one
product/FK configuration and do not control the majority-conditioned ratio of
two logical sectors. Planar alpha-orientation and circulation theorems use the
full local-move lattice, whereas the physical switching graph keeps only
opposite-rough-arc logical flips. Normalized matching results assume random or
pseudorandom bipartite graphs and, in any case, normalized matching alone does
not lower-bound the physical minority mass. Fixed-width transfer matrices are
valid strip tools but do not supply a two-dimensional size-uniform conclusion.

The [theorem-interface audit](../results/midpoint-alternative-theorem-interface-audit-2026-09-21.json)
therefore demotes the selector route. This is an applicability result, not a
proof that a new theorem cannot be invented and not a midpoint classification.
The next central question uses the selector-free sector partition sums

\[
\Delta F(Q)=\log\!\frac{Z_0(Q)}{Z_1(Q)}
\]

#### Posterior gap gives the selector-free order parameter

Set $G_L=|\Delta F|$. The exact
record-level and physical risks are

\[
b(G)=\frac{1}{1+e^G},\qquad R_L=\mathbb E_Q[b(G_L)].
\]

Consequently $R_L\to0$ if and only if $G_L\to\infty$ in
physical-record probability. For every fixed $a$, with
$C_L(a)=\Pr(G_L\leq a)$,

\[
\frac{C_L(a)}{1+e^a}\leq R_L\leq
\frac{C_L(a)}2+\frac{1-C_L(a)}{1+e^a}.
\]

This supplies the discriminating protocol. Typical stiffness requires every
fixed-$a$ CDF to vanish, not merely a growing median. Persistent positive
fixed-gap mass forces nonzero limiting risk. A third possibility has outward-
moving typical gaps while a shrinking low-gap tail carries most of the risk;
the risk-concentration statistic
$B_L(a)=\mathbb E[b(G_L)\mathbf{1}_{G_L\leq a}]/R_L$ detects that mechanism.

The [posterior-gap synthesis](../results/posterior-gap-order-parameter-synthesis-2026-09-21.json)
replays all 15 existing square `p=.30`, `L=5,7,9` cells without new samples or
bootstraps. At `q=.90`, risk is `.3013,.2494,.2450` and $C_L(1)$ is
`.617,.457,.432`; the last size step is effectively flat. At `q=.97`, the
median gap moves `1.40,1.73,2.13`, but $C_9(1)=.240$ and risk remains `.156`.
At `q=1`, the median moves `2.05,3.25,4.16` while risk falls
`.1536,.0910,.0460`. These are distinct finite-size patterns, but none selects
an asymptotic class from three sizes.

The registered successor is therefore boundary-focused rather than a broad
phase-map rescan: fixed `p=.30`, `q=.90,.94,.97`, `L=7,9,11`, with only five
new cells after reusing four endpoint cells without numerical pooling. An
exact `L=11,q=.94` resource and identity preflight must pass before sampling.
The analysis must report $R_L,C_L(a)$, gap quantiles and $B_L(a)$ together;
no crossing, threshold or BKT fit is allowed.

That prerequisite has now passed. Exact construction used 43,578,135 candidate
transitions with frontier width 10, completed the full deterministic preflight
in 11.48 seconds, and reached 0.91 GiB peak RSS, all within the registered
caps. Zero, signed-edge, sparse mixed, and rough-to-rough logical currents pass
posterior normalization, risk-gap, sector-swap and exact replay checks; the
logical current shares the zero public charge record while flipping the true
logical sector. No stochastic history or bootstrap replicate was generated.

Production has subsequently completed under the unchanged gate: 2,688 total
records across the five registered cells, with record counts
`640,512,640,512,384` and every cell stopping on both precision targets before
the 1,024-record hard cap. Replay passes unique-key, stream, normalization and
risk-gap checks. By themselves these acquisition summaries are not the
complete-matrix analysis and do not select a mechanism or critical boundary.

The complete 3-by-3 analysis now resolves the registered finite-size question.
For `q=.90,.94,.97`, L7-to-L11 Bayes-risk changes are respectively
`-.0425 [-.0619,-.0225]`, `-.0493 [-.0661,-.0317]`, and
`-.0692 [-.0922,-.0457]`; every corresponding `C_L(1)` contrast is negative,
while median and lower-quartile gap contrasts are positive. The formerly flat
`q=.90` L7-to-L9 trajectory therefore moves outward at L11. `B_L(1)` at L11
is not above its L7 value for any q, so the data do not show a shrinking
low-gap set taking an increasing share of risk. Finite-size typical-gap motion
is favored, a persistent plateau is weakened, and rare-tail takeover is not
supported through L11. Three sizes still cannot establish gap divergence in
probability or exclude a later crossover.

![Posterior-gap boundary diagnostics](../figures/posterior-gap-boundary-tail-matrix.png)
*Pointwise record-bootstrap 95% intervals. Open markers are historical controls
retained without numerical pooling; lines only join sampled sizes.*

## Status

The residual-support equivalence, midpoint cluster law and nonvanishing
ambiguity probability are established. The boundary-flux representation is
exact and its L3/L4 root diagnostics pass, but fixed-divergence stability,
global common interlacing and size-uniform variance are unavailable. The
square posterior-balance limit remains open; p=1/2 is not established as a
decoding critical point. Deterministic selectors collide, while the full L3/L4
switching graphs satisfy exact normalized matching and every bounded edge-
deletion control retains saturation. Reviewed orientation-lattice theorems do
not cover the restricted logical graph. Moreover, crossing plus NMP is
information-theoretically insufficient for nonzero Bayes-risk density. Exact
optimal congestion is 2/6 at L3/L4 and physical L4 \(K_{1,6}\) fibers exist,
but no size-uniform per-record theorem survives. Two-copy overlap has the wrong
charge weighting by itself, and its conversion loses with growing charge
dimension under the available hypotheses. Local gluing does not create
conditioned sector balance. A direct physical-law reduction is now proved, but
its selector second moment lacks a uniform bound. Shortest-first is the best
finite order, but ordinary geodesic exchange misses the dominant open boundary
fans; the finite witness is injective, while product-measure disjoint-occurrence
inequalities have the wrong conditional law. A nine-source audit finds no
hypothesis-complete replacement for that selector interface, so the route is
demoted. The posterior-gap identity is now exact, but the existing three-size
data do not select among typical stiffness, finite gaps and rare-tail control.
The boundary-focused acquisition, integrity checks, and complete-matrix
analysis are complete. They establish finite-size outward gap motion and no
rare-tail takeover through L11, not a thermodynamic phase. No threshold,
critical q, exponent, universality or BKT claim follows.

## Related pages

- [Thermodynamic limits and correctability](thermodynamic-limits.md)
- [Logical-sector predictions](sector-predictions.md)
- [Connected-current path bounds](connected-current-defects.md)
- [Complex weights and CFT](complex-weights-and-cft.md)
- [Research plan](../PLAN.md)
