---
title: Thermodynamic decoding theory
status: current
updated: 2026-09-23
---

# Thermodynamic decoding theory

## Summary

The researcher's correction is methodological: increasing L from 7 to 9 to
11 to 13 has become a substitute for specifying an infinite-size theory.
Further size acquisition and contraction optimization are stopped. The
existing calculations remain useful exploratory evidence, but are not the
active research deliverable.

The question is now: **which size-uniform properties of the physical logical
interface make optimal LER vanish or remain positive, and how does direction
bias change those properties?** The family includes the undirected lattice
model: no preferred edge direction, with signed integer charge still measured.
Keep p, q, the bias pattern when present, and aspect ratio fixed before taking L to infinity. This is a thermodynamic limit, not a
time-dependent dynamical limit.

The researcher explicitly confirmed that "undirected" does not discard the
sign of charge, and identified the continuous control as the effective
electric field on each link. Integer charge remains quantized at every field.
The zero-field model is a primary thermodynamic reference,
not merely a control for the fully directed endpoint. The endpoint-specific
transport results below retain their stated scope and do not settle this
zero-bias theory or the relevance of an infinitesimal bias.

The current results below are exact reformulations and conditional lemmas.
They do not solve the square transition. The main unresolved mathematical
step is a bound on the boundary-flux measure after regions are glued, strong
enough to control sector-weight cancellations at all sizes.

## Evidence

### Undirected lattice model and continuous direction bias

Use an undirected underlying graph. An active edge deposits charges +1 and
-1 at its endpoints, with either assignment equally likely in the undirected
model. The orientation of that pair is hidden; signed vertex charges Q are
observed. This is exactly Lab 006's existing hidden-fair U(1) channel, not
a new absolute-charge measurement model.

Choose reference arrows only to write an incidence matrix D and currents j.
Use a dimensionless link field h as the primary parameter, with
b=tanh(h)=2q-1 as an equivalent bounded bias. The continuous family has probabilities

\[
w_b(0)=1-p,\qquad
w_b(+1)=\frac p2(1+b),\qquad
w_b(-1)=\frac p2(1-b),\qquad -1\le b\le1.
\]

| Link field and bias | Physical meaning |
| --- | --- |
| h=0, b=0, q=1/2 | Undirected lattice model: no preferred edge direction |
| Finite nonzero h, 0<abs(b)<1 | Both assignments occur with a directional preference |
| h tends to positive or negative infinity, b tends to +1 or -1 | Only one assignment occurs, relative to a specified preferred-arrow pattern |

The field convention is fixed by the orientation odds, not by assigning a
continuous value to the charge:

\[
q(h)=\frac{e^h}{e^h+e^{-h}}=\frac{1+\tanh h}{2},\qquad
\frac{P(j=+1\mid |j|=1)}{P(j=-1\mid |j|=1)}=e^{2h}.
\]

Thus w_h(0)=1-p and w_h(plus or minus 1)=p exp(plus or minus h)/(2 cosh h).
The edge jump j remains in {0,+1,-1} and Q=D_M j remains a signed integer
vector. The field changes probabilities, not the elementary charge magnitude.
Here h is an external/effective bias parameter, not a dynamical quantized
rotor flux. Relating it to a laboratory electric field and temperature would
require a microscopic noise-generation model.

The underlying adjacency does not change as b changes. Nonzero bias specifies
extra physical edge data; a reference arrow alone specifies no physical data.
For a general pattern write b_e in the chosen edge coordinates.

**Reference-arrow invariance (exact, all sizes).** Let S be any diagonal
matrix of edge signs. Relabel D'=DS, j'=Sj and b'=Sb. Then D'j'=Dj and
the binary activity and logical parity are unchanged. Each edge probability
is also unchanged, so every physical sector probability Z_a(Q), and hence
LER, is invariant. At b=0 no parameter changes under any reference reversal.
This proves that a current representation is compatible with an undirected
physical model; it does not impose a preferred direction.

The corresponding Fourier edge factor is exactly

\[
K_b(\phi)=1-p+p\cos\phi+i p b\sin\phi.
\]

At b=0 it is real and even. The full fixed-charge integral still contains
exp(-i Q dot theta), and K_0 can be negative for p>1/2; this alone does not
identify a clean positive XY model or a continuum universality class.
The positive-current representation remains valid throughout the family.

At interior p and |b|<1 its single-edge potential has parameters

\[
V_b(j)=t_b|j|-h_bj,\qquad
t_b=\log\frac{2(1-p)}{p\sqrt{1-b^2}},\qquad
h_b=\operatorname{artanh}b.
\]

Equivalently, at fixed total jump probability p,

\[
V_h(j)=\tau(p,h)|j|-hj,\qquad
\tau(p,h)=\log\frac{2(1-p)\cosh h}{p}.
\]

The h-dependent activity term is necessary: the original channel fixes p
while varying orientation. Holding tau fixed instead would give
p(h)=2 exp(-tau) cosh(h)/(1+2 exp(-tau) cosh(h)), a different path through
the statistical-mechanical parameter space. The lab uses the fixed-p path.

Thus a small bias first adds a signed-current field, while the symmetric
activity cost changes at second order. For a gradient bias field the linear
tilt can move into charge-source and rough-boundary factors; those factors
must be retained in the physical sector ratios. A bulk RG perturbation is
not inferred just from the imaginary sine term.

**Global bias reflection (exact, all sizes).** The transformation j to -j
sends Q to -Q and b_e to -b_e, while preserving binary logical parity. Hence
Z_a(Q;b)=Z_a(-Q;-b) and R_L(p,b)=R_L(p,-b) for a fixed pattern with scalar
amplitude b. Any limiting correctable set has the same reflection symmetry.
This does not prove monotonic improvement with |b|. Evenness also does not
guarantee differentiability of LER, because it includes a sector minimum.

**Thermodynamic question.** First characterize the zero-field model at fixed
p. Then determine whether an infinitesimal field changes its long-distance
logical-defect statistics, and whether the directed endpoint connects to it
smoothly or through a distinct regime. If a critical fixed point exists,
the relevance, irrelevance or marginality of bias is a question to derive,
not an assumption. The fixed-charge posterior, rough boundaries and physical
record average must survive any effective-field-theory reduction.

### Exact zero-field response and the finite-volume cusp

The fixed-`p` path has an exact response representation. For
`J(j)=sum_e j_e` along the physical bias pattern and
`N(j)=sum_e |j_e|`, every record and sector obeys

\[
 Z_a(Q;h)=Z_a(Q;0)\,
 \mathbb E_{0\mid Q,a}\!\left[e^{hJ-N\log\cosh h}\right]. \tag{H1}
\]

The activity term in (H1) is essential: deleting it changes the total jump
rate. Writing `Delta_Q=log(Z_0/Z_1)` gives the exact derivatives

\[
 \Delta'_Q(0)=\mathbb E_0[J\mid Q]-\mathbb E_1[J\mid Q], \tag{H2}
\]
\[
 \Delta''_Q(0)=\operatorname{Var}_0(J\mid Q)-\operatorname{Var}_1(J\mid Q)
 -\mathbb E_0[N\mid Q]+\mathbb E_1[N\mid Q]. \tag{H3}
\]

Thus the zero-field ensemble needed for bias response is the
sector-conditioned joint law of signed field current `J`, activity `N`, and
charge `Q`, not merely an activity density or a clean rotor stiffness.

There is also an exact warning about symmetry. Let
`D_Q(h)=Z_0(Q;h)-Z_1(Q;h)`. Since the channel is normalized,

