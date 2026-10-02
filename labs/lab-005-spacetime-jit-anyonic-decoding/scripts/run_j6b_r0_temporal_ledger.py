"""Fail-closed deterministic J6B-R0 ledger-reconciliation gate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import sysconfig
import time

import numba
import numpy
import pymatching
import scipy


LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
RESULT = LAB / "results/j6b-r0-temporal-ledger-reconciliation-2026-09-23.json"
TEST = "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_j6b_r0_temporal_ledger.py"
FIXTURES = (
    "test_odd_then_even",
    "test_persistent_odd",
    "test_same_round_duplicates_and_conflict",
    "test_whole_matrix_replay",
)
FROZEN_J6 = {
    "results/j6-d4-matched-history-pilot-rows-2026-09-19.jsonl": "9e120e1402f2cd5332ecbea1d15ded2979e8d0fe2165083eeb21794cbed22225",
    "results/j6-d4-matched-history-pilot-analysis-2026-09-19.json": "fa2bc6d7b7de69004d266557b1b885a0369fb3944d3dbcee94ee54fb6e6cfcf3",
}
PINNED = {"numpy": "1.26.4", "numba": "0.65.0", "scipy": "1.17.1", "pymatching": "2.4.0"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = time.monotonic()
    versions = {
        "numpy": numpy.__version__, "numba": numba.__version__,
        "scipy": scipy.__version__, "pymatching": pymatching.__version__,
    }
    sources = {
        name: _sha(LAB / name)
        for name in (
            "scripts/d4_integrated_history.py",
            "scripts/e1_schedule_integration.py",
            "scripts/d4_spatial_policy.py",
            "scripts/test_j6b_r0_temporal_ledger.py",
        )
    }
    status = "censored"
    reason = None
    fixture_output = ""
    regression_output = ""
    fixture_count = 0
    regression_count = 0
    try:
        if versions != PINNED:
            raise RuntimeError(f"research runtime mismatch: {versions}")
        if any(_sha(LAB / name) != expected for name, expected in FROZEN_J6.items()):
            raise RuntimeError("frozen J6 raw/analysis hash mismatch before R0")
        pytest = shutil.which("pytest")
        if pytest is None:
            raise RuntimeError("existing pytest executable is unavailable")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, (sysconfig.get_paths()["purelib"], env.get("PYTHONPATH")))
        )
        exact = subprocess.run(
            [pytest, "-q", "-x", *(f"{TEST}::{name}" for name in FIXTURES)],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=120, check=False,
        )
        fixture_output = exact.stdout + exact.stderr
        if exact.returncode:
            raise RuntimeError(f"R0 fixture failure: exit {exact.returncode}")
        fixture_count = len(FIXTURES)
        suite = subprocess.run(
            [pytest, "-q", "labs/lab-005-spacetime-jit-anyonic-decoding/scripts"],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=120, check=False,
        )
        regression_output = suite.stdout + suite.stderr
        if suite.returncode or "158 passed" not in regression_output:
            raise RuntimeError(f"Lab 005 regression failure: exit {suite.returncode}")
        regression_count = 158
        if any(_sha(LAB / name) != expected for name, expected in FROZEN_J6.items()):
            raise RuntimeError("frozen J6 raw/analysis hash mismatch after R0")
        if any(_sha(LAB / name) != expected for name, expected in sources.items()):
            raise RuntimeError("R0 source changed during the deterministic matrix")
        if time.monotonic() - started > 120:
            raise RuntimeError("R0 exceeded its registered runtime cap")
        status = "passed"
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        reason = f"{type(error).__name__}:{error}"
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak_mib = usage.ru_maxrss / (1024**2 if sys.platform == "darwin" else 1024)
    result = {
        "contract_id": "lab005-j6b-r0-temporal-ledger-reconciliation-2026-09-23",
        "status": status,
        "reason": reason,
        "fixture_ids": list(FIXTURES),
        "fixtures_passed": fixture_count,
        "lab_regressions_passed": regression_count,
        "new_stochastic_histories": 0,
        "production_schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "peak_memory_mib": round(peak_mib, 3),
        "runtime_versions": versions,
        "source_sha256": sources,
        "frozen_j6_artifact_sha256": FROZEN_J6,
        "fixture_output": fixture_output,
        "regression_output": regression_output,
        "claim_boundary": "Deterministic ledger reconciliation only; J6 remains censored and no replacement pilot was sampled.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "reason": reason, "result": str(RESULT)}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
