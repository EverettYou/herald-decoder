---
title: Exact frontier transfer and controlled MPS contraction
page_type: method
status: current
updated: 2026-10-01
topics:
  - Decoding Algorithms
source_refs:
  - results/validation.json
idea_ids: []
---

# Exact frontier transfer and controlled MPS contraction

## Summary

Frontier transfer supplies a width-limited exact posterior; finite-bond MPS is a separately labeled approximation.

## Evidence

The [cross-backend and bond-sensitivity checks](../results/validation.json) measure their finite-size agreement and truncation behavior.

## Status

Current within recorded width, memory, and bond-dimension limits.

## Related pages

- [[planar-ml|Planar sector solver]]
- [[comparison|Decoder comparison]]

## Independent tensor network

Assign each edge its two-state prior, and each detector the tensor

$$
T_v(x_{\partial v})=1\{\sum x_e\bmod2=s_v\}\phi_q(h_v,\sum x_e).
$$

Rough vertices carry the identity factor. Contract the network while retaining a two-state logical accumulator. An occupied edge in the package logical mask toggles that accumulator when the edge closes. This computes absolute $(Z_0,Z_1)$ directly, without a reference matching graph or a Pfaffian orientation. It also supports the package square geometry, whose degree-four tensors are generally not matchgates.

## Exact frontier transfer

Visit vertices in a geometry-based column sweep. Introduce each edge with its prior at its first endpoint, multiply the detector tensor when all its incident bits are available, then sum closing edges. With frontier width $w$, state size is $2^{w+1}$ per shot, and cost is exponential in width rather than total area. Normalize after every vertex and accumulate the log record probability. All states are nonnegative, but severe underflow can still occur; zero/nonfinite normalization raises a numerical error.

`HeraldTransferMLDecoder` caps width at 18 by default and the principal state array at 256 MiB. Temporary arrays also occupy memory; this cap is not a total process-memory promise. Large batches must be split. The batch path vectorizes records with the same topology. This method is a small/medium-width exact oracle, not a scalable solution for arbitrary $L$. Its exactness does not require planarity or a free-fermion identity. The current forest representative does require accessible rough boundaries and the package logical path.

## Column MPS approximation

The honeycomb column construction combines a pair of detector columns into an MPO with virtual bond dimension two. Its two detector tensors encode the exact parity and herald likelihood; its edge priors are placed once on incoming, internal and vertical links. The right boundary is contracted with a two-state parity accumulator, then translated to the package absolute sector using a syndrome-compatible reference. Edge-coverage checks reject a mismatched column construction.

Store the frontier vector as an MPS with physical dimension two. Applying a column MPO grows the virtual bonds. Sweep QR to canonicalize, then SVD in the opposite direction and retain at most $\chi$ singular values per bond. Renormalize each column and retain discarded-weight diagnostics. Storage is approximately $O(L\chi^2)$ per record and dense SVD work typically scales as $O(L^2\chi^3)$ over the sweep, with constants and actual ranks affecting runtime. Batched QR/SVD vectorizes independent records.

Finite $\chi$ is approximate even if sampled decisions happen to agree with exact ML. The summed relative discarded singular-value weight is a diagnostic, not a certified bound on the final posterior ratio, Bayes risk or threshold. In particular, a small absolute contraction error can matter when sector sums are small or nearly tied. Increase $\chi$, compare posteriors and conditional regret, and use exact transfer/planar inference when available. Negative sector sums beyond roundoff or failed decompositions raise errors rather than being reported as valid probabilities.

[Bravyi, Suchara and Vargo](https://arxiv.org/abs/1405.4883) develops tensor-network ML decoding and controlled approximations; the particular column implementation here uses this lab's binary site law. Both methods return sector-equivalent forest corrections; herald compatibility of those representatives is not an output requirement. The [source API](../../../src/herald_decoder/README.md) documents width, memory, $\chi$ and batch contracts.

## What this lab verifies

Exact whole-error enumeration at size two and transfer comparisons through size five check the mapping. $\chi=4$ produces visible posterior errors in the sampled size-five records; $\chi=16$ agrees there to roundoff. The new size-nine matched records are also compared against planar ML. No observed decision changes in one cohort imply neither all-record exactness nor large-size convergence. See [comparison](comparison.md) and [validation](../results/validation.json).

## Full-prior update

The domain is p in [0,1]. Deterministic p=1 records are supported and impossible records rejected. The herald planar/MPS wrappers also use the width-capped exact transfer fallback when 1−10^{-12}<p<1. Literal transfer priors are (1−p,p); no complement folding is used.