\[
 R_L(h)=\frac12\left(1-\sum_Q |D_Q(h)|\right). \tag{H4}
\]

Reflection pairs cancel all linear terms from records with `D_Q(0) != 0`,
but zero-field ties can split immediately:

\[
 R'_L(0+)=-\frac12\sum_{Q:D_Q(0)=0}|D'_Q(0)|. \tag{H5}
\]

Therefore `R_L(h)=R_L(-h)` does not imply quadratic response; finite-volume
Bayes risk may have a downward `|h|` cusp. Exact rational replay on the
existing L3 square enumerates all 6561 currents with zero normalization,
reflection, or derivative-cancellation failures. At `p=3/10`, 182 of 357
charge records are tied, `R_3(0)=882351/2000000`, and
`-R'_3(0+)=151263/1000000`. At `p=1/2`, the corresponding values are
`63/128` and `3/64`. The largest absolute recordwise gap slope is exactly two
in both controls.

For a gradient field `A=d psi`, the signed tilt is the full charge pairing
`sum_v psi_v Q_v`. The measured interior contribution is fixed within a
record, but rough-boundary charges remain unmeasured and summed, so the field
survives precisely as a boundary fugacity in sector ratios. Equations
(H1)--(H5) retain that factor rather than gauging it away.

Thermodynamic relevance is not decided by these finite controls. The exponent
`hJ-N log cosh h` is extensive, and fixed `h` before `L` grows need not agree
with `h` tending to zero first. A valid next theorem must control the
size-dependent conditional cumulant-generating functions and the tied-record
cusp mass in (H5). [Exact response result](../results/zero-field-infinitesimal-response-2026-09-22.json).

### A universal shrinking-field window, but no fixed-field TV route

The independent-edge channel gives an exact size-dependent control without
assuming a continuum theory. For `E` edges,

\[
D(P_0^E\Vert P_h^E)=Ep\log\cosh h,
\qquad
D(P_h^E\Vert P_0^E)=Ep\,[h\tanh h-\log\cosh h]. \tag{H6}
\]

Let `kappa(h)` be the smaller of the two bracketed per-active-edge factors.
The map from a full current to `(Q,H)` is deterministic, Bayes error is
one-Lipschitz in joint total variation, and Pinsker therefore gives

\[
 |R_L(h)-R_L(0)|
 \le \min\!\left\{1,\sqrt{\frac{Ep\,\kappa(h)}2}\right\}. \tag{H7}
\]

Since `kappa(h)=h^2/2+O(h^4)`, equation (H7) also bounds the cusp in (H5):
`-R'_L(0+) <= sqrt(Ep)/2`. More importantly, every graph sequence with
`h_L sqrt(E_L) -> 0` has `R_L(h_L)-R_L(0) -> 0` uniformly. On a
fixed-aspect two-dimensional patch, `E_L` is of order `L^2`, so
`h_L=o(1/L)` is a rigorous perturbative window. This is a statement about
simultaneous limits; it does not say that a fixed nonzero `h` is irrelevant.

The same calculation proves why full-law comparison stops there. The
single-edge Hellinger affinity is

\[
 \alpha(p,h)=1-p+p\,\frac{\cosh(h/2)}{\sqrt{\cosh h}}. \tag{H8}
\]

For every fixed `p>0` and `h!=0`, `alpha<1` and
`TV(P_0^E,P_h^E) >= 1-alpha^E -> 1`. Thus the complete current laws become
asymptotically distinguishable, even though the decoded observable could in
principle remain stable. A fixed-field thermodynamic theorem must exploit the
charge/sector map or boundary structure rather than proximity of the full
product laws.

Exact replay on the existing L3 square at `p=.30`, `h=.10,.50` verifies both
KL formulas and the Hellinger product formula to `2.87e-14`, and verifies
`|Delta R| <= TV(Q,H) <= TV(j) <=` the Pinsker bound in both cells. No new
size or sample is used. [Window theorem and obstruction](../results/zero-field-field-window-bound-2026-09-22.json).

### Exact pure-gradient rough-charge generator and its pointwise limit

For the canonical square arrows, take `psi(x,y)=x+y`. Every retained edge
has `psi(head)-psi(tail)=1`. At fixed physical `p`, define

\[
 p_*={p\over p+(1-p)\cosh h},\qquad
 c={p+(1-p)\cosh h\over\cosh h}.
\]

The edge identity `w_{p,h}(j)=c w_{p_*,0}(j)e^{hj}` holds separately for
`j=0,+1,-1`; thus it preserves the fixed-`p` channel, rather than silently
holding the activity fixed. Incidence summation gives
`sum_e j_e=sum_v psi_v Q_v`. Write `M(Q)=sum_{interior} psi_v Q_v` for the
measured part and `B(Q_rough)=sum_{rough} psi_v Q_v` for the hidden part.
Then, exactly at every finite `L`,

\[
 Z_a(Q;p,h)=c^E e^{hM(Q)}
 \sum_{Q_{\rm rough}}e^{hB(Q_{\rm rough})}
 Z_a(Q,Q_{\rm rough};p_*,0). \tag{H9}
\]

The common measured factor cancels in `Z_0/Z_1`: fixed-field sector response
is a ratio of **sector-conditioned rough-charge generating functions at
`p_*`**, not a gauge removal of the field at the original `p`. The activity
shift `p_*<p` for `h!=0` is inseparable from that exact reduction.

A pointwise size-uniform rough-fugacity bound is false. With measured `Q=0`,
the all-zero current has `B=0`, while a complete positive horizontal row has
`B=L-1` and switches logical parity. Their rough-fugacity factors differ by
`e^{h(L-1)}`; the larger forward/inverse ratio is `e^{|h|(L-1)}`. This is a
configuration-level counterfamily. It **does not** show that the summed
sector generating functions have an unbounded ratio or that Bayes risk has a
particular thermodynamic limit. The next theorem must control their
physical-record average or conditional boundary distribution. Existing L3
controls at `p=.30`, `h=.10,.50` replay all 6561 states per cell with maximum
sector-sum discrepancy `9.72e-17`; no new size or sample was used.
[Exact result and scope](../results/pure-gradient-rough-boundary-generator-2026-09-22.json).

### The physical average cannot discard measured charge or the absolute value

The right rough vertices have degree one; their incident edges are exactly the
logical cut. Since `j mod 2 = |j| mod 2`, sector `H` equals total right rough
charge modulo two. This gives two different all-size averages of (H9):

\[
 \sum_Q[Z_0(Q;p,h)-Z_1(Q;p,h)]
 =\mathbb E_{p,h}(-1)^H=(1-2p)^L, \tag{H10}
\]

independent of `h`, because each right-cut occupancy is Bernoulli `p`. By
contrast, remove the measured factor `c^E e^{hM(Q)}` and average the signed
boundary generators `F_a(Q)=\sum_{Q_{rough}}e^{hB}Z_a(Q,Q_{rough};p_*,0)`.
Independence of zero-field boundary edges yields exactly

\[
 {\sum_Q(F_0-F_1)\over\sum_Q(F_0+F_1)}
 =\prod_{y=0}^{L-1}
 {1-p_*-p_*\cosh[h(L-1+y)]\over
  1-p_*+p_*\cosh[h(L-1+y)]}. \tag{H11}
\]

