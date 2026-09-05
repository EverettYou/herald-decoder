#!/usr/bin/env python3
"""No-new-data floor/saturation/transition analysis for Phase B11."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from scipy.special import betainc


LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase-b11-honeycomb-three-layer-reanalysis-manifest-2026-08-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def validate_manifest(manifest_path: Path, manifest: dict) -> None:
    if manifest["status"] not in {"registered", "preflight_passed", "analyzed"}:
        raise ValueError("invalid Phase B11 lifecycle")
    if manifest["new_decoder_runs"] != 0 or manifest["new_decodes"] != 0 or manifest["render_output"] is not None:
        raise ValueError("Phase B11 must remain a no-new-data, no-render analysis")
    for field in ("source_map", "phase_b10_update", "methodology"):
        path = LAB_DIR / manifest[field]["path"]
        if sha256(path) != manifest[field]["sha256"]:
            raise ValueError(f"Phase B11 {field} hash drift")
    analyzer = LAB_DIR / manifest["analyzer"]["path"]
    if sha256(analyzer) != manifest["analyzer"]["sha256"]:
        raise ValueError("Phase B11 analyzer hash drift")
    calibration = manifest["anchor_calibration"]
    if calibration["posterior_gates"] != [0.8, 0.9, 0.95]:
        raise ValueError("Phase B11 posterior-gate matrix drift")
    if manifest["posterior"]["direction_gate"] != 0.9:
        raise ValueError("Phase B11 direction gate drift")


def infer_sizes(cell: dict) -> list[int]:
    if cell.get("sizes"):
        return list(map(int, cell["sizes"]))
    if len(cell["shots"]) == 3:
        return [7, 9, 11]
    raise ValueError("cannot infer measured distance window")


def merged_cells(source_map: dict, update: dict) -> list[dict]:
    updates = {(float(row["q"]), float(row["p"])): row for row in update["analyses"]}
    expected = {(0.30, 0.20), (0.35, 0.20), (0.55, 0.24), (0.65, 0.32)}
    if set(updates) != expected:
        raise ValueError("Phase B11 update set drift")
    cells = []
    for qrow in source_map["analyses"]:
        q = float(qrow["q"])
        for original in qrow["cells"]:
            p = float(original["p"])
            cell = dict(original)
            replacement = updates.get((q, p))
            if replacement is not None:
                cell.update({key: value for key, value in replacement.items() if key not in {"q", "p"}})
            cell["q"], cell["p"] = q, p
            cell["sizes"] = infer_sizes(cell)
            cells.append(cell)
    if len(cells) != 231:
        raise ValueError("Phase B11 cell-count drift")
    return cells


def joint_anchor_probability(cell: dict, kind: str, tolerance: float, prior: tuple[float, float]) -> float:
    alpha0, beta0 = prior
    probability = 1.0
    for errors, shots in zip(cell["logical_errors"], cell["shots"]):
        alpha = float(errors) + alpha0
        beta = float(shots - errors) + beta0
        if kind == "floor":
            factor = float(betainc(alpha, beta, tolerance))
        elif kind == "saturation":
            lower = max(0.0, 0.5 - tolerance)
            upper = min(1.0, 0.5 + tolerance)
            factor = float(betainc(alpha, beta, upper) - betainc(alpha, beta, lower))
        else:
            raise ValueError(f"unknown anchor kind: {kind}")
        probability *= factor
    return probability


def choose_rule(cells_by_key: dict, *, kind: str, tolerances: list[float], gates: list[float],
                validation_keys: list[tuple[float, float]], exclusion_keys: list[tuple[float, float]],
                prior: tuple[float, float]) -> tuple[dict, list[dict]]:
    candidates = []
    for tolerance in tolerances:
        validation = [joint_anchor_probability(cells_by_key[key], kind, tolerance, prior) for key in validation_keys]
        exclusion = [joint_anchor_probability(cells_by_key[key], kind, tolerance, prior) for key in exclusion_keys]
        for gate in gates:
            qualifies = min(validation) >= gate and max(exclusion) < gate
            candidates.append({"tolerance": tolerance, "gate": gate, "qualifies": qualifies,
                               "minimum_validation_probability": min(validation),
                               "maximum_exclusion_probability": max(exclusion)})
    qualified = [row for row in candidates if row["qualifies"]]
    if not qualified:
        raise ValueError(f"no qualifying Phase B11 {kind} anchor rule")
    selected = sorted(qualified, key=lambda row: (-row["gate"], row["tolerance"]))[0]
    return selected, candidates


def analyze(manifest_path: Path) -> dict:
    manifest = json.loads(Path(manifest_path).read_text())
    validate_manifest(manifest_path, manifest)
    source = json.loads((LAB_DIR / manifest["source_map"]["path"]).read_text())
    update = json.loads((LAB_DIR / manifest["phase_b10_update"]["path"]).read_text())
    cells = merged_cells(source, update)
    by_key = {(cell["q"], cell["p"]): cell for cell in cells}
    calibration = manifest["anchor_calibration"]
    exclusions = [tuple(map(float, key)) for key in calibration["transition_exclusion_cells"]]
    selected = {}
    diagnostics = {}
    for kind in ("floor", "saturation"):
        selected[kind], diagnostics[kind] = choose_rule(
            by_key,
            kind=kind,
            tolerances=calibration[f"{kind}_tolerances"],
            gates=calibration["posterior_gates"],
            validation_keys=[tuple(map(float, key)) for key in calibration[f"{kind}_validation_cells"]],
            exclusion_keys=exclusions,
            prior=(0.5, 0.5),
        )
    anchor_rows = []
    for cell in cells:
        key = (cell["q"], cell["p"])
        scores = {}
        stable = {}
        for kind in ("floor", "saturation"):
            rule = selected[kind]
            primary = joint_anchor_probability(cell, kind, rule["tolerance"], (0.5, 0.5))
            sensitivity = joint_anchor_probability(cell, kind, rule["tolerance"], (1.0, 1.0))
            scores[kind] = {"primary": primary, "uniform_prior": sensitivity}
            stable[kind] = primary >= rule["gate"] and sensitivity >= rule["gate"]
        if stable["floor"] and stable["saturation"]:
            raise ValueError(f"conflicting Phase B11 anchors: {key}")
        direction = "decodable" if stable["floor"] else "undecodable" if stable["saturation"] else None
        anchor_rows.append({"q": key[0], "p": key[1], "anchor": direction, "scores": scores})
    anchor_by_key = {(row["q"], row["p"]): row["anchor"] for row in anchor_rows}
    brackets = []
    for q in sorted({cell["q"] for cell in cells}):
        row = sorted([cell for cell in cells if cell["q"] == q], key=lambda cell: cell["p"])
        decodable = []
        undecodable = []
        for cell in row:
            key = (q, cell["p"])
            floor = anchor_by_key[key] == "decodable"
            saturation = anchor_by_key[key] == "undecodable"
            prior_stable = cell.get("prior_sensitivity_status") == "stable"
            if floor or (prior_stable and float(cell.get("posterior_probability_downward_trend", 0.0)) >= 0.9 and not saturation):
                decodable.append(cell["p"])
            if saturation or (prior_stable and float(cell.get("posterior_probability_upward_trend", 0.0)) >= 0.9 and not floor):
                undecodable.append(cell["p"])
        pair = None
        for upper in sorted(undecodable):
            lower = [p for p in decodable if p < upper]
            if lower:
                pair = (max(lower), upper)
                break
        brackets.append({"q": q, "lower_decodable_p": pair[0] if pair else None,
                         "upper_undecodable_p": pair[1] if pair else None,
                         "width": pair[1] - pair[0] if pair else None})
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_no_new_data_no_render",
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "selected_anchor_rules": selected,
        "anchor_rule_diagnostics": diagnostics,
        "anchors": anchor_rows,
        "lower_boundary_brackets": brackets,
        "new_decoder_runs": 0,
        "new_decodes": 0,
        "map_rendered": False,
        "claim_boundary": manifest["claim_boundary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate_manifest(args.manifest, manifest)
    if args.preflight:
        output = LAB_DIR / manifest["preflight_output"]
        payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                   "status": "preflight_passed_not_analyzed", "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
                   "analyzer": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
                   "source_hashes_valid": True, "new_decoder_runs": 0, "new_decodes": 0,
                   "analysis_performed": False, "map_rendered": False}
        atomic_json(output, payload)
        print(json.dumps(payload, indent=2))
        return
    output = analyze(args.manifest)
    atomic_json(LAB_DIR / manifest["analysis_output"], output)
    print(json.dumps({"status": output["status"], "anchors": sum(row["anchor"] is not None for row in output["anchors"])}, indent=2))


if __name__ == "__main__":
    main()
