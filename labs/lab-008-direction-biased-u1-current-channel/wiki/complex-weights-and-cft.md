---
title: Complex weights, replica field theory and boundary CFT
status: current
updated: 2026-09-22
---

# Complex weights, replica field theory and boundary CFT

## Summary

**Theory reorientation, 2026-09-22:** further finite-size acquisition is stopped.
The [thermodynamic decoding program](thermodynamic-decoding-theory.md) specifies
competing asymptotic hypotheses, exact planted-gap and interface-gluing identities,
and the missing uniform estimate. Existing data constrain the questions; they
do not establish a continuum action, line tension or complex fixed point.

**Current priority: decoding transitions and correction thresholds.**
The [threshold analysis](decoding-thresholds.md) collects rigorous bounds
and proves the directed-midpoint residual-graph mapping. Critical percolation
keeps ambiguous records present, but a posterior-balance bound is still needed
to prove nonzero LER. The CFT route below remains a supporting possibility.

**Thermodynamic result, 2026-09-20:** the
[new infinite-size proofs](thermodynamic-limits.md) establish an open all-p
correctable honeycomb bias interval q>.9925857155 (and its reflected interval),
with exponential optimal-LER decay at fixed bias. They also separate an
averaged bulk free-energy-density limit from the logical sector-gap criterion.
These results do not identify a physical CFT or a square critical point.

**Directional crossover:** the [new sector calculation](directional-crossover.md)
derives the exact low-noise exponent along 1-q=lambda p^alpha. On a square
with d=L-1, the directed boundary layer is 1-q of order p^(d-1), with a
computed leading coefficient. This is a result for the physical sector
minimum, without a Gaussian or replica assumption. The full moderate-p
square curve remains open.

**Fixed-p reverse response:** the
[normalized joint-law expansion](reverse-sector-response.md) retains every
zero- and single-reverse configuration before taking the record-sector
minimum. Its exact LER error is bounded by
$Ep\epsilon[1-(1-p\epsilon)^{E-1}]\leq
E(E-1)p^2\epsilon^2$, with $\epsilon=1-q$. Fifteen exact L3 controls pass,
including newly accessible records and sector switches. This theorem supplies
a controlled near-directed approximation but is not an evaluated L5 curve or
a CFT result.

**New calculation, 2026-09-19:** the
[connected-current theorem](connected-current-defects.md) now controls the
physical LER through a positive path partition bound. It gives an exact
small-square LER polynomial, improved biased square certificates and an
all-p correctability theorem for fully directional honeycomb noise. This
uses the rigorous honeycomb self-avoiding-walk growth constant, whose proof
has a parafermionic observable. It does not identify the original model's
CFT. The Gaussian calculation below remains conditional and its bare-stiffness
calibration remains rejected.

The proposed route from a statistical model to boundary partition ratios
and LER is viable as a research program. There is now an exact lattice
observable to carry into field theory: the physical moments of the logical
twist, with a specified replica limit. The closest literature uses disorder
averages, replica twists and boundary conformal theory. Complex CFT is a
possible later identification, not a consequence of a complex edge weight.

This review distinguishes proved results for our ternary-current channel,
known results in other models, and conditional continuum predictions.
The [replica derivation](replica-boundary-ratios.md) supplies the new exact
results and their independent finite checks.

## Evidence

### Which statistical model answers the original question?

The exact model is a bounded integer-current ensemble conditioned on the
measured charges, equivalently a constrained relative-height model. Its
complex rotor integral is another exact representation. The positive
self-avoiding-path model used below is a bound on its logical ambiguity;
the compact Gaussian replica theory is a conditional continuum candidate.
These four objects have different logical roles.

For 0<p<1 and 0<q<1, set

\[
\tau=\log\frac{1-p}{p\sqrt{q(1-q)}},\qquad
h=\frac12\log\frac{q}{1-q}.
\]

The single-link potential, with temperature absorbed into its definition, is

