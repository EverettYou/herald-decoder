---
title: Ideal short-path conditional stabilizer instrument
status: current
updated: 2026-09-24
record: true
---

## Summary

For the paper's illustrated two-red-edge path on the pinned L=2 honeycomb,
the first green-star result `p2` is equiprobable. After a prescribed matching
red-X correction, the next blue-star result `p` is equiprobable *conditional
on either* `p2`. Both blue endpoints carry `p`, and the bare green star is
vacuum. This yields four joint local outcomes of probability `1/4` each.
It is an exact source-derived **local symbolic stabilizer instrument**, not
an implementation or verification of a general D4 density channel.

## Evidence

The [registered contract](../../manifests/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json),
[source-transcription runner](../../scripts/run_j6h_l2_conditional_stabilizer_instrument.py),
and [machine-readable four-branch result](../../results/j6h-l2-conditional-stabilizer-instrument-2026-09-24.json)
pin the archived paper and prior L=2 support fixtures. In
[Jing et al., Appendix A.2 Eq. (A6)](https://arxiv.org/html/2507.23765),
the first green measurement has `p2=±1`, each with probability `1/2`.
Appendix A.4 Eq. (A13) displays a blue-pair `+1` generator, bare green
`+1`, and a distinct `p2`-weighted dressed green generator. The paper states
that measuring blue star 1 or 3 anti-commutes only with that third generator.
The anticommuting-stabilizer measurement rule gives `P(p=±1|p2)=1/2`;
the measured blue generator replaces the dressed green generator. Eq. (A14)
then has equal blue signs `p` and bare green `+1`. The symbolic trace retains
this replacement separately from the public full-binary measurement arrays.

For either first green charge bit 0 or 1, the two committed postflux public
records have local charge bits `(blue0,green1,blue2)=(0,0,0)` and `(1,0,1)`.
Every other site has zero charge, and flux is cleared by the prescribed action.
Defer has no E2 record; it is not assigned an invented outcome. First and
second public arrays contain no private stabilizer or physical support field.
All four rows, the conditional `2×2` matrix, joint normalization and the
pre-existing support projection pass exactly; no stochastic histories,
schedule arms or bootstrap replicates were generated.

## Status

The illustrated ideal L=2 short-path conditional law is derived within the
paper's symbolic stabilizer sector. The `p2` label disappears from the
*listed local measured-star generators* after blue measurement, but this does
not prove equality of complete global density operators across branches.
Arbitrary geometry, other correction actions, new faults, noisy readings,
the general D4 transition kernel and the five-round caller remain unvalidated.
The next gate must test a genuine generalizable instrument and its public
adapter before any physical schedule-performance interpretation.

## Related pages

[[schedule-state|Schedule state]] · [[records/index|Research-record index]]
