# Figures

`herald-belief-matching.html` is the interactive inference workbench served from the Lab 002 result page. It exposes four layers on the same deterministic sample:

1. the true simulated edge error plus observed syndrome and fusion-remnant heralds;
2. the selected herald-aware BP edge marginals;
3. the marginal change caused by adding the herald factors to syndrome-only BP;
4. the selected Herald-aware BP+PyMatching correction compared edgewise with simulated truth.

Clicking an edge reports its prior, syndrome-only posterior, herald-aware posterior, posterior change, matching weight, and correction/truth membership. The decoder panel switches between the default probability-damped recurrence and the opt-in memory recurrence. It reports the single damping trajectory or selected memory candidate, the memory score when applicable, and the fixed-point state. The right panel follows the shared Lab workbench order: lattice, tuning parameters, decoder, measurement errors, and random seed; Lab-specific posterior-quality, density-flow, and edge diagnostics follow those common controls. The backend is `scripts/artifact_backend.py`; the dashboard only transports its JSON response.

The decoder outcome is displayed as a logical coset: `correct` when the residual is in the ground-state logical class and `wrong` when it is not. The backend retains the boolean `logical_error` field as a machine-readable compatibility field; the artifact does not present that boolean as a yes/no answer.
