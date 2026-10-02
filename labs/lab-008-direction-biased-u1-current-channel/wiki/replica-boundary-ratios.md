---
title: Replica boundary ratios and logical error
status: current
updated: 2026-09-18
---

# Replica boundary ratios and logical error

## Summary

There is an exact statistical observable whose ordering is equivalent to
vanishing optimal logical error. It is the **physical second moment of the
logical twist ratio**, not the ratio of two disorder-averaged partition sums.
We derive its replicated lattice model, rigorous LER bounds, and a convergent
moment expansion for the full LER. An exactly soluble path also gives a
rigorous lower bound on the actual two-dimensional square curve.

These are lattice results for this channel. A two-dimensional conformal
fixed point and its critical noise probability have not been identified.
The [companion theory review](complex-weights-and-cft.md) explains how to
make that identification and what a CFT calculation could then determine.

## Evidence

### Physical record and boundary conventions

Let a=1-p, b=pq, c=p(1-q), and let D contain -1 at an edge's tail and +1 at
its head. M denotes measured vertices; rough endpoints are unmeasured.
The cut vector ell selects the right logical boundary. For t=0,1 define

\[
K(\phi)=a+b e^{i\phi}+c e^{-i\phi},
\]
\[
A_t(Q)=\int\prod_{v\in M}\frac{d\theta_v}{2\pi}\,
 e^{-iQ\cdot\theta}\prod_e K((D_M^T\theta)_e+\pi t\ell_e).
\]

Angles at auxiliary rough endpoints are zero. A right-boundary shift by pi
implements t=1. This is binary parity, not an unrestricted integer winding.
With Z0,Z1 the positive joint sector probabilities,

\[
A_0=Z_0+Z_1=P(Q),\qquad A_1=Z_0-Z_1,\qquad m(Q)=A_1/A_0.
\]

A1 is real but can be negative: it is a signed twist amplitude, not a positive
partition function. Only records with A0>0 enter conditional expressions.
The already derived optimal risk is

\[
\mathcal R\equiv\mathrm{LER}_*
=\frac12\mathbb E_{Q\sim A_0}[1-|m(Q)|].
\]

### A rigorous order parameter for correctability

Define the even moments under the physical record law:

\[
M_{2k}=\sum_{Q:A_0>0}A_0(Q)m(Q)^{2k},\qquad M_0=1.
\]

For two independently sampled posterior logical sectors at the same Q, the
mean probability of disagreement is (1-M2)/2. A planted true current and
one posterior sample give the same value: conditioned on Q, both have the
same posterior law. This is a matched-inference replica identity.

For x=|m| between zero and one, 1-x <= 1-x^2 <= 2(1-x). Therefore

\[
\boxed{\frac{1-M_2}{4}\ \leq\ \mathcal R\ \leq\ \frac{1-M_2}{2}.}
\]

Consequently, along any matched sequence of growing graphs,

\[
\mathcal R_L\longrightarrow0\quad\Longleftrightarrow\quad M_{2,L}\longrightarrow1.
\]

This identifies an exact statistical-mechanics criterion for the optimal
decoding region. If a critical boundary exists, these two definitions give
the same boundary. It proves neither that a transition exists nor that there
is a unique p_c. When 1-M2 tends to zero, its power-law or exponential decay
rate is also that of LER up to bounded factors. M2 alone generally does not
determine a nonzero critical LER amplitude.

### The replicated partition functions to calculate

For integer R>=2k, give 2k copies a pi cut twist and leave the others untwisted:

\[
\mathcal Z_R^{(2k)}=\sum_Q A_1(Q)^{2k}A_0(Q)^{R-2k},
\qquad \mathcal Z_R^{(0)}=\sum_Q A_0(Q)^R.
\]

Equivalently the numerator is sum A0^R m^(2k); this expression extends to
real R near one without zero-probability ambiguities on a finite graph.
The physical moment is exactly

\[
\boxed{M_{2k}=\lim_{R\to1}\frac{\mathcal Z_R^{(2k)}}{\mathcal Z_R^{(0)}}.}
\]