For every fixed `0<p<1` and finite `h!=0`, (H11) tends in magnitude to one,
with eventual sign `(-1)^L`: once all numerators are negative,
`1-|H11| <= 2L(1-p_*)/[p_* cosh(|h|(L-1))]`. In stark contrast, the true
global signed parity contrast (H10) tends to zero. The measured factor is
therefore essential **after** physical-record averaging even though it
cancels from every fixed-record sector ratio.

Neither signed average is the decoding observable. Exactly,

\[
 1-2R_L(p,h)=\sum_Q|Z_0-Z_1|
 =c^E\sum_Q e^{hM(Q)}|F_0(Q)-F_1(Q)|. \tag{H12}
\]

The absolute value must stay inside the physical-record sum. In the two
existing L3 controls at `p=.30`, the signed physical contrast is `0.064` at
both `h=.10,.50`, while the absolute contrasts are `0.14441` and `0.22020`.
All formula errors are at most `1.12e-15`; no new size or sample was used.
Thus boundary-only averaging and signed averaging are both rejected as
thermodynamic shortcuts. A size-uniform bound or counterfamily for (H12)
remains open. [Exact proof and controls](../results/rough-charge-physical-average-cancellation-2026-09-22.json).

### A certified square wedge for the physical absolute contrast

The existing physical connected-current path theorem already bounds (H12)
in a nonempty region; expressing it in the *correct* absolute observable
requires no new sampling. On the canonical square, there are `2L` rough
vertices, an opposite-side path has at least `L-1` edges, and at most
`(4/3)3^n` simple `n`-step paths leave a vertex. Set
`rho_c=3 sqrt[p(1-p)(1+sech h)]`. If `rho_c<1` and the ternary edge cost is
convex, the prior path theorem and `A_L=1-2R_L` give

\[
 A_L(p,h)\geq\max\left\{0,
 1-{32L\over3(1-\rho_c)}\rho_c^{L-1}\right\}. \tag{H13}
\]

The low-`p` condition is explicitly
`0<p<p_cert(h)=[1-sqrt(1-4/{9(1+sech h)})]/2`; here convexity is automatic
because `p_cert(h)<=0.12733` while its gate
`p<=1/[1+1/(2cosh h)]` is at least `2/3`. The strict certificate starts at
`p_cert(0)=0.05904145` and tends to `0.12732200` as `|h|` tends to infinity.
These are sufficient roots of a path bound, **not** critical points.

Independently, the binary syndrome contained in signed charge and the known
all-active complement at high `p` give the old parity-only path bound.
For `r=min(p,1-p)` and `rho_b=6sqrt[r(1-r)]<1`, (H13) holds with `rho_b`
in place of `rho_c`, for every finite `h`. In particular it covers
`p>(3+2sqrt2)/6=0.97140452` as well as a smaller low-`p` region. The two
branches use the **physical** `p,h` channel; substituting the `p_*` inside
(H9) into their witness rates would change the model. Closed-form root and
convexity checks pass to `4.45e-16`, with no new size or physical record.

Thus `A_L` tends to one exponentially in the certified regions, but the
moderate-`p` square problem—especially the existing `p=.30` evidence—remains
unresolved. This is a direct corollary of the prior
[physical path proofs](thermodynamic-limits.md), not a new square phase
boundary. [H12 corollary and scope](../results/physical-absolute-contrast-certified-wedge-2026-09-22.json).

### Why optimizing one pathwise Chernoff exponent does not reach p=.30

A bounded audit tested whether the preceding path proof can be rescued by
choosing a global Chernoff exponent `0<s<1` and keeping step direction in a
four-direction nonbacktracking transfer. Write `a=1-p`, `b=pq`, `c=p(1-q)`.
The forward and backward unit-shift factors are
`u_s=a^(1-s)b^s+c^(1-s)a^s` and
`v_s=a^(1-s)c^s+b^(1-s)a^s=u_(1-s)`. Let `T` weight each permitted next
step by `u_s` or `v_s`, excluding only immediate reversal. Its exact optimum
over all such global exponents is

\[
 \inf_{0<s<1}\rho(T_s)
 =3\sqrt{p(1-p)}(\sqrt q+\sqrt{1-q}). \tag{H14}
\]

Indeed, log-convexity gives `u_s v_s>=u_(1/2)^2`. The transfer is similar
to a symmetric matrix whose Rayleigh quotient at vector `sqrt(w)` is
`2[(u+v)-uv/(u+v)]>=3sqrt(uv)`; equality holds at `s=1/2`, when every
row sum is `3u_(1/2)`. At `p=.30`, even the `q=1` limiting value is
`3sqrt(.21)=1.374772708487>1`; every finite `h` has an equal or larger
value. The registered 12-cell arithmetic matrix confirms the formula.

This closes **only** the fixed-global-exponent, unrestricted
nonbacktracking geometric-series route. It is not an upper or lower estimate
for physical H12 at `p=.30`, nor a phase claim. Self-avoiding geometry,
path-conditioned exponents, correlations between witnesses, or a direct
physical-record posterior estimate remain distinct possibilities.
[Registered method audit and exact arithmetic](../results/h12-global-chernoff-audit-2026-09-22.json).

### A physical charge-prefix route that keeps the H12 target

The failed path sum need not be replaced by another path count. Reveal the
*actual measured signed charges* in any fixed order. For prefix `x` of length
`k`, let `Z_a^k(x)` be the physical sector mass after summing every unrevealed
charge, and set `F_k=sum_x sqrt[Z_0^k(x) Z_1^k(x)]`. Writing
`alpha_k(x)=sum_y sqrt[P_0(y|x)P_1(y|x)]` for the next charge gives the exact
chain

\[
 F_k=\sum_x\sqrt{Z_0^{k-1}(x)Z_1^{k-1}(x)}\,\alpha_k(x),
 \qquad F_k\le F_{k-1}. \tag{H15}
\]

Only prefixes with both sector masses positive enter that sum. The ratio
`F_k/F_(k-1)` is weighted by the geometric mean of the two *physical sector
masses*, not by `P(Q)` itself and not by an annealed two-replica collision
law. At the full record,
`A_L=1-2R_L` obeys, without model-specific approximation,

\[
 1-2F_m\ \le\ A_L\ \le\ \sqrt{1-4F_m^2}. \tag{H16}
\]

The left inequality is `min(Z_0,Z_1)<=sqrt(Z_0Z_1)`; the right is
Cauchy–Schwarz applied to `|Z_0-Z_1|`. Thus accumulated affinity decay is a
valid sufficient route to `A_L->1`, while affinity bounded away from zero
forces a nonzero Bayes-risk lower bound. Neither conclusion follows from a
single finite-size factor.

There is an important evidence limit. With the already-defined full-record
gap `G(Q)=|log[Z_0(Q)/Z_1(Q)]|` and physical record law
`P(Q)=Z_0(Q)+Z_1(Q)`, the terminal affinity is identically

\[
 F_m={1\over2}\,\mathbb E_{Q\sim P}
       [\operatorname{sech}(G(Q)/2)]. \tag{H17}
\]

Together with (H16), this makes `F_m->0` *equivalent* to `R_L->0`, and
`F_m->1/2` equivalent to `R_L->1/2`. Recomputing `F_m` from the stored
posterior-gap cohorts is therefore a deterministic transformation of the
same data, not independent transition evidence. The sequential identity
becomes a proof method only if the spatial model supplies a genuinely
size-uniform bound on its **accumulated conditional factors**; more L3
orders or a rebootstrap of the same gap samples cannot supply that bound.

