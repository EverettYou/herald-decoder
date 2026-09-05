---
title: 'R2 post-flux local-rule matrix audit'
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

# R2 post-flux local-rule matrix audit

## Source transcription

Appendix A page 13 prints seven local physical-error/correction cases for one blue or green star and its three opposite-colour neighbors. Using the table's vertical top arm and two diagonal bottom arms, the implementation records the physical arm mask, correction arm mask, whether an intermediate e measurement followed the physical error, and the resulting entangled neighbor set. Direct visual reinspection of the source fixes that flag to false for rows 1-3 and 7, and true only for rows 4-6.

Rows 1-5 and 7 entangle the top and bottom-right neighbors. Row 6 entangles all three neighbors. The implementation generates the two other lattice rotations algebraically, yielding 21 distinct accepted configurations. Reflections or arbitrary unlisted cases are not inferred: an input outside the printed rows and rotations fails closed.

## Verification

Four new tests verify:

- all seven printed rows exist once and preserve their printed output;
- all 21 rotations are distinct and return the correctly rotated entangled-neighbor directions;
- two-neighbor rules emit one DSU union and the all-three rule emits two unions spanning all neighbors; and
- unlisted configurations are rejected.

The complete Lab 004 suite now passes 64 tests, including regressions for the reflected-mask ambiguity and the distinct union/XOR homology semantics.

## Claim boundary

This audit verifies the printed canonical diagrams and their rotational closure only. Integration against arbitrary MWPM outputs exposed mirrored configurations that the seven diagrams do not uniquely specify: closing the table under reflection makes some masks map to different entangled-neighbor pairs. The table lookup therefore remains a fail-closed source-diagram diagnostic and is not used to infer the production parity graph.

The production implementation instead uses the source's global invariant stated immediately after the table: every connected component of the union of physical and correction X strings induces exactly one blue and one green parity component. This distinction prevents a visually plausible local-frame convention from becoming an unsupported decoder rule.

