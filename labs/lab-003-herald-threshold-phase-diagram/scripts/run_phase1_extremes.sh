#!/bin/sh
# The only supported entry point for Lab 003 Phase 1 simulation runs.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/../../.." && pwd)
exec "$repo_dir/run_research_python.sh" "$script_dir/run_phase1_extremes.py" "$@"
