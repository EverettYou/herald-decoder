---
name: wiki-query
description: Answer Herald Decoder research questions from the maintained project Wiki with traceable citations. Use for reference synthesis, hypothesis comparison, contradictions, research directions, and lab context.
---

# Wiki Query

Use compiled knowledge before reaching back into raw sources. This operation is read-only by default.

## Scope

Read the project-root `wiki/`, which is authoritative for project architecture, cross-reference knowledge, and completed lab evidence.

## Workflow

1. Read `wiki/SCHEMA.md`, then `wiki/index.md` and `wiki/thesis.md`.
2. Turn the request into a small set of search concepts, code symbols/aliases, relevant page types, and evidence needs.
3. Use the local Wiki search endpoint when the dashboard is running, or search Markdown with `rg` as the filesystem fallback. Treat retrieval as candidate ranking, not evidence. Read the highest-ranked concept, method, implementation, comparison, project, and question pages and follow their links. Consult `wiki/sources.yml` for ingest coverage and revisions.
4. Synthesize across pages instead of concatenating excerpts. Separate established evidence, current wiki synthesis, unresolved contradiction, and your new inference.
5. Cite Wiki page paths near claims and include primary reference/code/lab citations when the answer drives a scientific decision. When proposing text for a Wiki page, use only portable standard Markdown citations: `[readable label](relative-path#locator)`, never a source ID or dashboard-resolved citation. Distinguish Wiki synthesis, static code inspection, repository-test evidence, and lab evidence.
6. For idea generation, propose multiple candidates before selecting one. Score them qualitatively by scientific value, information gain, tractability, discriminating power, and dependency risk.
7. For a next lab, return motivation, hypothesis/alternatives, required wiki context, minimal discriminating design, observables, failure interpretation, and likely idea-graph update. Do not fabricate findings or create the lab unless requested.

Read [references/query-output.md](references/query-output.md) when the answer will seed an idea or lab.

## Write boundary

Do not edit the Wiki or labs during an ordinary query. If a synthesis is genuinely reusable, offer to preserve it; after approval, prepare it as a candidate source and invoke `$wiki-ingest`. If the user asks to create a lab, update the appropriate artifacts as a separately authorized action. Log a query only when it is saved or repository policy explicitly requires it.

## Answer quality

Say when the wiki lacks coverage. Prefer a source-acquisition or lab proposal over speculation. A good query answer should make the next decision cheaper, not just restate the current thesis.
