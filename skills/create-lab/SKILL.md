---
name: create-lab
description: Scaffold one discriminating experiment in the project research loop.
---

# Create lab

Create a lab only for a well-scoped question. Its `PLAN.md` must state motivation, hypothesis and alternatives, observables, comparison, stop conditions, and completion criteria. Start `REPORT.md` as prospective; do not record expected results as findings. Create `wiki/index.md` as the lab's Local Wiki and add topic pages as independently navigable knowledge emerges; raw result documents remain under `results/`. In `lab.json`, set `stage: "active"` and a `report_contract` with line and evidence-map limits. A lab has no separate progress state.

For multi-branch implementations, remediations, or requests that include analysis/reporting, add a deliverable contract to `PLAN.md` with:

- affected branches, modes, baselines, and downstream consumers;
- separate acceptance items for implementation, end-to-end verification, replacement data, analysis, report text, and requested visualizations;
- the durable artifact expected for each item;
- dependency order and any invalidated predecessor artifacts; and
- the exact evidence required before the lab may be marked complete.

Do not combine “code patched” and “experiment complete” into one completion criterion. A branch is verified only when that branch—not merely a shared helper or default mode—has been exercised end to end. A requested visualization is a first-class deliverable and must be regenerated from valid data rather than inherited from an invalid run.

If a completed lab is reopened because a correctness defect invalidates results, move its stage back to active/remediation, mark affected claims and artifacts invalid, and keep it ahead of dependent labs until the contract is satisfied or the researcher explicitly changes scope.
