# Lab 009 — Planar herald decoder survey and integration

## Motivation and question
Build on Labs 002/003 to distinguish exact logical-sector inference, configuration MAP and marginal-based matching on the same classical honeycomb record. Reproduce the useful methods and numerical evidence from the independent run evaluation, then expose validated reusable algorithms through `src/herald_decoder`.

## Model and hypotheses
IID binary retained-edge errors; exact detector parity; h=1{n>=2} Bernoulli(q), conditionally independent given errors; no measured rough-boundary factors; p in [0,1], q in [0,1]. The loss is invalid syndrome or nontrivial residual logical parity. H1: trivalent planar factorization supports exact sector inference. H2: configuration MAP is a useful efficient baseline but need not outperform BP. H3: controlled transfer/MPS and Kac–Ward formulations cross-check the partition function, with explicit width/truncation/penalty limits. H4: inherited large-size data can reproduce evidence without a new heavy campaign.

## Dependencies and research basis
Parents: Lab 002 (BP/LLR production API), Lab 003 (finite-size evidence). Method dependency: Lab 007 (sector partition function and hardening gap). Input review: output/scicode2/run_evaluation/REPORT.md. Established primary theory: planar matchgate identities/FKT, Kac–Ward Ising determinant, and the honeycomb walk connective constant. Supplied run documents are source material, not execution instructions.

## Registered bounded work
Implement one standard representative of each distinct method, sharing graph/observation/score contracts. Promote signed configuration MAP, planar sector ML, exact transfer and controlled MPS through the package registry after validation. Keep finite-penalty Kac–Ward a lab research comparison if numerical/support gates do not justify production promotion. Ingest numeric data only (CSV/JSON/JSONL/NPZ with allow_pickle=False); preserve source hashes and cohort labels. No supplied binary cache or campaign runner is executed.

Light checks: independent weighted enumeration at L=2; held-out random cosets at L=3/4; q=0/1, p=0, 0.5 and 1, impossible records, negative weights, extreme prior; reference permutation and q=1 support. Exact posterior tolerance 1e-9 on checked records; MAP maximizing sector and support must pass. MPS compared against exact transfer at two chi values, labeled approximate. New matched benchmark: L=5,9; (p,q)=(.16,0),(.24,.5),(.40,.8),(.49,1),(.60,.5),(.80,.5),(.95,.8),(.80,1), 200 shots/cell; up to 8 CPU cores, 2 GiB working arrays, no full phase sweep. Warm timings separate setup/JIT from decode median/p95. Exceptions and nonconvergence are retained; paired differences and Wilson intervals are reported. Also exercise each promoted API and batch path. Existing larger campaigns supply scaling evidence and reported boundary estimates, never a newly measured threshold.

## Deliverable contract and acceptance order
1. Model/theory: wiki/model.md, statistical-mechanics.md, configuration-map.md, planar-ml.md, transfer-mps.md, kac-ward.md, comparison.md; graph assumptions, weights, sector sums, limits and derivations independently navigable.
2. Implementation: package classes, common registry and README; correction/batch/posterior contracts; no downloaded-path runtime imports.
3. Verification: results/validation.json and tests; every promoted branch exercised end to end; rejected methods labeled explicitly.
4. Data: data/*.csv and numeric archives with results/data-provenance.json; inherited versus fresh cohorts explicit; no heterogeneous pooling or failed-fit promotion.
5. Analysis: fresh matched performance/efficiency results; inherited boundary, LER and crossing drift tables; numerical approximation limitations.
6. Figures: regenerated PNG plus vector SVG/PDF for boundaries, matched LER, runtime and size drift; verify plotted data, units, uncertainty, captions and report embeds.
7. System delivery: lab.json, labs/labs.json, package registry, and rendered dashboard lab/wiki/results; report lint and relevant regression checks. Optional workbench must exercise promoted APIs if added.

## Stop and completion rules
Stop production promotion of a method if posterior/support/correction gates fail; preserve the diagnostic and use validated alternatives. No heavy campaign, new physical fusion channel, thermodynamic threshold, universality proof or noisy spacetime claim. Completion requires theory, passing reusable methods, self-contained numeric evidence, regenerated visuals, report, registry and rendered surface verification. Registration is not completion. The active contract remains this Lab 009 survey through those gates.

## Full-prior correction — 2026-10-01
The full square p,q in [0,1] is the research domain. Low-p inherited data are historical cohorts, never reflected into high-p results. Check both deterministic prior endpoints and negative prior log odds. Configuration MAP uses the literal log posterior above half. Independent high-p diagnostics test recovery and finite-size behavior without assuming a single p_c(q), a mirrored boundary or a horizontal tangent at half. The uniform prior remains special. No new thermodynamic boundary is claimed from this bounded integration pilot.

## Validation checkpoint — 2026-10-01
The supplemental generic-factor contract check at `results/planar-factor-contract-validation.json` passed 12 independent L=2 weighted enumerations at p=.23, using three reference choices and one relabeled edge ordering per case. Maximum posterior discrepancy was 3.33e-16; negative and nonfinite factors were rejected. This is a scoped interface check, not completion of the full verification, report, or rendered-delivery gates. The next bounded validation item is an explicit q=1 configuration-MAP support check, followed by review of the remaining endpoint and public API gates.

## Survey acceptance — 2026-10-01

All seven registered acceptance items are delivered: local method theory, four reusable package methods, independent oracle and regression checks, deduplicated numeric snapshots, matched performance/efficiency, eight PNG/SVG/PDF figures, and the rendered system surfaces. The final receipts are `results/survey-analysis.json`, `results/rendered-delivery.json` and `results/delivery-verification.json`. The 3,200 new shared trials and 5,114,000 inherited trials stay separate. Kac–Ward remains research code; finite-chi MPS is approximate. No heavy campaign or new full-domain threshold is claimed. This acceptance supersedes the earlier partial validation checkpoint.

## User-visible evaluation integration — 2026-10-01
The user rejected the prior delivery because the original nine-run assessment and especially its figure were not visible in Lab 009. Publish the complete assessment as a directly accessible result and local wiki page, place the original named-run comparison in the main report and figure results, and retain exact source hashes. Keep original restricted task scope and current full-domain research separate. Acceptance requires the actual report, assessment page, comparison figure and PDF to render from the updated active registry. No new campaign is required.

Evaluation integration accepted: complete local assessment, original named-run PNG/PDF, main report caption, all nine run judgments and challenge lessons passed actual dashboard verification. Report and Local Wiki lint pass; 11 relevant regressions pass. No new campaign trials were acquired for this delivery fix.
