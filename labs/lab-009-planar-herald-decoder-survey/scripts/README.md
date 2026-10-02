# Lab 009 reproduction

Run from the repository root, with the existing `.venv` research runtime. For deterministic single-thread timing use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; use writable `MPLCONFIGDIR` and `NUMBA_CACHE_DIR` directories when needed.

1. `validate_decoders.py`: literal weighted L2 oracle, independent transfer comparisons, endpoints, MPS sensitivity and finite-penalty Kac–Ward diagnostics. Writes `results/validation.json`.
2. `validate_planar_factor_contract.py`: independently weighted generic binary factors, references and edge-order permutation. Writes its separate interface receipt.
3. `audit_full_prior_symmetry.py`: complete L2 joint-record Bayes-risk sums, proving the interior-q counterexample and checking deterministic/endpoint cases.
4. `benchmark.py`: registered 200 shared trials per cell at L5/L9, all five package methods, single-shot and batch timing. Resumes complete checkpoints; a completed cohort is not regenerated. Keep existing checkpoint/vector files for the published results.
5. `import_data.py`: snapshot hashes and aggregate numeric vectors from the supplied studies. Requires the original run folder and audit folder; existing snapshots suffice for subsequent analysis. It does not execute their campaign scripts.
6. `build_survey_figures.py`: rebuild eight survey figures and publish the original named-run evaluation figure from saved numeric data, in PNG/SVG/PDF (original evaluation PNG/PDF); source hashes and scientific semantics are saved. It copies the measured parent trend table, not a symmetry-constrained guide.
7. `analyze_survey.py`: audit retained physical records, failure flags, posteriors, current-source replay and inherited cohort uniqueness; saves source/input hashes.
8. `verify_delivery.cjs`: uses Playwright and local Chrome to check the exact dashboard, figure downloads, report links, local wiki and workbench. Set `NODE_PATH` to the existing bundled Node modules.
9. `artifact_backend.py`: bounded dashboard adapter for the standard decoder factory. Serves one shared visible record at a time.

The separate `build_full_prior_report.py` belongs to the bounded full-prior correction checkpoint. Its figure/data remain provenance; the survey report is the final combined synthesis. It must not overwrite the final survey report on a routine figure rebuild.

Regression command: `PYTHONPATH=src .venv/bin/python -m unittest discover -s src/herald_decoder/tests -v`. Dashboard tests and rendered delivery verification are recorded in `results/delivery-verification.json` when the complete lab passes its delivery gate. Runtime/source receipts have explicit tested scope; inherited millions of trials are not claimed as a fresh rerun.

`integrate_run_evaluation.py` brings the existing nine-run audit into the Local Wiki and copies its exact named-run PNG/PDF. It updates provenance and runs automatically after survey figure generation; it does not execute submitted campaign code or regenerate trial data.
