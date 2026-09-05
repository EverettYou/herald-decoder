#!/usr/bin/env python3
"""Render the matched seed-1 q ablation used in the Lab 001 report."""

from __future__ import annotations

import argparse
from pathlib import Path

from local_decoder import lattice_edges, logical_boundary_edges, predecode_payload
from mwpm_decoder import mwpm_decode


class Lcg:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / 4294967296


def sample(size: int, p: float, q: float, pm: float, ph: float, seed: int):
    rng = Lcg(seed)
    edges = lattice_edges(size)
    error_indices = {index for index in range(len(edges)) if rng.random() < p}
    degree = {(x, y): 0 for y in range(size) for x in range(size)}
    for index in error_indices:
        a, b = edges[index]
        degree[a] += 1
        degree[b] += 1

    syndromes: set[tuple[int, int]] = set()
    heralds: set[tuple[int, int]] = set()
    for y in range(size):
        for x in range(1, size - 1):
            measurement_flip = rng.random() < pm
            herald_draw = rng.random() < q
            herald_loss = rng.random() < ph
            if bool(degree[(x, y)] % 2) != measurement_flip:
                syndromes.add((x, y))
            if degree[(x, y)] >= 2 and herald_draw and not herald_loss:
                heralds.add((x, y))
    return edges, error_indices, syndromes, heralds, degree


def decode(size: int, edges, error_indices, syndromes, heralds):
    to_id = lambda vertex: vertex[1] * size + vertex[0]
    indexed_edges = [[to_id(a), to_id(b)] for a, b in edges]
    detectors = [to_id((x, y)) for y in range(size) for x in range(1, size - 1)]
    stage_one = predecode_payload(
        {
            "vertex_count": size * size,
            "edges": indexed_edges,
            "detector_vertices": detectors,
            "syndromes": sorted(to_id(vertex) for vertex in syndromes),
            "heralds": sorted(to_id(vertex) for vertex in heralds),
        }
    )
    stage_one_correction = set(stage_one["correction_edge_indices"])
    stage_one_residual = error_indices ^ stage_one_correction
    stage_one_degree = {(x, y): 0 for y in range(size) for x in range(size)}
    for index in stage_one_residual:
        a, b = edges[index]
        stage_one_degree[a] += 1
        stage_one_degree[b] += 1
    residual_syndromes = {
        vertex
        for vertex, value in stage_one_degree.items()
        if 0 < vertex[0] < size - 1 and bool(value % 2)
    }
    matching = mwpm_decode(
        {
            "vertex_count": size * size,
            "edges": indexed_edges,
            "detector_vertices": detectors,
            "boundary_vertices": [to_id((x, y)) for y in range(size) for x in (0, size - 1)],
            "syndromes": sorted(to_id(vertex) for vertex in residual_syndromes),
        }
    )
    stage_two_correction = set(matching.get("correction_edge_indices", []))
    final_correction = stage_one_correction ^ stage_two_correction
    final_residual = error_indices ^ final_correction
    logical_edges = {
        edges.index(edge)
        for edge in logical_boundary_edges(size)
    }
    return {
        "stage_one": stage_one,
        "stage_one_correction": stage_one_correction,
        "stage_one_residual": stage_one_residual,
        "stage_one_syndromes": residual_syndromes,
        "stage_two_correction": stage_two_correction,
        "final_correction": final_correction,
        "final_residual": final_residual,
        "logical_parity": len(final_residual & logical_edges) % 2,
        "matching": matching,
        "logical_edges": logical_edges,
    }


