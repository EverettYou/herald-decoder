---
name: consult-human
description: Open, continue, and resolve durable research decisions in this project's Discussion surface. Use when scientific direction, scope, resources, or interpretation needs researcher judgment; do not use for routine reversible work or scheduling.
---

# Consult human

Use the project-root `discussion/threads.json` as the sole durable researcher–agent mailbox. Do not create lab-local discussion systems or bury consequential questions in chat. Read `discussion/README.md`, relevant labs, Wiki pages, references, and existing open threads before escalating.

Use `scripts/research_mailbox.py`; it preserves IDs, timestamps, agent/user authorship, and append-only message history. Agent-created threads must use `--author agent`. The Discussion UI renders such messages as **Research agent** and a user UI reply is automatically authored as `user`.

## When to ask

Ask only after gathering the evidence that can safely be gathered without the decision. First apply this decision test:

- If every candidate action is independent, reversible, already within scope and budget, and will eventually be run, there is no decision. Execute the smallest useful experiment matrix; use concurrency when safe and otherwise queue the work. Its order is scheduling, not a reason to ask the researcher.
- If a result is needed to decide a dependent follow-up, run the cheapest discriminating prerequisite first. Do not ask the researcher to choose a hypothesis before the experiment can test it.
- Escalate only when doing one option excludes another, resources can fund only a subset, an option changes the approved scope/budget/dependency/deliverable, or bounded evidence cannot discriminate a consequential scientific interpretation.

Open or reuse one thread for each coherent decision only when any of these is true:

- choosing among scientifically consequential hypotheses, model assumptions, or decoder definitions that available evidence cannot distinguish;
- changing the central research question, accepted scope, compute/dependency budget, or deliverable;
- interpreting conflicting evidence or a stalled frontier where the choice redirects a lab; or
- reaching a planned checkpoint explicitly requiring the researcher's preference.

Continue independent, reversible work while waiting. Do not ask for routine implementation details or priority ordering among runnable tasks, and do not manufacture alternatives when one action is clearly required. Never open a question of the form “Which bounded diagnostic should be tried first?” when all diagnostics can be run within the approved budget.

An explicit user request to repair, verify, rerun, compare, report, or visualize supplies the deliverable direction. Do not turn missing routine seeds, cell counts, filenames, or plotting choices into a blocking decision. Reuse existing matched provenance or register conservative bounded defaults. Escalate only when the resulting resource cost, scientific scope, or interpretation would materially exceed what the user authorized.

Do not work around an unresolved upstream invalidation by asking which downstream task to do. First complete the authorized remediation contract. Independent work may continue only when it neither consumes the invalid evidence nor competes with the remediation's required deliverables.

## Decision brief

An agent's opening question (and any later agent message containing a new decision) must contain these sections in this order:

1. **What this is about** — the artifact and research goal.
2. **What we know** — evidence, constraints, and durable links.
3. **What is unclear or blocked** — the exact judgment and why it matters now.
4. **Options** — materially different choices, with consequence, cost, and reversibility.
5. **Recommendation** — one `**Suggested: …**` choice with a short reason.
6. **Decision requested** — one explicit question that can be answered directly.

Use `blocking` only if no useful independent work remains after executing every runnable branch. Link related labs through `--lab`; use project-wide threads when no single lab owns the decision.

```bash
python3 skills/consult-human/scripts/research_mailbox.py open . \
  --author agent --title "Choose posterior-weight projection" \
  --category scientific --priority high --lab lab-002-herald-belief-matching \
  --message "**What this is about**: ..."
```

When a user reply is present, acknowledge and apply it before selecting unrelated work. Append an agent `resolution` with durable artifact links after implementation, but never impersonate the user or close the thread on their behalf.
