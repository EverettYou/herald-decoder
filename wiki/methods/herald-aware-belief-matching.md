---
title: Herald-aware belief matching
page_type: method
status: preliminary-evidence
updated: 2026-09-04
source_refs:
  - labs/lab-002-herald-belief-matching/PLAN.md
  - labs/lab-002-herald-belief-matching/scripts/herald_bp_decoder.py
  - labs/lab-002-herald-belief-matching/REPORT.md
  - labs/lab-002-herald-belief-matching/results/bp-matching-benchmark.json
  - labs/lab-002-herald-belief-matching/results/memory-vs-damping-ab.json
  - labs/lab-002-herald-belief-matching/results/systematic-memory-vs-damping-ab.json
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
---

# Herald-aware belief matching

**Summary**: Herald-aware belief matching combines loopy belief propagation (BP) over the joint syndrome–herald observation model with a posterior-weighted PyMatching correction. It turns a local fusion-remnant record into soft edge weights rather than treating herald vertices as erased edges.

**Sources**: [Lab 002: herald-aware belief matching](/lab?id=lab-002-herald-belief-matching); [Improved Decoding of Circuit Noise and Fragile Boundaries of Tailored Surface Codes](/reference?id=higgott2023-belief-matching); [Belief-Matching Decoder](/reference?id=beliefmatching-code); [PyMatching Decoder](/reference?id=pymatching-code)

**Last updated**: 2026-09-04

## Probabilistic model and inference target

Let $G=(V,E)$ be the retained data-edge graph and let $V_{\rm det}\subseteq V$ denote its detector vertices.  The latent variable is a binary error field $x=(x_e)_{e\in E}$, with $x_e=1$ when edge $e$ has an error.  The initial model takes independent edge errors,

\[
\pi_e(x_e)=P(x_e)=p^{x_e}(1-p)^{1-x_e}.
\]

One extraction round supplies the observed record $y_v=(\tilde s_v,h_v)$ at each detector vertex.  For a proposed local error pattern $x_{\partial v}=\{x_e:e\ni v\}$, define its incident error degree $d_v=\sum_{e\ni v}x_e$ and set $\alpha=q(1-p_h)$.  The local observation model is

\[
\psi_v(x_{\partial v};y_v)
= P(\tilde s_v\mid d_v)P(h_v\mid d_v),
\]

\[
P(\tilde s_v\mid d_v)=
\begin{cases}
1-p_m,&\tilde s_v=d_v\bmod2,\\
p_m,&\tilde s_v\ne d_v\bmod2,
\end{cases}
\]

\[
P(h_v\mid d_v)=
\begin{cases}
\alpha\,\mathbf 1[d_v\ge2],&h_v=1,\\
1-\alpha\,\mathbf 1[d_v\ge2],&h_v=0.
\end{cases}
\]

The role of $\psi_v$ is not to identify an erroneous incident edge.  It is a likelihood for every *joint* incident-edge pattern: parity constrains the pattern's odd/even degree, while a herald shifts probability toward patterns of degree at least two.  Thus the herald is represented as a correlated local witness, rather than being reinterpreted as an erased edge. [String-herald simulator model](../models/string-herald-simulator.md#generative-model)

These local ingredients define the joint posterior target

\[
P(x\mid \tilde S,H)
\propto
\left[\prod_{e\in E}\pi_e(x_e)\right]
\left[\prod_{v\in V_{\rm det}}\psi_v(x_{\partial v};y_v)\right].
\]

The desired soft output for each edge is its marginal

\[
r_e=P(x_e=1\mid\tilde S,H)
=\sum_{x:x_e=1}P(x\mid\tilde S,H).
\]

This exact marginalization is exponential in $|E|$.  BP is introduced to approximate these marginals by exploiting the fact that the joint distribution is built from small, local vertex factors.

## Sum-product messages: meaning and update equations

The factor graph has one binary variable node for each edge and one factor node for each detector vertex.  A variable-to-factor message means: *given all evidence available to this edge except the receiving vertex, how plausible are its two states?*  A factor-to-variable message means: *given this vertex's syndrome/herald observation and the current beliefs on its other incident edges, how compatible is each state of the receiving edge?*

For an edge $e$ incident on detector factors $N(e)$, and a vertex factor $v$ incident on edges $\partial v$, the sum-product updates are

\[
m_{e\to v}(x_e)
\propto
\pi_e(x_e)
\prod_{u\in N(e)\setminus\{v\}}m_{u\to e}(x_e),
\]

\[
m_{v\to e}(x_e)
\propto
\sum_{x_{\partial v\setminus\{e\}}}
\psi_v(x_{\partial v};y_v)
\prod_{e'\in\partial v\setminus\{e\}}
m_{e'\to v}(x_{e'}).
\]

The exclusion of the recipient in both equations is essential: it prevents a factor from immediately receiving its own evidence back and counting it twice.  The factor update performs the physical/statistical operation required by a local fusion-remnant observation: it sums over the unobserved neighbouring error assignments, retaining only their aggregate support for $x_e=0$ and $x_e=1$.  It therefore transmits a soft local constraint, never a hard edge decision.

