---
title: SU(N) full-irrep belief propagation
page_type: method
status: validated-finite-size
updated: 2026-09-14
source_refs:
  - labs/lab-007-decoding-statistical-mechanics/REPORT.md
  - labs/lab-006-sun-bp-theory/REPORT.md
  - labs/lab-006-sun-bp-theory/PLAN.md
  - labs/lab-006-sun-bp-theory/scripts/sun_fusion_bp.py
  - labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py
  - labs/lab-006-sun-bp-theory/scripts/artifact_backend.py
  - labs/lab-006-sun-bp-theory/scripts/test_artifact_backend.py
  - labs/lab-006-sun-bp-theory/results/small-graph-exact-vs-bp.json
  - labs/lab-006-sun-bp-theory/results/a1-numba-belief-matching.json
  - labs/lab-006-sun-bp-theory/results/a5b-two-dimensional-convergence-scan.json
idea_ids: []
topics: [Quantum Error Correction, Symmetry-Enriched Systems, Decoding Algorithms]
---

# SU(N) full-irrep belief propagation

**Summary**: The decoder observes exactly two labels at each vertex,

\[
s_v=(m_v,R_v).
\]

The binary label \(m_v\) resolves the \(\mathbb Z_2\) topological/gauge-sector boundary, while the complete
\(\mathrm{SU}(N)\) irrep \(R_v\) resolves the symmetry sector and is itself the representation-resolved heralding signal.
The local fusion law turns this joint record into a normalized likelihood for binary edge errors. Sum-product
belief propagation (BP) estimates the posterior edge probabilities, which become weights for a
syndrome-constrained matching decoder. BP is exact on a factor tree and is a Bethe approximation on a generic
loopy lattice. The implementation also supports a hidden-orientation undirected edge channel, a min-sum
alternative, and explicit message damping; these choices have different probabilistic meanings.

**Sources**: [Lab 006 viewer](/lab?id=lab-006-sun-bp-theory) · [Lab 006 report](../../labs/lab-006-sun-bp-theory/REPORT.md)

**Last updated**: 2026-09-14

---

## Why the record contains both \(m_v\) and \(R_v\)

The two entries are associated with different structures of a symmetry-enriched topological system:

- \(m_v\in\mathbb Z_2\) is the boundary of the binary error chain. It is the gauge/topological-order label used
  as the hard constraint by the matching decoder.
- \(R_v\in\widehat{\mathrm{SU}(N)}\) is the complete measured symmetry irrep at the same site. It reweights the error
  hypotheses compatible with the gauge-sector boundary.

Thus the record jointly resolves information that a measurement of the gauge sector alone or the symmetry
sector alone need not resolve. There is no third observation field: in this model, “heralding” refers to the
additional full-irrep information \(R_v\) beyond \(m_v\).

### When does \(R_v\) determine \(m_v\)?

Suppose the active local leaves contain \(n_F\) fundamentals and \(n_{\bar F}\) antifundamentals. Every irrep in
their tensor product has \(N\)-ality

\[
\nu(R_v)=n_F-n_{\bar F}\pmod N,
\]

whereas the binary boundary syndrome is

\[
m_v=n_F+n_{\bar F}\pmod2.
\]

Subtraction and addition agree modulo two. If \(N\) is even, changing an integer representative of
\(\nu\in\mathbb Z_N\) by \(N\) preserves parity. Therefore, for an exact full-irrep readout and leaves restricted
to \(F,\bar F\),

\[
m_v=\nu(R_v)\pmod2
\]

is well defined. This includes \(\mathrm{SU}(2)\): integer versus half-integer spin is the corresponding
\(\mathbb Z_2\) grading.

For odd \(N\), reduction of \(N\)-ality modulo two is not well defined because adding \(N\) flips parity. The
\(\mathrm{SU}(3)\) singlet is an explicit counterexample:

\[
\mathbf1\subset 3^{\otimes0}.
\]

and

\[
\mathbf1\subset 3^{\otimes3}.
\]

The same exact irrep can therefore arise from an even or odd number of fundamentals. A useful local criterion is

\[
\mathcal P_v(R)=
\left\{|L|\bmod2:\ L\text{ is allowed at }v,\ M_L^R>0\right\}.
\]

\(R_v\) determines \(m_v\) at that vertex exactly when every allowed \(\mathcal P_v(R)\) is a singleton. The
degree-two \(\mathrm{SU}(3)\) ring oracle happens to satisfy this restricted criterion, but a general
\(\mathrm{SU}(3)\) lattice need not. Keeping \(m_v\) explicitly therefore preserves the general gauge-sector
label and the hard-decoder interface instead of relying on an accidental property of one fixture.

