from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_r4_corrected_sequential_policy import (  # noqa: E402
    HiddenActionTransition,
    _select_min_mask,
    evaluate_weighted_observation,
)


def test_minimum_risk_tie_breaks_by_action_mask() -> None:
    import numpy as np

    assert _select_min_mask(np.asarray([0.2, 0.2]), (9, 3), 1e-12) == 1


def test_future_aware_action_uses_continuation_value() -> None:
    transitions = {
        (0, 2): HiddenActionTransition(False, 1.0, ((0, 0),)),
        (1, 2): HiddenActionTransition(False, 1.0, ((0, 1),)),
        (0, 7): HiddenActionTransition(False, 1.0, ((0, 0),)),
        (1, 7): HiddenActionTransition(False, 1.0, ((1, 1),)),
    }
    result = evaluate_weighted_observation(
        ((0, 0.5), (1, 0.5)),
        (2, 7),
        transitions,
        public_action_index=0,
        public_second_predictions={0: 0, 1: 1},
        tolerance=1e-12,
    )
    assert result["actions"] == {"public": 2, "myopic": 2, "future_aware": 7}
    assert result["risk_numerators"]["public_fixed"] == 0.5
    assert result["risk_numerators"]["fixed_first_exact_continuation"] == 0.5
    assert result["risk_numerators"]["myopic_first_exact_continuation"] == 0.5
    assert result["risk_numerators"]["future_aware_exact"] == 0.0
    assert result["maximum_action_mass_conservation_error"] == 0.0
