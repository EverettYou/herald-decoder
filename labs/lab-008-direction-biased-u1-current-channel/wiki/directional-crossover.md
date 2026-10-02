---
title: The singular directional crossover of the LER curve
status: current
updated: 2026-09-19
---

# The singular directional crossover of the LER curve

## Summary

The two limits p->0 and q->1 cannot be interchanged in the leading LER law.
For the canonical square with d=L-1>=2, the boundary layer is 1-q of order
p^(d-1), much narrower than simply requiring few reverse jumps. We derive
the exponent along every power-law approach and the complete leading
coefficient in that layer directly from physical logical-sector sums.
These are fixed-size asymptotic theorems, not finite-p fits or thresholds.

## Evidence

### Why return to the sector sums?

The [witness-union audit](connected-current-defects.md) proves that even exact
evaluation of the earlier full path-event union cannot improve on one half
at L5,p=.30,q=.5. The event envelope loses information that correcting its
overlaps cannot restore. The calculation here instead applies the physical
functional sum_Q min(Z_0(Q),Z_1(Q)) itself. It resolves the nonuniform endpoint
of the [fixed-q expansion](partition-function-ler.md).

### Exact exponent along a biased approach

Let 1-q=lambda p^alpha, with fixed alpha>0 and lambda>0. At small p the three
edge probabilities have leading orders 1, p and lambda p^(1+alpha).
A configuration therefore has weighted activity

\[
I_\alpha(j)=N_+(j)+(1+\alpha)N_-(j).
\]

For a fixed record Q, let s_h(Q) be the smallest I_alpha in logical sector h.
The positive finite sum Z_h has leading order p^s_h, with no cancellations.
The smaller sector has exponent max(s_0,s_1). Thus the exact risk exponent is
the minimum of those maxima over records. In particular,

\[
\boxed{\mathrm{LER}_{*,L}(p,1-\lambda p^\alpha)
=\Theta\!\left(p^{\nu_d(\alpha)}\right),}
\]
\[
\boxed{\nu_d(\alpha)=\min_{k=0,\ldots,d}
\max\{k,(1+\alpha)(d-k)\}.}
\]

**Lower bound on the exponent.** Take two compatible currents in opposite
logical sectors and order them so the right-boundary flux difference is
positive. Summation by parts with the horizontal coordinate gives

\[
N_{H,+}(j)-N_{H,-}(j)-N_{H,+}(j')+N_{H,-}(j')=dF_R,
\]