**All-size localization of the information-bearing reveal.** On the
canonical square, let `B={v measured: x(v)<=L-3}` and let `S` be the `L`
measured vertices at `x=L-2`, adjacent to the right rough boundary. The
logical cut consists of exactly the `L` edges from `S` to the unmeasured
right boundary. Every `Q_v` with `v in B` depends only on currents incident
to `B`; none of those edges is in the cut. By independence of physical edge
currents, the *joint* bulk record `Q_B` is independent of the cut parity
`H`. This holds for every size, every `0<p<1`, and any independent-edge bias
pattern at fixed activity `p`, including finite `h` and the directed limit.
The sector priors and any bulk-only Bayes risk are therefore exactly

\[
 \pi_{0,1}={1\pm(1-2p)^L\over2},\qquad
 R(H\mid Q_B)={1-|1-2p|^L\over2},\qquad
 F(Q_B)=\sqrt{\pi_0\pi_1}
 ={1\over2}\sqrt{1-(1-2p)^{2L}}. \tag{H18}
\]

In particular, at any interior fixed `p`, bulk-only risk tends to `1/2`.
If a charge-reveal order lists the bulk before `S`, every one of its bulk
prefixes has precisely the initial sector affinity: no `O(L^2)` sequence of
bulk steps contracts (H15). The remaining `L` strip charges *can* become
informative after conditioning on the bulk, so this lemma neither bounds
their conditional affinity nor classifies the full-record `p=.30` phase.
Four previously used square sizes `L=3,5,7,11` pass the incidence and
cut-endpoint gates; the retained exact L3 initial affinity matches (H18)
within `1.39e-15`. No physical history or new size was generated.
[Geometry audit and retained control](../results/h12-bulk-charge-independence-2026-09-23.json).

**A stronger all-size mask for incomplete strip readout.** Let `T` be any
subset of the `L` cut-adjacent measured vertices, and reveal `O_T=(Q_B,Q_T)`.
Each cut edge from an unobserved row has no endpoint in this partial record.
Its activity is therefore still an independent Bernoulli(`p`) variable,
even after conditioning on `O_T`. Writing `C_T` for the observed-row cut
activities and `r=L-|T|`, independent parity factorization gives

\[
 \mathbb E[(-1)^H\mid O_T]
 =(1-2p)^r\mathbb E[(-1)^{\sum_{y\in T}C_y}\mid O_T],
 \qquad
 A(O_T)\le |1-2p|^r,
 \qquad
 R(H\mid O_T)\ge {1-|1-2p|^r\over2}. \tag{H19}
\]

Here `A(O_T)=E|E[(-1)^H|O_T]|` is the *physical* absolute sector contrast
for this deliberately incomplete public record. Equation (H19) is valid
for all sizes and independent-edge orientation biases at fixed activity
`p`, including finite `h`; it does not assume conditional independence of
the observed cut edges or of the bulk charges. If `0<p<1` is fixed and
`r` grows, then this partial-record contrast vanishes and its Bayes risk
tends to `1/2`. In particular, observing any fixed fraction less than one
of the strip rows, even along with **all** bulk charges, cannot decode the
parity asymptotically. The effect of revealing the last `O(1)` cut-adjacent
rows is not bounded by this argument: at `r=0`, (H19) is trivial and the
full-record phase is still open. Thus a proof cannot distribute a uniform
affinity contraction over bulk sites or early strip sites; it must control
the terminal collective record.

The canonical cut-endpoint gate passes at previously used `L=3,5,7,11`.
All eight `L=3` strip subsets at each existing `q=.50,.90,1` pass the
contrast bound, with maximum numerical violation `2.09e-16`; these are
exact finite checks of an all-size product-law proof, not trend evidence.
[Partial-record theorem audit](../results/h12-unrevealed-cut-parity-mask-2026-09-23.json).

**The complete strip alone is also asymptotically uninformative.** This is a
different incomplete-record bound: retain all `L` charges in the right
cut-adjacent strip but hide *all bulk charges*. Reveal the strip's vertical
edge currents `V` only to an auxiliary proof oracle. Subtracting their
known divergence from each strip charge leaves independent row variables
`Y_y=X_y-C_y`, where `X_y` is the horizontal edge entering the strip and
`C_y` is its cut edge. The actual decoder does **not** see `V`. Because
revealing data cannot reduce absolute sector contrast, its physical
strip-only contrast is at most the oracle contrast.

For the canonical uniform horizontal bias, set
`a=1-p`, `b=pq`, `c=p(1-q)`. The signed one-row mass
`d(r)=P(Y=r,C=0)-P(Y=r,|C|=1)` is, for
`r=-2,-1,0,1,2`, respectively,
`(-bc, a(c-b), a²-b²-c², a(b-c), -bc)`. Independence of row pairs
then gives the exact proof-oracle contrast and physical bound

\[
 A(Q_S)\le A(Q_S,V)=\delta(p,q)^L,\qquad
 \delta=|a^2-b^2-c^2|+2a|b-c|+2bc<1. \tag{H20}
\]

The strict inequality holds for every fixed `0<p<1` and `0<=q<=1`:
at `Y=0`, the even contribution `a²` and odd contribution `b²+c²`
both have positive mass, so `delta<=1-2min(a²,b²+c²)<1`.
Consequently, strip-only Bayes risk tends to `1/2` exponentially with
`L`, even at the directed endpoint. This says nothing about the joint
physical record `(Q_B,Q_S)`, because bulk observations can reveal hidden
interface currents and make strip charges jointly informative. Together
with (H18) and (H19), the result locates the unresolved problem in these
**bulk-strip correlations**, not in either marginal record or further
partial-prefix tuning. No more partial-record refinement is needed before
a direct full-record H12 attack.

The canonical strip decomposition passes at the already used
`L=3,5,7,11` sizes. At the retained `p=.30`, the exact row factors are
`delta=.49,.7684,.82` for `q=.50,.90,1`; the exact L3 strip-only
contrasts `0.117649,0.331743,0.414622` obey their respective cubic
bounds `0.117649,0.453693,0.551368`. These finite controls validate
the algebra, not a thermodynamic fit.
[Strip-only proof and controls](../results/h12-strip-only-parity-erasure-2026-09-23.json).

**Joint-record method gate after the marginal bounds.** The missing
quantity is the *physical* conditional strip contrast, averaged over the
bulk record: `A(Q_B,Q_S)=sum_b P(Q_B=b) A(Q_S|Q_B=b)`. This is not bounded by
either (H18) or (H20): conditioning on `Q_B` changes the law of the hidden
horizontal currents entering the strip. A direct H12 argument must control
that conditional interface law and the resulting signed parity cancellation
uniformly in `L`, or construct an admissible full-record counterfamily.
This is a proof obligation, not a new result or a proposed threshold.

A targeted primary-source audit closes two tempting shortcuts. The Gaussian,
toric, full-charge winding-sector/stiffness argument in
[Temkin et al.](../../../references/temkin2025-charge-informed-qec/paper.pdf)
does not directly establish a rough-boundary, bounded-ternary-current,
partial-charge H12 statement. Its replica identities also cannot replace
the physical-record absolute average by an annealed two-replica average;
the distinction is explicit in the [replica audit](replica-boundary-ratios.md).
The pathwise minimum-energy/Peierls union bound in
[Dennis et al.](../../../references/dennis2001-topological-quantum-memory/paper.pdf)
is a sufficient bound, not a characterization of optimal decoding. The
registered [global-Chernoff audit](../results/h12-global-chernoff-audit-2026-09-22.json)
already shows that this global path-counting route cannot certify `p=.30`
even at the most favorable bias. Neither source may be used to infer the
full-record phase by analogy; the next step must attack the joint physical
law rather than tune the same bound or refine another incomplete record.

