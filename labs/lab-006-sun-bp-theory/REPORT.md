# Lab 006 — SU(N) full-irrep belief propagation

## Overview

### L006.1 Motivation

This lab tests whether a symmetry-resolved irrep measurement can improve a
binary topological decoder without changing the decoder-visible syndrome. The
[Global Wiki method page](../../wiki/methods/sun-fusion-herald-belief-propagation.md)
is the source of truth for the probability model, the BP derivation, and the
proof relating a BP edge belief to the matching weight.

### L006.2 Background and key notation

Each edge has a binary error variable \(e_a\). At vertex \(v\), the decoder
observes exactly

\[
s_v=(m_v,R_v).
\]

Here \(m_v\) is the \(\mathbb Z_2\) boundary syndrome and \(R_v\) is the complete
measured \(\mathrm{SU}(N)\) irrep. The irrep is the heralding signal; there is no
additional coarse label \(H_v\) or noise parameter \(\eta\). The BP edge belief
is \(r_a=P_{\mathrm{BP}}(e_a=1\mid m,R)\), and its matching weight is
\(\widehat w_a=\log[(1-r_a)/r_a]\). The correction chain \(c\) must satisfy the
hard boundary constraint \(Ac=m\).

### L006.3 Question and frozen configuration

Can full-irrep conditioning be implemented correctly and efficiently, and
where does a fixed synchronous BP schedule fail on the canonical two-dimensional
geometries?

The registered studies use oriented fundamental/antifundamental pair errors,
a perfect \(m\) record, and a projective full-irrep record. Small-graph checks
use SU(3) at \(p=0.18\). The public workbench and convergence scan use the Lab
002 square and honeycomb lattices with rough left/right and smooth transverse
boundaries. The convergence scan freezes sizes 5 and 7, SU(2) and SU(3),
\(p\in\{0.1,0.2,0.3,0.4\}\), four seeds per cell, damping 0.25, 80 iterations,
and tolerance \(10^{-10}\).

### L006.4 Hypothesis and final algorithm

The hypothesis is that \(R\) changes useful edge posteriors while preserving
the same binary matching constraint, but that short loops can prevent or bias
BP convergence.

The implemented decoder is:

1. Read the vertex record \((m_v,R_v)\).
2. Build each local fusion likelihood from the incident representation leaves.
3. Run normalized, damped sum-product BP on the edge-variable/vertex-factor graph.
4. Convert every final edge belief \(r_a\) to the LLR weight
   \(\log[(1-r_a)/r_a]\).
5. Use PyMatching to minimize the weighted correction subject to \(Ac=m\).
6. Record convergence, residual, syndrome fidelity, and the registered logical diagnostic.

On a factor tree, the BP beliefs are exact posterior marginals. On a loopy
lattice, they are Bethe beliefs; the weighted matching step is an
independent-edge surrogate and is not generally the global MAP decoder.

## Evidence

### L006.5 Registered result summary

| Check | Frozen scope | Key result |
| --- | --- | --- |
| Exactness | SU(3) path and four-edge plaquette, \(p=0.18\) | Tree BP agrees with exact enumeration; the plaquette exposes the missing loop correlation. |
| Acceleration | 256 observations on a warmed 64-site SU(3) ring | Python/Numba marginals agree to \(1.88\times10^{-37}\); scalar and batched medians are 0.1739 ms and 0.0922 ms versus 144.1804 ms in Python. |
| Hard decoding | 16 registered matching checks | Every correction reproduces the supplied \(m\) syndrome. |
| 2D convergence | 128 paired square/honeycomb observations | Full-\((m,R)\) converges in 106/128 cases; matched \(m\)-only BP converges in 102/128. |
| Strongest failure direction | \(L=7\), honeycomb, SU(2) | Full-record BP converges in 0/4 cases at each of \(p=0.2,0.3,0.4\) under the frozen 80-iteration schedule. |

The local [Lab 006 overview](wiki/overview.md) records the same bounded
interpretation and identifies which claims remain unsupported.

### L006.6 Reader-facing artifact

The [fusion-aware workbench](figures/fusion-belief-matching.html) presents the
square and honeycomb geometries, the observed \((m,R)\) record, the change in
error log-odds caused by \(R\), the final correction, and the BP convergence
diagnostics. Red edges mean that \(R\) raises the inferred error odds; blue
edges mean that it lowers them. The workbench's
scientific boundary is summarized in the [Local Wiki](wiki/overview.md).

### L006.7 Evidence map

- [Exact posterior versus BP](results/small-graph-exact-vs-bp.json)
- [Accelerated belief-matching benchmark](results/a1-numba-belief-matching.json)
- [Two-dimensional convergence scan](results/a5b-two-dimensional-convergence-scan.json)
- [Detailed derivation and proof](../../wiki/methods/sun-fusion-herald-belief-propagation.md)
- [Local Wiki evidence boundary](wiki/overview.md)

## Analysis

### L006.8 Implications

The full-irrep likelihood, posterior-to-LLR interface, and hard matching
constraint form an executable decoding pipeline. The tree fixture verifies the
inference algebra, while the two-dimensional scan shows why agreement on a
ring cannot establish lattice-level convergence. This interpretation is also
recorded in the [Local Wiki](wiki/overview.md); the detailed mathematical
argument remains on the [Global Wiki method page](../../wiki/methods/sun-fusion-herald-belief-propagation.md).

### L006.9 Limitations

The fusion backend is audited only for U(1), SU(2), and SU(3) product
distributions through local degree four. The model assumes a perfect static
\(m\) record. Loopy BP need not equal the exact posterior, and four seeds per
cell support neither a threshold nor a general comparison of full-record and
\(m\)-only decoding. The 64-site ring is only an exactness/throughput fixture,
not the physical lattice model. See the [Local Wiki boundary](wiki/overview.md).

### L006.10 Next question

The next bounded experiment is a preregistered matched schedule/damping study
on the frozen honeycomb SU(2) failure seeds. It should test convergence and
posterior stability before any threshold or logical-rate study. The detailed
theory should continue to be maintained on the Wiki, while this report remains
the concise record of configuration and measured outcomes.
