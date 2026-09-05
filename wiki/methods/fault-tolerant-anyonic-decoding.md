---
title: Fault-Tolerant Anyonic Decoding
page_type: method
status: established-background
updated: 2026-08-28
source_refs:
  - references/jing2025-intrinsic-heralding/paper.pdf
  - references/lyons2026-anyonic-fault-tolerance/paper.pdf
  - references/jing2026-ilp-topological-decoder/paper.pdf
idea_ids: []
topics: [Quantum Error Correction, Topological Phases, Decoding Algorithms]
---

# Fault-Tolerant Anyonic Decoding

**Summary**: In a non-Abelian anyonic computer, decoding must process a time-resolved syndrome record, account for faulty measurements, and avoid corrections that disrupt computation. Intrinsic fusion outcomes and delayed commitments are two distinct ways of managing that information.

**Sources**: [Intrinsic Heralding and Optimal Decoders for Non-Abelian Topological Order](/reference?id=jing2025-intrinsic-heralding); [Quantum Computing with Anyons Is Fault Tolerant](/reference?id=lyons2026-anyonic-fault-tolerance); [Integer Linear Programming Decoder for Abelian and Non-Abelian Topological Codes](/reference?id=jing2026-ilp-topological-decoder)

**Last updated**: 2026-08-28

## Intrinsic heralding with perfect measurements

Jing *et al.* formulate a \(D_4\) decoder where measured intermediate fusion products condition the inference problem. For non-Abelian charge noise and perfect syndrome measurement, they report an optimal conditioned threshold \(p_c=0.218(1)\), while their intrinsically heralded MWPM decoder obtains \(p_c=0.20842(2)\); standard MWPM using only non-Abelian endpoint charges obtains \(p_c=0.15860(1)\). [Jing *et al.* (2025), abstract and pp. 1–5](/reference?id=jing2025-intrinsic-heralding)

These are results for a fixed-point (D_4) model and its stated noise channel. They demonstrate that a non-Abelian fusion record can raise a decoding threshold within that model; they do not provide a threshold for the project's (SU(2))-motivated herald observation.

### Decoder hierarchy in the D4 result

The practical intrinsically heralded decoder in Jing *et al.* (2025) is not a linear/integer-programming decoder. The unheralded baseline uses unit-weight PyMatching MWPM, while the heralded version assigns a large negative contribution to edges adjacent to measured intermediate Abelian charges and then calls PyMatching. The reported conditioned optimum is instead a posterior sum over error configurations in each logical sector, evaluated through a statistical-mechanics mapping and Monte Carlo. [Jing *et al.* (2025), pp. 3–5 and Appendices A–C](/reference?id=jing2025-intrinsic-heralding)

The paper's more general fusion setting produces a Steiner minimum-tree problem. Such a problem can motivate an integer-programming oracle, but this is an extension rather than the algorithm used for the paper's D4 `[2]` benchmark. Lab 004 preserves this distinction while reproducing the published MWPM rule and adding independently labelled optimization and Bayesian oracles.

## ILP with noisy syndrome measurements

Jing *et al.* (2026) introduce the corresponding ILP/BLP formulation. In a finite (2+1)-dimensional spacetime window, the variables represent physical anyon-creation events, syndrome-measurement errors, and one allowed fusion channel per spacetime site. Spatial and temporal anyon-string multiplicities are constrained by the selected channel. For non-Abelian order, the defect record alone does not in general determine the configuration: the measured syndrome at the site is also needed to identify its permitted fusion channels. [Jing *et al.* (2026), §VII.A–B](/reference?id=jing2026-ilp-topological-decoder)

This applies directly to the structural goal of noisy (D_4) herald decoding. It retains intermediate fusion/syndrome outcomes while distinguishing physical spatial strings from temporal strings caused by measurement errors. The paper assumes uncorrelated physical and measurement errors for this formulation and treats its linear objective as an approximation to the posterior configuration probability; those are modeling choices that a project implementation must expose rather than inherit silently.

## Just-in-time ILP protocol

At every measurement round, the proposed decoder adds new defects to an unresolved set, solves spacetime ILP using the syndrome history, and partitions the solution into clusters. For a cluster with smallest containing spacetime-cube size (Q), it defers correction if any contained defect or inferred correction string is younger than (Q); otherwise it performs the cluster correction and removes its defects from the unresolved set. [Jing *et al.* (2026), §VII.C and Algorithm 1](/reference?id=jing2026-ilp-topological-decoder)

The central reason for this just-in-time schedule is non-Abelian charge accumulation: delayed correction can allow anyons to fuse into non-Abelian charges that hide additional content, whereas premature correction can misinterpret a recent faulty measurement. The authors describe the construction as proof of principle and explicitly leave numerical study and a threshold proof for the just-in-time ILP decoder to future work. It is therefore the right methodological target for a measurement-noise extension, but not yet evidence for its threshold or runtime.

## Faulty measurements make decoding spacetime-resolved

Lyons and Brown explicitly include noisy circuit elements and repeated stabilizer measurements in a (2+1)-dimensional spacetime syndrome. A physical error produces a spatial string, while a false measurement produces a time-directed string in the detector record. [Lyons and Brown (2026), pp. 1–3](/reference?id=lyons2026-anyonic-fault-tolerance)

