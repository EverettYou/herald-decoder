---
title: From the auxiliary partition function to the LER curve
status: current
updated: 2026-09-18
---

# From the auxiliary partition function to the LER curve

## Summary

**Current extension:** [connected current defects](connected-current-defects.md)
now gives improved biased finite-square upper bounds and an exact directed
L3 polynomial through p=.2. The earlier figure and certificates on this page
remain frozen baselines; they are not the strongest current bounds in every cell.

Follow-on results are now in [replica boundary ratios](replica-boundary-ratios.md):
rigorous moment bounds on LER, an exact long-path decay rate and a square
information bound. The [CFT review](complex-weights-and-cft.md) states the
conditions for extending these lattice results to critical field theory.

The primary task is to explain the LER curve using the auxiliary statistical
model. Phase classification and decoder improvements are subsequent questions.
This note gives the exact K-integral observable, an all-p closed-form path
example, and a low-p expansion for the actual two-dimensional square patch.
The latter predicts different powers and leading coefficients for directed
and bidirectional errors, without fitting any decoder data. A controlled
moderate-p prediction for the full square curve remains unfinished.

## Evidence

### Exact K integral with a logical twist

Let M be measured vertices and B the unmeasured rough endpoints. Use the
parent incidence convention, with -j at the tail and +j at the head.
Let c_e be 1 on the logical cut and 0 elsewhere. Absolute logical parity is
a=c dot j mod2, identical to c dot |j| mod2 for j=0,+1,-1. Relative logical
labels only permute the two sectors for fixed Q, leaving their minimum unchanged.

Set theta_b=0 for b in B; integrate only measured angles. This implements
absence of a boundary-charge constraint. Integrating boundary angles without
a source would instead impose zero boundary charge and change the problem.
Define phi_e=(D_M^T theta)_e and

\[
K_{p,q}(\phi)=1-p+pq e^{i\phi}+p(1-q)e^{-i\phi}.
\]

For t=0,1 define the untwisted and logical-sign-inserted integrals

\[
A_t(Q)=\int\prod_{v\in M}\frac{d\theta_v}{2\pi}\,
e^{-i\sum_{v\in M}Q_v\theta_v}
\prod_e K_{p,q}(\phi_e+\pi t c_e).
\]

Expanding each K in its three currents, Fourier orthogonality enforces
D_M j=Q; shifting by pi multiplies each cut-crossing active current by -1.
Therefore, exactly,

\[
A_t(Q)=\sum_{j:D_Mj=Q}P(j)(-1)^{t c\cdot j},
\qquad Z_a(Q)=\frac{A_0(Q)+(-1)^a A_1(Q)}2.
\]

Here A0=P(Q)>=0 and A1 is real, although its integral uses complex factors.
A1 is a signed partition sum, not itself a positive sector partition function;
one must not take log(A1) and call it a physical defect free energy. The
conditional logical-parity polarization is m(Q)=A1/A0 when A0>0. Then

\[
r_*(Q)=\frac{1-|m(Q)|}{2},
\qquad
\mathrm{LER}_*(p,q,L)=\frac12\left[1-\sum_Q|A_1(Q)|\right].
\]

On the parent's square the logical cut is precisely the edges entering the
right rough boundary. Thus A1 can equivalently be computed with right
boundary angle pi and left boundary angle zero, whereas A0 fixes both to
zero. This gives the concrete boundary-response interpretation: evaluate
the auxiliary model with and without a pi boundary twist, retaining the
same interior charge sources, then apply the displayed projection and
record average. Separating local boundary and bulk effects is not a
prerequisite for this calculation.

The normalization sum_Q A0=1 follows from the normalized edge prior. The
absolute value is inside the Q sum. Averaging the twist before taking its
absolute value loses exactly the record-dependent information used by optimal
decoding. This is a concrete observable of the K model that produces a full
LER curve; the bulk free energy alone does not determine it.

The prior finite-patch oracle already evaluated the positive-current version
of these sector sums. Thus it was more than repeated practical decoding, but
it did not yet give an analytic explanation of the curve's shape.

### An exactly soluble boundary-to-boundary path

