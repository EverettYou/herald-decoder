---
title: J6 tiny matched-history D4 schedule pilot
status: current
updated: 2026-09-19
record: true
---

## Summary

J6 ran a tiny, fixed-size matched-history pilot across four schedules and two
public D4 information modes. All registered rows were retained, but the
clean-herald JIT arm missed the preregistered event-resolution minimum by one
history, so the pilot closed censored before bootstrap or risk interpretation.

## Question

Can the translated D4 stochastic path produce integrity-clean paired outcomes
with enough nontrivial events to justify a larger causal schedule comparison?
This is an exploratory implementation-and-resolution pilot, not a threshold or
fault-tolerance experiment.

## Evidence

The verified J1-E4B translation matrix supplies the causal public interface and
the resolved thread-009 decision supplies the phenomenological/projector-level
D4 model boundary. The machine-readable contract below freezes the experiment
that may consume those prerequisites.

## Frozen design

The registered geometry is paper (L=2), with five public readout rounds. One
independent master-seeded hidden/public history is evaluated under immediate,
fixed-delay-1, Lyons--Brown JIT and explicitly noncausal offline schedules, in
both syndrome-only and heralded modes. Online arms share the same timing,
physical history, action semantics, inner decoder and scoring window; the only
mode difference is access to the categorical herald record.

The three cells are a 16-history zero-noise control, 128 histories at
`p_data=p_syndrome=.05` with perfect herald readout, and 128 matched histories
with `.05` false-positive, false-negative and blue/green-confusion rates. This
gives exactly 272 independent histories and 2,176 arm evaluations. No adaptive
extension is allowed.

The primary loss is unconditional ground-state-relative Boolean-union logical
failure. Abort, timeout, malformed completion and missing score remain in the
denominator as failures. Whole histories, not arm rows, are the resampling
unit. Arm risks receive pointwise Wilson intervals; registered paired
differences receive 2,000 fixed-seed whole-history bootstrap replicates.

## Gates and claim boundary

Before production sampling, a deterministic preflight must pass frozen-source,
normalization, zero-control, matched-key, causal-prefix, action-binding,
relation-free public action, unconditional-denominator and replay gates. A
source mismatch or failed gate censors the branch. A promotion trigger requires
an absolute preregistered online paired risk difference of at least .05 with a
pointwise paired interval excluding zero; this is only a reason to propose a
larger confirmatory study, not a superiority claim.

The [machine-readable contract](../../manifests/j6-d4-matched-history-stochastic-pilot-2026-09-19.json)
freezes the cells, seeds, observables, uncertainty, compute caps, stop rules and
planned outputs. This registration generated zero histories, ran zero schedule
arms and performed zero bootstrap replicates.

## Preflight outcome

Frozen provenance matches, five deterministic component groups pass (22
selected pytest fixture cases), and all six capability gates pass.
The integrated implementation composes hidden five-round D4 transitions and
their causal public first records, generates the second full-binary record
under the realized flux action, sends only that public record to the
relation-free R6AF charge decoder, and derives physical winding, Boolean-union
winding, charge winding and terminal residual privately. The scorer accepts no
external logical label. A deterministic matrix produces exactly all eight
schedule/mode terminal rows on a single-cluster fixture, rejects wrong action
binding and replays bit-identically. Missing and malformed completions are
retained as unconditional-denominator logical failures.

The arm-level remediation treats every public spatial output as an absolute
cumulative Pauli-frame estimate at its decision round. Same-round duplicate
cluster callbacks must have identical full-snapshot action content and collapse
to one commit; later-round estimates supersede earlier frames. Physical,
Boolean-union and charge winding are accumulated over canonical commits, and
terminal residual is evaluated against the final hidden physical state. A
zero-event arm is scored privately without fabricating a public action;
distinct same-round actions fail closed.

The zero fixture now emits eight successes with zero invocations. On the
transition-edge `(0,1)` witness, the two syndrome-only immediate callbacks
still carry syndrome `(1,17)` and correction `(0,1)`, but they collapse to one
canonical commit and one unconditional arm row. Zero-, single- and
multi-cluster matrices replay identically with exactly eight rows each.

The additional noisy-syndrome fixture covers the valid measurement-noise case
where a periodic static decoder rejects an odd instantaneous syndrome. That
decoder abort now yields eight explicit failed-closed, denominator-included
logical-failure rows rather than aborting the history or silently dropping it.

The [machine-readable preflight](../../results/j6-d4-matched-history-pilot-preflight-2026-09-19.json)
reports `passed` and `production_armed=true`. The production-readiness audit
used two deterministic synthetic histories and 16 arm evaluations; it
generated zero production histories, zero production arm evaluations and zero
bootstrap replicates. This is interface evidence only.

## Production outcome

The one-shot production path retained exactly 272 independent histories and
2,176 schedule/mode rows. The zero-noise control had no public events or
logical failures. Both stochastic cells had nonempty detector events in all
128 histories. For each public mode, clean-herald immediate and fixed-delay-1
invoked on eight histories, while JIT invoked on seven; the registered minimum
was eight for every online arm. In the joint-readout-noise cell the corresponding
counts were 10, 10 and 9, so that cell passed.

The clean-herald miss triggers the fixed stop rule. The
[machine-readable integrity result](../../results/j6-d4-matched-history-pilot-analysis-2026-09-19.json)
is `censored`; the [2,176 raw unconditional rows](../../results/j6-d4-matched-history-pilot-rows-2026-09-19.jsonl)
have SHA-256 `9e120e1402f2cd5332ecbea1d15ded2979e8d0fe2165083eeb21794cbed22225`.
Exactly zero bootstrap replicates ran. No schedule-risk direction, herald-mode
effect, equivalence, threshold, scaling or fault-tolerance conclusion may be
drawn from this pilot, and J6 may not adapt its rates or sample count.

The retained denominator also localizes the dominant interface-coverage gap:
960/1,024 clean-herald rows and 944/1,024 joint-readout rows failed closed with
`periodic D4 flux syndrome must have even cardinality`. Measurement noise can
legitimately create odd instantaneous public syndromes, but the current static
periodic inner decoder accepts only an even spatial snapshot. This diagnostic
does not compare schedule risks. It makes a causal odd-snapshot/time-boundary
handoff the prerequisite for any separately registered replacement pilot.

## Status

J6 is closed censored and non-informative. No bootstrap or adaptive extension
is allowed within this contract. A replacement pilot would require a separate
registration and compute budget and may not reuse J6 as performance evidence.

## Related pages

- [[schedule-state|Schedule state]]
- [[spatial-policy-boundary|Spatial-policy boundary]]
- [[records/j1-e4b-translation-interface-matrix-2026-09-19|Verified J1 E4B interface matrix]]
