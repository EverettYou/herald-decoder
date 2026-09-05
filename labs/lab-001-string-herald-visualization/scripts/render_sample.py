#!/usr/bin/env python3
"""Render one sampled square-lattice error configuration as a self-contained SVG."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from local_decoder import decode_local, logical_parity, residual_state


def sample_edges(size: int, p: float, rng: random.Random) -> set[tuple[tuple[int, int], tuple[int, int]]]:
    edges = set()
    for y in range(size):
        for x in range(size):
            if x + 1 < size and rng.random() < p:
                edges.add(((x, y), (x + 1, y)))
            if y + 1 < size and 0 < x < size - 1 and rng.random() < p:
                edges.add(((x, y), (x, y + 1)))
    return edges


def incident_counts(size: int, edges: set[tuple[tuple[int, int], tuple[int, int]]]) -> dict[tuple[int, int], int]:
    counts = {(x, y): 0 for y in range(size) for x in range(size)}
    for a, b in edges:
        counts[a] += 1
        counts[b] += 1
    return counts


def render(size: int, p: float, pm: float, q: float, ph: float, seed: int, output: Path) -> None:
    rng = random.Random(seed)
    edges = sample_edges(size, p, rng)
    counts = incident_counts(size, edges)
    measurement_flips: set[tuple[int, int]] = set()
    observed_syndromes: set[tuple[int, int]] = set()
    underlying_heralds: set[tuple[int, int]] = set()
    observed_heralds: set[tuple[int, int]] = set()
    for vertex, degree in counts.items():
        if vertex[0] in {0, size - 1}:
            continue
        measurement_flip = rng.random() < pm
        herald_draw = rng.random() < q
        herald_loss = rng.random() < ph
        if measurement_flip:
            measurement_flips.add(vertex)
        if bool(degree % 2) != measurement_flip:
            observed_syndromes.add(vertex)
        if degree >= 2 and herald_draw:
            underlying_heralds.add(vertex)
            if not herald_loss:
                observed_heralds.add(vertex)
    predicted, consumed_heralds = decode_local(size, observed_syndromes, observed_heralds)
    residual, true_residual_syndromes, remaining_heralds = residual_state(
        size, edges, predicted, observed_heralds - consumed_heralds
    )
    detector_vertices = {vertex for vertex in counts if vertex[0] not in {0, size - 1}}
    residual_syndromes = (true_residual_syndromes ^ measurement_flips) & detector_vertices
    residual_logical_parity = logical_parity(residual, size)

    step, margin = 64, 64
    width = height = 2 * margin + step * (size - 1)
    pos = lambda v: (margin + step * v[1], margin + step * (size - 1 - v[0]))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-labelledby="title desc">' % (width, height, width, height),
        '<title id="title">Residual configuration after local herald-assisted correction</title>',
        '<desc id="desc">The lattice is rotated so the open rough plaquettes are at the top and bottom and the smooth boundaries are at the left and right. A horizontal dashed line through one row of open-plaquette centers extends beyond the smooth boundaries and defines the logical parity. Red bonds are unmatched residual errors, green bonds are resolved errors, and purple bonds are false corrections. Gold circles and blue diamonds are recomputed residual syndromes and unresolved heralds. Logical parity is %d.</desc>' % residual_logical_parity,
        '<rect width="100%" height="100%" fill="#fffdf8"/>',
        '<style>text{font-family:ui-sans-serif,system-ui,sans-serif;fill:#1f2937}.edge{stroke:#cbd5e1;stroke-width:2}.logical{stroke:#0f766e;stroke-width:2.2;stroke-dasharray:7 6}.miss{stroke:#e4572e}.match{stroke:#188f65}.false{stroke:#8b5cf6}.decoded{stroke-width:8;stroke-linecap:round}.v{fill:#334155}.syndrome{fill:#fbbf24;stroke:#7c4a03;stroke-width:2}.herald{fill:#2563eb;stroke:#172554;stroke-width:2}.small{font-size:13px}</style>',
    ]
    for y in range(size):
        for x in range(size):
            if x + 1 < size:
                a, b = pos((x, y)), pos((x + 1, y))
                lines.append('<line class="edge" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (*a, *b))
            if y + 1 < size and 0 < x < size - 1:
                a, b = pos((x, y)), pos((x, y + 1))
                lines.append('<line class="edge" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (*a, *b))
    logical_y = margin + .5 * step
    lines.append('<line class="logical" x1="%g" y1="%g" x2="%g" y2="%g"/>' % (margin - .65 * step, logical_y, margin + (size - .35) * step, logical_y))
    for a, b in set(edges) | predicted:
        pa, pb = pos(a), pos(b)
        state = "match" if (a, b) in edges and (a, b) in predicted else "miss" if (a, b) in edges else "false"
        lines.append('<line class="decoded %s" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (state, *pa, *pb))
    for vertex in counts:
        if vertex not in detector_vertices:
            continue
        x, y = pos(vertex)
        has_syndrome = vertex in residual_syndromes
        if has_syndrome:
            lines.append('<circle class="syndrome" cx="%d" cy="%d" r="10"/>' % (x, y))
        else:
            lines.append('<circle class="v" cx="%d" cy="%d" r="3.5"/>' % (x, y))
        if vertex in remaining_heralds:
            hx, hy, radius = (x + 10, y - 10, 9) if has_syndrome else (x, y, 13)
            lines.append('<path class="herald" d="M %d %d L %d %d L %d %d L %d %d Z"/>' % (hx, hy - radius, hx + radius, hy, hx, hy + radius, hx - radius, hy))
    legend_y = height - 18
    lines.extend([
        '<line class="decoded miss" x1="18" y1="%d" x2="38" y2="%d"/><text class="small" x="44" y="%d">residual</text>' % (legend_y - 5, legend_y - 5, legend_y),
        '<line class="decoded match" x1="110" y1="%d" x2="130" y2="%d"/><text class="small" x="136" y="%d">resolved</text>' % (legend_y - 5, legend_y - 5, legend_y),
        '<line class="decoded false" x1="190" y1="%d" x2="210" y2="%d"/><text class="small" x="216" y="%d">correction</text>' % (legend_y - 5, legend_y - 5, legend_y),
        '<circle class="syndrome" cx="330" cy="%d" r="8"/><text class="small" x="344" y="%d">syndrome</text>' % (legend_y - 5, legend_y),
        '<path class="herald" d="M 440 %d L 448 %d L 440 %d L 432 %d Z"/><text class="small" x="454" y="%d">herald</text>' % (legend_y - 13, legend_y - 5, legend_y + 3, legend_y - 5, legend_y),
        '</svg>',
    ])
    output.write_text("\n".join(lines), encoding="utf-8")
    matched = len(edges & predicted)
    herald_losses = len(underlying_heralds - observed_heralds)
    print(f"{output}: {len(edges)} errors, {len(predicted)} corrections, {matched} resolved, {len(residual)} residual bonds, {len(residual_syndromes)} measured residual syndromes, logical parity {residual_logical_parity}, {len(remaining_heralds)} unresolved heralds, {herald_losses} herald losses")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=9)
    parser.add_argument("--p", type=float, default=0.12)
    parser.add_argument("--pm", type=float, default=0.0)
    parser.add_argument("--q", type=float, default=0.75)
    parser.add_argument("--ph", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--output", type=Path, default=Path("figures/sample-configuration.svg"))
    args = parser.parse_args()
    if args.size < 2 or not 0 <= args.p <= 0.5 or not 0 <= args.pm <= 0.5 or not 0 <= args.q <= 1 or not 0 <= args.ph <= 1:
        parser.error("size must be >= 2; p and pm must lie in [0, 1/2]; q and ph must lie in [0, 1]")
    render(args.size, args.p, args.pm, args.q, args.ph, args.seed, args.output)


if __name__ == "__main__":
    main()
