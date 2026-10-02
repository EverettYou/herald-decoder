---
title: Planar logical ML with matchgates and a Pfaffian observable
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
  - results/planar-factor-contract-validation.json
idea_ids: []
---

# Planar logical ML with matchgates and a Pfaffian observable

## Summary

The trivalent planar factorization gives a logical-sector posterior through a matching observable on the supported honeycomb patch.

## Evidence

The [general validation](../results/validation.json) and [generic-factor check](../results/planar-factor-contract-validation.json) exercise the implementation within their stated finite-size scopes.

## Status

Current with explicit geometry and floating-point limits; no all-size numerical certificate is asserted.

## Related pages

- [[statistical-mechanics|Sector partition functions]]
- [[transfer-mps|Independent contractions]]

## Assumptions and local signature

Use the [relative even-subgraph formulation](statistical-mechanics.md) on the canonical planar honeycomb patch, with exact parity and nonnegative local likelihood tensors on binary edge variables. Conditioned on parity, every measured site has arity two or three. Every even signature of arity at most three admits a planar matching gadget; parity is the only matchgate restriction at these arities. At arity four an extra identity already appears, for example

$$
f_{0000}f_{1111}-f_{1100}f_{0011}+f_{1010}f_{0101}-f_{1001}f_{0110}=0.
$$

Arbitrary degree-four factors violate it. This is why the present source solver does not silently claim square-lattice ML. [Cai and Gorenstein, Matchgates Revisited](https://www.theoryofcomputing.org/articles/v010a007/v010a007.pdf) gives the general signature theory.

## Constructive gadget and weights

At a three-port site let $(g_0,g_1,g_2,g_3)$ be its relative even weights for $000,011,101,110$. Put ports on a triangle and one interior vertex. A matching that occupies two external wires leaves the remaining port paired with the center. Set spoke weights to $(g_1,g_2,g_3)$. For no occupied external wires, the internal matching sum is

$$
g_1 b_{23}+g_2 b_{13}+g_3 b_{12}=g_0.
$$

Choose one nonzero $g_j$ and set its opposite triangle weight to $g_0/g_j$, with the other triangle weights zero. This represents the signature using nonnegative weights, including hard zeros. Normalize the local signature first; its common scale cancels from sector probabilities. If only $g_0$ is nonzero, force all incident relative wires unoccupied and use a unit gadget. Degree two uses an internal link with weight $g_{00}/g_{11}$, or the corresponding forced-wire construction if $g_{11}=0$.

An external lattice wire carries $t_e=(p/(1-p))^{1-2r_e}$. Spokes/triangle weights encode site likelihoods; lattice wires encode the prior once per edge. Internal dimer nodes do not carry a separate physical site prior.

## Rough-boundary rail and sector encoding

Join the active rough terminals by a planar rail outside the patch, ordered up the left side and down the right side, with a top bridge. Add parity gadgets at rail vertices. For each even relative subgraph, the rail bits are determined by cumulative terminal parity; occupancy of the top bridge is its right-boundary parity. The package cut differs from that boundary cut by a syndrome-dependent offset. Since $z$ has zero syndrome, their parities agree on $z$. Finally translate from relative sector to absolute sector by $\ell(x)=\ell(z)\oplus\ell(r)$. This avoids discarding same-side boundary paths or confusing cuts on nonzero syndrome configurations.

## Pfaffian partition function and one inverse element

Orient gadget edges so every bounded face has an odd number of clockwise arrows. A dual spanning-tree construction sets this orientation and checks both Euler planarity and every face parity. Form the skew matrix $K$, with $K_{ij}=\pm w_{ij}$ and $K_{ji}=-K_{ij}$. The dimer partition sum is $|\operatorname{Pf}K|$, up to a common sign. All matching terms have compatible signs under this orientation.

For the logical rail edge $(i,j)$, dimer occupancy is

$$
P_{\rm relative}(1\mid s,h)=K_{ij}(K^{-1})_{ji}.
$$

This follows by differentiating $\log\operatorname{Pf}K$ with respect to its edge weight. It obtains the two sector probabilities from one sparse LU factorization and one solve $Kz=e_i$. It does not need a subtraction of two nearly equal extensive partition sums or an ambiguous square-root sign. The absolute probabilities are reversed if $\ell(r)=1$.

## Numerical gates and integration

`HeraldPlanarMLDecoder` builds the literal binary-herald factors and uses visible-record configuration MAP as a reference to improve conditioning. `PlanarParitySolver.posterior_from_factors` accepts other nonnegative binary local factors in `graph.incident_edges` order. No sampled truth is used. Positive diagonal congruence $K\mapsto D K D$ balances dynamic range and leaves edge occupancies invariant. The implementation checks solve residual, finiteness and probability range. Algebraic exactness is not an all-size floating-point guarantee.

For the herald wrapper, $0<p<10^{-12}$ or $1-10^{-12}<p<1$ uses exact transfer under its width/memory caps; it raises if that fallback cannot run. The generic factor solver does not offer that specialized fallback. A numerical failure is explicit, never silently converted to a class decision. Batch planar decoding currently loops over shots. The reusable geometry and sparse topology are constructed once; no dense inverse is stored.

The primary gain over BP is full correlated sector summation. The limitations are supported geometry, local-factor assumptions and numerical conditioning. [Transfer/MPS](transfer-mps.md) supplies an independent formulation and a route beyond matchgate signatures. The [general validation](../results/validation.json) and [supplemental factor-contract validation](../results/planar-factor-contract-validation.json) record the tested range: the latter compares 12 L=2 random positive-factor records against whole-error enumeration, switches between both logical reference sectors, permutes the edge ordering, and rejects negative/nonfinite factors. Its maximum posterior error is 3.33e-16 at p=.23; it does not certify larger-size conditioning or arbitrary geometry. [Source](../../../src/herald_decoder/planar_ml.py).

## Full-prior update

The domain is p in [0,1]. Deterministic p=1 records are supported and impossible records rejected. The herald planar/MPS wrappers also use the width-capped exact transfer fallback when 1−10^{-12}<p<1. Literal transfer priors are (1−p,p); no complement folding is used.
