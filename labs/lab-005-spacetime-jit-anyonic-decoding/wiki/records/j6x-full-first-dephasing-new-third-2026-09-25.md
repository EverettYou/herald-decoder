---
title: Full-first loop dephasing and new-third-site discriminator
status: current
updated: 2026-09-25
---

## Summary

The two registered ideal diagnostics separate cleanly. A complete first loop charge measurement over all six variable sites has 16 positive records, not 64. On the one selected second site, every full-first-conditioned result is deterministic because that site is the same unchanged operator measured again. Coarse-graining to the two first sites used by the earlier local fixture gives `1/2` for the second `+` result in all four coarse records, exactly matching the earlier fixture; this specific contrast detects no dephasing change. The independent three-edge new-third-site branch is censored at its preregistered second-site selection gate, not repaired post hoc.

## Evidence

The [contract](../../manifests/j6x-full-first-dephasing-new-third-2026-09-25.json) pins the Jing source, L=2 embedding/orbit, earlier local result and unchanged five-round caller before computation. The [machine result](../../results/j6x-full-first-dephasing-new-third-2026-09-25.json) passes all five pins. All eligible first loop stars commute on the actual triangle sector; six have nonzero variance and the others are deterministic `+1`. Exact rational first mass sums to one over 16 positive six-bit records. After correcting edge 0, the one measured second star at site 17 is the *unchanged first-site-17 operator*: its charge bit repeats the first result with probability one. Averaging over the unshown first bits yields `P(second + | first sites 0,1)=1/2` for each coarse prefix, the same as measuring only those two first stars. This is not evidence of novel-site information or a full second public record.

For the separate physical chain `[0,4,3]`, the frozen first correction is edge 0. The preregistered second-site rule required exactly two eligible sites with nonzero *unconditional* variance; only site 2 qualifies. The branch therefore stops before evaluating the two registered third-action alternatives. This is an experiment-design censor, not a negative result about first-conditioned third information. In particular, a site with zero unconditional variance can become random after the first measurement, so a later conditional-site rule needs its own registration and validation.

## Status

The loop branch passes its exact full-first/one-site-second gates; the independent three-edge branch is explicitly censored. The shared 60-CPU-second cap, zero-history/arm/bootstrap rule, and unchanged caller all hold. The separately registered [conditional-site/nonrepeat follow-up](j6y-conditional-site-nonrepeat-matrix-2026-09-25.md) now resolves this specific selection censor as a selected-local negative control. The noisy five-round performance branch remains frozen.

## Related pages

- [[schedule-state|Schedule state]]
- [[records/j6w-loop-and-three-block-ideal-projector-matrix-2026-09-25|Prior selected-projector fixture]]
- [[records/j6s-repeat-transfer-four-site-2026-09-25|Repeat-versus-transfer control]]
- [[records/j6y-conditional-site-nonrepeat-matrix-2026-09-25|Conditional-site/nonrepeat follow-up]]
