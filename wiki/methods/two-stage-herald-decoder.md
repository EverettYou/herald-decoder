---
title: Two-stage herald decoder
page_type: method
status: implemented-demonstration
updated: 2026-08-26
source_refs:
  - labs/lab-001-string-herald-visualization/scripts/local_decoder.py
  - labs/lab-001-string-herald-visualization/scripts/mwpm_decoder.py
  - labs/lab-001-string-herald-visualization/REPORT.md
idea_ids: []
topics: [Quantum Error Correction, Decoding Algorithms]
---

# Two-stage herald decoder

**Summary**: The two-stage herald decoder is Lab 001's named configuration-level baseline: it first applies deterministic local rules to the observed herald field, then delegates the remaining syndrome to PyMatching minimum-weight perfect matching (MWPM). It is a demonstrator of how heralds can be consumed as hard evidence, not a posterior-optimal decoder.

**Sources**: [Lab 001: string-herald visualization](/lab?id=lab-001-string-herald-visualization); [PyMatching Decoder](/reference?id=pymatching-code)

**Last updated**: 2026-08-26

## Input and output

The decoder accepts a lattice graph and the simultaneous record $(\tilde S,H)$. It returns a binary correction $c\subseteq E$; the residual is $r=x\oplus c$ in simulation. In experiment, $x$ is latent, so only syndrome faithfulness and a logical observable can be checked directly.

## Stage 1: local herald rules

Stage 1 forms a correction $c^{(1)}$ by applying three deterministic rules in order, consuming every herald that participates:

1. from one snapshot, connect every herald pair at graph distance one, then consume all heralds touched by that parallel update;
2. for each still-remaining herald with exactly two adjacent syndrome vertices, join those two vertices through that herald and consume the center;
3. from a new snapshot of remaining heralds, connect every pair at graph distance two, then consume all heralds touched by that parallel update.

Within either distance step, one herald may support multiple paths; consumption does not occur until every qualifying pair in that step has been evaluated. Shortest paths and tie-breaking are deterministic. The binary rule outputs combine by symmetric difference, so repeated correction edges across rule outputs cancel. The resulting residual syndrome is

\[
\tilde s^{(1)}=H\bigl(x\oplus c^{(1)}\bigr)\oplus m.
\]

This stage uses the herald as a local hard constraint and intentionally ignores unmatched or ambiguous herald patterns. [Lab 001 plan, Stage 1](../../labs/lab-001-string-herald-visualization/PLAN.md#stage-1--predecoding) [Local decoder, `decode_local`](../../labs/lab-001-string-herald-visualization/scripts/local_decoder.py#decode_local)

## Stage 2: syndrome-only MWPM

All remaining heralds are discarded before Stage 2. PyMatching receives the sparse detector-by-edge matrix and $\tilde s^{(1)}$, producing $c^{(2)}$. Singleton columns are allowed only for retained edges adjacent to explicitly declared rough-boundary vertices, where they represent a match to the virtual boundary. The final correction is

\[
c=c^{(1)}\oplus c^{(2)}.
\]

This division makes the interface clear: Stage 1 is Lab-owned heuristic inference; Stage 2 uses a mature MWPM implementation and does not claim to implement matching itself. [MWPM adapter](../../labs/lab-001-string-herald-visualization/scripts/mwpm_decoder.py) [Lab 001 report, Evidence](../../labs/lab-001-string-herald-visualization/REPORT.md#evidence)

## Evidence boundary

Unit tests cover the local rule order, path consumption, boundary columns, and syndrome-faithful matching behavior. These are implementation invariants. The interactive viewer shows individual configurations, but neither it nor this method page establishes a threshold or a statistical advantage from heralds.

## Related pages

- [[concepts/error-correction-decoding|Error-correction decoding]]
- [[models/string-herald-simulator|String-herald simulator model]]
- [[methods/herald-aware-belief-matching|Herald-aware belief matching]]
- [[methods/surface-code-decoding-baselines|Surface-code decoding baselines]]
