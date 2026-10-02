---
title: Source-image disambiguation of the green postflux stabilizer
status: current
updated: 2026-09-24
record: true
---

## Summary

A visual reread of the original stabilizer diagrams retracts the prior J6F
objection. The `p2` label multiplies a *dressed* green operator, not the bare
post-correction green star. In the illustrated two-red-edge, L=2 case, the
second-round bare green charge is vacuum for either first-round `p2` result.
J6E's two postflux support patterns remain source-consistent in this narrow
case; a general action-conditioned D4 channel is not thereby validated.

## Evidence

The [preregistered disambiguation](../../manifests/j6g-source-stabilizer-disambiguation-2026-09-24.json)
pins the source PDF and both prior results. Its [four-case exact check](../../results/j6g-source-stabilizer-disambiguation-2026-09-24.json)
compares the source transcription with their machine-readable support; it
does not claim to read the paper automatically.

In [Jing et al., Appendix A.4 Eq. (A13)](https://arxiv.org/html/2507.23765),
the displayed second stabilizer is bare green star 2 with eigenvalue `+1`.
The displayed third stabilizer is `p2` times a *different*, red-Z-dressed
green operator. The text states that measuring blue star 1 or 3
anti-commutes only with that third stabilizer and replaces it. The final
Eq. (A14) explicitly retains bare green star 2, without `p2`, while the
two blue stars have common eigenvalue `p`. The article also states that
homologically trivial physical-plus-correction components have even parity
for each color. For this green singleton, that means vacuum.

Both first-green outcomes occur in the J6E fixture. For each one, the two
source-consistent local postflux patterns are `(blue0,green1,blue2)=(0,0,0)`
and `(1,0,1)`. J6E contains both. J6F incorrectly required green bit 1
when first-green bit 1; its two alleged counterexamples are therefore false.

## Status

J6F is withdrawn and J6E's exact local postflux support is restored. The
J6F-only claim that the Lab 004 sampler is wrong is retracted; no production
code or stochastic data was changed in this audit. J6/J6B stay censored for
their independently registered limitations. The next scientific gate remains
an explicit conditional stabilizer/density instrument, then general-geometry
and integrated-caller validation before physical schedule interpretation.

## Related pages

[[schedule-state|Schedule state]] · [[records/index|Research-record index]]
