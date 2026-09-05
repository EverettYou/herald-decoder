---
name: auto-research
description: Run a bounded, resumable Herald Decoder research loop with durable deliverable contracts, remediation priority, and evidence-backed escalation. Use to start, resume, supervise, or report autonomous project research; do not use to replace a requested one-off analysis.
---

# Auto research

Coordinate the existing reference → Wiki → lab → report loop. Keep one transition per tick, preserve competing hypotheses, and treat plans or chat as non-evidence. The durable control state is `.auto-research/state.json`; use `scripts/loop_state.py` instead of editing it directly.

For a multi-part request, defect remediation, invalidated experiment, or requested report/visualization, read and apply [Deliverable integrity](references/deliverable-integrity.md) before selecting work. The user's complete requested outcome is the work unit; a tick is only a bounded scheduling unit. Point the durable state at the canonical contract with `loop_state.py set-contract ... --next-item ...`; record the satisfied and next acceptance items on every transition. Clear the contract only after all required items have evidence or the researcher explicitly removes them from scope.

## Operations

- `start` / `resume`: initialize or set state `active`; inspect open Discussion threads first.
- `pause`: set `paused`; do not discard an open decision.
- `status`: report state, current lab, newest evidence, and any thread awaiting the researcher.
- `research-tick`: perform at most one bounded state-advancing action.
- `supervisor-tick`: assess whether the frontier progressed; after three quiet supervisor ticks, diagnose the stall and either redirect an independent branch or use `$consult-human`.

## Each tick

1. Read `README.md`, the relevant lab plan/report, shared Wiki frontier, and open Discussion. If the latest message in an open thread is from `user`, acknowledge it and apply that decision before unrelated work.
2. If a deliverable contract is active, select its highest-priority unmet acceptance item before unrelated frontier work. An upstream correctness defect or invalidated evidence places every dependent experiment, synthesis, report claim, and downstream lab behind that remediation until corrected evidence exists. Do not advance a downstream consumer merely because its next step is independently runnable in isolation.
3. When no contract or remediation determines the next action, use the shared Wiki to identify the highest-information unresolved question. Propose several candidate labs or bounded tests, preserve competing hypotheses in the selected `PLAN.md`, and select the next one with a recorded scientific rationale. Route supported completed evidence through the Wiki and promote code to `src/` only after validated cross-lab reuse justifies it.
4. Classify the fork before escalating. A choice of **what to try first** is ordinarily an experiment-design or scheduling question, not a human decision. When several independent, reversible branches are within the approved scope, dependencies, and budget, register and run the smallest discriminating matrix that covers all of them. Run independent branches concurrently when resources permit, otherwise sequentially; their order must not block the loop. If one result determines a dependent follow-up, run the cheapest/highest-information prerequisite first rather than asking the researcher to guess its outcome.
5. Escalate only a genuine judgment: an option irreversibly changes the central question, accepted scope, compute/dependency budget, deliverable, external dependency, or interpretation; or a bounded experiment cannot discriminate among materially different options. State why the experiment matrix is not affordable or not discriminating. Never open a thread merely to choose among short, reversible diagnostics that can all be run. Missing routine parameters do not justify stopping an explicitly requested rerun: register conservative bounded values from existing provenance, or ask only if the resource impact is materially outside the approved scope.
   For any new research direction, model, experiment, simulation, scientific
   evaluation, or interpretation-changing revision, invoke
   `$research-workflow` and resume from the earliest unsupported gate. A chat
   request, visual preference, or plausible mechanism is not by itself a
   registered scientific plan.
6. Create a lab only when the question and comparison are sufficiently scoped; preserve alternatives in `PLAN.md`. Execute or analyze only the registered lab work. Keep design, implementation, and analysis as a scientific loop, not lab states. Write machine-readable measurements and interactive artifacts to `results/`; write prose runner output only to `wiki/records/`. Update the lab's Local Wiki when a result changes a method, evidence family, decision, or boundary; do not create one page per routine test. After every accepted evidence batch, invoke `$organize-lab`'s evidence-integration gate before editing `REPORT.md` or reporting the lab as current: normalize any raw record pages, update the owning topical Wiki pages, and pass both `python3 skills/organize-lab/scripts/lab_wiki_lint.py labs/<id>` and `python3 skills/organize-lab/scripts/lab_report_lint.py labs/<id>`. Before setting `stage` to `complete`, rerun those same gates; a lint failure keeps the lab `active` or `blocked`. New accepted evidence reopens a completed lab as `active` before its report is updated. Promote only validated evidence through the existing Wiki skills. When updating lab state, `labs/<id>/lab.json` is canonical, but keep the matching `labs/labs.json` index entry complete with `stage`, `summary`, `current_focus`, `next_action`, and `updated`; never replace the index with id/title-only records.
7. Before a genuine consequential choice, use `$consult-human` to create an evidence-backed Discussion thread, record its ID with `set-pending-human`, and pause only the dependent branch. A pending Discussion thread is never a project-wide stop condition: continue independent work that does not consume invalidated upstream output. If the thread was opened for a runnable experimental fork, clear the pending ID, record the misclassification, and proceed with the matrix.
8. Update state with the acceptance item completed, its durable evidence, and the next unmet item. A no-op is valid only after recording why the frontier cannot advance safely; waiting for routine registration or ranking among runnable branches is not a valid no-op. Never report the user's objective complete because one tick completed.

When a pending thread has a user reply, apply the decision durably, append an agent resolution, clear the pending ID, and continue. Never invent a user answer, close a Discussion thread, or treat an empty / quiet tick as evidence.

Use precise status language: `patched` means code changed; `verified` means every affected branch passed end-to-end checks; `rerun` means replacement data exists; `analyzed` means the registered comparison was evaluated; `reported` means the requested narrative and presentation artifacts exist. Say `complete` only when every required acceptance item is evidenced.

Use the installed Codex automation capability only when asked to run the loop on a schedule. A scheduled prompt should invoke `supervisor-tick` once, keep the work bounded, and report a thread awaiting the researcher when one is opened.
