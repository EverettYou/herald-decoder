"""Truth-referenced recovery scoring for the published D4 decoder.

Only the source-controlled flux stage is implemented here.  The source's
second stage first derives effective blue/green Pauli-Z strings after flux
correction using disjoint-set connectivity and local fusion rules.  Treating
those strings as ordinary honeycomb edge chains without that derivation would
change the decoder, so charge recovery remains an explicit later gate.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from d4_honeycomb import PeriodicHoneycomb
from d4_matching import (
    D4FluxRecoveryResult,
    classify_closed_chain,
    classify_physical_correction_union,
    compose_edge_chains,
    decode_flux_syndrome,
    edge_chain_boundary,
    physical_correction_union,
)


def decode_and_score_flux_recovery(
    lattice: PeriodicHoneycomb,
    physical_error: NDArray[np.generic],
    edge_weights: NDArray[np.generic],
) -> D4FluxRecoveryResult:
    """Decode a flux syndrome and score the residual homology against truth."""

    physical = np.asarray(physical_error, dtype=np.uint8)
    syndrome = edge_chain_boundary(lattice, physical)
    decoded = decode_flux_syndrome(lattice, syndrome, edge_weights)
    residual = compose_edge_chains(lattice, physical, decoded.correction)
    residual_analysis = classify_closed_chain(lattice, residual)
    union = physical_correction_union(lattice, physical, decoded.correction)
    union_analysis = classify_physical_correction_union(
        lattice, physical, decoded.correction
    )
    logical_error = any(
        not component.homologically_trivial
        for component in union_analysis.components
    )
    return D4FluxRecoveryResult(
        syndrome=syndrome,
        correction=decoded.correction,
        residual=residual,
        residual_analysis=residual_analysis,
        physical_correction_union=union,
        union_analysis=union_analysis,
        objective_weight=decoded.objective_weight,
        logical_error=logical_error,
    )
