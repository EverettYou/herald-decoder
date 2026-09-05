---
name: organize-lab
description: Curate a research lab report, its evidence, figures, and provenance. Use to finalize or reorganize a lab report; do not use for running new experiments.
---

# Organize lab

`REPORT.md` is the reader-facing research product, not the experiment log.
Use this skill whenever new validated evidence is to be presented, a report is
revised, or a lab is about to be marked complete.

Read [the report contract](references/report-contract.md) before editing. The
contract is mandatory before a lab may be marked complete.
Read [the Local Wiki contract](references/local-wiki.md) when organizing
research detail or evidence.

## Lifecycle

`lab.json.stage` is the only lab state: `active`, `blocked`, or `complete`.
Scientific work may loop freely through design, implementation, and analysis;
do not represent that loop as a linear progress bar. A lab can be `complete`
only when its current report passes the report lint. If new accepted evidence
makes a completed report stale, reopen the lab as `active` before updating it.

## Evidence organization

- Keep detailed experiment chronology, failed branches, method changes, raw
  audit artifacts, and full manifests under `manifests/`; retain them for
  provenance. Keep machine-readable measurement data and presentation assets
  under `results/`. Curate human-readable meaning and relationships in `wiki/`, the lab's
  Local Wiki. Do not create a Local Wiki page for every test run: create a page
  for each independently navigable method, evidence family, decision, or
  boundary, and cite its underlying results.
- Keep `REPORT.md` short, varied, and selective. It should tell the reader why
  the question matters, what was actually established, and what follows.
- Before completing a report, make a visualization pass over each major fact
  and implication. Replace prose with a figure, compact table, or interactive
  web artifact whenever that communicates the relation more clearly. Do not
  manufacture decorative visuals when prose is genuinely clearer.
- Curate a small evidence map in the report. Link each claim family to its
  current Local Wiki page, which in turn cites its canonical data/result
  artifact. Do not paste a directory listing or expose internal run names as
  the report's narrative.
- Define project-specific terms at first use in Overview. Treat a withdrawn,
  superseded, or withheld Local Wiki page as provenance only: it cannot support
  a current report fact or implication.
- For every major fact or implication, name one current Local Wiki page that
  owns its evidence boundary. Before completion, compare the report's claims
  against those page statuses and remove duplicated or contradictory prose.
- Treat a section heading as a claim boundary: every Evidence subsection must
  cite a current Local Wiki page in that subsection. Implications and
  Limitations must also cite the current page whose evidence they interpret.
  A single generic evidence map does not satisfy this requirement.
- Put every static report figure under `figures/`, link it to machine-readable data in `results/`,
  and give it a substantive caption and interpretation. An artifact is a
  genuinely interactive `results/*.html` page, not a static image relabelled
  as an artifact.
- Keep only `lab.json` at a lab root. A JSON experiment contract belongs in
  `manifests/`; JSON/JSONL/NPZ data belongs in `results/`; a prose audit or
  implementation/remediation record belongs in the Local Wiki, never in JSON.

## Finalization gate

After any batch of new accepted evidence—not only when closing a lab—run the
evidence-integration gate before editing `REPORT.md` or handing the lab back
to the research loop:

1. Move any prose result, audit, remediation, or experiment narrative from
   `results/` to `wiki/records/` with
   `python3 skills/organize-lab/scripts/move_lab_result_records.py labs/<lab-id> --apply`.
   Keep only machine-readable data and interactive artifacts in `results/`.
2. Repair the moved records' Local Wiki links and update the small number of
   topical current pages that own the new evidence boundary. Do not make the
   raw dated record the report's narrative source.
3. Run both lints below. A failure means the integration is incomplete: do not
   append raw run prose to the report, and do not present the lab as current.

For report finalization:

1. Inventory the report, candidate figures, result index, and unresolved
   evidence boundary.
2. Move detail out of the report without losing provenance; add or update the
   curated evidence map.
3. Use the lab-local decimal identifiers from the contract, never ad-hoc
   `R`, `P`, `M`, or letter-suffixed run identifiers as reader-facing labels.
4. Run `python3 skills/organize-lab/scripts/lab_wiki_lint.py labs/<lab-id>` and repair structural
   Local Wiki errors before citing it from the report.
5. Run `python3 skills/organize-lab/scripts/lab_report_lint.py labs/<lab-id>`.
6. If both pass, the report satisfies the presentation prerequisite for
   `stage: complete`; otherwise repair the stated violations and rerun lint.

Do not claim a performance result, or scientific conclusion beyond
the registered evidence. Separate validated facts from interpretation and
current limits.
