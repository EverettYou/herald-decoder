# Methodology note — scaling claims for logical error rate

## Correction recorded on 2026-08-28

The Lab previously used

\[
\operatorname{logit} P_{\rm L}(L;p,q)=\alpha(p,q)+\beta(p,q)\log L
\]

and interpreted the sign of \(\beta\) as a phase label. This was not derived
from the code, noise model, or decoder. It was an unjustified model choice and
is withdrawn from active phase inference.

The hidden assumption is exact:

\[
\frac{P_{\rm L}}{1-P_{\rm L}}=e^\alpha L^\beta.
\]

Thus the fit assumes that the logical-error *odds* are a power law in linear
size. When \(P_{\rm L}\ll1\), it further implies
\(P_{\rm L}\approx e^\alpha L^\beta\). A bootstrap interval for \(\beta\)
can quantify sampling fluctuation conditional on that model, but it cannot
validate the model or turn an unsupported ansatz into a phase criterion.

## What can actually be justified

Let a distance-\(d\) code correct every error of weight at most
\(t=\lfloor(d-1)/2\rfloor\), and assume independent physical errors with rate
\(p\). For fixed \(d\), the failure probability can be grouped by error weight:

\[
P_{\rm fail}(d,p)=\sum_{w=t+1}^{n} A_w(d)
p^w(1-p)^{n-w},
\]

where \(A_w(d)\) counts harmful weight-\(w\) configurations. Therefore, if
\(A_{t+1}(d)>0\), the small-\(p\) leading term is

\[
P_{\rm fail}(d,p)=A_{t+1}(d)p^{t+1}+O(p^{t+2}).
\]

This is the precise content behind the heuristic “roughly \(p^{d/2}\).” The
coefficient is distance dependent, and herald conditioning, correlated
effective noise, boundaries, degeneracy, and an approximate BP+MWPM decoder
can change the first harmful weight. The heuristic is therefore not itself a
global fitting law for the current decoder.

For surface-code recovery below threshold, a path-counting argument gives a
bound of the form

\[
P_{\rm fail}(L)\le \operatorname{poly}(L)\,\rho(p,q)^L,
\qquad \rho(p,q)<1,
\]

so the robust large-size expectation is exponential suppression in linear
size, up to subexponential factors. Dennis *et al.* derive such a bound in
Eq. (62) and explicitly state that below threshold the failure probability
decreases exponentially with \(L\):
[`references/dennis2001-topological-quantum-memory/paper.pdf`](../../references/dennis2001-topological-quantum-memory/paper.pdf).

This does **not** establish one global exponential formula either. Near a
critical point, finite-size corrections matter; above threshold, LER generally
approaches an order-one limit rather than following the same exponential law.
The current herald-aware, truncated BP+MWPM decoder also needs a decoder-
specific argument before asymptotic claims are made.

## Epistemic status of the existing Lab 003 outputs

| Item | Status | Reason |
|---|---|---|
| Corrected posterior-LLR raw logical outcomes | valid measurements | Decoder/source audits remain valid. |
| Seed-cluster bootstrap | valid conditional uncertainty tool | It captures the registered sampling unit but proves no scaling law. |
| Logit-versus-log-size slope | historical exploratory projection only | Its power-law-odds assumption has no derivation here. |
| Red/green phase colors and inferred boundary from that slope | withdrawn | Their physical interpretation depends on the unsupported ansatz. |
| Pairwise curve crossings | finite-size diagnostics only | With noisy curves they are fluctuation-sensitive and are not a phase definition. |

The active Bayesian figure is accepted only as a finite-window posterior
direction map; it is not an accepted asymptotic phase diagram.

## Boundary-guide and uncertainty correction — Phase B17

The withdrawn B16 presentation attached a narrow conditional refit envelope to
a cubic guide selected after inspecting the field. That envelope conditioned on
the model, endpoint choices, first-root selection, and independent cellwise
posterior draws; it did not cover finite-grid resolution, model selection,
boundary topology, or the high-q endpoint. It must not be read as a confidence
or credible interval for a phase boundary.

B17 separates the two objects. The dashed curve is only a monotone visual guide
with endpoints derived from central cellwise log-odds crossings. The neutral
region is the narrowest nondecreasing envelope containing all sixteen B11
marginal-0.90 directional brackets and three B14 high-q right-censoring
brackets. It is a finite-grid evidence region, not a pointwise or simultaneous
contour confidence set. A genuine contour credible region would require a
registered joint latent-surface model with seed-cluster dependence and
calibrated joint coverage.

## Symmetry constraint on the guide — Phase B18

