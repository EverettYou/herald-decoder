from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spacetime_ilp import (  # noqa: E402
    FusionChannel,
    PhysicalEvent,
    SpacetimeIlpProblem,
    SpacetimeSite,
    solve_spacetime_fusion_ilp,
)


def _single_site_problem(*, physical_cost: float, measurement_cost: float) -> SpacetimeIlpProblem:
    return SpacetimeIlpProblem(
        species=("a",),
        sites=(
            SpacetimeSite(
                name="s0t0",
                previous_site=None,
                channels=(
                    FusionChannel("physical-a", (1,), (0,), (0,)),
                    FusionChannel("false-positive-a", (0,), (0,), (1,)),
                ),
            ),
        ),
        physical_events=(PhysicalEvent("create-a", physical_cost, ((0, 0, 1),)),),
        measurement_costs=np.asarray([[measurement_cost]], dtype=float),
    )


def test_ilp_selects_lower_cost_physical_explanation() -> None:
    result = solve_spacetime_fusion_ilp(
        _single_site_problem(physical_cost=1.0, measurement_cost=3.0)
    )
    assert result.selected_physical_events == ("create-a",)
    assert result.selected_measurement_errors == ()
    assert result.selected_channels == (("s0t0", "physical-a"),)


def test_ilp_selects_lower_cost_measurement_explanation() -> None:
    result = solve_spacetime_fusion_ilp(
        _single_site_problem(physical_cost=4.0, measurement_cost=1.0)
    )
    assert result.selected_physical_events == ()
    assert result.selected_measurement_errors == (("s0t0", "a"),)
    assert result.selected_channels == (("s0t0", "false-positive-a"),)


def test_temporal_measurement_string_must_enter_next_site() -> None:
    problem = SpacetimeIlpProblem(
        species=("a",),
        sites=(
            SpacetimeSite(
                "s0t0",
                None,
                (FusionChannel("start-readout-string", (0,), (0,), (1,)),),
            ),
            SpacetimeSite(
                "s0t1",
                0,
                (FusionChannel("end-readout-string", (0,), (1,), (0,)),),
            ),
        ),
        physical_events=(),
        measurement_costs=np.asarray([[1.0], [9.0]], dtype=float),
    )
    result = solve_spacetime_fusion_ilp(problem)
    assert result.selected_measurement_errors == (("s0t0", "a"),)
    assert result.selected_channels == (
        ("s0t0", "start-readout-string"),
        ("s0t1", "end-readout-string"),
    )


def test_measured_syndrome_can_change_allowed_nonabelian_channel() -> None:
    physical = (PhysicalEvent("create-b", 1.0, ((0, 1, 1),)),)
    # Fig. 4(c)-type outcome: the created b is present but unreported, so an
    # outgoing temporal b string is required.
    reported_other = SpacetimeIlpProblem(
        species=("a", "b"),
        sites=(
            SpacetimeSite(
                "s0t0",
                None,
                (FusionChannel("unreported-b", (0, 1), (0, 0), (0, 1)),),
            ),
        ),
        physical_events=physical,
        measurement_costs=np.asarray([[9.0, 1.0]], dtype=float),
    )
    # Fig. 4(d)-type outcome: a x b = a lets b fuse without a new readout
    # error.  The defect is unchanged, but the measured syndrome differs.
    reported_a = SpacetimeIlpProblem(
        species=("a", "b"),
        sites=(
            SpacetimeSite(
                "s0t0",
                None,
                (FusionChannel("a-times-b-to-a", (0, 1), (0, 0), (0, 0)),),
            ),
        ),
        physical_events=physical,
        measurement_costs=np.asarray([[9.0, 1.0]], dtype=float),
    )
    first = solve_spacetime_fusion_ilp(reported_other)
    second = solve_spacetime_fusion_ilp(reported_a)
    assert first.selected_measurement_errors == (("s0t0", "b"),)
    assert second.selected_measurement_errors == ()


def test_inconsistent_temporal_channel_is_infeasible() -> None:
    problem = SpacetimeIlpProblem(
        species=("a",),
        sites=(
            SpacetimeSite(
                "s0t0",
                None,
                (FusionChannel("impossible-incoming", (0,), (1,), (0,)),),
            ),
        ),
        physical_events=(),
        measurement_costs=np.zeros((1, 1)),
    )
    with pytest.raises(ValueError, match="infeasible"):
        solve_spacetime_fusion_ilp(problem)


def test_duplicate_labels_and_nonfinite_channel_cost_are_rejected() -> None:
    duplicate_sites = SpacetimeIlpProblem(
        species=("a",),
        sites=(
            SpacetimeSite("s", None, (FusionChannel("vac", (0,), (0,), (0,)),)),
            SpacetimeSite("s", 0, (FusionChannel("vac", (0,), (0,), (0,)),)),
        ),
        physical_events=(),
        measurement_costs=np.zeros((2, 1)),
    )
    with pytest.raises(ValueError, match="site names"):
        solve_spacetime_fusion_ilp(duplicate_sites)

    nonfinite = SpacetimeIlpProblem(
        species=("a",),
        sites=(
            SpacetimeSite(
                "s", None, (FusionChannel("vac", (0,), (0,), (0,), np.nan),)
            ),
        ),
        physical_events=(),
        measurement_costs=np.zeros((1, 1)),
    )
    with pytest.raises(ValueError, match="channel costs"):
        solve_spacetime_fusion_ilp(nonfinite)