Consider d arrows in a row, all pointing from the left rough endpoint to the
right one, with all d-1 interior charges measured. Write
a=1-p, b=pq, c=p(1-q). Two currents with the same record differ by a constant
along the whole path. Configurations containing both +1 and -1 cannot shift
within the bounded alphabet and are unambiguous. At Q=0 the three constant
currents have sector weights a^d and b^d+c^d. Every nonzero ambiguous record
is a pair: a mixed 0,+1 string and the same string shifted by -1.

For k positive edges in the first string, the two weights are a^(d-k)b^k
and a^k c^(d-k). There are binom(d,k) such records. Summing the smaller weight
over all records gives the exact, all-p formula

\[
\mathrm{LER}^{\rm path}_*(p,q,d)
=\min(a^d,b^d+c^d)
+\sum_{k=1}^{d-1}\binom{d}{k}
\min(a^{d-k}b^k,a^k c^{d-k}).
\]

For q=1 this becomes min((1-p)^d,p^d), or p^d for p<1/2. A fully directed
path's only ambiguity is the empty versus fully occupied path at zero
interior charge. If 0<q<1, partial forward and reverse strings can also
produce the same nonzero record. The leading low-p order is instead
p^ceil(d/2). This is a precise ambiguity mechanism, not an assumption about
vortex proliferation or a fitted transition. The path is an illustrative
geometry; the next argument establishes the exponent on the actual square.

### A low-p theorem on the actual square patch

Fix a finite canonical square with L=d+1 rows and d horizontal steps between
its rough boundaries. Stored horizontal arrows point right, vertical arrows
point in increasing y. Retain full interior charge and the parent's binary
logical cut. For fixed 0<q<1,

\[
\mathrm{LER}_*(p,q,L)=\Theta(p^{\lceil d/2\rceil}),
\qquad p\to0.
\]

At the directed endpoint,

\[
\mathrm{LER}_*(p,1,L)=\Theta(p^d).
\]

