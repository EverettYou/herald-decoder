---
title: 'J1 repeated-measurement generator boundary audit'
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

# J1 repeated-measurement generator boundary audit

## Scientific correction

The phrase “source-matched repeated-measurement generator with noisy D4
heralds” combines two different models and must not be used.

Lyons–Brown formulate a D(S3) fault-tolerance construction under weak local
circuit noise. Physical errors form spatial strings, false stabilizer readings
form temporal strings, and gauging/ungauging introduces phase-boundary
detectors and circuit-dependent local faults. Their paper does not define the
project's blue/green D4 intrinsic-herald confusion channel.

Jing *et al.* demonstrate D4 intrinsic heralding from measured intermediate
fusion products, but the reported threshold analysis uses perfect syndrome
measurements. Adding false-positive, false-negative, and label-confusion noise
to repeated D4 herald readout is therefore a project extension, not a sourced
result.

## Layered contract

Three layers are now durable and separate:

1. **R — D(S3) source reproduction:** local circuit faults, repeated
   stabilizers, detectors, and gauging-boundary consistency. Not implemented.
2. **G — generic probability/schema preflight:** binary edge-data faults,
   binary syndrome readout flips, and a categorical `none/blue/green` confusion
   channel on supplied trajectories. Registered next because its normalization
   and anti-leakage properties can be tested without a physics claim.
3. **E — noisy D4 herald extension:** a future derived spacetime channel linked
   to Lab 004. Blocked on G plus an explicit D4 spacetime derivation.

For G, the registered categorical channel has separate false-positive
(`none`→label), false-negative (label→`none`), and blue/green confusion
probabilities. Exact matrix normalization, parameter-domain validation,
channel isolation, independent seeded substreams, causal prefixes, and matched
history across all schedules are acceptance gates.

Contract:
[`manifests/j1-layered-repeated-measurement-generator-manifest-2026-08-29.json`](../../manifests/j1-layered-repeated-measurement-generator-manifest-2026-08-29.json).

## Claim boundary

No generator was implemented and no data were sampled in this audit. The G
layer will be phenomenological and cannot be called Lyons–Brown reproduction
or noisy D4 physics. R and E remain separate blocked scientific deliverables.
No LER, schedule advantage, threshold, or fault-tolerance conclusion follows.