The physical phase diagram is taken to obey $q_c(p)=q_c(1-p)$ after the known
configuration-complement syndrome/logical relabeling. On the plotted
fundamental domain $0\le p\le0.5$, a differentiable guide must therefore obey

\[
\left.\frac{dq_c}{dp}\right|_{p=0.5}=0.
\]

B18 enforces this exactly with a parametric cubic Bezier whose last two q
controls coincide at $q_c$ while its last two p controls remain distinct. This
is a structural constraint on the visual guide, not new cellwise evidence.
The evidence raster is shown only over its measured p-cell support inside a
full $[0,0.5]$ axis; unmeasured low-p space is not extrapolated.

## Proof obligations before another phase claim

Every new scaling hypothesis must record, before fitting:

1. the exact mathematical statement and the quantity it predicts;
2. assumptions about code family, noise, herald conditioning, decoder, and
   asymptotic regime;
3. a derivation or a primary-source theorem, with all gaps labeled as
   assumptions rather than results;
4. competing models or a model-free null that could falsify the proposal;
5. identifiability with the available distances and a preregistered
   goodness-of-fit or held-out-distance check;
6. sampling uncertainty and model uncertainty as separate objects; and
7. a claim boundary distinguishing a finite-window trend from an asymptotic
   phase.

## Bayesian finite-window hypotheses

The current data support a Bayesian question without choosing a global
scaling law. At one measured $(p,q)$, let
\(\theta_7,\theta_9,\theta_{11}\) be the unknown LERs. For logical-error count
\(k_i\) in \(n_i\) independent Monte Carlo shots,

\[
k_i\mid\theta_i\sim\operatorname{Binomial}(n_i,\theta_i).
\]

Use independent Jeffreys priors
\(\theta_i\sim\operatorname{Beta}(1/2,1/2)\). Conjugacy gives

\[
\theta_i\mid D\sim
\operatorname{Beta}\!\left(k_i+\tfrac12,n_i-k_i+\tfrac12\right).
\]

Define three exhaustive finite-window hypotheses (ties have posterior measure
zero):

\[
\begin{aligned}
H_\downarrow &: \theta_7>\theta_9>\theta_{11},\\
H_\uparrow &: \theta_7<\theta_9<\theta_{11},\\
H_{\rm other} &: \text{the other four strict orderings}.
\end{aligned}
\]

If \(f_i\) and \(F_i\) are the posterior Beta density and CDF, respectively,
then

\[
\Pr(H_\downarrow\mid D)=
\int_0^1 f_9(y)[1-F_7(y)]F_{11}(y)\,dy,
\]

\[
\Pr(H_\uparrow\mid D)=
\int_0^1 f_9(y)F_7(y)[1-F_{11}(y)]\,dy.
\]

The third probability is one minus their sum. Under the exchangeable prior,
the prior masses are \(1/6,1/6,4/6\), so the calculation does not silently
favor either direction. The integrals are evaluated deterministically by
Gauss--Jacobi quadrature and checked against a uniform-prior sensitivity run.

The operational classification is green only when
\(\Pr(H_\downarrow\mid D)\ge0.90\), red only when
\(\Pr(H_\uparrow\mid D)\ge0.90\), and unresolved otherwise. The plotted
continuous evidence score follows the requested posterior log-odds form:

\[
\Lambda_{\rm post}=
\log\frac{\Pr(H_\uparrow\mid D)}{\Pr(H_\downarrow\mid D)}.
\]

Because the two directional hypotheses have equal prior mass, this is also
their log Bayes factor. The separate value
\(\Pr(H_{\rm other}\mid D)\) prevents a large odds ratio between two small
directional masses from being mistaken for a resolved classification. This
propagates uncertainty in the measured LERs and retains more information than
a binary label. It is not a posterior probability of an asymptotic phase;
that stronger claim still needs a decoder-specific scaling model and held-out
larger distances.

## Researcher-selected Bayesian fuzzy linear trend

Strict order is stronger than the research question: a noisy curve can have
an overall downward direction while one adjacent pair reverses. The selected
replacement retains the binomial likelihood and independent Beta posteriors
above, but changes the finite-window trend functional.

For a posterior draw \(\boldsymbol\theta=(\theta_{L_1},\ldots,\theta_{L_m})\),
define

\[
\beta(\boldsymbol\theta)=
\frac{\sum_i(L_i-\bar L)\theta_{L_i}}
     {\sum_i(L_i-\bar L)^2}.
\]

