---
title: Three charge bits are the first discriminating marginal in one finite D4 witness
status: current
updated: 2026-09-28
---

## Summary

For the frozen positive second-record witness, the smallest public-charge joint marginal that distinguishes the two equal-prior private errors uses three sites. All single- and two-site marginals are identical. Two disjoint three-site sets—`[0,20,22]` and `[1,17,21]`—each have exact total variation `1/2` and charge-parity expectation difference `1`; the complete six-variable-site law has total variation `3/4`. This precisely localizes the finite higher-order information without implying a broader decoding gain.

## Evidence

The [prospective contract](../../manifests/j8z-minimum-joint-charge-order-2026-09-28.json) fixes first-flux mask `3591`, the same all-zero-charge complete first record, private errors `[0,5,16]` and `[2,4,15]`, the five-edge public action `[1,30,32,34,35]`, and the six variable public charge sites `[0,1,17,20,21,22]` before contraction. The [exact result](../../results/j8z-minimum-joint-charge-order-2026-09-28.json) checks all 64 subsets of these sites, grouped by size zero through six, with both joint-marginal TV and charge-parity moments. It verifies that all other 18 charge sites are fixed identically for both errors, the six-site law replays complete-record TV `3/4`, every one-/two-site TV and parity difference is zero, and exactly two of the 20 three-site subsets are positive. The maximum TV is `1/2` at orders three through five and `3/4` at order six. Pinned hashes, exact normalization, data-processing and zero new Born/history/arm/bootstrap gates pass in `0.040845` CPU seconds.

## Status

The registered finite contraction is closed. Third-order public-charge correlation is necessary and sufficient for a *positive* distinction in this one cell, but not sufficient to reproduce its full six-site TV. The calculation does not establish an operator automorphism, law reuse in other sectors, full-IID information, logical-risk improvement, noisy JIT, scaling or threshold. The next bounded question is whether the two disjoint triple-parity signals have a simple validated operator relation; any channel-wide claim still requires other records and errors.

## Related pages

- [[schedule-state|Schedule state]]
- [[records/j8y-action-overlap-and-low-order-witness-2026-09-28|One-/two-site null and action-overlap diagnostic]]
- [[records/j8x-deterministic-first-collision-census-2026-09-28|Complete deterministic-first collision class]]
