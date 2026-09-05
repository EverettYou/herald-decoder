#!/usr/bin/env python3
"""Audit whether Lab 003 q=3/4 and corrected D4 records share a channel.

This is a record- and convention-level audit.  It deliberately performs no
threshold fitting and consumes no withdrawn support-revealing BP evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1]
ROOT = LAB_DIR.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(LAB_DIR / "scripts"))

from herald_decoder.lattice_model import honeycomb_graph  # noqa: E402
from d4_honeycomb import paper_periodic_honeycomb  # noqa: E402


LAB003_MANIFEST = (
    ROOT
    / "labs/lab-003-herald-threshold-phase-diagram/manifests/"
    "phase-b14-honeycomb-two-branch-acquisition-manifest-2026-08-28.json"
)
R6AC_AUDIT = LAB_DIR / "manifests/r6ac-d4-sublattice-herald-model-audit-2026-08-31.json"
R6AE_MANIFEST = LAB_DIR / "manifests/r6ae-signal-only-bp-threshold-manifest-2026-09-01.json"
DEFAULT_OUTPUT = LAB_DIR / "results/p4-lab003-d4-channel-equivalence-audit-2026-09-01.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing required evidence: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit() -> dict:
    lab003 = _load(LAB003_MANIFEST)
    r6ac = _load(R6AC_AUDIT)
    r6ae = _load(R6AE_MANIFEST)
    if r6ac.get("signal_only_event_table_gate_passed") is not True:
        raise RuntimeError("corrected D4 signal-only event-table gate is not passed")
    if r6ae.get("status") != "completed_at_registered_cap_no_threshold":
        raise RuntimeError("R6AE is not closed at its registered cap")

    lab003_graph = honeycomb_graph(5)
    d4_graph = paper_periodic_honeycomb(5)
    lab003_event_table = [
        {"degree": degree, "P_h_equals_1": 0.75 if degree >= 2 else 0.0}
        for degree in range(4)
    ]
    d4_event_table = [
        {
            "degree": degree,
            "P_matching_colour_e_signal": 0.5 if degree == 2 else 0.0,
            "P_zero_signal": 0.5 if degree == 2 else 1.0,
            "P_wrong_colour_e_signal": 0.0,
        }
        for degree in range(4)
    ]
    phase_decoder = lab003.get("decoder", lab003.get("decoder_configuration", {}))
    r6ae_decoder = r6ae["scan_design"]["bp_defaults"]

    matrix = [
        {
            "dimension": "latent physical event",
            "status": "partial_form_match_only",
            "lab_003": "IID Bernoulli-p errors on every retained edge of an open honeycomb patch.",
            "d4": "IID Bernoulli-p_X red-X error edges on the paper periodic coloured honeycomb quotient.",
            "consequence": "The local Bernoulli form matches, but the edge spaces and physical channel do not.",
        },
        {
            "dimension": "herald conditioning",
            "status": "non_equivalent",
            "lab_003": "Uncoloured h=1 independently with probability 3/4 whenever degree>=2.",
            "d4": "Matching-colour e_B/e_G signal with probability 1/2 only at degree=2; zero is ambiguous between vacuum and absent support.",
            "consequence": "Degree-2 probabilities differ and degree-3 support is disjoint.",
        },
        {
            "dimension": "correlation structure",
            "status": "non_equivalent",
            "lab_003": "Herald draws are conditionally independent across eligible vertices.",
            "d4": "Colour-resolved e signals obey component parity constraints; the six-vertex hexagon has 16 allowed records rather than 64 independent binary records.",
            "consequence": "No vertexwise deterministic coarse-graining preserves the joint law.",
        },
        {
            "dimension": "geometry and boundary",
            "status": "non_equivalent",
            "lab_003": "Open rough-boundary honeycomb patch with one recorded logical cut.",
            "d4": "Periodic torus with coloured A/B sublattices and two primitive winding directions.",
            "consequence": "The same size label denotes different graphs and logical sectors.",
        },
        {
            "dimension": "error parameter",
            "status": "not_calibrated",
            "lab_003": "p is the retained-edge Bernoulli probability on the open phenomenological graph.",
            "d4": "p_X is the red-X edge probability on the periodic D4 graph; p_Z=0 in R6AE.",
            "consequence": "Equal numeric p and p_X do not define a common channel coordinate.",
        },
        {
            "dimension": "decoder-visible record",
            "status": "non_equivalent",
            "lab_003": "One parity syndrome plus an uncoloured binary herald field H.",
            "d4": "Flux syndrome plus sublattice-labelled binary e_B/e_G signals; hidden degree-two support is unavailable.",
            "consequence": "The information budgets and sufficient statistics differ.",
        },
        {
            "dimension": "decoder",
            "status": "non_equivalent",
            "lab_003": "Phenomenological factor graph, damping 0.25, stable-sort residual-priority BP, 80-iteration cap, posterior-LLR MWPM.",
            "d4": "D4 local coloured-flow factors, damping 0.25, synchronous dense BP, 40-iteration cap, posterior-LLR MWPM; O0 and O2 are separate arms.",
            "consequence": "The common BP-to-MWPM label does not make the algorithms or likelihoods identical.",
        },
        {
            "dimension": "logical-loss convention",
            "status": "non_equivalent",
            "lab_003": "Parity of error XOR correction across one open-patch logical cut.",
            "d4": "Paper-unconditional first-stage Boolean union over periodic winding sectors, with physical winding already terminal failure.",
            "consequence": "Reported LERs are different observables and denominators.",
        },
    ]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete_non_equivalence_audit",
        "question": "Can Lab 003 q=3/4 and corrected signal-only D4 data be compared as one channel?",
        "verdict": "non_equivalent_cross_lab_numerical_comparison_prohibited",
        "comparison_allowed": False,
        "shared_structure": [
            "binary edge variables with an IID Bernoulli local prior form",
            "vertex parity syndrome as a marginal observation",
            "matching-based correction after a belief front end",
        ],
        "lab_003_event_table": lab003_event_table,
        "corrected_d4_signal_event_table": d4_event_table,
        "closed_hexagon_support": {
            "lab_003_conditional_independent_binary_support": 64,
            "d4_colour_parity_constrained_support": 16,
        },
        "size_5_geometry": {
            "lab_003": {
                "vertices": len(lab003_graph.vertices),
                "edges": len(lab003_graph.edges),
                "boundary_vertices": len(lab003_graph.boundary_vertices),
                "logical_cut_edges": len(lab003_graph.logical_edges),
            },
            "d4": {
                "vertices": d4_graph.vertex_count,
                "edges": d4_graph.edge_count,
                "boundary_vertices": 0,
                "primitive_winding_directions": 2,
            },
        },
        "decoder_provenance": {
            "lab_003_manifest": str(LAB003_MANIFEST.relative_to(ROOT)),
            "lab_003_manifest_decoder": phase_decoder,
            "r6ae_manifest": str(R6AE_MANIFEST.relative_to(ROOT)),
            "r6ae_bp_defaults": r6ae_decoder,
        },
        "equivalence_matrix": matrix,
        "candidate_reductions": [
            {
                "name": "degree-at-most-two support-only q=1 fixture",
                "status": "toy_support_alignment_only",
                "reason": "Conditions the physical ensemble, discards D4 signal values/correlations, changes q, geometry, decoder, and loss.",
            },
            {
                "name": "randomly thin D4 degree-two signals to an apparent 3/4 rate",
                "status": "new_hybrid_channel_not_equivalence",
                "reason": "Added randomness cannot create Lab 003 degree-three herald support or remove D4 component correlations without changing the record.",
            },
        ],
        "acceptance": {
            "latent_event_checked": True,
            "herald_conditioning_checked": True,
            "correlations_checked": True,
            "geometry_checked": True,
            "error_parameter_checked": True,
            "decoder_visible_record_checked": True,
            "decoder_checked": True,
            "logical_loss_checked": True,
            "all_required_evidence_present": True,
        },
        "evidence": [
            str(R6AC_AUDIT.relative_to(ROOT)),
            str(R6AE_MANIFEST.relative_to(ROOT)),
            str(LAB003_MANIFEST.relative_to(ROOT)),
            "src/herald_decoder/lattice_model.py",
            "src/herald_decoder/herald_bp_decoder.py",
            "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_honeycomb.py",
            "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/run_r6v_x_only_flux_threshold_scan.py",
        ],
        "claim_boundary": "This audit prohibits direct numerical threshold or LER comparison. It does not assert that no separately derived common channel can ever be constructed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_audit()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "verdict": payload["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
