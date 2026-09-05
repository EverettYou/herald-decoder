---
title: Lie groups, Lie algebras, and representations
page_type: concept
status: established-background
updated: 2026-09-04
source_refs:
  - references/feger2019-lieart2/paper.pdf
  - labs/lab-006-sun-bp-theory/REPORT.md
idea_ids: []
topics: [Symmetry-Enriched Systems, Topological Phases]
---

# Lie groups, Lie algebras, and representations

**Summary**: Representation data gives a precise language for the proposed \(SU(2)\) extension: an excitation may carry an irrep, and combining excitations decomposes a tensor product into representation channels. This is necessary bookkeeping for a model, not yet evidence for a measurable herald or a decoding advantage.

**Sources**: [LieART 2.0](/reference?id=feger2019-lieart2)

**Last updated**: 2026-09-04

## Representation labels and channels

For a compact symmetry such as \(SU(2)\), finite-dimensional irreducible representations can be labelled by a highest weight (equivalently a Dynkin label). A tensor product decomposes into irreps with non-negative multiplicities,

\[
R_1\otimes R_2=\bigoplus_R N_{R_1R_2}^{R}R.
\]

For the project's motivating spin-\(1/2\) example,

\[
\tfrac12\otimes\tfrac12=0\oplus1.
\]

The labels \(0\) and \(1\) are representation channels of this ordinary \(SU(2)\) tensor product. They supply a notation for stating what a putative local measurement resolves; they do not by themselves specify the measurement, its noise, or a probability distribution over outcomes. [Feger, Kephart, and Saskowski (2019), §§3.1–3.2 and §5.4](/reference?id=feger2019-lieart2)

## What this does and does not mean by fusion

The multiplicities \(N_{R_1R_2}^{R}\) above are finite-dimensional Lie-group tensor-product multiplicities. In this Wiki they should not be silently identified with the fusion rules of an \(SU(N)_k\) topological phase, which can be level-truncated and requires additional categorical data such as associators/\(F\)-symbols. A future microscopic anyon model must state which of these two structures it uses.

This distinction matters for decoding. The current representation-resolved model uses a static classical record
\((m,R)\), not a fusion tree or a history reconstruction. Representation theory validates the allowed symmetry
labels and candidate local channels; the \(\mathbb Z_2\) boundary label and the SU(N) irrep still arise from
different gauge and symmetry sectors.

## Computational reference

[[references/lieart|LieART]] collects the associated paper and Wolfram implementation for finite-dimensional representation calculations.

## From representation channels to a decoder likelihood

[[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]] gives one explicit
operational model under a maximally mixed local leaf state and a projective total-irrep measurement. It weights
a latent irrep $R^\star$ by its isotypic-block dimension,

\[
P(R\mid L)=\frac{M^R_L\dim R}{\prod_{\ell\in L}\dim\ell},
\]

The irrep's intrinsic center label is its $N$-ality in $\mathbb Z_N$, not a universal independent
$\mathbb Z_2$ grading. For leaf lists containing only $F$ and $\bar F$, this $N$-ality determines the leaf-number
parity when $N$ is even. It does not do so in general when $N$ is odd; the $SU(3)$ singlet, for example, occurs
in both zero and three fundamentals. A fixed low-degree local fusion table can still make parity derivable, so
redundancy must be checked for the actual geometry.

In Lab 006, the complete irrep $R$ itself is the symmetry-resolved heralding signal. The local record contains
only $(m,R)$: $m$ is the $\mathbb Z_2$ topological/gauge-sector boundary and $R$ is the SU(N) symmetry-sector
label. For even $N$ and exact $F/\bar F$-only data, $N$-ality determines the parity; for odd $N$ it need not,
as the SU(3) singlet in both $3^{\otimes0}$ and $3^{\otimes3}$ demonstrates.
[Detailed Lab 006 derivation](../methods/sun-fusion-herald-belief-propagation.md)

## Open questions

- Which representation-resolved observable can be measured in one syndrome-extraction round in the proposed \(SU(2)\) model?
- Does the operational model use ordinary \(SU(N)\) tensor-product channels or level-truncated anyonic fusion data?
- Which channel record remains available to a decoder without recovering a fusion history?

## Related pages

- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/sun-fusion-herald-belief-propagation|SU(N) full-irrep belief propagation]]
- [[references/lieart|LieART]]
