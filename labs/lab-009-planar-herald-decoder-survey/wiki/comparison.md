---
title: Decoder survey, evidence cohorts and reuse
page_type: comparison
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Decoder survey, evidence cohorts and reuse

## Summary

This page separates decoder objectives, finite-size evidence cohorts, and the limits of reuse.

## Evidence

The [validation](../results/validation.json), [fresh benchmark](../results/benchmark.json), and [provenance ledger](../results/data-provenance.json) anchor the comparisons below.

## Status

Current as a finite-size comparison; inherited and fresh cohorts remain distinct, with no new threshold claim.

## Related pages

- [[model|Model and logical loss]]
- [[planar-ml|Planar sector solver]]

## Deduplicated algorithm families

| Family | Objective | Exactness and assumptions | Main benefit | Main limit |
| --- | --- | --- | --- | --- |
| Syndrome-only matching | Least prior-weight correction | Ignores herald information | Cheap baseline | Throws away a useful record |
| BP + LLR matching | Approximate edge marginals, then syndrome projection | Loopy approximate inference | Existing general local-factor machinery | Correlation and convergence loss |
| Signed configuration MAP | Highest individual configuration weight | Exact integer objective below half; literal floating objective above half | Hard constraints without BP | Does not sum logical entropy |
| Planar matchgate ML | Largest logical-sector sum | Algebraically exact trivalent planar factors; floating-point gates | Correlated Bayes inference with sparse LU | Geometry and conditioning |
| Exact transfer | Largest logical-sector sum | Exact binary contraction, bounded frontier width | Independent oracle, square support | Exponential width |
| MPS | Approximate logical-sector sum | Finite bond dimension, checked truncation | More flexible and batched contraction | No all-record risk certificate |
| Kac–Ward | Even-subgraph sector sum | Current finite-penalty version approximate | Useful determinant cross-check | Hard zeros and numerical conditioning |

Hard-constraint matching gadgets, direct signed T-joins and integer simplifications belong to one MAP family. Alternative planar matching gadgets implement one ML family. Exact transfer and finite-$\chi$ MPS share the tensor network but have different exactness claims. Three implementations of the same idea do not count as three scientific mechanisms.

The package adds configuration MAP, planar ML, transfer and MPS to a common factory. Existing BP defaults remain as documented in their class. The generic planar local-factor solver permits further factorized binary records; it is not automatic integration of all physical fusion or spacetime channels.

## Fresh implementation verification and timing

The lab's validation includes whole-error weighted enumeration, independent frontier contraction, alternate references, endpoint/impossible inputs, batch shapes and truncation sensitivity. Exactness receipts list scope and tolerance rather than saying every size is numerically certified.

The new benchmark uses 200 unconditional records in each of sixteen cells at $L=5,9$, shared by all five methods. Source BP is synchronous with a 40-iteration cap and default tolerance/damping. Nonconverged records are retained (2,218 of 3,200); syndrome-valid output remains scoreable. Setup and an independent warm call are excluded from median/p95 shot times. These results measure the current wrappers and this CPU environment, not the inherited implementations or a best-tuned BP study. Exceptions and invalid corrections count as failures; the completed cohort had none.

At size nine, typical warmed median times per record are roughly 1.9 ms for BP, 5.7–6.3 ms for MAP, 25–27 ms for planar ML, 47–48 ms for exact transfer, and 15 ms for $\chi=16$ MPS. Batched transfer/MPS improve throughput in the measured 16-record batches. MAP's per-shot matching reconstruction and repeated graph-property access contribute Python overhead. The source backend is sufficient for the scientific comparison; optimization is a separate future decision.

Wilson 95% intervals describe each realized failure proportion. Paired differences use common-record failure differences and their sample standard error. Conditional regret evaluates each selected sector against exact planar posterior, making the objective gap visible even when finite realized counts favor BP or MAP. Regret uncertainty is over sampled records; it is not a thermodynamic confidence interval. Exact oracles determine correctness, not whether ML happens to win all sixteen finite cohorts.

## Inherited cohorts, vectors and reproduced figures

[Data provenance](../results/data-provenance.json) records source hashes and copied numeric evidence. The lab snapshots 5,114,000 previously generated planar-ML trials in 1,430 parameter/size cells, preserving sufficient statistics for direct and Rao–Blackwellized LER. Trial-level errors from that campaign are not present; these are cell vectors, not reconstructed private samples. Fresh input/output/timing vectors are stored separately in `data/fresh-matched-vectors.npz` and load with `allow_pickle=False`.

Ten reported boundary curves from nine studies remain separate. Published estimates use different sizes, tie rules and fit conventions. Out-of-domain fits are excluded; connecting valid estimates is not a new fit. The three larger planar-ML studies place $p_c(q=0)$ near 0.163–0.165 and $q_c(p=1/2)$ near 0.866–0.872. MAP studies report different values near 0.158–0.160 and 0.88–0.89. These are descriptive ranges of reported estimates, not pooled confidence intervals. Crossing drift and fit-window sensitivity remain important at the historical half-domain endpoint; p=0.5 is interior to the physical domain.

The imported independent audit also contains a 4,000-record comparison at $L=7,11$ using residual-priority BP with an 80-iteration cap and separate MAP/ML implementations. At $L=11$, ML minus BP failure proportions are −0.048 at $(.24,.5)$ and −0.056 at $(.40,.8)$, with paired SE about .0159 and .0168. That is supportive local evidence. It is a distinct inherited cohort and cannot be pooled with the new synchronous-40 benchmark or its timings.

Lab 003 contributes its measured 231-cell finite-window directional map, mainly $L=7,9,11$. Its B18 symmetry-constrained guide has been withdrawn: incomplete heralding does not generally possess $p\leftrightarrow1-p$ symmetry. This lab preserves the measured evidence and records the limitation without relabeling it as an exact threshold.

## Selection and remaining questions

Use planar ML for this model when the sector posterior matters. Use MAP as a useful exact-configuration baseline or visible reference, not as a guaranteed BP replacement. Use exact transfer for bounded-width validation and generic factors; use MPS with convergence checks where the exact contraction becomes costly. Keep finite-penalty Kac–Ward outside standard production selection. All methods retain finite-size and floating-point qualifications.

No heavy phase campaign has been rerun, no new asymptotic threshold or universality class is claimed, and no noisy quantum channel is inferred from these classical results. The next scientific extension is a matched full-irrep binary-factor observation study with an independently validated law, or a separately registered large-size convergence comparison. Routine wrapper speedups should not substitute for that model decision.

## Full-domain evidence scope

Eight low-p pilot cells are retained and eight high-p cells are independently acquired. The full physical domain is p,q in [0,1], but these sixteen sampled cells are not a converged two-dimensional phase diagram. No reflected data, single-valued boundary or imposed half-point tangent is used. The inherited boundary fits concern their historical restricted domain; they do not establish high-p topology or an all-p herald ceiling. [Full-prior diagnostic](../results/full-prior-update.json).
