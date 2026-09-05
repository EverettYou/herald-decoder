# Plan — Square-lattice string-herald decoder

## Motivation

Establish a minimal, operational model and test the first local use of herald information before choosing a global decoder or making a phase-diagram claim. The ordinary surface-code baseline is a square lattice with binary link errors and vertex-parity checks. The enrichment is an independently sampled internal-string herald.

## Lab boundary

This Lab owns the configuration generator, visualization, local Stage 1 demonstration, and the already-established syndrome-only Stage 2 display. It does not own posterior inference, belief propagation, PyMatching reweighting, decoder benchmarks, or exact logical-posterior comparisons. Those form the independent experiment in [Lab 002](../lab-002-herald-belief-matching/PLAN.md). No new belief-matching pipeline code or numerical benchmark should be added here.

## Model

Use an open \(L\times L\) square lattice with smooth boundaries at the top and bottom and rough boundaries at the left and right. Each link \(e\) holds an error bit \(x_e\in\{0,1\}\), sampled independently with

\[
\Pr(x_e=1)=p.
\]

Restrict \(p\in[0,1/2]\). The endpoint \(p=1/2\) is maximal decoherence, and \(p\) and \(1-p\) are equivalent under a global relabeling of the binary link variable, so values above \(1/2\) introduce no distinct noise regime.

At each vertex \(v\), let \(d_v=\sum_{e\ni v}x_e\), summing only the links present at that boundary vertex. The ordinary syndrome is

\[
s_v=d_v\bmod 2.
\]

Odd parity produces a syndrome. A simple string endpoint has \(d_v=1\) and is excluded from herald sampling. Every vertex with two or more incident error bonds is herald-eligible, independently drawing

\[
h_v\sim\operatorname{Bernoulli}(q),\qquad h_v\text{ is defined only when }d_v\ge2.
\]

In this first lab, the herald is the extra observable associated with multiple incident error bonds, and it does not alter the link noise. The intended SU(2)-motivated special value is \(q=3/4\), but the implementation treats \(q\) as a freely tunable parameter. Because syndrome records odd parity while herald eligibility records \(d_v\ge2\), a branching vertex with \(d_v=3\) can carry both messages simultaneously.

### Terminology boundary: the herald is not an erasure

Throughout this Lab, an unqualified **herald** means a fusion-remnant witness: extra vertex information left by the local fusion or cancellation of syndrome/anyon excitations. It does not mean a heralded atom loss, data-qubit loss, or known edge erasure. The link variables remain present and are sampled by the ordinary bit-flip rate \(p\); observing \(h_v=1\) does not erase any of them.

This distinction changes the decoder interface. A quantum-erasure decoder receives an explicit set of erased data-qubit or edge locations. Here \(h_v\) is a vertex factor correlated with the joint incident pattern \(\{x_e:e\ni v\}\): it witnesses \(d_v\ge2\) in the ideal eligibility model, but does not identify which incident edges carry the string. Treating all edges adjacent to a herald as erased would inject location information that was never observed and would discard the incident-degree/fusion constraint that defines the model. Erasure decoders remain comparison literature, not the default decoder for Lab 001. When this Lab discusses the conventional meaning, it uses the qualified terms **erasure herald** or **loss herald**.

## Stage 1 — predecoding

Let \(\operatorname{dist}_G(u,v)\) be graph distance on the selected lattice, and let \(P(u,v)\) be one deterministic shortest path. Stage 1 applies three local rules in order:

1. Take a snapshot of the current herald set, form every herald pair with \(\operatorname{dist}_G(u,v)=1\), add the edge in each \(P(u,v)\) to the correction, then consume every herald touched by at least one pair. A herald may participate in multiple distance-one paths within this synchronous step.
2. Using only the heralds still remaining, if a herald has exactly two adjacent syndrome vertices, add the two-edge syndrome–herald–syndrome path to the correction and consume the central herald.
3. Take a new snapshot of only the remaining heralds, form every pair with \(\operatorname{dist}_G(u,v)=2\), add both edges in each \(P(u,v)\) to the correction, then consume every herald touched by at least one pair. A herald may likewise participate in multiple distance-two paths within this synchronous step.

Consumption happens only at the end of each rule step. It removes a touched herald signal from every later rule and from the Stage 1 display; it does not remove the underlying lattice vertex and does not suppress another path proposed from the same step snapshot. Corrections are binary, so the three rule outputs combine by symmetric difference: applying the same edge in different rule outputs cancels. Sorted vertex order and lexicographically ordered breadth-first search make tied shortest paths reproducible. Rule 3 deliberately does nothing when a herald has fewer or more than two adjacent syndromes, since no pairing convention has been chosen for that case.

