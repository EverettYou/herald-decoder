---
title: 'R6X dense-Numba production-backend remediation'
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

# R6X dense-Numba production-backend remediation

## Problem

The active scan path was not uniformly enforced: one production runner called
the generic Python `run_sum_product` recurrence even though the validated
dense-Numba recurrence had already passed the R6Q equivalence audit. A timing
report could therefore describe a Python execution while the registered
implementation claimed dense execution. Existing checkpoints also had no
backend identity, so resuming them could silently mix implementations.

## Changes

- `d4_local_bp.py` now defines one production backend ID,
  `r6d_dense_template_numba_v1`, and emits the module SHA-256 and runtime
  Numba availability as immutable provenance.
- `require_r6d_dense_backend()` is called by the production R6N and R6V scan
  entry points. It fails closed when Numba is unavailable or a manifest asks
  for a different backend.
- R6N now builds one cached dense template per cell and calls
  `run_r6d_dense_template`; it no longer imports or calls the Python reference
  recurrence.
- R6V serializes the same provenance at payload and BP-row level. Its resume
  guard rejects checkpoints with missing, stale, or mismatched provenance.
  Terminal physical-winding rows are allowed to omit decoder policy data.
- R6N/R6V/R6W/R6X manifests declare the backend ID. The old checkpoint files
  are preserved for auditability but are intentionally not upgraded or
  resumed, because their execution backend cannot be proven from the file.

## Verification

The focused test suite passes (10 tests), including exact dense-vs-Python
equivalence, production-runner AST checks, backend availability/provenance,
and fail-closed checkpoint validation. The Python recurrence remains in the
repository only as an explicit equivalence/reference control; it is not a
production scan default.

## Boundary and next action

This is an implementation-integrity remediation, not a new threshold or LER
result. R6X threshold refinement must start from a fresh checkpoint produced
by the dense backend and then analyze the declared multi-size crossing and
40-vs-160 iteration sensitivity.

