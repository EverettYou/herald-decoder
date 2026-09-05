"""Branch-resolved helpers for the corrected R4.5c sequential preflight."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from d4_charge import ChargeLattice, charge_chain_boundary
from d4_charge_multigraph import (
    ChargeBranch,
    BranchPostFluxRelations,
    branch_chain_sector,
    build_branch_charge_lattice,
    build_charge_branch_catalog,
)
from d4_honeycomb import BLUE, GREEN, PeriodicHoneycomb


@dataclass(frozen=True)
class BranchRepresentativeContext:
    """Reusable immutable geometry for one charge colour."""

    lattice: PeriodicHoneycomb
    color: int
    charge_lattice: ChargeLattice
    catalog_by_id: dict[int, ChargeBranch]


def build_branch_representative_context(
    lattice: PeriodicHoneycomb,
    color: int,
) -> BranchRepresentativeContext:
    if color not in (BLUE, GREEN):
        raise ValueError("color must be BLUE or GREEN")
    catalog = build_charge_branch_catalog(lattice, color)
    return BranchRepresentativeContext(
        lattice=lattice,
        color=color,
        charge_lattice=build_branch_charge_lattice(lattice, color),
        catalog_by_id={branch.branch_id: branch for branch in catalog},
    )


@dataclass(frozen=True)
class RelationKernelAudit:
    """Exact GF(2) cycle-kernel audit for one colour relation subgraph."""

    color: int
    branch_ids: tuple[int, ...]
    candidate_chain_count: int
    kernel_chain_count: int
    nontrivial_kernel_count: int
    first_nontrivial_mask: int | None
    first_nontrivial_sector: tuple[int, int] | None

    @property
    def passed(self) -> bool:
        return self.nontrivial_kernel_count == 0


def relation_branch_ids(
    relations: BranchPostFluxRelations,
    color: int,
) -> tuple[int, ...]:
    """Return the stable physical branches present for one charge colour."""

    if color not in (BLUE, GREEN):
        raise ValueError("color must be BLUE or GREEN")
    selected = tuple(
        sorted(relation.branch_id for relation in relations.relations if relation.color == color)
    )
    if len(selected) != len(set(selected)):
        raise ValueError("branch-resolved relations contain a duplicate physical branch")
    return selected


def audit_relation_cycle_kernel(
    lattice: PeriodicHoneycomb,
    color: int,
    branch_ids: tuple[int, ...],
    context: BranchRepresentativeContext | None = None,
) -> RelationKernelAudit:
    """Require the period cochain to vanish on every relation-cycle kernel element."""

    geometry = context or build_branch_representative_context(lattice, color)
    if geometry.lattice is not lattice or geometry.color != color:
        raise ValueError("representative context does not match lattice and colour")
    charge_lattice = geometry.charge_lattice
    ids = tuple(sorted(int(branch_id) for branch_id in branch_ids))
    if len(ids) != len(set(ids)) or any(
        branch_id < 0 or branch_id >= charge_lattice.edge_count for branch_id in ids
    ):
        raise ValueError("branch_ids must be unique valid physical branch ids")
    kernel_count = 0
    nontrivial = 0
    first_mask = None
    first_sector = None
    for local_mask in range(1 << len(ids)):
        chain = np.zeros(charge_lattice.edge_count, dtype=np.uint8)
        for local_edge, branch_id in enumerate(ids):
            chain[branch_id] = (local_mask >> local_edge) & 1
        if np.any(charge_chain_boundary(charge_lattice, chain)):
            continue
        kernel_count += 1
        sector = branch_chain_sector(lattice, color, chain)
        if sector != (0, 0):
            nontrivial += 1
            if first_mask is None:
                first_mask = local_mask
                first_sector = sector
    return RelationKernelAudit(
        color=color,
        branch_ids=ids,
        candidate_chain_count=1 << len(ids),
        kernel_chain_count=kernel_count,
        nontrivial_kernel_count=nontrivial,
        first_nontrivial_mask=first_mask,
        first_nontrivial_sector=first_sector,
    )


def effective_branch_chain_from_record(
    lattice: PeriodicHoneycomb,
    color: int,
    relations: BranchPostFluxRelations,
    binary_record: tuple[int, ...] | NDArray[np.generic],
    context: BranchRepresentativeContext | None = None,
) -> NDArray[np.uint8]:
    """Choose a stable-branch spanning-forest representative of one measured boundary."""

    if color not in (BLUE, GREEN):
        raise ValueError("color must be BLUE or GREEN")
    record = np.asarray(binary_record, dtype=np.uint8)
    if record.shape != (lattice.vertex_count,) or np.any(record > 1):
        raise ValueError("binary_record must be binary on every honeycomb vertex")
    geometry = context or build_branch_representative_context(lattice, color)
    if geometry.lattice is not lattice or geometry.color != color:
        raise ValueError("representative context does not match lattice and colour")
    charge_lattice = geometry.charge_lattice
    by_id = geometry.catalog_by_id
    active = tuple(
        vertex for vertex in relations.active_vertices if int(lattice.vertex_colors[vertex]) == color
    )
    active_set = set(active)
    inactive = set(int(vertex) for vertex in charge_lattice.vertex_ids) - active_set
    if any(record[vertex] for vertex in inactive):
        raise ValueError("binary record is nonzero outside the hidden active support")

    color_relations = tuple(
        sorted(
            (relation for relation in relations.relations if relation.color == color),
            key=lambda relation: relation.branch_id,
        )
    )
    for relation in color_relations:
        branch = by_id[relation.branch_id]
        if branch.endpoints != relation.endpoints or not set(branch.endpoints) <= active_set:
            raise ValueError("relation branch provenance or active support is inconsistent")

    parent = {vertex: vertex for vertex in active}

    def find(vertex: int) -> int:
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    forest = []
    for relation in color_relations:
        left, right = relation.endpoints
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            continue
        parent[right_root] = left_root
        forest.append(relation)

    adjacency: dict[int, list[tuple[int, int]]] = {vertex: [] for vertex in active}
    for relation in forest:
        left, right = relation.endpoints
        adjacency[left].append((right, relation.branch_id))
        adjacency[right].append((left, relation.branch_id))
    for values in adjacency.values():
        values.sort(key=lambda value: (value[1], value[0]))

    selected = np.zeros(charge_lattice.edge_count, dtype=np.uint8)
    unseen = set(active)
    while unseen:
        root = min(unseen)
        tree_parent: dict[int, int | None] = {root: None}
        parent_edge: dict[int, int] = {}
        order = [root]
        for vertex in order:
            unseen.discard(vertex)
            for neighbor, branch_id in adjacency[vertex]:
                if neighbor in tree_parent:
                    continue
                tree_parent[neighbor] = vertex
                parent_edge[neighbor] = branch_id
                order.append(neighbor)
        parity = {vertex: int(record[vertex]) for vertex in order}
        for vertex in reversed(order[1:]):
            ancestor = tree_parent[vertex]
            if ancestor is None:
                raise RuntimeError("non-root forest vertex lacks a parent")
            if parity[vertex]:
                selected[parent_edge[vertex]] ^= 1
                parity[ancestor] ^= 1
        if parity[root]:
            raise ValueError("relation component has odd measured charge parity")

    expected = np.asarray(
        [record[int(vertex)] for vertex in charge_lattice.vertex_ids], dtype=np.uint8
    )
    if not np.array_equal(charge_chain_boundary(charge_lattice, selected), expected):
        raise RuntimeError("constructed branch representative has the wrong measured boundary")
    return selected
