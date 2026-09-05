---
title: 'J1 generic repeated-measurement history generator preflight'
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

# J1 generic repeated-measurement history generator preflight

Date: 2026-08-29

## Result

The registered **G-generic-preflight** layer is implemented and verified. It
samples three independent phenomenological channels from one explicit master
seed expanded into distinct data, syndrome-readout, and herald substreams:

- Bernoulli edge-data faults propagated through a supplied binary
  check–edge incidence matrix;
- Bernoulli syndrome-readout flips with adjacent-round detector construction;
- categorical `none`/`blue`/`green` herald readout with separate
  false-positive, false-negative, and blue/green-confusion probabilities.

The categorical channel is represented by the exact registered stochastic
matrix. Labels remain strings throughout generation, causal-prefix exposure,
history hashing, and four-branch scheduling; they are never coerced to a
Boolean herald field.

## Acceptance evidence

Eight focused fixtures verify:

1. nonnegative, unit-normalized confusion rows on a boundary/interior domain
   grid and rejection of `p_fn + p_confuse > 1`;
2. separate false-positive, false-negative, and label-confusion support;
3. zero data/syndrome noise recovery of truth readouts and detector identity;
4. the adjacent-time detector pair from one syndrome-readout fault;
5. bit-identical replay and parameter isolation across deterministic random
   substreams;
6. causal-prefix truncation with no truth, fault, or random-variate sidecars;
7. one generated history digest bound to immediate, fixed-delay-1, abstract
   JIT, and explicitly offline schedule requests; and
8. preservation and validation of all three categorical herald labels.

The focused fixtures pass 8/8. The complete Lab 005 suite passes 75/75.

## Provenance

- implementation: `scripts/generic_history.py`
  (`sha256:6b2509ed4619ff2a7e4610a2262874abb94fb961c384f7ca6d25407c8f05f8d4`)
- focused tests: `scripts/test_generic_history.py`
  (`sha256:10e55d8702148e5d9e46cbcf122cd6115e8e338ea83538548c8a333b128f1f09`)
- categorical digest support: `scripts/baseline_harness.py`
  (`sha256:64ac262f3401f04dbb7cb27d095b675abe37a46ccf0031b81c3e188cf40424da`)
- governing contract:
  `manifests/j1-layered-repeated-measurement-generator-manifest-2026-08-29.json`

## Claim boundary

This is a probability, schema, causality, and shared-history preflight. It is
not a D(S3) circuit-noise reproduction, not a derived noisy D4 fusion-herald
channel, and not a logical-performance, threshold, or fault-tolerance result.
No pilot samples or logical-error-rate data were produced.

The next scientific gate is to register the smallest prerequisite matrix for
the still-distinct R (D(S3) source reproduction) and E (derived noisy D4
spacetime herald) branches before either can support a meaningful performance
pilot.