\[
V(j)=\begin{cases}\tau|j|-hj,&j\in\{-1,0,1\},\\
+\infty,&\text{otherwise}.\end{cases}
\]

Then w(j)=(1-p) exp[-V(j)] exactly, and the two logical partition sums are

\[
Z_s(Q)=(1-p)^E
\sum_{\substack{D_Mj=Q\\\ell(j-j_0)=s\ ({\rm mod}\ 2)}}
\exp\!\left[-\sum_e V(j_e)\right].
\]

Thus the current Hamiltonian is real, with a hard support and divergence
constraint. Bias acts as a real signed-current field h, and also changes
the activity cost tau at fixed p. At q=1 use the supported values 0,1 with
V(1)=log[(1-p)/p] and V(-1)=infinity; the separate tau,h limits are singular.

The [Lab 007 integral-cycle construction](../../lab-007-decoding-statistical-mechanics/wiki/statistical-model.md)
gives an integer basis C of ker_Z(D_M), including rough-boundary paths.
Every compatible current has a unique form j=j_0+C n. Consequently the
height/current action is exactly sum_e V(j_0,e+(C n)_e). Contractible planar
cycles give local dual height differences; the boundary generators must
remain to represent logical errors. The offsets j_0 depend on the fixed
observed record. They are quenched within each partition sum and are not an
independently chosen random-bond distribution. This is a constrained integer
height model, not the quadratic height action of a free boson.

For F_s=-log Z_s and Delta F=F_1-F_0, the physical observable is

\[
\mathrm{LER}_*=\mathbb E_{Q\sim P}\frac{1}{1+e^{|\Delta F(Q)|}},
\qquad P(Q)=Z_0(Q)+Z_1(Q).
\]

Small absolute sector gaps produce ambiguous records. A bulk free energy,
the Q=0 partition function, or the mean gap does not determine this average.
The [sector calculation](sector-predictions.md) also gives the exact additional
loss when the practical decoder selects the less probable sector.

The [controlled current expansion](partition-function-ler.md) explains the
low-noise square curves: for d=L-1, fixed bidirectional 0<q<1 gives order
p^ceil(d/2), whereas the directed endpoint gives order p^d. At L=5 the fair
and directed leading terms are 7.5 p^2 and 70 p^4. These are fixed-size,
low-p results; the q->1 limit of the first leading term is not a uniform
approximation. The [connected-current calculation](connected-current-defects.md)
adds the untruncated L3 directed polynomial on p<=.2, finite positive path
and overlap bounds, and an all-p directed-honeycomb correctability theorem.
The general moderate-noise square curve remains unsolved.

This is the current answer to the original research goal: an exact model and
an exact LER functional, with several solved regimes and rigorous bounds.
It is not yet an identified integrable two-dimensional model or physical CFT.

### What does the complex weight mean here?

Our local factor is K(phi)=1-p+pq exp(i phi)+p(1-q) exp(-i phi).
It is a Fourier polynomial of a positive current prior, not exp(J cos phi).
Writing H=-sum log K introduces a complex, generally multiharmonic interaction
with possible zeros and logarithm branches. It does not turn the current
probability law into a nonunitary physical quantum channel.

There is a useful exact diagnostic. For the isolated convolution operator

