# Lab 009 — Planar herald decoder survey and integration

## Motivation and question
Build on Labs 002/003 to distinguish exact logical-sector inference, configuration MAP and marginal-based matching on the same classical honeycomb record. Develop and expose validated reusable algorithms through `src/herald_decoder`.

## Model and hypotheses
IID binary retained-edge errors; exact detector parity; h=1{n>=2} Bernoulli(q), conditionally independent given errors; no measured rough-boundary factors; p in [0,1], q in [0,1]. The loss is invalid syndrome or nontrivial residual logical parity. H1: trivalent planar factorization supports exact sector inference. H2: configuration MAP is a useful efficient baseline but need not outperform BP. H3: controlled transfer/MPS and Kac–Ward formulations cross-check the partition function, with explicit width/truncation/penalty limits. H4: matched finite-size records can expose differences between decoder objectives.

## Dependencies and research basis
Parents: Lab 002 (BP/LLR production API), Lab 003 (finite-size evidence). Method dependency: Lab 007 (sector partition function and hardening gap). Established primary theory: planar matchgate identities/FKT, Kac–Ward Ising determinant, and the honeycomb walk connective constant.

## Registered bounded work
Implement one standard representative of each distinct method, sharing graph/observation/score contracts. Promote signed configuration MAP, planar sector ML, exact transfer and controlled MPS through the package registry after validation. Keep finite-penalty Kac–Ward a lab research comparison if numerical/support gates do not justify production promotion. Ingest numeric data only (CSV/JSON/JSONL/NPZ with allow_pickle=False); preserve source hashes and cohort labels. 

Light checks: independent weighted enumeration at L=2; held-out random cosets at L=3/4; q=0/1, p=0, 0.5 and 1, impossible records, negative weights, extreme prior; reference permutation and q=1 support. Exact posterior tolerance 1e-9 on checked records; MAP maximizing sector and support must pass. MPS compared against exact transfer at two chi values, labeled approximate. New matched benchmark: L=5,9; (p,q)=(.16,0),(.24,.5),(.40,.8),(.49,1),(.60,.5),(.80,.5),(.95,.8),(.80,1), 200 shots/cell; up to 8 CPU cores, 2 GiB working arrays, no full phase sweep. Warm timings separate setup/JIT from decode median/p95. Exceptions and nonconvergence are retained; paired differences and Wilson intervals are reported. Also exercise each promoted API and batch path.

## Deliverable contract and acceptance order
1. Model/theory: wiki/model.md, statistical-mechanics.md, configuration-map.md, planar-ml.md, transfer-mps.md, kac-ward.md, comparison.md; graph assumptions, weights, sector sums, limits and derivations independently navigable.
2. Implementation: package classes, common registry and README; correction/batch/posterior contracts; no downloaded-path runtime imports.
3. Verification: results/validation.json and tests; every promoted branch exercised end to end; rejected methods labeled explicitly.
4. Data: data/*.csv and numeric archives with results/data-provenance.json; benchmark cohorts explicit; no heterogeneous pooling or failed-fit promotion.
5. Analysis: matched performance/efficiency results; numerical approximation limitations.
6. Figures: regenerated PNG plus vector SVG/PDF for matched LER, conditional risk, runtime and approximation diagnostics; verify plotted data, units, uncertainty, captions and report embeds.
7. System delivery: lab.json, labs/labs.json, package registry, and rendered dashboard lab/wiki/results; report lint and relevant regression checks. Optional workbench must exercise promoted APIs if added.

## Stop and completion rules
Stop production promotion of a method if posterior/support/correction gates fail; preserve the diagnostic and use validated alternatives. No heavy campaign, new physical fusion channel, thermodynamic threshold, universality proof or noisy spacetime claim. Completion requires theory, passing reusable methods, self-contained numeric evidence, regenerated visuals, report, registry and rendered surface verification. Registration is not completion. The active contract remains this Lab 009 survey through those gates.

## Full-prior correction — 2026-10-01
The full square p,q in [0,1] is the research domain. Low-p pilot data are retained cohorts, never reflected into high-p results. Check both deterministic prior endpoints and negative prior log odds. Configuration MAP uses the literal log posterior above half. Independent high-p diagnostics test recovery and finite-size behavior without assuming a single p_c(q), a mirrored boundary or a horizontal tangent at half. The uniform prior remains special. No new thermodynamic boundary is claimed from this bounded integration pilot.

## Validation checkpoint — 2026-10-01
The supplemental generic-factor contract check at `results/planar-factor-contract-validation.json` passed 12 independent L=2 weighted enumerations at p=.23, using three reference choices and one relabeled edge ordering per case. Maximum posterior discrepancy was 3.33e-16; negative and nonfinite factors were rejected. This is a scoped interface check, not completion of the full verification, report, or rendered-delivery gates. The next bounded validation item is an explicit q=1 configuration-MAP support check, followed by review of the remaining endpoint and public API gates.

## Survey acceptance — 2026-10-01

All seven registered acceptance items are delivered: local method theory, four reusable package methods, independent oracle and regression checks, matched numeric vectors, matched performance/efficiency, four PNG/SVG/PDF figures, and the rendered system surfaces. The final receipts are `results/survey-analysis.json`, `results/rendered-delivery.json` and `results/delivery-verification.json`. The 3,200 shared trials retain their measured inputs and outputs. Kac–Ward remains research code; finite-chi MPS is approximate. No heavy campaign or new full-domain threshold is claimed. This acceptance supersedes the earlier partial validation checkpoint.

