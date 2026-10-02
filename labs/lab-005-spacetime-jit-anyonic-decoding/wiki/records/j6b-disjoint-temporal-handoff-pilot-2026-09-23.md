---
title: J6B disjoint temporal-handoff finite pilot
status: current
updated: 2026-09-24
---

## Summary

The fixed, disjoint J6B cohort ran exactly once and passed its registered
production integrity and event-resolution gates. The registered whole-history
paired analysis is now complete. Four of 14 exploratory pointwise contrasts
meet the predeclared proposal trigger, but their directions conflict and the
unconditional failure rates are near saturation. This is neither JIT
superiority nor a threshold result. The older J6 cohort remains censored and
separate.

## Evidence

The [immutable contract](../../manifests/j6b-disjoint-temporal-handoff-pilot-2026-09-23.json),
[passed preflight](../../results/j6b-disjoint-temporal-handoff-preflight-2026-09-23.json),
[complete unconditional arm rows](../../results/j6b-disjoint-temporal-handoff-rows-2026-09-23.jsonl),
and [machine-readable integrity result](../../results/j6b-disjoint-temporal-handoff-analysis-2026-09-23.json)
bind the result. The run generated 272 independent histories and 2,176 arm
evaluations, exactly eight rows per history, with zero bootstrap replicates.
All declared provenance and runtime hashes matched. The zero control and both
stochastic event gates passed: each stochastic cell had 128 histories with
nonempty detectors; each online mode/schedule had at least 56 real-action
histories, against a minimum of eight. Across both stochastic cells, each
public mode had 158 distinct histories with an odd defer followed by a later
even physical action, also above the minimum of eight. The raw-row SHA-256 is
`620c5db65231e5c112a497397aad168eefd7d284f1af362c52d512c6741fbefe`.

The unconditional records also retain 456 clean-herald and 466 joint-readout
rows with `ValueError:unresolved_temporal_boundary_handoff`; none were
discarded. The run used 46.97 CPU seconds, peaked at 124.5 MB RSS, and wrote
2.28 MB of raw rows, all below the hard caps. These are integrity and
mechanism-coverage diagnostics, not an estimate of logical-risk improvement.

The [paired analysis](../../results/j6b-disjoint-temporal-handoff-paired-analysis-2026-09-23.json)
uses all 128 independent histories in each stochastic cell for every arm,
including failed-closed rows. It reports pointwise 95% Wilson intervals for
arm risks and pointwise 95% percentile intervals from exactly 2,000
fixed-seed (`923242000`) whole-history resamples for each of 14 preregistered
online contrasts. The machine result preserves all estimates and discordant
pair counts. Four contrasts have absolute difference at least 0.05 and
pointwise intervals excluding zero:

| Cell | Paired unconditional failure-risk difference (left minus right) | Pointwise 95% interval |
| --- | ---: | ---: |
| Clean herald: heralded JIT − heralded fixed-delay | +0.0781 | [+0.0234, +0.1328] |
| Clean herald: heralded immediate − syndrome-only immediate | −0.0625 | [−0.1094, −0.0234] |
| Joint readout noise: syndrome-only JIT − syndrome-only immediate | +0.0703 | [+0.0234, +0.1250] |
| Joint readout noise: heralded immediate − syndrome-only immediate | +0.0703 | [+0.0234, +0.1250] |

The first and third rows favor simpler online schedules over JIT at this
particular finite pilot. The herald access effect changes sign between clean
and noisy readout; this is an operational heuristic-decoder result, not a
violation of optimal-information monotonicity. The other ten registered
contrasts do not satisfy the trigger. Arm failure fractions range from
0.7891 to 0.9922; the large unresolved-handoff component and near-ceiling
loss sharply limit mechanistic interpretation. Intervals are pointwise and
not adjusted for 14 comparisons. The trigger only permits proposing a
separate larger study; it does not authorize one or prove superiority.

A separately registered, read-only [outcome-attribution audit](../../results/j6b-d0-frozen-outcome-attribution-2026-09-23.json)
examined the same frozen rows after the paired analysis. Its
[descriptive contract](../../manifests/j6b-d0-frozen-outcome-attribution-2026-09-23.json)
fixed two complementary views before the audit: each arm's mutually exclusive
failed-closed/scored-failure/scored-success counts, and every original online
contrast's matched three-by-three outcome table. All 16 stochastic arms and
14 online contrasts close exactly on 128 histories per cell. The four
proposal-triggered contrasts decompose as follows; entries are counts on the
unchanged 128-history denominator, not a new test:

| Contrast, in table order above | Failed-closed difference | Scored-failure difference | Total failure difference |
| --- | ---: | ---: | ---: |
| Clean: heralded JIT − fixed-delay | +3 | +7 | +10 |
| Clean: heralded − syndrome-only immediate | 0 | −8 | −8 |
| Joint: syndrome-only JIT − immediate | +1 | +8 | +9 |
| Joint: heralded − syndrome-only immediate | 0 | +9 | +9 |

Thus the net differences that crossed the exploratory trigger are mostly
accounted for by already-scored logical failures, even though failed-closed
handoffs contribute heavily to absolute failure rates. This accounting does
not identify a causal mechanism: categories can change jointly on a matched
history, and the scored winding/residual flags overlap. In particular,
conditioning on scored rows would change the estimand and is not used here.