**A rare joint-record witness defeats pointwise conditional erasure.** For
every canonical square size `L>=4`, let `E_L` be the *public bulk-charge*
event that every measured vertex `v=(L-3,y)` in the last bulk column has
`Q_v=(-1)^y deg(v)`. Since every incident ternary current contributes at
most one to `|Q_v|`, each such charge pins all incident currents. The
alternating signs agree on the vertical edges shared by consecutive rows,
so `E_L` is physically attainable. It pins all `L` horizontal interface
currents `X_y` entering the cut-adjacent strip. Summing the public charges
over that strip cancels every internal vertical current and gives

\[
 \sum_y Q_{S,y}=\sum_y X_y-\sum_y C_y,
 \qquad H=\sum_y |C_y|\bmod 2
       =\left(\sum_y X_y-\sum_y Q_{S,y}\right)\bmod 2. \tag{H21}
\]

Thus **the full public record determines `H` exactly on `E_L`**: for every
supported bulk record satisfying this pattern,
`A(Q_S|Q_B=b)=1`. The event fixes `2L` horizontal and `L-1` vertical
edge currents. For uniform finite `0<q<1`,
`P(E_L)>= [p min(q,1-q)]^(3L-1)>0`; at `q=1/2` its probability is exactly
`(p/2)^(3L-1)`. Hence the physical full-record contrast obeys the weak
lower bound `A(Q_B,Q_S)>=P(E_L)`. The bound decays exponentially, so it
does **not** establish correctability, a phase, or a threshold at `p=.30`.
It specifically rules out promoting (H20) to a uniform
`A(Q_S|Q_B=b)<=delta^L` statement for every bulk record. Any useful
full-record theorem must weight the *typical* bulk records rather than
require pointwise erasure. Deterministic incidence and parity checks passed
at the already used `L=5,7,11` sizes, with no physical sampling or new size.
[Joint-record witness and gates](../results/h12-saturated-bulk-joint-record-witness-2026-09-23.json).

An exact reuse of the existing `L=3` current enumeration at `p=.30` tested
all six charge orders for each `q=.50,.90,1`: 18 deterministic cells, no new
size or sampled record. Normalization, (H12), (H15), monotonicity, order
invariance and (H16) pass with maximum error `4.58e-16`; replay is
bit-identical. The full-record affinities are `0.488924`, `0.467977` and
`0.426556`, respectively, while the physical absolute contrasts are
`0.117649`, `0.331743` and `0.414622`. Four of six fair-noise reveal
orders have a supported prefix with `alpha=1`; even the best order's largest
conditional affinity is `0.999310`. At `q=.90`, some physical weighted
stage factors exceed `0.99795`. Consequently the exact chain supplies a
target-preserving proof interface, but these finite controls do **not**
establish any size-uniform contraction, correctable phase, or transition at
`p=.30`. The unresolved quantity is the accumulated physical contraction
across growing squares, not the apparent gap of one chosen L3 order.
[Exact prefix result and all 18 cells](../results/h12-physical-charge-prefix-affinity-2026-09-23.json).

Provenance: [Lab 006 observation definition](../../lab-006-sun-bp-theory/wiki/hidden-orientation.md),
[Lab 007 undirected current and rotor representation](../../lab-007-decoding-statistical-mechanics/wiki/statistical-model.md),
and the researcher's explicit signed-charge and link-field clarification on
2026-09-22. This field dictionary is an algebraic reparameterization of the
existing channel, not a new numerical result or a new critical theory.

### What the completed calculations allow us to hypothesize

| Existing evidence | Supported use | Unsupported inference |
| --- | --- | --- |
| Optimal sector inference retains the direction contrast | Seek a mechanism in the posterior statistical model itself | Attribute the whole effect to a practical decoder |
| At p=.30, the L7/L9/L11 gaps move outward for q=.90/.94/.97 | A growing interface-cost hypothesis is worth investigating | Positive asymptotic line tension, a critical q, or a thermodynamic phase |
| Finite-size low-p defect counting changes powers with q | Identify allowed logical defects and their activity costs | Interchange p to zero and L to infinity |
| The single-reverse expansion is controlled by the number of edges | Identify the obstruction to a uniform perturbation around q=1 | Treat any fixed small 1-q as a single defect at arbitrarily large L |
| Directed-midpoint support maps to critical crossing | There are macroscopically ambiguous supports | Both sectors carry comparable posterior mass |
| Honeycomb path bounds give an open all-p correctable bias interval | At least one geometry has robust thermodynamic correctability | Transfer that region or its endpoint to the square lattice |

The existing finite-size matrix cannot choose between eventual linear gap
growth, slower divergence, or a late plateau. Its lower-tail observations are
also not a rare-event large-deviation estimate. In two dimensions the expected
reverse-edge count is of order L squared times p(1-q); fixed-size perturbation
theory therefore loses uniformity at fixed nonzero reverse probability.
This does not prove that reversal is a relevant RG perturbation: the
honeycomb theorem already supplies a counterexample to a universal claim
that every nonzero reversal destroys correctability.

Sources within this lab: [finite-size data](decoding-thresholds.md),
[low-noise derivation](partition-function-ler.md),
[reverse expansion](reverse-sector-response.md), and
[thermodynamic bounds](thermodynamic-limits.md).

### The positive disordered interface model

Use the existing exact current model, not a presumed clean XY action. At
interior p,q, write w(j)=(1-p) exp[-V(j)], with

\[
V(j)=t|j|-hj,\quad
t=\log\frac{1-p}{p\sqrt{q(1-q)}},\quad
h=\frac12\log\frac{q}{1-q},\qquad j\in\{-1,0,1\}.
\]

Outside the alphabet V is infinite. Sample a planted physical current j*,
then condition on Q=D_M j*. Every compatible current is j*+k with D_M k=0.
Thus the posterior is exactly a positive constrained relative-current model
with action sum_e V(j*_e+k_e). Contractible k can be represented by dual
height differences; rough-boundary current generators must also be retained.
Changing binary logical sector inserts a nontrivial relative current.

The planted offsets are iid under the original edge prior; they are not iid
after conditioning on Q. Neither independence of coarse blocks nor a Gaussian
height action follows. Bias h changes local weights and the activity cost t;
at q=1 it additionally removes the negative-current support. At p=1/2,q=1
all supported currents have equal prior weight, so the sector gap is entirely
an entropy difference: log of the ratio of compatible-configuration counts.
Its sign and magnitude are not fixed by the existence of a crossing.

This construction is an application of the already established
[current/height mapping](complex-weights-and-cft.md), not a new solved model.

### Exact planted-gap symmetry, valid at every size

Let Z_a(Q)=P(Q,a) for a in {0,1}, with T=Z_0+Z_1=P(Q). Let A be the actual
planted logical parity and define the signed cost

\[
D=\log\frac{Z_A(Q)}{Z_{1-A}(Q)},\qquad
G=|D|=\left|\log\frac{Z_0(Q)}{Z_1(Q)}\right|.
\]

The planted label is used only in this theoretical probability space, never
as decoder input. At a fixed Q with both weights positive, write d=log(Z_0/Z_1).
The joint law places mass Z_0 at D=d and mass Z_1 at D=-d. Hence the measure
nu of finite D satisfies, for x>0,

\[
\nu(-dx)=e^{-x}\nu(dx).
\]

