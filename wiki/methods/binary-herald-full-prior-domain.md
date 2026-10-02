---
title: Binary herald decoding over the full prior domain
page_type: method
status: validated-finite-size
source_refs:
  - labs/lab-009-planar-herald-decoder-survey/results/full-prior-symmetry-audit.json
  - labs/lab-009-planar-herald-decoder-survey/scripts/audit_full_prior_symmetry.py
  - labs/lab-009-planar-herald-decoder-survey/results/validation.json
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
updated: 2026-10-01
---

# Binary herald decoding over the full prior domain

**Summary**: The incomplete binary-herald channel requires independent research over p,q in [0,1]; the B18 complement-symmetric guide is withdrawn.

**Sources**: [Complete small-system audit](/lab?id=lab-009-planar-herald-decoder-survey); [Corrected evidence](/lab?id=lab-003-herald-threshold-phase-diagram).

**Last updated**: 2026-10-01

The honeycomb model uses iid edge errors x_e ~ Bernoulli(p), exact syndrome s=Hx mod 2, and h_v=1{n_v>=2} b_v with independent b_v ~ Bernoulli(q). Its physical domain is p,q in [0,1]. The binary-herald q is a detection probability; it is not the direction-bias q in Lab 008.

At a degree-three detector, complementation sends n to 3−n and swaps eligible and ineligible events. For 0<q<1, h=0 mixes the two mechanisms “ineligible” and “eligible but missed.” There is no generally invertible relabeling of the visible (s,h) record implementing p↔1−p. Complementing only the prior, or substituting min(p,1−p) while leaving herald likelihoods unchanged, changes the inference problem.

An independent complete L=2 enumeration gives optimal logical risks:

| q | p=0.2 | p=0.8 |
| --- | --- | --- |
| 0 | 0.308157992960 | 0.308157992960 |
| 0.5 | 0.231775342400 | 0.304423178240 |
| 1 | 0.139016683520 | 0.139016683520 |

The interior-q difference disproves a general Bayes-risk complement symmetry. The enumeration sums joint probability mass separately in each logical sector for every visible record, then sums the smaller sector mass. [Reproducible audit](/lab?id=lab-009-planar-herald-decoder-survey).

At q=0 the transformed syndrome is s⊕H1 and the logical bit shifts by the parity of the all-edge vector. At q=1, (s,h) determines exact incident count for detector degrees at most three, so the complementary count record is recoverable. These endpoint transformations preserve optimal risk; an arbitrary approximate decoder need not obey them unless its equivariance is checked. At p=0 and p=1 the physical error vector is deterministic and optimal risk is zero for every q. At p=0.5 the error prior is uniform; this remains a special point, but is not an interior-q symmetry boundary or guaranteed extremum.

The phase diagram must consider both sides of half independently. Do not assume one threshold p_c(q), monotonicity in p, a symmetric high-p branch, a horizontal tangent at half, or an all-p ceiling inferred from a scan stopping at half. Define decodability by the limiting logical risk of a stated decoder/optimal inference as L grows; distinguish it from finite-window trend evidence. More herald information cannot increase optimal risk (records can be thinned), but practical decoder curves can violate that ordering.

Lab 003's B18 guide is withdrawn. Its measured low-p cohorts remain valid within their recorded geometry, decoder, size and channel. The current coverage figure leaves unmeasured p>0.5 blank. Lab 009 owns independent full-domain inference checks and bounded diagnostics; a converged full-domain thermodynamic phase diagram has not yet been measured.

## Related pages

- [Statistical-mechanics formulation](sun-fusion-herald-belief-propagation.md)
- [Lab 009](/lab?id=lab-009-planar-herald-decoder-survey)
