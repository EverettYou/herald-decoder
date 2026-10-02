"""Frozen shortest-loop feasibility screen controls."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / "scripts/run_j7l_alternative_same_flux_loop_screen.py"
sys.path.insert(0, str(LAB / "scripts"))
SPEC = importlib.util.spec_from_file_location("j7l_loop_screen", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_unique_six_edge_cycles_have_degree_two_and_replay_prior():
    lattice = MODULE.paper_periodic_honeycomb(2)
    cycles = MODULE.simple_six_cycles(lattice)
    assert len(cycles) == len(set(cycles)) == 12
    assert cycles == sorted(cycles)
    assert (0, 1, 30, 32, 34, 35) in cycles
    for cycle in cycles:
        assert len(cycle) == len(set(cycle)) == 6
        degree = {}
        for edge in cycle:
            left, right = (int(x) for x in lattice.edge_vertices[edge])
            degree[left] = degree.get(left, 0) + 1
            degree[right] = degree.get(right, 0) + 1
        assert len(degree) == 6 and set(degree.values()) == {2}


def test_screen_replays_deterministically_and_stays_within_registered_cap():
    stored = json.loads(MODULE.RESULT.read_text())
    fresh = MODULE.run()
    stored.pop("cpu_seconds")
    fresh.pop("cpu_seconds")
    assert fresh == stored
    assert stored["status"] == "alternative_shortest_loop_screen_closed"
    assert stored["unique_simple_six_edge_cycle_count"] == 12
    assert stored["homologically_trivial_cycle_count"] == 12
    assert stored["passing_trivial_loop_count"] == 0
    assert stored["selected_prospective_loop_red_edges_private"] is None
    assert stored["usage"]["ordered_moment_terms"] <= 65536
    assert all(value == 0 for value in stored["counters"].values())
