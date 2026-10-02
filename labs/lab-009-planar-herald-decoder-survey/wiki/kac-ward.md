---
title: Kac–Ward even-subgraph determinant and finite penalties
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Kac–Ward even-subgraph determinant and finite penalties

## Summary

The determinant gives a useful research cross-check but finite penalties do not justify production promotion.

## Evidence

The [research validation](../results/validation.json) records bounded finite-size numerical discrepancies and failures; the formulation follows.

## Status

Current as a research comparison only, not a registry decoder.

## Related pages

- [[statistical-mechanics|Sector partition functions]]
- [[comparison|Decoder comparison]]

## From site signatures to an even-subgraph polynomial

For a strictly positive degree-three even tensor $(g_0,g_1,g_2,g_3)$, write

$$
g(z)=g_0\prod_i a_i^{z_i},\qquad
(a_1,a_2,a_3)=\left(\sqrt{bc/a},\sqrt{ac/b},\sqrt{ab/c}\right),
$$

where $(a,b,c)=(g_1,g_2,g_3)/g_0$. The two-bit entries are reproduced by pairwise products of leg weights. At degree two, each leg can carry $\sqrt{g_{11}/g_{00}}$. Multiply each lattice wire prior $t_e$ by the leg weights at its measured endpoints. The rough-boundary rail has unit factors and carries the sector marker. After dropping common site constants this produces

$$
P(w)=\sum_{z\ {
m even}}\prod_e w_e^{z_e}.
$$

For a planar embedded graph, index directed edges. If directed edge $a$ ends where $b$ starts and $b\ne\bar a$, set $T_{ab}=w_b\exp(i\theta(a,b)/2)$, where $\theta$ is the principal turning angle. Otherwise set it to zero. The Kac–Ward relation is $\det(I-T)=P(w)^2$ for compatible conventions. [Lis, a short proof](https://arxiv.org/abs/1502.04322) supplies the underlying theorem.

## Extracting the sector without taking a square root

The logical rail-edge occupancy is the derivative of $\log P$ with respect to that wire's log weight. Hence

$$
P_{\rm relative}(1)=-\tfrac12\operatorname{tr}\left[(I-T)^{-1}
\frac{\partial T}{\partial\log w_{\rm rail}}\right].
$$

This avoids choosing a complex square-root sign. Translate relative to absolute sectors with the reference parity as in [planar ML](planar-ml.md). The lab implementation uses a dense complex solve and checks probability range and imaginary residue. This is not the sparse scalable backend chosen for standard use.

## Hard zeros and why the current branch is approximate

The leg formulas divide by weights and take square roots, so literal forbidden configurations can be singular. The research implementation replaces each zero site entry by $\exp(-\lambda)$ after normalization. For finite $\lambda$, forbidden configurations contribute positive weight. The determinant may be evaluated accurately while describing the wrong softened model. Increasing $\lambda$ decreases modeling error but can worsen matrix conditioning; a large fixed value is not a proof of exact support across $p\to0$ or all sizes.

The light size-three checks compare penalties 8, 12 and 16 to exact transfer. At nonzero herald availability, posterior discrepancies shrink with the penalty; they remain measurable at finite penalty. The $q=0$ checks have no hard herald zeros and agree to roundoff. The recorded convergence therefore diagnoses a useful limiting representation, not an exact continuous-domain decoder.

The algorithm remains [lab research code](../scripts/kac_ward.py), excluded from `DECODER_METHODS`. The [nonnegative matchgate gadget](planar-ml.md) handles zeros directly and meets the promotion gate without a finite penalty. A future exact Kac–Ward backend would need a hard-zero construction or rigorously controlled limit, explicit conditioning checks and matched runtime evidence. This is the same reason a fixed penalty in configuration MAP is replaced by a dominating integer construction.