\[
(Tf)(\theta)=\int\frac{d\theta'}{2\pi}
 K(\theta'-\theta)f(\theta'),
\]

K(-phi)=K(phi)* makes T Hermitian. Its Fourier eigenvalues are 1-p,pq,p(1-q)
on the three allowed modes and zero otherwise; T is positive semidefinite.
This fact alone does **not** establish reflection positivity or unitarity of
the full two-dimensional source-conditioned model. It does establish that
complex entries by themselves are insufficient evidence of nonunitarity.

Three different notions must be kept distinct:

| Notion | Meaning | Present status |
| --- | --- | --- |
| Complex Boltzmann representation | Individual angular factors or source insertions are complex. | Exact for this model. |
| Nonunitary continuum theory | Positivity of the CFT state space fails; scaling data can still be real. | Possible after the disorder/replica limit; unproved here. |
| Complex CFT | A fixed point with intrinsically complex conformal data, usually with a distinct conjugate partner. | No identification here. |

Gorbenko, Rychkov and Zan distinguish real nonunitary theories from complex
ones; even complex-conjugate dimensions alone need not identify a complex
CFT. Their controlled Q>4 Potts example relates conjugate fixed points to
walking and a weak first-order transition on the real parameter axis.
Thus a complex fixed point need not be a continuous transition at real p.
[General framework](https://arxiv.org/abs/1807.11512),
[Potts construction](https://arxiv.org/abs/1808.04380).

Yang–Lee is a concrete exactly identified nonunitary CFT example, with
c=-22/5 and h=-1/5. Its imaginary-field singularity is a different tuning
problem from our positive physical-current inference problem. There is no
derived map transferring that spectrum to this channel.
[Cardy's Yang–Lee identification](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.54.1354).

### Methods in the primary literature and what transfers

| Source | Relevant method or result | Applicability here |
| --- | --- | --- |
| [Aarts–James, 2010](https://arxiv.org/abs/1005.3468) | Finite-chemical-potential XY: comparison of complex Langevin with a worldline formulation reveals incorrect Langevin convergence in part of the phase diagram. | Our exact positive-current representation is the natural benchmark; complex sampling is not necessary just because K is complex. Their 3D XY phase diagram does not transfer. |
| [Merz–Chalker, 2002](https://arxiv.org/abs/cond-mat/0201137) | Disorder-operator partition ratios at the Nishimori point have a nontrivial moment spectrum and conformal scaling. | Supports calculating physical moments of ratios. A mean ratio or a mean free-energy difference can miss the distribution required for LER. Their RBIM exponents are not our exponents. |
| [Yang–Sun–Jian, 2025](https://arxiv.org/abs/2512.19523) | Boundary criticality at the Nishimori point: distinct boundary conditions and boundary-changing operators studied using tensor networks and replica field theory. | A close precedent for boundary-sensitive decoding observables; not a solved U(1) boundary theory. |
| [Temkin et al., 2025, Appendix SIV](https://arxiv.org/abs/2512.22119) | Charge-informed inference: compact-boson theory with an imaginary random-gradient coupling, replicas, independent twists and vortex corrections. | Closest U(1) precedent. Their unbounded discrete-Gaussian currents, periodic geometry and integer winding differ from our ternary prior, rough boundaries and binary parity. |
| [Cardy, boundary CFT](https://arxiv.org/abs/hep-th/0411189) | Boundary states and characters compute partition functions with specified conformal boundaries. | Gives a route to the desired ratio once the continuum theory and logical-twist boundary operator are identified. |

In particular, the charge-informed paper obtains a quadratic replicated
action with both diagonal and inter-replica gradient couplings and keeps
vortices to discuss its transition. Its independently marked twists are a
useful methodological precedent. Neither its stiffness jump nor its
critical microscopic noise parameter can be imported without a new mapping.

### The exact lattice object for our field theory

The physical second moment is

\[
M_2=\sum_Q\frac{A_1(Q)^2}{A_0(Q)}
=\lim_{R\to1}\frac{\mathcal Z_R^{(2)}}{\mathcal Z_R^{(0)}}.
\]

The integer-R replicated edge weight is

\[
W_R=\prod_{a=1}^{R}K(\phi_a),\qquad
\sum_{a=1}^{R}\phi_a=0\pmod{2\pi},
\]

with two marked cut twists in the numerator. The exact inequalities
(1-M2)/4 <= LER* <= (1-M2)/2 connect this boundary observable to correctability.
Higher even moments reconstruct LER with a known truncation bound.
This is an explicit target for a continuum theory, not a choice of a CFT
based solely on the visual form of K.

At R=2 the weight is |K|^2, a real generalized rotor model with first and
second harmonics. This solvable reduction is annealed in the syndrome law:
it uses P(Q)^2. The physical problem uses P(Q), hence requires R->1. A clean
XY analysis at R=2 can be a control but cannot settle the physical threshold.

### What a spin-wave expansion does and does not establish

The cumulant expansion about zero phase gives

\[
\log K(\phi)=i\mu\phi-\frac{v_0}{2}\phi^2+O(\phi^3),
\qquad \mu=p(2q-1),\quad v_0=p-\mu^2.
\]

On the smooth replica branch sum phi_a=0, the imaginary linear terms cancel.
The bare quadratic action is therefore

\[
S_R^{\rm quad}=\frac{v_0}{2}\sum_e\sum_{a=1}^{R}(\phi_e^a)^2.
\]

In R-1 independent fields its metric is I+11^T. This shows how a real
Gaussian sector can emerge from complex single-copy weights. It is a local
expansion, not a controlled approximation throughout the physical p range.
In particular, small p does not concentrate all angles near zero.

Compactness, winding sectors, vortex fugacity, higher cumulants and the
replica continuation remain essential. A pi logical twist is finite, so a
noncompact small-twist expansion cannot replace its winding sum. Effective
stiffness is renormalized and cannot simply be set to v0 at a putative
transition. Bias can survive in higher cumulants and defect weights even
though its linear term cancels. There is no derived BKT or Gaussian critical
description of the present channel yet.

### Compactification and the elementary vortex

For integer R>=2 the exact compact target of the constrained replica angles
is the hyperplane sum theta_a=0, modulo the lattice 2pi Lambda_R, where

\[
\Lambda_R=\{\boldsymbol n\in\mathbb Z^R:\sum_a n_a=0\}.
\]

This is the A_(R-1) root lattice. A vortex has winding n in Lambda_R. In a
stipulated Gaussian action with renormalized coefficient kappa multiplying
sum_a (grad theta_a)^2/2, its logarithmic energy is
pi kappa |n|^2 log(r/a), and its scaling dimension is pi kappa |n|^2.
The shortest windings are e_a-e_b, of squared length two. Their formal
marginality condition is therefore 2pi kappa=2, or kappa=1/pi.

The charge lattice is exact for integer replicas. The scaling dimension is
conditional on a Gaussian fixed point. The marginality condition is **not**
an established transition of the physical R->1 model: there are R(R-1)
elementary roots, the continuation is nontrivial, and core fugacities and
their RG flows have not been controlled. It gives a concrete candidate
calculation to test, rather than a critical noise value.

### An explicit conditional boundary-ratio calculation

To make the CFT route concrete, suppose an independently justified long-distance
sector is a compact free boson with action

\[
S=\frac{\kappa}{2}\int d^2x\,(\nabla\theta)^2,\qquad\theta\sim\theta+2\pi.
\]

Take an annulus of width W and periodic length H, with Dirichlet angles
zero and alpha on the two boundaries; rho=H/W in isotropic coordinates.
This is an illustrative control geometry, not the actual open square.
Write theta=(alpha+2pi n)x/W plus a fluctuation with homogeneous boundaries.
The cross term vanishes and the fluctuation determinants cancel in the ratio:

\[
\frac{Z_\alpha}{Z_0}
=\frac{\sum_{n\in\mathbb Z}e^{-\kappa\rho(\alpha+2\pi n)^2/2}}
 {\sum_{n\in\mathbb Z}e^{-\kappa\rho(2\pi n)^2/2}}.
\]

For alpha=pi this is theta_2(0,z)/theta_3(0,z), z=exp(-2pi^2 kappa rho).
It is an exact partition ratio within the stipulated Gaussian continuum
theory. It must be embedded into the correct marked replica theory before
being interpreted as a physical M2 or LER. A clean single-boson ratio alone
is neither of these observables.

### Solving a candidate Gaussian replica annulus

One can go further than a single boson. Stipulate the constrained Gaussian
replica action above on the annulus and set A=2pi^2 kappa rho. Untwisted
classical windings lie in Lambda_R. A pi twist on 2k marked copies shifts
those components by one half; the constraint on the integer lifts is then
sum n_a=-k. Define

\[
F_A(x)=\sum_{n\in\mathbb Z}e^{-A n^2}e^{inx},\qquad
G_A(x)=\sum_{n\in\mathbb Z}e^{-A(n+1/2)^2}e^{i(n+1/2)x}.
\]

Fourier projection of the lift constraint gives the Gaussian ratio

\[
\mathcal G_R^{(2k)}=
\frac{\int_{-\pi}^{\pi}\!\frac{dx}{2\pi}\,G_A(x)^{2k}F_A(x)^{R-2k}}
 {\int_{-\pi}^{\pi}\!\frac{dx}{2\pi}\,F_A(x)^R}.
\]

The oscillator determinant is independent of the boundary shift and cancels.
Poisson summation writes F as a sum of positive Gaussians centered at 2pi n;
G is the same sum with alternating signs. Thus F>0 and |G|<=F. This integral
defines a particular explicit continuation to real R near one, yielding

\[
M_{2k}^{\rm G}=\int_{-\pi}^{\pi}\frac{dx}{2\pi}
 F_A(x)\left[\frac{G_A(x)}{F_A(x)}\right]^{2k}.
\]

Since integral F=1, this is a normalized moment hierarchy. The same LER
functional then has the closed form

\[
\mathcal R_{\rm G}(A)
=\frac12-\frac2\pi\sum_{n=0}^{\infty}
 \frac{(-1)^n}{2n+1}e^{-A(n+1/2)^2}.
\]

To obtain it, use G>=0 for -pi<=x<=pi (the theta_2 product formula, or the
positive Dirichlet heat kernel) and integrate its cosine series. It tends
to zero as A tends to zero and to one half as A tends to infinity. The series
is rapidly convergent at moderate A.

Combining this **candidate** with the root marginality value kappa=1/pi and
rho=1 gives A=2pi and a conditional annulus LER about 0.36766. This number
belongs to the stipulated Gaussian replica annulus with the stated
continuation. It is not a prediction yet for the Lab 006 open square, its
critical LER, or its p_c. Both the continuum approximation and its replica
continuation must be derived from the physical lattice limit before that
interpretation is valid. Non-Gaussian criticality would change the formula.

Independent checks at A=.2,1,2pi,10 compare constrained R=2,3,4 root sums
with these integrals, and the series with direct integration. They verify
the candidate calculation, not its applicability; see the
[theory check results](../results/replica-boundary-theory-2026-09-18.json).

### Continuum-control result: the bare calibration is rejected

The registered control investigation asked whether this conditional annulus
can be calibrated to the physical square without adding an unproved matching
step. It cannot. Three independent obstructions close that shortcut.

1. There is no demonstrated spin-wave endpoint. As p tends to zero,
   K(phi) tends exactly to one, so angles are flat rather than concentrated
   near phi=0. At q=1,p=1, K(phi)=exp(i phi) also has flat modulus. Thus the
   endpoints with exact physical behavior do not supply a small-angle
   parameter.
2. The bare curvature v0 is not the renormalized helicity modulus kappa.
   Setting kappa=v0 and rho=1 in the annulus formula disagrees with the exact
   L=3 open-square LER by .0185 to .1204 on the frozen p,q grid. Because the
   geometries differ, this is only a rejection of the naive substitution,
   not a continuum fit. More fundamentally, the exact ternary kernel provides
   no shown small vortex-core fugacity; at R>=3 the core weights can be complex
   and species-dependent, while R=2 uses the wrong annealed record law.
3. Integer-replica values do not fix the physical continuation. If C0(R) is
   any proposed continuation, then

   Cc(R)=C0(R)+c sin(pi(R-1))/(R-1)

   agrees with it at every admissible integer R>=2 but changes the removable
   R->1 limit by c*pi. The positive finite-lattice problem defines the desired
   continuation, but it must be carried through coarse graining; the integer
   root sums alone cannot choose it.

Therefore kappa=1/pi gives neither a physical p_c nor a critical LER here.
The Gaussian annulus remains a useful conditional benchmark, and this result
does not exclude a genuinely derived Gaussian infrared fixed point. The next
controlled analytic route is instead a direct positive-current defect/polymer
expansion with a certified omitted-weight remainder. See the
[machine-readable control result](../results/compact-replica-control-2026-09-18.json).

### General boundary CFT and the actual square geometry

More generally, with a diagonalizable identified BCFT, annulus amplitudes
are sums of boundary-sector characters. In open-strip normalization,

\[
Z_{ab}(\rho)=\sum_i n_{ab}^{i}\chi_i(e^{-\pi u\rho}),
\]
\[
-\log\lambda_i(W)=f_b W+f_s+
 \frac{\pi u}{W}(h_i-c/24)+o(W^{-1}).
\]

Here u accounts for lattice anisotropy; descendants are included among h_i.
Bulk and surface terms must be removed consistently. For a real nonunitary
spectrum whose leading weight is h_min, the ground-state correction measures
c_eff=c-24 h_min, not necessarily c. Ratios require the boundary spectrum
and amplitudes, not just a central charge. Replica limits may also produce
logarithmic structures, for which an ordinary diagonal character ansatz is
not automatically sufficient. These formulas specify diagnostics, not a
measured spectrum for this lab.

The actual rough square has open top and bottom edges and corners. Its
continuum partition function uses the appropriate boundary-state matrix
element or boundary-changing correlations, rather than an annulus trace.
One must match these boundaries before predicting a universal LER value.
Calling decoding a boundary question is compatible with this treatment:
the boundary ratio is governed by the bulk theory together with the
boundary conditions and their scaling operators.

### What could determine a critical point and a critical LER?

An identified replica fixed point and its marked-boundary partition ratios
would predict the moments M2k at fixed shape. Those moments give certified
LER intervals and, in the full hierarchy, the critical LER itself. The M2
criterion already fixes the same correctable region as Bayes decoding.

However, the location p_c(q) in the microscopic noise coordinates is not
fixed by universality data alone. It needs a lattice-to-continuum matching
calculation, a controlled RG separatrix, an exact duality/integrability
condition, or an independently validated critical tuning. If a complex CFT
pair instead governs walking, finite-size conformal-looking spectra may
precede a first-order transition. That possibility has to be distinguished
from a real-axis critical point; it cannot be presumed from complex K.

### Ordered research route and decision gates

1. **Completed:** derive the correct lattice twist, physical replica limit,
   exact bounds and solvable path; validate normalization independently.
2. **Completed with a negative decision:** the integer-replica compactification, elementary
   vortices and marked half-lattice boundary shift are now derived above.
   The Gaussian annulus candidate is evaluated with an explicit continuation,
   but its bare physical calibration is rejected for the reasons above.
3. **Controlled curve:** register a direct positive-current defect/polymer
   expansion with a certified omitted-weight remainder. Existing exact
   contraction is the validation reference. A continuum route may re-enter
   only after physical R->1 matching is derived.
4. **Conditional critical investigation:** only after a candidate continuum
   theory is specified, compare its twist spectrum and aspect-ratio dependence
   to lattice partition sums. A fit of the central charge alone is inadequate.
   Identify which prediction could reject the candidate before extending size.

These steps retain the researcher's main goal: explain LER from the model.
They do not require another BP decoder sweep or assume a phase transition.

## Status

Primary literature reviewed on 2026-09-18. Exact new lattice statements and
the long-path limit are derived and checked. The Gaussian replica annulus
formula and candidate marginality value remain conditional on the stated
continuum theory, continuation and geometry. Its naive bare calibration is
now rejected. No universality class, two-dimensional p_c(q), or numerical
critical LER has been obtained. The next calculation returns to a
positive-current expansion with an explicit remainder.

## Related pages

- [Replica boundary ratios and logical error](replica-boundary-ratios.md)
- [Auxiliary partition function and dilute limits](partition-function-ler.md)
- [Sector predictions](sector-predictions.md)
- [Research plan](../PLAN.md)