This statement is about measures and includes discrete atoms. Records with
one supported sector give D=+infinity and zero error; no negative-infinity
mass is possible. Equal weights give an atom at D=0. Pairing the masses proves

\[
R_L=P(D<0)+\tfrac12P(D=0)
=E_Q\frac{1}{1+e^{G}}.
\]

For 0<s<1 the finite-support moment also obeys

\[
E[e^{-sD}]=\sum_{Q:Z_0Z_1>0}
\left(Z_0^{1-s}Z_1^s+Z_1^{1-s}Z_0^s\right)
=E[e^{-(1-s)D}].
\]

These identities require neither Gaussian fluctuations nor replica
continuation. They constrain any proposed scaling distribution or effective
theory. They do not themselves determine that distribution. They are the
binary matched-posterior analogue of Nishimori domain-wall identities; the
proof here comes directly from the two sector probabilities.

### A uniform target that is equivalent to exponential correction

The existing exact risk identity gives

\[
\tfrac12 E[e^{-G}]\le R_L\le E[e^{-G}].
\]

Consequently a typical line tension, even if it exists, does not by itself
determine the exponential decay rate of average risk. A useful proof target
is instead the following statement, with constants independent of L:

\[
P(G\le aL)\le C e^{-bL},\qquad a,b>0.
\tag{T}
\]

Splitting the risk average on this event proves

\[
R_L\le\tfrac C2e^{-bL}+e^{-aL}.
\]

Conversely, if R_L<=C exp(-kL), then for every 0<a<k,

\[
P(G\le aL)\le(1+e^{aL})R_L
\le2C e^{-(k-a)L}.
\]

Thus existence of constants in (T) is equivalent to exponential correctability.
This is a conditional all-size lemma, not proof that (T) holds in the
unresolved square parameter region. The existing path bounds already imply
it inside their sufficient regions by the converse direction.

For general vanishing risk, allow any diverging scale g_L and prove
P(G<=g_L)->0. Slower, for example logarithmic, gap growth may yield vanishing
risk with zero line tension. For an impossibility theorem it suffices to find
fixed M<infinity and delta>0 with liminf P(G<=M)>=delta; then
liminf R_L>=delta/(1+exp(M)). These remain distinct possible thermodynamic
regimes. Positive line tension is not the definition of correctability.

### Exact gluing: the missing variable in a scalar size recursion

Partition edges into two disjoint regions A and B sharing measured interface
vertices S. Interior measured vertices belong to only one region. Retain each
edge's original prior exactly once. Let u be the vector of divergence supplied
to S by A, so B supplies Q_S-u. Define W_A,a(Q_A,u) by summing A currents with
the specified interior charges, interface divergence and contribution a to
the global logical cut; define W_B,b analogously. These definitions also
allow an arbitrary cut split, including a trivial contribution on one side.

Factorization of the unconditioned edge prior and charge conservation give
the exact, size-independent identity

\[
Z_s(Q)=\sum_u\sum_{a\oplus b=s}
W_{A,a}(Q_A,u)W_{B,b}(Q_B,Q_S-u).
\]

Write T_A=W_A,0+W_A,1, m_A=(W_A,0-W_A,1)/T_A, and likewise for B, only on
supported states. The normalized interface measure is

\[
\rho_Q(u)=\frac{T_A(Q_A,u)T_B(Q_B,Q_S-u)}{T(Q)}.
\]

Its sum is one, and the logical polarization satisfies

\[
m(Q)=\sum_u\rho_Q(u)m_A(Q_A,u)m_B(Q_B,Q_S-u).
\tag{G}
\]

This is a concrete coarse-graining equation. It retains a vector
boundary flux, not just a scalar gap. Averaging over that hidden flux may
cancel opposite signs even when every fixed-flux block is individually
unambiguous. For example, products +1 and -1 at two equally weighted flux
states give global m=0. This algebraic example disproves automatic scalar
closure; it is not claimed to construct a typical physical lattice family.

An exact conditional cancellation decomposition makes the proof target
more explicit. Set x_u=m_A m_B and
U_+=sum_u rho_Q(u) max(x_u,0), U_-=sum_u rho_Q(u) max(-x_u,0).
Then

\[
r(Q)=\frac{1-|m(Q)|}{2}
=\frac12\sum_u\rho_Q(u)(1-|x_u|)+\min(U_+,U_-).
\tag{C}
\]

The first term is uncertainty left with the interface flux revealed. The
second is the additional ambiguity caused by forgetting that flux. It can
be order one even when the first term vanishes. A proof must control both.
This also gives r(Q)>=sum_u rho_Q(u) r_product(u), as expected from the
fact that revealing the interface cannot worsen optimal inference.

### Exact average-cancellation bound: interface distinguishability

The physical average can be reduced further without assuming independent
blocks. For a fixed public record Q, let p_h=P(H=h|Q) and let
pi_h^Q(u)=P(U=u|Q,H=h) be the interface-flux law in logical sector h. Define

\[
d_Q=\|\pi_0^Q-\pi_1^Q\|_{\rm TV}.
\]

The risk with U revealed is

\[
r_U(Q)=\sum_u\min\{p_0\pi_0^Q(u),p_1\pi_1^Q(u)\}.
\]

Hence the cancellation term in (C) is exactly the value of hiding U,
`c(Q)=r(Q)-r_U(Q)`. If p_0<=p_1, divide by p_0 and use
`min(pi_0,(p_1/p_0)pi_1)>=min(pi_0,pi_1)`; the other ordering is symmetric.
This proves the size-independent recordwise bound

\[
0\le c(Q)\le r(Q)d_Q. \tag{D}
\]

Consequently, if d_Q<=epsilon_L outside a physical-record event of probability
delta_L, then

\[
\mathbb E[c(Q)]\le \epsilon_L R_L+\frac{\delta_L}{2}. \tag{E}
\]

This is the requested averaged rather than pointwise criterion. It identifies
the missing physical theorem precisely: the two logical sectors must induce
nearby interface-flux laws on the records carrying Bayes risk. It is not
enough that typical records have small d_Q if the risk is concentrated on the
exceptional set.

There is also an information-theoretic sufficient form. Put
`I_Q=I(H;U|Q=q)` in natural units. Pinsker applied to each sector-conditioned
law and their mixture gives

\[
I_Q\ge 2p_0p_1d_Q^2,
\qquad
c(Q)\le\sqrt{\frac{r(Q)I_Q}{2(1-r(Q))}}
\le\sqrt{r(Q)I_Q}.
\]

Cauchy--Schwarz over the physical Q law therefore yields

\[
\mathbb E[c(Q)]\le
\sqrt{R_L\,I(H;U\mid Q)}. \tag{F}
\]

These inequalities are exact for every finite graph. They do not yet prove a
new correctable square region. The interface alphabet grows with its boundary,
so the generic estimate `I(H;U|Q)<=H(U|Q)=O(L)` is useless. What remains is a
model-specific decay estimate for the risk-weighted d_Q in (D), or for the
conditional information in (F), under the charge-constrained two-dimensional
current law. The all-length path has disjoint sector-conditioned interface
laws on its ambiguous record, d_Q=1, and saturates (D); thus no universal
strict factor below one is available. In regions already covered by the
direct path theorem, the weaker `E[c]<=R_L` inherits exponential decay, which
is a consistency check rather than an independent threshold proof.

### Square q=1 calibration: an exact contour bound and its stopping point

