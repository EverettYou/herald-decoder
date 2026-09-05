---
title: 'Phase B18 symmetry-constrained guide — registered method'
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

# Phase B18 symmetry-constrained guide — registered method

The plotted phase-map coordinates are physical error probability `p` on the
horizontal axis and herald probability `q` on the vertical axis. The
researcher supplied the physical-model symmetry

\[
q_c(p)=q_c(1-p).
\]

Consequently the fundamental domain ends at `p=0.5` and a differentiable
boundary must satisfy `dq_c/dp=0` there. B17 did not: its linearly spaced q
controls gave a nonzero endpoint slope.

B18 retains the B17 evidence, brackets, and data-derived intercepts. Only the
guide parameterization and visible x domain change. It uses a parametric cubic
Bezier with controls `(p_i,q_i)`. Setting `q_2=q_3=q_c` while enforcing
`p_2<p_3=0.5` gives

\[
\left.\frac{dq}{dp}\right|_{u=1}
=\frac{3(q_3-q_2)}{3(p_3-p_2)}=0
\]

exactly. Ordered p and q controls prevent folds and reversal. The two interior
p controls are fit to the same B17 bracket midpoints; no cell labels, bracket
limits, or uncertainty claims are changed.

The current all-q honeycomb evidence has measured p centers only at
`0.08,0.12,...,0.49`. The figure will show the full `0<=p<=0.5` fundamental
domain but leave portions outside the measured cell edges blank. It will not
copy the p=0.08 color to p=0 or present p=0.5 as measured. No decoder run or
new decode is authorized.

