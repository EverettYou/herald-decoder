#!/usr/bin/env python3
"""Compare bounded measured-distance designs on the exact Phase B9 frontier.

This diagnostic intentionally reuses the vetted Phase B8 posterior-predictive
machinery.  Phase B9 changes only the source map and exact frontier: the newly
resolved green cell at (q=.65, p=.28) leaves the frontier, while its unresolved
neighbor at (q=.65, p=.32) enters.  The three-distance cell is evaluated only
at its measured L=7,9,11 values; the independent-Beta model does not justify
forecasting unmeasured code distances.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP = LAB_DIR / "results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b9-honeycomb-frontier-posterior-predictive-design-2026-08-28.json"
EXPECTED = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.65, 0.32)}


def load_phase_b8():
    path = Path(__file__).with_name("analyze_phase_b8_frontier_posterior_predictive.py")
    spec = importlib.util.spec_from_file_location("phase_b9_reused_phase_b8", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_PHASE_B8 = load_phase_b8()
cell_by_key = _PHASE_B8.cell_by_key
additions = _PHASE_B8.additions


def analyze(
    map_path: Path,
    *,
    outer_draws: int = 1024,
    inner_draws: int = 4096,
    seed: int = 8292929,
) -> dict[str, Any]:
    _PHASE_B8.EXPECTED = EXPECTED
    output = _PHASE_B8.analyze(
        map_path,
        outer_draws=outer_draws,
        inner_draws=inner_draws,
        seed=seed,
    )
    output["evidence_boundary"] = (
        "Conditional finite-window posterior-predictive design comparison for the exact "
        "Phase B9 frontier; no data registration, launch, crossing statistic, interpolation, "
        "unmeasured-distance extrapolation, or asymptotic phase claim."
    )
    output["frontier_transition_from_phase_b8"] = {
        "left_frontier_after_resolution": {"q": 0.65, "p": 0.28, "phase": "decodable"},
        "entered_frontier_as_adjacent_unresolved_cell": {"q": 0.65, "p": 0.32},
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--outer-draws", type=int, default=1024)
    parser.add_argument("--inner-draws", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=8292929)
    args = parser.parse_args()
    output = analyze(
        args.phase_map,
        outer_draws=args.outer_draws,
        inner_draws=args.inner_draws,
        seed=args.seed,
    )
    _PHASE_B8.load("analyze_phase_b6_posterior_predictive_design.py", "phase_b9_writer").atomic_json(
        args.output, output
    )
    print(json.dumps({
        "frontier_count": output["frontier_count"],
        "efficiency_ranking": output["efficiency_ranking_descriptive_only"],
    }, indent=2))


if __name__ == "__main__":
    main()
