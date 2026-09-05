# Ingest protocol

## Provenance

Every paper or repository citation must use its readable dashboard record, for example `[Temkin et al. (2025), §II](/reference?id=temkin2025-charge-informed-qec)`. The record owns the PDF or repository view; never expose a raw PDF path in a visible `Sources` field. Keep immutable project-root-relative paths, revisions, and hashes only in `wiki/sources.yml`. Lab claims may link the corresponding lab record. Add a page, section, figure, table, commit, result key, symbol, test, heading, or line locator whenever possible. Mark unsupported claims `(needs verification)`.

## Integration units

Create pages around durable concepts, methods, entities, comparisons, and questions. Record source-level provenance only in `wiki/sources.yml`; do not create source-summary pages or mirror a reference's section structure. A paper entity page may exist as a routing node for its canonical assets, compiled topics, implementations, and lab uses, but it must remain compact and avoid duplicating topic synthesis. The registry entry lists the compiled pages changed by the ingest without duplicating their content.

If a reference folder includes a repository, treat the folder as a bundle and the paper and code snapshot as separate sources with separate revisions and `updated_pages`. Static code inspection supports statements about architecture and interfaces, not runtime correctness or reproduction of paper results. Create a paper-to-code comparison when the implemented objective, level of description, or algorithm differs materially from the paper method a reader might otherwise assume it realizes.

Reusable scientific pages belong in this project Wiki. Keep lab-specific hypotheses, decisions, implementation constraints, and raw evidence in the lab folder rather than maintaining parallel full copies.

## Claims

For consequential claims, preserve:

- the claim and calibrated confidence;
- supporting and challenging raw sources;
- scope and assumptions;
- whether it is source-reported, lab-observed, or wiki synthesis;
- related concepts, methods, comparisons, questions, and ideas.

## Contradictions

Never overwrite an older claim just because a new source disagrees. Record both scoped claims, identify possible reasons for disagreement, update the thesis only to the degree justified, and create an open question when the conflict is unresolved.

## Idempotence

Before ingest, inspect the matching `sources.yml` entry and log. Re-ingesting the same revision should not duplicate pages, links, or log claims. If a source changed, update its revision and affected-page list and explain which compiled conclusions changed.

## Ingest preview

Before mutation, show the human the extracted takeaways, possible contradictions, planned page changes, and proposed thesis effect. Human review is mandatory for ambiguous ontology, conflicting interpretations, or consequential scope changes. A routine ingest may continue after a visible preview when the user already authorized the operation and no material decision remains.