At convergence, or after the iteration limit, the edge belief is assembled from its prior and all incoming factor messages,

\[
b_e(x_e)
\propto
\pi_e(x_e)\prod_{v\in N(e)}m_{v\to e}(x_e).
\]

\[
r_e=b_e(1).
\]

On a tree factor graph these equations give exact marginals.  A two-dimensional decoding lattice contains loops, so repeated messages can carry overlapping evidence and the resulting $r_e$ is a loopy-BP approximation.

## Recurrence control on loopy graphs

The public decoder exposes two recurrence modes. The operational default is
`recurrence_mode="damping"`. If $\widehat m_{v\to e}^{(t)}$ denotes the raw
factor-to-variable update above, the stored message is

\[
m_{v\to e}^{(t)}
=\lambda m_{v\to e}^{(t-1)}
+(1-\lambda)\widehat m_{v\to e}^{(t)}.
\]

The result is normalized after mixing. Damping does not add evidence or alter
the target factor model. Its purpose is numerical: it reduces the amplitude
of oscillations caused when loopy paths return correlated evidence to the same
message. The default coefficient is $\lambda=0.25$.

`recurrence_mode="memory"` enables an experimental Relay-BP-inspired search
in edge log-odds space. Let

\[
\Lambda_e^{(0)}=\log\frac{1-p}{p}.
\]

Let $L_e^{(r,t-1)}$ be the previous belief log-odds in relay leg $r$.
The memory-adjusted variable bias is

\[
\Lambda_e^{(r,t)}
=(1-\gamma_e^{(r)})\Lambda_e^{(0)}
+\gamma_e^{(r)}L_e^{(r,t-1)}.
\]

The variable-to-factor update then uses this bias in place of the static
prior.  Thus $\gamma_e=0$ recovers ordinary sum-product BP, while positive
$\gamma_e$ retains part of the preceding belief.  Negative $\gamma_e$ is an
algorithmic anti-memory perturbation: it pushes the next update away from a
previously reinforced belief and can break symmetric trapping sets.  It is
not a negative physical error probability.

The first memory leg uses a uniform $\gamma_0$. Each subsequent leg inherits the
preceding edge beliefs, resets directed messages, and draws a disordered
$\gamma_e$ independently for every edge from a configured interval.  This
is relay ensembling, not a collection of independent restarts: the state is
passed forward while the update dynamics are changed. The tested interval
includes negative values, following the mechanism of
[[methods/relay-belief-propagation|Relay belief propagation]], but its values
are a herald-model hyperparameter to benchmark rather than a portable
default.

Relay legs are heuristic searches and do not by themselves retain the exact
posterior semantics of ordinary BP.  The implementation therefore ranks legs
using only the observed herald model, never simulator edge truth and never a
hard syndrome-validity test.  From each candidate's edge beliefs $b_e$ and
factor beliefs $b_v$, it evaluates the Bethe free energy

\[
F_{\rm B}
=\sum_v\sum_{x_{\partial v}}
b_v\log\frac{b_v}{\psi_v}
+\sum_e(1-|N(e)|)\sum_{x_e}
b_e\log\frac{b_e}{\pi_e}.
\]

It also measures local pseudomarginal inconsistency,

\[
C=\sum_{(v,e)}
\left\|
b_e-
\sum_{x_{\partial v\setminus e}}b_v
\right\|_1.
\]

The selected candidate maximizes

\[
J=-F_{\rm B}-C.
\]

