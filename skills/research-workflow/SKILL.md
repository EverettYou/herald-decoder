---
name: research-workflow
description: Guide an evidence-first scientific investigation from question framing through literature review, modeling, registration, computation or experiment, analysis, reporting, and knowledge synthesis. Use for new research directions, experiments, models, simulations, scientific evaluations, or interpretation-changing revisions; do not invoke the full workflow for routine implementation under an approved plan or purely cosmetic edits.
---

# Research workflow

Use this skill to produce defensible knowledge, not merely an artifact. The
default sequence is:

**orient → research → model → register → compute/experiment → analyze → report → synthesize**

Do not begin at the step mentioned most recently in chat. Reconstruct where the
request sits in the scientific chain, then resume from the earliest stage whose
assumptions are not yet supported.

## Choose proportional rigor

- **Routine execution:** The question, model, and registered method already
  exist and the request does not change interpretation. Verify the contract,
  execute, analyze the output, and report concisely.
- **Exploratory study:** Use a compact written plan covering the question,
  candidate explanation/model, evidence, bounded computation, analysis, and
  stop rule. Clearly label conclusions preliminary.
- **Claim-bearing study:** For a threshold, mechanism, comparison, scaling law,
  optimality statement, new scientific model, or collaborator/publication
  result, require the full gates below, calibrated uncertainty, sensitivity or
  model comparison, and durable reporting.

Rigor scales with claim strength, irreversibility, and resource cost—not with
how many files or plots the user requested.

## Gate 1 — orient to the research program

Read the authoritative project thesis, current knowledge base, roadmap, and
relevant prior labs before selecting work. Identify:

- the central scientific question being advanced;
- this task's epistemic role: theory, physical model, measurement/observation,
  method, intrinsic limit, algorithm, experiment, evaluation, or synthesis;
- which upstream assumptions and downstream claims it depends on;
- whether it is a pilot, validation, falsification, or claim-bearing study; and
- why it is higher-information than polishing a downstream artifact.

For Herald Decoder, read
[references/herald-decoder-program-gates.md](references/herald-decoder-program-gates.md)
and the live Wiki pages it names. The Wiki is authoritative when it changes;
the skill reference is only a routing aid.

## Gate 2 — formulate the question and possible outcomes

State the question before choosing a method. Define the intended knowledge gain,
the smallest supportable claim, competing hypotheses or explanations, and what
outcome would falsify, weaken, censor, or leave each unresolved. Separate:

- facts supported by external sources;
- findings supported by this project's evidence;
- modeling assumptions;
- researcher-supplied physical intuition or design constraints; and
- open hypotheses.

User feedback is not automatically empirical evidence. Classify it first. A
correction may reveal a defect, a violated physical constraint, a changed goal,
or a presentation preference; each routes to a different earlier stage.

## Gate 3 — research the existing knowledge

Query the local Wiki and reference archive first, then perform a targeted
scholarly search before inventing a scientific method or model. Prefer primary
papers and authoritative technical sources. Investigate:

- how the same or analogous question has been formulated;
- established theoretical constraints and physical mechanisms;
- candidate methods, assumptions, and known failure modes;
- appropriate baselines, observables, and uncertainty procedures; and
- what remains genuinely unknown.

Record search scope, sources, and what each source changes in the plan. Do not
cite a method name in place of understanding its assumptions. If browsing is
unavailable, disclose that limitation and do not describe an improvised approach
as literature-grounded. Read [references/source-basis.md](references/source-basis.md)
for the general methodological basis of this workflow.

## Gate 4 — build the scientific and mathematical model

Translate the question into a model only after the research stage. Depending on
the task, define:

- physical system, accessible observations, hidden variables, information
  budget, interventions, and boundary/initial conditions;
- mathematical objects, symmetries, invariants, limiting regimes, and expected
  qualitative behavior;
- data-generating or measurement process, observation units, dependence,
  noise, censoring, and selection;
- inferential target or performance estimand, candidate models, and simplest
  credible baseline; and
- identifiable versus assumed quantities and the design's resolution limits.

The model must explain how observations bear on the scientific question. A loss
function, simulator, neural network, or smooth curve is not a model merely
because it produces a plausible output. Preserve alternatives when available
evidence cannot select among them.

For statistical estimation or fitted scientific graphics, also read
[references/statistical-inference.md](references/statistical-inference.md).

## Gate 5 — register the study before production work

Create a durable plan using
[references/research-plan-template.md](references/research-plan-template.md),
scaled to the rigor tier. Register:

- hypotheses/questions and claim boundary;
- models, methods, baselines, observables, and analysis procedure;
- verification, validation, uncertainty, and sensitivity checks;
- inputs, provenance, parameter grid, independent sampling unit, and compute
  budget;
