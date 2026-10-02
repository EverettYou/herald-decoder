# Numerical evidence

Matched records are retained with their observation and scoring contracts. `results/data-provenance.json` records hashes for snapshots and derived tables; `results/figure-provenance.json` records the exact inputs/outputs of the reproduced survey figures. No threshold fit is rerun by figure generation.

- `fresh-matched-vectors.npz`: 3,200 new common-record trials at sizes 5/9 and eight parameter pairs per size. Each cell has keys ending in `errors`, `syndrome`, `herald`, `failure_flags`, `invalid_flags`, `predicted_sectors`, `posterior`, `timing_seconds`. Method order is `bp_matching`, `configuration_map`, `planar_ml`, `transfer_ml`, `mps_ml`. Posterior axes are `(shot, method, absolute sector)`, with NaN where no sector posterior is produced; timing is seconds. Truth is retained for scoring only, never passed to a decoder. `results/benchmark.json` supplies cell settings, setup/warm call times, Wilson intervals and paired statistics.
- `warm-runtime-summary.csv`: pooled median/p95 for an equal-size mix of the eight fresh cells, 1,600 timed decodes per method/size; one thread, setup and independent first call excluded. Per-cell results remain available.

Load numeric arrays with `numpy.load(path, allow_pickle=False)`. No binary cache or downloaded campaign runner is required. Reproduction scripts are listed in `scripts/README.md`; figures are generated in PNG and editable SVG/PDF.

## Vector figure exports

| Figure | SVG | PDF |
| --- | --- | --- |
| fresh-matched-ler | [SVG](../figures/fresh-matched-ler.svg) | [PDF](../figures/fresh-matched-ler.pdf) |
| fresh-conditional-regret | [SVG](../figures/fresh-conditional-regret.svg) | [PDF](../figures/fresh-conditional-regret.pdf) |
| warm-runtime | [SVG](../figures/warm-runtime.svg) | [PDF](../figures/warm-runtime.pdf) |
| approximation-diagnostics | [SVG](../figures/approximation-diagnostics.svg) | [PDF](../figures/approximation-diagnostics.pdf) |

