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

