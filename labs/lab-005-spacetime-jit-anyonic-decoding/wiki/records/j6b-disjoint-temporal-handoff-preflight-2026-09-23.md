---
title: Disjoint temporal-handoff pilot preflight
status: current
updated: 2026-09-23
---

## Summary

The separately registered J6B replacement pilot passed its deterministic
preflight. This releases only the fixed disjoint production cohort; no
replacement stochastic history, schedule arm, bootstrap replicate, or paired
risk estimate exists yet. The older J6 pilot remains closed censored.

## Evidence

The [immutable pilot contract](../../manifests/j6b-disjoint-temporal-handoff-pilot-2026-09-23.json)
and [machine-readable preflight](../../results/j6b-disjoint-temporal-handoff-preflight-2026-09-23.json)
bind the production runner and manifest SHA-256 values, frozen D4 source and
dependency hashes, legacy-J6 quarantine hashes, and pinned runtime versions.
All 26 selected public-path/model tests passed. Three new synthetic histories
expanded to 48 deterministic schedule-arm evaluations, under the 32-history
and 256-arm preflight ceilings. Each history produced eight unconditional
rows with bit-identical replay. The zero case had eight scored nonfailures;
the odd-then-even case retained two failed-closed rows instead of dropping
them. The exact causal odd-to-later-even, persistent-odd, same-round conflict,
future/private invariance, action-binding, full-binary charge-action, and
normalization assertions are owned by the selected test matrix.

The first runner smoke attempt stopped before any fixture because the pinned
research Python does not package `pytest` as a module. The runner was corrected
to use the existing pytest executable with the pinned environment's library
path, as in earlier Lab gates. The passing preflight supersedes that technical
attempt; neither attempt sampled the registered stochastic cohort.

## Status

The preflight's `production_armed` flag records a release gate, not completed
production or scientific evidence. The next bounded transition is a one-shot
272-history, 2,176-arm run under its fixed seeds, rates, unconditional loss,
event/resolution gates, hard resource caps, and stop rule. A gate failure must
censor all paired-risk interpretation; J6 and J6B may not be pooled.

## Related pages

[[schedule-state|Schedule state]] · [[spatial-policy-boundary|Spatial-policy boundary]]