## Generative model

Let every oriented edge \(a=(u\to v)\) carry an independent error bit \(e_a\in\{0,1\}\):

\[
P(e)=\prod_{a\in E}p_a^{e_a}(1-p_a)^{1-e_a}.
\]

An active edge deposits an antifundamental \(\bar F\) at its tail and a fundamental \(F\) at its head. The active
leaf list at vertex \(v\) is

\[
L_v(e)=
\bigl(
\{F:a=(u\to v),e_a=1\},
\{\bar F:a=(v\to w),e_a=1\}
\bigr).
\]

Its representation space decomposes as

\[
\bigotimes_{\ell\in L_v(e)}V_\ell
\cong
\bigoplus_{R\in\widehat{SU(N)}}
V_R\otimes\mathbb C^{M^R_{L_v(e)}},
\]

where \(M_L^R\) is the fusion or Littlewood--Richardson multiplicity. For a maximally mixed state on the active
leaves and a projective measurement of the total irrep,

\[
P(R_v=R\mid L_v)=
\frac{M^R_{L_v}\dim R}{\prod_{\ell\in L_v}\dim\ell}.
\tag{1}
\]

This is normalized because tensor-product dimensions satisfy

\[
\prod_{\ell\in L}\dim\ell
=
\sum_R M_L^R\dim R.
\]

For example,

\[
F\otimes\bar F=\mathbf1\oplus\mathrm{Adj},
\]

so

\[
P(\mathbf1\mid F,\bar F)=\frac1{N^2}.
\]

The complementary outcome has probability

\[
P(\mathrm{Adj}\mid F,\bar F)=\frac{N^2-1}{N^2}.
\]

The degree-two \(\mathrm{SU}(3)\) implementation additionally uses

\[
3\otimes3=6\oplus\bar3.
\]

Its conjugate channel is

\[
\bar3\otimes\bar3=\bar6\oplus3.
\]

### Directed and undirected edge channels

The word **directed** describes the representation deposited by an active pair, not the incidence structure of
the matching graph. In the directed model above, the stored orientation of edge \(a=(u\to v)\) fixes
\(\bar F\) at \(u\) and \(F\) at \(v\).

The optional **undirected edge channel** removes that physical preference. Introduce a ternary latent edge
state

\[
x_a\in\{0,\rightarrow,\leftarrow\}.
\]

Its prior is

\[
P(x_a=0)=1-p_a.
\]

The two active orientations have equal probability:

\[
P(x_a=\rightarrow)=P(x_a=\leftarrow)=\frac{p_a}{2}.
\]

The state \(\rightarrow\) uses the stored \(\bar F\)-to-\(F\) assignment, while \(\leftarrow\) reverses it. The
binary topological error and syndrome depend only on activity,

\[
e_a=\mathbf1\{x_a\ne0\}.
\]

The irrep likelihood still distinguishes the two orientations whenever \(F\not\cong\bar F\). Sum-product BP
therefore carries three states internally and marginalizes the unobserved orientation. Its activity belief is

\[
r_a=b_a(\rightarrow)+b_a(\leftarrow).
\]

The weight passed to binary matching is then

\[
\widehat w_a=
\log\frac{b_a(0)}{b_a(\rightarrow)+b_a(\leftarrow)}.
\]

For \(\mathrm{SU}(2)\), the fundamental is pseudoreal, so reversing \(F\) and \(\bar F\) does not create a new
local representation channel. For U(1) and \(\mathrm{SU}(3)\), the latent orientation can change the observed
charge or irrep and must be summed out. The stored arrow remains only a computational reference label; the
decoder never observes it. See the [ternary likelihood and inference implementation,
`undirected_potential_bank`](../../labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py) and its
[deterministic hidden-orientation test](../../labs/lab-006-sun-bp-theory/scripts/test_artifact_backend.py).

## Local likelihood and posterior

Let

\[
\mu_v(e)=|L_v(e)|\bmod2.
\]

With the current perfect binary readout, the local factor is

\[
\psi_v(e_{\partial v};m_v,R_v)
=
\mathbf1\{m_v=\mu_v(e)\}
\frac{M^{R_v}_{L_v(e)}\dim R_v}
{\prod_{\ell\in L_v(e)}\dim\ell}.
\tag{2}
\]

