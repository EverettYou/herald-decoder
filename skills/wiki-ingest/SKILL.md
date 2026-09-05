---
name: wiki-ingest
description: Integrate immutable references, project resources, code, and completed lab evidence into the Herald Decoder project's persistent Wiki with traceable provenance.
---

# Wiki Ingest

Compile source knowledge once and keep the project Wiki current. A source ingest may revise many existing pages; do not merely create a standalone summary and stop.

## Scope

This project has one project-root Wiki. Its internal sources are project-root-relative paths outside `wiki/`, commonly under `references/`, `labs/`, `src/`, and `skills/`. Cite external sources by their canonical URL; do not mirror or snapshot them locally unless the user explicitly requests archival.

## Inputs and ownership

Require one explicit source at a time unless the user requests a batch. Valid lab evidence is a completed `labs/*/REPORT.md` with selected result/figure paths. Use canonical project resources and fetched reference folders in their existing root-relative locations; never move or copy them merely for ingest. For external sources, retain the canonical URL directly in the page rather than creating a project copy.

Read `wiki/SCHEMA.md`, `wiki/index.md`, `wiki/thesis.md`, `wiki/sources.yml`, and the recent tail of `wiki/log.md` before editing. Read [references/ingest-protocol.md](references/ingest-protocol.md) for provenance and contradiction rules. Use [assets/page-template.md](assets/page-template.md) when creating a compiled page.

Classify the input before reading it deeply:

- For papers and textual sources, read [references/text-ingest.md](references/text-ingest.md).
- For repository/code sources, read [references/code-ingest.md](references/code-ingest.md) and use [assets/implementation-template.md](assets/implementation-template.md) for durable implementation pages.
- For lab reports, combine both modes: ingest the narrative as text and inspect cited scripts/results as code or data evidence.

Treat a paper folder containing a companion repository as one source bundle but two provenance records. Ingest the paper and repository independently, connect the knowledge they actually share, and record mismatches explicitly. Never infer that the repository implements every method or result in the paper merely because it is stored with that paper.

This skill owns routine writes under `wiki/`. Never modify raw sources, labs, or `src/` unless separately requested.

## Two-pass workflow

Keep analysis and wiki mutation separate. This is a two-call analysis → generation protocol, not a request to expose or persist private chain-of-thought.

- **Pass 1 — structured analysis:** read the source and current wiki, then produce a compact ingest brief containing source identity and revision, supported claims, implementation facts, evidence and limitations, contradictions, candidate page operations, proposed links, controlled topics, and expected thesis impact. Do not edit wiki files in this pass.
- **Pass 2 — generation and integration:** use the reviewed ingest brief as the plan, re-check every claim against the source, then perform the page edits, provenance registration, index/thesis updates, and lint. The brief is transient unless the user explicitly asks to preserve it.

1. Resolve the source identity, immutable path, revision/date, relevant locations, and whether it has already been ingested.
2. **Pass 1:** read the source according to its mode and produce the structured ingest brief. For text, identify claims, concepts, methods, evidence, assumptions, limitations, contradictions, and questions. For project resources, extract ownership, interfaces, relationships, and canonical links without copying operational detail. For code, identify architecture, interfaces, algorithms, dependencies, conventions, tests, failure modes, and paper-to-implementation gaps.
3. Search `wiki/index.md` and existing pages while preparing the brief. Prefer revising an established concept page over producing duplicates or one page per source heading.
4. Present the concise ingest brief before writing. When categorization, claim scope, or conflict resolution would materially change the Wiki, ask the user to resolve it. If routine or unattended ingest was explicitly requested and no material choice exists, share the preview and continue.
5. **Pass 2:** integrate the source across every affected concept, method, implementation, comparison, question, and thesis page. Preserve competing claims; never silently overwrite disagreement. Connect reference methods to repository implementations and both to lab evidence. Never copy a reference, repository file, lab report, or source summary into the Wiki. A `wiki/papers/<reference-id>.md` page is allowed only as a compact entity/router linking the canonical reference bundle, compiled topic pages, implementations, and lab uses; it must not duplicate those pages.
6. Add claim-level citations as standard Markdown links to the paper or repository record, such as `[Temkin et al. (2025), §II](/reference?id=temkin2025-charge-informed-qec)`, or the canonical URL for external material. The record owns the embedded PDF or repository viewer; raw paths and revisions belong only in `wiki/sources.yml`. Use path-qualified Obsidian links such as `[[concepts/locality|Locality]]`. Give every concept, method, comparison, model, and implementation page one to three controlled `topics` in frontmatter so the Wiki remains navigable. Mark synthesis, inference, uncertainty, and needs-verification claims distinctly.
   Keep displayed mathematics narrow and semantically legible: put one primary relation in each display, split long derivations into successive displays, and never use manual horizontal-spacing commands such as `\quad`, `\qquad`, `\hspace`, or `\hfill` to place relations side by side. Keep every display-math source line at or below 110 characters; use line breaks at meaningful mathematical boundaries.
7. Re-evaluate `wiki/thesis.md`: strengthen, narrow, challenge, or leave it unchanged with an explicit reason.
8. Update `wiki/index.md` with every created page and changed one-line summary.
9. Register the canonical raw path, stable revision, ingest time, and all changed wiki pages in `wiki/sources.yml` with `scripts/source_registry.py`. Update an existing entry on re-ingest; do not create a source page.
10. Append one parseable entry to `wiki/log.md`; never rewrite older entries.
11. Run `$wiki-lint`. Fix deterministic structural problems and ask the user to resolve substantive contradictions or uncertain merges.

Register provenance after the page edits are known:

```bash
python3 skills/wiki-ingest/scripts/source_registry.py register \
    <project-root> \
  --source-id paper:<paper-id> \
  --title "<paper title>" \
  --kind paper \
  --path references/<reference-id>/paper.pdf \
  --revision sha256:<digest> \
  --updated-page wiki/thesis.md \
  --updated-page wiki/concepts/<concept>.md
```

## Lab handoff

Ingest a lab only after `REPORT.md` records methods, findings, uncertainty, limitations, result provenance, and a wiki-ingest handoff. Treat prospective motivation and design as hypotheses, not findings. Cite selected `results/` or `figures/` directly when a wiki claim depends on them.

## Completion

Report the source ingested, pages created/updated, thesis change, contradictions introduced/resolved, and lint status. Use clear, plain language. Stop rather than inventing missing provenance or experimental conclusions.
