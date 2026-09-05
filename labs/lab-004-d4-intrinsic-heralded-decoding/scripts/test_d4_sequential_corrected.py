from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d4_charge import charge_chain_boundary  # noqa: E402
from d4_charge_multigraph import (  # noqa: E402
    BranchPostFluxRelations,
    BranchRelation,
    build_branch_charge_lattice,
    build_charge_branch_catalog,
)
from d4_honeycomb import BLUE, periodic_honeycomb  # noqa: E402
from d4_sequential_corrected import (  # noqa: E402
    audit_relation_cycle_kernel,
    effective_branch_chain_from_record,
)


def test_empty_relation_support_has_zero_representative_and_trivial_kernel() -> None:
    lattice = periodic_honeycomb(2)
    relations = BranchPostFluxRelations((), ())
    record = (0,) * lattice.vertex_count
    representative = effective_branch_chain_from_record(
        lattice, BLUE, relations, record
    )
    assert not np.any(representative)
    audit = audit_relation_cycle_kernel(lattice, BLUE, ())
    assert audit.passed
    assert audit.kernel_chain_count == 1


def test_one_branch_forest_reproduces_its_two_endpoint_boundary() -> None:
    lattice = periodic_honeycomb(2)
    branch = build_charge_branch_catalog(lattice, BLUE)[0]
    relation = BranchRelation(
        color=BLUE,
        branch_id=branch.branch_id,
        endpoints=branch.endpoints,
        opposite_center=branch.opposite_center,
        honeycomb_edges=branch.honeycomb_edges,
    )
    relations = BranchPostFluxRelations(branch.endpoints, (relation,))
    record = [0] * lattice.vertex_count
    for vertex in branch.endpoints:
        record[vertex] = 1
    representative = effective_branch_chain_from_record(
        lattice, BLUE, relations, tuple(record)
    )
    assert representative[branch.branch_id] == 1
    charge_lattice = build_branch_charge_lattice(lattice, BLUE)
    expected = np.asarray(
        [record[int(vertex)] for vertex in charge_lattice.vertex_ids], dtype=np.uint8
    )
    assert np.array_equal(charge_chain_boundary(charge_lattice, representative), expected)
    assert audit_relation_cycle_kernel(
        lattice, BLUE, (branch.branch_id,)
    ).passed


def test_parallel_pair_kernel_exposes_nontrivial_period_sector() -> None:
    lattice = periodic_honeycomb(2)
    branches = build_charge_branch_catalog(lattice, BLUE)
    first = branches[0]
    twin = next(branch for branch in branches if branch.endpoints == first.endpoints and branch.branch_id != first.branch_id)
    audit = audit_relation_cycle_kernel(
        lattice, BLUE, (first.branch_id, twin.branch_id)
    )
    assert not audit.passed
    assert audit.nontrivial_kernel_count == 1
    assert audit.first_nontrivial_sector != (0, 0)
