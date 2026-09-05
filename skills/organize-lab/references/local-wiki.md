# Local Wiki contract

Each `labs/<lab>/wiki/` is the lab's navigable knowledge layer. `results/`
keeps machine-readable measurements and presentation assets; `manifests/`
keeps machine-readable experiment contracts; `wiki/` holds explanatory audit,
implementation, remediation, and decision records. `REPORT.md` is a concise
synthesis of the Local Wiki, not a second archive.

## Layout

```
wiki/
  index.md
  methods/<topic>.md
  evidence/<topic>.md
  decisions/<topic>.md
  records/<dated-record>.md
```

Each page has YAML frontmatter with `title`, `status` (`current`,
`superseded`, or `withdrawn`), and `updated`, then visible `Summary`,
`Evidence`, `Status`, and `Related pages` sections. Use relative Markdown
citations to `results/`, `notes/`, data, or figures and path-qualified local
wikilinks such as `[[methods/observation-model|Observation model]]`.

Create a page only for an independently useful concept, method, evidence
family, decision, or scientific boundary. A sequence of small tests usually
belongs in `wiki/records/`: preserve each dated record there, give the
collection one index, and cite the record collection from an evolving topical
page. This preserves provenance without producing a second uncontrolled file
pile in `results/` or in the report.

`current` pages may support report claims. `superseded` and `withdrawn` pages
must identify their replacement or reason and may be cited only as provenance.
The index groups pages by topic, not chronology, and every page must be
reachable from it.
