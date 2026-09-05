---
title: 'R2 source-normalized exhaustive flux-oracle audit'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# R2 source-normalized exhaustive flux-oracle audit

Date: 2026-08-28

## Question and exact method

This audit asks whether the first-stage PyMatching correction is globally optimal on the actual paper-`L=2` graph for both public weight rules, and whether minimum objective weight uniquely determines the Boolean-union logical decision.

An independent GF(2) Gaussian elimination constructs one particular solution and the full nullspace of the 24-by-36 incidence matrix. Its affine dimension is 13, so all 8,192 correction chains are enumerated for each syndrome. The registered 192-record matched R2 cohort is regenerated exactly; both syndrome-only and heralded objectives are evaluated on every feasible chain. Every global minimizer is then scored by physical/correction union homology.

## Results

Both execution objectives pass exactly:

- syndrome-only: 96/96 PyMatching weights equal the exhaustive global minimum and every returned correction belongs to the minimizing set;
- heralded: 96/96 satisfy the same gate, including negative-weight cases.

Minimum weight does not always fix the logical decision:

- syndrome-only has 12 tied optima; 9 records contain globally optimal corrections with both trivial and nontrivial union homology;
- heralded has 6 tied optima; 5 records contain both logical outcomes among global minimizers.

Thus PyMatching's deterministic correction is a valid global objective minimizer, but on these finite instances its logical result can depend on tie selection. This is not a solver failure. It is evidence that a minimum-weight oracle—even an exact one—does not define the Bayes-optimal logical decision. Later comparisons must preserve the concrete decoder's tie convention and separately sum posterior mass by logical sector for R4.

## Verification and boundary

Two new tests verify the complete 8,192-chain affine space, syndrome faithfulness, and exact agreement for both weight branches. The complete Lab 004 suite passes 70 tests. Machine-readable counts and representative ambiguous ties are in `manifests/r2-exact-flux-oracle-audit.json`.

This is an exact first-stage execution-objective audit. It is not the R3 fusion-constrained MILP, does not validate the second charge MWPM objective, and is not a conditioned logical posterior or performance experiment.

