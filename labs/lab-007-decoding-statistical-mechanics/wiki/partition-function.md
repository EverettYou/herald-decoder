---
title: Exact observation-conditioned sector partition function
status: current
updated: 2026-09-14
---

# Exact observation-conditioned sector partition function

## Summary

The inherited classical instrument defines a positive, quenched vertex model
with binary logical sectors. Its temperature is fixed by the likelihood; the
SU(N) label is representation data, not an assumed spin symmetry or loop weight.
The formulas below are exact for ordinary finite-dimensional SU(N), N ≥ 2,
with fundamental/antifundamental leaves. Computation verifies U(1), SU(2), SU(3).

## Evidence

### Physical variables, observation, and boundaries

Let G=(V,E) be the stored oriented graph, M the measured vertices, and B=V−M
the rough boundary. Write A for the binary incidence matrix restricted to M,
and D for the signed incidence matrix, +1 at a head and −1 at a tail, also
restricted to M. A boundary display value of zero is not a measurement.
There is no factor at a rough vertex: summing its unobserved m and R gives 1.
This matches the parent's [instrument](../../../wiki/methods/sun-fusion-herald-belief-propagation.md)
and [boundary implementation](../../lab-006-sun-bp-theory/scripts/artifact_backend.py).

One physical edge state x_a is shared by both endpoints. In the directed channel
x_a∈{0,+1} with prior (1−p_a,p_a). In the hidden channel x_a∈{0,+1,−1}
with prior (1−p_a,p_a/2,p_a/2). Set e_a=|x_a|. An active +1 edge puts
an antifundamental at the tail and a fundamental at the head; −1 reverses them.
The record s=(m,R) contains only the measured m_v and full irrep R_v.

Define k_v=∑_{a∋v}e_a, L_v(x) the signed leaf list, and

\[
f_v(x;R_v)=\frac{\dim R_v\,M^{R_v}_{L_v(x)}}{N^{k_v}},\qquad
\psi_v(x;s_v)=\mathbf1\{(Ae)_v=m_v\}f_v(x;R_v).
\]

The modeling assumption is conditional independence of these **classical**
local outcomes, given x. No joint quantum instrument for entangled edge pairs
is derived here. The dimension identity ∑_R dim(R)M_L^R=N^{|L|} proves
local normalization. U(1) instead has f_v=1{(Dx)_v=q_v} and dim(F)=1.

### Relative logical sectors and exact normalization

Choose any c₀ with Ac₀=m. Let ℓ be the parent's binary logical cut, extended
linearly to all chains. For its planar patch, h=ℓ(e⊕c₀)∈{0,1}; loops that
bound faces and paths ending on the same rough side are trivial. A path joining
opposite rough sides has h=1. More generally use one cut per logical bit.
The operational score agrees with the parent's residual-cut parity. Here
ker(A)∩ker(ℓ) is precisely the zero-score subspace used for inference; no
additional logical observable is silently introduced.

\[
W(x;s)=\prod_a\pi_a(x_a)\prod_{v\in M}\psi_v(x;s_v),\qquad
Z_h(s)=\sum_x W(x;s)\mathbf1\{\ell(e\oplus c_0)=h\}.
\tag{1}
\]

Then Z(s)=∑_h Z_h(s)=P(s), Q_h(s)=Z_h(s)/Z(s), and
P(x|s)=W(x;s)/Z(s) for Z(s)>0. Impossible records have no posterior.
For each x the sum over all records is 1, so ∑_s Z(s)=∑_x∏_aπ_a(x_a)=1.
Changing c₀ to c₁ with the same syndrome sends h to h⊕ℓ(c₀⊕c₁).
It permutes sectors and leaves optimal success unchanged. A reference is
chosen from the visible syndrome; the decoder is never given the true error.

For the binary logical bit, set F_h=−ln Z_h and ΔF=F₁−F₀. The conditional
optimal failure probability and its physical average are

\[
r_*(s)=\min(Q_0,Q_1)=\frac{1}{1+e^{|\Delta F(s)|}},\qquad
\mathcal R_* =\sum_s\min\{Z_0(s),Z_1(s)\}.
\tag{2}
\]

Infinite contrasts mean a sector has zero support. The thermodynamic target
is concentration of the posterior sector, not a BP convergence event.
This use of homology-class probability follows the decoding/statistical-mechanics
construction of [Dennis et al.](https://arxiv.org/abs/quant-ph/0110143);
the fusion and orientation weights here are derived from the parent instrument.

### Quenched conditioning and the matched-model identity

The record is held fixed inside Z_h. Physical disorder averages use P(s)=Z(s),
not a uniform distribution over records. In particular, averaging the likelihood
before computing sector free energies loses the inference problem.
At the matched prior and likelihood, if X⁰ is the planted state and X¹,X² are
independent posterior samples given S, then

\[
\mathbb E\,g(X^0,X^1,S)=\mathbb E\,g(X^2,X^1,S).
\tag{3}
\]

Proof: conditional on S, all three states are independent draws from P(x|S).
Equation (3) is the precise Nishimori-type exchange identity used here.
It does not identify this instrument with a clean magnetic model. Tempering
W to W^β while retaining the original data law generally breaks this matched
condition; β=1 is the physical posterior.

### Finite verification

The [registered rational enumeration](../manifests/exact-model-checks-2026-09-14.json)
and [machine-readable checks](../results/exact-model-checks-2026-09-14.json)
cover every nonzero record on a tree, contractible cycle, rough square and
hexagonal motifs, and a degree-four star, at three priors and both orientation
laws. They test total and posterior normalization, reference permutation,
and reconstruction of all compatible binary chains. These are finite motifs
with the parent local and boundary laws, not size-scaling lattice samples.

## Status

Exact formulation and proofs for the frozen classical model. No threshold,
physical quantum-channel realization, or universality class is established.

## Related pages

- [Conjugacy and shared orientation](conjugacy.md)
- [Spin, current, and restricted loop representations](statistical-model.md)
- [Decoder gap](decoder-gap.md)