Proof of the interior-q exponent: let n_a(Q) be the least number of active
edges among supported configurations in sector a. Since all allowed
orientation weights are positive and independent of p, each sector sum has
leading order p^n_a. Consequently the contribution of Q to LER has order
p^max(n_0,n_1), and the global exponent is the minimum of these maxima.
Any opposite-sector pair j,j' with the same Q has a mod2 difference that
contains a rough-to-rough logical path of length at least d. Its union of
active edges therefore has size at least d, so N(j)+N(j')>=d. This bounds
the exponent below by ceil(d/2). Conversely, split a straight logical path
into floor(d/2) forward edges in j and the remaining reverse edges in j'.
Then j-j' is the full unit path, the interior records agree, and logical
parities differ. Both configurations are supported for fixed interior q;
the lower bound is attained.

Proof of the directed exponent: use the vertex potential x. For k=j-j',
the interior divergence vanishes. Since x=0 and x=d on the two rough
boundaries, discrete summation by parts gives

\[
N_H(j)-N_H(j')
=\sum_e (x_{\rm head}-x_{\rm tail})k_e=d\,F_R.
\]

Here N_H counts active horizontal edges (nonnegative for directed currents),
and F_R is the signed difference of right-boundary flux. Opposite logical
parity forces F_R to be an odd integer, hence its magnitude is at least one.
At least one member of every opposite-sector pair therefore has at least d
active edges. A straight occupied path versus the vacuum attains this bound.
This proof uses the actual square arrows and boundary geometry. It is not a
theorem for arbitrary arrow patterns or for the original honeycomb geometry.

### Leading coefficients from minimal defects

For even d=2m (the parent's odd sizes L=5,7,9), the preceding proof sharpens
to an explicit coefficient at fixed 0<q<1:

\[
\mathrm{LER}_*(p,q,L)
=L\binom{d}{m}\min(q,1-q)^m p^m+O(p^{m+1}).
\]

At this order both competing configurations have exactly m occupied edges.
Their union must be a shortest logical path, hence one of the L straight
rows. Choosing which m edges carry forward current gives binom(d,m)
distinct nonzero charge records per row. The other configuration carries
reverse current on the complement. Their leading weights are q^m and
(1-q)^m; summing the smaller one proves the coefficient. No contractible
decoration fits at this minimal total activity.

For directed noise the coefficient on every canonical size is

\[
\mathrm{LER}_*(p,1,L)
=\binom{2d}{d}p^d+O(p^{d+1}).
\]

To see this, a leading ambiguous pair has one configuration containing d
horizontal edges and no vertical edges, and the other only vertical edges,
with at most d of them. Conservation makes the difference a rightward,
non-increasing-y staircase. There is one horizontal edge per column; their
row sequence is weakly decreasing, length d, with d+1 available rows. There
are binom(2d,d) such sequences. Each nonconstant sequence has a unique
nonzero charge record and a unique matching vertical configuration, and
contributes coefficient one. The L constant sequences share Q=0, whose
odd-sector sum contributes coefficient L. Together these count all leading
ambiguous records, including the ties when the vertical string also has d
edges. The coefficient is a defect multiplicity, not a fit parameter.

| Square size | Fair q=1/2, first term | Directed q=1, first term |
| --- | --- | --- |
| L=5, d=4 | (15/2) p^2 | 70 p^4 |
| L=7, d=6 | (35/2) p^3 | 924 p^6 |
| L=9, d=8 | (315/8) p^4 | 12870 p^8 |

Thus direction changes both the minimal activity order of ambiguous logical
defects and their statistical weight. In a low-p expansion these are the
energy order and the multiplicity/orientation factor controlling LER. This
is a statistical-mechanics explanation of the low-noise curve, independent
of BP convergence. It is not a calculation of the moderate-p region: many
higher-order defects and their correlations contribute there.

The expansion is at fixed L and fixed q. The interior coefficient tends to
zero as q approaches one for even d, and higher orders can dominate long
before the endpoint. Taking q to one and extracting the leading power in p
are not interchangeable operations. No uniform large-L or near-endpoint
approximation is asserted.

### Certified finite-activity extension

A direct positive-current expansion replaces the leading-term heuristic by a
rigorous interval. Let Z_a^(k)(Q) contain every current configuration with at
most k nonzero edges, and set

LER_k = sum_Q min(Z_0^(k)(Q),Z_1^(k)(Q)).

All omitted sector weights are nonnegative. If the square has E edges, their
total mass is the binomial tail T_k=Pr[Binomial(E,p)>k], hence

LER_k <= LER <= min(1/2, LER_k+T_k).

The registered exhaustive check reproduces four exact L=3 values within
5.6e-16. For L=5 and k=4, the certified absolute widths are .00041055 at
p=.02 and .02035390 at p=.05 for every q in {.5,.75,.97,1}. The p=.02 lower
bounds already differ from the leading monomial for interior q, resolving
subleading contributions without a fit. At p=.08 the width grows to .10848909,
so blind support-order extension is stopped there. The next method must resum
repeated local activity, through connected polymers or a positive transfer
representation, rather than merely increasing k. See the
[machine-readable activity result](../results/current-activity-expansion-2026-09-18.json).

The first positive-transfer alternative has also been tested and rejected.
It sums every pair of physical current configurations with the same measured
charge and odd relative logical parity, weighted by sqrt(P0 P1). This is an
exact 1,250-state-frontier contraction of a positive relative-defect gas and
an upper bound on LER, but the configuration-level relaxation is too loose:
at p=.08 its capped bounds are .5,.5,.5,.26273 for q=.5,.75,.97,1, all above
the activity bounds .13836,.12506,.11404,.10877. It improves none of the
eight frozen cells. The next representation must contract sector-level
Hellinger/total-variation information or use a genuinely controlled connected
cluster expansion; merely summing configuration pairs loses too much posterior
competition. [Pair-transfer result](../results/positive-defect-transfer-2026-09-18.json).

Keeping competition at the record-sector level does not yet solve the global
remainder. The truncated Hellinger coefficient was combined with exact omitted
even/odd logical masses using Cauchy bounds. This construction passes exact L=3
gates, but at p=.08 gives .42049,.40883,.37181,.35756, again above every
activity upper bound. It improves zero cells and is rejected. The failure
identifies the problem precisely: allocating only total omitted sector mass
forgets which charge records receive it. The next bounded test must exploit
local connected structure rather than another global mass relaxation.
[Sector-Hellinger result](../results/sector-hellinger-remainder-2026-09-18.json).

### A controlled Wiener cumulant representation

The local kernel itself admits a stronger, q-uniform representation for every
p<1/2. Write z=p/(1-p) and

K=(1-p)(1+zS),  S=q exp(i phi)+(1-q)exp(-i phi).

In the Wiener algebra of absolutely summable Fourier coefficients, ||S||=1.
Truncating log(1+zS) after N connected cumulants leaves norm
r_N=sum_{n>N}z^n/n. For E edges, exponentiation gives

||F-F_N||_A <= exp(E r_N)-1.

Logical twists preserve this norm and charge projection is l1-contractive, so

|LER_N-LER| <= [exp(E r_N)-1]/2.

This bound controls the full absolute-value LER functional, unlike the two
failed global mass relaxations. On the E=32 L5 square it reaches absolute
error <=.001 uniformly in q with N=3 at p=.08 and p=.10, and N=10 at p=.30.
At p=.46 the same target needs N=48. Deterministic phase-grid checks satisfy
the analytic scalar and product bounds to 1.1e-14. This is a representation
theorem, not yet a computed L5 LER: the next contract must approximate
exp(P_N) by finite harmonics with its own Wiener tail and contract the twisted
charge coefficients. [Cumulant feasibility result](../results/wiener-cumulant-feasibility-2026-09-19.json).

The feasibility result also exposes a correction to the implementation plan:
the physical K is already exactly finite harmonic, with only 0,+1,-1 current
coefficients. Replacing it by finite harmonics of exp(P_N) would increase the
local alphabet without solving the difficult operation, which is the l1 norm
over all public charge records.

An exact physical-kernel transfer therefore tested nested coarse observations
instead. Observing 7 of the 15 L5 charges produces 823,323 records and
1,646,646 peak states, but its p=.08 upper bounds remain
.22637,.21231,.17179,.15751, all above the activity bounds. The registered
9-charge step reaches 5,461,398 states and fails the two-million-state cap.
This branch is stopped without inference about the unrun 9--15 charge levels.
The remaining computational question is a scalable exact or certified l1
contraction: a tensor/decision diagram or branch-and-bound must merge charge
records without discarding the sector competition that defines LER.
[Charge-prefix result](../results/exact-charge-prefix-transfer-2026-09-19.json).

Adaptive refinement does recover information value without keeping all charge
records. At each detector, a decision diagram retains only the B prefixes with
largest current Bayes-risk contribution; discarded prefixes contribute their
exact coarse-information upper bound, including analytic convolution of all
unassigned logical-cut parities. L=3 no-prune runs reproduce exact LER.

For L5,p=.08, B=1024 reduces certified interval width by 24.95% at q=.97 and
30.69% at q=1, giving upper bounds .08697 and .07547. It improves q=.75 by
only 5.05% and q=.5 not at all, so those cells are not promoted. Every B=4096
run exceeds the two-million pre-prune-state cap (2.23--2.90M) and is censored,
not extrapolated. The next bounded question is whether a different deterministic
priority or structured merge can capture value of future charge information
for fair/intermediate bias without raising B.
[Adaptive branch result](../results/adaptive-charge-branch-bound-2026-09-19.json).

One alternative priority has now exhausted the priority-only branch. Instead
of current risk mass, it ranks prefixes by the maximum reduction available if
the frontier currents were revealed. At B=1024 this lowers the fair upper bound
from .14143 to .13553, only a 2.61% activity-interval reduction, and gives a
worse q=.75 bound than the original risk priority. Neither cell passes the
registered 10% gate. The next bounded method must merge structurally equivalent
frontier/charge states with a certified error; testing further heuristic
priorities or increasing B is not supported.
[Frontier-value result](../results/frontier-value-branch-bound-2026-09-19.json).

The single registered structured merge is also complete. It coarsens charge
histories by last charge, preferred-sector sign and a deterministic posterior
log-odds bin, while propagating frontier currents exactly. Because this label
is a deterministic coarsening of the public record, its Bayes risk remains a
certified upper bound. With 64 bins it uses only 178--213 final labels and
about 11.7k peak states. The fair interval shrinks by 8.11%, just below the
10% gate, and q=.75 does not improve. No run is resource-censored.

This closes the registered contraction refinements: low-p activity intervals
and near-directed adaptive bounds are retained, while fair/intermediate
p=.08 and above remain unresolved.
[Posterior-bucket result](../results/posterior-bucket-merge-2026-09-19.json).

### Evidence boundary against the exact oracle

The registered synthesis places the deterministic L5 certificates beside the
existing exact-posterior Monte Carlo anchors without fitting or interpolation.
All four biases are controlled through p=.05. At p=.08, only q=.97 and q=1
use promoted B=1024 upper bounds; q=.5 and q=.75 retain the broad activity
intervals. The posterior Monte Carlo points at p=.10,.30,.46 (and q=.97 at
p=.30) show the moderate-p target but do not analytically continue the
partition expansion or shrink its deterministic remainder.

![Certified prediction and oracle anchors](../figures/partition-oracle-evidence-boundary.png)

The shaded fair/intermediate p>=.08 region is therefore an explicit unresolved
set, not a confidence band or a phase region. The plot contains no connecting
curve, threshold, crossing, pooled interval or monotonicity assumption.
[Machine-readable synthesis](../results/partition-oracle-synthesis-2026-09-19.json).

### Validation and source context

The [finite checks](../results/analytic-partition-bridge-2026-09-18.json)
compare the path formula to 72 independent exhaustive cases (error below
3e-17). A 9-point-per-angle Fourier quadrature is exact for square L3's
bounded charge harmonics: it recovers both twist coefficients for all 357
supported records to below 1e-16, and reproduces LER=.3865665182 at p=.30,
q=.75. Low-activity enumeration at square L3,L4,L5 verifies the predicted
exponents and applicable coefficients, including intermediate q=.75,.97.
The arbitrary-size statements rest on the proofs above, not these tests.

The directed coefficient was conjectured after initial finite counts and
then derived by the staircase count; this is recorded as an exploratory
theory extension in the [manifest](../manifests/analytic-partition-bridge-2026-09-18.json).
No production decoder samples were used to fit these formulas.

[Dennis et al.](https://arxiv.org/abs/quant-ph/0110143) provides the broader
homology-sector statistical-mechanics framework.
[Temkin et al.](https://arxiv.org/abs/2512.22119) studies charge-informed
optimal decoding and a statistical transition in another U(1) noise model.
Neither source supplies the bounded-current path formula or the square
coefficients derived here; no phase classification is imported from them.

## Status

The K-to-LER observable, exact path curve and canonical-square dilute-limit
prediction are established within the stated assumptions. They directly
address what was missing from a purely numerical sector-risk comparison.
The full moderate-p two-dimensional curve is still not analytically solved.
The targeted [non-perturbative method audit](nonperturbative-method-audit.md)
finds that scalar polymer, spatial-mixing, zero-free and MPS results do not
control the required public-record l1 norm. The only reviewed route that
preserves the estimand is the physical even-moment hierarchy. Its next step is
a no-new-sampling degree-versus-width feasibility matrix, not a curve claim;
existing exact-posterior anchors remain validation evidence, not fit targets.
Decoder optimization, bulk/boundary interventions and phase classification
are secondary to that task.

A logical-sector insertion can be represented as a change of boundary
condition or a nontrivial defect across the block. Its statistical cost
includes configurations through the entire block. Calling the observable a
boundary response does not imply a microscopic boundary-only origin, or
remove the need to calculate its partition function.

## Related pages

- [Sector predictions and the LER connection](sector-predictions.md)
- [Direction-biased U(1) current channel](direction-biased-u1-current-channel.md)
- [Finite numerical mechanism results](mechanism-results.md)
- [Research plan](../PLAN.md)
