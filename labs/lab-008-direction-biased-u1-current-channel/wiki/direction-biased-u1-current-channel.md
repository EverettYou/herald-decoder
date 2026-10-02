---
title: Direction-biased U(1) current channel
status: current
updated: 2026-09-22
---

# Direction-biased U(1) current channel

## Summary

**Naming and observation clarification (2026-09-22):** the researcher calls
the q=1/2 channel the **undirected lattice model**. There is no preferred
edge direction, but signed vertex charge Q remains observed. Reference arrows
used in D are coordinate choices. The [thermodynamic program](thermodynamic-decoding-theory.md)
now treats this symmetric point and continuous bias away from it explicitly;
it does not replace Q by its magnitude. The researcher's preferred continuous
control is the effective link field h, with q=(1+tanh h)/2: zero field is
undirected, finite field biases the probabilities, and infinite field is
one-way noise. Edge jumps and signed vertex charges remain integer-valued.

Yes: this is a well-defined and useful one-parameter extension of the existing
U(1) channel.  It interpolates continuously between the fair hidden channel
at \(q=1/2\) and the fully directed channel at \(q=1\).  Its Fourier form has
an imaginary vector potential, but it is **not generically an ordinary XY
model related to a real XY magnet by a harmless gauge transformation**. The
tilt can be removed only for a pure-gauge bias one-form, with compatible
boundaries and sector projection, and a changed symmetric activity prior.
The fully directed endpoint is singular.

Here \(q\) denotes the directional-bias parameter; measured U(1) charges are
written \(Q_v\).

## Evidence

### Exact posterior model

Choose a reference arrow on every edge \(a=(u,v)\), and let \(j_a\) be positive
along that coordinate. At \(q_a=1/2\) this arrow has no physical significance;
at other values the edge prior specifies a physical preference. The channel is

\[
w_a(j_a)=
\begin{cases}
1-p_a,&j_a=0,\\
p_aq_a,&j_a=+1,\\
p_a(1-q_a),&j_a=-1,\\
0,&\text{otherwise}.
\end{cases}
\tag{1}
\]

For the full interior charge record, the exact relative-sector sum is simply

\[
Z_h(Q)=\sum_{j:Dj=Q}\prod_a w_a(j_a)\,
\mathbf{1}\!\left\{\ell((j-j_0)\bmod2)=h\right\}.
\tag{2}
\]

Thus the existing bounded-current implementation and the shared-edge
orientation rule survive unchanged; only the \(+1\) and \(-1\) edge weights
change.  It is therefore straightforward to simulate or contract once the
decoder is told the actual \(q_a\).  If the decoder instead assumes
\(q_a=1/2\), that is a deliberate mismatched-decoding experiment.

Write
\[
h_a=\tfrac12\log\frac{q_a}{1-q_a},
\]
\[
q_a=\frac{e^{h_a}}{2\cosh h_a}.
\tag{3}
\]
For \(0<q_a<1\), Fourier enforcement of \(Dj=Q\) gives the link factor

\[
K_a(\phi_a)=1-p_a+p_a\left[q_ae^{i\phi_a}+(1-q_a)e^{-i\phi_a}\right]
=1-p_a+\frac{p_a}{\cosh h_a}\cos(\phi_a-i h_a),
\tag{4}
\]

where \(\phi_a=\theta_v-\theta_u\), with the source insertion
\(e^{-i\sum_v Q_v\theta_v}\) for the stated incidence convention.
This is the precise source of the proposed imaginary term.

### What the complex gauge statement actually says

Let the bias on an edge written in a fixed reference orientation be
\(A_a=h_a s_a\), where \(s_a=\pm1\) records agreement with the assigned
arrow.  A single-valued imaginary vertex shift removes it from every bulk
link precisely if

\[
A_a=\psi_v-\psi_u
\iff \sum_{a\in C}\operatorname{sgn}_C(a)A_a=0.
\tag{5}
\]

The circulation condition must hold for every graph cycle C. In that special
case, introducing \(\vartheta_v=\theta_v-i\psi_v\) changes
the cosine in (4) to an unbiased one.  On a finite compact integral this is a
contour deformation, so charge insertions, boundary terms, and the parity
twist must be carried with it.  It is not permission to discard those terms.

Two common cases separate cleanly.

