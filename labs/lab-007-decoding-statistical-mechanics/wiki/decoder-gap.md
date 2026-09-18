---
title: Logical-sector inference versus marginal-weight matching
status: current
updated: 2026-09-14
---

# Logical-sector inference versus marginal-weight matching

## Summary

An exact posterior marginal is insufficient to guarantee optimal logical
inference. We exhibit strict counterexamples in the frozen fusion model,
including a hexagonal motif reproduced by the actual matching backend.
This separates a loss from converting marginals to a correction from any BP
approximation. It does not apportion Lab 006's large-lattice LER into those losses.

## Evidence

### Three different inferential targets

For a fixed physical channel and record s, sector Bayes decoding selects
h*=argmax_h Q_h(s). Exact-marginal matching instead computes r_a=P(e_a=1|s),
forms w_a=ln[(1−r_a)/r_a], and minimizes ∑_a w_a c_a over Ac=m.
This is MAP for the surrogate

\[
\widetilde P(c|s)\propto\mathbf1\{Ac=m\}\prod_a r_a^{c_a}(1-r_a)^{1-c_a}.
\tag{1}
\]

It is neither the true joint posterior nor a sum over logical equivalence
classes. BP-marginal matching replaces r by approximate BP beliefs. On a factor
tree BP is exact, but the remaining conversion (1) can still lose logical
information. On a loopy graph even converged BP can add marginal error.
This distinction follows the [parent method](../../../wiki/methods/sun-fusion-herald-belief-propagation.md),
with an explicit finite witness supplied here.

For any syndrome-compatible correction c(s), its conditional failure is
1−Q_{ℓ(c⊕c₀)}. Its excess risk is exactly

\[
\delta(s)=\max_h Q_h(s)-Q_{\ell(c\oplus c_0)}(s)\ge0.
\tag{2}
\]

There is no general ordering between BP-marginal and exact-marginal matching:
approximation errors can accidentally change a correction toward the better
sector. The two excess risks relative to Bayes are nonnegative separately.
Their difference need not be.

### A strict SU(2) witness with the actual matching backend

Use the registered rough hexagon with edge order
(L,a), (a,b), (b,c), (c,d), (d,e), (e,f), (f,a), (d,R).
Only a,…,f are measured. The logical cut is edge 0. Set p=1/3 and take
records (m,R)=[(1,2),(0,1),(1,2),(1,2),(1,2),(0,1)], where R is the SU(2)
irrep dimension. Directed and hidden orientation give the same result.
Choose the syndrome-compatible reference c₀={1,2,4}.

| Active edge set | Exact posterior mass | Relative sector |
| --- | --- | --- |
| {1,2,4} | 64/193 | 0 |
| {3,5,6} | 64/193 | 0 |
| {0,3,4,7} | 64/193 | 1 |
| {0,1,2,5,6,7} | 1/193 | 1 |

Hence Q₀=128/193 and Q₁=65/193. Edges 3 and 4 have marginal 128/193;
the other six have marginal 65/193. The unique maximum of (1) is
c={0,3,4,7}, in the **less likely sector**. Bayes failure is 65/193;
exact-marginal matching failure is 128/193, an excess of 63/193 on this record.
The record has physical probability 193/52488. PyMatching reproduces this
correction and its syndrome exactly. The witness is a finite degree-three
motif with unmeasured rough endpoints; it is not an estimate of large-L loss.

### Tree witness and an explicit backend boundary

A degree-four star with two left and two right rough endpoints is a factor
tree. In directed SU(3), at p=1/3 and central (m=0,R=8), four activity pairs
joining opposite rough sides each have posterior mass 9/37, while all four
edges active have mass 1/37. Every edge marginal is 19/37. Thus the ideal
surrogate uniquely selects all four edges (sector 0), although sector 1 has
mass 36/37. The conditional excess risk is 35/37. Parent BP reproduces the
exact tree marginals, so BP error cannot explain this example.

The star contains repeated detector columns. Passing them directly to
PyMatching merges parallel boundary edges; the actual returned chain is empty,
not the ideal all-four-edge minimizer. It happens to select the same wrong
sector, but the star is used only as a **mathematical hardening/tree witness**,
not as a claim that the backend solves every multigraph objective. All six
selected hexagon witnesses reproduce the exact surrogate objective. A follow-up
inspection found no repeated detector columns on either canonical parent lattice
at L=5,7,9,11. No parent production result is invalidated by this motif issue,
and no decoder implementation was changed.

### An error bound and an equivalence condition

Let T_h be the sector probabilities of any surrogate joint distribution,
and let d be the sector of its selected chain. Adding and subtracting T gives

\[
\max_h Q_h-Q_d\le2\,\mathrm{TV}(Q,T)
+\left[\max_hT_h-T_d\right].
\tag{3}
\]

The first term bounds distribution error; the second measures selecting a
single chain instead of the surrogate's most probable sector. Deterministic
sector projection cannot increase total variation. Equality of all edge
marginals alone controls neither term. A sufficient exactness condition is
that the surrogate has the true sector probabilities and that the selected
chain lies in a maximizing sector. A unique syndrome-compatible activity
configuration is a simple limiting case. Posterior factorization alone still
leaves chain-MAP versus sector-sum degeneracy to check.

### Exhaustive evidence and reproducibility

The [main results](../results/exact-model-checks-2026-09-14.json) cover all
records in 90 fixed fixture/group/orientation/prior cases. Twenty-one cases
contain strict witnesses, with exact tie handling; an average risk is also
reported using a declared smallest-mask tie rule. Every full-record Bayes risk
is at most its matched m-only risk. No binomial uncertainty is attached to
an exhaustive rational sum.

The [supplementary checks](../results/mapping-supplement-2026-09-14.json)
verify all 21 selected witnesses against PyMatching, retaining the 15 star
mismatches. Fifteen tree-BP checks agree with exact marginals to at most
1.12×10⁻¹⁶. The [registered scripts](../scripts/check_exact_model.py)
and [supplement](../scripts/check_mapping_supplement.py) retain fixture,
record, reference, posterior, source hashes, and numerical tolerances.

## Status

A loss from marginal-to-matching conversion is proved and demonstrated under
matched inputs. Its magnitude and group dependence on full square/honeycomb
families remain unresolved. Loopy BP error is not estimated by these tree checks.

## Related pages

- [Sector probabilities and Bayes risk](partition-function.md)
- [Self-conjugacy](conjugacy.md)
- [Discriminating predictions](predictions.md)
