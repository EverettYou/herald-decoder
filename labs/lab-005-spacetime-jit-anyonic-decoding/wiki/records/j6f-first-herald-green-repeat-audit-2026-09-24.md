---
title: First-herald green-repeat source-semantic audit
status: withdrawn
updated: 2026-09-24
record: true
---

## Summary

**Withdrawn: false source transcription.** This record incorrectly treated
the `p2`-weighted *dressed* green operator in Eq. (A13) as the bare green star
measured after correction. [J6G replaces this interpretation](j6g-source-stabilizer-disambiguation-2026-09-24.md)
using the visually inspected A13 and A14 operator diagrams. Preserve the
original audit only as provenance of the error; its purported contradiction
and downstream invalidation must not be cited as current evidence.
Reason for withdrawal: A13's bare and red-Z-dressed green stabilizers were
conflated. The J6G record is the replacement interpretation.

## Evidence

The [preregistered zero-sampling audit](../../manifests/j6f-first-herald-green-repeat-audit-2026-09-24.json)
and [exact result](../../results/j6f-first-herald-green-repeat-audit-2026-09-24.json)
show a source-semantic mismatch in the L=2 two-red-edge fixture. The first
green-star e-charge bit is 0 or 1 with probability 1/2 each. In
[Jing et al., Appendix A.2 Eq. (A6) and A.4 Eqs. (A13)–(A14)](https://arxiv.org/html/2507.23765),
the matching red-X correction preserves that green stabilizer eigenvalue
`p2`; subsequent blue endpoints share a common eigenvalue `p`. Thus the
post-correction green bit must equal the first green bit in this ideal,
no-new-fault sequence.

J6E's unconditional post-flux union sampler returned only `(blue0, green1,
blue2)=(0,0,0)` and `(1,0,1)`. Its `first_green=1` branch has no valid
post-flux record under the source rule. The four-case matrix (first-green
0/1 × common-blue 0/1) therefore passes for the two first-green=0 cases
and fails for both first-green=1 cases. This is a support contradiction,
not a noisy estimate; no joint probabilities for the blue bit are inferred.

## Status

The J6F conclusion and proposed freeze of the Lab 004 sampler are retracted.
The following text documents the historical inference, not an active claim.

Withdraw J6E's post-flux support and any D4 physical-risk or schedule
interpretation that depends on that sampler. Retain its graph, flux-chain
XOR and ideal projector-repeat algebra only as narrow kinematic facts.
Lab 004 `sample_postflux_charge_outcomes` accepts no first-herald record;
Lab 005's integrated-history caller inherits that omission. Preserve old
data as provenance, but do not promote it to a physical baseline. The next
bounded gate is to implement a source-consistent first-measurement/correction/
postflux conditional instrument, then audit every dependent result before
any new performance sampling. General-geometry probabilities remain open.

## Related pages

[[schedule-state|Schedule state]] · [[records/index|Research-record index]]