Writing R=1+n gives the usual zero-extra-replica limit n->0. The extra one
comes from the physical weight P(Q)=A0(Q). This finite-sum continuation is
defined explicitly; continuing only an integer-replica field theory remains
a substantive problem. Taking R->1 and the thermodynamic limit cannot be
interchanged without justification.

Summing the common integer Q in the Fourier representation imposes
sum_a theta_v^a=0 modulo 2pi at each measured vertex. Eliminate the last
angle. With phi_a=(D^T theta^a)_e, the exact untwisted local weight is

\[
W_R(\phi_1,\ldots,\phi_{R-1})
=\left[\prod_{a=1}^{R-1}K(\phi_a)\right]
 K\!\left(-\sum_{a=1}^{R-1}\phi_a\right).
\]

Marked copies receive the cut shifts before evaluating this product. Thus
the required ratios are boundary-defect partition functions of an explicit
local replicated lattice model. R>=3 weights can still be complex; the
underlying constrained current sum has nonnegative weights.

### The exactly real double-copy model and its limitation

For R=2, phi_2=-phi_1, and the untwisted weight reduces to

\[
G_2(\phi)=|K(\phi)|^2=C_0+2p(1-p)\cos\phi
 +2p^2q(1-q)\cos2\phi,
\]
\[
C_0=(1-p)^2+p^2[q^2+(1-q)^2].
\]

This is a real nonnegative generalized rotor weight; it can have zeros.
Twisting both copies changes it to G2(phi+pi ell). At q=1 the second harmonic
vanishes. It is a useful exact starting point for transfer or dual methods.
It is not an exponential nearest-neighbor XY weight.

Crucially, its ratio is sum A1^2 / sum A0^2. It weights records by A0^2,
whereas M2 weights them by A0. A small exact example shows the distinction:

| Square L=3, p=.30, q=.75 | Value |
| --- | --- |
| Physical M2 | 0.064087819 |
| R=2 annealed partition ratio | 0.094612980 |
| Exact optimal LER | 0.386566518 |
| LER interval from physical M2 | [0.233978045, 0.467956091] |

One cannot infer the physical decoding threshold from this clean R=2
model without controlling the replica continuation.

### Reconstructing the full LER from partition ratios

Let B_k=E[(1-m^2)^k]. The binomial expansion of sqrt(1-y), y=1-m^2, gives

\[
\mathcal R=\frac12\sum_{k=1}^{\infty}a_k B_k,
\qquad a_k=\frac{\binom{2k}{k}}{4^k(2k-1)},
\]
\[
B_k=\sum_{j=0}^{k}(-1)^j\binom{k}{j}M_{2j}.
\]

Every term a_k B_k is nonnegative. If S_N is the first N terms, then

\[
0\leq\mathcal R-S_N
\leq\frac{\binom{2N}{N}}{2\,4^N}\,B_{N+1}
\leq\frac{\binom{2N}{N}}{2\,4^N}.
\]

The tail identity follows by summing the binomial coefficients; y^k<=y^(N+1)
for k>N gives the sharper bound. Monotone convergence includes m=0. This
is a controlled route from a hierarchy of replicated boundary ratios to
the **whole** LER, including a critical value at fixed shape if those ratios
are known there. It converges slowly near maximally ambiguous records;
high-order alternating moment combinations need numerical care.

For the exact example above, eight terms give [0.356755665,0.416124252],
containing 0.386566518. This illustrates a certified interval, not an efficient
solution of the large two-dimensional model.

### An exactly soluble long-path limit

Consider d forward-oriented edges joining two unmeasured endpoints, with
every interior charge observed. For 0<p<1/2 the exact path formula simplifies to

\[
\mathcal R_d=\sum_{k=0}^{d}\binom dk
 \min\{a^{d-k}b^k,\ a^k c^{d-k}\}.
\]

