# Decoding with incomplete local witnesses

**A two-parameter phase diagram on the specified open honeycomb patch**  
Computational research study · 27 September 2026

Local witnesses substantially enlarge the recoverable region. For the documented
configuration-MAP matching decoder, the syndrome-only transition is near
**p = 0.159**. The estimated boundary rises to the physical-error ceiling
**p = 1/2 near q = 0.886**. Its endpoint has a statistical interval
[0.882, 0.890] and a broader finite-size sensitivity range [0.873, 0.896].
These are estimates for this decoder. At **q = 1**, a separate path-counting
argument establishes decodability throughout the entire stated p range.

![Two-dimensional phase diagram](figures/phase_diagram.png)

**Figure 1.** Main result. Green and rose are inferred decodable and non-decodable
regions for the implemented decoder. The yellow band combines statistical
intervals with sensitivity to lattice size, scaling corrections, fitting window
and pair crossings; it is not a rigorous confidence band for the infinite lattice.
Dots are independently fitted fixed-q sections; lines interpolate between them.
No monotonicity constraint is imposed on these estimates. The dotted curve is
a separate sufficient condition for ideal configuration MAP. The q = 1 edge
has an analytic justification independent of posterior optimality.

<div class="pagebreak"></div>

## Finite-size evidence

The production dataset contains **1,850,800 unconditional decoding trials**;
564,000 additional trials scan the wider domain. Patches range from L = 8
to L = 128, with the larger sizes concentrated near the boundary.
The complete schedules specify every point, shot count and seed. An initial
scan was followed by fixed-count refinement; no trial was discarded or stopped
because of decoder convergence or its outcome. There were **0 invalid
or missing corrections**. Confidence intervals use the full trial denominator.

![LER curves at multiple sizes](figures/finite_size_sections.png)

**Figure 2.** Fixed-q sections and the p = 1/2 endpoint, with pointwise 95% Wilson
intervals. Shaded vertical intervals are statistical fit intervals only.
Below a section's transition the error decreases with size; above it the
error stays nonzero and generally grows toward 1/2. The endpoint has appreciable
drift: small patches alone suggest a lower critical q. In particular, at
q = 0.875 the rate first falls slightly and then rises at larger L.

At p = 1/2, parentheses below give failures/trials; dashes mark unsampled points.
Zero failures have the exact one-sided 95% upper bound 1−0.05^(1/N), about 3/N.

| q | L = 8 | L = 32 | L = 64 | L = 128 |
|---:|---:|---:|---:|---:|
| 0.85 | 29.83% (1790/6000) | 36.03% (2162/6000) | 43.70% (1311/3000) | — |
| 0.875 | 27.08% (1625/6000) | 25.52% (1531/6000) | 31.27% (938/3000) | 34.80% (174/500) |
| 0.885 | — | 21.15% (423/2000) | 21.80% (436/2000) | 18.40% (92/500) |
| 0.9 | 21.52% (1291/6000) | 14.03% (842/6000) | 10.10% (303/3000) | 6.60% (33/500) |
| 0.95 | 11.77% (353/3000) | 0.77% (23/3000) | 0.13% (4/3000) | — |
| 1 | 3.63% (109/3000) | 0.00% (0/3000) | 0.00% (0/3000) | — |

At p = 0.25, q = 0.8, the L = 48 failure rate is 0.07% (2/3000). The syndrome-only
threshold is much lower than this physical error probability. Additional
[size-growth plots](figures/size_trends.pdf), the
[full-domain scan](figures/global_scan.pdf) and
[crossing-drift plots](figures/crossing_drift.pdf) accompany the data.
The scan resolves one separating curve and finds no reentrant region on its
sampling scale. It cannot exclude features narrower than the sampling and
finite-size uncertainty, or very late crossovers.

<div class="pagebreak"></div>

## Decoder and physical validation

