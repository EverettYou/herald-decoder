#!/usr/bin/env python3
"""Validate and analyze a registered Lab 003 Phase 2 campaign.

The analyzer is deliberately fail-closed.  It never reads temporary shard
files and never repairs or rewrites a shard.  Every registered ``(lattice,q)``
artifact must be present, internally consistent, produced by one common
runtime/source configuration, and backed by a complete raw JSONL stream.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LAB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = LAB_DIR.parents[1]
DEFAULT_MANIFEST = LAB_DIR / "phase2-scout-manifest.json"
DEFAULT_OUTPUT = LAB_DIR / "results/phase2-q-skeleton-analysis-2026-08-27.json"
FILE_RE = re.compile(
    r"^phase2-(square|honeycomb)-(q\d{3})-discovery-1000-2026-08-27\.json$"
)
HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DECODER = {
    "name": "HeraldAwareBpMatchingDecoder",
    "recurrence_mode": "damping",
    "damping": 0.25,
    "max_iterations": 40,
    "matching_projection": "posterior_llr",
    "p_m": 0.0,
    "p_h": 0.0,
    "use_numba": True,
}
RUNTIME_KEYS = {
    "python_executable",
    "python_version",
    "numpy_version",
    "numba_version",
    "scipy_version",
    "pymatching_version",
    "numba_available",
}
SOURCE_FILES = {
    "runner": LAB_DIR / "scripts/run_phase2_scout.py",
    "lattice_model": PROJECT_ROOT / "src/herald_decoder/lattice_model.py",
    "decoder": PROJECT_ROOT / "src/herald_decoder/herald_bp_decoder.py",
    "damping_decoder": PROJECT_ROOT / "src/herald_decoder/legacy_damped_bp_decoder.py",
    "numba_kernels": PROJECT_ROOT / "src/herald_decoder/numba_bp_kernels.py",
}


class ValidationError(ValueError):
    """Raised when a discovery campaign is unsafe to combine."""


def expected_decoder(manifest: dict) -> dict:
    return dict(manifest.get("decoder", DECODER))


def decoder_label(manifest: dict) -> str:
    schedule = expected_decoder(manifest).get("update_schedule", "synchronous")
    return f"herald_{schedule}_bp_llr_mwpm" if schedule != "synchronous" else "herald_damping_bp_llr_mwpm"


def artifact_filename(manifest: dict, lattice: str, q: float) -> str:
    template = manifest.get(
        "artifact_stem_template",
        "phase2-{lattice}-{q_tag}-discovery-1000-2026-08-27",
    )
    return template.format(lattice=lattice, q_tag=q_tag(q)) + ".json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def q_tag(q: float) -> str:
    return f"q{int(round(100 * q)):03d}"


def canonical_config(payload: dict) -> dict:
    keys = (
        "campaign",
        "lattice",
        "q",
        "p_grid",
        "sizes",
        "seeds",
        "shots_per_seed",
        "decoder",
        "sampling",
    )
    return {key: payload[key] for key in keys}


def config_sha256(payload: dict) -> str:
    encoded = json.dumps(canonical_config(payload), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def expected_sampling(lattice: str) -> dict:
    return {
        "nested_common_random_numbers": True,
        "master_rng": "numpy.default_rng(SeedSequence([0x48445233, lattice_id, L, seed]))",
        "error_rule": "x_e(p) = 1[u_e < p]",
        "herald_rule": "h_v(p,q) = 1[d_v(p)>=2] 1[u_v<q]",
    }


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    required = {"campaign", "q_values", "lattices", "sizes", "seeds", "shots_per_seed", "p_grid"}
    missing = required - set(manifest)
    if missing:
        raise ValidationError(f"manifest is missing keys: {sorted(missing)}")
    q_values = [float(value) for value in manifest["q_values"]]
    if (
        not q_values
        or len(q_values) != len(set(q_values))
        or q_values != sorted(q_values)
        or any(not 0.0 <= value <= 1.0 for value in q_values)
    ):
        raise ValidationError("manifest q values must be a nonempty sorted unique subset of [0,1]")
    q_grid_policy = manifest.get("q_grid_policy", "full_skeleton")
    if q_grid_policy == "full_skeleton":
        expected_q = [step / 20 for step in range(21)]
        if len(q_values) != len(expected_q) or not np.allclose(q_values, expected_q, atol=1e-12, rtol=0):
            raise ValidationError("full_skeleton manifest must contain q=0:0.05:1")
    elif q_grid_policy != "explicit":
        raise ValidationError("manifest q_grid_policy must be full_skeleton or explicit")
    lattices = manifest["lattices"]
    if not lattices or len(lattices) != len(set(lattices)) or not set(lattices) <= {"square", "honeycomb"}:
        raise ValidationError("manifest lattices must be a nonempty unique subset of square and honeycomb")
    if len(manifest["sizes"]) < 2 or len(manifest["sizes"]) != len(set(manifest["sizes"])):
        raise ValidationError("manifest sizes must be unique and contain at least two values")
    if not manifest["seeds"] or len(manifest["seeds"]) != len(set(manifest["seeds"])):
        raise ValidationError("manifest seeds must be nonempty and unique")
    shots_per_cell = len(manifest["seeds"]) * int(manifest["shots_per_seed"])
    if shots_per_cell <= 0:
        raise ValidationError("manifest must specify a positive shots-per-cell total")
    if int(manifest.get("shots_per_cell", shots_per_cell)) != shots_per_cell:
        raise ValidationError("manifest shots_per_cell does not match seeds times shots_per_seed")
    for lattice in manifest["lattices"]:
        grid = [float(value) for value in manifest["p_grid"].get(lattice, [])]
        if len(grid) < 2 or grid != sorted(set(grid)) or any(not 0.02 <= value <= 0.49 for value in grid):
            raise ValidationError(f"invalid registered p grid for {lattice}")
    expected_shards = len(manifest["lattices"]) * len(q_values)
    if int(manifest.get("expected_shards", expected_shards)) != expected_shards:
        raise ValidationError("manifest expected_shards does not match lattice/q coverage")
    confidence = float(manifest.get("inference", {}).get("confidence_level", 0.95))
    if not 0.5 < confidence < 1.0:
        raise ValidationError("inference confidence_level must lie in (0.5, 1)")
    manifest["q_values"] = q_values
    return manifest


def discover_shards(results_dir: Path, manifest: dict) -> dict[tuple[str, float], Path]:
    expected = {(lattice, q) for lattice in manifest["lattices"] for q in manifest["q_values"]}
    discovered = {
        (lattice, q): results_dir / artifact_filename(manifest, lattice, q)
        for lattice, q in expected
        if (results_dir / artifact_filename(manifest, lattice, q)).is_file()
    }
    missing = expected - set(discovered)
    if missing:
        detail = {
            "missing": [f"{lattice}:{q:.2f}" for lattice, q in sorted(missing)],
        }
        raise ValidationError(f"Phase 2 q/lattice coverage mismatch: {detail}")
    return discovered


def _validate_runtime(runtime: object) -> dict:
    if not isinstance(runtime, dict) or set(runtime) != RUNTIME_KEYS:
        raise ValidationError("runtime provenance keys do not match the registered schema")
    if runtime["numba_available"] is not True:
        raise ValidationError("artifact was not produced by the required Numba runtime")
    if any(not isinstance(runtime[key], str) or not runtime[key] for key in RUNTIME_KEYS - {"numba_available"}):
        raise ValidationError("runtime provenance contains an empty/non-string value")
    return runtime


def _validate_source_hashes(source_hashes: object, current_sources: dict[str, str] | None) -> dict:
    if not isinstance(source_hashes, dict) or set(source_hashes) != set(SOURCE_FILES):
        raise ValidationError("source hash keys do not match the registered schema")
    if any(not isinstance(value, str) or not HEX_SHA256_RE.fullmatch(value) for value in source_hashes.values()):
        raise ValidationError("source hashes must be lowercase SHA-256 digests")
    if current_sources is not None and source_hashes != current_sources:
        raise ValidationError("artifact source hashes do not match the current registered implementation")
    return source_hashes


def _validate_rows(payload: dict, manifest: dict) -> tuple[dict, dict]:
    lattice = payload["lattice"]
    q = float(payload["q"])
    sizes = [int(value) for value in manifest["sizes"]]
    p_grid = [float(value) for value in manifest["p_grid"][lattice]]
    seeds = [int(value) for value in manifest["seeds"]]
    shots_per_seed = int(manifest["shots_per_seed"])
    total_shots = len(seeds) * shots_per_seed

    seed_rows: dict[tuple[int, float, int], dict] = {}
    for row in payload.get("per_seed", []):
        key = (int(row.get("L", -1)), float(row.get("p", -1)), int(row.get("seed", -1)))
        if key in seed_rows:
            raise ValidationError(f"duplicate per-seed row in {lattice}, q={q:.2f}: {key}")
        if (
            row.get("lattice") != lattice
            or not np.isclose(float(row.get("q", -1)), q, atol=1e-12, rtol=0)
            or key[0] not in sizes
            or key[1] not in p_grid
            or key[2] not in seeds
            or int(row.get("shots", -1)) != shots_per_seed
            or not 0 <= int(row.get("logical_errors", -1)) <= shots_per_seed
        ):
            raise ValidationError(f"invalid per-seed row in {lattice}, q={q:.2f}: {key}")
        seed_rows[key] = row
    expected_seed_keys = {(size, p, seed) for size in sizes for p in p_grid for seed in seeds}
    if set(seed_rows) != expected_seed_keys:
        raise ValidationError(f"incomplete per-seed cells in {lattice}, q={q:.2f}")

    summaries: dict[tuple[int, float], dict] = {}
    for row in payload.get("summaries", []):
        key = (int(row.get("L", -1)), float(row.get("p", -1)))
        if key in summaries:
            raise ValidationError(f"duplicate summary row in {lattice}, q={q:.2f}: {key}")
        errors = int(row.get("logical_errors", -1))
        seed_errors = sum(int(seed_rows[(key[0], key[1], seed)]["logical_errors"]) for seed in seeds) if key[0] in sizes and key[1] in p_grid else -1
        if (
            row.get("lattice") != lattice
            or not np.isclose(float(row.get("q", -1)), q, atol=1e-12, rtol=0)
            or row.get("decoder") != decoder_label(manifest)
            or key[0] not in sizes
            or key[1] not in p_grid
            or int(row.get("shots", -1)) != total_shots
            or errors != seed_errors
            or not np.isclose(float(row.get("logical_error_rate", -1)), errors / total_shots, atol=1e-12, rtol=0)
        ):
            raise ValidationError(f"invalid/inconsistent summary row in {lattice}, q={q:.2f}: {key}")
        summaries[key] = row
    expected_summary_keys = {(size, p) for size in sizes for p in p_grid}
    if set(summaries) != expected_summary_keys:
        raise ValidationError(f"incomplete summary cells in {lattice}, q={q:.2f}")
    return seed_rows, summaries


def _validate_raw(
    payload: dict,
    summary_path: Path,
    lab_dir: Path,
    manifest: dict,
    seed_rows: dict,
) -> None:
    metadata = payload.get("raw_records")
    if not isinstance(metadata, dict) or set(metadata) != {"path", "format", "records", "sha256"}:
        raise ValidationError(f"invalid raw-record metadata in {summary_path.name}")
    expected_raw = summary_path.with_name(f"{summary_path.stem}-raw.jsonl.gz")
    raw_path = (lab_dir / str(metadata["path"])).resolve()
    if raw_path != expected_raw.resolve() or metadata["format"] != "gzip_json_lines":
        raise ValidationError(f"raw-record path/format mismatch in {summary_path.name}")
    if not raw_path.is_file() or sha256(raw_path) != metadata["sha256"]:
        raise ValidationError(f"missing or checksum-mismatched raw records for {summary_path.name}")

    lattice = payload["lattice"]
    q = float(payload["q"])
    sizes = set(int(value) for value in manifest["sizes"])
    p_grid = set(float(value) for value in manifest["p_grid"][lattice])
    seeds = set(int(value) for value in manifest["seeds"])
    shots_per_seed = int(manifest["shots_per_seed"])
    seen: set[tuple[int, float, int, int]] = set()
    raw_errors = {key: 0 for key in seed_rows}
    count = 0
    with gzip.open(raw_path, "rt", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValidationError(f"invalid raw JSON at {raw_path.name}:{line_number}") from error
            key = (int(row.get("L", -1)), float(row.get("p", -1)), int(row.get("seed", -1)), int(row.get("shot", -1)))
            if key in seen:
                raise ValidationError(f"duplicate raw observation cell in {raw_path.name}: {key}")
            if (
                row.get("campaign") != manifest["campaign"]
                or row.get("lattice") != lattice
                or not np.isclose(float(row.get("q", -1)), q, atol=1e-12, rtol=0)
                or row.get("decoder") != decoder_label(manifest)
                or key[0] not in sizes
                or key[1] not in p_grid
                or key[2] not in seeds
                or not 0 <= key[3] < shots_per_seed
            ):
                raise ValidationError(f"invalid raw observation at {raw_path.name}:{line_number}")
            expected_id = f"{manifest['campaign']}:{lattice}:L{key[0]}:seed{key[2]}:shot{key[3]}"
            if row.get("observation_id") != expected_id or not isinstance(row.get("logical_failure"), bool):
                raise ValidationError(f"invalid raw observation identity/outcome at {raw_path.name}:{line_number}")
            seen.add(key)
            raw_errors[(key[0], key[1], key[2])] += int(row["logical_failure"])
            count += 1
    expected_count = len(sizes) * len(p_grid) * len(seeds) * shots_per_seed
    if count != expected_count or int(metadata["records"]) != expected_count:
        raise ValidationError(f"raw record count mismatch for {summary_path.name}")
    if any(raw_errors[key] != int(seed_rows[key]["logical_errors"]) for key in seed_rows):
        raise ValidationError(f"raw outcomes do not reproduce per-seed counts for {summary_path.name}")


def validate_shard(
    path: Path,
    manifest: dict,
    *,
    lab_dir: Path = LAB_DIR,
    expected_runtime: dict | None = None,
    expected_sources: dict | None = None,
    current_sources: dict[str, str] | None = None,
    validate_raw: bool = True,
) -> dict:
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1 or payload.get("campaign") != manifest["campaign"]:
        raise ValidationError(f"schema/campaign mismatch in {path.name}")
    filename_lattice = payload.get("lattice")
    filename_q = float(payload.get("q", -1))
    if path.name != artifact_filename(manifest, filename_lattice, filename_q):
        raise ValidationError(f"filename/payload q or lattice mismatch in {path.name}")
    lattice = filename_lattice
    if (
        list(payload.get("p_grid", [])) != list(manifest["p_grid"][lattice])
        or list(payload.get("sizes", [])) != list(manifest["sizes"])
        or list(payload.get("seeds", [])) != list(manifest["seeds"])
        or int(payload.get("shots_per_seed", -1)) != int(manifest["shots_per_seed"])
        or int(payload.get("total_shots_per_cell", -1))
        != len(manifest["seeds"]) * int(manifest["shots_per_seed"])
        or payload.get("decoder") != expected_decoder(manifest)
        or payload.get("sampling") != expected_sampling(lattice)
    ):
        raise ValidationError(f"manifest/config mismatch in {path.name}")
    if payload.get("config_sha256") != config_sha256(payload):
        raise ValidationError(f"config SHA-256 mismatch in {path.name}")
    runtime = _validate_runtime(payload.get("runtime"))
    sources = _validate_source_hashes(payload.get("source_hashes"), current_sources)
    stability = payload.get("source_stability")
    if "artifact_stem_template" in manifest and (
        not isinstance(stability, dict) or stability.get("start_equals_end") is not True
    ):
        raise ValidationError(f"missing/failed start-end source stability in {path.name}")
    fidelity = payload.get("syndrome_fidelity")
    if "artifact_stem_template" in manifest and (
        not isinstance(fidelity, dict) or fidelity.get("all_faithful") is not True
    ):
        raise ValidationError(f"missing/failed syndrome fidelity in {path.name}")
    if expected_runtime is not None and runtime != expected_runtime:
        raise ValidationError(f"mixed runtime provenance in {path.name}")
    if expected_sources is not None and sources != expected_sources:
        raise ValidationError(f"mixed source revisions in {path.name}")
    seed_rows, _ = _validate_rows(payload, manifest)
    if validate_raw:
        _validate_raw(payload, path, lab_dir, manifest, seed_rows)
    return payload


def curve_crossings(p_values: list[float], deltas: list[float], *, tolerance: float = 1e-15) -> list[dict]:
    """Return every zero interval and adjacent-grid sign change in order.

    A zero plateau is retained, but is a boundary candidate only when the
    nearest nonzero deltas on its two sides have opposite signs.  This avoids
    treating the common all-zero low-p LER plateau as a physical crossing.
    """
    if len(p_values) != len(deltas) or len(p_values) < 2:
        raise ValueError("crossing curves require equal vectors with at least two points")
    crossings: list[dict] = []
    index = 0
    while index < len(p_values):
        if abs(deltas[index]) <= tolerance:
            end = index
            while end + 1 < len(p_values) and abs(deltas[end + 1]) <= tolerance:
                end += 1
            left = deltas[index - 1] if index > 0 else None
            right = deltas[end + 1] if end + 1 < len(deltas) else None
            crossings.append({
                "kind": "exact_zero" if end == index else "zero_interval",
                "p_interval": [float(p_values[index]), float(p_values[end])],
                "estimate": float((p_values[index] + p_values[end]) / 2),
                "boundary_candidate": bool(left is not None and right is not None and left * right < 0),
            })
            index = end + 1
            continue
        if index + 1 < len(p_values) and abs(deltas[index + 1]) > tolerance and deltas[index] * deltas[index + 1] < 0:
            fraction = -deltas[index] / (deltas[index + 1] - deltas[index])
            crossings.append({
                "kind": "sign_change",
                "p_interval": [float(p_values[index]), float(p_values[index + 1])],
                "estimate": float(p_values[index] + fraction * (p_values[index + 1] - p_values[index])),
                "boundary_candidate": True,
            })
        index += 1
    return crossings


def analyze_q(payload: dict, manifest: dict, *, bootstrap_replicates: int, bootstrap_seed: int) -> dict:
    lattice = payload["lattice"]
    q = float(payload["q"])
    sizes = [int(value) for value in manifest["sizes"]]
    p_values = [float(value) for value in manifest["p_grid"][lattice]]
    seeds = [int(value) for value in manifest["seeds"]]
    seed_index = {seed: index for index, seed in enumerate(seeds)}
    size_index = {size: index for index, size in enumerate(sizes)}
    p_index = {p: index for index, p in enumerate(p_values)}
    counts = np.zeros((len(seeds), len(sizes), len(p_values)), dtype=float)
    shots = np.zeros_like(counts)
    for row in payload["per_seed"]:
        coordinate = (seed_index[int(row["seed"])], size_index[int(row["L"])], p_index[float(row["p"])])
        counts[coordinate] = int(row["logical_errors"])
        shots[coordinate] = int(row["shots"])
    observed = counts.sum(axis=0) / shots.sum(axis=0)
    rng = np.random.default_rng(np.random.SeedSequence([bootstrap_seed, 1 if lattice == "square" else 2, int(round(q * 100))]))
    bootstrap_rates = np.empty((bootstrap_replicates, len(sizes), len(p_values)), dtype=float)
    for size_offset in range(len(sizes)):
        # Size streams use distinct SeedSequence inputs in the simulator, so
        # resample them independently while preserving each seed's complete
        # nested-p trajectory within a size.
        draws = rng.integers(0, len(seeds), size=(bootstrap_replicates, len(seeds)))
        bootstrap_rates[:, size_offset, :] = (
            counts[:, size_offset, :][draws].sum(axis=1)
            / shots[:, size_offset, :][draws].sum(axis=1)
        )
    confidence = float(manifest.get("inference", {}).get("confidence_level", 0.95))
    alpha = 1.0 - confidence
    percentiles = [100 * alpha / 2, 100 * (1 - alpha / 2)]
    interval_key = f"interval{int(round(100 * confidence))}"

    pair_results = []
    pair_delta_bootstrap: dict[tuple[int, int], np.ndarray] = {}
    for lower_index, upper_index in zip(range(len(sizes) - 1), range(1, len(sizes))):
        lower, upper = sizes[lower_index], sizes[upper_index]
        deltas = observed[lower_index] - observed[upper_index]
        bootstrap_deltas = bootstrap_rates[:, lower_index, :] - bootstrap_rates[:, upper_index, :]
        pair_delta_bootstrap[(lower, upper)] = bootstrap_deltas
        observed_events = curve_crossings(p_values, deltas.tolist())
        observed_crossings = [item for item in observed_events if item["boundary_candidate"]]
        observed_ties = [item for item in observed_events if not item["boundary_candidate"]]
        bootstrap_crossings = [
            [item for item in curve_crossings(p_values, row.tolist()) if item["boundary_candidate"]]
            for row in bootstrap_deltas
        ]
        for ordinal, crossing in enumerate(observed_crossings):
            estimates = [items[ordinal]["estimate"] for items in bootstrap_crossings if len(items) > ordinal]
            crossing["bootstrap"] = {
                "cluster": "seed",
                "replicates": bootstrap_replicates,
                "ordinal_support": len(estimates) / bootstrap_replicates,
                "no_crossing_fraction": sum(not items for items in bootstrap_crossings) / bootstrap_replicates,
                "multiple_crossing_fraction": sum(len(items) > 1 for items in bootstrap_crossings) / bootstrap_replicates,
                interval_key: [float(value) for value in np.percentile(estimates, percentiles)] if estimates else None,
            }
        pair_results.append({
            "sizes": [lower, upper],
            "delta_definition": "LER(smaller)-LER(larger); positive is decodable trend",
            "deltas": [float(value) for value in deltas],
            "crossings": observed_crossings,
            "noncrossing_zero_ties": observed_ties,
        })

    cells = []
    for p_offset, p in enumerate(p_values):
        pair_evidence = []
        for pair in pair_results:
            lower, upper = pair["sizes"]
            values = pair_delta_bootstrap[(lower, upper)][:, p_offset]
            interval = np.percentile(values, percentiles)
            pair_evidence.append({
                "sizes": [lower, upper],
                "delta": pair["deltas"][p_offset],
                f"bootstrap_{interval_key}": [float(interval[0]), float(interval[1])],
                "probability_decodable_trend": float(np.mean(values > 0)),
            })
        cell_interval_key = f"bootstrap_{interval_key}"
        if all(item[cell_interval_key][0] > 0 for item in pair_evidence):
            classification = "decodable"
        elif all(item[cell_interval_key][1] < 0 for item in pair_evidence):
            classification = "undecodable"
        else:
            classification = "unresolved"
        cells.append({"p": p, "classification": classification, "adjacent_size_evidence": pair_evidence})

    crossing_counts = [len(pair["crossings"]) for pair in pair_results]
    all_deltas = np.asarray([pair["deltas"] for pair in pair_results])
    if all(count == 1 for count in crossing_counts):
        classification = "finite"
    elif all(count == 0 for count in crossing_counts):
        if np.all(all_deltas >= 0) and cells[-1]["classification"] == "decodable":
            classification = "ceiling"
        elif np.all(all_deltas <= 0) and cells[0]["classification"] == "undecodable":
            classification = "below-range"
        else:
            classification = "unresolved"
    else:
        classification = "unresolved"
    return {
        "q": q,
        "classification": classification,
        "cells": cells,
        "adjacent_size_crossings": pair_results,
        "evidence_boundary": "Seed-cluster bootstrap scouting classification; not a final finite-size scaling threshold.",
        "confidence_level": confidence,
    }


def plot_lattice(lattice: str, analyses: list[dict], manifest: dict, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11.4, 6.7), constrained_layout=True)
    cell_style = {
        "decodable": ("#2A9D8F", "o"),
        "undecodable": ("#E76F51", "s"),
        "unresolved": ("#B8B8B8", "x"),
    }
    for classification, (color, marker) in cell_style.items():
        points = [
            (cell["p"], analysis["q"])
            for analysis in analyses
            for cell in analysis["cells"]
            if cell["classification"] == classification
        ]
        if points:
            axis.scatter(
                [point[0] for point in points],
                [point[1] for point in points],
                color=color,
                marker=marker,
                s=28,
                alpha=0.82,
                label=f"cell: {classification}",
                zorder=2,
            )
    pair_styles = [
        ("#264653", "o", "-"),
        ("#F4A261", "D", "--"),
        ("#6A4C93", "^", ":"),
        ("#118AB2", "v", "-."),
        ("#8D6E63", "P", (0, (3, 1, 1, 1))),
    ]
    sizes = [int(value) for value in manifest["sizes"]]
    confidence = float(manifest.get("inference", {}).get("confidence_level", 0.95))
    interval_key = f"interval{int(round(100 * confidence))}"
    for pair_offset, (lower, upper) in enumerate(zip(sizes[:-1], sizes[1:])):
        color, marker, line_style = pair_styles[pair_offset % len(pair_styles)]
        single_q = []
        single_p = []
        single_low = []
        single_high = []
        multiple_q = []
        multiple_p = []
        for analysis in analyses:
            pair = analysis["adjacent_size_crossings"][pair_offset]
            for crossing in pair["crossings"]:
                estimate = crossing["estimate"]
                interval = crossing["bootstrap"][interval_key]
                target_q = multiple_q if len(pair["crossings"]) > 1 else single_q
                target_p = multiple_p if len(pair["crossings"]) > 1 else single_p
                target_q.append(analysis["q"])
                target_p.append(estimate)
                if len(pair["crossings"]) == 1:
                    single_low.append(0.0 if interval is None else max(0.0, estimate - interval[0]))
                    single_high.append(0.0 if interval is None else max(0.0, interval[1] - estimate))
        if single_q:
            order = np.argsort(single_q)
            x = np.asarray(single_p)[order]
            y = np.asarray(single_q)[order]
            xerr = np.asarray([single_low, single_high])[:, order]
            axis.errorbar(
                x,
                y,
                xerr=xerr,
                color=color,
                marker=marker,
                linestyle=line_style,
                linewidth=1.45,
                capsize=2.3,
                label=f"L{lower}/L{upper} crossing ({confidence:.0%} seed bootstrap)",
                zorder=4,
            )
        if multiple_q:
            axis.scatter(
                multiple_p,
                multiple_q,
                color=color,
                marker="X",
                s=60,
                edgecolor="white",
                linewidth=0.5,
                label=f"L{lower}/L{upper} multiple crossings",
                zorder=5,
            )
    top = max(manifest["p_grid"][lattice])
    bottom = min(manifest["p_grid"][lattice])
    ceiling_q = [item["q"] for item in analyses if item["classification"] == "ceiling"]
    below_q = [item["q"] for item in analyses if item["classification"] == "below-range"]
    if ceiling_q:
        axis.scatter([top] * len(ceiling_q), ceiling_q, marker=">", s=95, facecolors="none", edgecolors="#1B7F79", linewidth=1.8, label="boundary above grid / ceiling-compatible", zorder=6)
    if below_q:
        axis.scatter([bottom] * len(below_q), below_q, marker="<", s=95, facecolors="none", edgecolors="#C44536", linewidth=1.8, label="boundary below grid", zorder=6)
    axis.set(
        title=f"Lab 003 Phase 2 {lattice}: q-p scouting cells and adjacent-size boundaries",
        xlabel="physical edge-error rate p",
        ylabel="herald efficiency q",
        xlim=(bottom - 0.025, min(0.5, top + 0.025)),
        ylim=(-0.025, 1.025),
    )
    axis.set_yticks(np.arange(0, 1.01, 0.1))
    axis.grid(alpha=0.19)
    handles, labels = axis.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axis.legend(unique.values(), unique.keys(), fontsize=8, ncol=2, loc="best")
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=200)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-dir", type=Path, default=LAB_DIR / "results")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--figures-dir", type=Path, default=LAB_DIR / "figures")
    parser.add_argument("--bootstrap-replicates", type=int)
    parser.add_argument("--bootstrap-seed", type=int)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    inference = manifest.get("inference", {})
    bootstrap_replicates = args.bootstrap_replicates or int(inference.get("bootstrap_replicates", 2000))
    bootstrap_seed = args.bootstrap_seed or int(inference.get("bootstrap_seed", 320027))
    if bootstrap_replicates < 100:
        raise SystemExit("bootstrap-replicates must be at least 100")
    paths = discover_shards(args.results_dir, manifest)
    current_sources = {name: sha256(path) for name, path in SOURCE_FILES.items()}
    payloads: dict[tuple[str, float], dict] = {}
    runtime = None
    sources = None
    for key, path in sorted(paths.items()):
        payload = validate_shard(
            path,
            manifest,
            lab_dir=LAB_DIR,
            expected_runtime=runtime,
            expected_sources=sources,
            current_sources=current_sources,
        )
        runtime = payload["runtime"] if runtime is None else runtime
        sources = payload["source_hashes"] if sources is None else sources
        payloads[key] = payload
    analyses = {
        lattice: [
            analyze_q(payloads[(lattice, q)], manifest, bootstrap_replicates=bootstrap_replicates, bootstrap_seed=bootstrap_seed)
            for q in manifest["q_values"]
        ]
        for lattice in manifest["lattices"]
    }
    figure_paths = {
        lattice: args.figures_dir / f"{manifest['campaign']}-{lattice}-phase-map.png"
        for lattice in manifest["lattices"]
    }
    for lattice in manifest["lattices"]:
        plot_lattice(lattice, analyses[lattice], manifest, figure_paths[lattice])
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "campaign": manifest["campaign"],
        "manifest": str(args.manifest),
        "validated_artifacts": [str(paths[key]) for key in sorted(paths)],
        "runtime": runtime,
        "source_hashes": sources,
        "bootstrap": {
            "cluster": "seed trajectory within size",
            "replicates": bootstrap_replicates,
            "seed": bootstrap_seed,
            "confidence_level": float(inference.get("confidence_level", 0.95)),
        },
        "lattices": analyses,
        "figures": {lattice: str(path) for lattice, path in figure_paths.items()},
        "evidence_boundary": (
            "Complete common-grid Phase 2 scouting analysis. Cell labels and adjacent-size crossing intervals "
            "are seed-cluster bootstrap diagnostics, not final asymptotic thresholds. Multiple crossings are retained."
        ),
    }
    output_json = args.output_json or LAB_DIR / "results" / f"{manifest['campaign']}-analysis.json"
    atomic_json(output_json, output)
    print(json.dumps({
        "output": str(output_json),
        "figures": output["figures"],
        "classifications": {
            lattice: {f"{item['q']:.2f}": item["classification"] for item in values}
            for lattice, values in analyses.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