Equation (2) conditions directly on the observed full irrep \(R_v\). It neither replaces \(R_v\) with a binary
partition nor sums over \(R_v\) as a hidden variable. Assuming conditionally independent local instruments,

\[
P(m,R\mid e)=\prod_v\psi_v(e_{\partial v};m_v,R_v).
\]

Bayes' rule gives

\[
P(e\mid m,R)=\frac{W(e;m,R)}{Z(m,R)},
\]

with

\[
W(e;m,R)=
\left[\prod_a p_a^{e_a}(1-p_a)^{1-e_a}\right]
\left[\prod_v\psi_v(e_{\partial v};m_v,R_v)\right],
\]

and \(Z(m,R)=\sum_{e'}W(e';m,R)\). The desired soft edge probability is

\[
r_a=P(e_a=1\mid m,R).
\]

## Sum-product BP

Construct a factor graph with an edge-error variable node for every \(a\) and a likelihood factor for every
vertex \(v\). Messages are normalized functions on \(x\in\{0,1\}\).

The variable-to-factor update is

\[
m_{a\to v}(x)\propto
p_a^x(1-p_a)^{1-x}
\prod_{w\in\partial a\setminus v}m_{w\to a}(x).
\tag{3}
\]

The factor-to-variable update is

\[
m_{v\to a}(x)\propto
\sum_{e_{\partial v\setminus a}}
\psi_v(x,e_{\partial v\setminus a};m_v,R_v)
\prod_{b\in\partial v\setminus a}m_{b\to v}(e_b).
\tag{4}
\]

The edge belief is

\[
b_a(x)\propto
p_a^x(1-p_a)^{1-x}
\prod_{v\in\partial a}m_{v\to a}(x).
\tag{5}
\]

### Damping and convergence convention

On a loopy graph, the implementation damps each newly computed factor-to-variable message before
renormalization. If \(\widetilde m_{v\to a}^{(t+1)}\) is the fresh sum-product update, the stored message is

\[
m_{v\to a}^{(t+1)}=
\lambda m_{v\to a}^{(t)}+
(1-\lambda)\widetilde m_{v\to a}^{(t+1)}.
\]

Thus \(\lambda\) is the **retained-old-message fraction**: \(\lambda=0\) is undamped BP, and larger \(\lambda\)
moves more conservatively. Variable-to-factor messages are then recomputed from the damped factor messages;
they are not independently damped. For \(0\leq\lambda<1\), damping does not change the fixed-point equation,
but it can change whether the iteration reaches a fixed point, how quickly it does so, and which fixed point is
selected on a loopy graph.

The convergence diagnostic is the maximum absolute change over all factor and variable messages after a full
synchronous sweep. The registered two-dimensional scan used \(\lambda=0.25\), tolerance \(10^{-10}\), and an
80-iteration cap. The current explanatory artifact defaults to \(\lambda=0.50\), permits values from 0 to 0.90,
and uses a 300-iteration cap. Those are algorithmic controls, not physical noise parameters. See the
[damped kernels](../../labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py) and the
[artifact control boundary](../../labs/lab-006-sun-bp-theory/scripts/artifact_backend.py).

### Exactness on a factor tree

Remove one variable--factor connection \((a,v)\) from a factor tree. The graph separates into two components.
By induction from the leaves, the message from either component is exactly its partial partition function with
\(e_a=x\) fixed. The two components are conditionally independent given \(e_a\); multiplying their messages and
the edge prior, then normalizing, performs the sum over all variables except \(e_a\). Hence (5) equals the exact
\(P(e_a=x\mid m,R)\).

On a graph with cycles, this separation argument fails. A converged loopy-BP solution obeys the stationary
equations of the Bethe approximation, not generally the exact global marginalization. The four-edge plaquette
fixture intentionally records this difference.

## From a BP fixed point to the edge log-likelihood ratio

The relation used by the matching back end follows from the normalized belief, not from an additional
assumption. Write the Bernoulli prior as

\[
\pi_a(x)=p_a^x(1-p_a)^{1-x}.
\]

The normalized version of (5) is

\[
b_a(x)=
\frac{\pi_a(x)\prod_{v\in\partial a}m_{v\to a}(x)}
{\sum_{y\in\{0,1\}}\pi_a(y)\prod_{v\in\partial a}m_{v\to a}(y)}.
\tag{6}
\]

Assume first that the messages are positive. Taking the ratio of (6) at \(x=0\) and \(x=1\) cancels the same
normalization denominator and gives

