---
title: 'R6 raw-trajectory compaction'
date: 2026-09-05
status: validated
---

# R6 raw-trajectory compaction

The R6 Monte Carlo outputs incorrectly retained every physical error pattern,
public observation, correction edge set, BP diagnostic, and wall time.  R6AE
also wrote cumulative Stage 1--5 payloads and duplicated each completed payload
as both a final file and a checkpoint.  The 27 redundant files occupied
18,636,645,592 bytes (about 17.36 GiB).

Before deletion, the final non-redundant raw sources were streamed into compact,
resumable sufficient-statistics files.  Each `(L, p_X)` cell retains:

- attempted histories and the next deterministic trajectory index;
- logical-failure counts for every decoder and the resulting LER;
- Wilson 90% and 95% binomial intervals;
- BP convergence counts as diagnostics only, never as a failure gate;
- matched two-decoder 2x2 outcome counts; and
- 256-history batch histograms for drift/correlation checks.

No grouping is required to estimate an IID Bernoulli LER error bar: `(k, n)` is
sufficient for Wilson or beta-binomial intervals.  The batch histogram is kept
to test the IID assumption and diagnose nonstationarity; it is not substituted
for the binomial sample size.

The compact counts passed internal invariants and cell-by-cell comparisons with
the frozen R6AE, R6W, R6X, R6Y, R6AB, and R6AF analyses.  The complete removal
map and validation record are in
`results/r6-raw-trajectory-compaction-manifest-2026-09-05.json`.
