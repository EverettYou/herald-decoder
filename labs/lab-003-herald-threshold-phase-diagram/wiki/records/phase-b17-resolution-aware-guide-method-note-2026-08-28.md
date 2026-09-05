---
title: 'Phase B17 resolution-aware guide — registered method note'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# Phase B17 resolution-aware guide — registered method note

## Program alignment

This is a bounded Lab 003 presentation repair for the phenomenological
finite-window decoder evaluation. It does not advance the D4 physical-channel
or intrinsic-information program and must not be promoted as a thermodynamic
phase boundary.

## Question and intended claim

Can the current B14 honeycomb directional-evidence field be summarized without
inventing a low-q reversal or displaying a falsely narrow uncertainty band?
The allowed claim is only that a monotone dashed guide and a conservative
finite-grid transition region summarize the measured decoder-specific evidence.

The researcher supplies two constraints: the guide should not resolve an
unsupported low-q right-then-left feature, and fitting details should not be
printed on the figure. These are presentation and shape constraints, not new
data or a likelihood.

## Research basis

- Bolin and Lindgren, [Excursion and contour uncertainty regions for latent
  Gaussian models](https://arxiv.org/abs/1211.3946), show that marginal
  pointwise probabilities do not provide joint contour coverage and motivate
  reporting an uncertainty region for a contour rather than a narrow band
  around a selected line.
- Pya and Wood, [Shape constrained additive
  models](https://doi.org/10.1007/s11222-013-9448-7), provide a principled basis
  for treating monotonicity as an explicit shape constraint and for checking
  interval performance rather than tuning wiggles visually.
- NIST's [nonlinear least-squares
  guidance](https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd142.htm)
  distinguishes model-based confidence/prediction/calibration intervals; a
  shaded region must not be named a confidence interval without the associated
  model and coverage statement.

## Evidence and mathematical object

At each sampled cell, the existing B14 analysis uses binomial logical-error
counts, Jeffreys posteriors for latent LER, and the sign of the OLS projection
slope against the measured code distances. B11 converts the marginal 0.90
directional gate into sixteen finite-grid lower-transition brackets through
q=0.75.

B17 treats those brackets—not selected row roots—as the data-backed uncertainty
object. It adds explicit right-censoring brackets at q=0.80, 0.85, and 0.90 from
the high-p B14 cells. The displayed region is the narrowest nondecreasing
envelope containing all of these discrete brackets. It is deliberately called a
finite-grid directional bracket/censoring region, not a pointwise or
simultaneous confidence/credible set.

The dashed line is a separate visual guide. Its endpoints are derived from the
q=0 central LLR crossing and the p=0.49 high-q central LLR crossing. A cubic
Bezier with ordered p controls is fit to bracket midpoints, guaranteeing that
p(q) cannot reverse. No interval is attached statistically to this guide.

## Validation and failure rules

The result is accepted only if the guide is nondecreasing, the region contains
every registered bracket, the region is wider than the withdrawn B16 conditional
refit envelope, no method footer/curve legend remains, source hashes match, and
no decoder runs occur. If the high-q endpoint or topology requires a genuine
confidence set, B17 must remain exploratory and a future seed-cluster latent
surface analysis must be separately registered.

