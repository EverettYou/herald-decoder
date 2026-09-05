---
title: String-herald simulator model
page_type: model
status: implemented
updated: 2026-08-26
source_refs:
  - labs/lab-001-string-herald-visualization/PLAN.md
  - labs/lab-001-string-herald-visualization/REPORT.md
  - labs/lab-001-string-herald-visualization/figures/string-herald-sample.html
idea_ids: []
topics: [Quantum Error Correction, Topological Phases]
---

# String-herald simulator model

**Summary**: Lab 001 fixes a static, graph-level observation model for a surface-code-like lattice: independent binary edge errors generate an endpoint syndrome and a correlated fusion-remnant herald field. The model is a configuration simulator, not a threshold model or a microscopic fusion-history reconstruction.

**Sources**: [Lab 001: string-herald visualization](/lab?id=lab-001-string-herald-visualization)

**Last updated**: 2026-08-26

## Generative model

Let $G=(V,E)$ be a retained data-edge graph, with detector vertices $V_{\rm det}\subseteq V$. Each edge independently carries a binary error

\[
x_e\sim\operatorname{Bernoulli}(p).
\]

\[
0\le p\le\tfrac12.
\]

At every detector vertex define its incident error degree and parity syndrome by

\[
d_v=\sum_{e\ni v}x_e.
\]

\[
s_v=d_v\bmod2.
\]

The extra observation is a **fusion-remnant herald**, not an erasure location. A vertex can emit a herald only when at least two incident edges are erroneous:

\[
h_v^{\rm true}\sim
\begin{cases}
\operatorname{Bernoulli}(q),&d_v\ge2,\\
0,&d_v<2.
\end{cases}
\]

For the honeycomb variant, parity-readout error and one-way herald-extraction loss are explicitly separated:

\[
\tilde s_v=s_v\oplus m_v.
\]

\[
m_v\sim\operatorname{Bernoulli}(p_m).
\]

\[
h_v^{\rm obs}=h_v^{\rm true}(1-\ell_v).
\]

\[
\ell_v\sim\operatorname{Bernoulli}(p_h).
\]

Thus a herald changes the likelihood over the incident edge pattern; it neither marks an edge as missing nor identifies a specific error. [Lab 001 plan, Model and terminology boundary](../../labs/lab-001-string-herald-visualization/PLAN.md#model)

## Geometry, boundaries, and logical observable

The simulator instantiates both square and trivalent honeycomb graphs. In model coordinates, top and bottom boundaries are smooth; the left and right rough plaquettes are open. The outward rough-side edge is absent, and rough-side outer vertices do not contribute detector checks. Retained edges from such a vertex to an interior detector are singleton columns in the detector-by-edge parity-check matrix. [Lab 001 plan, Stage 2](../../labs/lab-001-string-herald-visualization/PLAN.md#stage-2--pymatching-mwpm)

The displayed view is rotated by $90^\circ$, so the rough boundaries appear at top and bottom. The logical observable is the parity of the displayed residual edges crossed by a fixed smooth-to-smooth dashed cut,

\[
\lambda_\Gamma(r)=\sum_{e\in C_\Gamma}r_e\bmod2.
\]

This is a configuration-level diagnostic. A nonzero $\lambda_\Gamma$ is a logical error for the displayed residual, not an estimate of a logical-error rate. [Lab 001 report, Findings](../../labs/lab-001-string-herald-visualization/REPORT.md#findings)

## Interpretation

At an ideal trivalent honeycomb vertex, parity and herald eligibility together distinguish degrees $0,1,2,3$; finite $q$, $p_m$, or $p_h$ convert that lookup into probabilistic side information. The simulator is therefore a common controlled input for hard-rule decoding in Lab 001 and posterior inference in Lab 002, rather than evidence that either decoder improves an asymptotic threshold.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/two-stage-herald-decoder|Two-stage herald decoder]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