\[
\frac{b_a(0)}{b_a(1)}=
\frac{1-p_a}{p_a}
\prod_{v\in\partial a}
\frac{m_{v\to a}(0)}{m_{v\to a}(1)}.
\tag{7}
\]

Taking logarithms turns the product into a sum:

\[
\widehat w_a=
\log\frac{1-p_a}{p_a}
+\sum_{v\in\partial a}
\log\frac{m_{v\to a}(0)}{m_{v\to a}(1)}.
\tag{8}
\]

Because \(b_a(0)+b_a(1)=1\), defining \(r_a=b_a(1)\) yields the exact identity

\[
\widehat w_a=
\log\frac{b_a(0)}{b_a(1)}
=\log\frac{1-r_a}{r_a}.
\tag{9}
\]

Zero messages give the same statement in the extended reals by continuity: a zero numerator or denominator
produces \(-\infty\) or \(+\infty\). In code, clipping merely replaces these hard infinities by finite numerical
bounds.

Equation (9) is algebraic and is true for any normalized BP belief. At a loopy fixed point it is the **Bethe
edge-belief LLR**. On a factor tree, the preceding theorem gives
\(b_a(x)=P(e_a=x\mid m,R)\), so (9) strengthens to the exact posterior statement

\[
\widehat w_a=
\log\frac{P(e_a=0\mid m,R)}{P(e_a=1\mid m,R)}.
\tag{10}
\]

Thus convergence alone proves (9), but only tree exactness proves (10). A probability \(b_a(1)\) is not itself
a log-likelihood ratio; it determines the LLR through its log-odds.

## Why the edge LLR is the matching weight

Belief matching forms the explicit independent-edge surrogate

\[
\widetilde P_{\mathrm{BP}}(c\mid m,R)
\propto
\prod_a b_a(c_a)
\mathbf1\{Ac=m\}.
\tag{11}
\]

For any feasible correction \(c\) satisfying \(Ac=m\), its negative log probability is

\[
-\log\widetilde P_{\mathrm{BP}}(c\mid m,R)
=C+\sum_a c_a\widehat w_a,
\tag{12}
\]

where \(C=-\sum_a\log(1-r_a)\) does not depend on \(c\). Therefore maximizing (11) over feasible chains is
exactly equivalent to minimizing \(\sum_a c_a\widehat w_a\). For a graphlike parity-check matrix, PyMatching
solves this minimum-weight chain problem, so the quantity passed through to it is exactly the LLR in (9), not
the raw probability.

This last equivalence is exact for the surrogate (11). It does **not** prove that the product of edge beliefs is
the true joint posterior: even exact tree marginals can remain mutually correlated after conditioning. Hence the
belief-matching correction is a posterior-marginal-weighted matching reduction, not in general the global MAP
decoder for the original fusion factor graph. The hard backend also fails closed when \(m\) is noisy, because
that setting requires a spacetime matching construction.

## Sum-product versus min-sum

The standard probabilistic algorithm here is **sum-product** BP (sometimes informally reversed to
“product-sum”). Equations (3)--(5) sum over compatible local configurations and multiply likelihoods and
incoming messages. Its output \(b_a\) is a normalized belief; on a factor tree it is the exact posterior
marginal, and on a loopy graph it is a Bethe belief.

The implementation also contains a **min-sum** or min-marginal mode. Define the local energy

\[
E_v(x_{\partial v})=-\log\psi_v(x_{\partial v};m_v,R_v).
\]

A zero likelihood has infinite energy. The factor update replaces the sum of products by a minimum of additive
costs:

\[
M_{v\to a}(x_a)=
\min_{x_{\partial v\setminus a}}
\left[
E_v(x_{\partial v})+
\sum_{b\in\partial v\setminus a}M_{b\to v}(x_b)
\right].
\]

Messages are defined only up to an additive constant, so the implementation subtracts the smallest state cost
after every update. Damping uses the same retained-old-message convention, but now interpolates these relative
cost messages rather than probabilities.

Let \(C_a(0)\) and \(C_a(1)\) be the final directed-edge min-marginal costs. The additive matching weight is

\[
\widehat w_a^{\min}=C_a(1)-C_a(0).
\]

For the ternary undirected channel, the active cost is

\[
C_a(\mathrm{on})=min\{C_a(\rightarrow),C_a(\leftarrow)\}.
\]

