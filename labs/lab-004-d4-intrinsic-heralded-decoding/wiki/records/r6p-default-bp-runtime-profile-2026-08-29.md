---
title: 'R6P default R6D BP runtime profile'
status: current
updated: 2026-08-31
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

# R6P default R6D BP runtime profile

Profiled 20 fixed, replay-verified R6N trajectories.

| layer | mean time | median time |
| --- | ---: | ---: |
| factor graph build | 4.94 ms | 4.59 ms |
| BP recurrence | 596.42 ms | 560.23 ms |
| posterior-LLR MWPM + scoring | 1.37 ms | 0.93 ms |

The recurrence accounts for 99.0% of this Python-table pipeline; mean BP iterations are 24.50.

## cProfile cumulative-time excerpt

```text
         8463266 function calls in 11.925 seconds

   Ordered by: cumulative time
   List reduced from 26 to 20 due to restriction <20>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       20    3.045    0.152   11.924    0.596 d4_local_bp.py:102(run_sum_product)
   246960    2.849    0.000    4.600    0.000 d4_local_bp.py:85(_factor_message)
   743040    1.966    0.000    3.753    0.000 d4_local_bp.py:69(normalise)
  1236960    1.877    0.000    1.877    0.000 {method 'reduce' of 'numpy.ufunc' objects}
   743040    0.297    0.000    1.644    0.000 {method 'sum' of 'numpy.ndarray' objects}
   493920    0.346    0.000    1.593    0.000 fromnumeric.py:2692(max)
   743040    0.172    0.000    1.347    0.000 _methods.py:47(_sum)
   493920    0.473    0.000    1.247    0.000 fromnumeric.py:71(_wrapreduction)
   506160    0.267    0.000    0.267    0.000 {method 'copy' of 'numpy.ndarray' objects}
   743043    0.143    0.000    0.143    0.000 {built-in method numpy.asarray}
   246960    0.127    0.000    0.127    0.000 {method 'astype' of 'numpy.ndarray' objects}
   246960    0.104    0.000    0.104    0.000 {method 'reshape' of 'numpy.ndarray' objects}
   494900    0.071    0.000    0.071    0.000 {method 'items' of 'dict' objects}
   493920    0.059    0.000    0.059    0.000 {built-in method builtins.max}
   493920    0.046    0.000    0.046    0.000 fromnumeric.py:2687(_max_dispatcher)
   246960    0.032    0.000    0.032    0.000 {built-in method builtins.len}
   246960    0.029    0.000    0.029    0.000 multiarray.py:892(bincount)
    10080    0.011    0.000    0.015    0.000 numeric.py:274(full)
       20    0.003    0.000    0.005    0.000 d4_local_bp.py:77(_incidences)
    10100    0.003    0.000    0.003    0.000 {built-in method numpy.empty}
```

This profile identifies prototype implementation cost only. It does not extrapolate the measured Python ratio to an optimized dense, Numba, JAX, or GPU recurrence.

