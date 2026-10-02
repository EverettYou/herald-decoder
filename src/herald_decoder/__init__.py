"""Stable simulator and posterior-LLR decoder API shared by research Labs."""

from .herald_bp_decoder import HeraldAwareBpMatchingDecoder, HeraldBeliefMatchingDecoder, SyndromeOnlyMatchingDecoder
from .lattice_model import LatticeGraph, honeycomb_graph, sample_observation, square_graph
from .numba_bp_kernels import NUMBA_AVAILABLE

__all__ = [
    "HeraldAwareBpMatchingDecoder",
    "HeraldBeliefMatchingDecoder",
    "SyndromeOnlyMatchingDecoder",
    "LatticeGraph",
    "honeycomb_graph",
    "sample_observation",
    "square_graph",
    "NUMBA_AVAILABLE",
]

from .sector import SectorResult, NumericalInferenceError
from .configuration_map import HeraldConfigurationMAPDecoder
from .planar_ml import HeraldPlanarMLDecoder, PlanarParitySolver
from .transfer_ml import HeraldTransferMLDecoder
from .mps_ml import HeraldMPSDecoder
from .registry import DECODER_METHODS, make_decoder

__all__ += [
    'SectorResult', 'NumericalInferenceError', 'HeraldConfigurationMAPDecoder',
    'HeraldPlanarMLDecoder', 'PlanarParitySolver', 'HeraldTransferMLDecoder',
    'HeraldMPSDecoder', 'DECODER_METHODS', 'make_decoder',
]