This is the overlap of two product weights (a,b) and (c,a). To derive the
large-d rate, use min(X,Y)<=X^s Y^(1-s) for 0<=s<=1, giving an exponential
upper bound on the overlap. A type k/d has entropy H(k/d); maximizing its
entropy plus the smaller log weight gives a matching lower exponential rate.
Concavity in type and affinity in s allow the max/min interchange. Polynomial
type-counting factors do not contribute to the rate. Hence for 0<q<1,

\[
\boxed{\tau(p,q)=-\lim_{d\to\infty}\frac1d\log\mathcal R_d
=-\log\min_{0\leq s\leq1}
 [a^s c^{1-s}+b^s a^{1-s}].}
\]

The minimization includes endpoints. At fair bias symmetry fixes s=1/2;
the directed endpoint is solved with its supported alphabet separately:

\[
\tau(p,1/2)=-\tfrac12\log[2p(1-p)],\qquad
\mathcal R_d(p,1)=p^d,\qquad\tau(p,1)=-\log p.
\]

At p=.30, tau is 0.433750, 0.470264, 0.634815, 1.203973 for
q=.5,.75,.97,1. These are predictions from the partition weights, with no
decoder fit. All are positive: this path limit has exponentially vanishing
LER throughout this p range. It is not the fixed-aspect-ratio square limit.

### A rigorous two-dimensional bound from that solution

On the canonical L by L square, reveal every vertical current to the decoder.
Subtracting their contributions from Q leaves L independent horizontal paths,
each of length d=L-1. The total logical parity is the XOR of their parities,
so its posterior magnetization is the product of the path magnetizations.
The revealed information cannot increase Bayes risk. Independence therefore gives

\[
\boxed{\mathrm{LER}_{*,\mathrm{square}}(L,p,q)
\ \geq\ \frac{1-[1-2\mathcal R_{L-1}(p,q)]^L}{2}.}
\]

This holds with the full path formula at any physical p,q. The simplified
path sum above is used only for p<1/2. For even d and fixed interior q,
its leading dilute term equals the already derived square coefficient
L binom(d,d/2) min(q,1-q)^(d/2) p^(d/2). At q=1 it gives only L p^d:
the larger true coefficient binom(2d,d) includes paths with vertical steps
whose uncertainty this extra-information oracle has removed.

This connects an exact lower-dimensional solution to the actual square LER
curve. Its large-L limit is a vanishing lower bound, so it does not locate a
two-dimensional transition.

### Independent checks and provenance

The [registered investigation](../manifests/replica-boundary-theory-2026-09-18.json)
separates the above exact statements from conditional CFT interpretations.
The square information bound was derived during analysis and registered as
an extension before its finite check. The
[reproducible check](../scripts/check_replica_boundary_theory.py) verifies:

- Twelve channel points on all square L3 records, physical moment bounds,
  the square information bound and the positive moment series.
- R2 square and R3 two-edge-path integrals against independent current sums;
  maximum absolute error 5e-16 using exact finite Fourier quadrature.
- Convolution spectra and both R2 harmonics; 1,001 pointwise series tests.
- Exact log-domain path sums through d=2048 versus the independently
  minimized rate; final discrepancies below .01 per edge in every case.

The [machine-readable result](../results/replica-boundary-theory-2026-09-18.json)
contains all values and source hashes. The analytic proofs establish the
identities and limits; these finite calculations check signs, normalization
and implementation. No new decoder simulation enters this investigation.

## Status

Exact replica identities, LER bounds, moment reconstruction, long-path rate
and square information bound are derived and checked. Evaluating physical
replica ratios in the two-dimensional thermodynamic limit remains open.
The companion note now derives integer-replica compactification and vortex
charges and solves a conditional Gaussian replica annulus. Its registered
control investigation rejects the naive bare calibration: vortex fugacities,
renormalized stiffness and the R->1 continuation are not fixed by the integer
Gaussian model. These must be derived before assigning
a universality class or importing a CFT spectrum.

## Related pages

- [Complex weights, replica field theory and boundary CFT](complex-weights-and-cft.md)
- [Auxiliary partition function and dilute square prediction](partition-function-ler.md)
- [Sector predictions and LER](sector-predictions.md)
- [Research plan](../PLAN.md)
