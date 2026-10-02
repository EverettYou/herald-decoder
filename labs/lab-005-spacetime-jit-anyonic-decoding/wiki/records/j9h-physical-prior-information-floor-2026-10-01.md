---
title: Conservative physical-prior information floor from three D4 first records
status: current
updated: 2026-10-01
---

## Summary

Under the frozen ideal L=2 D4 two-stage instrument and IID red-X rate `p_X=1/10`, the second full public record has strictly positive conditional information about the private error even after *all* other physical-prior errors and first records are admitted. For a globally fixed singleton public charge action, `I(E;O₂ | O₁,a)` is at least `2.5078403×10⁻⁵` bits; for the separately fixed five-edge action, it is at least `3.0651381×10⁻⁵` bits. These are rigorous conservative lower bounds, not actual channel information or a comparison of actual action values. No logical-class or decoding-risk gain is inferred.

## Evidence

The [prospective contract](../../manifests/j9h-physical-prior-information-floor-2026-10-01.json) freezes three previously selected distinct complete first public records, their two equal-prior three-edge private errors each, the two relation-free fixed actions, and the [twelve complete public second laws](../../results/j8v-equal-prior-collision-second-laws-2026-09-28.json). The [machine certificate](../../results/j9h-physical-prior-information-floor-2026-10-01.json) replays all twelve normalized full flux/charge/vacuum laws, six exact total-variation distances `(3/4,3/4)`, `(0,1/2)`, `(0,0)`, and the earlier [joint first masses](../../results/j8w-same-flux-posterior-certificate-2026-09-28.json). It uses `0.00887` CPU seconds, with no new Born term, law, history, arm or bootstrap.

For each selected first record `oᵢ`, the equal first likelihoods and equal IID prior make the two selected errors equiprobable *within their pair*. Introduce a pair-membership indicator and apply the mutual-information chain rule: the contribution at `oᵢ` is at least the pair's joint physical probability times the Jensen–Shannon information between its two conditional second laws. Binary Pinsker bounds that information below by `TVᵢ²/(2 ln 2)` bits. The three first records are disjoint; all other first-record and error contributions are nonnegative. Thus each fixed action has an exact rational coefficient `Cₐ=Σᵢ P(E in pairᵢ,O₁=oᵢ) TVᵢ,ₐ²`, with `I(E;O₂|O₁,a)≥Cₐ/(2 ln 2)`:

| Fixed public action | Exact `Cₐ` | Conservative floor |
| --- | --- | ---: |
| singleton `[0]` | `278128389443693511257285776231761/8000000000000000000000000000000000000` | `2.5078403×10⁻⁵` bits |
| five-edge `[1,30,32,34,35]` | `339934698208958735981127059838819/8000000000000000000000000000000000000` | `3.0651381×10⁻⁵` bits |

The first likelihood `1` stratum contributes to both actions; the `1/2` stratum contributes only to the five-edge action, and the `1/4` stratum is a null control. The positive result needs no imputation of the other errors' first or second laws.

## Status

The registered six-cell arithmetic certificate passes. It establishes strict positivity of ideal *private-error* information under each separately precommitted fixed action, not the actual full-channel information. The unequal lower bounds do not rank the actions' actual information. It does not establish information about the logical class, a logical Bayes-risk improvement, a noisy or adaptive JIT benefit, size scaling or a threshold. The J9G upper bound concerns a *different selected first record*; its number must not be pooled with these floors. The next useful question is whether the finite private-error information is about distinct logical classes under a matched physical-prior scorer, or only about errors within one class.

## Related pages

- [[schedule-state|Schedule state]]
- [[records/j8v-equal-prior-collision-second-laws-2026-09-28|Frozen finite pair laws]]
- [[records/j8w-same-flux-posterior-certificate-2026-09-28|Frozen physical pair masses]]
- [[records/j9g-omitted-second-law-bound-2026-09-28|Separate selected-record upper bound]]