Write the Stage 1 correction as \(c^{(1)}\). Its residual error and measured residual syndrome are

\[
r^{(1)}=x\oplus c^{(1)},
\qquad
\tilde s^{(1)}=H r^{(1)}\oplus m.
\]

## Stage 2 — PyMatching MWPM

After Stage 1, discard every herald that remains; Stage 2 sees only \(\tilde s^{(1)}\). Build the binary check matrix \(H\) with one row per detector vertex and one column per correctable lattice edge. The Lab-owned `scripts/mwpm_decoder.py` imports PyMatching, constructs `pymatching.Matching` from this sparse matrix, and asks it for the minimum-weight correction \(c^{(2)}\). The dashboard only transports the request to this Lab entry point. All current link priors are identical, so unit edge weights give the same minimum-length ordering as any common positive log-likelihood weight for \(0<p<1/2\).

PyMatching interprets a check-matrix column containing two ones as an edge between two detectors, and a column containing one one as an edge to a boundary. The viewer passes the rough-side vertices explicitly as `boundary_vertices`; the Lab decoder accepts a singleton column only when its non-detector endpoint belongs to that set. It rejects a zero column, because an edge with no incident check would be the missing outward side of an open plaquette rather than a physical data edge. The implementation uses `use_virtual_boundary_node=True`, the mode recommended in the [PyMatching API documentation](https://pymatching.readthedocs.io/en/stable/api.html#pymatching.Matching.from_check_matrix).

The plaquettes on the left and right rough boundaries are open. On the square lattice, each such plaquette retains its inner vertical edge and its two horizontal edges, but its outer vertical edge is absent. Vertices on that open side carry no stabilizer and are omitted from the detector rows of \(H\). A retained horizontal edge joining an open-side vertex to an interior detector therefore has a singleton column, so Stage 2 can match a residual syndrome to the physical rough boundary. Vertices on the top and bottom smooth boundaries remain detectors except at the rough-boundary corners. The honeycomb uses the same rough-side rule, while its top and bottom smooth boundaries are the retained armchair-shaped outer lattice chains. No extra straight boundary edge or thick guide is added.

The final correction and residual are

\[
c=c^{(1)}\oplus c^{(2)},
\qquad
r^{(2)}=x\oplus c^{(1)}\oplus c^{(2)}.
\]

For visualization, compare the underlying error \(x_e\) with the predicted correction \(c_e\):

- red: \((x_e,c_e)=(1,0)\), an unmatched true error;
- green: \((x_e,c_e)=(1,1)\), a matched correction;
- purple: \((x_e,c_e)=(0,1)\), a false correction.

Logical failure and threshold estimation are deferred until the boundary and logical-observable conventions are specified.

The interactive result has a master Decoder switch and three Decoder On views. `Stage 1` compares \(x\) with \(c^{(1)}\) and shows only unconsumed heralds that still have at least two incident residual bonds. `Stage 2` treats \(r^{(1)}\) as its input, compares it with \(c^{(2)}\), and shows no heralds. `Combined`, the default Decoder On view, compares \(x\) with \(c^{(1)}\oplus c^{(2)}\) and also shows no heralds. `Decoder Off` displays \(x\), its measured syndrome, and the initially sampled heralds. The Results view rotates both lattices by \(90^\circ\), placing rough boundaries at the top and bottom and smooth boundaries at the left and right; this is a display transform only and does not change \(H\).

## Rough-boundary logical check and live statistics

An error string can terminate on the two rough boundaries. A transverse logical check therefore runs from the top smooth boundary to the bottom smooth boundary. Choose a dashed path \(\Gamma_R\) through the centers of the right-hand column of open plaquettes and extend it beyond both smooth boundaries. Let \(C_{\Gamma_R}\) be the retained data edges crossed by this path. On the square lattice these are the horizontal edges connecting the right open-side vertices to the adjacent detector column. On the honeycomb they are found by the geometric intersections of the center path with the retained polygon edges. For the error configuration \(r\) shown in the current view, define

\[
\lambda_R(r)=\sum_{e\in C_{\Gamma_R}}r_e\pmod 2.
\]

The viewer reports `logical error` exactly when \(\lambda_R=1\). Decoder Off evaluates \(x\), Stage 1 evaluates \(r^{(1)}\), and Stage 2 and Combined evaluate \(r^{(2)}\). After the display rotation, this dashed path is horizontal and extends beyond the left and right smooth boundaries. It is a logical-check guide, not a physical data edge.

The live statistics use the currently displayed residual state:

\[
\rho_e=\frac{|r|}{|E|},\qquad
\rho_s=\frac{|\tilde s(r)|}{|V_{\rm det}|},\qquad
\rho_h=\frac{|h_{\rm shown}|}{|V_{\rm det}|}.
\]

Here \(E\) includes all retained data edges; the missing open side of a rough plaquette is not an edge and is not sampled. Rough-boundary outer vertices are excluded from the syndrome and herald denominators because they have no stabilizer.

## Honeycomb variant

The second visualization uses a trivalent honeycomb graph with the same binary edge variables. For each vertex,

\[
d_v=\sum_{e\ni v}x_e\in\{0,1,2,3\},
\qquad s_v=d_v\bmod2.
\]

Parity readout has an independent binary measurement error

\[
m_v\sim\operatorname{Bernoulli}(p_m),
\qquad \tilde s_v=s_v\oplus m_v,
\qquad p_m\in[0,1/2].
\]

First sample the underlying herald content

\[
h_v^{\rm true}=\begin{cases}
\operatorname{Bernoulli}(q), & d_v\ge2,\\
0, & d_v<2.
\end{cases}
\]

Herald extraction has a separate one-way loss channel

\[
\ell_v\sim\operatorname{Bernoulli}(p_h),
\qquad
h_v^{\rm obs}=h_v^{\rm true}(1-\ell_v).
\]

Thus \(p_m\) flips the parity/syndrome readout in either direction, while \(p_h\) only removes an underlying herald and never creates a false herald. The current baseline is \(p_m=p_h=0\), but both parameters remain exposed for later measurement-error studies.

Therefore the noiseless message content is:

| Incident count \(d_v\) | True parity \(s_v\) | Underlying herald eligibility |
| --- | --- | --- |
| 0 | 0 | no |
| 1 | 1 | no |
| 2 | 0 | yes, observed with probability \(q\) |
| 3 | 1 | yes, observed with probability \(q\) |

The unified visualization shows measured parity \(\tilde s_v\) and observed herald \(h_v^{\rm obs}\) directly. Measurement errors receive no auxiliary glyph: changing \(p_m\) changes which syndrome markers appear, and changing \(p_h\) changes which herald markers remain visible.

## Question and hypothesis

How much of the error is removed by herald-assisted predecoding before a syndrome-only MWPM completion?

Hypothesis: distance-one herald pairs provide the highest-confidence corrections, syndrome–herald–syndrome patterns recover additional local segments, and distance-two herald pairs extend the remaining local information across one intermediate vertex. At \(q=0\), Stage 1 is empty and the combined decoder reduces exactly to syndrome-only PyMatching on the same graph.

## Deliverables

1. A deterministic sampled configuration with distinct unmatched errors, matched corrections, false corrections, syndrome markers, and herald markers.
2. A tested local decoder implementing the three ordered local rules, plus a tested PyMatching check-matrix endpoint.
3. One interactive renderer with a square/honeycomb lattice choice, open rough plaquettes, a smooth-to-smooth logical-check guide through right open-plaquette centers, live densities, and shared \(p\), \(p_m\), \(q\), \(p_h\), \(L\), decoder-state, and stage-view controls.
4. Explicit limiting-case checks; no decoder threshold is claimed in this Lab.

## Observables and comparisons

| Observable | \(q=0\) | \(q>0\) |
| --- | --- | --- |
| Link-error realization (hidden to a decoder) | sampled with \(p\) | sampled with \(p\) |
| Vertex syndrome \(s_v\) | observed | observed |
| Internal herald \(h_v\) | absent | observed on a subset of \(d_v\ge2\) vertices |

Any later matched logical-error comparison belongs to [Lab 002](../lab-002-herald-belief-matching/PLAN.md), which uses the observation and boundary conventions frozen here.

## Stop conditions and completion criteria

Lab 001 is complete once both decoder stages, the rough/smooth boundary convention, the right-boundary logical observable, and their separate/combined residual semantics are visually checkable and their limiting cases have unit tests. Ensemble LER, threshold estimation, and phase-diagram work are explicitly outside this Lab and are handed to Labs 002–003.