Their just-in-time decoder receives detector events at each timestep and either commits to a correction or defers it. Deferral prevents an early, false reading from triggering a damaging fusion/correction; their stated commit criterion waits until a cluster has persisted for a time set by its maximum initial spacetime separation. Their scheme combines this real-time decision rule with gauging and ungauging for a (D(S_3)) quantum double that supports universal anyonic computation. [Lyons and Brown (2026), pp. 1–4](/reference?id=lyons2026-anyonic-fault-tolerance)

The schedule and the spatial decoder are distinct. The schedule has causal access only to the detector history up to the present, tracks cluster age and absorber/boundary state, and decides `commit` or `defer`. A deferred event is propagated into the next round by updating the latest measurement record. A committed cluster is ungauged so hidden fusion content can be tested; neutral clusters are corrected and re-gauged, while non-neutral clusters are deferred because they may belong to a larger unseen cluster. [Lyons and Brown (2026), Methods, pp. 12–15](/reference?id=lyons2026-anyonic-fault-tolerance)

Their result is a threshold theorem under sufficiently weak local circuit noise, not a published numerical threshold for the project's herald channel. Applying the idea to D4 therefore requires a new spacetime observation model and explicit noise on both syndrome and herald/fusion readout. Lab 005 owns this schedule problem; Lab 004 supplies candidate inner spatial decoders only after the cross-model interface is derived.

A primary-source audit narrows that gap. Jing *et al.* (2025), Supplemental
Appendix D, already write a time-ordered repeated-projector expression and a
false-negative non-Abelian-flux example with time-like measurement-error
weight. [Jing *et al.* (2025)](/reference?id=jing2025-intrinsic-heralding)
Jing *et al.* (2026), Appendix B and Section VII, give the complete local D(G)
anyon projectors and species-resolved spacetime readout-error variables.
[Jing *et al.* (2026)](/reference?id=jing2026-ilp-topological-decoder) These
ingredients support a phenomenological projector-level D4 instrument, but not
an ancilla-resolved extraction circuit. Conversely, the Lyons–Brown D(S3)
citation chain supplies preparation/gauging circuits and commuting projectors
but not a primitive extraction-fault catalogue. [Lyons and Brown
(2026)](/reference?id=lyons2026-anyonic-fault-tolerance) Lab 005 therefore
advances the D4 projector branch while keeping exact D(S3) circuit-level
reproduction locally paused.

Project evidence now verifies that narrow phenomenological layer. The hidden
projector update, subsequent classical false-negative/false-positive report,
and localized five-star quasi-stabilizer example pass separate deterministic
fixtures, including the perfect limit through both public D4 modes. A
simultaneous multi-label report is preserved but cannot yet enter the current
binary spatial-policy request; this is a translation-layer gap, not evidence
against the projector instrument. No schedule or logical-error performance is
inferred from these checks.

The dependent translation check now closes that interface gap. In heralded
mode the existing request can represent both reported membership bits at one
site; in syndrome-only mode the charge bit is deliberately projected away
without erasing its provenance from the enclosing causal digest. The earlier
multi-label rejection was therefore an adapter limitation rather than a need
for a new public schema. Deterministic schedule integration remains the next
gate before any noisy performance study.

A subsequent integration audit found a stricter causal-interface issue in the
project harness: causal callback requests included a digest of the complete
visible history, so future-only changes altered request and response digests
despite an unchanged causal prefix. This partially invalidates the earlier J2
callback-isolation claim but not branch timing, outer shared-history identity,
offline labeling, or truth exclusion. The full-history digest must remain in
outer provenance and be absent from causal decoder inputs before typed E1
schedule integration can be considered verified.

At the R1 checkpoint that callback boundary was repaired and counterfactually verified. The
complete-history digest remains in enclosing provenance but is absent from the
inner request and request digest. A future-only public change preserves all
earlier immediate, fixed-delay, and JIT request/response digests, while the
final offline result changes and remains explicitly noncausal. This closed R1
only; round-local E1 construction and the full mode/schedule matrix remained
separate gates at that checkpoint.

The next gate, I1, is also verified for the bounded paper-\(L=2\) interface.
Each schedule invocation now yields a typed public E1 record from only the last
row of its bound causal prefix, with syndrome and herald membership mapped
independently to flux and charge labels. Truth-only and future-only changes
cannot alter an earlier record. This is an observation-interface result; the
at that checkpoint the two decoder modes had not yet been exercised across the
four schedules.

The full deterministic I2/I3 interface matrix now also passes. Both public
D4 stage-1 modes execute under immediate, fixed-delay, JIT, and explicitly
noncausal offline schedules on the same trace, with syndrome-faithful flux
actions and preserved information budgets. Future-only and private-truth
counterfactuals, simultaneous labels, odd-parity rejection, offline labeling,
and replay are verified. No logical or schedule-performance conclusion follows
from this bounded interface check.

