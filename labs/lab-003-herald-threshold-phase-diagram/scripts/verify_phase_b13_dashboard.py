#!/usr/bin/env python3
"""Verify the public dashboard serves the Phase B13 evidence-only result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


LAB_ID = "lab-003-herald-threshold-phase-diagram"
RESULT_ID = "phase-b13-honeycomb-continuous-log-odds-map-2026-08-28"
ASSET_PATH = "figures/phase-b13-honeycomb-continuous-log-odds-map-2026-08-28.png"
LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = LAB_DIR / "results/phase-b13-dashboard-e2e-audit-2026-08-28.json"


def fetch(url: str) -> tuple[int, str, bytes]:
    request = Request(url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=10) as response:  # noqa: S310 - local dashboard only
        return response.status, response.headers.get_content_type(), response.read()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def verify(base_url: str) -> dict:
    base = base_url.rstrip("/")
    route = f"{base}/lab-result?lab={LAB_ID}&result={RESULT_ID}"
    api_url = f"{base}/api/labs/{LAB_ID}"
    asset_url = f"{base}/lab-assets/{LAB_ID}/{ASSET_PATH}"

    route_status, route_type, route_body = fetch(route)
    api_status, api_type, api_body = fetch(api_url)
    asset_status, asset_type, asset_body = fetch(asset_url)
    payload = json.loads(api_body)
    outputs = payload["outputs"]
    matches = [row for row in outputs if row["id"] == RESULT_ID]
    if len(matches) != 1:
        raise AssertionError("Phase B13 output must appear exactly once")
    active = matches[0]
    retired = [
        row for row in outputs
        if row.get("kind") == "figure"
        and re.match(r"phase-b(?:5|6|7|8|9|12)-", row["id"])
    ]
    report = payload["report"]["content"]
    audit = json.loads((LAB_DIR / "results/phase-b13-honeycomb-continuous-log-odds-render-audit-2026-08-28.json").read_text())
    expected_hash = audit["figure"]["sha256"]

    checks = {
        "lab_result_route_status_200": route_status == 200,
        "lab_result_route_is_html": route_type == "text/html",
        "lab_result_route_loads_result_controller": b"/js/lab-result-page.js" in route_body,
        "lab_api_status_200": api_status == 200,
        "lab_api_is_json": api_type == "application/json",
        "phase_b13_output_is_page_image": (
            active.get("presentation") == "page"
            and active.get("kind") == "figure"
            and active.get("format") == "image"
            and active.get("asset_path") == ASSET_PATH
        ),
        "report_embeds_phase_b13": f"]({ASSET_PATH})" in report,
        "report_embeds_no_b5_b12_categorical_figure": not re.search(
            r"!\[[^\]]*\]\(figures/phase-b(?:5|6|7|8|9|12)-[^)]*\.png\)", report
        ),
        "retired_categorical_figures_exist": len(retired) >= 6,
        "retired_categorical_figures_are_downloads": all(
            row.get("presentation") == "download" for row in retired
        ),
        "phase_b13_asset_status_200": asset_status == 200,
        "phase_b13_asset_is_png": asset_type == "image/png" and asset_body.startswith(b"\x89PNG\r\n\x1a\n"),
        "phase_b13_asset_matches_render_audit": sha256_bytes(asset_body) == expected_hash,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"Phase B13 dashboard verification failed: {failed}")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "verified",
        "base_url": base,
        "lab_id": LAB_ID,
        "result_id": RESULT_ID,
        "checks": checks,
        "retired_categorical_figure_ids": [row["id"] for row in retired],
        "asset": {
            "path": ASSET_PATH,
            "bytes": len(asset_body),
            "sha256": sha256_bytes(asset_body),
        },
        "browser_runtime_note": (
            "The in-app browser runtime could not initialize because the workspace path contains "
            "square brackets that its filesystem glob parser rejected. Verification therefore used "
            "the same live public HTTP route, API, and asset endpoints plus dashboard contract tests."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = verify(args.base_url)
    atomic_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
