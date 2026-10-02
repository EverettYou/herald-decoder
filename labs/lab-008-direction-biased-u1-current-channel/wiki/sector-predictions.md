---
title: Sector predictions and the LER connection
status: current
updated: 2026-09-20
---

# Sector predictions and the LER connection

## Summary

The statistical model predicts posterior logical-sector probabilities. Their
physical-record average determines the best possible logical error rate (LER).
To explain Lab 006's practical curves, also evaluate which sector its actual
BP-MWPM correction selects. A complex-looking Hamiltonian alone predicts
neither those decisions nor a transition.

## Evidence

### Current priority: decoding transitions and correction thresholds

The researcher's 2026-09-20 steering prioritizes the thermodynamic decoding
boundary. The [threshold analysis](decoding-thresholds.md) defines the initial
correctable threshold, lists rigorous bounds, and isolates the posterior-
balance statement needed at the square midpoint. The partition ratio remains
the physical observable; bulk-pressure or CFT claims must contribute to a
correctability or noncorrectability statement.

The [connected-current calculation](connected-current-defects.md) now adds
physical LER upper bounds without a replica limit, an exact L3 directed
curve through p=.2, and a fully directional honeycomb theorem. Earlier
finite comparisons and the conditional CFT route remain distinct evidence.

The earlier finite-curve investigation supplied the following results. The
[partition-function derivation](partition-function-ler.md) now writes the
logical parity projection directly as a twisted K integral and derives
an exact boundary-path curve. For the actual canonical square, it also
proves a fixed-size low-p result: bidirectional noise at fixed 0<q<1 has
leading order p^ceil((L-1)/2), whereas fully directed noise has order p^(L-1).
At L=5 the fair and directed first terms are respectively 7.5 p^2 and 70 p^4.
These follow from counting the minimal ambiguous logical defects, without
fitting a decoder. They do not yet describe the full moderate-p curve.

The new [replica boundary calculation](replica-boundary-ratios.md) gives an
exact next step: M2 is the physical second moment of the logical twist ratio,
and (1-M2)/4 <= LER* <= (1-M2)/2. Hence M2 tends to one exactly when optimal
LER vanishes. Higher even moments reconstruct the full LER with a certified
tail bound. A solved long-path limit also gives a rigorous lower bound for
the actual square curve. These are theory results, independently checked
without a production decoder sweep.

The [complex-weight and CFT review](complex-weights-and-cft.md) connects this
observable to primary literature on replica twists and boundary criticality.
Complex K alone does not identify a nonunitary or complex CFT. The physical
replica limit is R->1, while the simple real R=2 rotor model changes the
record weighting. No two-dimensional CFT spectrum or critical p has yet
been established; that field-theory route remains conditional.

### A corrected symmetric-prior mapping

For 0<p<1 and 0<q<1 define

\[
s=2\sqrt{q(1-q)},
\]
\[
c=1-p+ps,
\]
\[
\widetilde p=\frac{ps}{1-p+ps},
\]
\[
h=\frac12\log\frac{q}{1-q}.
\]

The exact single-edge identity is

\[
w_{p,q}(j)=c\,w_{\widetilde p,1/2}(j)e^{hj}.
\]

Thus removing a pure-gradient tilt maps to a **different** symmetric activity
prior. At fixed p, changing q changes both the symmetric weight and the tilt.
The old circulating-square example demonstrated nonzero holonomy but did not
isolate it from the simultaneous change of symmetric activity. For q=4/5 and
p=1/3 the audit checks c=14/15, tilde-p=2/7, exp(h)=2 exactly on 171 states.
See [the registered audit](../results/sector-prediction-audit-2026-09-18.json).

If A=h times the stored edge orientation equals a vertex gradient D^T psi,
then sum(A j)=sum(psi Q) for all vertices, including rough endpoints. For
measured M and unmeasured B, the sector identity is

\[
Z_a^{p,q}(Q_M)=c^{|E|}e^{\psi_M\cdot Q_M}
\sum_{Q_B}e^{\psi_B\cdot Q_B}
Z_a^{\widetilde p,1/2}(Q_M,Q_B).
\]

