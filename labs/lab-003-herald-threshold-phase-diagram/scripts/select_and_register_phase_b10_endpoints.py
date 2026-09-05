#!/usr/bin/env python3
"""Register the Phase B10 measured-endpoints exact-frontier matrix."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_DESIGN = LAB_DIR / "results/phase-b9-honeycomb-frontier-posterior-predictive-design-2026-08-28.json"
DEFAULT_SELECTION = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-selection-2026-08-28.json"
DEFAULT_MANIFEST = LAB_DIR / "phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json"
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.65, 0.32)}
NEW_SEEDS = [890001, 890002, 890003, 890004, 890005]
CAMPAIGN = "phase-b10-honeycomb-measured-endpoints-2026-08-28"


def load_b9():
    path = Path(__file__).with_name("select_and_register_phase_b9_endpoints.py")
    spec = importlib.util.spec_from_file_location("phase_b10_registration_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.DEFAULT_MAP = DEFAULT_MAP
    module.DEFAULT_DESIGN = DEFAULT_DESIGN
    module.EXPECTED = EXPECTED
    module.NEW_SEEDS = NEW_SEEDS
    module.CAMPAIGN = CAMPAIGN
    return module


_BASE = load_b9()
sha256 = _BASE.sha256
atomic_json = _BASE.atomic_json
seed_audit = _BASE.seed_audit


def build_selection(map_path: Path, design_path: Path) -> dict:
    selection = _BASE.build_selection(map_path, design_path)
    selection["design_rule"] = (
        "Cover every exact Phase B9 frontier branch with the descriptive-efficiency-leading "
        "measured_endpoints_1000 design; preserve the low-yield q=0.30,p=0.20 forecast and "
        "use only measured distances."
    )
    selection["claim_boundary"] = (
        "Phase B10 registration only; exact four-cell Phase B9 frontier, current finite-window "
        "endpoints only, fixed 0.90 gate, no unmeasured-distance extrapolation, adaptive "
        "expansion, or asymptotic claim."
    )
    return selection


def build_manifest(selection_path: Path, selection: dict) -> dict:
    manifest = _BASE.build_manifest(selection_path, selection)
    manifest["purpose"] = "Run the smallest measured-distance design covering every exact Phase B9 frontier branch."
    manifest["analysis"]["pooling"] = "Pool fresh endpoint counts only with the corresponding Phase B9 map-count vector."
    manifest["preflight_gate"] = "Implement and test non-overwriting dispatch, exact completion, pooled analysis, and four-payload rendering before launch."
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    selection = build_selection(args.phase_map, args.design)
    atomic_json(args.selection, selection)
    atomic_json(args.manifest, build_manifest(args.selection, selection))
    print(json.dumps({k: selection[k] for k in ("job_count", "expected_new_decodes", "expected_resolved_cells")}, indent=2))


if __name__ == "__main__":
    main()