The canonical square gives a controlled calibration of the new quantity. Its
shortest rough-to-rough path has length `L-1`, and there are at most
`2L 3^(n-1)` oriented length-`n` candidates. At `q=1` the half-Chernoff edge
affinity is `gamma_1(p)=sqrt(p(1-p))`. Define

\[
\rho(p)=3\sqrt{p(1-p)}.
\]

Because `0<=d_Q<=1`, the interface theorem and the existing logical-path
theorem combine without any additional assumption:

\[
0\le \mathbb E[c(Q)]\le \mathbb E[r(Q)d_Q]\le R_L
\le \min\!\left\{\frac12,
 \frac{2L}{3}\frac{\rho(p)^{L-1}}{1-\rho(p)}\right\}.
\tag{S}
\]

The last expression is valid when `rho(p)<1`, namely on the low-p branch

\[
0<p<p_{\rm suff}(1)=\frac{3-\sqrt5}{6}=0.127322003750035\ldots .
\]

Thus the risk-weighted interface distinguishability is exponentially small in
this certified region, with exponent `-log rho(p)` up to the displayed linear
prefactor. This is an exact contour corollary, but **not a stronger proof**:
the only new step was `d_Q<=1`, so (S) inherits the old Bayes-risk bound and
does not enlarge its parameter range.

The obstruction toward the unresolved `p=.30` regime is equally explicit:

\[
\rho(.30)=3\sqrt{.30\,.70}=1.374772708486752>1.
\]

The sum of length-`n` witness weights can therefore no longer be bounded by a
decaying geometric tail. This is the exact failed step; it is not evidence
that decoding fails at `.30`. The interface-TV identity still holds there,
but the generic inequality `d_Q<=1` contributes no suppression. Progress
beyond the old certificate must use a genuinely sector-conditioned property
of the square interface law on risk-carrying records, rather than another
unconditional path union or a larger finite-size scan. The machine-readable
[calibration record](../results/square-directed-interface-contour-calibration-2026-09-22.json)
freezes the constants and this claim boundary.

### A topological obstruction: the complete straight-interface flux reveals H

The proposed contraction cannot hold for the complete flux state used in (G).
This follows from a finite-graph parity identity, not from weak bounds. In the
canonical square choose any measured separator column `S={x=k}` with
`1<=k<=L-2`. Put in A exactly the edges whose two endpoints have `x<=k`, and
put every remaining edge in B. For `v` in S, let `U_v=(D_Aj)_v`. Then
`(D_Bj)_v=Q_v-U_v` on S, while `D_Bj=Q_v` at every measured B vertex strictly
to its right.

Sum the B-edge divergence over all measured vertices with `x>=k`. Modulo two,
every B edge between measured vertices appears twice and cancels. The only
uncancelled edges are those entering the unmeasured right rough boundary,
whose binary-current parity is the absolute logical bit. Therefore

\[
H=\left[\sum_{v\in M:\,x(v)\ge k}Q_v+
          \sum_{v\in S}U_v\right]\bmod 2. \tag{P}
\]

A record-dependent reference correction only adds a known function of Q to
the right-hand side, so the same conclusion holds for relative sector labels.
For every ambiguous Q, the two sector-conditioned laws of U consequently live
on disjoint parity classes. Hence, exactly,

\[
d_Q=1,\qquad r_U(Q)=0,\qquad c(Q)=r(Q),\qquad
\mathbb E[r(Q)d_Q]=R_L. \tag{O}
\]

Likewise `I(H;U|Q)=H(H|Q)`: complete flux carries the bit one is trying to
infer. Exhaustive deterministic replay on all 256 L3 and 262,144 L4 binary
currents finds zero parity-identity failures and zero cross-sector U-support
overlaps, including 46 and 24,638 ambiguous charge records respectively.
The [topology record](../results/straight-separator-interface-parity-2026-09-22.json)
and its replay script preserve the exact partition and counts.

This closes the full-interface-TV contraction branch for a straight square
separator. It does not settle the phase. A nontrivial gluing approach must
first remove or align this deterministic topological parity—for example by an
explicit sector-switching transport—and only then compare the residual
interface laws. Alternatively, one must bound the global sector-ratio lower
tail directly. Calling the unaligned `d_Q` a mixing observable would confuse
topological information with local distinguishability.

### Parity alignment works algebraically but not as a physical coupling

The smallest parity quotient is explicit. For an anchor `s` on the separator,
let `e_s` be the one-hot interface vector and define

\[
\bar U_s=U-H e_s.
\]

Equation (P) makes every aligned state have the same known parity. Sectorwise
translation is bijective on the integer interface alphabet, so exact gluing is
preserved by the reindexing

\[
Z_h(Q)=\sum_{\bar u}\sum_{a\oplus b=h}
W_{A,a}(Q_A,\bar u+h e_s)
W_{B,b}(Q_B,Q_S-\bar u-h e_s). \tag{A}
\]

All minimal one-hot anchors were preregistered, rather than choosing one after
inspection. Exhausting `L=3,4`, `p=.30,.50` gives zero parity failures and
reproduces every sector weight to `2.17e-19`. Alignment is nontrivial:
the two sector supports overlap on 52.2%--56.5% of ambiguous L3 records and
28.8%--35.8% of ambiguous L4 records. Revealing aligned flux leaves positive
risk, between 22.4%--30.4% of `R_L` on L3 and 15.6%--23.3% on L4.

This does not establish contraction. The risk-weighted aligned TV is still
72.3%--79.2% of `R_L` on L3 and 79.2%--86.3% on L4. Two sizes cannot select an
asymptotic trend, but they supply no finite-control evidence for decay. Anchor
minima are not promoted; every anchor remains in the result matrix.

More importantly, (A) is a sector-specific relabeling, not a physical current
transport. Toggling a fixed horizontal path is binary-feasible and always
changes logical parity, but preserves the integer charge record on only 1/2
of L3 and 1/4 of L4 currents. Even on Q-preserving all-zero/all-one path pairs,
the reciprocal weight ratios are
`(p/(1-p))^(L-1)` and `((1-p)/p)^(L-1)`, so no size-uniform action-distortion
bound exists away from `p=1/2`. The [aligned-interface result](../results/parity-aligned-interface-matrix-2026-09-22.json)
therefore promotes `bar U_s` only as an exact algebraic state and rejects its
interpretation as a mixing coupling.

### Residual-directed switching preserves Q but has unavoidable action distortion

There is a physical sector switch for every ambiguous binary-current state.
Orient each residual edge along the stored arrow when `j_e=0` and against it
when `j_e=1`. Choose the shortest directed rough-to-rough crossing, breaking
ties by left-to-right direction and then edge/vertex lexicographic order, and
toggle its edges. Along the selected directed path, each toggle adds one unit
of current in the traversal direction. Its measured interior divergence
therefore cancels exactly; binary support is preserved and logical parity
flips.

The preregistered exhaustive audit confirms these identities on all L3/L4
currents. The transport domain matches ambiguous-fiber membership with zero
failures, and all 233,060 domain states have zero binary, charge or logical
failures. The rule is not an involution: only 63.9% of L3 and 60.8% of L4
domain states return after two applications. Maximum inverse multiplicity
grows from 3 to 8.

More decisively, no residual-path flip has size-uniform two-sided action
distortion away from the entropy-only midpoint. On the all-zero current every
residual crossing flips at least `L-1` zeros to ones. Hence

\[
\max\!\left\{\frac{w(Tj)}{w(j)},\frac{w(j)}{w(Tj)}\right\}
\ge
\max\!\left\{\left(\frac p{1-p}\right)^{L-1},
\left(\frac{1-p}{p}\right)^{L-1}\right\}. \tag{R}
\]

