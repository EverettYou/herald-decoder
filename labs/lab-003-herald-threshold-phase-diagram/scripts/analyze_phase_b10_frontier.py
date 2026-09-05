#!/usr/bin/env python3
"""Pool Phase B10 endpoint counts into the Phase B9 map frontier."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_base():
    path = Path(__file__).with_name("analyze_phase_b9_frontier.py")
    spec = importlib.util.spec_from_file_location("phase_b10_analysis_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BASE = load_base()
LAB_DIR = Path(__file__).resolve().parents[1]
BASE.DEFAULT_MANIFEST = LAB_DIR / "phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json"
BASE.DEFAULT_AUDIT = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-completion-audit-2026-08-28.json"
BASE.DEFAULT_OUTPUT = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-analysis-2026-08-28.json"
base_cell = BASE.base_cell
analyze_counts = BASE.analyze_counts


def analyze(manifest_path: Path, audit_path: Path) -> dict:
    output = BASE.analyze(manifest_path, audit_path)
    output["evidence_boundary"] = (
        "Exactly four Phase B9 frontier cells updated by registered Phase B10 endpoint data; "
        "no crossing statistic, interpolation, grid expansion, or asymptotic claim."
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BASE.DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=BASE.DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=BASE.DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = analyze(args.manifest, args.audit)
    submit = BASE.load("submit_phase_b10_endpoints.py", "phase_b10_writer")
    submit.atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells_updated": 4}, indent=2))


if __name__ == "__main__":
    main()
