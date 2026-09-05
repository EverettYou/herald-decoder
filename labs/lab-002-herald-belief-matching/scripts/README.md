# Scripts

- `lattice_model.py`, `herald_bp_decoder.py`, `legacy_damped_bp_decoder.py`, and `numba_bp_kernels.py` are compatibility shims. Their stable implementations now live in [`src/herald_decoder/`](../../../src/herald_decoder/), which owns the square/honeycomb model and posterior-LLR BP-plus-PyMatching decoder.
- `benchmark_memory_ab.py` runs the registered matched old-versus-new BP comparison with identical observations and the shared posterior-LLR PyMatching projection.
- The dense-array Numba kernels are mandatory for new benchmark artifacts; use the project launcher below rather than a bare interpreter.
- `benchmark_systematic_memory_ab.py` runs the legacy-only grid pilot and the process-parallel 1000-shot-per-cell systematic A/B with exact observation caching.
- `benchmark_decoders.py` performs matched Monte Carlo comparisons, scores soft posteriors, counts paired logical rescues/harms, estimates the operational effective physical error, and writes JSON plus Markdown results.
- `artifact_backend.py` returns one deterministic sample together with all three decoder paths, soft-quality scores, and the diagnostic syndrome-density flow for the interactive workbench. Its recurrence selector also defaults to damping.
- `trace_damping_convergence.py` performs the registered measurement-only Phase C0 trace for square L=9, p=0.20, q=1, seed=12 and writes the per-iteration JSON plus convergence figure without modifying the decoder.
- `benchmark_residual_priority_c5.py` compares the bit-identical compiled
  repeated-scan and stable-sort residual-priority orderings on the fixed C4
  square stream using warmed alternating-order timings.
- `benchmark_residual_priority_c6.py` performs the fresh square/honeycomb
  common-protocol end-to-end comparison of synchronous Numba and stable-sort
  residual priority.
- `benchmark_residual_priority_c7.py` applies the exact-equivalence gate and
  matched timing protocol to the allocation-only preallocated-buffer kernel.
- `benchmark_residual_priority_c8.py` gates the cached-product candidate on
  marginal, posterior-LLR, correction, convergence, iteration, and syndrome
  equivalence; it times the candidate only if every observation passes.
- `test_herald_bp_decoder.py` checks lattice invariants, posterior accuracy on a tree factor graph, and correction faithfulness.

Run tests from the repository root with the project-level accelerated runtime:

```bash
./run_research_python.sh -m unittest discover \
  -s labs/lab-002-herald-belief-matching/scripts -p 'test_*.py'
```

Run the single registered Phase C0 convergence trace with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/trace_damping_convergence.py
```

Run the Phase C5 compiled ordering profile with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_residual_priority_c5.py
```

Run the Phase C6 end-to-end confirmation with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_residual_priority_c6.py
```

Run the Phase C7 allocation-only equivalence benchmark with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_residual_priority_c7.py
```

Run the Phase C8 cached-product gate with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_residual_priority_c8.py
```

Run the registered preliminary benchmark with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_decoders.py
```

The focused attribution run recorded in `results/soft-attribution-benchmark.json` uses:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_decoders.py \
  --shots 100 --exact-shots 20 --sizes 5 --p 0.06 0.10 \
  --q 0.75 --p-m 0 --p-h 0 --seed 260826 \
  --output labs/lab-002-herald-belief-matching/results/soft-attribution-benchmark.json
```

Run the controlled BP-update A/B with:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_memory_ab.py \
  --shots-per-seed 100 --seeds 281001 281002 281003
```

Run the systematic pilot or final run through the same project launcher:

```bash
./run_research_python.sh \
  labs/lab-002-herald-belief-matching/scripts/benchmark_systematic_memory_ab.py \
  final --square-p .08 .10 .12 --honeycomb-p .16 .18 .20 \
  --shots-per-seed 200 --seeds 490001 490002 490003 490004 490005 \
  --workers 4 \
  --output labs/lab-002-herald-belief-matching/results/systematic-memory-vs-damping-ab.json
```