This diverges exponentially for every fixed `p!=1/2`, independently of the
path-selection rule. For the registered rule at `p=.30`, the observed maximum
is 12.70 on L3 and 161.38 on L4 because some shortest residual crossings are
longer than `L-1`. At `p=.50` action distortion is exactly one, leaving inverse
multiplicity as the distinct unresolved midpoint gate. The
[transport result](../results/residual-directed-sector-transport-2026-09-22.json)
therefore closes bounded-distortion residual-path coupling away from the
midpoint, but does not rule out weighted mass transport or an entropy-only
midpoint argument.

At the midpoint the frozen rule also fails uniformly, for a different exact
reason. For every `L>=3`, let `j_star` equal one on all horizontal edges and
zero on all vertical edges, so every horizontal residual edge points from
right to left. For each row `r`, reverse exactly that row to obtain `j_r`.
The row is then a left-to-right residual crossing of the minimum possible
length `L-1`. Other rows remain right-to-left crossings of the same length,
so the frozen direction tie-break selects row `r` and maps `j_r` back to
`j_star`. The `L` states `j_r` are distinct; hence

\[
\max_y |T^{-1}(y)|\ge L. \tag{M}
\]

Exact replay on the existing L3/L4 controls gives respectively three and four
constructed preimages with zero selector, common-image, charge or logical
failures. Equation (M) disproves every size-independent inverse-multiplicity
bound for this deterministic map even at `p=1/2`. It does not disprove the
previously observed finite fractional matching certificates, another map, or
either thermodynamic behavior. [Counterfamily and replay](../results/midpoint-residual-transport-multiplicity-2026-09-22.json).

### An arbitrary-length physical check and a rejected shortcut

Take a directed path of any length d=m+n, split after m edges, with rough
endpoints and every interior charge measured. At Q=0 the only compatible
currents are all zero and all one. Their weights are (1-p)^d and p^d. The
two allowed interface fluxes reveal the current completely, so both block
posteriors are deterministic once that flux is fixed. Their product logical
polarizations nevertheless have opposite signs. Therefore (C) gives exactly

\[
r(Q=0)=\frac{\min((1-p)^d,p^d)}{(1-p)^d+p^d},\qquad
R_d=\min((1-p)^d,p^d),
\]

because every nonzero record is unambiguous. This reproduces the existing
all-length path solution from the gluing equation, without finite-size
enumeration. At p=1/2, m(Q=0)=0 while every fixed-flux |m_A m_B|=1.
Consequently a bound |m|>=c E_rho[|m_A m_B|] with any c>0, uniform over
physical records, is false even for this admissible family.

Yet the ambiguous record has probability 2^(1-d), and R_d=2^(-d) vanishes.
Thus a worst-record obstruction is not an impossibility theorem either.
This check selects an averaged, physical-record cancellation estimate as the
next target, and rejects uniform pointwise sign-coherence as a proof shortcut.
It does not decide the two-dimensional square phase.

### Proof program and competing hypotheses

The complete flux variable is topologically trivial as a mixing observable.
Parity quotienting is algebraically valid, and residual-directed switching is
physically Q-preserving, but (R) rules out a size-uniform two-sided action bound
away from `p=1/2`, while (M) rules out uniform inverse multiplicity for the
frozen deterministic rule at the midpoint. Pointwise sign coherence remains
disproved, and no scalar subadditivity theorem has been established.

1. Work in a declared parameter region and arrow geometry. Use the existing
   positive path bound as a consistency baseline and the entropy-only
   directed midpoint as a distinct difficult limit.
2. Use the exact quotient (A), but distinguish algebraic reindexing from a
   physical coupling. Residual-path switching passes Q preservation but fails
   uniform action distortion away from `p=1/2` by (R), and the frozen rule has
   inverse multiplicity at least `L` by (M). Do not tune another path order.
3. Return to selector-independent capacity: prove or disprove restricted
   normalized matching, or directly control the physical probability of competing aligned
   interface states through a contour expansion or boundary-state coupling.
   State any mixing, finite-energy or bounded-distortion condition explicitly
   and prove it for the constrained posterior; do not assume independent blocks.
4. A successful upper-tail/contour estimate must imply (T), or its slower-scale
   version. A successful impossibility argument must retain a positive mass
   of bounded G. A support-crossing theorem alone fails this acceptance item.
5. Only after such control, ask whether a coarse-grained height action,
   stiffness limit or critical fixed-point description follows. A clean
   Gaussian, BKT or complex-CFT label is not an input assumption.

The competing outcomes are an exponentially correctable region, a region
with slower vanishing risk, and a persistent bounded-gap component. The
existing data do not select among their eventual realizations near the
unresolved square boundary. At p=1 activity parity is known, so neither a
single global transition nor monotonicity in p is assumed.

### Primary literature and what transfers

The literature search targeted domain-wall free-energy distributions,
Nishimori identities and defect-based decoding transitions. Existing local
replica and midpoint audits were read first.

- [Kovalev and Pryadko, Spin glass reflection of the decoding transition](https://arxiv.org/abs/1311.7688)
  frames decoding through extended defects and their entropy/tension. This
  motivates a defect measure, but its binary-code spin-model theorems do not
  automatically cover the charge-conditioned bounded-current ensemble.
- [Wan, Dai and Zhu, Revisiting Nishimori multicriticality](https://arxiv.org/html/2511.02907v2)
  explicitly studies the signed domain-wall distribution and its fluctuation
  identity (Eq. 22) for the random-bond Ising decoding model. We transfer the
  distribution-level question and independently prove the two-sector identity
  above; neither their Ising threshold nor their critical exponents transfer.
- [Ising on the donut](https://arxiv.org/html/2512.10399)
  emphasizes the full defect-cost distribution and the distinction between
  stiffness and failure probability. Its phenomenological scaling fits are
  not a proof or an ansatz adopted for this U(1) channel.

## Status

The data-role audit, planted-gap identities, conditional tail criterion,
gluing identity, cancellation decomposition and exact interface-TV/information
bounds are derived above for arbitrary finite graphs or graph sequences under
their stated assumptions. On the canonical square at `q=1`, the new quantity
inherits the old exponential path bound for `p<(3-sqrt5)/6`; this adds no new
correctable region, and its geometric-series step fails at `p=.30`. More
decisively, the complete straight-interface flux determines H by (P), so its
sector TV equals one on every ambiguous record and cannot contract. The exact
one-hot parity quotient has now been constructed and has overlapping finite
supports. Residual-directed switching repairs Q preservation, but exact
all-zero control proves exponentially growing two-sided action distortion for
fixed `p!=1/2`; at `p=1/2`, the row counterfamily proves inverse multiplicity
at least `L` for the frozen rule.
No new physical sample, size, bootstrap or threshold fit is used. The old L13
contract is stopped, not a queued next step.

The next deliverable is selector-independent restricted normalized matching or
an averaged physical posterior-balance estimate. Tuning another deterministic
path order is not counted as progress toward the thermodynamic phase.

## Related pages

- [Decoding transitions and correction thresholds](decoding-thresholds.md)
- [Existing thermodynamic theorems](thermodynamic-limits.md)
- [Physical replica observable](replica-boundary-ratios.md)
- [Current model and CFT boundary](complex-weights-and-cft.md)
- [Registered theory contract](../manifests/thermodynamic-theory-reorientation-2026-09-22.json)