def esc(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render(size: int, p: float, q_values: tuple[float, ...], pm: float, ph: float, seed: int, output: Path) -> None:
    if len(q_values) != 2:
        raise ValueError("the ablation renderer requires exactly two q values")
    panels = []
    for q in q_values:
        edges, errors, syndromes, heralds, degree = sample(size, p, q, pm, ph, seed)
        panels.append((q, edges, errors, syndromes, heralds, degree, decode(size, edges, errors, syndromes, heralds)))

    width, height = 980, 560
    panel_w, panel_h = 450, 440
    step, margin = 37, 54
    colors = {"edge": "#cbd5e1", "error": "#e4572e", "match": "#188f65", "false": "#8b5cf6", "syndrome": "#fbbf24", "herald": "#2563eb", "logical": "#0f766e"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Seed-1 herald ablation: q=1 versus q=0.75</title>',
        '<desc id="desc">Two square L=9 configurations share the same sampled error. The left panel observes all eligible heralds at q=1; the right panel misses one herald at q=0.75. Red is residual true error, green is a true error corrected, purple is a false correction, gold is a residual syndrome, and blue is an observed herald.</desc>',
        '<rect width="100%" height="100%" fill="#fffdf8"/>',
        '<style>text{font-family:ui-sans-serif,system-ui,sans-serif;fill:#172033}.title{font-size:22px;font-weight:700}.subtitle{font-size:14px;fill:#536661}.panel{fill:#fff;stroke:#dbe3e0}.edge{stroke:#cbd5e1;stroke-width:1.7}.active{stroke-width:6;stroke-linecap:round}.logical{stroke:#0f766e;stroke-width:2;stroke-dasharray:7 6}.syndrome{fill:#fbbf24;stroke:#7c4a03;stroke-width:1.5}.herald{fill:#2563eb;stroke:#172554;stroke-width:1.5}.herald.consumed{opacity:.35}.stat{font-size:12px;fill:#43544f}.stat strong{font-weight:800;fill:#173b36}.legend{font-size:12px;fill:#43544f}</style>',
        '<text class="title" x="24" y="32">Same sampled string, different herald record</text>',
        '<text class="subtitle" x="24" y="54">Square L=9 · p=0.20 · pₘ=pₕ=0 · seed=1 · Stage 1: H-H(d=1) → S-H-S → H-H(d=2)</text>',
    ]
    for panel_index, (q, edges, errors, syndromes, heralds, degree, result) in enumerate(panels):
        ox = 18 + panel_index * 480
        oy = 75
        lines.append(f'<rect class="panel" x="{ox}" y="{oy}" width="{panel_w}" height="{panel_h}" rx="10"/>')
        logical = "YES" if result["logical_parity"] else "NO"
        lines.append(f'<text class="title" x="{ox + 18}" y="{oy + 29}">q = {q:g}</text>')
        lines.append(f'<text class="subtitle" x="{ox + 100}" y="{oy + 29}">{"all eligible heralds" if q == 1 else "one eligible herald missing"}</text>')
        x0, y0 = ox + margin, oy + 73
        point = lambda vertex: (x0 + step * vertex[1], y0 + step * (size - 1 - vertex[0]))
        for edge in edges:
            a, b = point(edge[0]), point(edge[1])
            lines.append(f'<line class="edge" x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}"/>')
        logical_y = y0 + step * (size - 1 - (size // 2))
        lines.append(f'<line class="logical" x1="{x0 - 24}" y1="{logical_y}" x2="{x0 + step * (size - 1) + 24}" y2="{logical_y}"/>')
        final_correction = result["final_correction"]
        for index in sorted(errors | final_correction):
            edge = edges[index]
            a, b = point(edge[0]), point(edge[1])
            state = "match" if index in errors and index in final_correction else "error" if index in errors else "false"
            lines.append(f'<line class="active" stroke="{colors[state]}" x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}"/>')
        for vertex in sorted({(x, y) for y in range(size) for x in range(1, size - 1)}):
            x, y = point(vertex)
            if vertex in result["final_residual"]:
                pass
            residual_degree = sum(1 for index in result["final_residual"] if vertex in edges[index])
            if residual_degree % 2:
                lines.append(f'<circle class="syndrome" cx="{x}" cy="{y}" r="7"/>')
            else:
                lines.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#334155"/>')
            if vertex in heralds:
                consumed = vertex in {tuple(divmod(item, size)[::-1]) for item in result["stage_one"]["consumed_herald_vertices"]}
                radius = 9
                lines.append(f'<path class="herald{" consumed" if consumed else ""}" d="M {x} {y-radius} L {x+radius} {y} L {x} {y+radius} L {x-radius} {y} Z"/>')
        stage_one_count = len(result["stage_one_correction"])
        final_count = len(result["final_correction"])
        lines.extend([
            f'<text class="stat" x="{ox + 18}" y="{oy + 382}">errors <strong>{len(errors)}</strong> · heralds <strong>{len(heralds)}</strong> · Stage 1 corrections <strong>{stage_one_count}</strong></text>',
            f'<text class="stat" x="{ox + 18}" y="{oy + 402}">final correction <strong>{final_count}</strong> · logical error <strong>{logical}</strong> (parity {result["logical_parity"]})</text>',
        ])
    lines.extend([
        f'<line x1="28" y1="540" x2="50" y2="540" stroke="{colors["error"]}" stroke-width="6"/><text class="legend" x="56" y="544">residual true error</text>',
        f'<line x1="190" y1="540" x2="212" y2="540" stroke="{colors["match"]}" stroke-width="6"/><text class="legend" x="218" y="544">resolved</text>',
        f'<line x1="284" y1="540" x2="306" y2="540" stroke="{colors["false"]}" stroke-width="6"/><text class="legend" x="312" y="544">false correction</text>',
        f'<circle cx="470" cy="540" r="7" fill="{colors["syndrome"]}" stroke="#7c4a03" stroke-width="1.5"/><text class="legend" x="482" y="544">residual syndrome</text>',
        f'<path d="M 635 533 L 642 540 L 635 547 L 628 540 Z" fill="{colors["herald"]}"/><text class="legend" x="652" y="544">observed herald</text>',
        '</svg>',
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"{output}: q={q_values[0]:g} logical={panels[0][-1]['logical_parity']}, q={q_values[1]:g} logical={panels[1][-1]['logical_parity']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=9)
    parser.add_argument("--p", type=float, default=0.20)
    parser.add_argument("--q-high", type=float, default=1.0)
    parser.add_argument("--q-low", type=float, default=0.75)
    parser.add_argument("--pm", type=float, default=0.0)
    parser.add_argument("--ph", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("figures/seed1-herald-ablation.svg"))
    args = parser.parse_args()
    if args.size < 2 or not 0 <= args.p <= 0.5 or not 0 <= args.q_high <= 1 or not 0 <= args.q_low <= 1 or not 0 <= args.pm <= 0.5 or not 0 <= args.ph <= 1:
        parser.error("invalid probability or size")
    render(args.size, args.p, (args.q_high, args.q_low), args.pm, args.ph, args.seed, args.output)


if __name__ == "__main__":
    main()