A separately registered [J6B-D1 scored-mask/timing audit](../../manifests/j6b-d1-scored-mask-timing-audit-2026-09-23.json)
then inspected every arm and original online pair on these same frozen rows.
Its [machine result](../../results/j6b-d1-scored-mask-timing-audit-2026-09-23.json)
passes exact mask and timing mass balance against D0. For the four JIT arms,
terminal residual is flagged in 57/61 and 57/60 clean-cell scored failures,
and 67/68 and 67/70 joint-noise scored failures (syndrome-only, heralded).
Zero or one physical commit appears in 54/61, 53/60, 57/68 and 59/70 of
those respective scored-failure rows. No scored row in this finite cohort has
physical winding. Charge, union and residual flags overlap; the mask counts
cannot be summed as exclusive causes. Matched mask transitions are only
descriptive because many online pairs contain a failed-closed side. No new
histories, arm evaluations, bootstrap replicates or significance tests were run.

A separately registered [deterministic residual/frame trace](../../manifests/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json)
then exercised five fixed, explicitly supplied five-round histories through the
same public interface and [recorded 40 unique arm rows](../../results/j6b-d2-deterministic-residual-frame-trace-2026-09-23.json)
(80 deterministic evaluations including exact replay). All scored terminal
residual flags equal an independently recomputed boundary of the final
physical chain XOR the latest committed public full-snapshot frame; all
Boolean-union losses and action-bound, relation-free second records replay.
The zero and single early-error cases clear in every arm. A single final-round
edge error clears under immediate, JIT and offline but leaves a residual under
fixed-delay-1, which has no final-round physical commit. Early and final
flips on the same edge cancel physically, yet fixed-delay-1 retains its stale
round-2 correction and a terminal residual. A readout-only odd round fails
closed under immediate but is resolved by later actions in the other three
schedules. Early causal outputs remain unchanged when a later fault is added.
These fixtures demonstrate internally consistent timing/frame semantics on
the selected cases. They neither explain how often each path occurs in the
stochastic J6B cohort nor validate a universal advantage of JIT.

A further [selected-history replay contract](../../manifests/j6b-d3-selected-frozen-history-replay-2026-09-23.json)
fixed the first existing syndrome-only JIT row in each of four strata per
stochastic cell: scored residual failure with zero, one, or multiple physical
commits, and scored success as a control. The [machine trace](../../results/j6b-d3-selected-frozen-history-replay-2026-09-23.json)
reproduces all eight selected seed/key/history digests and all 64 stored arm
rows exactly. The first attempt was censored before interpretation by an
off-by-one diagnostic detector-row index; the corrected trace preserves that
failure, changes no scientific input, and passes exact replay and independent
final residual/frame identity.

| Selected path (one per cell) | Clean-herald example | Joint-readout-noise example |
| --- | --- | --- |
| No JIT physical commit, residual failure | Final hidden syndrome is nonzero with zero public correction | Same observation; public/private readout first differs at round 2 |
| One JIT commit, residual failure | Last commit is round 1, residual is clear then, and a later physical transition occurs | Last commit is round 4; readout differs from hidden syndrome and residual is already present at commit |
| Multiple JIT commits, residual failure | Last commit is round 3, residual is clear then, and a later physical transition occurs | Last commit is round 4; readout differs from hidden syndrome and residual is already present at commit |
| Scored success control | Final residual clear after a round-4 commit | Final residual clear after a round-3 commit |

The same selected histories were replayed under both public modes and all
four schedules, but this table describes only their syndrome-only JIT rows.
The mismatch and timing flags overlap and are post-hoc case descriptions,
not exclusive physical causes or population frequencies. In particular, the
eight selected cases cannot tell whether post-commit changes or readout
disagreement dominates the complete stochastic cohort.

The preregistered [full frozen-cohort overlap audit](../../manifests/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json)
then [replayed all 256 original stochastic histories and 2,048 original arm rows](../../results/j6b-d4-frozen-cohort-overlap-audit-2026-09-24.json)
exactly, including all 512 JIT target rows. Original hashes, matched keys,
action-bound second records, public/private separation, independent terminal
residuals, all 16 selected D3 JIT checks, and D1 outcome counts reconcile.
Each cell/mode retains 128 unconditional rows, including 59 clean-cell and 57
joint-cell failed-closed rows per mode. The table below shows only the
syndrome-only *scored-failure* subset; heralded flag masks are the same
except for the number of failures with no listed flag. These masks are
overlapping observations, not mutually exclusive explanations:

| Scored-failure flag pattern | Clean herald | Joint readout noise |
| --- | ---: | ---: |
| No physical commit | 13 | 14 |
| Later physical transition, no last-commit readout mismatch | 10 | 12 |
| Last-commit readout mismatch and residual already present, no later transition | 13 | 11 |
| Later physical transition *and* last-commit readout mismatch/residual | 21 | 30 |
| None of these four flags; failure can still be another Boolean-union component | 4 | 1 |

The largest named pattern in each cell has both a later physical transition
and a public/hidden readout mismatch at last commit (21 and 30), so a
single-cause ranking would be false. A later transition occurs in one
scored-success row in each clean-cell mode, showing that the flag alone is
not sufficient for failure. The complete mask and outcome counts, including
both public modes, are in the machine result. This is a finite-cohort
description under the unchanged phenomenological model, not a conditional
risk, causal attribution, or new schedule comparison.

## Status

The registered pilot is analyzed at its fixed bound. D0–D4 close the frozen
cohort accounting: D2 corrects a simple final-round fault under JIT, while
D3/D4 expose multiple, often co-occurring paths. Exact replay found no
scorer or public-binding defect in these 256 stochastic histories, but near-
saturated risk and frequent failed-closed paths do not justify another
micro-audit as a scientific answer. The next transition should reassess the
central fault-tolerance question and preregister a genuinely discriminating
channel/schedule study only if its scope, observable and compute are
justified. No
threshold, crossing, universal JIT benefit, circuit-level D4 claim, or J6/J6B
pooling is permitted.

## Related pages

[[schedule-state|Schedule state]] · [[spatial-policy-boundary|Spatial-policy boundary]]
