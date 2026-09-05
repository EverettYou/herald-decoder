# Labs

Labs are the project’s exploratory workspace. A lab owns its scripts, configurations, raw results, figures, prospective plan, and completed report. Code becomes `src/` only after repeated, validated reuse; findings become Wiki knowledge only after a report identifies the evidence and its limitations.

## Result versus evidence

The Lab **Results** panel is deliberately selective: it contains only research-facing figures, interactive artifacts, and explicitly promoted summarized data. Raw shot records, intermediate JSON, launch manifests, preflight checks, and completion audits remain Lab evidence/provenance, not Results. In a Lab manifest, use `presentation: "page"` for a rendered figure or interactive artifact and `presentation: "result"` only for a compact, meaningful data summary; use `presentation: "download"` for provenance files that must not appear in the Results panel.

## Lab stage vocabulary

`labs/labs.json` uses one project-wide stage field. The Dashboard renders these labels consistently:

| Stage | Meaning | Badge color |
| --- | --- | --- |
| `design` | The question or protocol is being scoped before execution. | Blue-violet |
| `active` | The Lab is currently being executed or analyzed. | Teal-green |
| `blocked` | Progress requires a decision, dependency, or resolved failure. | Coral-red |
| `complete` | The Lab has concluded at its recorded evidence boundary. | Graphite-gray |
