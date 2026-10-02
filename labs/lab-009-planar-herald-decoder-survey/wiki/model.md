---
title: Classical herald model and logical loss
page_type: model
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Classical herald model and logical loss

## Summary

This page fixes the classical honeycomb geometry, public syndrome/herald record, and logical failure definition used by Lab 009.

## Evidence

The [lightweight validation](../results/validation.json) exercises the stated record and correction contracts; the precise model definitions follow below.

## Status

Current for this classical binary channel; it does not specify a noisy quantum fusion instrument.

## Related pages

- [[statistical-mechanics|Sector partition functions]]
- [[comparison|Decoder comparison]]

## Geometry and visible information

The canonical honeycomb patch retains the merged hexagon edges after removing the exposed sides specified in the model. Isolated tips stay in the vertex inventory. Rough boundary vertices are unmeasured; every nonisolated rough vertex has degree one. Detectors have degree two or three. The patch has $E=3L^2-1$ edges and $D=2L^2-2$ detectors; its shortest left-to-right logical path has $d=2L-1$ edges. Thus $L$ is a linear size, not the code distance. The check matrix $H$ is detector-edge incidence modulo two; the package's cut vector $\ell$ measures the chosen nontrivial left-right class.

The physical domain is $0\le p\le1$, $0\le q\le1$. Neither half-domain truncation nor interior-q complement symmetry is assumed.

Draw independent edge bits $x_e\sim\operatorname{Bernoulli}(p)$. At each measured vertex,

$$
n_v(x)=\sum_{e\ni v}x_e,\qquad s_v=n_v(x)\bmod2.
$$

Given $x$, herald coins are independent, with

$$
P(h_v=1\mid x)=q\,1\{n_v(x)\ge2\}.
$$

There are no false positives, no noisy syndrome and no temporal rounds. Heralds are generally correlated after marginalizing $x$. Decoder-visible input is $(G,p,q,s,h)$; sampled errors and private coins are used only by the scorer. Measured-boundary factors must not be added to rough tips.

## Literal likelihood and endpoints

The site likelihood is

$$
\phi_q(h,n)=
\begin{cases}
q\,1\{n\ge2\},&h=1,\\
1-q\,1\{n\ge2\},&h=0.
\end{cases}
$$

The edge prior is $w_e(0)=1-p$, $w_e(1)=p$. The joint unnormalized posterior weight is

$$
W(x;s,h)=1\{Hx=s\}\prod_e w_e(x_e)\prod_{v\in D}\phi_q(h_v,n_v(x)).
$$

At $p=1$, the all-edge error vector is deterministic: $s=H\mathbf1$, and heralds are eligible coins at every degree-two/three detector. Its logical bit is known, giving zero optimal risk. At $p=0$, only $(s,h)=(0,0)$ is possible and decoding is exact. At $q=0$, a positive herald is impossible. At $q=1$, parity and herald together fix $n_v=s_v+2h_v$, whenever that count fits the degree. At $(p,q)=(1/2,0)$, the two logical sectors have equal weight, giving Bayes risk $1/2$. Impossible records are rejected instead of assigned an arbitrary correction.

## What counts as successful decoding

Return a binary edge correction $c$ with $Hc=s$. Its logical failure is $\ell(x\oplus c)=1$. The correction does not need to reconstruct $x$, and need not itself reproduce $h$. Two corrections with the same syndrome and logical parity have identical loss. This allows a sector solver to return a canonical forest representative even when its local counts differ from the sampled record. A configuration-MAP solver here returns its actual maximizing configuration, which is a stronger output convention, not a different success criterion.

The absolute-sector sums are

$$
Z_a(s,h)=\sum_{x:Hx=s,\ \ell(x)=a}\prod_e w_e(x_e)\prod_v\phi_q(h_v,n_v(x)).
$$

Logical ML chooses the larger $Z_a$; its conditional risk is $\min(Z_0,Z_1)/(Z_0+Z_1)$. Configuration MAP chooses a largest individual $W(x)$ and returns that configuration's sector. BP estimates edge marginals, then matching projects marginal log odds into a valid correction. These three objectives are distinct.

## Scope boundary

This model is binary and classical. A full-irrep record can be inserted as a nonnegative local binary factor only when it really factorizes given these edge variables. Hidden orientations, higher-valence fusion spaces, temporally correlated measurements and noncommuting instruments require a new observation model. The degree-four matchgate identity is a real extra restriction; planarity alone does not solve arbitrary square-lattice likelihoods. See [the planar mapping](planar-ml.md) and [the comparison](comparison.md).
