---
title: Sector partition functions and statistical mechanics
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Sector partition functions and statistical mechanics

## Summary

This page derives the constrained sector sums for the frozen classical herald channel.

## Evidence

The [exact small-record validation](../results/validation.json) checks posterior values against independent weighted enumeration; the derivation and limits follow.

## Status

Current for the registered finite-size model, not a thermodynamic threshold proof.

## Related pages

- [[model|Model and logical loss]]
- [[planar-ml|Planar sector solver]]

## Exact factor model

[The model](model.md) gives a positive factor graph with edge spins $\sigma_e=(-1)^{x_e}$. For $0<p<1$, the edge prior is proportional to $\exp(J_p\sigma_e)$, with $J_p=\tfrac12\log((1-p)/p)$. Exact parity enforces $\prod_{e\ni v}\sigma_e=(-1)^{s_v}$. Site energies are $-\log\phi_q(h_v,n_v)$; a zero likelihood means infinite energy. This is a constrained statistical-mechanics partition function, not automatically an ordinary pairwise Ising model on the original graph.

Choose a syndrome-compatible reference $r$ using visible information only. Write $x=r\oplus z$, so $Hz=0$. At a degree-three vertex the allowed $z$ patterns are $000,011,101,110$; at degree two they are $00,11$. Define

$$
f_v^r(z_{\partial v})=\phi_q\left(h_v,\sum_{e\ni v}(r_e\oplus z_e)\right).
$$

After dropping the common reference prior, an occupied relative edge carries

$$
\rho_e=\left(\frac{p}{1-p}\right)^{1-2r_e}.
$$

Then $Z_a$ is a sum of $\prod_e\rho_e^{z_e}\prod_v f_v^r(z_{\partial v})$ over even subgraphs with $\ell(z)=a\oplus\ell(r)$. This uses the same notation as the [planar-ML derivation](planar-ml.md): $f_v$ is the physical site function, $f_v^r$ is that function after the reference change, and $\rho_e$ is the ratio of physical edge weights. Boundary-to-boundary paths as well as face cycles belong to $\ker H$; a construction using only interior cycles loses boundary degrees of freedom. The [boundary rail](planar-ml.md) handles those paths explicitly. Changing $r$ permutes relative configurations and leaves the absolute posterior unchanged.

The [expanded planar-ML derivation](planar-ml.md) now follows the full conversion: each vertex function becomes internal gadget-edge weights, the auxiliary graph defines $K$, and its weighted matching sum equals a Pfaffian/Grassmann Gaussian integral. It also explains the normalization constants and why planarity alone does not suffice.

## Face-spin picture and free fermions

On a planar completion, even subgraphs are domain walls of dual face spins, up to the selected boundary sector. Domain-wall edge factors can be written as signed Ising couplings $J_e=-\tfrac12\log\rho_e$ when weights are strictly positive. The degree-three even site tensor can be factored into leg weights when all four entries are positive; this gives another pairwise formulation on a decorated graph. Zero entries are hard constraints and may require a matchgate gadget or a limit. A generic high-valence site tensor need not be pairwise Ising or free fermionic.

Here “trivalent” means degree three. “Transfer” means a sweep contraction; there is no traveling-wave assumption. The useful solvable structure is parity plus planar matchgate signatures. “Free fermion” describes the algebra obeyed by those signatures. FKT means Fisher–Kasteleyn–Temperley, the planar dimer/Pfaffian method; it is not an additional statistical assumption called “f-regular.” The [matchgate page](planar-ml.md) states the local identity and constructive reduction; [Kac–Ward](kac-ward.md) gives an alternative determinant representation.

## Energy versus entropy

Configuration MAP minimizes the energy of one configuration. Logical ML compares the full free energies $F_a=-\log Z_a$. A sector containing many moderately likely configurations can outweigh the sector containing the single most likely one. This entropy contribution explains why exact configuration MAP does not attain the logical Bayes risk in general. BP plus marginal matching can also lose correlations between edges and logical sectors. Neither a matching solver nor posterior edge marginals alone imply logical ML.

For each observed record, exact posterior probabilities permit a low-variance risk estimator $R(s,h)=\min(P_0,P_1)$. Averaging $R$ over unconditional sampled records is Rao–Blackwellization of the realized ML failure bit. A realized sample can favor a different decoder even though ML has minimal conditional expected loss. Finite-MPS posterior risk is only an approximation to this estimator.

## Information ordering and what it does not prove

Given a record generated at $q_2\ge q_1$, independently retain every positive herald with probability $q_1/q_2$. This reproduces the $q_1$ channel. Therefore optimal Bayes risk cannot increase with $q$. It does not prove monotonicity in $p$, a unique transition on a fixed-$q$ cut, or monotonic performance for a specified approximate decoder. In particular, complementing all error bits generally fails to preserve incomplete herald likelihoods at intermediate $q$, so $p\leftrightarrow1-p$ symmetry cannot constrain the present boundary without another proof.

## A sufficient recovery region

For an ideal configuration-MAP logical failure, the symmetric difference with truth contains a left-right path of length $m\ge2L-1$ whose flip does not reduce posterior weight. At a degree-three internal vertex, flipping the two path edges preserves herald eligibility if those bits differ, and swaps eligibility if they agree. The Bhattacharyya overlap for the herald law is respectively $1$ and $t=\sqrt{1-q}$, independently of the off-path edge. Summing path bits with the matrix $\begin{pmatrix}t&1\\1&t\end{pmatrix}$ gives overlap

$$
2[p(1-p)]^{m/2}(1+\sqrt{1-q})^{m-1}.
$$

Boundary degree-two vertices obey the same rule. The honeycomb walk connective constant is $\mu=\sqrt{2+\sqrt2}<2$ ([Duminil-Copin and Smirnov](https://annals.math.princeton.edu/2012/175-3/p14)). For every $\epsilon>0$, walk counts are bounded by $C_\epsilon(\mu+\epsilon)^m$. A union bound over $O(L)$ terminals therefore decays exponentially when

$$
\rho(p,q)=\mu\sqrt{p(1-p)}(1+\sqrt{1-q})<1.
$$

This is a sufficient region, not the numerical phase boundary. At $q=1$, compatible counts force ambiguity paths to alternate; a fixed path has probability at most $2^{1-m}$ and $\rho\le\mu/2<1$ across the full $0\le p\le1$. Thus a count-compatible recovery method, and hence optimal logical ML, succeeds asymptotically on the entire perfect-herald edge. It does not imply unique finite-patch recovery. The proof assumes this binary channel, bounded-degree planar honeycomb geometry, the stated rough boundaries and actual MAP/count-compatible inference; it is not a theorem for unconverged BP or the quantum spacetime problem.

The symmetric form of this sufficient upper bound is not an equality for Bayes risk or a symmetry of the phase boundary. At interior q, independently computed full-prior risks need not be symmetric.

## Measured full-domain transition

The [exact-planar phase diagram](phase-diagram.md) samples the complete p,q square, with confirmation-record crossings, successive lattice-size comparisons, statistical uncertainty and unresolved regions. The sufficient bound above is plotted separately from measured transition estimates.
