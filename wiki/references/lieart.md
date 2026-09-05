---
title: LieART
page_type: reference
status: archived
updated: 2026-08-27
source_refs:
  - references/feger2019-lieart2/paper.pdf
  - references/lieart-code/provenance.json
idea_ids: []
---

# LieART

**Summary**: LieART is a Wolfram Language toolkit and accompanying publication for finite-dimensional Lie-algebra representation calculations, including roots, weights, tensor-product decompositions, and subalgebra branching.

**Sources**: [LieART 2.0](/reference?id=feger2019-lieart2); [LieART implementation](/reference?id=lieart-code)

**Last updated**: 2026-08-27

## Scope and capabilities

LieART represents irreps internally by Dynkin labels and provides root and weight systems, representation properties, \(SU(N)\) Young tableaux, tensor-product decomposition, and subalgebra branching. The paper describes a Young-tableau path for \(SU(N)\) tensor products and Klimyk’s formula for the general case. [Feger, Kephart, and Saskowski (2019), §§3.2–3.5 and §5.4](/reference?id=feger2019-lieart2)

The archived repository is a Wolfram paclet, version 2.1.1, with its main package, branching-rules package, table-generation code, Mathematica documentation, and a LaTeX style asset. Its documented public operations include Irrep, WeightSystem, YoungTableau, DecomposeProduct, and DecomposeIrrep. [LieART implementation, README, PacletInfo.wl, and Kernel/LieART.wl](/reference?id=lieart-code)

## Mathematical boundary

LieART computes ordinary finite-dimensional representation data. Tensor-product multiplicities such as

\[
R_1\otimes R_2=\bigoplus_R N_{R_1R_2}^{R}R
\]

are distinct from level-truncated anyon fusion, braiding, and associator data in a topological quantum field theory. [LieART 2.0, program summary and §5.4](/reference?id=feger2019-lieart2)

## Related pages

- [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[concepts/quantum-spin-liquids|Quantum spin liquids]]
