#!/usr/bin/env python3
"""Merge the four audited Phase B14 combined posteriors into the current map."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = LAB_DIR / "results/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.json"
DEFAULT_ANALYSIS = LAB_DIR / "results/phase-b14-honeycomb-two-branch-analysis-2026-08-28.json"
DEFAULT_AUDIT = LAB_DIR / "results/phase-b14-honeycomb-two-branch-completion-audit-2026-08-28.json"
DEFAULT_B9_COUNTS = LAB_DIR / "results/phase-b9-honeycomb-bayesian-fuzzy-trend-phase-map-2026-08-28.json"
DEFAULT_B10_COUNTS = LAB_DIR / "results/phase-b10-honeycomb-measured-endpoints-analysis-2026-08-28.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json"
EXPECTED = {(0.20, 0.16), (0.20, 0.20), (0.70, 0.28), (0.70, 0.32)}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic_sha256(path: Path) -> str:
    payload = json.loads(Path(path).read_text())
    payload.pop("generated_at", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = Path(path).with_name(f".{Path(path).name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def count_vectors(b9: dict, b10: dict) -> dict[tuple[float, float], dict]:
    counts = {}
    for analysis in b9["analyses"]:
        q = float(analysis["q"])
        for cell in analysis["cells"]:
            counts[(q, float(cell["p"]))] = {
                "sizes": cell.get("sizes", [7, 9, 11]),
                "logical_errors": cell["logical_errors"],
                "shots": cell["shots"],
            }
    for row in b10["analyses"]:
        counts[(float(row["q"]), float(row["p"]))] = {
            "sizes": row["sizes"], "logical_errors": row["logical_errors"], "shots": row["shots"]
        }
    if len(counts) != 231:
        raise ValueError("Phase B14 current count inventory must cover 231 cells")
    return counts


def merge(base: dict, analysis: dict, audit: dict, b9: dict | None = None, b10: dict | None = None) -> dict:
    if analysis.get("status") != "complete_continuous_evidence_only":
        raise ValueError("Phase B14 analysis is incomplete")
    if analysis.get("cell_or_phase_classification_performed") or analysis.get("boundary_inference_performed"):
        raise ValueError("Phase B14 source must remain continuous evidence only")
    if audit.get("status") != "data_complete_not_analyzed" or audit.get("raw_rows_observed") != 10000:
        raise ValueError("Phase B14 completion audit is incomplete")
    updates = {(float(row["q"]), float(row["p"])): row["variants"]["combined"] for row in analysis["analyses"]}
    if set(updates) != EXPECTED:
        raise ValueError("Phase B14 update coordinates drift")
    cells = []
    updated = []
    limit = float(base["display"]["symmetric_limit"])
    inventory = count_vectors(
        b9 or json.loads(DEFAULT_B9_COUNTS.read_text()),
        b10 or json.loads(DEFAULT_B10_COUNTS.read_text()),
    )
    for original in base["cells"]:
        key = (float(original["q"]), float(original["p"]))
        if key not in updates:
            retained = dict(original)
            retained.update(inventory[key])
            cells.append(retained)
            continue
        source = updates[key]
        upward = float(source["posterior_probability_upward_trend"])
        downward = float(source["posterior_probability_downward_trend"])
        if abs(upward + downward - 1.0) > 1e-9:
            raise ValueError("Phase B14 directional probabilities do not sum to one")
        censoring = dict(source["posterior_log_odds_censoring"])
        raw = source["posterior_log_odds_upward_vs_downward"]
        display_source = float(raw) if raw is not None else float(censoring["bound"])
        display_value = max(-limit, min(limit, display_source))
        record = {
            "q": key[0], "p": key[1],
            "posterior_probability_upward_trend": upward,
            "posterior_probability_downward_trend": downward,
            "posterior_log_odds_upward_vs_downward": raw,
            "posterior_log_odds_censoring": censoring,
            "qmc_standard_error_upward_probability": source["qmc_standard_error_upward_probability"],
            "qmc_standard_error_downward_probability": source["qmc_standard_error_upward_probability"],
            "qmc_probability_resolution": 1.0 / 65536.0,
            "display_source_value": display_source,
            "display_log_odds": display_value,
            "display_clipped": display_value != display_source,
            "evidence_source": "phase_b14_combined_distance_and_precision",
            "sizes": source["sizes"],
            "logical_errors": source["logical_errors"],
            "shots": source["shots"],
            "posterior_mean_slope_ler_per_distance": source["posterior_mean_slope_ler_per_distance"],
            "posterior_slope_interval90": source["posterior_slope_interval90"],
        }
        cells.append(record)
        updated.append({"q": key[0], "p": key[1], "before": original["display_source_value"], "after": display_source})
    if len(cells) != 231 or len(updated) != 4:
        raise ValueError("Phase B14 merge must preserve 231 cells and replace exactly four")
    counts = {}
    for row in cells:
        counts[row["evidence_source"]] = counts.get(row["evidence_source"], 0) + 1
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "current_b14_compatible_finite_window_trend_evidence",
        "quantity": base["quantity"],
        "axes": base["axes"],
        "display": {
            "symmetric_limit": limit,
            "clipping_applies_only_to_display": True,
            "clipped_cell_count": sum(row["display_clipped"] for row in cells),
        },
        "provenance": {
            "base": {"path": str(DEFAULT_BASE.relative_to(LAB_DIR)), "semantic_sha256": semantic_sha256(DEFAULT_BASE)},
            "phase_b14_analysis": {"path": str(DEFAULT_ANALYSIS.relative_to(LAB_DIR)), "sha256": sha256(DEFAULT_ANALYSIS)},
            "phase_b14_completion_audit": {"path": str(DEFAULT_AUDIT.relative_to(LAB_DIR)), "sha256": sha256(DEFAULT_AUDIT)},
            "phase_b9_count_inventory": {"path": str(DEFAULT_B9_COUNTS.relative_to(LAB_DIR)), "sha256": sha256(DEFAULT_B9_COUNTS)},
            "phase_b10_count_updates": {"path": str(DEFAULT_B10_COUNTS.relative_to(LAB_DIR)), "sha256": sha256(DEFAULT_B10_COUNTS)},
            "evidence_source_counts": counts,
            "updated_cells": updated,
            "new_decoder_runs": 8,
            "new_decodes": 10000,
            "sample_selection": "Phase B14 preregistered four-cell two-branch matrix",
        },
        "q_values": base["q_values"],
        "p_values": base["p_values"],
        "cells": cells,
        "interpretation_policy": "Continuous finite-window evidence only; B15 may fit regularized LLR=0 summaries but not assign phases.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = merge(json.loads(args.base.read_text()), json.loads(args.analysis.read_text()), json.loads(args.audit.read_text()))
    atomic_json(args.output, output)
    print(json.dumps({"status": output["status"], "cells": len(output["cells"]), "updated": len(output["provenance"]["updated_cells"])}, indent=2))


if __name__ == "__main__":
    main()