The geometry is constructed directly from the supplied integer-coordinate
hexagons, exposed-side removal and boundary rule. All isolated vertices remain.
The resulting counts are |V| = 2L² + 4L, |E| = 3L² − 1 and |D| = 2L² − 2;
the shortest logical path has **d = 2L − 1**. Thus L is never treated as the
code distance. The logical mask consists exactly of retained edges meeting the
right unmeasured boundary. See the [L = 3 geometry figure](figures/geometry.pdf).

For degree at most three, parity implies $n_v=s_v+2z_v$ with $z_v$ binary.
A positive herald fixes $z_v=1$; an absent herald contributes a factor
$(1-q)^{z_v}$. Conditional on these constraints, posterior maximization reduces
exactly, for 0 < p ≤ 1/2 and q < 1, to minimizing edge costs

\[
w_e=\log\frac{1-p}{p}-\frac{d_e}{2}\log(1-q),\qquad d_e\in\{1,2\},
\]

where $d_e$ is the number of measured endpoints. The derivation uses the
conditional herald likelihood; observed heralds are not treated as independent
after averaging over errors. Both positive and zero heralds are used.
At q = 0 this is the same family's ordinary syndrome-only matching decoder.
At q = 1, all local counts equal $s_v+2h_v$ exactly. At p = 0, return zero.

