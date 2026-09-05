#!/usr/bin/env python3
"""Move misplaced lab manifest JSON files into manifests/ and repair references."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re


def manifest(path: Path) -> bool:
    # Manifest identity lives in its small, top-level contract.  Reading just
    # the header keeps this classification safe for multi-hundred-MB samples
    # and checkpoints stored as JSON data under results/.
    text = path.read_bytes()[:65536].decode("utf-8", errors="replace")
    return '"schema_version"' in text and any(key in text for key in ('"acceptance"', '"question"', '"purpose"', '"claim_boundary"'))


MANIFEST_LINK = re.compile(r"(?P<prefix>\]\()(?P<target>(?:(?:\.\./)|results/)?manifests/[^)#\s]+\.json)(?P<suffix>(?:#[^)]+)?\))")


def repair_markdown_manifest_links(text: str, page: Path, manifest_dir: Path) -> str:
    """Make manifest links relative to the Markdown page that contains them."""
    def replace(match: re.Match[str]) -> str:
        name = Path(match.group("target")).name
        destination = manifest_dir / name
        if not destination.exists():
            return match.group(0)
        target = Path(os.path.relpath(destination, page.parent)).as_posix()
        return f"{match.group('prefix')}{target}{match.group('suffix')}"
    return MANIFEST_LINK.sub(replace, text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    lab = args.lab.resolve()
    sources = [
        path
        for directory in (lab, lab / "results")
        if directory.is_dir()
        for path in directory.glob("*.json")
        if path.name != "lab.json" and (manifest(path) or (directory == lab and "manifest" in path.name))
    ]
    replacements = {
        path.relative_to(lab).as_posix(): f"manifests/{path.name}"
        for path in sources
    }
    if not args.apply:
        for source in sources: print(f"MOVE {source.relative_to(lab)} -> {replacements[source.relative_to(lab).as_posix()]}")
        return 0
    target_dir = lab / "manifests"; target_dir.mkdir(exist_ok=True)
    for source in sources: source.rename(target_dir / source.name)
    # Never rewrite raw result JSON: those files may be very large samples or
    # checkpoints.  References live in Markdown, the small manifest contracts,
    # and the project state file.
    reference_files = [*lab.rglob("*.md"), *target_dir.glob("*.json"), lab.parent.parent / ".auto-research" / "state.json"]
    for path in reference_files:
        if not path.is_file(): continue
        text = path.read_text(encoding="utf-8")
        # Repair the former path-blind replacement before applying the
        # path-aware replacements below.
        updated = text.replace("results/manifests/", "manifests/").replace("manifests/manifests/", "manifests/")
        for source, replacement in replacements.items():
            updated = updated.replace(source, replacement)
            # A bare filename appears in a few human-readable references.
            updated = updated.replace(Path(source).name, replacement)
        if path.suffix == ".md":
            updated = repair_markdown_manifest_links(updated, path, target_dir)
        if updated != text: path.write_text(updated, encoding="utf-8")
    print(f"Moved {len(sources)} manifests into {target_dir}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
