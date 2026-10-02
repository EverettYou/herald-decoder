"""Stable selection of decoding methods with one visible-record interface."""
from .herald_bp_decoder import HeraldBeliefMatchingDecoder,SyndromeOnlyMatchingDecoder
from .configuration_map import HeraldConfigurationMAPDecoder
from .planar_ml import HeraldPlanarMLDecoder
from .transfer_ml import HeraldTransferMLDecoder
from .mps_ml import HeraldMPSDecoder

DECODER_METHODS={
    'bp_matching':{'label':'BP + posterior-LLR matching','objective':'marginal-based matching','geometry':['square','honeycomb']},
    'configuration_map':{'label':'Configuration MAP matching','objective':'maximum posterior configuration','geometry':['honeycomb']},
    'planar_ml':{'label':'Planar logical ML','objective':'logical-sector Bayes risk','geometry':['honeycomb']},
    'transfer_ml':{'label':'Exact transfer logical ML','objective':'logical-sector Bayes risk; width cap','geometry':['square','honeycomb']},
    'mps_ml':{'label':'MPS logical inference','objective':'approximate logical-sector Bayes risk','geometry':['honeycomb']},
}

def make_decoder(graph,method='bp_matching',*,p,q,**options):
    classes={'bp_matching':HeraldBeliefMatchingDecoder,'configuration_map':HeraldConfigurationMAPDecoder,'planar_ml':HeraldPlanarMLDecoder,'transfer_ml':HeraldTransferMLDecoder,'mps_ml':HeraldMPSDecoder}
    if method not in classes:raise ValueError(f'unknown method {method!r}; choose from {tuple(classes)}')
    return classes[method](graph,p=p,q=q,**options)