The corrected chain is now consolidated in a final Lab 005 report that keeps
the original future-sensitive callback claim explicitly invalid. The supported
project statement is limited to deterministic causal information flow and
stage-1 syndrome fidelity at paper \(L=2\); downstream release still requires
an audit for stale consumers, and no performance sampling follows from this
result.

The downstream audit found no executable consumer outside Lab 005 and updated
four stale machine-readable pointers. The corrected paper-\(L=2\) stage-1
interface is therefore released for downstream interface work, while the old
preflight remains historical-only. This release does not authorize post-action
recovery or performance sampling.

The next bounded Lab 005 gate is E2 causal post-flux completion. It is
registered as a deterministic interface matrix: first bind a physical
charge/vacuum report and measurement layout to the exact flux action, then run
the resulting second-stage charge action and next-round transition across both
public modes and all four schedule branches. This is a prerequisite for noisy
history or schedule-performance work, not evidence for either.

The common E2A prerequisite now passes at paper \(L=2\). A public adapter binds
charge/vacuum membership and an explicitly supplied physical layout to the
exact flux-action digest, reproduces the perfect E0 post-flux observation, and
rejects wrong binding, non-charge labels, layout mismatch, and temporal
inversion. At the E2A gate this did not yet verify the schedule matrix or noisy
performance; the dependent matrix is reported below.

The dependent E2B/E2C matrix now also passes at paper \(L=2\): both public modes
complete all four schedule branches, with a nonempty charge action in every
cell and with causal next-prefix advancement occurring only after completion.
The matched design holds pre-action history, measurement layout, and report
rule fixed; because the two modes choose different physical flux actions, each
post-action report is necessarily conditioned on and bound to its own action.
Future-only and private-truth counterfactuals, deterministic replay, and
parity-inconsistent-support rejection pass. This is an implemented interface
result, not evidence of noisy-measurement performance, a threshold, or a
schedule ranking.

The final E2 synthesis records this as deterministic causal-composition
evidence only. Fixture-specific action sizes are not comparative observables,
and the synthesis makes no claim about logical-error rate, threshold, hardware
readout fidelity, runtime scaling, or fault tolerance. A downstream release
audit remains required before later Lab 005 work may consume E2.

That downstream audit now passes: no executable consumer outside Lab 005 uses
the E2 interface, no artifact promotes it as performance evidence, and active
surfaces point to the bounded final synthesis. Deterministic E2 composition is
therefore released for downstream interface work only. Any stochastic history,
logical scoring, or schedule comparison still requires a new registered
research-workflow transition.

The next Lab 005 gate is consequently a transition-kernel completeness audit,
not a noisy schedule benchmark. It asks whether current source-backed and
project-defined pieces specify every factor of
\(P(X_{t+1},O_{t+1}\mid X_t,F_t,A_t)\), including action-conditioned post-flux
measurement and private logical scoring. In particular, the static D4 fusion
sampler may not be independently resampled each round unless the audit supplies
a state-update argument. Exact limiting-case checks are registered; stochastic
sampling remains blocked.

The registered K1-K4 audit now finds that this kernel is incomplete. Local
classical report rows normalize and the single-cycle private homology scorer is
available, but no current component defines cross-round hidden D4 state
evolution or generates the physical post-flux record after an action. Thus the
project cannot promote independent per-round fusion resampling as a noisy D4
model. This is a localized physical-model gap, not a decoder-performance
failure.

The formal synthesis sharpens the dependency: K1 hidden-state evolution must be
chosen before K3 physical post-action reporting can be generated. The existing
normalized report channels and single-cycle scorer cannot repair that missing
transition. The audited evidence also cannot discriminate among a
phenomenological finite-state Markov closure, a stateful projector/density
closure, and an ancilla/circuit-derived channel. Selecting among these changes
the physical interpretation and resource scope of the project, so it is a
researcher decision. Until resolved, independent per-round resampling and all
schedule-performance sampling remain prohibited.

Discussion thread-009 is the active decision surface for this model choice. It
does not ask which cheap diagnostic to run first: the bounded checks are already
non-discriminating. It asks which physical semantics future noisy spacetime
histories should claim. Until the researcher answers, only the dependent D4
generator and schedule-performance branch is paused.

## Implication for a future herald decoder

The present project operates on a single-round snapshot \((S,H)\). A measurement-fault extension would instead require a declared temporal observation model, for example a record \(\{(S_t,H_t)\}\), explicit readout-error channels for both fields, and a spacetime matching/factor-graph or cluster decoder. This is a Wiki synthesis from the cited methods, not an implemented project result.

The existing project semantics remain important: a fusion-remnant herald is not a loss flag. A future time-like record may carry evidence both from physical faults and from readout faults, so treating every absent or changed herald as a known error location would be unjustified.

## Related pages

- [[concepts/non-abelian-topological-order|Non-Abelian topological order]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[methods/integer-linear-programming-decoding|Integer linear programming decoding]]
- [Lab 004 — D4 intrinsic-heralded decoder reproduction](/lab?id=lab-004-d4-intrinsic-heralded-decoding)
- [Lab 005 — Spacetime just-in-time anyonic decoding](/lab?id=lab-005-spacetime-jit-anyonic-decoding)
