---
title: 'Phase B15 method note — constrained neural versus spline boundary summaries'
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

# Phase B15 method note — constrained neural versus spline boundary summaries

This is a design-only review: it does not alter the active B13 evidence map, collect data, or promote a phase-boundary claim.

The B13 field is $\ell(p,q)=\log[\Pr(\mathrm{upward}\mid\mathrm{data})/\Pr(\mathrm{downward}\mid\mathrm{data})]$. Direct contouring is rejected: the 21 q rows have 0--6 adjacent-p sign changes, so marching squares would make noise-following loops.

For the requested neural implementation, do not use a free $(p(u),q(u))$ curve: it can fold and create multiple p values at one q. Parameterize the lower-boundary summary as $q=u$ and $p_\theta(q)=p_{\min}+(p_{\max}-p_{\min})\sigma[f_\theta(q)]$, where $f_\theta$ is a one-hidden-layer tanh PyTorch MLP of width at most three. Fit only the 16 q rows with audited two-sided B11 lower brackets, and never extrapolate into q=0.80--1.00.

Let $s_{ij}=\tanh[\ell(p_j,q_i)/\ell_0]$ and let $[a_i,b_i]$ be the B11 lower bracket. With a preregistered transition-band mask $\mathcal T$, minimize $\sum_{i,j\in\mathcal T}w_{ij}\operatorname{softplus}[-s_{ij}(p_j-p_\theta(q_i))/\tau]+\lambda_b\sum_i(\operatorname{ReLU}(a_i-p_\theta(q_i))^2+\operatorname{ReLU}(p_\theta(q_i)-b_i)^2)/(b_i-a_i)^2+\lambda_1\int[p_\theta'(q)]^2dq+\lambda_2\int[p_\theta''(q)]^2dq+\lambda_w\lVert\theta\rVert_2^2$. The sign term places negative LLR evidence on the low-p side and positive evidence on the high-p side; the bracket term keeps the curve within audited discrete evidence; derivative penalties suppress slope and wiggle.

QMC standard error is computational error, not experimental precision. Bootstrap seed-cluster replicates of the underlying LER measurements must recompute LLR and brackets before refitting.

Anti-overfitting gates: compare against an interval-constrained cubic spline using leave-one-q-row-out prediction; use the neural model only if it wins beyond the one-standard-error rule. Repeat at least 16 initializations and bootstrap fits. Draw a dark dashed median only where at least 90% of fits have a valid bracket; add a light 90% envelope and leave a gap when it exceeds 0.08 in p or reaches the sampled-grid edge. Label the result a regularized finite-window LLR=0 summary, not a thermodynamic phase boundary.

The spline remains the lower-complexity baseline because it has fewer effective degrees of freedom and is easier to audit. Penalized spline smoothness is standard ([Wood 2003](https://doi.org/10.1111/1467-9868.00374)); contour/level-set work likewise treats uncertainty around a contour as part of the result ([Gotovos et al. 2013](https://www.ijcai.org/Proceedings/13/Papers/202.pdf)).

## Researcher decision and completion contract — 2026-08-28

The researcher requested that both constrained models be run and shown as a
direct comparison; neither is preselected as the reported winner. Phase B15
therefore has two peer branches:

1. the bounded width-three tanh neural function described above; and
2. an interval-constrained penalized cubic spline using the same rows,
   brackets, bootstrap resamples, display gaps, and claim boundary.

The current Phase B13 raster is not a valid frozen input because the audited
Phase B14 measurements have not yet been analyzed and merged. The mandatory
prerequisite is the preregistered B14 branch-separated analysis and a
data-currency update that identifies the exact B14-compatible evidence field.
No B15 fit may run on the superseded B13-only field.

Before fitting, freeze one shared comparison manifest containing source hashes,
the eligible q rows, transition mask, bracket constraints, regularization
grids, leave-one-q-row-out folds, bootstrap resamples, random seeds, and stop
rules. Both branches must be evaluated on identical evidence and report:

- held-out sign-prediction log loss and bracket violations;
- effective roughness and maximum slope/curvature;
- median curve, 90% envelope width, valid-row coverage, and edge/gap counts;
- initialization/bootstrap instability and wall time; and
- pairwise curve displacement with uncertainty.

The requested deliverable is a side-by-side comparison figure and a
machine-readable score table, followed by a concise report interpretation.
The figure may show both regularized finite-window `LLR=0` summaries but must
not call either a thermodynamic phase boundary, extrapolate into unbracketed
q rows, hide disagreement, or automatically convert a lower validation score
into a physical conclusion. No new decoder runs or adaptive sampling are part
of B15.

