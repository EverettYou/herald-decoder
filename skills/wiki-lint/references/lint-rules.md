# Wiki lint rules

## Structural errors

- missing `SCHEMA.md`, `index.md`, `thesis.md`, `log.md`, or `sources.yml`;
- broken or ambiguous local Markdown/Obsidian wikilink;
- compiled page lacking required frontmatter or a unique title;
- compiled page lacking visible Summary, Sources, Last updated, or Related pages fields;
- malformed, duplicate, unresolved, or unsafe `sources.yml` provenance entries;
- internal source reference that does not resolve inside the selected scope; external canonical `http`/`https` URLs are valid and must not require a local mirror;
- source citation whose standard Markdown target is broken or unsafe;
- resolver-style source IDs such as `` `global:paper-id` ``, `` `benchmark:task` ``, or
  `source:record-id` in a compiled page; citations must remain readable and resolvable as
  standard Markdown without a dashboard-specific source-ID resolver;
- malformed chronological log heading.
- display math using manual horizontal-spacing commands such as `\quad`, `\qquad`,
  `\hspace`, `\hfill`, `\enspace`, `\kern`, or `\mkern`; split the display instead;
- a source line inside a display-math block longer than 110 characters; break the expression
  across semantic lines rather than placing multiple relations side by side.

## Structural warnings

- page unreachable from the root index through collection or topic links;
- orphan page with no inbound wiki link;
- empty source references, missing inline citations, or stale update date;
- a completed lab report not referenced by the Wiki;
- a reference or repository raw-source folder not referenced by any Wiki page;
- raw material missing from `sources.yml`, or a registry entry whose affected pages no longer exist.
- display math that violates the narrow-layout convention above. This warning is mechanical:
  repair it during ingest or routine Wiki maintenance unless a documented rendering exception is needed.

## Semantic review

- claims without scope, evidence, or calibrated uncertainty;
- new evidence that contradicts another page without an explicit tension;
- thesis claims no longer matching underlying pages;
- duplicate pages that silently use different terminology;
- important recurring concepts without pages;
- registered sources not integrated into durable synthesis pages;
- questions that remain open despite available evidence;
- gaps worth filling with another source or lab.

The optional LLM pass is conservative and evidence-bounded. It may emit only
`unsupported_claim`, `possible_contradiction`, `stale_thesis`,
`duplicate_terminology`, `missing_recurring_concept`, `source_not_integrated`, or
`scope_boundary`. Findings below 0.75 confidence are discarded. A contradiction requires
incompatible supplied passages under compatible scope; a recorded tension is healthy wiki
state, not a lint problem. Semantic output is advisory and must not automatically rewrite
scientific claims, confidence, or thesis state.

Scientific disagreement is not a lint error. Unrecorded disagreement is.
