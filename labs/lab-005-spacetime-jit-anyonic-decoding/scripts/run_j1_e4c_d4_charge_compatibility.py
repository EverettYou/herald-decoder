"""Run the J1-E4C public-contract compatibility audit."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "labs/lab-005-spacetime-jit-anyonic-decoding"
MANIFEST = LAB / "manifests/j1-e4c-d4-charge-semantic-compatibility-2026-09-19.json"
RESULT = LAB / "results/j1-e4c-d4-charge-semantic-compatibility-2026-09-19.json"
PLUGIN = LAB / "scripts/j1_e4c_charge_hash_override.py"
CURRENT_SOURCE = ROOT / "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/d4_charge.py"

TEST_FILES = [
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_spatial_policy.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_projector_instrument.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_d4_temporal_composition.py",
    "labs/lab-005-spacetime-jit-anyonic-decoding/scripts/test_e1_schedule_integration.py",
    "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_charge.py",
    "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_r6af_two_stage_public_charge.py",
    "labs/lab-004-d4-intrinsic-heralded-decoding/scripts/test_d4_sampler.py",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    current_hash = digest(CURRENT_SOURCE)
    hash_gate = current_hash == manifest["current_remediated_hash"]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    scripts = str(LAB / "scripts")
    env["PYTHONPATH"] = scripts + os.pathsep + env.get("PYTHONPATH", "")
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "j1_e4c_charge_hash_override",
        *TEST_FILES,
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    ) if hash_gate else None
    passed = bool(hash_gate and completed and completed.returncode == 0)
    sources = [Path(__file__), PLUGIN, MANIFEST, CURRENT_SOURCE]
    out = {
        "status": "passed" if passed else "incompatible_or_censored",
        "claim_boundary": manifest["scope"],
        "old_source_body_available": False,
        "frozen_old_hash": manifest["frozen_old_hash"],
        "current_remediated_hash": current_hash,
        "current_hash_gate_passed": hash_gate,
        "intervention": manifest["intervention"],
        "test_files": TEST_FILES,
        "pytest_returncode": None if completed is None else completed.returncode,
        "pytest_stdout": "" if completed is None else completed.stdout.strip(),
        "pytest_stderr": "" if completed is None else completed.stderr.strip(),
        "public_contract_compatible": passed,
        "internal_algorithm_equivalence_claimed": False,
        "production_histories_generated": 0,
        "performance_evaluations": 0,
        "bootstrap_replicates": 0,
        "next_action": (
            "Update only the Lab 005 d4_charge.py frozen hash, then rerun the unchanged J1-E4B matrix."
            if passed
            else "Keep the interface blocked and remediate the public adapter."
        ),
        "source_sha256": {
            str(path.relative_to(ROOT)): digest(path) for path in sources
        },
    }
    RESULT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "status": out["status"],
        "public_contract_compatible": passed,
        "pytest_stdout": out["pytest_stdout"],
        "pytest_stderr": out["pytest_stderr"],
    }, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
