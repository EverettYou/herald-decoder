#!/usr/bin/env python3
"""R6AD: rescore preserved BP scans with the paper's unconditional LER.

The original scans skipped decoder execution when the sampled physical string
already had nontrivial winding and then reported a conditional decoder risk.
Appendix C instead declares a logical error whenever the physical/correction
union winds.  This script retains all raw trajectories and adds the physical
winding rows back as failures, without rerunning or altering any decoder.
"""
from __future__ import annotations

import gc
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[1]
RESULTS = LAB_DIR / "results"
INPUTS = (
    RESULTS / "r6w-d4-bp-threshold-bracket-dense-2026-08-31.json",
    RESULTS / "r6x-d4-bp-threshold-refinement-dense-provenance-2026-08-31.json",
    RESULTS / "r6y-d4-bp-threshold-lowerside-2026-08-31.json",
    RESULTS / "r6aa-d4-bp-threshold-interleave-2026-08-31.json",
)
OUTPUT = RESULTS / "r6ad-d4-unconditional-flux-rescore-2026-09-01.json"
REPORT = RESULTS / "r6ad-d4-unconditional-flux-rescore-2026-09-01.md"
BP = "R6D_local_BP_posterior_LLR_MWPM"


def main() -> None:
    cells = defaultdict(lambda: {"attempted": 0, "physical_winding": 0, "decoded": 0, "decoder_failures": 0, "unavailable": 0})
    inputs = []
    for path in INPUTS:
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        inputs.append(path.name)
        for row in payload.get("rows", []):
            key = (int(row["size"]), float(row["p_X"]))
            cell = cells[key]; cell["attempted"] += 1
            if row["status"] == "terminal_physical_winding":
                cell["physical_winding"] += 1
                continue
            decoded = row.get("policies", {}).get(BP, {})
            if decoded.get("status") != "decoded":
                cell["unavailable"] += 1
                continue
            cell["decoded"] += 1
            cell["decoder_failures"] += int(bool(decoded["flux_union_logical_failure"]))
        del payload
        gc.collect()
    rows = []
    for (size, p), cell in sorted(cells.items()):
        total_failures = cell["physical_winding"] + cell["decoder_failures"]
        rows.append({"size": size, "p_X": p, **cell,
                     "conditional_decoder_failure_rate": cell["decoder_failures"] / cell["decoded"] if cell["decoded"] else None,
                     "paper_unconditional_flux_LER": total_failures / cell["attempted"] if cell["attempted"] else None,
                     "paper_unconditional_logical_failures": total_failures})
    result = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
              "status": "rescored_with_physical_winding_as_logical_failure",
              "inputs": inputs,
              "paper_rule": "Appendix C: logical error iff physical error string union flux correction contains a homologically nontrivial component.",
              "acceptance": {"all_attempted_trajectories_accounted": all(r["attempted"] == r["physical_winding"] + r["decoded"] + r["unavailable"] for r in rows),
                             "no_decoder_rerun_or_raw_data_mutation": True}, "cells": rows,
              "claim_boundary": "This rescoring corrects an LER denominator/protocol mismatch. It does not establish source-faithful BP likelihood or fit a threshold."}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# R6AD unconditional D4 flux-LER rescore", "", "The earlier BP scans reported a conditional decoder failure rate after excluding physical winding histories. Appendix C counts those histories as logical failures. The table below is the paper-compatible unconditional first-stage LER reconstructed from preserved trajectories; no decoder was rerun.", "", "| L | p_X | attempted | physical winding failures | decoder failures | unconditional LER |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(f"| {row['size']} | {row['p_X']:.3f} | {row['attempted']} | {row['physical_winding']} | {row['decoder_failures']} | {row['paper_unconditional_flux_LER']:.4f} |")
    lines += ["", "## Boundary", "", "These cells were selected around the invalid conditional crossing and are not a threshold fit. They are a diagnostic proving exactly how much of the apparent BP advantage came from an excluded physical-logical-failure class.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "report": str(REPORT), "cells": len(rows)}))


if __name__ == "__main__":
    main()
