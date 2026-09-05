import numpy as np

from run_a7_ler import SCORING_RULE, final_decoder_failure


def test_final_score_depends_only_on_residual_and_logical_parity():
    assert not final_decoder_failure(np.zeros(3, dtype=np.uint8), False)
    assert final_decoder_failure(np.array([0, 1, 0], dtype=np.uint8), False)
    assert final_decoder_failure(np.zeros(3, dtype=np.uint8), True)
    assert "BP convergence diagnostic only" in SCORING_RULE
