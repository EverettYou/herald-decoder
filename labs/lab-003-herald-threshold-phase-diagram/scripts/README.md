# Scripts

`run_n0_convergence_cap_diagnostic.py` runs the registered matched square
$q=1$ convergence-cap matrix comparing synchronous-40, synchronous-80, and
stable-sort residual-priority-80.

`run_phase3_highq_convergence_cap_diagnostic.py` runs the bounded honeycomb
L=11 high-q prerequisite after the 20-cluster phase refinement. It holds the
stable-sort residual-priority recurrence fixed and compares only iteration
caps 80, 160, and 320 on 576 fresh matched observations. It fails closed on
syndrome mismatch or source drift and cannot itself update the phase boundary.

`test_run_phase2_scout.py` verifies the Phase 2 runner's fail-closed
correction-syndrome fidelity assertion and its raw-row, cell-summary, and
top-level persisted aggregates on a real residual-priority honeycomb smoke
shard. It also injects a start/end source-hash mismatch and verifies that the
runner raises before publication and removes the temporary raw shard.

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_n0_convergence_cap_diagnostic.py
```

Use `./run_phase1_extremes.sh`, never a bare `python3`, to run the registered
fixed-grid first wave for the Phase 1 $q=0$ and $q=1$ extremes. The wrapper
delegates to the project-level accelerated runtime, which pins the Python,
Numba, NumPy, and PyMatching environment. `run_phase1_extremes.py` fails before writing any
artifact if Numba is unavailable; each new artifact records its interpreter,
NumPy, Numba, and PyMatching versions.

Run `./run_phase1_extremes.sh --preflight` before a sweep. It must print
`"numba_available": true`. The runner writes per-cell aggregates and L=7/L=9
diagnostic crossings to `../results/`, and generates the two LER-versus-p
figures in `../figures/`. The output is an initial finite-shot diagnostic, not
a final threshold fit.

`run_q0_square_calibration.py` is the square-only refined Phase 1a runner.
It uses 0.005 spacing through the $p=0.10$--$0.14$ crossover region, writes
one raw record per shot, defaults to 5000 shots/cell, and uses nested
common-random-number error fields across $p$.
Run it through the same accelerated launcher:

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_q0_square_calibration.py
```

The square $q=1$ largest-size refinement is isolated from discovery artifacts
and defaults to five fresh seeds, 5000 shots/cell, $L=11,13$, and
$p=0.20,0.21,\ldots,0.32$:

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_q1_square_refined.py
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/analyze_q1_square_refined.py
```

The q=1 square high-p refinement uses fresh seeds, 5000 shots/cell, and 0.01
spacing through $p=0.30$--$0.49$. Run the two immutable shards with the same
seeds, then merge them into the unified $L=3,5,7,9,11,13$ analysis:

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_phase2_scout.py \
  --lattice square --q 1 \
  --p .30 .31 .32 .33 .34 .35 .36 .37 .38 .39 .40 .41 .42 .43 .44 .45 .46 .47 .48 .49 \
  --sizes 3 5 7 9 --seeds 610001 610002 610003 610004 610005 \
  --shots-per-seed 1000 \
  --stem q1-square-l3-l9-highp-refined-5000-2026-08-27
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_phase2_scout.py \
  --lattice square --q 1 \
  --p .30 .31 .32 .33 .34 .35 .36 .37 .38 .39 .40 .41 .42 .43 .44 .45 .46 .47 .48 .49 \
  --sizes 11 13 --seeds 610001 610002 610003 610004 610005 \
  --shots-per-seed 1000 \
  --stem q1-square-l11-l13-highp-refined-5000-2026-08-27
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/analyze_q1_square_all_sizes_highp.py
```

The bounded no-$L=3$ synchronous-40 crossing refinement uses 10,000
shots/cell and 0.005 spacing over $p=0.28$--$0.42$:

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_phase2_scout.py \
  --lattice square --q 1 \
  --p .280 .285 .290 .295 .300 .305 .310 .315 .320 .325 .330 .335 .340 .345 .350 .355 .360 .365 .370 .375 .380 .385 .390 .395 .400 .405 .410 .415 .420 \
  --sizes 5 7 9 11 13 --seeds 710001 710002 710003 710004 710005 \
  --shots-per-seed 2000 \
  --stem q1-square-l5-l13-crossing-refined-10000-2026-08-27
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/analyze_q1_square_crossing_refined.py
```

`run_phase2_scout.py` is the generic immutable Phase 2 shard runner. It accepts
every registered q value on the 0.05 skeleton, uses the same master uniforms
across independent q jobs and every p value, and writes both a summary JSON and
gzip-compressed per-shot JSONL. `submit_phase2_parallel.py` reads the durable
`../manifests/manifests/phase2-scout-manifest.json`, runs unique `(lattice,q)` shards through the
project runtime with bounded process parallelism, and records resumable status
under `.tmp/lab3-phase2-scout/status.json`.

For the 2026-08-28 residual-priority restart, pass
`../manifests/phase2-residual80-q-skeleton-manifest-2026-08-28.json`. The dispatcher is
manifest-driven and emits unique campaign stems plus the registered
residual-priority-80 flags. The analyzer uses the manifest confidence level,
resamples full nested-p seed trajectories independently by size, and retains
no/single/multiple-crossing topology when constructing conditional 90%
crossing intervals.

Adaptive manifests may set `q_grid_policy` to `explicit` and declare a
`shots_per_cell` value equal to `len(seeds) * shots_per_seed`. The analyzer
still requires every explicitly registered lattice/q shard and rejects a
partial q list unless this policy is stated. The first such registered wave is
`../manifests/phase3-residual80-honeycomb-highq-refinement-manifest-2026-08-28.json`.

The 2026-08-28 honeycomb campaign is complete. If a summary exists but its
declared gzip path has been reverted by the storage layer to one hidden atomic
temporary name, run `recover_declared_atomic_raw.py` before analysis. The tool
restores a file only when there is exactly one candidate and both its SHA-256
and decompressed row count match the immutable summary; it otherwise fails
without moving anything.

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/run_phase2_scout.py \
  --lattice square --q 0.50 --p .04 .08 .12 .16 .20 .24 .28 .32 .36 .40 .45 .49

python3 labs/lab-003-herald-threshold-phase-diagram/scripts/submit_phase2_parallel.py --workers 4
```

After every shard in the selected manifest has completed, run the Phase 2
analyzer through the same registered research runtime and pass that manifest:

```bash
./run_research_python.sh \
  labs/lab-003-herald-threshold-phase-diagram/scripts/analyze_phase2_scout.py \
  --manifest labs/lab-003-herald-threshold-phase-diagram/manifests/phase2-residual80-q-skeleton-manifest-2026-08-28.json
```

`analyze_phase2_scout.py` is fail-closed: it requires exactly one artifact for
every registered `(lattice,q)` pair, verifies each manifest/config hash,
runtime and source fingerprint, checks the gzip raw-record checksum and every
raw/per-seed/summary count, and rejects duplicate cells. It ignores `.tmp-*`
files and never modifies a shard. The output preserves every adjacent-size
sign change, attaches seed-cluster bootstrap intervals, and classifies each q
as `finite`, `ceiling`, `below-range`, or `unresolved`. It writes
`../results/phase2-q-skeleton-analysis-2026-08-27.json` plus separate square
and honeycomb q-p scouting figures under `../figures/`. These are scouting
diagnostics, not final asymptotic threshold estimates.

Run the focused unit tests with:

```bash
./run_research_python.sh -m unittest \
  labs/lab-003-herald-threshold-phase-diagram/scripts/test_analyze_phase2_scout.py
```