This is the ordinary least-squares slope of the best linear projection of
that latent LER draw onto distance. The line is a **descriptive functional**,
not the sampling model: the likelihood remains binomial at each independent
\(\theta_{L_i}\), and no claim is made that the true LER curve is linear.
Curvature therefore does not invalidate the posterior calculation; it is
reported separately as a shape diagnostic.

The fuzzy directional hypotheses and score are

\[
H_\uparrow:\beta(\boldsymbol\theta)>0,
\qquad H_\downarrow:\beta(\boldsymbol\theta)<0,
\qquad
\Lambda_{\rm trend}=\log
\frac{\Pr(H_\uparrow\mid D)}{\Pr(H_\downarrow\mid D)}.
\]

Continuous Beta posteriors make the hypotheses exhaustive up to a
measure-zero tie. Red/undecodable requires
\(\Pr(H_\uparrow\mid D)\ge0.90\), green/decodable requires
\(\Pr(H_\downarrow\mid D)\ge0.90\), and other cells are gray. Replicated
scrambled Sobol draws integrate the posterior. Zero QMC events are
resolution-censored with a one-sided log-odds bound. Independent Beta(1,1)
prior, endpoint-direction, and Kendall-tau-sign results are retained as
sensitivity diagnostics.

This answers whether the measured distance window has a fuzzy overall trend;
it does not prove an asymptotic phase. In particular, a gray trend label is
not by itself a reason to collect more data: floor- and saturation-limited
curves can have an unresolvable slope while lying far from the transition.

## Applicability domain and boundary-focused sampling

The slope-sign functional is a **transition-band diagnostic**, not a universal
phase definition. Three regimes must be separated before assigning sampling
value:

1. **Low-LER decodable interior.** When logical failures are zero or very rare
   across the measured window, the posterior slope is dominated by the
   finite-sample floor. More shots mostly tighten an already small absolute
   LER and need not locate the phase boundary.
2. **Saturated undecodable interior.** Above threshold, finite-size LER curves
   approach the random-logical-decision limit and their residual size
   differences can be smaller than sampling noise. A gray slope here means
   saturation, not genuine phase ambiguity. For the current binary logical
   observable the observed plateau is near (1/2), not (1); the physical
   point is the order-one saturation limit appropriate to the observable.
3. **Transition band.** Only between those interiors is the sign and magnitude
   of finite-size flow useful for locating the operational lower boundary
   (p_c(q)). This is where additional LER sampling is valuable.

The next map must therefore expose separate posterior quantities for absolute
LER magnitude, saturation/floor status, and transition-band direction. It
must not render every slope-unresolved cell as an unknown physical phase.
Floor and saturation cutoffs must be preregistered from the logical observable
and validated anchor cells, with posterior probabilities rather than hard
comparisons of noisy point estimates.

Future active sampling is restricted to the **lower decodable-to-undecodable
boundary** encountered as (p) increases at fixed (q). A candidate must be
neither floor- nor saturation-limited, must lie in a row-wise bracket between
decodable and undecodable anchors (or reduce uncertainty in such a bracket),
and must have positive posterior-predictive value for the boundary location.
The acquisition target is uncertainty in (p_c(q)), not the number of gray
cell labels resolved. High-(p), low-(q) saturated cells and low-(p),
high-(q) floor cells receive zero routine sampling priority.

## Posterior-predictive measurement design after Phase B6

Additional shots are not selected by comparing the observed LER point
estimates. For each unresolved cell, the current posterior is

\[
\theta_i\mid D\sim\operatorname{Beta}
\left(k_i+\tfrac12,n_i-k_i+\tfrac12\right).
\]

For a proposed vector of extra shot counts \(m_i\), the diagnostic draws a
latent vector from that posterior and then draws future counts

\[
K_i^{\rm new}\mid\theta_i\sim\operatorname{Binomial}(m_i,\theta_i).
\]

It updates the Beta posterior with \(K_i^{\rm new}\), recomputes the posterior
probability of the same finite-window projection-slope sign, and records
whether the updated probability crosses the preregistered 0.90 gate. Repeating
this nested calculation estimates the probability of an upward resolution, a
downward resolution, or continued ambiguity before any decoder job is run.

The diagnostic also reports posterior sign entropy and the probability that a
resolved direction disagrees with the slope sign of the outer latent draw.
That latter quantity is a posterior-predictive decision-error diagnostic, not
a frequentist guarantee. All estimates are conditional on independent
binomial shots, independent Jeffreys-Beta posteriors across distances, the
finite-window slope functional, and finite Monte Carlo integration. They do
not establish asymptotic scaling or define a resource-value loss function.
