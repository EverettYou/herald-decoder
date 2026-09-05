#!/usr/bin/env python3
"""Build the single current, research-facing Lab 003 evidence bundle.

Phase files remain provenance inputs.  This bundle is the compact data record
promoted alongside the current collaborator-facing B18 figure.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


LAB = Path(__file__).resolve().parents[1]
RESULTS = LAB / "results"
SOURCES = {
    "honeycomb_finite_window_trend": "phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json",
    "symmetry_constrained_boundary_guide": "phase-b18-symmetry-constrained-guide-2026-08-28.json",
    "selected_ler_q0_q075_q1": "final-selected-ler-curves-q0-q075-q1-square-honeycomb-2026-08-28.json",
}
OUTPUT = RESULTS / "current-evidence.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payloads = {}
    provenance = {}
    for label, name in SOURCES.items():
        path = RESULTS / name
        payloads[label] = json.loads(path.read_text(encoding="utf-8"))
        provenance[label] = {"path": f"results/{name}", "sha256": digest(path)}
    bundle = {
        "schema_version": 1,
        "status": "current_lab003_evidence",
        "evidence_boundary": (
            "The B14-current finite-window honeycomb trend evidence, the B18 "
            "p<->1-p symmetry-constrained visual guide and unchanged finite-grid directional bracket/censoring region, and selected "
            "non-pooled LER context panels. This is not a threshold fit or "
            "thermodynamic phase claim."
        ),
        "provenance": provenance,
        "evidence": payloads,
    }
    OUTPUT.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
