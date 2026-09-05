# Deliverable integrity

Apply this protocol when a request has multiple outputs, a defect can alter
scientific results, an experiment is invalidated, several executable modes are
affected, or the user requests analysis, a report, or a visualization in
addition to implementation.

## 1. Establish the completion contract

Translate the user's requested outcome into durable acceptance items before
declaring any part complete. Preserve the contract in the owning lab plan or
another canonical project artifact. Register that artifact and its next unmet
item in `.auto-research/state.json` through `loop_state.py set-contract` so the
priority survives later ticks and context compaction. Each applicable item
needs a status and an evidence path:

| Item | Completion evidence |
|---|---|
| Implementation | All affected executable paths contain the intended change |
| Branch coverage | Every named/default/optional mode is enumerated |
| End-to-end verification | Each affected mode runs through its public interface and checks the scientifically relevant output |
| Data remediation | Invalidated experiments are regenerated with recorded parameters and provenance |
| Analysis | Registered baselines and branches are compared with uncertainty and limitations |
| Report | Durable narrative distinguishes corrected findings from invalid history |
| Visualization | Requested figures are regenerated from corrected machine-readable data |
| Downstream release | Dependent labs and claims consume only corrected evidence |

Items that the user did not request may be omitted. Items they did request
cannot be silently replaced by a test, plan, status note, or unrelated
diagnostic.

## 2. Build an impact and branch matrix

For a correctness defect, inventory:

- public branches, modes, backends, defaults, experimental options, fallbacks,
  and accelerated implementations;
- result artifacts and individual fields affected by the defect;
- reports, visualizations, Wiki claims, and downstream experiments that consume
  those outputs; and
- unaffected evidence that remains usable for a stated reason.

Shared code reduces duplication but does not prove branch behavior. Exercise
each affected branch through its public entry point. A unit test of a helper is
implementation evidence; an end-to-end branch test is verification evidence;
a replacement benchmark is scientific evidence. Do not merge these levels.

## 3. Enforce causal priority

An unresolved upstream correctness defect outranks new work that depends on
its output. Freeze dependent claims and experiments until corrected evidence
exists. Unrelated work may continue only when it does not consume invalidated
artifacts and does not displace the next required remediation item.

The next transition is the earliest unmet dependency in the contract. The
one-transition-per-tick rule limits mutation and compute within a tick; it does
not authorize stopping the overall request, marking it complete, or choosing a
different frontier on the next tick.

If a replacement experiment needs routine parameters, use prior matched
provenance or conservative bounded defaults and register them. Ask the
researcher only when cost, scope, dependencies, or interpretation would
materially exceed the existing authorization.

## 4. Preserve invalidation explicitly

Keep invalid raw artifacts for provenance when safe, but label affected fields
and conclusions invalid. Do not mix corrected and invalid rows in one active
comparison without unmistakable status labels. Reports and figures must source
corrected data only. A new code timestamp does not rehabilitate old outputs.

## 5. Report state precisely

Use these terms narrowly:

- **patched** — code changed, branch verification may remain;
- **verified** — every affected branch passed its end-to-end acceptance check;
- **rerun** — replacement experimental data exists;
- **analyzed** — the registered comparisons and uncertainty were evaluated;
- **reported** — requested narrative and visual artifacts exist; and
- **complete** — every required acceptance item has durable evidence.

At every handoff record what was completed, the evidence path, what remains,
and the single highest-priority next item. Use the structured
`--acceptance-item` and `--next-item` fields when recording the transition.
Never summarize a partial state with the vocabulary of a later state, and do
not clear the active contract while a required item remains.
