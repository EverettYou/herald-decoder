---
title: Binary constraint rank and affine-class cost preflight
status: current
updated: 2026-09-27
---

## Summary

An exact orbit-character identity gives a much smaller *conditional* cost projection for first-projector terms. Across all 54 eight-edge supports and both fixed actions, the nonzero-character subset constraint has an affine solution class of at most four first-projector subsets. This does not itself compute the signs, second-charge moments or complete public laws.

## Evidence

The [prospective rank contract](../../manifests/j8g-binary-constraint-rank-preflight-2026-09-27.json) follows the pinned local exact identity: a Z character survives the ideal orbit only when its overlap parity with every orbit-flip generator is zero. First-subset Z signatures therefore form a GF(2) linear map; a reachable second-group signature has an affine preimage with size `2^(n-r)`, where `n` is the number of variable first stars and `r` the map rank. This is a project-specific algebraic fact. Binary/quadratic stabilizer representation has [primary methodological context](https://arxiv.org/abs/quant-ph/0304125), but that paper is not substituted for the local identity or control replays.

The [machine result](../../results/j8g-binary-constraint-rank-preflight-2026-09-27.json) covers all 54 supports and 108 action cells, including necessary-reachability replay on all 45 earlier completed supports. The rank is 4 for four supports, 6 for four, and 8 for 46. Affine preimage sizes are one for 24 supports, two for 12, and four for 18. The runner performs 2,832 signature tests, no orbit-expectation or complete-law evaluation, and passes before/after hash checks. Summing all nonempty second-variable groups gives a conservative 4,920 affine-class terms, using the earlier measured variable-site counts for 45 supports and the inherited bound of five for each of the nine unmeasured supports. Even adding 28,992 naive one-time first-subset preparation terms remains below the inherited 65,536 orbit-term ceiling, but these units are not a validation of the signed solver.

## Status

This reopens an affordable-looking exact computational route, *conditional* on the nine unmeasured supports having at most five variable second sites and on implementing/replaying the signed affine-class sum correctly. The 4,920-term figure is a structural upper bound under that condition, not a measured complete-law workload. Equal ranks or signatures do not prove a physical action-preserving symmetry or equality of public laws. The next bounded gate is a preregistered signed-sum identity on earlier complete-law controls plus exact singleton/site-count checks for the nine unresolved supports. Do not infer private-error information, logical risk, noisy JIT, L=3 or a threshold from this preflight.

## Related pages

- [[schedule-state|Schedule state]]
- [[records/j8f-orbit-character-reuse-audit-2026-09-27|Prior exact-character cap]]
- [[records/j8d-winding-class-second-law-witness-2026-09-27|Exact complete-law controls]]
