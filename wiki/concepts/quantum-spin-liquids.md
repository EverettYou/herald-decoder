---
title: Quantum spin liquids
page_type: concept
status: established-background
updated: 2026-09-04
source_refs:
  - references/savary2016-quantum-spin-liquids/paper.pdf
  - references/essin2012-fractionalization-z2-spin-liquids/paper.pdf
  - references/qi2016-fractionalization-z2-spin-liquids/paper.pdf
  - references/zaletel2015-space-group-fractionalization/paper.pdf
  - references/barkeshli2014-symmetry-fractionalization/paper.pdf
  - references/zhou2016-quantum-spin-liquid-states/paper.pdf
  - references/yao2011-su2-kitaev/paper.pdf
idea_ids: []
topics: [Topological Phases, Symmetry-Enriched Systems]
---

# Quantum spin liquids

**Summary**: Quantum spin liquids are highly entangled phases of quantum matter that can host emergent gauge structure, fractionalized excitations, and intrinsic or symmetry-enriched topological order.

**Sources**: [Quantum Spin Liquids](/reference?id=savary2016-quantum-spin-liquids); [Classifying Fractionalization](/reference?id=essin2012-fractionalization-z2-spin-liquids); [Classification of Symmetry Fractionalization](/reference?id=qi2016-fractionalization-z2-spin-liquids); [Measuring Space-Group Symmetry Fractionalization](/reference?id=zaletel2015-space-group-fractionalization); [Symmetry Fractionalization, Defects, and Gauging](/reference?id=barkeshli2014-symmetry-fractionalization); [Quantum Spin Liquid States](/reference?id=zhou2016-quantum-spin-liquid-states); [Fermionic Magnons and Non-Abelian Spinons](/reference?id=yao2011-su2-kitaev)

**Last updated**: 2026-09-04

## Overview

Quantum spin liquids are highly entangled spin phases without conventional magnetic long-range order. Their low-energy descriptions can include emergent gauge fields and fractionalized excitations such as spinons, and some are intrinsically topologically ordered. [Savary and Balents (2016), abstract and §§1–5](/reference?id=savary2016-quantum-spin-liquids)

Topological excitations in appropriate QSL phases can carry both topological data and symmetry quantum numbers. QSLs nevertheless include a broad range of phases: not every QSL is intrinsically topologically ordered, and spin-orbit coupling or other anisotropies can reduce or remove spin-rotation symmetry. [Zhou, Kanoda, and Ng (2017), abstract and §§I–III](/reference?id=zhou2016-quantum-spin-liquid-states)

## Spin symmetry and fractionalized excitations

In a gapped \(\mathbb Z_2\) spin liquid, an anyon can carry a fractionalized symmetry action. For internal \(SO(3)\) spin rotation, this is expressed by a projective representation; a spinon with half-integer spin is the familiar physical example. Symmetry fractionalization classes distinguish otherwise identical topological orders and are constrained by microscopic spin content and lattice symmetry. [Essin and Hermele (2013), abstract and §§III–IV](/reference?id=essin2012-fractionalization-z2-spin-liquids) [Qi and Cheng (2016), abstract](/reference?id=qi2016-fractionalization-z2-spin-liquids)

For spin systems, \(SO(3)\) is often the faithful physical spin-rotation group while \(SU(2)\) is its double cover used to label half-integer representations. The proposed project language should state this convention rather than treating \(SU(2)\) as an automatic property of all QSL candidates.

## An exactly solvable SU(2) spin-liquid example

Yao and Lee construct an exactly solvable spin-\(1/2\) model on the decorated honeycomb lattice with global
\(SU(2)\) symmetry. In their time-reversal-broken phase, a \(\mathbb Z_2\) vortex binds three Majorana zero
modes; the paper identifies the resulting deconfined vortex as a spin-\(1/2\), non-Abelian spinon. This is a
concrete microscopic setting where global spin symmetry and non-Abelian excitations coexist. [Yao and Lee
(2011), abstract and pp. 1–4](/reference?id=yao2011-su2-kitaev)

Its relevance here is motivational rather than operational. The paper does not define a syndrome-extraction
protocol, a current representation-resolved readout, a herald likelihood, or a quantum-error-correction decoder.
It therefore cannot validate the project's \((m,R)\) observation model by itself.

## From abstract symmetry data to observables

SET data is more than a label on an anyon: it describes how symmetry acts in the presence of topological order. The general framework can include non-Abelian anyons, symmetry permutations, defects, and gauging. [Barkeshli, Bonderson, Cheng, and Wang (2019), abstract and §§I–IV](/reference?id=barkeshli2014-symmetry-fractionalization)

For \(\mathbb Z_2\) spin liquids with \(SU(2)\) spin-rotation invariance, symmetry-fractionalization information can be tied to robust ground-state quantum numbers and other physical diagnostics in specified geometries. [Zaletel, Lu, and Vishwanath (2015), abstract and §§I–III](/reference?id=zaletel2015-space-group-fractionalization)

## Distinct symmetry structures

The term \(SU(2)\) can refer to several distinct structures in the spin-liquid literature. It may denote a physical global spin symmetry, label an excitation irrep, or describe an emergent gauge redundancy in a parton construction. These structures have different observables and different constraints, and should not be identified without a microscopic mapping.

Ordinary finite-dimensional \(SU(N)\) tensor-product rules are likewise distinct from the categorical fusion, braiding, and associator data of an anyon theory. [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]] records the representation-theory conventions used for the former.

## Related pages

- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]]
- [[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking and decodability]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