| Bias geometry | Bulk gauge status | Consequence |
| --- | --- | --- |
| Open square patch with the same bias along \(+x\) and \(+y\) | Pure gauge: the plaquette circulation is \(h+h-h-h=0\) | Bias can be moved to charge sources and rough-boundary fugacities. It need not leave an open-boundary logical-sector ratio unchanged. |
| Periodic ring or torus with a uniform directed bias | Not single-valued globally: a noncontractible cycle has holonomy \(Lh\) | The bias is an imaginary twist of the boundary condition and changes winding-sector weights. |
| Arbitrary prescribed arrows | Usually not pure gauge: directed plaquettes can have nonzero circulation | The complex vector potential has gauge-invariant local flux and cannot be removed. |

The open-boundary qualification matters for this decoder.  When \(A=d\psi\),
the bias factor in a current configuration is
\(\exp[\sum_a A_aj_a]=\exp[\sum_v\psi_v(Dj)_v]\).  It is constant only when
the charges at *all* vertices are fixed.  The existing rough boundaries are
unmeasured, so their endpoint charges are summed; the transformation moves the
effect into their weights and can still favor one logical path family.

Also, (4) is a polynomial high-temperature link factor, rather than
\(\exp[K\cos\phi]\).  Taking \(-\log K_a\) produces a complex,
multi-harmonic interaction, and a nonzero record supplies complex charge
insertions.  Calling it a “complex XY-like representation” is accurate;
calling the full posterior an ordinary clean XY Hamiltonian is not.

### Fully directional limit

At \(q\to1\), \(h\to+\infty\) and the negative-current weight vanishes.
Equation (2) becomes a positive directed-current model with \(j_a\in\{0,+1\}\).
The finite imaginary gauge transformation in (5) is then singular.

This limit can strongly suppress closed currents on an open acyclic arrow
field: a zero-charge configuration then has no nonzero directed cycle.  But a
periodic directed ring still allows an occupied circulation.  For a four-edge
directed cycle at \(Q=0\), exact enumeration gives

\[
Z_{Q=0}=(1-p)^4+(pq)^4+[p(1-q)]^4.
\tag{6}
\]

At \(p=1/3\), this is \(43/216\) at \(q=1/2\), \(2089/10368\) at
\(q=3/4\), and \(17/81\) at \(q=1\).  The bias therefore has a measurable
gauge-invariant effect whenever the cycle holonomy is present.  The exact
checks also verify zero circulation for the gradient-oriented square plaquette
and holonomy \(4h\) for the periodic ring.

It follows that “the fully directional limit has no transition because it is
gauge-equivalent to XY” is too strong.  A pure-gauge, fully measured,
open-boundary bulk may indeed reduce to the unbiased bulk after its boundary
weights are transformed.  That does not establish the absence of a transition
for periodic twists, fluxful arrow patterns, the rough-boundary sector sum, or
the practical decoder.  Conversely, the directed limit is a promising
distinct regime: it is closer to a constrained directed-loop/current problem
than to a conventional equilibrium XY magnet.

### Connection to the new research program

The primary test compares exact sector inference, exact-marginal MWPM and
parent-schedule BP-MWPM on the same records, followed by intermediate direction
biases. The [numerical evidence design](numerical-evidence.md) supersedes the
initial suggestion to prioritize deliberately mismatched-q decoding. Periodic
twist observables require a separately registered geometry and score.

The initial finite checks, migrated from Lab 007, are in
[the result record](../results/direction-biased-u1-checks-2026-09-18.json), with
[the executable check](../scripts/check_direction_biased_u1.py) and
[registered scope](../manifests/direction-biased-u1-checks-2026-09-18.json).
They establish the mapping and obstruction only.  They do not estimate a
threshold, a BKT scale, or the existence of any thermodynamic transition.

## Status

Current mapping, with corrections and its LER interpretation developed in
[sector predictions](sector-predictions.md). The original cycle example is
a holonomy obstruction, not an isolation of bias at fixed symmetric activity.
Matched intrinsic-sector versus practical-decoder inference has now run;
the [mechanism results](mechanism-results.md) resolve an intrinsic component
and additional decoder loss. A deliberately mismatched decoder remains a
secondary diagnostic. No transition classification follows from these finite data.

## Related pages

- [Sector predictions and the LER connection](sector-predictions.md)
- [Numerical evidence and experiment design](numerical-evidence.md)
- [Lab 006 orientation evidence](../../lab-006-sun-bp-theory/wiki/hidden-orientation.md)
