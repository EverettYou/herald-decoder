"""Run the frozen eight-case J6A matrix with zero production histories."""

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
MANIFEST = LAB / "manifests/j6a-causal-odd-syndrome-time-boundary-handoff-2026-09-22.json"
RESULT = LAB / "results/j6a-causal-odd-syndrome-time-boundary-handoff-2026-09-22.json"
TEST = LAB / "scripts/test_j6a_causal_handoff.py"
REPO = LAB.parents[1]
EXPECTED_TESTS = (
    "test_even_identity",
    "test_odd_readout_snapshot",
    "test_odd_two_round_reconciliation",
    "test_odd_persistence",
    "test_causal_future_extension",
    "test_truth_sidecar_invariance",
    "test_replay_and_vertex_permutation",
    "test_malformed_or_unbound_token",
)
PINNED = {"numpy": "1.26.4", "numba": "0.65.0", "scipy": "1.17.1", "pymatching": "2.4.0"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    frozen = manifest["frozen_j6_artifact_sha256"]
    versions = {
        "numpy": numpy.__version__, "numba": numba.__version__,
        "scipy": scipy.__version__, "pymatching": pymatching.__version__,
    }
    checks = {}
    for relative, expected in frozen.items():
        checks[relative] = {
            "expected_sha256": expected,
            "actual_sha256": _sha(LAB / relative),
        }
    source_names = [
        "scripts/d4_spatial_policy.py", "scripts/e1_schedule_integration.py",
        "scripts/d4_integrated_history.py", "scripts/test_j6a_causal_handoff.py",
    ]
    sources = {name: _sha(LAB / name) for name in source_names}
    started = time.monotonic()
    status = "censored"
    reason = None
    output = ""
    passed = 0
    peak_mib = 0.0
    try:
        if versions != PINNED:
            raise RuntimeError(f"research runtime mismatch: {versions}")
        if any(item["actual_sha256"] != item["expected_sha256"] for item in checks.values()):
            raise RuntimeError("frozen J6 artifact SHA-256 changed before fixtures")
        if manifest["budget"]["deterministic_fixture_cases"] != len(EXPECTED_TESTS):
            raise RuntimeError("fixture budget differs from registered matrix")
        if shutil.which("pytest") is None:
            raise RuntimeError("existing pytest executable is unavailable")
        # The repository's pytest executable is a development tool; force it
        # to import the already-verified pinned research packages first.
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, (sysconfig.get_paths()["purelib"], env.get("PYTHONPATH")))
        )
        completed = subprocess.run(
            ["pytest", "-q", "-x", "--disable-warnings", *(f"{TEST.relative_to(REPO)}::{name}" for name in EXPECTED_TESTS)],
            text=True, capture_output=True, timeout=manifest["budget"]["maximum_runtime_seconds"],
            env=env, cwd=REPO, check=False,
        )
        output = completed.stdout + completed.stderr
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        # macOS ru_maxrss is bytes; Linux is KiB.
        peak_mib = usage.ru_maxrss / (1024**2 if sys.platform == "darwin" else 1024)
        if completed.returncode != 0:
            raise RuntimeError(f"fixture matrix failed with exit {completed.returncode}")
        passed = len(EXPECTED_TESTS)
        if peak_mib > manifest["budget"]["maximum_peak_memory_mib"]:
            raise RuntimeError("fixture matrix exceeded registered memory budget")
        if time.monotonic() - started > manifest["budget"]["maximum_runtime_seconds"]:
            raise RuntimeError("fixture matrix exceeded registered time budget")
        if any(_sha(LAB / name) != digest for name, digest in sources.items()):
            raise RuntimeError("J6A source changed during fixture matrix")
        if any(_sha(LAB / name) != item["expected_sha256"] for name, item in checks.items()):
            raise RuntimeError("frozen J6 artifact SHA-256 changed during fixtures")
        status = "passed"
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        reason = f"{type(error).__name__}:{error}"
    result = {
        "contract_id": manifest["id"],
        "status": status,
        "reason": reason,
        "fixture_ids": list(EXPECTED_TESTS),
        "deterministic_fixtures_passed": passed,
        "new_stochastic_histories": 0,
        "schedule_arm_evaluations": 0,
        "bootstrap_replicates": 0,
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "peak_memory_mib": round(peak_mib, 3),
        "research_runtime_versions": versions,
        "source_sha256": sources,
        "frozen_j6_artifact_checks": checks,
        "pytest_output": output,
        "claim_boundary": "Structural causal-interface fixture only; no logical-performance or schedule-risk evidence.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "reason": reason, "result": str(RESULT), "fixtures_passed": passed}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
