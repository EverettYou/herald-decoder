"""Compatibility shim; shared posterior-LLR decoder now lives in ``src/herald_decoder``."""
from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parents[3] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from herald_decoder.herald_bp_decoder import *  # noqa: F401,F403
