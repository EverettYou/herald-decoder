"""Check geometry behind the all-size bulk-charge independence lemma.

No physical histories or new sizes are generated. The proof itself is the
disjoint-edge sigma-algebra argument recorded in the owning Local Wiki.
"""

from __future__ import annotations

import hashlib
import json
from math import sqrt
from pathlib import Path

from herald_decoder.lattice_model import square_graph


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
RETAINED = LAB / "results/h12-physical-charge-prefix-affinity-2026-09-23.json"
RESULT = LAB / "results/h12-bulk-charge-independence-2026-09-23.json"
P = 0.3
TOL = 1e-12


def main() -> None:
    checks = []
    for size in (3, 5, 7, 11):
        graph = square_graph(size)
        cut = set(graph.logical_edges)
        bulk = {v for v in graph.detector_vertices if graph.vertices[v].x <= size - 3}
        strip = {v for v in graph.detector_vertices if graph.vertices[v].x == size - 2}
        assert len(bulk) == size * (size - 3)
        assert len(strip) == size
        assert bulk | strip == set(graph.detector_vertices)
        bulk_edges = {e for v in bulk for e in graph.incident_edges[v]}
        overlap = bulk_edges & cut
        assert not overlap
        assert len(cut) == size
        for e in cut:
            endpoints = set(graph.edges[e])
            assert len(endpoints & strip) == 1
            assert len(endpoints & bulk) == 0
            assert len(endpoints & set(graph.boundary_vertices)) == 1
        checks.append({
            "L": size,
            "bulk_charge_vertices": len(bulk),
            "cut_adjacent_charge_vertices": len(strip),
            "logical_cut_edges": len(cut),
            "bulk_incidence_cut_overlap": len(overlap),
            "cut_endpoint_gate": "pass",
        })
    retained = json.loads(RETAINED.read_text())
    prior_contrast = (1 - 2 * P) ** 3
    pi0 = (1 + prior_contrast) / 2
    pi1 = (1 - prior_contrast) / 2
    initial_affinity = sqrt(pi0 * pi1)
    errors = [
        abs(cell["orders"][0]["prefix_affinity"][0] - initial_affinity)
        for cell in retained["cells"]
    ]
    assert len(errors) == 3 and max(errors) < TOL
    result = {
        "id": "lab008-h12-bulk-charge-independence-2026-09-23",
        "status": "passed_geometry_and_retained_exact_control",
        "source_manifest": "../manifests/h12-bulk-charge-independence-2026-09-23.json",
        "source_sha256": hashlib.sha256((ROOT / "src/herald_decoder/lattice_model.py").read_bytes()).hexdigest(),
        "retained_result_sha256": hashlib.sha256(RETAINED.read_bytes()).hexdigest(),
        "sampling": {"new_physical_samples": 0, "new_system_sizes": 0, "bootstrap_replicates": 0},
        "theorem": "Every charge at x<=L-3 is a function only of non-cut independent edge currents, while H is a function only of the L right-cut edge activities. Hence Q_bulk is independent of H at all L and all independent edge priors; any bulk-only prefix leaves sector affinity at sqrt(pi0*pi1).",
        "sector_priors_at_p_0_3_L3": {"pi0": pi0, "pi1": pi1, "initial_affinity": initial_affinity},
        "maximum_retained_L3_affinity_error": max(errors),
        "geometry_checks": checks,
        "claim_boundary": "The all-size independence is only for bulk charges before conditioning on the cut-adjacent strip. The full record may distinguish H through that strip; no p=.30 phase follows.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "maximum_error": max(errors)}))


if __name__ == "__main__":
    main()
