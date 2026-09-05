# Continuous research execution protocol

These instructions apply to every agent working in this repository.

## Do not convert authorization into a pause

When a user has authorized a research direction with language such as
"continue", "start", "go ahead", "one by one", or has given a concrete
next experiment, that authorization remains active across intermediate
planning, registration, profiling, implementation, and status questions.
Creating a manifest, editing a plan, writing a runner, passing a unit test,
or reporting progress is **not** a completion condition.

Continue the authorized work until one of these is true:

1. the requested experimental deliverable and its registered acceptance gates
   are complete and reported;
2. a real blocker requires a new scientific, scope, resource, or safety
   decision from the user; or
3. the user explicitly changes, cancels, or pauses the task.

Do not stop merely because an experiment is long-running. Start it, preserve
its output/checkpoint, and continue with independent verification, analysis,
or the next authorized bounded transition.

## Status questions do not end the active task

For questions such as “做到哪里了？”, “结果是什么？”, or “你在等什么？”:

1. report the exact state honestly, including what has not yet run;
2. identify the next concrete operation; and
3. perform that operation in the same turn when it is already authorized.

Never reply with only a plan, registration, or “in progress” notice when a
safe authorized action remains.

## Research execution discipline

- Separate scientific experiments from engineering support work. Freeze a
  support branch once it is sufficient for the current scientific decision;
  do not let micro-optimization overtake an unresolved scientific question.
- For an A/B request, implement one change only, use matched inputs, define
  acceptance before timing, and either promote or reject the candidate from
  measured evidence. A rejected candidate is progress, not a reason to pause.
- Before claiming a comparison or threshold, verify matched noise channel,
  geometry, observation record, decoder-visible information, score, and
  finite-size interpretation.
- Keep durable state current: PLAN, manifest status, result/report, lab
  metadata, and `.auto-research/state.json` must name the actual active
  deliverable rather than an older completed branch.

## Communication

Use commentary for short progress updates during work. A final answer is only
for a genuine handoff, a real decision request, or a clearly stated continuing
execution checkpoint that immediately has a scheduled follow-on action.

## User-visible delivery gate

Do not report a figure, report, dashboard, or registered result as fixed merely
because its source script, generated file, metadata, or lint changed. Before a
completion claim, verify the exact user-facing target through every applicable
link: current inputs, regenerated artifact, report embed, active registry, and
the rendered page or URL. Confirm scientific semantics as well as file
existence: the intended inference, scope, ranges, units, reader-facing names,
uncertainty, caption, and absence of superseded active versions.

If the user says the visible result is unchanged or broken, that observation
rejects the prior completion claim. Reproduce the issue on the exact named
surface and keep the task open until that surface passes. Record separately
which links were verified; never let one passing proxy stand in for the chain.
