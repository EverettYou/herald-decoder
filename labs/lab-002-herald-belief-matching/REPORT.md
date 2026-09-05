# Lab 002 — Herald-aware belief matching

## Overview

### L002.1 Motivation

Use herald information probabilistically rather than discarding it before matching.

### L002.2 Background

Joint syndrome–herald belief propagation produces posterior log-likelihood weights for a matching decoder.

### L002.3 Question

Can a stable belief-matching backend provide an auditable downstream decoder interface?

### L002.4 Hypothesis

Damped belief propagation with posterior-weighted matching is a robust practical interface.

## Evidence

### L002.5 Frozen backend

The selected backend uses synchronous damped belief propagation and posterior-LLR matching; its scope and validation are maintained in the [belief-matching backend](wiki/overview.md).

![Matched memory-versus-damping comparison for posterior-LLR belief matching](figures/llr-systematic-memory-vs-damping-rerun-2026-08-27.png)
*Figure L002.5 — the selected damping behavior is shown on the audited comparison; data: [belief-matching backend evidence](wiki/overview.md).* 

| Established | Boundary |
| --- | --- |
| Decoder interface and selected damping rule | Not a D4 threshold result |

## Analysis

### L002.6 Implications

The backend is a controlled input to D4 reproduction work rather than a claim that every observation model has been validated; see the [belief-matching backend boundary](wiki/overview.md).

### L002.7 Limitations

Its phenomenological validation does not replace a matched physical D4 public-record comparison, as recorded by the [belief-matching backend boundary](wiki/overview.md).

### L002.8 Next question

Test the corrected D4 signal-only interface in Lab 004.
