# Statistical inference and scientific graphics

Read this only when the task requires statistical estimation, hypothesis
testing, uncertainty, fitted curves/surfaces, thresholds, or scientific plots.

## Inferential contract

Define observations, independent sampling unit, likelihood or estimating
equation, parameters/latent variables, target estimand, and conditioning set.
Account for dependence, censoring, missingness, selection, convergence failure,
and adaptive sampling. Explain how the model connects the observed data to the
scientific target.

Separate uncertainty from:

- sampling and clustered Monte Carlo variation;
- parameters or latent quantities;
- model/form/regularization choice;
- numerical approximation and convergence;
- finite-size or out-of-domain extrapolation; and
- measurement/design resolution.

State whether each interval is pointwise or simultaneous, confidence or
credible, conditional or selection-adjusted, and what coverage or calibration
it targets. Resample the independent unit, not convenient lower-level rows.

## Model checking

Before promotion, use applicable checks that can reject the method:

- recovery on synthetic or exact cases;
- empirical coverage or simulation-based calibration;
- residual, posterior-predictive, or goodness-of-fit checks;
- held-out clusters, sizes, rows, regimes, or experiments;
- sensitivity to plausible priors, regularizers, functional forms, and
  inclusion rules; and
- comparison with the simplest scientifically credible baseline and at least
  one serious alternative when model choice matters.

If failures are driven by model misspecification, do not hide them by increasing
sample size or smoothing.

## Curves, boundaries, and phase diagrams

Distinguish a regression surface, zero level set, root/crossing, finite-grid
bracket, extrapolated asymptotic boundary, and visual guide. They are different
estimands.

For a modeled level set, define a surface such as

\[
y_i\sim p(y_i\mid f(x_i),\phi),\qquad
\mathcal B=\{x:f(x)=0\},
\]

and propagate uncertainty in the full surface to boundary location, endpoints,
branch existence, and topology. Fitting selected crossings as if they were
precise independent data usually understates uncertainty.

Do not resolve features at or below design spacing unless identifiability and
coverage are demonstrated on suitable synthetic truths. Shape constraints such
as monotonicity are assumptions; derive them physically or include them in a
sensitivity comparison. A line called a “guide” must not carry a
confidence-looking band. Either infer the object and its uncertainty from a
stated model, or show a non-inferential guide without implying precision.

When data cannot select topology or locate the boundary, show an unresolved
region, identified set, representative draws, probability surface, or no line.
Changing a fitted model invalidates uncertainty computed under the old model.

## Analysis output

Plots are optional. First produce a machine-readable analysis that records
integrity checks, estimates, uncertainty, diagnostics, alternatives, failures,
and claim status. Then choose the lightest communication form that helps the
researcher: a concise message, report, table, or figure.
