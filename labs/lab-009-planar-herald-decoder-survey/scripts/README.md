# Lab 009 reproduction

Run from the repository root, with the existing `.venv` research runtime. For deterministic single-thread timing use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; use writable `MPLCONFIGDIR` and `NUMBA_CACHE_DIR` directories when needed.

1. `validate_decoders.py`: literal weighted L2 oracle, independent transfer comparisons, endpoints, MPS sensitivity and finite-penalty Kac–Ward diagnostics. Writes `results/validation.json`.
2. `validate_planar_factor_contract.py`: independently weighted generic binary factors, references and edge-order permutation. Writes its separate interface receipt.
3. `audit_full_prior_symmetry.py`: complete L2 joint-record Bayes-risk sums, proving the interior-q counterexample and checking deterministic/endpoint cases.
4. `benchmark.py`: registered 200 shared trials per cell at L5/L9, all five package methods, single-shot and batch timing. Resumes complete checkpoints; a completed cohort is not regenerated. Keep existing checkpoint/vector files for the published results.
6. `build_survey_figures.py`: rebuild four matched benchmark and approximation figures from saved numeric data, in PNG/SVG/PDF; source hashes and scientific semantics are saved.
7. `analyze_survey.py`: audit retained physical records, failure flags, posteriors, current-source replay; saves source/input hashes.
8. `verify_delivery.cjs`: uses Playwright and local Chrome to check the exact dashboard, figure downloads, report links, local wiki and workbench. Set `NODE_PATH` to the existing bundled Node modules.
9. `artifact_backend.py`: bounded dashboard adapter for the standard decoder factory. Serves one shared visible record at a time.

The separate `build_full_prior_report.py` belongs to the bounded full-prior correction checkpoint. Its figure/data remain provenance; the survey report is the final combined synthesis. It must not overwrite the final survey report on a routine figure rebuild.

Regression command: `PYTHONPATH=src .venv/bin/python -m unittest discover -s src/herald_decoder/tests -v`. Dashboard tests and rendered delivery verification are recorded in `results/delivery-verification.json` when the complete lab passes its delivery gate. Runtime/source receipts have explicit tested scope.


The reader-facing vertex-weight/Pfaffian derivation is checked independently by `validate_site_gadget_partition.py`: four local signatures and eight small closed planar fixtures compare literal physical partition sums, auxiliary matching sums, Pfaffians and inverse-matrix edge probabilities. This check acquires no Monte Carlo samples and does not expand the production geometry API.
The exact document and Local Wiki rendering check is `verify_site_gadget_wiki.cjs`; its receipt is `results/site-gadget-wiki-render-review.json`.

Run `MPLCONFIGDIR=/tmp/lab009-mpl .venv/bin/python labs/lab-009-planar-herald-decoder-survey/scripts/build_k4_gadget_diagrams.py` from the repository root to rebuild the three explanatory K4 schematics in PNG/SVG/PDF. The generator checks each illustrated matching against the existing local partition fixture and writes `results/k4-gadget-diagrams.json`; it is separate from the survey and phase-diagram figure pipelines.

## Full-domain phase diagram

1. `validate_phase_method.py`: matched cached/vectorized planar posterior and speed gate, with independent transfer checks.
2. `run_phase_sweep.py --workers 6`: resume the registered three-size full-square grid.
3. `analyze_phase_sweep.py --refine`: freeze selected refinement jobs; archive the broad grid receipt before refinement. `archive_phase_pilot.py` preserves the original record prefixes with independently checked risk/count summaries.
4. `run_phase_sweep.py --jobs labs/lab-009-planar-herald-decoder-survey/manifests/phase-refinement-jobs.json --workers 6`: acquire independent confirmation records and size-32 checks.
5. `select_phase_guard_checks.py`, followed by `run_phase_sweep.py --jobs labs/lab-009-planar-herald-decoder-survey/manifests/phase-guard-jobs.json --workers 6`: execute the bounded adjacent-bracket and closing-region checks, preserving the declared stopping rule.
6. `audit_phase_vectors.py`: verify every retained observation/score vector, whole-error oracle and source replays.
7. `analyze_phase_sweep.py`: confirmation-only crossing bootstraps, full-domain size-trend evidence and tabular risk data.
8. `build_phase_diagram.py`, then `publish_phase_diagram.py`: PNG/SVG/PDF, provenance, main report, wiki and active registry.
9. `verify_delivery.cjs`: verify the complete rendered delivery chain.

The measurement method is exact planar sector summation with unchanged numerical gates. `phase_runtime.py` caches canonical incidence and vectorizes identical local weights. This support work is frozen after the matched-input promotion gate.
