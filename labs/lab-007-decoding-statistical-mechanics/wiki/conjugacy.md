---
title: What self-conjugacy removes, and what it does not
status: current
updated: 2026-09-14
---

# What self-conjugacy removes, and what it does not

## Summary

For SU(2), hidden and directed orientation have identical joint laws for
activity and the full record, hence identical sector posteriors and Bayes
risks. U(1) and SU(3) already violate that quotient on a two-edge rough path.
This is a channel distinction; it is not an information-ordering theorem.

## Evidence

### SU(2) quotient theorem

Every fundamental leaf is isomorphic to its dual. Under the stipulated local
maximally mixed fusion instrument, f_v depends only on k_v and R_v. Therefore
for fixed e and s, summing its 2^{|e|} hidden orientations cancels exactly the
2^{−|e|} in the prior:

\[
\sum_{x:\,|x|=e}W_{\rm hidden}(x;s)
=\prod_a p_a^{e_a}(1-p_a)^{1-e_a}\prod_{v\in M}\psi_v(e;s_v)
=W_{\rm directed}(e;s).
\tag{1}
\]

The identity survives restriction to any logical sector and implies equality
of P(s), P(e|s), Z_h(s), exact activity marginals, and optimal risk, for any
finite graph and inhomogeneous prior. Pseudoreality introduces no sign in
these nonnegative irrep probabilities. It could matter in a coherent amplitude
model, which is outside the assumed instrument.

It also intertwines the parent's sum-product updates: sum the two active
message components; every local factor depends only on activity, so these
sums obey the binary recurrence. With correspondingly aggregated initialization,
the same damping and sweep count, activity beliefs agree at every iteration.
Stopping tolerances based on individual ternary components can differ by a
factor of two, so a claim of identical stopping iterations requires the actual
implementation convention. Neither convergence nor correctness on cycles is
implied. This theorem explains orientation invariance, not the absolute LER.

### A sector-level distinction on the same visible record

Use L→v→R with only v measured, c₀=00, and h the first-edge parity. For the
record (m=0,R=trivial), the two supported activity configurations are 00 and 11.
At p=1/3:

| Group | Sector-1 probability, directed | Sector-1 probability, hidden |
| --- | --- | --- |
| U(1) | 1/5 | 1/9 |
| SU(2) | 1/17 | 1/17 |
| SU(3) | 1/37 | 1/73 |

For U(1), both active edges have zero measured charge only when their shared
orientations agree; the hidden likelihood is 1/2 instead of 1. For SU(3),
the corresponding singlet likelihood is 1/18 instead of 1/9. SU(2)'s
likelihood is 1/4 in either channel. These ratios follow by comparing
Z₀=(1−p)² with Z₁=p² times the relevant likelihood. The same observation
is feasible in both channels, but its probability and sector posterior change.
The [exact checks](../results/exact-model-checks-2026-09-14.json) exhaust these
records rather than comparing unrelated syndrome samples.

### Why separate endpoint averaging fails

Take one active edge with both degree-one endpoints measured. In hidden U(1),
the joint charge pair is (−1,+1) or (+1,−1), each with probability 1/2.
Independent endpoint averaging instead gives each opposite pair probability
1/4 and introduces two impossible same-sign pairs. The SU(3) version replaces
±1 by F and F̄ and has the same obstruction. The latent sign must remain shared
through every contraction and mapping.

### SU(3) does not inherit the U(1) current constraint

N-ality gives (Dx)_v=ν(R_v) mod N, but it does not determine the integer
(Dx)_v. The measured m also imposes (Dx)_v=m_v mod 2. Thus two states with
the same record have divergence differences divisible by lcm(N,2), rather
than necessarily zero. At a trivalent SU(3) vertex,

\[
P(R=1\mid F^{\otimes3})=P(R=1\mid\bar F^{\otimes3})=1/27.
\]

Both have m=1 and the identical full irrep; their signed divergences are +3
and −3. Their difference is 6. A divergence-free integer height field cannot
represent both states relative to one reference without additional source
variables. Charge reduction modulo three also discards irrep multiplicities
and dimensions, so a bare clock model is insufficient.

## Status

The SU(2) quotient is proved at sector level; U(1)/SU(3) counterexamples are
exact. Nothing here orders average risk across the two different channels.
For a single fixed channel, revealing R in addition to m cannot worsen the
optimal average risk; the exhaustive check verifies that separate statement.

## Related pages

- [Partition function and matched-model identity](partition-function.md)
- [Statistical-mechanics reductions](statistical-model.md)
- [Inherited orientation evidence](problem.md)
