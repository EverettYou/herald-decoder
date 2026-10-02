---
title: Normalized reverse-sector response at fixed noise
status: current
updated: 2026-09-19
---

# Normalized reverse-sector response at fixed noise

## Summary

At fixed physical occupation rate $p$, write $\epsilon=1-q$. The first
reverse-current correction can be made as a normalized joint law before
conditioning on a charge record. It keeps all zero-reverse and single-reverse
configurations, preserves records that first appear at order $\epsilon$, and
takes the logical-sector minimum only after those record-sector masses are
assembled. Its LER error is uniformly bounded by an exact total-variation
formula of order $\epsilon^2$.

This is a finite-graph theorem and a target-preserving approximation. It is
not a fitted posterior, threshold, phase classification, or evaluated L5 LER.

## Evidence

### A normalized joint-law expansion

An edge is idle, forward, or reverse with probabilities


\[
(1-p),\qquad p(1-\epsilon),\qquad p\epsilon.
\]

Let $P_\epsilon(j)$ be the resulting current law on $E$ edges. Define

\[
J_\epsilon=P_0+\epsilon
\left.\frac{\partial P_\epsilon}{\partial\epsilon}\right|_{\epsilon=0}.
\]

Conditional on an occupied-edge set of size $N$, $J_\epsilon$ assigns
weight $1-N\epsilon$ to no reverse edges, weight $\epsilon$ to each of the
$N$ single-reverse choices, and zero to configurations with two or more
reverse edges. Therefore it is positive for
$0\leq\epsilon\leq1/E$, and its conditional weights sum exactly to one.
It follows that $J_\epsilon$ is a normalized probability law, not a signed
or separately normalized posterior approximation.

For record $Q$ and logical sector $h$, write

\[
Z_h^J(Q;\epsilon)=Z_h^{(0)}(Q)+\epsilon\dot Z_h(Q).
\]

The insertion operator subtracts $Nw_0$ from the original record-sector
cell of every forward-only current of base weight $w_0$, then adds $w_0$
to the record obtained by reversing each occupied edge in turn. This
construction automatically includes charge records absent at
$\epsilon=0$.

The response risk is evaluated as

\[
R_J(\epsilon)=\sum_Q\min_h Z_h^J(Q;\epsilon),
\]

not by averaging an approximate conditional risk under the physical record
law. The right derivative at zero chooses $\dot Z_h$ in the strictly smaller
zero-order sector. At a tie it chooses
$\min(\dot Z_0,\dot Z_1)$; this includes a newly accessible record with
$Z_0^{(0)}=Z_1^{(0)}=0$.

### Exact uniform error certificate

For fixed $N$, the only negative difference $P_\epsilon-J_\epsilon$ is the
total single-reverse deficit

\[
N\epsilon\left[1-(1-\epsilon)^{N-1}\right].
\]

Averaging over $N\sim\mathrm{Binomial}(E,p)$ gives the exact configuration-law
total variation

\[
\boxed{\operatorname{TV}(P_\epsilon,J_\epsilon)
=Ep\epsilon\left[1-(1-p\epsilon)^{E-1}\right]}
\]

and Bernoulli's inequality gives

\[
\operatorname{TV}(P_\epsilon,J_\epsilon)
\leq E(E-1)p^2\epsilon^2.
\]

Pushing both laws through the current-to-$(Q,h)$ map cannot increase total
variation. For any normalized binary-sector joint law,

\[
R=\sum_Q\min(P(Q,0),P(Q,1))
=\frac{1-\sum_Q|P(Q,0)-P(Q,1)|}{2},
\]

so the reverse triangle inequality proves

\[
\boxed{|R(P_\epsilon)-R(J_\epsilon)|
\leq\operatorname{TV}(P_\epsilon,J_\epsilon).}
\]

### Full-support L3 validation

The [registered calculation](../manifests/reverse-sector-response-2026-09-19.json)
and [executable check](../scripts/check_reverse_sector_response.py) enumerate
all $3^8=6561$ currents and all 357 charge records on the canonical L3
square. Exact rational sector sums cover
$p=.05,.08,.10,.30,.46$ and
$\epsilon=.005,.01,.03$, for 15 full-support cells.

All joint response laws normalize exactly; an independent edge-insertion
construction reproduces every derivative coefficient. At each p, 96 records
first appear at order $\epsilon$, and 60 of them contain both logical sectors,
so discarding new records would change the LER response. Four strict sector
switches occur in some finite-$\epsilon$ cells, confirming that the minimum
must be retained after the affine sector sums rather than frozen at q=1.

Every exact LER error lies below the exact total-variation bound. The largest
observed L3 error is $5.93031\times10^{-4}$, at
$p=.46,\epsilon=.03$, while the bound there is $1.02331\times10^{-2}$.
The largest error-to-bound ratio across all cells is 0.22272. These are
validation diagnostics, not fitted constants.

For an $E=32$ graph, the theorem alone gives bounds from $1.5777\times10^{-4}$
at $p=.08,\epsilon=.005$ through 0.070392 at
$p=.30,\epsilon=.03$. These numbers alone certify only the approximation
error; the later L5 contraction and its failed width gates are reported below.

The [machine-readable result](../results/reverse-sector-response-2026-09-19.json)
contains every exact rational risk, response, error, bound, tie/new-record
diagnostic, and source hash. No physical records were sampled.

## Status

The fixed-p reverse-sector response theorem and all registered L3 controls
pass. This supplies a normalized, target-preserving route beyond the directed
endpoint, but its usefulness is rate-dependent: the E=32 certificate is tight
near q=1 and too broad by itself at the most aggressive registered moderate-p
cell. The [L5 response contraction](../manifests/l5-reverse-sector-contraction-2026-09-19.json)
is now separately preregistered at only $(p,q)=(.08,.97)$ and $(.30,.99)$.
It must retain the complete affine record-sector pair and return a contraction
interval no wider than the corresponding theorem certificate before a
physical-LER interval is allowed. The
[implementation gates](../results/l5-reverse-sector-contraction-gates-2026-09-19.json)
match every directly enumerated tiny/L3 record-sector coefficient to at most
$2.23\times10^{-16}$ and replay all 15 L3 cells, including new records and
sector switches.

The [frozen L5 contraction](../results/l5-reverse-sector-contraction-2026-09-19.json)
then completed both cells without censoring. At B=4096,
$p=.08,q=.97$ gives $R_J\in[.005631,.062498]$, of width .056868, while
$p=.30,q=.99$ gives $R_J\in[.002849,.466097]$, of width .463248. These widths
are respectively 10.32 and 54.26 times their exact TV certificates, so both
registered promotion gates fail. The widened envelopes are retained only as
diagnostics; neither is a promoted physical L5 LER interval. Peak pre-prune
state count was 2,532,424 and total runtime 448.9 seconds, within the frozen
caps. The stop rule closes B enlargement and additional-cell refinement.

Thus the normalized response theorem remains valid, but this charge-prefix
contraction does not make it quantitatively decisive on L5. Lab 008 closes at
this evidence boundary and requires a new target-preserving theorem or a
separately registered thermodynamic study to reopen.

## Related pages

- [The singular directional crossover](directional-crossover.md)
- [From the partition function to the LER curve](partition-function-ler.md)
- [Connected current defects](connected-current-defects.md)
- [Research plan](../PLAN.md)