The corresponding weight is \(C_a(\mathrm{on})-C_a(0)\). The code maps this gap through a logistic function only
to reuse the existing belief-matching interface. That number is **not a calibrated posterior probability**:
min-sum chooses the best orientation/configuration instead of summing their probability mass. On a factor tree,
min-sum gives exact min-marginals for the MAP objective; on a loopy lattice it is another approximation.

Consequently the posterior-LLR proof in equations (6)--(10) applies to sum-product, not to min-sum. No registered
matched study yet establishes whether min-sum is more accurate, more stable, or better for logical decoding in
this model. The current web workbench exposes sum-product; the min-sum backend is an implementation capability
awaiting a separately verified UI and scientific comparison. See [`_infer_min_sum_inplace`](../../labs/lab-006-sun-bp-theory/scripts/numba_fusion_decoder.py).

## Measuring the heralding effect of \(R\)

The clean comparison holds the physical error, \(m\), geometry, prior, BP schedule, and hard decoder fixed. It
evaluates two beliefs on the same record. Define the error log-likelihood ratio

\[
\ell_a(s)=
\log\frac{P(e_a=1\mid s)}{P(e_a=0\mid s)}.
\]

For sum-product BP on a loopy graph, \(P\) in this definition denotes the corresponding normalized Bethe edge
belief. On a factor tree, it is the exact posterior marginal. The representation-resolved heralding effect is

\[
\Delta\ell_a=
\ell_a(m,R)-\ell_a(m).
\]

Equivalently,

\[
\Delta\ell_a=
\log
\frac{P(e_a=1\mid m,R)P(e_a=0\mid m)}
{P(e_a=0\mid m,R)P(e_a=1\mid m)}.
\tag{13}
\]

Thus \(\Delta\ell_a\) is the log Bayes factor contributed by \(R\) to the binary comparison “error versus no
error.” Its multiplicative form is the posterior-odds ratio

\[
\exp(\Delta\ell_a)=
\frac{\operatorname{odds}(e_a=1\mid m,R)}
{\operatorname{odds}(e_a=1\mid m)}.
\]

This is the natural evidence coordinate: independent likelihood factors multiply odds, so their logarithms add.
A raw probability difference depends on the baseline probability and is not used as the heralding-strength
metric. With the matching convention \(\widehat w_a=\log[P(e_a=0)/P(e_a=1)]\), the same quantity is

\[
\Delta\ell_a=
\widehat w_a^{(m)}-
\widehat w_a^{(m,R)}.
\]

Positive \(\Delta\ell_a\) means \(R\) raises the error odds; negative \(\Delta\ell_a\) means it lowers them. The
paired construction attributes the change specifically to \(R\), rather than to a changed physical sample,
prior, schedule, or decoder convention.

The [interactive full-irrep workbench](/lab?id=lab-006-sun-bp-theory)
shows four layers: the measured \((m,R)\) record, \(P(e\mid m,R)\), the signed error-LLR shift, and the final
syndrome-faithful correction. Red edges have \(\Delta\ell_a>0\), blue edges have \(\Delta\ell_a<0\), and line
width encodes \(|\Delta\ell_a|\) relative to the largest shift in the displayed sample.

## Numerical implementation

The executable implementation has two independently checkable paths:

1. `sun_fusion_bp.py` builds the exact degree-two \(\mathrm{SU}(3)\) local factors, enumerates all \(2^{|E|}\) error
   configurations on small graphs, and implements a readable Python BP recurrence.
2. `numba_fusion_decoder.py` precomputes a dense potential bank indexed only by
   \((v,m_v,R_v,e_{\partial v})\), caches graph topology, reuses message buffers, and supplies scalar and batched
   Numba kernels. The same class can disable the irrep factor to produce the paired \(m\)-only baseline; this does
   not create a different physical sample.

The public workbench uses the canonical Lab 002 square and honeycomb constructors, with open rough left/right
boundaries and smooth transverse boundaries. Its U(1), SU(2), and SU(3) local product distributions cover all
degrees through four exercised by those lattices. A fixed seed provides an explanatory example, not a
performance estimate. The ring is used only by the small-graph exactness and throughput checks.

## Numerical justification

- On the registered path factor tree, BP and exact enumeration agree to numerical precision.
- On the registered plaquette, the stored comparison shows the expected loopy-BP/exact discrepancy rather than
  promoting a false exactness claim.
- On 256 fixed-seed observations of a warmed 64-site \(\mathrm{SU}(3)\) ring, the reference and Numba marginals agree to
  \(1.88\times10^{-37}\) maximum absolute difference; convergence flags and iteration counts agree for all 256
  observations.
