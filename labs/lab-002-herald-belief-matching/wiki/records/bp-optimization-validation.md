---
title: 'BP optimization validation'
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

# BP optimization validation

The dense-array Numba kernels preserve the frozen decoder outputs exactly on
eight representative observations per lattice spanning $p=0.08$ through
$p=0.20$. Marginals are bit-identical, corrections match exactly, and the
iteration, convergence, and memory-candidate metadata are unchanged.

At $L=5$, $p=0.14$, after JIT warm-up, legacy decoding changes from 72.5 ms
to 0.839 ms per square observation and from 127.0 ms to 1.423 ms per
honeycomb observation. Memory-assisted decoding changes from 254.4 ms to
13.2 ms on square and from 644.9 ms to 30.8 ms on honeycomb. These are
86--89 times and 19--21 times faster, respectively.

The final six-cell, 6000-observation matched study completed in 60.8 seconds
with four worker processes on its first registered run. A deterministic
regeneration took 67.8 seconds and reproduced the scientific counts.

The compatible runtime is inherited rather than installed into this project:

```bash
PYTHONPATH=.tmp/numba-runtime:labs/lab-002-herald-belief-matching/scripts \
MPLCONFIGDIR=/tmp/matplotlib-herald \
NUMBA_CACHE_DIR=.tmp/numba-cache \
/Users/home/Documents/GitHub/emergent_classicality/lab/.venv/bin/python3
```

No project dependency metadata or environment was modified. The ordinary
project runtime continues to use the exact Python fallback when compatible
Numba is unavailable.

