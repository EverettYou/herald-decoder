# Plan — Statistical mechanics of representation-informed decoding

## Motivation and inherited evidence

Lab 006 is the sole parent. Its completed directed/hidden-orientation comparison
shows exact SU(2) orientation invariance, strong practical LER degradation for
U(1)/SU(3) under hidden orientation, and different square/honeycomb size curves.
The user's central question is why SU(2) differs and how representation conjugacy
reaches the hard decoder. The square hidden-U(1) curve merging suggests a
KT/BKT-like hypothesis worth distinguishing, not an established transition.
See the [inherited evidence and scope](wiki/problem.md).

Here “stat model” means a statistical-mechanics model for the decoding posterior.
This is a theory lab, not an extension of Lab 006's Monte Carlo acquisition.

## Question

What exact observation-conditioned partition function governs logical-sector
inference in the Lab 006 model, and what does its reduction reveal about
self-conjugacy, hidden orientation, lattice geometry, and BP-to-MWPM hardening?

## Hypotheses and alternatives

- Self-conjugacy removes a latent orientation in SU(2); residual signed-current
  or conjugate-irrep constraints in U(1)/SU(3) change sector weights. Establish
  what this implies and what it does not imply for threshold-like behavior.
- The apparent group distinction may also depend on full-irrep multiplicities,
  geometry, boundaries, and the approximation from posterior to hard correction.
- The thermodynamic alternatives include a finite threshold, a critical
  interval, or no transition over the studied p range; the current curves do
  not select among them for U(1)/SU(3).
- Square hidden-U(1) may admit a compact-height/current description with
  KT/BKT-like behavior; alternatives are ordinary finite-size drift, a smooth
  crossover, or an algorithmic transition. No universality class is assumed.

## Frozen model and comparisons

Reuse Lab 006's Bernoulli activity, directed or shared hidden pair orientation,
full interior (m,R), and unmeasured rough-boundary records. “Undirected” refers
to the physical pair-orientation law, not a new matching graph. Keep one latent
orientation per edge shared by its two endpoints; never replace the joint
orientation sum with independent endpoint averages. Use the conditionally
independent classical local fusion instrument defined in the parent method.

Compare U(1), SU(2), SU(3), both geometries and both orientation laws. Hold the
physical model and observation fixed when comparing exact logical-sector
inference, exact-marginal MWPM, and BP-marginal MWPM. The existing orientation
contrast changes the R-record law; it is not an information-ordering theorem.

## Ordered deliverable contract

| Item | Deliverable and acceptance | Durable artifact | Dependency |
| --- | --- | --- | --- |
| 1 | Define and normalize the sector-resolved posterior; specify latent states, measured sites, reference correction and relative boundary sectors. | `wiki/partition-function.md`, exact identities and a bounded enumeration check in `results/` | Frozen inherited model |
| 2 | Extend the inherited SU(2) orientation quotient into the sector partition sum; identify an explicit U(1)/SU(3) obstruction or counterexample. | `wiki/conjugacy.md` and exact checks | Item 1 |
| 3 | Derive a loop/current/height/spin representation, or show precisely why a proposed reduction fails. Separate degree-three and degree-four vertices and rough boundaries. | `wiki/statistical-model.md` | Items 1–2; source-assumption audit |
| 4 | Identify how sector inference, edge marginalization, BP approximation, and hard matching differ; give a bound, equivalence condition, or counterexample relevant to the group contrast. | `wiki/decoder-gap.md` and exact small-graph checks | Items 1–3 |
| 5 | State discriminating predictions for conventional, KT/BKT-like, and algorithmic explanations; specify valid observables and any subsequent experiment, without fitting unsupported critical parameters. | `wiki/predictions.md`, concise final `REPORT.md` | Items 1–4 |
| 6 | Integrate theory, reproducible checks, and any genuinely clarifying figure; validate report/Wiki, metadata, and rendered Lab pages. | Delivery audit in `results/`; presentation in `figures/` only if needed | Items 1–5 |

The launch contract is [registered here](manifests/theory-scope-2026-09-09.json).
At launch only scope registration and source orientation were complete. The
2026-09-14 execution below supplies the new derivations and exact checks.
A valid counterexample or no-go result can satisfy an item without forcing an
incorrect mapping. New computation must name its bounded size and comparison
before running; no large Monte Carlo scan is part of this launch.

## Observables and scientific gates