where F_R is a positive odd integer. Hence x=N_(H,+)(j) and
y=N_(H,-)(j') obey x+y>=d. Their weighted costs are at least x and
(1+alpha)y. Minimizing over nonnegative integer x,y gives the displayed
bound. Extra vertical currents cannot lower these costs.

**Attainment.** Split a straight left-to-right path into k positive edges
in j and d-k negative edges in j'. Then j-j' is the complete unit path:
the interior charges agree and the logical parities differ. Their costs
are k and (1+alpha)(d-k). The choices k=0,d include the empty/full path pair.
This attains every candidate needed in the minimum.

In particular nu_d=d if and only if alpha>=d-1. If alpha<d-1, choosing
k=d-1 gives an exponent strictly below d; if alpha>=d-1, every k<d has
(1+alpha)(d-k)>=d, while k=d attains d.

The exact exponents at the checked sizes are

\[
\begin{array}{c|ccc}
\alpha & L=3 & L=4 & L=5\\\hline
1/2 & 3/2 & 2 & 3\\
1 & 2 & 2 & 3\\
2 & 2 & 3 & 3\\
3 & 2 & 3 & 4
\end{array}
\]

For example, q=1-lambda p on L5 gives p^3, although q tends to one.
The endpoint itself gives p^4. The familiar fixed interior-q exponent
ceil(d/2) is recovered at alpha=0 with a fixed admissible q; its leading
coefficient has different forward weights and is not taken from this table.

### The complete boundary-layer coefficient

At alpha=d-1, a reverse jump has weight lambda p^d. Every configuration of
weighted activity at most d is either a fully forward configuration with at
most d jumps or a single reverse jump with no other active edge. This gives
the exact leading coefficient

\[
\boxed{\mathrm{LER}_{*,L}(p,1-\lambda p^{d-1})
=p^d\!\left[\binom{2d}{d}+Ld\lambda+(L-2)d\min(\lambda,1)\right]
+O(p^{d+1}).}
\]

The three contributions are distinct charge-record families:

1. Forward-only ambiguity contributes binom(2d,d), as in the directed
   theorem. Changing the forward probability to p-lambda p^d does not
   change this leading coefficient.
2. A single reverse horizontal edge has an opposite-sector forward
   completion of its row with d-1 edges. No forward configuration of
   activity at most d occupies the reverse edge's sector: horizontal
   conservation would require at least 2d-1 forward horizontal edges.
   Its smaller-sector weight is therefore lambda p^d. There are Ld edges.
3. A single reverse vertical edge has one opposite-sector completion with
   exactly d forward horizontal edges, consisting of the appropriate
   left prefix and right suffix on adjacent rows. A forward configuration
   with fewer than d jumps cannot have this charge record: with zero
   horizontal flux it would have only vertical forward currents, which
   cannot produce a reverse dipole on a measured column. At cost d the
   horizontal completion is unique. The two weights are lambda p^d and
   p^d, giving min(lambda,1). There are (L-2)d vertical edges.

Distinct single reverse edges have distinct records on these L>=3 patches.
Their records were not forward-only ambiguous at order d: the competing
forward-sector weights just described occur in only one sector. Thus these
terms do not double-count the directed coefficient. Terms with additional
edges start at order d+1 or higher. The kink at lambda=1 is a change in the
smaller sector's leading weight, not a thermodynamic phase transition.

For L5 the formula is

\[
\mathrm{LER}_{*,5}(p,1-\lambda p^3)
=\bigl[70+20\lambda+12\min(\lambda,1)\bigr]p^4+O(p^5).
\]

At lambda=1 its coefficient is 102 instead of the directed value 70.
Both curves have exponent four; having the same exponent does not mean
having the same logical error rate.

### Recovering the directed coefficient

The earlier coupling inequality is uniform in q at finite size:

\[
|\mathrm{LER}_*(p,1-\epsilon)-\mathrm{LER}_*(p,1)|
\leq1-(1-p\epsilon)^E\leq Ep\epsilon.
\]

Therefore epsilon=o(p^(d-1)) recovers the directed leading coefficient
binom(2d,d), at fixed L. The nonzero correction in the boundary-layer formula
shows why epsilon=lambda p^(d-1) does not recover that coefficient at fixed
positive lambda. This is a statement about relative low-noise accuracy;
the finite-graph risk itself remains continuous in q.

### Exact checks and their scope

The [registered calculation](../manifests/directional-crossover-2026-09-19.json)
and [executable sector enumeration](../scripts/check_directional_crossover.py)
enumerate every current of weighted activity at most d at L3,L4,L5 for
alpha=1/2,1,2,3. The largest case has 72,729 configurations. Exact integer
record-sector coefficient counts verify all 12 exponents and all 15
boundary-layer coefficients at lambda=1/4,1/2,1,2,4.

An independent full-support L3 calculation includes all 6,561 ternary
currents and uses exact rational probabilities. At lambda=1, alpha=1, the
ratio LER/p^2 is 13.12698,13.56158,13.78037 at p=.02,.01,.005, approaching
the proved coefficient 14. All nine registered finite-p controls are
reported, without a fitted exponent. These controls illustrate convergence;
the proof, not that convergence trend, establishes the limit.

The [result file](../results/directional-crossover-2026-09-19.json) records
all cases, exact coefficients, finite probabilities and input hashes.
No new physical records were sampled and no decoder was changed.

## Status

The exponent and boundary-layer coefficient are derived and pass the bounded
exact checks. They explain a singular directional crossover in the low-noise
curve, with fixed L throughout. They do not determine the moderate-p square
curve, a critical noise rate, a CFT or a joint L->infinity limit. The next
target has now passed: the [normalized fixed-p response](reverse-sector-response.md)
preserves the complete record-sector minimum and has a uniform quadratic
error certificate.

## Related pages

- [Current model, complex weights and the CFT question](complex-weights-and-cft.md)
- [Fixed-q partition expansion](partition-function-ler.md)
- [Connected defects and the witness-envelope limitation](connected-current-defects.md)
- [Research plan](../PLAN.md)
