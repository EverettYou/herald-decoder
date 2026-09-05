"""Compatibility shim; shared damping BP now lives in ``src/herald_decoder``."""
from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parents[3] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from herald_decoder.legacy_damped_bp_decoder import *  # noqa: F401,F403
