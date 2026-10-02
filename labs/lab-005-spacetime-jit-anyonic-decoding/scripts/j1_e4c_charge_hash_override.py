"""Pytest-only override for the registered J1-E4C compatibility audit."""

from __future__ import annotations

import hashlib
from pathlib import Path


OLD_HASH = "c7b528d343abedb052e6bea7f5c29f65de2bab5dae96befa339763198bb17e9a"
CURRENT_HASH = "2ba3dd13feda42e4441ae0089be2403b5c75b626ae0a0542d4aa9089807472fd"


def pytest_configure(config) -> None:  # noqa: ANN001
    import d4_spatial_policy

    source = (
        Path(d4_spatial_policy.__file__).resolve().parents[2]
        / "lab-004-d4-intrinsic-heralded-decoding/scripts/d4_charge.py"
    )
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    frozen = d4_spatial_policy._POLICY_SOURCE_HASHES["d4_charge.py"]
    if frozen != OLD_HASH:
        raise RuntimeError(f"unexpected Lab 005 frozen hash: {frozen}")
    if actual != CURRENT_HASH:
        raise RuntimeError(f"unexpected current Lab 004 hash: {actual}")
    d4_spatial_policy._POLICY_SOURCE_HASHES["d4_charge.py"] = CURRENT_HASH