- All 16 registered hard-decoding checks reproduce the supplied \(m\) syndrome.
- The measured medians are 144.1804 ms per observation for Python, 0.1739 ms for scalar Numba, and 0.0922 ms for
  batched Numba. These are implementation-throughput measurements for degree-two \(\mathrm{SU}(3)\), not a threshold or
  general-\(\mathrm{SU}(N)\) scaling claim.

### Two-dimensional convergence diagnostic

The preregistered A5b scan deliberately probed the loopy square and honeycomb geometries instead of assuming
that the ring behavior transfers. It evaluated 128 observations on \(L=5,7\), groups SU(2)/SU(3), and
\(p=0.1,0.2,0.3,0.4\), with four independent seeds per cell. The paired full-\((m,R)\) and \(m\)-only arms used
identical records and a frozen synchronous schedule with damping 0.25, 80 iterations, and tolerance
\(10^{-10}\).

Full-\((m,R)\) BP converged in 106/128 observations, and the \(m\)-only arm in 102/128. The failures were
structured rather than negligible:

- square full-record inference converged in 59/64 observations, compared with 47/64 on honeycomb;
- SU(3) full-record inference converged in 62/64, compared with 44/64 for SU(2);
- for \(L=7\) honeycomb SU(2), the full-record arm converged in 0/4 observations at each of
  \(p=0.2,0.3,0.4\); at \(p=0.2\), its largest residual was \(8.43\times10^{-4}\).

These counts diagnose one fixed BP schedule. Four samples per cell are far too few for a phase boundary, and no
logical-error score was part of the scan. They establish neither that SU(3) is generally easier nor that one
observation arm is generally more stable. They do show that the degree-two ring hid material two-dimensional
failure modes and identify larger honeycomb SU(2) instances as a concrete next convergence target.

See the [Lab 006 report](../../labs/lab-006-sun-bp-theory/REPORT.md),
[small-graph evidence](../../labs/lab-006-sun-bp-theory/results/small-graph-exact-vs-bp.json),
[accelerated-decoder evidence](../../labs/lab-006-sun-bp-theory/results/a1-numba-belief-matching.json), and
[two-dimensional convergence evidence](../../labs/lab-006-sun-bp-theory/results/a5b-two-dimensional-convergence-scan.json).

## Limits

- The compiled fusion tables cover U(1), SU(2), and SU(3) product distributions through local degree four. A
  general arbitrary-degree SU(N) implementation still needs an audited Littlewood--Richardson or
  model-specific fusion backend.
- Equation (1) assumes a maximally mixed local state and a projective total-irrep measurement. A different
  preparation or detector requires a newly registered likelihood.
- A Lie-group tensor-product decomposition is not automatically the level-truncated fusion algebra of an
  \(\mathrm{SU}(N)_k\) anyon theory.
- The current hard matching stage assumes a perfect static \(m\) record. Measurement errors require a spacetime
  decoder.
- The fixed-size demonstrations establish small-graph correctness, a visible information effect, and a
  schedule-specific convergence boundary, not a decoding threshold.

## Exact sector model and the logical hardening gap

Lab 007 now derives the normalized observation-conditioned sector partition
function for this classical instrument, including unmeasured rough boundaries
and shared hidden orientations. Its SU(2) quotient holds for the entire joint
activity/record law, not only local beliefs. U(1) has an exact bounded-current
representation; full-record SU(3) generally requires extra source structure.
These reductions and their claim boundaries are synthesized in
[[models/representation-informed-sector-model|the logical-sector model]].

Exact marginals still need not make matching Bayes-optimal: a finite SU(2)
rough-hexagon record has sector probabilities (128/193,65/193), but the exact
marginal-weighted chain lies in the less probable sector. PyMatching reproduces
that witness. A deliberately small star also exposes merging of repeated
boundary columns, so the ideal surrogate equivalence assumes a graph encoding
that preserves the intended objective. The inspected canonical L=5,7,9,11
matrices have no such duplicate columns. These are finite mathematical and
implementation boundaries, not revised production LER estimates.
[Lab 007, decoder-gap evidence](../../labs/lab-007-decoding-statistical-mechanics/wiki/decoder-gap.md).

## Related pages

- [[concepts/lie-algebra-representations|Lie groups, Lie algebras, and representations]]
- [[concepts/symmetry-enriched-topological-order|Symmetry-enriched topological order]]
- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
