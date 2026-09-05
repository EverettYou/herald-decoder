# Herald Decoder Wiki schema

The root Wiki is this project's canonical compiled knowledge layer. It synthesizes reusable scientific knowledge across references, project code, and completed labs while linking back to the material that owns the raw detail.

## Scope

- Pages synthesize concepts, methods, models, implementations, comparisons, questions, and project architecture.
- Reference identity and raw files remain under `references/`; the Wiki cites them rather than copying them.
- A compact `references/<reference-id>.md` entity page may route to canonical paper, repository, dataset, or other reference assets and their compiled topics; it is not a reference summary.
- Completed lab reports and their results remain authoritative under `labs/`; a compact Wiki lab router may link the evidence to durable synthesis.

## Required files and page types

The Wiki contains `index.md`, `thesis.md`, `log.md`, `sources.yml`, and this schema. Compiled pages live in `concepts/`, `methods/`, `models/`, `implementations/`, `comparisons/`, `questions/`, `project/`, `references/`, and `labs/` when warranted by the material.

Use lowercase kebab-case filenames. Every compiled page has YAML frontmatter containing `title`, `page_type`, `status`, `updated`, `source_refs`, and `idea_ids`. Concept, method, comparison, model, and implementation pages also carry one to three controlled `topics`: `Quantum Error Correction`, `Topological Phases`, `Symmetry-Enriched Systems`, and `Decoding Algorithms`. Every compiled page visibly includes `Summary`, `Sources`, and `Last updated`, and ends with `Related pages`.

## Links and provenance

Use path-qualified Obsidian links such as `[[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking]]`. Cite papers and repositories through their dashboard records, for example `[Temkin et al. (2025), §II](/reference?id=temkin2025-charge-informed-qec)`. The record owns the embedded PDF or repository viewer; `wiki/sources.yml` alone records raw paths, revisions, and hashes for provenance.

Scientific claims must distinguish source evidence, Wiki synthesis, inference, contradiction, and uncertainty. Static repository inspection establishes architecture and interfaces only; it does not establish runtime correctness or reproduction of published results.

## Ownership

- `$wiki-ingest` performs routine integration into the project Wiki.
- `$wiki-query` queries the Wiki without mutation by default.
- `$wiki-lint` checks structural integrity and knowledge health.
- The dashboard renders Wiki navigation from links and source references; edges are derived, not maintained separately.
