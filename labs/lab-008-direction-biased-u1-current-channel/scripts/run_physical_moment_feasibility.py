"""Evaluate the registered physical even-moment interval feasibility matrix."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from current_oracle import LAB, ROOT, exact_enumeration, square_graph


MANIFEST = LAB / "manifests/physical-moment-feasibility-2026-09-19.json"
RESULT = LAB / "results/physical-moment-feasibility-2026-09-19.json"
DEGREES = (1, 2, 4, 8, 16, 32)
BOOTSTRAPS = 4000
SEED = 919113624


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval_rows(m: np.ndarray, weights: np.ndarray) -> tuple[float, list[dict]]:
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    m = np.asarray(m, dtype=float)
    y = 1.0 - m * m
    truth = float(np.sum(weights * (1.0 - np.abs(m))) / 2.0)
    rows = []
    for n in DEGREES:
        lower = 0.0
        for k in range(1, n + 1):
            a = math.comb(2 * k, k) / (4.0**k * (2 * k - 1))
            lower += 0.5 * a * float(np.sum(weights * y**k))
        coefficient = math.comb(2 * n, n) / (2.0 * 4.0**n)
        width = coefficient * float(np.sum(weights * y ** (n + 1)))
        upper = lower + width
        assert lower <= truth + 2e-13
        assert truth <= upper + 2e-13
        rows.append({"N": n, "lower": lower, "upper": upper, "width": width})
    return truth, rows


def exact_l3(p: float, q: float) -> dict:
    table = exact_enumeration(square_graph(3), p, q)
    probs, m = [], []
    for z, _, _ in table.values():
        total = float(z.sum())
        probs.append(total)
        m.append(float((z[0] - z[1]) / total))
    truth, rows = interval_rows(np.array(m), np.array(probs))
    return {"L": 3, "p": p, "q": q, "records": len(table), "risk": truth, "series": rows}


def stored_l5(path: Path, rng: np.random.Generator) -> dict:
    data = json.loads(path.read_text())
    probs = np.array([record["sector_probabilities"] for record in data["records"]], dtype=float)
    m = probs[:, 0] - probs[:, 1]
    weights = np.ones(len(m), dtype=float) / len(m)
    truth, rows = interval_rows(m, weights)
    indices = rng.integers(0, len(m), size=(BOOTSTRAPS, len(m)))
    y = 1.0 - m * m
    for row in rows:
        n = row["N"]
        coefficient = math.comb(2 * n, n) / (2.0 * 4.0**n)
        replicate_width = coefficient * np.mean(y[indices] ** (n + 1), axis=1)
        row["width_bootstrap95"] = [float(x) for x in np.quantile(replicate_width, [0.025, 0.975])]
    cell = data["cell"]
    return {
        "id": cell["id"], "L": 5, "p": float(cell["p"]), "q": float(cell["q"]),
        "records": len(m), "risk": truth, "series": rows,
        "source": str(path.relative_to(ROOT)),
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    exact = [exact_l3(p, q) for p in manifest["exact_L3_grid"]["p"] for q in manifest["exact_L3_grid"]["q"]]
    rng = np.random.default_rng(SEED)
    paths = [LAB / rel for rel in manifest["stored_L5_cells"]]
    empirical = [stored_l5(path, rng) for path in paths]
    primary = [row for row in empirical if row["q"] in (0.5, 0.75) and row["p"] in (0.1, 0.3)]
    gate_rows = []
    for cell in primary:
        final = next(row for row in cell["series"] if row["N"] == 32)
        passed = final["width"] <= 0.01 and final["width_bootstrap95"][1] <= 0.0125
        gate_rows.append({
            "id": cell["id"], "width": final["width"],
            "width_bootstrap95": final["width_bootstrap95"], "passed": passed,
        })
    passed = all(row["passed"] for row in gate_rows)
    decision = "retain_physical_moment_interface_design" if passed else "close_physical_moment_compression"
    sources = [Path(__file__), MANIFEST, LAB / "scripts/current_oracle.py", ROOT / "src/herald_decoder/lattice_model.py", *paths]
    out = {
        "status": "complete", "scope": manifest["scope"], "moment_degrees": list(DEGREES),
        "exact_L3": exact, "stored_L5": empirical,
        "primary_gate": {"thresholds": {"point_width": 0.01, "bootstrap95_upper": 0.0125},
                         "cells": gate_rows, "passed": passed},
        "decision": decision,
        "next_action": ("Register one physical R-to-1 moment interface design without production computation."
                        if passed else "Do not implement replica transfer for this statistic; retain the unresolved analytic band."),
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sources},
    }
    RESULT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "decision": decision, "primary_gate": out["primary_gate"]}, indent=2))


if __name__ == "__main__":
    main()
