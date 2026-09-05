# Herald decoder core

This package owns the reusable square/honeycomb observation model, the
posterior-LLR BP-plus-PyMatching decoder, and its exact-output-preserving
Numba kernels. Experiment-specific runners, figures, and raw results remain
in `labs/`.

Use `./run_research_python.sh` for simulation work. It verifies the pinned
accelerated runtime in `../../requirements-research.txt` before executing the
requested Python command. The matching projection is fixed to posterior LLR:
`log((1 - r_e) / r_e)`.
