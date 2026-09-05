# Evidence and methodology boundary

Lab 003 reports finite-window trend evidence from corrected posterior-LLR
decoding. A measured cell is not assigned an asymptotic phase. The active
method evaluates the posterior probability that LER trends upward or downward
across the sampled distances, retaining uncertainty and source-cohort
boundaries.

The formal definitions, withdrawn categorical-map assumptions, and fitting
constraints are in [`../METHODOLOGY.md`](../METHODOLOGY.md). The current
machine-readable source bundle is [`../results/current-evidence.json`](../results/current-evidence.json).

Important provenance boundaries:

- historical negative-log MWPM outputs are excluded;
- raw corrected-LLR observations can remain valid when later presentation or
  inference is superseded;
- discovery, refinement, and confirmation cohorts are never silently pooled;
- source drift and incomplete-provenance cohorts are recorded, not promoted.

The [boundary research log](honeycomb-boundary-research-log.md) distinguishes
current continuous trend evidence from earlier categorical or exploratory
figures retained for reproducibility.
