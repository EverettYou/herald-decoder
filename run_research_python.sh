#!/bin/sh
# Single fail-closed launcher for accelerated research simulations.
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
default_python="$project_root/.venv-research/bin/python3"
research_python=${HERALD_RESEARCH_PYTHON:-$default_python}

if [ ! -x "$research_python" ]; then
    echo "Research Python was not found: $research_python" >&2
    echo "Set HERALD_RESEARCH_PYTHON to the Python 3.13.2 runtime pinned in requirements-research.txt." >&2
    exit 2
fi

mkdir -p "$project_root/.tmp/matplotlib" "$project_root/.tmp/numba-cache" "$project_root/.tmp/cache"
export PYTHONPATH="$project_root/src:$project_root/.tmp/numba-runtime${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$project_root/.tmp/matplotlib"
export NUMBA_CACHE_DIR="$project_root/.tmp/numba-cache"
export XDG_CACHE_HOME="$project_root/.tmp/cache"

"$research_python" - <<'PY'
import sys
try:
    import numba
    import numpy
    import pymatching
    import scipy
except ImportError as error:
    raise SystemExit(f"accelerated research runtime is incomplete: {error}")

expected = {
    "Python": (sys.version_info[:3], (3, 13, 2)),
    "NumPy": (numpy.__version__, "1.26.4"),
    "Numba": (numba.__version__, "0.65.0"),
    "PyMatching": (pymatching.__version__, "2.4.0"),
    "SciPy": (scipy.__version__, "1.17.1"),
}
failed = [f"{name}={actual!r}, expected {wanted!r}" for name, (actual, wanted) in expected.items() if actual != wanted]
if failed:
    raise SystemExit("accelerated research runtime mismatch: " + "; ".join(failed))
print("accelerated research runtime: verified")
PY

exec "$research_python" "$@"