Use the same logical reference c0(Q_M) in every term; Q_B only refines the
record. On fully observed graphs the charge factor cancels from conditional
sector ratios, yielding the symmetric model at tilde-p on the same record.
The physical record distribution still differs, so averaged LER curves need
not collapse. On open rough patches the boundary tilt generally remains;
it cancels only if constant over all compatible endpoint charges. Even a tree
can retain a relative logical ambiguity. As q tends to one, tilde-p tends to
zero while the tilt diverges: dropping their compensating factors is invalid.

### From partition sums to an actual LER curve

Choose any syndrome-compatible reference correction c0(Q) and label the
two sectors of the binary score a=0,1 relative to it. Define

\[
\Delta F(Q)=\log\frac{Z_0(Q)}{Z_1(Q)},
\]
\[
r_*(Q)=\frac{\min(Z_0(Q),Z_1(Q))}{Z_0(Q)+Z_1(Q)}
=\frac{1}{1+e^{|\Delta F(Q)|}}.
\]

Because Z0+Z1=P(Q) for the normalized physical prior,

\[
\mathrm{LER}_*(p,q,L)
=\mathbb E_{Q\sim P_{p,q,L}}[r_*(Q)]
=\sum_Q\min(Z_0(Q),Z_1(Q)).
\]

This is the direct statistical-mechanics prediction for optimal binary-sector
decoding. It is a quenched typical-record quantity. In particular,
E[min(P0,P1)] is not min(E[P0],E[P1]), and a zero-charge partition sum is not
the average performance. If a sector has zero weight, the formula uses its
continuous limit (infinite |DeltaF| and zero conditional Bayes error).

For a deterministic syndrome-valid decoder returning sector a_D(Q),

\[
\mathrm{LER}_D=\mathbb E_Q[1-P(a_D(Q)\mid Q)].
\]
\[
\mathrm{LER}_D-\mathrm{LER}_*
=\mathbb E_Q\!\left[
|P(0\mid Q)-P(1\mid Q)|\,\mathbf{1}\{a_D(Q)\ne a_*(Q)\}
\right]\ge0.
\]

At posterior ties the excess is zero whichever sector is selected. If a
decoder returns an invalid measured syndrome, count its conditional risk as
one and record that event separately. Lab 006's reported failures use the
actual final correction, not BP nonconvergence. Recompute the returned
correction's relative sector even if it is not a feasible integer-current
configuration; the scoring space is binary, not integer winding recovery.

Exact marginals followed by the *same* MWPM isolate the cost of hardening.
Comparing that decoder with BP-marginal MWPM tests belief approximation.
Each is no better than Bayes on average; their mutual ordering has no theorem.
BP nonconvergence alone is not proof of inaccurate marginals or logical failure.

### Response of a fixed-record sector gap

Let N+ and N- count forward and reverse active edges. For fixed p, fixed Q,
fixed sector labels and 0<q<1, differentiating the finite positive sum gives

\[
\partial_q\log Z_a
=\frac{\langle N_+\rangle_a}{q}
-\frac{\langle N_-\rangle_a}{1-q}.
\]

Therefore

\[
\partial_q\Delta F
=\frac{\langle N_+\rangle_0-\langle N_+\rangle_1}{q}
-\frac{\langle N_-\rangle_0-\langle N_-\rangle_1}{1-q}.
\]

This predicts which sector is favored as the noise bias changes on an
unchanged record. Sector averages are conditional on Q; this is not a claim
of monotonic average LER, since P(Q) itself changes with q. At q=1 use the
supported current alphabet directly; the displayed derivative is not defined
there. On the square gradient field the signed-count difference also equals
the difference of the weighted unmeasured endpoint charges between sectors,
after the fixed interior charge contribution cancels. The changed symmetric
activity weight remains a separate contribution.

The completed validation checks 282 fixed-record derivatives against centered
finite differences, with maximum error 4.91e-10. With N=N+ + N- and J=N+ - N-,
the response separates into an activity term and a signed-current term:

\[
\partial_q\Delta F =
\frac{(1-2q)\,\Delta\langle N\rangle+\Delta\langle J\rangle}
{2q(1-q)}.
\]

Here Delta denotes sector 0 minus sector 1. For the actual square arrows,
J is the weighted full-vertex charge sum with potential x+y. Conditional on
the interior record, its sector difference is entirely an unmeasured-boundary
charge difference. This identity does not remove the activity contribution.
See the [response/oracle validation](../results/response-oracle-validation-2026-09-18.json).

### Predictions to test in the authorized experiment