Start with Z_h(m,R), normalized sector probabilities, and sector free-energy
contrasts. Fix a syndrome-compatible reference correction and explain sector
label invariance. Compare Bayes sector risk with the practical correction's
risk on the same record. A partition-function identity alone is not a proof
of a phase transition or of the performance of BP followed by matching.

If a current/height model is justified, derive the relevant defect, stiffness,
correlation-length or winding-sector diagnostic before invoking BKT scaling.
Separate quenched conditioning on (m,R) from annealed record averages, and
state any Nishimori-type matched-model condition rather than assuming a clean
O(N), XY, or Ising model. Never identify SU(N)'s N or dim(F) with an effective
loop fugacity without deriving the weights.

Use exact sums on a tree, a cycle, and a minimal graph with the relevant boundary
sectors to test normalization and proposed transformations. Verify both directed
and hidden models, both lattice-local degrees, and the shared orientation. Record
any numerical tolerance before a check and use exact arithmetic where possible.

## Sources

The already archived [Sala–Verresen paper](../../references/sala2025-decohering-nonabelian-topological-order/paper.pdf)
is the initial source, with a [source and transfer boundary](wiki/source-context.md).
The parent [method](../../wiki/methods/sun-fusion-herald-belief-propagation.md)
defines the actual likelihood to be mapped. The existing charge-informed U(1)
reference is a further comparison target, not automatic equivalence to this model.

## Stop conditions and completion

Stop a proposed reduction if it loses orientation correlations, changes the
record/boundary law, or cannot reproduce exact sector sums; retain the failure
as a no-go result. Stop a universality claim if the appropriate effective theory
or observable has not been derived. Keep microscopic quantum-channel assumptions
separate from the parent's classical instrument.

Complete the lab when the contract has an exact mapping or explicit obstruction,
a justified conjugacy/decoder connection or counterexample, falsifiable follow-on
predictions, and a short report passing both lints and rendered-page acceptance.
The parent's figures and controls are inherited evidence, not Lab 007 results.

## Execution — 2026-09-14

The user resumed this theory direction and invoked auto research. The active
contract is this lab's original six-item scope; Lab 004 compute work is not the
current deliverable. Open Discussion has no unanswered user message relevant
to this work. No scientific decision or additional resource permission is needed.

- Items 1–2: normalized relative-sector posterior, reference invariance and
  matched-model identity; SU(2) joint-law quotient; U(1)/SU(3) path counterexamples.
- Item 3: positive SU(N) vertex model, binary-spin coordinates, U(1) bounded
  integer currents and relative heights, character identity, and restricted
  trivalent singlet loop gas. Typical-record pure-loop and unqualified clean
  spin reductions are rejected. SU(3) same-record divergences can differ by six.
- Item 4: strict exact-marginal hardening counterexamples. The hexagon witnesses
  reproduce the actual matching objective. The star has repeated boundary
  columns and is retained as a mathematical/tree-BP example, with its backend
  mismatch explicitly reported; canonical parent L=5,7,9,11 lack that duplication.
- Item 5: intrinsic sector-risk/entropy/free-energy diagnostics and conventional,
  BKT-like, algorithmic and crossover alternatives; no critical parameters fitted.
- Item 6: integration, three lints, report/Local Wiki/document-link rendering,
  active registry and shared-Wiki delivery passed. The delivery audit records
  each link separately in `results/theory-delivery-2026-09-14.json`.

Bounded exact evaluation was registered before running in
[the check manifest](manifests/exact-model-checks-2026-09-14.json).
[Core evidence](results/exact-model-checks-2026-09-14.json): 90 cases, 45 local
fusion comparisons, 870 sector-spin checks, 488,340 reference checks, 16,764
U(1) current checks; all rational identities pass. The core run took 76.22 s.
[Supplement](results/mapping-supplement-2026-09-14.json): 7,817 integer-current
reconstructions, 15 exact tree-BP checks, six matching-backend witness matches,
and 15 documented star backend obstructions. These are deterministic finite
motifs, not a new Monte Carlo acquisition or a finite-size threshold estimate.

Support code is frozen once these gates pass. A future exact strip contraction
is a proposed follow-on under [predictions](wiki/predictions.md), not a hidden
extension of this formulation contract. The open scientific question is the
controlled typical-record theory and its intrinsic-versus-algorithmic scaling.

All six formulation gates are complete. No follow-on acquisition is running.