Forced bits are eliminated using only s and h. Remaining local count constraints
are enforced with a penalty whose sufficient upper bound is proved in
[METHODS.md](METHODS.md). A smaller penalty is tried first and accepted only
when all observations are satisfied. A feasible minimum then has exactly the
constrained optimum cost. PyMatching solves the parity-constrained weighted
subgraph problem, including negative weights; its
[sparse-blossom method](https://quantum-journal.org/papers/q-2025-01-20-1600/)
keeps the computation practical. The callable interface is
`decode(GL, p, q, s, h) -> c`, with unpacked edge bits in a documented fixed
order. The decoder is deterministic and receives no hidden error information.

Validation checks the model and objective independently:

* Exhaustive L = 2 enumeration checks **8,888 feasible observations** at
  six parameter pairs, including q = 0, q = 1 and p = 1/2. Their observation
  masses sum to one and every returned configuration maximizes the exact weight.
* GF(2) elimination enumerates every syndrome-compatible configuration for
  750 sampled L = 3 trials. Separate mixed-integer optimization certifies
  **60/60** tested objectives through L = 16, without matching or penalties;
  the largest objective difference is below 2.3 × 10⁻¹³.
* Adjacent heralds have the expected nonzero covariance. One million sampler
  trials at p = 0.25, q = 0.8 give 0.01678 ± 0.00014 (standard error), versus
  the exact 0.016875. Penalty and uneliminated-formulation comparisons also
  preserve the optimum objective. Detailed outputs are in `data/*validation.json`.

This is **MAP for one configuration**, not for the sum of probabilities in a
logical sector. Exact small-patch sector sums quantify the distinction:
at L = 2, p = 1/2, q = 0.93, this decoder has LER 0.3958, while sector MAP has 0.3626. Consequently the non-decodable region of this algorithm is not
an information-theoretic limit on optimal recovery. Floating-weight rounding
is a separate numerical approximation; the validation found no objective
discrepancy at the stated precision. Deterministic tie choices are fixed by
the pinned implementation version and are included in the measured LER.

<div class="pagebreak"></div>

## Boundary estimates, uncertainty and analytic limits

| q | Estimated p transition | 95% statistical interval | Finite-size sensitivity range |
|---:|---:|---:|---:|
| 0 | 0.159 | [0.159, 0.160] | [0.154, 0.166] |
| 0.1 | 0.167 | [0.165, 0.169] | [0.155, 0.197] |
| 0.2 | 0.178 | [0.176, 0.179] | [0.170, 0.182] |
| 0.3 | 0.191 | [0.188, 0.194] | [0.163, 0.199] |
| 0.4 | 0.205 | [0.204, 0.207] | [0.200, 0.215] |
| 0.5 | 0.223 | [0.222, 0.225] | [0.216, 0.229] |
| 0.6 | 0.250 | [0.248, 0.252] | [0.242, 0.264] |
| 0.7 | 0.281 | [0.278, 0.285] | [0.262, 0.294] |
| 0.75 | 0.308 | [0.304, 0.311] | [0.281, 0.325] |
| 0.8 | 0.345 | [0.343, 0.347] | [0.328, 0.365] |
| 0.825 | unresolved | — | [0.351, 0.395] (crossings) |
| 0.85 | 0.400 | [0.397, 0.402] | [0.382, 0.413] |
| 0.875 | 0.459 | [0.452, 0.467] | [0.418, 0.474] |

At q = 0.825, scaling fits fail the 0.01 goodness-of-fit criterion. Crossings
constrain this unresolved section; the curve interpolates neighboring accepted fits.

Statistical columns are approximate pointwise 95% intervals from binomial
likelihood curvature. The sensitivity column is wider and is **not** a 95%
interval for an infinite-size threshold. It envelopes acceptable alternate
fits and larger-size pair-crossing intervals. Some systematic errors may remain
outside it. Fits use a local expansion of logit(LER) in
$z=(p-p_c)(d/d_0)^{1/\nu}/\Delta p$, with an optional term
$u(d/d_0)^{-\omega}$. Powers ω = 0.5, 1 and 2 are checked for sensitivity.
Endpoint fits replace p by q with the opposite orientation.
The exponent is a nuisance parameter, not a claimed universality measurement.

The default section fit uses L ≥ 16 and a quadratic expansion. Curvature
intervals require goodness-of-fit p-value > 0.01, interior parameters and at
least three sizes. Pair crossings use two sizes. Correction terms and higher
minimum sizes check drift; endpoint inference preferentially uses corrections
and at least four sizes. `data/fits.json` retains all windows, models and
covariances, including rejected variants. More trials reduce sampling error,
not extrapolation error. The sector-MAP gap is separate from this band.

A complementary argument constrains the whole continuous domain. Logical
failure of ideal configuration MAP requires a competing left-to-right path.
For a fixed length-n path, its likelihood-overlap bound is
$2[p(1-p)]^{n/2}(1+\sqrt{1-q})^{n-1}$. Combining this with the honeycomb
connective constant $\mu=\sqrt{2+\sqrt{2}}$
([Duminil-Copin and Smirnov](https://annals.math.princeton.edu/2012/175-3/p14))
gives the sufficient decodable condition

\[
\mu\sqrt{p(1-p)}\left(1+\sqrt{1-q}\right)<1.
\]

It guarantees p < 0.07955 at q = 0 and the entire p range for q > 0.993212.
This conservative bound is independent of the fits. At q = 1,
any count-feasible logical ambiguity must contain an alternating spanning
path. Its probability is at most $2^{1-n}$; since $\mu<2$, failure vanishes
with size even without configuration optimality. Conversely, at p = 1/2,
q = 0 the two sectors are exactly equiprobable, so every valid decoder has
LER = 1/2 for every size. At p = 0, LER is exactly zero. These checks anchor
three edges of the diagram analytically.

The recorded simulation loops used **5.83 CPU-hours**, with affinity
limited to eight CPU cores, one computational thread per worker, and no GPU.
The largest recorded worker RSS was 272.5 MiB; the largest captured aggregate
snapshot was 2.04 GiB. These are comfortably within 32 GiB. Total project wall time, including setup and analysis, was 67.9 minutes.
Hardware, package versions, stage timings and memory records are included.

**[README.md](README.md)** documents the API, data and reproduction commands.
`python3 analysis.py` rebuilds the figures; `bash run_all.sh` reruns the experiment
separately. Full derivations are in **[METHODS.md](METHODS.md)**.