| Statement | Status and falsification test |
| --- | --- |
| Bayes LER(p,q,L)=Bayes LER(p,1-q,L) | Exact under j->-j, Q->-Q and the same binary score. Practical equality additionally requires a charge-reflection-equivariant algorithm. |
| At q=1/2, arrow relabeling preserves the activity/charge law | Exact: changing one stored arrow is absorbed by relabeling its hidden j. A failure identifies a model or implementation change. |
| Relative current weights acquire a tilt exp(sum A j) and a changed symmetric prior | Exact, with the boundary/source factors above. Gauge-removing only the tilt does not preserve p. |
| Directed noise universally lowers LER | Not a theorem. Test the observed parent advantage, do not impose monotonicity. |
| Asymptotic Bayes LER tends to zero | Equivalent to the absolute sector free-energy gap diverging in probability for matched physical records. Its mean alone does not suffice. |
| Hidden square curve merging is an intrinsic phase feature | Hypothesis: the effect must survive sector Bayes inference and width/size growth. If it appears only after BP/MWPM, this explanation is weakened. |

On the two-edge rough path L->v->R, the record Q_v=0 has
Z0=(1-p)^2 and Z1=p^2[q^2+(1-q)^2]. For p=1/3,
P(sector 1|Q_v=0)=1/9 at q=1/2 and 1/5 at q=1. Here increasing bias raises
the ambiguity on this particular record. This is an exact boundary example,
not a prediction for the lattice-averaged sign of the LER change.

Also, no directed cycle at q=1 does not imply unique inference for nonzero
charges: two distinct directed routes can have identical source/sink charges,
and their difference is a signed cycle. Rough-to-rough routes are another
source of ambiguity. A zero-charge vacuum argument cannot settle recovery.

### Finite-size continuity at the directed endpoint

The imaginary gauge shift is singular at q=1, but the Bayes risk on a fixed
finite graph is continuous. Couple the channels using the same edge activities
and orientation uniforms. A q record differs from its directed counterpart
only if at least one active edge reverses. For E independent equal-rate edges,

\[
\left|\mathrm{LER}_*(p,q,L)-\mathrm{LER}_*(p,1,L)\right|
\leq 1-[1-p(1-q)]^{E}\leq E p(1-q).
\]

Proof: the joint laws of (Q,logical sector) have total variation at most the
coupling mismatch probability. Every fixed decision rule has risk difference
bounded by that distance; minimizing over the same set of decision rules
preserves the bound. This does not bound two independently q-adapted suboptimal
decoders without a further decision-stability argument. Nor is it uniform in
L: the volume factor grows. At L=9, p=.30, q=.97 the expected number of reverse
edges is 1.152. A sizable finite-sample LER change therefore does not imply
an endpoint discontinuity. A joint limit with p(1-q)E tending to zero does
force convergence of the two Bayes risks, irrespective of a gauge argument.

### Primary-source context

A targeted search on 2026-09-18 checked three primary sources. The results
above are our derivations for the bounded channel, not claims borrowed from
these papers.

- [Dennis et al., Topological quantum memory](https://arxiv.org/abs/quant-ph/0110143)
  motivates homology-sector inference and disorder-dependent statistical mechanics.
- [Temkin et al., Charge-Informed Quantum Error Correction, model and supplements](https://arxiv.org/html/2512.22119v1)
  studies Gaussian unbounded integer noise and periodic integer winding recovery.
  It motivates checking optimal inference separately from suboptimal decoders;
  its BKT result is not established for our bounded open-boundary binary score.
- [Hatano–Nelson, Localization transitions in non-Hermitian quantum mechanics](https://arxiv.org/abs/cond-mat/9603165)
  studies transitions with an imaginary vector potential. It is a useful analogy,
  not a no-transition theorem for this decoding model or its singular endpoint.

## Status

Algebraic predictions, response checks and canonical finite-patch sector
contractions are complete. The [mechanism study](mechanism-results.md) measures
the intrinsic and practical LER components, including intermediate bias and
a larger square patch. Thermodynamic transition classification remains open.
The underlying probability channel remains real and positive; a complex Fourier
action by itself does not establish a non-Hermitian quantum Hamiltonian.

## Related pages

- [Direction-biased U(1) current channel](direction-biased-u1-current-channel.md)
- [Numerical evidence and experiment design](numerical-evidence.md)
- [General sector formulation in Lab 007](../../lab-007-decoding-statistical-mechanics/wiki/partition-function.md)