- stopping, failure, and escalation rules; and
- machine-readable results plus the intended analysis/report outputs.

Registration precedes production computation. Separate exploratory development
from confirmatory evaluation and record post-data changes explicitly. Use
`$consult-human` only when a consequential scope, resource, model, or
interpretation choice remains after the available evidence and affordable
discriminating checks are exhausted.

## Gate 6 — compute or experiment with provenance

Verify implementations on analytically tractable, synthetic, limiting, or
small exact cases before expensive runs. Start with the smallest experiment
that can falsify the mechanism or discriminate models. Freeze source,
configuration, environment, seeds, and raw-output paths. Preserve independent
sampling structure and record failures, convergence, censoring, and aborted
runs—not only successful outputs.

Do not silently expand a pilot into a broad sweep. Do not continue collecting
data when the scientific model, observation channel, or analysis is invalid.

## Gate 7 — analyze, do not merely compute

Computation ending successfully is not a scientific result. Analyze the data
against the registered questions:

- check data integrity and whether the realized experiment matches the plan;
- evaluate diagnostics, uncertainty, sensitivity, and competing models;
- distinguish sampling noise, numerical error, model misspecification,
  algorithmic failure, and genuine scientific signal;
- compare with baselines and negative/null outcomes;
- identify what the data do not resolve; and
- decide whether evidence supports, weakens, or leaves each hypothesis open.

The analysis output may be a concise response to the researcher, a structured
result, a report, a table, or a figure. Use figures only when they materially
clarify the result. Never let a requested presentation substitute for analysis.

## Gate 8 — report and synthesize at the right strength

Connect every claim to a machine-readable result, raw provenance, or cited
source. Report assumptions, limitations, failed branches, uncertainty, and
unresolved alternatives. Distinguish finite-size or phenomenological evidence
from asymptotic, intrinsic, causal, optimal, or physically realizable claims.

Keep exploratory code/results in the owning lab. Promote reusable validated
components to `src/`; promote only cited background or completed evidence-backed
synthesis to the Wiki. Update the roadmap when a result changes which question
has highest information value.

### Presentation validity gate

Before presenting a comparison, estimate, or visual summary, state the
reader-facing inference it is meant to support. Check that the selected data,
domain, resolution, units, transformations, baselines, and uncertainty make
the relevant distinctions visible and do not imply coverage or equivalence
that the study did not establish.

Do not force heterogeneous cases into one view merely because they were
computed or collected together. Use separate views or narrow the stated claim
when a shared representation obscures the relevant evidence. Use descriptive
reader-facing names; keep implementation shorthand and internal identifiers in
provenance. If the available evidence does not cover the conditions needed for
the intended inference, collect the missing evidence or explicitly limit the
presentation rather than filling the gap by visual convention.

### User-visible deliverable closure gate

An upstream edit is not evidence that a reader-facing deliverable changed.
Before saying that a report, figure, dashboard, or other presented result is
fixed, current, replaced, or complete, identify the exact surface the user will
inspect and verify the whole delivery chain:

1. the intended data and renderer inputs are the selected current versions;
2. the required artifact was regenerated in the required format and inspected
   for its scientific content, labels, axes, and legibility;
3. the owning report embeds that exact artifact path;
4. the lab or result registry exposes the same artifact exactly once and no
   superseded version remains in the active reader-facing listing; and
5. when an application page or URL is the acceptance surface, load that exact
   surface and verify the rendered artifact there.

Static lint, a passing renderer, a changed script, a new PNG, or a registry
edit is only evidence for its own link in this chain. None is a substitute for
the downstream checks. Use a deterministic verifier when the repository
provides one, then perform visual or application-level inspection for semantics
that the verifier cannot establish.

Treat “the page is unchanged”, “the figure is broken”, or an equivalent user
observation as a failed acceptance test. Reopen the task at the named surface,
reproduce it there, and do not repeat a completion claim until that surface has
been checked. Keep internal run IDs and shorthand out of reader-facing text
unless the report explicitly defines and requires them.

## Mandatory stop and backtrack conditions

Return to the earliest affected gate when:

- the task is not connected to the program's central question;
- an observation or intervention lacks a physical/operational definition;
- the target is not identifiable from available data or design;
- a comparison changes information, noise, resources, or evaluation conditions;
- validation rejects the model or implementation;
- uncertainty is dominated by an unmodeled source;
- conclusions depend materially on an unregistered post-data choice; or
- a pilot artifact is being promoted beyond its declared epistemic role.

An unresolved or negative result is valid knowledge. A polished artifact that
skips an invalid upstream gate is not.
