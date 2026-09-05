# Herald Decoder program gates

This is a routing aid. Read the live [project thesis](../../../wiki/thesis.md),
[program-level roadmap](../../../wiki/questions/program-level-scientific-roadmap.md),
relevant Wiki method/model pages, and owning lab before acting. If they differ
from this file, the Wiki and current evidence win.

## Central question

The program asks whether symmetry/fusion-resolved information changes the
recoverability of topological quantum memory and whether a physically available
record can support a more capable practical decoder. Improving one decoder's
finite-size logical error rate is supporting evidence, not the full question.

## Scientific chain

Place each task in one or more layers:

1. **Physical information structure:** derive the microscopic error and
   measurement channel and specify what is operationally observed.
2. **Intrinsic recoverability:** quantify the optimal information-theoretic or
   exact Bayes limit conditioned on each nested observation record.
3. **Scalable decoding:** measure the algorithmic gap between practical
   decoders and the intrinsic limit under the same record.
4. **Transition theory:** derive a decoder-independent recoverability quantity,
   scaling theory, order parameter, or statistical-mechanics mapping before
   claiming an asymptotic phase transition or universality.
5. **Fault tolerance:** introduce noisy repeated measurements, causal spacetime
   records, adaptive decisions, and threshold surfaces.
6. **Physical realization and resources:** connect the record and protocol to
   a concrete platform, including measurement count, latency, feed-forward,
   and matched resource comparison.

The preferred program order is not rigidly linear, but a downstream claim
cannot repair a missing upstream definition.

## Project-wide hard gates

### Physical observation gate

Every decoder input must have a physical or explicitly phenomenological
generation rule. Distinguish current local measurement records from erasure
flags, hidden histories, fusion trees, worldlines, or pairing oracles. State
which information is inaccessible.

### Information-budget gate

Compare nested records such as syndrome-only, compressed herald, allowed local
fusion outcomes, and richer oracle records. Under optimal inference, enlarging
the record cannot worsen Bayes risk; a violation indicates a simulator,
likelihood, or inference defect.

### Matched-comparison gate

Decoder comparisons must use the same physical noise model, code family,
observation record, sampling design, and evaluation definition unless the
difference is the explicit scientific variable. Separate information gain from
algorithmic gain.

### Exact-or-limiting-case gate

Before trusting a scalable heuristic, test small systems, exact enumeration,
known limits, identities, conservation laws, or independently derived results.
The relevant comparator may be an exact posterior, a tensor contraction, or a
small-system oracle; label optimization or MILP surrogates separately from
Bayesian optimality.

### Transition-claim gate

Finite-size crossings, smoothed phase maps, or decoder-specific trends are not
by themselves thermodynamic transitions. An asymptotic claim needs a principled
observable, scaling hypothesis, uncertainty analysis, robustness to decoder
limitations, and evidence that convergence/censoring does not create the trend.

### Fault-tolerance gate

A perfect single-round observation study cannot support a fault-tolerant claim.
Specify readout noise, repeated rounds, causal availability, hidden internal
charge, and recovery timing before extrapolating to operational memory.

### Program-value gate

Ask whether the next computation can falsify the central mechanism or separate
intrinsic information gain from decoder optimization. Maintenance of a pilot
figure is appropriate when needed for communication, but it must not displace a
higher-information program gate without an explicit reason.

## Current work-package ownership

- Lab 003: phenomenological finite-window phase evidence and presentation;
  useful as a pilot, not the scientific center.
- Lab 004: D4 physical observation channel, published decoder reproduction,
  exact/small-system conditioned optimum, then matched scalable comparison.
- Lab 005: noisy spacetime records and just-in-time anyonic decoding.

Re-read `labs/labs.json` because ownership and priorities may change.