This score favors candidates that explain the observed $(\tilde S,H)$ well
under the original factor model and whose edge/factor beliefs agree locally.
It does not assert hard syndrome consistency, because this BP layer produces
soft weights rather than a correction chain.  The score is a model-based
selection heuristic, not an exact log evidence on a loopy graph. [Implementation,
Relay-memory inference](../../labs/lab-002-herald-belief-matching/scripts/herald_bp_decoder.py#HeraldBeliefMatchingDecoder)

## From soft belief to a correction

BP stops at $\{r_e\}$: it neither thresholds those values nor applies a chain, so it cannot change the measured syndrome. The registered decoder makes a separate, explicitly approximate projection from the active recurrence's beliefs to independent matching costs,

\[
w_e=\log\frac{1-r_e}{r_e},
\]

and gives PyMatching the original measured syndrome.  PyMatching then chooses a binary correction $c$ compatible with that syndrome.  For an independent posterior approximation, this LLR is the MAP reduction up to a correction-independent constant: it includes the likelihood of both $c_e=1$ and $c_e=0$. The former $-\log r_e$ projection omitted the latter term, so it made high-posterior edges cheap without penalising their omission; it is preserved only as a labelled legacy comparison. Neither projection recovers the full correlated posterior, and non-converged BP beliefs must not be interpreted as exact pins. [Lab 002 plan, Decoder candidates](../../labs/lab-002-herald-belief-matching/PLAN.md#decoder-candidates) [Implementation, `HeraldBeliefMatchingDecoder`](../../labs/lab-002-herald-belief-matching/scripts/herald_bp_decoder.py#HeraldBeliefMatchingDecoder)

BP is therefore the soft inference front end and PyMatching the hard syndrome-compatible decision back end.  Posterior quality and final logical performance answer different questions: the former tests whether $(\tilde S,H)$ makes latent edge errors more predictable, while the latter tests whether the particular independent-weight projection preserves enough of that information to select a better logical correction.

## Matched baselines

Three decoder paths separate the source of any gain: static syndrome-only MWPM, syndrome-only BP plus MWPM, and herald-aware BP plus MWPM. The latter two use the same matching backend; only the herald-aware factor receives $H$. This comparison tests whether side information adds value beyond the BP front end itself. A tiny-graph exact logical-MAP enumerator is an accuracy oracle, not a scalable candidate.

## Contribution accounting

At the soft layer, proper log loss and Brier score compare the independent prior, syndrome-only posterior, and herald-aware posterior against simulator edge truth. The two score improvements attribute predictive information to parity conditioning and herald conditioning. They are not gauge-invariant logical observables.

At the logical layer, matched shots count failures rescued and introduced along static MWPM → syndrome-BP+MWPM → herald-BP+MWPM. Exact McNemar tests use only discordant paired outcomes. This is the primary attribution because the matching backend is necessary to turn any soft posterior into a logical decision.

An operational effective physical error is defined at fixed lattice and size by matching logical rates, $P_L^{\rm MWPM}(p_{\rm eff})=P_L^{\rm herald}(p)$. It converts decoder gain into physical-error units without identifying it with residual edge density. The quantity remains baseline-, size-, and uncertainty-dependent.

A separate hard marginal-MAP diagnostic thresholds BP marginals, applies those edges, discards heralds, and passes the residual syndrome to ordinary MWPM. It can test a literal predecoding mechanism, but it is not a stage of the registered soft belief-matching decoder.

## Current evidence and limitations

A systematic matched A/B compares probability-damped BP with the tested
memory-assisted configuration. Both arms
receive identical observations and use the same negative-log projection and
PyMatching backend. A legacy-only pilot selects square
$p=0.08,0.10,0.12$ and honeycomb $p=0.16,0.18,0.20$, avoiding grid
selection from the A/B effect. Every $L=5$ cell contains 1000 observations
from five deterministic seeds.

There is no systematic LER benefit. At square $p=0.08$, memory-assisted BP
increases failures from 72 to 92 per 1000 shots, rescuing 10 legacy failures
while introducing 30. The exact McNemar value is $p=0.00222$. The other five
cells are unresolved: their paired LER changes range from $-0.006$ to
$+0.001$. Descriptive pooling across different physical-error rates also
does not resolve a benefit on either lattice.
[Systematic A/B result](../../labs/lab-002-herald-belief-matching/results/systematic-memory-vs-damping-ab.json)

Proper soft scores challenge the update in every cell. New minus old log
loss ranges from $+0.0934$ to $+0.0962$ on square and from $+0.2354$ to
$+0.4261$ on honeycomb; every paired bootstrap interval excludes zero.
Brier-score intervals likewise exclude zero in all cells. Positive values
are worse. The selected memory-search candidate meets the fixed-point
tolerance on 0% of 6000 observations, while legacy convergence ranges from
15.6% to 81.2%. The current coefficient range, candidate budget, and
observation-only scorer are therefore not validated as an improvement.
Consequently, damping is again the public and interactive default; memory
remains available as an explicit ablation rather than being removed.
[Lab 002 report, Systematic six-cell A/B](../../labs/lab-002-herald-belief-matching/REPORT.md#systematic-six-cell-ab)

Dense-array Numba kernels reproduce both frozen BP outputs exactly and make
the systematic comparison practical; they do not change the algorithm.
After warm-up, measured speedups are 86--89 times for legacy BP and 19--21
times for memory-assisted BP. The ordinary project runtime retains an exact
Python fallback, and no dashboard algorithm code is introduced.
[Optimization validation](../../labs/lab-002-herald-belief-matching/results/bp-optimization-validation.json)

Older benchmark files remain evidence for the probability-damped
implementation. They show preliminary herald-aware gains relative to
syndrome-only baselines, but cannot be transferred to the memory-assisted
option. The broader question of whether the herald likelihood improves
decoding therefore remains separate from whether this internal BP search
heuristic is beneficial.

The key approximation is still the projection from correlated BP beliefs to
independent matching weights. LLR corrects the independent-edge objective but
does not restore chain correlations; higher-shot paired replications across
sizes are required before a threshold or general decoder-improvement claim.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[models/string-herald-simulator|String-herald simulator model]]
- [[methods/two-stage-herald-decoder|Two-stage herald decoder]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
- [[methods/side-information-aware-decoding|Side-information-aware decoding]]
- [[methods/sun-fusion-herald-belief-propagation|SU(N) fusion-herald belief propagation]]
