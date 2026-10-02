"""Embed a repository-derived, vector L=3 geometry figure in the standalone TeX."""
from __future__ import annotations

import hashlib
import json
from math import sqrt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from herald_decoder.lattice_model import honeycomb_graph
from audit_lattice_construction import construction


def main() -> None:
    L = 3
    graph = honeycomb_graph(L)
    expected = construction(L)
    coords = [(round(2*v.x), round(2*v.y/sqrt(3))) for v in graph.vertices]
    edges = {tuple(sorted((coords[a],coords[b]))) for a,b in graph.edges}
    assert set(coords) == expected["vertices"]
    assert edges == expected["edges"]
    logical = {tuple(sorted((coords[graph.edges[e][0]],coords[graph.edges[e][1]])))
               for e in graph.logical_edges}
    assert logical == expected["logical"]
    offsets = [(2,0),(1,1),(-1,1),(-2,0),(-1,-1),(1,-1)]
    raw = set()
    for a in range(L):
        for b in range(L):
            corners = [(3*a+dx,2*b+a%2+dy) for dx,dy in offsets]
            raw.update(tuple(sorted((corners[j],corners[(j+1)%6]))) for j in range(6))
    removed = raw - edges
    assert len(removed) == 12

    def position(v):
        return f"({v[0]/2:.6f},{sqrt(3)*v[1]/2:.6f})"

    lines = [r"\begin{tikzpicture}[x=0.78cm,y=0.78cm,font=\small,",
             r"  kept/.style={draw=black!65,line width=0.65pt},",
             r"  removed/.style={draw=black!30,line width=0.6pt,dash pattern=on 2.2pt off 2pt},",
             r"  logical/.style={draw=logicaledge,line width=1.65pt},",
             r"  detector/.style={circle,fill=ink,draw=ink,inner sep=0pt,minimum size=4.5pt},",
             r"  leftv/.style={rectangle,fill=white,draw=leftboundary,line width=1pt,inner sep=0pt,minimum size=5.8pt},",
             r"  rightv/.style={diamond,aspect=1,fill=white,draw=rightboundary,line width=1pt,inner sep=0pt,minimum size=7.5pt}]"]
    for edge in sorted(removed):
        lines.append(r"\draw[removed] " + position(edge[0])+" -- "+position(edge[1])+";")
    for edge in sorted(edges):
        style = "logical" if edge in logical else "kept"
        lines.append(r"\draw["+style+"] "+position(edge[0])+" -- "+position(edge[1])+";")
    styles = {}
    for i,v in enumerate(graph.vertices):
        style = "detector" if v.detector else ("leftv" if v.boundary_side=="left" else "rightv")
        styles[coords[i]] = style
        lines.append(r"\node["+style+"] at "+position(coords[i])+" {};")
    assert {v for v,s in styles.items() if s=="detector"} == expected["detectors"]
    assert {v for v,s in styles.items() if s=="leftv"} == expected["left"]
    assert {v for v,s in styles.items() if s=="rightv"} == expected["right"]
    lines += [
        r"\node[font=\small\bfseries] at (1.5,5.95) {$L=3$};",
        r"\node[text=leftboundary] at (-0.7,5.6) {$B_{\rm left}$};",
        r"\node[text=rightboundary] at (3.7,5.6) {$B_{\rm right}$};",
        r"\node[detector] at (5.55,4.8) {};",
        r"\node[anchor=west] at (6.15,4.8) {$D_L$: measured detectors};",
        r"\node[leftv] at (5.55,3.85) {};",
        r"\node[anchor=west] at (6.15,3.85) {$B_{\rm left}$: unmeasured};",
        r"\node[rightv] at (5.55,2.9) {};",
        r"\node[anchor=west] at (6.15,2.9) {$B_{\rm right}$: unmeasured};",
        r"\draw[kept] (5.2,1.95) -- (5.9,1.95);",
        r"\node[anchor=west] at (6.15,1.95) {Retained edges $E_L$};",
        r"\draw[logical] (5.2,1.0) -- (5.9,1.0);",
        r"\node[anchor=west] at (6.15,1.0) {Logical edges $\Gamma_R\subset E_L$};",
        r"\draw[removed] (5.2,0.05) -- (5.9,0.05);",
        r"\node[anchor=west] at (6.15,0.05) {Removed edges (not in $E_L$)};",
        r"\node[anchor=west,font=\small] at (5.1,-0.95) {$V_L=D_L\,\dot\cup\,B_{\rm left}\,\dot\cup\,B_{\rm right}$};",
        r"\end{tikzpicture}",
    ]
    code = "\n".join(lines)+"\n"
    tex = ROOT / "output/scicode2/herald_decoding_problem.tex"
    text = tex.read_text()
    start = "% BEGIN GENERATED LATTICE FIGURE\n"
    end = "% END GENERATED LATTICE FIGURE"
    before,tail = text.split(start)
    _,after = tail.split(end)
    tex.write_text(before+start+code+end+after)
    incident = {v for edge in edges for v in edge}
    isolated = set(coords)-incident
    assert len(isolated)==6 and not isolated & expected["detectors"]
    payload = {
        "status":"passed", "L":L,
        "vertices":len(coords), "detectors":len(expected["detectors"]),
        "left_boundary_vertices":len(expected["left"]), "right_boundary_vertices":len(expected["right"]),
        "isolated_boundary_vertices":len(isolated), "retained_edges":len(edges),
        "logical_edges":len(logical), "removed_context_edges":len(removed),
        "source":"src/herald_decoder/lattice_model.py",
        "source_sha256":hashlib.sha256((ROOT/'src/herald_decoder/lattice_model.py').read_bytes()).hexdigest(),
        "tikz_sha256":hashlib.sha256(code.encode()).hexdigest(),
        "verification":"Exact coordinate sets, node classes, retained edges and Gamma_R matched to independent integer construction; removed dashed segments excluded from E_L.",
    }
    Path(__file__).with_name("lattice_figure_audit.json").write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))


if __name__ == "__main__":
    main()
