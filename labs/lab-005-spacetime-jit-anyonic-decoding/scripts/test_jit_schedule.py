from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jit_schedule import (  # noqa: E402
    CorrectionElement,
    Defect,
    InferredCluster,
    JitStateMachine,
)


def test_single_defect_defers_then_commits_after_one_round() -> None:
    state = JitStateMachine()
    state.add_defects((Defect("d0", (0, 0), 0),), current_time=0)
    cluster = InferredCluster("c0", ("d0",))
    assert state.step(current_time=0, clusters=(cluster,))[0].action == "defer"
    assert state.step(current_time=1, clusters=(cluster,))[0].action == "commit"
    assert state.unresolved == {}


def test_spatial_extent_sets_q_age_gate() -> None:
    state = JitStateMachine()
    state.add_defects(
        (Defect("left", (0, 0), 0), Defect("right", (3, 0), 0)),
        current_time=0,
    )
    cluster = InferredCluster("wide", ("left", "right"))
    early = state.step(current_time=3, clusters=(cluster,))[0]
    assert early.cube_size == 4
    assert early.action == "defer"
    assert state.step(current_time=4, clusters=(cluster,))[0].action == "commit"


def test_young_correction_string_delays_an_old_cluster() -> None:
    state = JitStateMachine()
    state.add_defects((Defect("d0", (0,), 0),), current_time=0)
    cluster = InferredCluster(
        "updated",
        ("d0",),
        correction_elements=(CorrectionElement((1,), 3),),
    )
    decision = state.step(current_time=3, clusters=(cluster,))[0]
    assert decision.cube_size == 4
    assert decision.youngest_time == 3
    assert decision.action == "defer"


def test_scheduler_rejects_future_information() -> None:
    state = JitStateMachine()
    with pytest.raises(ValueError, match="future defect"):
        state.add_defects((Defect("future", (0,), 2),), current_time=1)
    state.add_defects((Defect("d0", (0,), 0),), current_time=0)
    with pytest.raises(ValueError, match="future correction"):
        state.step(
            current_time=1,
            clusters=(
                InferredCluster(
                    "c0",
                    ("d0",),
                    correction_elements=(CorrectionElement((0,), 2),),
                ),
            ),
        )


def test_scheduler_rejects_overlapping_cluster_assignments() -> None:
    state = JitStateMachine()
    state.add_defects((Defect("d0", (0,), 0),), current_time=0)
    with pytest.raises(ValueError, match="two inferred clusters"):
        state.step(
            current_time=0,
            clusters=(
                InferredCluster("c0", ("d0",)),
                InferredCluster("c1", ("d0",)),
            ),
        )


def test_scheduler_rejects_time_reversal_and_incomplete_partition() -> None:
    state = JitStateMachine()
    state.add_defects(
        (Defect("d0", (0,), 0), Defect("d1", (1,), 0)),
        current_time=0,
    )
    with pytest.raises(ValueError, match="partition every unresolved"):
        state.step(
            current_time=0,
            clusters=(InferredCluster("c0", ("d0",)),),
        )
    state.step(
        current_time=0,
        clusters=(InferredCluster("c0", ("d0", "d1")),),
    )
    with pytest.raises(ValueError, match="backwards"):
        state.step(current_time=-1, clusters=())


def test_scheduler_rejects_duplicate_ids_in_one_new_batch() -> None:
    state = JitStateMachine()
    with pytest.raises(ValueError, match="new defect identifiers"):
        state.add_defects(
            (Defect("d0", (0,), 0), Defect("d0", (1,), 0)),
            current_time=0,
        )
    assert state.unresolved == {}
    assert state.last_time == -1
