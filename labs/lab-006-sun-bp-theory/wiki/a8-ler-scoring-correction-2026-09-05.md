# A8 LER scoring correction — 2026-09-05

## Finding

The A7/A8 experiment contract incorrectly defined BP tolerance
nonconvergence as a logical failure. That rule is invalid for this two-stage
belief-matching decoder. Stage 1 supplies final-iteration edge beliefs to
Stage 2; PyMatching still returns a correction whether or not the BP message
delta crossed its numerical tolerance.

## Correct final decision

A shot fails only if the final PyMatching correction leaves a nonzero measured
detector residual, or if `error XOR correction` has nontrivial logical parity.
The BP convergence flag, iteration count, and terminal message delta are
retained as numerical diagnostics and never gate LER.

## Root cause and propagation

The incorrect rule first entered the Lab 006 A7 PLAN and A7 manifest. The A7
runner then implemented `not bp_converged OR residual OR logical_parity`, and
the A8 manifest inherited that definition. This contradicted the established
Lab 002 belief-matching scorers, which compute LER from final residual homology
while recording BP convergence separately. It also contradicted the Lab 006
end-to-end profiling scorer, which never used BP convergence in its logical
count.

## Data consequence

All A7/A8 aggregates produced before this correction are invalid for LER or
threshold inference. They store the union count but not the overlap between BP
nonconvergence and genuine final logical failure, so they cannot be repaired
algebraically. The shots must be replayed. New checkpoints carry the explicit
`final-correction-v2` scoring rule and refuse to resume an old scope.
