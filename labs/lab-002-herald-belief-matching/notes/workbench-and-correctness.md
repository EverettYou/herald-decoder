# Workbench and correctness

The [belief-matching workbench](../figures/herald-belief-matching.html) shows
one reproducible observation, its syndrome and herald, the soft posteriors,
posterior-LLR weights, and the resulting correction. It is an inspection tool,
not a benchmark.

The executable default is probability-damped BP with posterior LLRs.
Regression checks cover graph invariants, tree posteriors, syndrome
faithfulness, LLR weights, artifact fields, and compiled equivalence. See
[`../scripts/test_herald_bp_decoder.py`](../scripts/test_herald_bp_decoder.py)
and [`../results/llr-regression-preflight-2026-08-27.json`](../results/llr-regression-preflight-2026-08-27.json).
