---
title: 'R1 periodic honeycomb constraint-generator audit'
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

# R1 periodic honeycomb constraint-generator audit

Date: 2026-08-28

## Transition

Implemented an LxL periodic bipartite honeycomb with `2L^2` blue/green vertices and `3L^2` error edges. Every edge retains its unwrapped blue-to-green cell displacement, allowing a lifted graph traversal to distinguish homologically trivial loops from torus-winding loops.

For each selected error subgraph, the generator classifies connected components as open/branched, nonbranching trivial loops, or nonbranching winding loops. Following Appendix A, it emits one independent even-parity constraint per colour for every nonbranching homologically trivial loop. It deliberately emits no even constraint for winding loops because their charge relation depends on the protected logical sector.

## Focused verification

The combined local-likelihood and topology suites pass 11 tests. They verify lattice counts/degree, a local hexagon's two colour constraints, winding-loop detection, branched-component exclusion, and normalization of all charge outcomes for a generated trivial loop.

## Exhaustive L=2 audit

The machine-readable audit exhausts all 4096 error subgraphs and 56,863 compatible raw charge assignments on the eight-vertex, twelve-edge torus.

- constraint-count failures: 0
- constraint-support failures: 0
- constraint-independence failures: 0
- Eq. A12 normalization failures: 0
- trivial nonbranching loop components: 4
- winding nonbranching loop components: 126

Evidence: `manifests/r1-periodic-constraint-generator-audit.json`.

## Claim boundary

The periodic topology and the source's trivial-loop constraints are verified. The observation generator is not yet complete for winding loops, whose measurement constraint depends on the chosen initial logical sector. The next bounded gate is a versioned sampler that normalizes every non-winding conditional distribution and explicitly flags rather than guesses logical-sector-dependent winding observations.

