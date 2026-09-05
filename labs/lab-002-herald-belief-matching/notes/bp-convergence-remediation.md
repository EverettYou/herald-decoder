# BP convergence remediation, C0--C8

This mechanism track investigates fixed-point convergence, not a threshold or
an LER claim.

## C0--C1: diagnosis and intervention screen

C0 shows slow residual drift rather than a period-two orbit: the maximum
residual falls from 1.32e-2 at iteration 20 to 2.16e-3 at iteration 80, still
above the 1e-8 tolerance.

![C0 residual and spatial bottleneck trace.](../figures/convergence-trace-seed12.png)

C1 tests damping, initialization, and residual-priority scheduling on 64
matched square samples. Synchronous damping-0.25 converges on 12/64; residual
priority converges on 22/64 (+15.6 points), while damping changes and local
initialization do not improve it.

![C1 complete convergence ablation.](../figures/convergence-ablations-c1.png)

## C2--C4: correction interface and replication

C2 confirms syndrome-faithful posterior-LLR corrections but finds the Python
schedule slow (+243.6 ms per observation after timing controls). C3 compiles
the exact schedule; C4 independently replicates the convergence gain and
end-to-end cost.

![C2 posterior-LLR correction-interface validation.](../figures/residual-priority-c2.png)

![C3 compiled equivalence and timing study.](../figures/residual-priority-c3.png)

![C4 independent multi-geometry replication.](../figures/residual-priority-c4.png)

## C5--C8: bounded implementation work

C5 is an exact stable-sort replacement for repeated priority scanning.

![C5 factor-priority ordering profile.](../figures/residual-priority-c5.png)

C6 is the common-protocol endpoint comparison: square convergence is 21/64
versus 11/64, but residual priority is 1.63 ms slower. Honeycomb is 60/64
versus 59/64 and 0.29 ms slower. The finite sample has no paired logical
rescue or harm.

![C6 synchronous versus stable-sort residual priority.](../figures/residual-priority-c6.png)

C7 buffer reuse preserves exact output but is slower.

![C7 buffer-reuse timing.](../figures/residual-priority-c7.png)

C8 cached products change posterior/correction-relevant output and fail the
equivalence gate before timing: 13/64 square and 15/64 honeycomb observations
fail, including one correction and three iteration disagreements.

![C8 cached-product equivalence gate.](../figures/residual-priority-c8.png)

## Conclusion

Residual-priority scheduling is the strongest tested convergence mechanism,
but not the default: its validated implementation remains slower. Stable sort,
buffer reuse, and cached products do not change that decision. Detailed JSON
evidence runs from [`../results/convergence-trace-seed12.json`](../results/convergence-trace-seed12.json) through [`../results/residual-priority-c8.json`](../results/residual-priority-c8.json).
