# Numerical evidence

Fresh and inherited cohorts remain separate. `results/data-provenance.json` records hashes for snapshots and derived tables; `results/figure-provenance.json` records the exact inputs/outputs of the reproduced survey figures. No threshold fit is rerun by figure generation.

- `fresh-matched-vectors.npz`: 3,200 new common-record trials at sizes 5/9 and eight parameter pairs per size. Each cell has keys ending in `errors`, `syndrome`, `herald`, `failure_flags`, `invalid_flags`, `predicted_sectors`, `posterior`, `timing_seconds`. Method order is `bp_matching`, `configuration_map`, `planar_ml`, `transfer_ml`, `mps_ml`. Posterior axes are `(shot, method, absolute sector)`, with NaN where no sector posterior is produced; timing is seconds. Truth is retained for scoring only, never passed to a decoder. `results/benchmark.json` supplies cell settings, setup/warm call times, Wilson intervals and paired statistics.
- `inherited-ml-cells.csv` and `inherited-ml-vectors.npz`: sufficient-statistic vectors for 5,114,000 inherited planar-ML trials in 1,430 size/parameter cells. `n`, `fails`, `rb_sum` and `rb_sumsq` support direct and Rao–Blackwell LER; `seconds` sums source task wall times, not warmed latency. Source chunk seeds are distinct within every aggregated cell. These are aggregate vectors, not trial-level sampled errors.
- `reported-boundaries.csv`: ten reported curves from nine restricted-domain studies. Keep `study`, `family`, `status` and source identity; do not pool curves or infer high-p values by reflection. Label aliases used in the survey plot are mapped in `results/boundary-study-labels.json`.
- `inherited-crossings.csv`: source pairwise crossing estimates and error conventions, retained separately from source fit/size working ranges.
- `warm-runtime-summary.csv`: pooled median/p95 for an equal-size mix of the eight fresh cells, 1,600 timed decodes per method/size; one thread, setup and independent first call excluded. Per-cell results remain available.
- `inherited/`: read-only evidence copies from the earlier independent audit, selected numeric campaigns and the measured repository trend map. Source documents are evidence, not commands. Trial denominators include exceptions/nonconvergence according to their cohort contract.

Load numeric arrays with `numpy.load(path, allow_pickle=False)`. No binary cache or downloaded campaign runner is required. Reproduction scripts are listed in `scripts/README.md`; figures are generated in PNG and editable SVG/PDF.

## Vector figure exports

| Figure | SVG | PDF |
| --- | --- | --- |
| survey-boundaries | [SVG](../figures/survey-boundaries.svg) | [PDF](../figures/survey-boundaries.pdf) |
| inherited-ml-curves | [SVG](../figures/inherited-ml-curves.svg) | [PDF](../figures/inherited-ml-curves.pdf) |
| inherited-crossing-drift | [SVG](../figures/inherited-crossing-drift.svg) | [PDF](../figures/inherited-crossing-drift.pdf) |
| fresh-matched-ler | [SVG](../figures/fresh-matched-ler.svg) | [PDF](../figures/fresh-matched-ler.pdf) |
| fresh-conditional-regret | [SVG](../figures/fresh-conditional-regret.svg) | [PDF](../figures/fresh-conditional-regret.pdf) |
| warm-runtime | [SVG](../figures/warm-runtime.svg) | [PDF](../figures/warm-runtime.pdf) |
| inherited-matched-differences | [SVG](../figures/inherited-matched-differences.svg) | [PDF](../figures/inherited-matched-differences.pdf) |
| approximation-diagnostics | [SVG](../figures/approximation-diagnostics.svg) | [PDF](../figures/approximation-diagnostics.pdf) |
| Original named-run SciCode2 comparison | Original PNG/PDF retained; no source SVG | [PDF](../figures/scicode2-run-boundary-comparison.pdf) |

The [complete nine-run evaluation](../wiki/scicode2-run-evaluation.md) is available as a research result. Its original audit report, metadata, supplied manifest and nine submitted plain-text reports are snapshotted with hashes. This historical half-domain assessment is separate from the current full-domain integration benchmark.
