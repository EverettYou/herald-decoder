#!/usr/bin/env python3
"""Audit Phase B10 output pairs before inference."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BASE = load("audit_phase_b9_outputs.py", "phase_b10_audit_base")
SUBMIT = load("submit_phase_b10_endpoints.py", "phase_b10_submit_for_audit")
BASE.load_submit = lambda: SUBMIT
BASE.DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "phase-b10-honeycomb-measured-endpoints-manifest-2026-08-28.json"
BASE.DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "results/phase-b10-honeycomb-measured-endpoints-completion-audit-2026-08-28.json"
audit_pair = BASE.audit_pair
audit = BASE.audit


if __name__ == "__main__":
    BASE.main()
