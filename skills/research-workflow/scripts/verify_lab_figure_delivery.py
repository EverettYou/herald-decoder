#!/usr/bin/env python3
"""Verify the static delivery chain for one reader-facing lab PNG.

This checker deliberately covers only deterministic links: the PNG itself,
the report embed, and the active lab registry. A browser or application-level
inspection is still required when the acceptance surface is a rendered URL.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message: str) -> None:
    raise ValueError(message)


def read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        fail(f"not a valid PNG with an IHDR header: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        fail(f"PNG has an invalid zero dimension: {path}")
    return width, height


def report_figure_block(report: str, figure_path: str) -> str:
    lines = report.splitlines()
    hits = [index for index, line in enumerate(lines) if f"]({figure_path})" in line]
    if len(hits) != 1:
        fail(
            f"REPORT.md must embed {figure_path!r} exactly once; found {len(hits)} embeds"
        )
    image_index = hits[0]
    heading_index = image_index
    while heading_index > 0 and not lines[heading_index].startswith("### "):
        heading_index -= 1
    end_index = image_index + 1
    while end_index < len(lines) and not lines[end_index].startswith("### "):
        end_index += 1
    return "\n".join(lines[heading_index:end_index])


def registry_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    results = data.get("results")
    if not isinstance(results, list):
        fail("lab.json has no top-level results list")
    if not all(isinstance(item, dict) for item in results):
        fail("lab.json results must contain objects")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a lab PNG, its REPORT.md embed, and its lab.json registration."
    )
    parser.add_argument("lab_dir", type=Path)
    parser.add_argument("figure_path", help="Lab-relative PNG path, e.g. figures/current.png")
    parser.add_argument("--result-id", help="Expected unique lab.json result id")
    parser.add_argument(
        "--forbid-term",
        action="append",
        default=[],
        help="Term forbidden in this figure's reader-facing report section; repeatable",
    )
    parser.add_argument(
        "--forbid-result-id-pattern",
        action="append",
        default=[],
        help="Regex that must match no active lab.json result id; repeatable",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lab_dir = args.lab_dir.resolve()
    figure_rel = Path(args.figure_path)
    if figure_rel.is_absolute() or ".." in figure_rel.parts:
        fail("figure_path must be a safe lab-relative path")
    if figure_rel.suffix.lower() != ".png":
        fail(f"reader-facing figure must be PNG: {figure_rel}")

    report_path = lab_dir / "REPORT.md"
    registry_path = lab_dir / "lab.json"
    figure_path = lab_dir / figure_rel
    for required in (report_path, registry_path, figure_path):
        if not required.is_file():
            fail(f"required delivery-chain file is missing: {required}")

    width, height = read_png_size(figure_path)
    report = report_path.read_text(encoding="utf-8")
    block = report_figure_block(report, figure_rel.as_posix())
    for term in args.forbid_term:
        if term.casefold() in block.casefold():
            fail(f"forbidden reader-facing term {term!r} appears in the figure section")

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    results = registry_results(data)
    path_hits = [item for item in results if item.get("path") == figure_rel.as_posix()]
    if len(path_hits) != 1:
        fail(
            f"lab.json must register {figure_rel.as_posix()!r} exactly once; "
            f"found {len(path_hits)} registrations"
        )
    registered = path_hits[0]
    if registered.get("kind") != "figure":
        fail(f"registered result kind must be 'figure', got {registered.get('kind')!r}")
    if str(registered.get("format", "")).lower() != "png":
        fail(f"registered figure format must be 'png', got {registered.get('format')!r}")
    if args.result_id and registered.get("id") != args.result_id:
        fail(
            f"registered result id is {registered.get('id')!r}, expected {args.result_id!r}"
        )

    for pattern in args.forbid_result_id_pattern:
        matcher = re.compile(pattern)
        matches = [str(item.get("id", "")) for item in results if matcher.search(str(item.get("id", "")))]
        if matches:
            fail(f"superseded active result ids match {pattern!r}: {', '.join(matches)}")

    print(
        "Figure delivery static verification passed: "
        f"{figure_rel.as_posix()} ({width}x{height}), one REPORT.md embed, "
        f"one lab.json registration ({registered.get('id')})."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, re.error) as error:
        print(f"Figure delivery static verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
