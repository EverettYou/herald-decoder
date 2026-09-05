---
title: Symmetry-enriched topological order
page_type: concept
status: established-background
updated: 2026-08-26
source_refs:
  - references/garre-rubio2020-enriched-toric-code/paper.pdf
  - references/temkin2025-charge-informed-qec/paper.pdf
  - references/essin2012-fractionalization-z2-spin-liquids/paper.pdf
  - references/qi2016-fractionalization-z2-spin-liquids/paper.pdf
  - references/zaletel2015-space-group-fractionalization/paper.pdf
  - references/barkeshli2014-symmetry-fractionalization/paper.pdf
  - references/iqbal2023-nonabelian-topological-order/paper.pdf
idea_ids: []
topics: [Topological Phases, Symmetry-Enriched Systems, Quantum Error Correction]
---

# Symmetry-enriched topological order

**Summary**: Symmetry enrichment can attach symmetry structure to topological excitations, but a particular SET construction does not automatically supply a measurable non-Abelian herald or a decoder advantage.

**Sources**: [String Order Parameters for Symmetry Fractionalization in an Enriched Toric Code](/reference?id=garre-rubio2020-enriched-toric-code); [Charge-Informed Quantum Error Correction](/reference?id=temkin2025-charge-informed-qec); [QSL symmetry-fractionalization background](/reference?id=essin2012-fractionalization-z2-spin-liquids); [General SET framework](/reference?id=barkeshli2014-symmetry-fractionalization)

**Last updated**: 2026-08-26

## Current synthesis

Garre-Rubio, Iqbal, and Stephen study a toric-code SET formed by decorating with lower-dimensional SPT structure. In their model, string order parameters characterize symmetry fractionalization and remain diagnostic under perturbations within the SET phase; they also analyze symmetry breaking associated with condensing a symmetry-fractionalizing anyon. [Garre-Rubio, Iqbal, and Stephen (2020), abstract and §§I–II](../../references/garre-rubio2020-enriched-toric-code/paper.pdf#Sec.I-Sec.II)

Temkin *et al.* instead use a \(U(1)\)-symmetry-enriched topological-memory model in which local anyon charge is explicitly measured for decoding. [Temkin *et al.* (2025), abstract](../../references/temkin2025-charge-informed-qec/paper.pdf)

## Representation data and operational data

An enriched topological phase combines topological data with a specified symmetry action. A representation label, a symmetry-fractionalization class, a local observable, and a decoding record are different kinds of data; relating them requires a model of the measurement process.

Finite-dimensional representation theory supplies a separate layer of bookkeeping: it fixes the allowed \(SU(N)\) labels and ordinary tensor-product channels, but does not turn those channels into topological anyon fusion data or a measurement protocol. [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]] and [[references/lieart|LieART]] record this distinction.

## Quantum spin-liquid realization and scope

Gapped \(\mathbb Z_2\) quantum spin liquids are a central physical realization of SET ideas: their anyons can carry projective symmetry actions, including fractional spin under \(SO(3)\) spin rotation. [Essin and Hermele (2013), abstract and §§III–IV](/reference?id=essin2012-fractionalization-z2-spin-liquids) A spinon with half-integer spin is one such possibility, subject to microscopic and lattice constraints. [Qi and Cheng (2016), abstract](/reference?id=qi2016-fractionalization-z2-spin-liquids)

The general SET framework also contains symmetry defects and categorical fusion data beyond ordinary representation products. [Barkeshli et al. (2019), abstract and §§III–V](/reference?id=barkeshli2014-symmetry-fractionalization) [[concepts/quantum-spin-liquids|Quantum spin liquids]] describes a broad class of condensed-matter realizations.

Non-Abelian topological order supplies an additional layer beyond symmetry enrichment: its anyons can have multi-channel fusion and noncommuting braid actions. A (D_4) topological-order state has been prepared and probed on a trapped-ion processor; its decoder significance requires a separate noise and measurement model. [Iqbal *et al.* (2024)](/reference?id=iqbal2023-nonabelian-topological-order) [[concepts/non-abelian-topological-order|Non-Abelian topological order]] records this distinction.

## Related pages

- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/charge-informed-decoding|Charge-informed decoding]]
- [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]]
- [[references/lieart|LieART]]
- [[concepts/quantum-spin-liquids|Quantum spin liquids]]
- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
