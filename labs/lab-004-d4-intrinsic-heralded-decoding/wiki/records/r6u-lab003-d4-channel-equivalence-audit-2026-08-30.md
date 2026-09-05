---
title: 'R6U — Lab 003 `q=3/4` versus the implemented D4 first-fusion channel'
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

# R6U — Lab 003 `q=3/4` versus the implemented D4 first-fusion channel

**Status:** complete audit; no common-channel threshold comparison is licensed.

## Conclusion

This memo compares the implemented Lab 003 phenomenological observation channel
with the implemented Lab 004 first D4 fusion record, conditional on a fixed
physical edge-error assignment `E`.

**Verdict: non-equivalence.** No deterministic coarse-graining from the D4
public record to Lab 003's `q=3/4` binary-herald channel preserves the
conditional observation law. The models share a Bernoulli edge prior and parity
flux syndrome, but not the herald/fusion record. Therefore a Lab 003 crossing
is not an estimate of a D4 threshold and must not be compared numerically to
the paper's D4 result or a D4-native O0/O2/BP curve.

## Event-by-event likelihood table

Let `d_v(E)` be the selected-edge degree at vertex `v`. The Lab 003 column uses
the noise-free setting `p_m=p_h=0` and `q=3/4`.

| `d_v(E)` | Lab 003 `(s_v,h_v)` | D4 `(f_v,c_v)` | Consequence |
|---|---|---|---|
| any `d` | `s_v=d mod 2` | `f_v=d mod 2` | Flux/syndrome is the common marginal. |
| `d=0,1` | `h_v=0` surely | `c_v=-1` surely | A support bit can call both unheralded. |
| `d=2` | `h_v=1` with 3/4; 0 with 1/4 | `c_v` must be measured: 0 or 1; allowed *joint* assignments have probability `2^(C-N_internal)` | D4 support is deterministic, not 3/4 thinning. |
| `d>2` | `h_v=1` with 3/4; 0 with 1/4 | `c_v=-1` surely | Support disagrees for every `q>0`. |

## Implementation evidence

- Lab 003 samples independent edge errors, defines `eligible = degree >= 2`,
  then samples the binary herald with probability `q(1-p_h)` at each eligible
  detector: [`lattice_model.py`](../../../../src/herald_decoder/lattice_model.py#L95-L114).
  Its likelihood is explicit: `P(h=1|d>=2)=q(1-p_h)` and `P(h=1|d<2)=0`
  ([`herald_bp_decoder.py`](../../../../src/herald_decoder/herald_bp_decoder.py#L37-L53)).
- Lab 004 represents D4 charge as `-1` (unmeasured), `0` (vacuum), or `1`
  (Abelian e charge), and accepts a measurement iff `d=2`
  ([`d4_observation.py`](../../scripts/d4_observation.py#L76-L142)).
- The D4 sampler initializes all charge values to `-1`, samples binary values
  only at `degrees == 2`, and fixes one pivot per constraint to enforce parity
  ([`d4_sampler.py`](../../scripts/d4_sampler.py#L90-L120)).

Thus the audited D4 implementation is uniform on an allowed binary charge
affine subspace, rather than an IID per-vertex 3/4 Bernoulli-herald model. If
“three out of four `m×m` outcomes are non-vacuum” is a microscopic statement,
it needs a separately registered source-to-record derivation; it cannot replace
the code-defined likelihood above.

## Candidate coarse-grainings

1. **Measurement-support bit** `h_v=1[c_v!=-1]` gives probability one at
   `d=2` and zero at `d>2`, unlike Lab 003's 3/4 at both degrees.
2. **Charge-one bit** `h_v=1[c_v=1]` merges `-1` and vacuum. It still has no
   `d>2` support and inherits the D4 affine parity correlations.
3. **Restricted support fixture:** condition on maximum degree at most two,
   discard charge values, and set Lab 003 `q=1`. This can align support only;
   it is not `q=3/4`, loses D4-visible information, and changes the ensemble.
4. **Random thinning:** hiding one quarter of degree-two D4 measurements
   defines a new hybrid channel; it neither creates Lab 003's `d>2` heralds nor
   restores discarded values/correlations.

## Valid comparison

The valid experiment is D4-native: apply O0 unit-MWPM, O2 published
herald-weight MWPM, and D4-local BP posterior-LLR MWPM to the same sampled
`(flux_syndrome, charge_outcomes)` record, and compare matched multi-size
flux-recovery LER curves. Lab 003 remains a phenomenological study unless a
new source-derived common channel is explicitly registered.
