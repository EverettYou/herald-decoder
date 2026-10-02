"""Validate the canonical geometry assumptions of the specialized reductions."""
from functools import lru_cache
from .lattice_model import honeycomb_graph


def signature(graph):
    coordinates = tuple((round(v.x, 10), round(v.y, 10)) for v in graph.vertices)
    vertices = frozenset((coordinates[i], v.detector, v.boundary_side) for i, v in enumerate(graph.vertices))
    edges = frozenset(tuple(sorted((coordinates[u], coordinates[v]))) for u, v in graph.edges)
    logical = frozenset(tuple(sorted((coordinates[graph.edges[e][0]], coordinates[graph.edges[e][1]]))) for e in graph.logical_edges)
    return len(coordinates), len(graph.edges), vertices, edges, logical


@lru_cache(maxsize=16)
def canonical_signature(size):
    return signature(honeycomb_graph(size))


def require_canonical_honeycomb(graph):
    # Set comparisons permit vertex/edge relabeling but reject a name-only match.
    if graph.name != 'honeycomb' or signature(graph) != canonical_signature(graph.size):
        raise ValueError('this method requires the canonical honeycomb geometry and package logical cut')
