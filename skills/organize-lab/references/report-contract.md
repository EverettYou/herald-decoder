# Lab report contract

This contract governs the reader-facing `REPORT.md`. Detailed notebooks,
manifests, raw data, and implementation audits remain durable provenance, but
do not become report sections merely because they exist.

## Fixed report shape

A report supporting a completed lab has exactly these top-level sections, in order:

1. `## Overview`
2. `## Evidence`
3. `## Analysis`

`Overview` contains the reader's starting point: a numbered
`Motivation`, `Background`, `Question`, and `Hypothesis`, plus the current
scientific boundary when needed. `Evidence` contains numbered validated facts,
the decisive figures, and a small curated evidence map. `Analysis` contains
numbered implications, limitations, and the next discriminating question.
Technical derivations, chronological remediation, and complete artifact
inventories belong in notes or result documents linked from that map.

Each major report fact or implication cites one `current` Local Wiki page. The
page, rather than a long raw-file list, owns its evidence boundary and links to
the underlying results. Dashboard-only `/lab-result` and `/lab-assets` routes
are not canonical report citations; use portable relative paths.

## One identifier grammar

Use one lab-local decimal namespace everywhere a reader needs to identify a
claim, figure, or sub-result:

```
L004.1      first report item in Lab 004
L004.4      a later top-level evidence item
L004.4.2    its second subordinate result
```

The prefix is the zero-padded lab number. Each dot component is a positive
integer. Number by report structure, not by the order experiments happened:

- `L004.1`–`L004.3` may be overview items;
- `L004.4` onwards may be evidence families;
- a subclaim or panel uses the parent identifier, such as `L004.4.2`.

Never recycle an identifier. Retired material keeps its identifier in a note
and is marked superseded. Internal filenames may retain `r6ab` or manifest
identifiers for provenance, but visible report labels must use the decimal
namespace. Each image is immediately followed by an italic caption beginning
`Figure L004.n` that interprets the visual and cites its supporting data
artifact.

## Visual-expression and length contract

`lab.json.report_contract` declares `max_lines` and `max_evidence_links`; its
defaults are 500 and 12. It deliberately has no figure-count target.

Before completion, review every major result and implication: use a figure,
table, or interactive artifact when it expresses the relationship more clearly
than prose. The report must contain at least one of these non-prose forms
unless its Limitations section explicitly explains why no meaningful visual
expression exists. This is a guard against a monotonous text wall, not an
instruction to manufacture decoration.

Every embedded figure must materially clarify a result, not decorate prose.
An artifact must be an interactive page under `results/` with an `.html`
extension. A static image is a figure, never an artifact.

## Completion test

Run:

```sh
python3 skills/organize-lab/scripts/lab_report_lint.py labs/<lab-id>
```

The lint checks the stable structure, local identifier grammar, reader-facing
run-ID leakage, visual-expression presence and figure captions, artifact type,
evidence-map size, and line budget. It is a completion gate, not a substitute
for the visualization pass or scientific review.
