#!/usr/bin/env python3
"""Check a lab's Local Wiki structure, links, and evidence status."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import yaml


STATUSES = {"current", "superseded", "withdrawn"}
REQUIRED_HEADINGS = {"Summary", "Evidence", "Status", "Related pages"}


def frontmatter(text: str):
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    return (yaml.safe_load(match.group(1)) or {}, text[match.end():]) if match else ({}, text)


def lint(lab: Path) -> list[str]:
    root = lab / "wiki"
    errors: list[str] = []
    root_json = [path for path in lab.glob("*.json") if path.name != "lab.json"]
    for path in root_json:
        errors.append(f"root manifest must move to manifests/: {path.name}")
    for path in (lab / "results").glob("*.md"):
        errors.append(f"human-readable result record must move to Local Wiki: {path.name}")
    metadata_path = lab / "lab.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        summary = str(metadata.get("summary", "")).strip()
        if not summary:
            errors.append("lab.json is missing a stable lab summary")
        elif re.search(r"\b(?:R|P|M)\d+(?:\.\d+|[A-Z]+)?\b", summary):
            errors.append("lab.json summary must describe the lab purpose, not an internal run result")
        for result in metadata.get("results", []):
            path = str(result.get("path", ""))
            if path.startswith("results/") and path.endswith(".md"):
                errors.append(f"lab.json retains a prose record under results/: {path}")
            if (
                str(result.get("kind", "")) == "document"
                and path.startswith("wiki/")
                and str(result.get("presentation", "")) == "result"
            ):
                errors.append(
                    "Local Wiki document must not be published as a Result card: "
                    f"{path}"
                )
    scripts = lab / "scripts"
    if scripts.is_dir():
        for script in scripts.rglob("*.py"):
            text = script.read_text(encoding="utf-8")
            if re.search(r'LAB_DIR\s*/\s*["\']results/[^"\']+\.md["\']', text):
                errors.append(f"runner defaults prose output to results/: {script.relative_to(lab)}")
    index = root / "index.md"
    if not index.is_file():
        return ["wiki/index.md is missing"]
    pages = sorted(path for path in root.rglob("*.md") if path != index)
    for page in pages:
        meta, body = frontmatter(page.read_text(encoding="utf-8"))
        rel = page.relative_to(root)
        for key in ("title", "status", "updated"):
            if not meta.get(key): errors.append(f"{rel}: missing frontmatter {key}")
        if meta.get("status") not in STATUSES:
            errors.append(f"{rel}: invalid status")
        headings = set(re.findall(r"^##\s+(.+?)\s*$", body, flags=re.M))
        for heading in REQUIRED_HEADINGS - headings:
            errors.append(f"{rel}: missing {heading} section")
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", body):
            if target.startswith(("http:", "https:", "/")): continue
            if not (page.parent / target).resolve().is_file():
                errors.append(f"{rel}: broken evidence link {target}")
        for target in re.findall(r"\[\[([^]|#]+)(?:\|[^]]+)?\]\]", body):
            if not (root / (target + ".md")).is_file():
                errors.append(f"{rel}: broken Local Wiki link {target}")
        if meta.get("status") in {"superseded", "withdrawn"} and not re.search(r"replacement|reason", body, flags=re.I):
            errors.append(f"{rel}: retired page needs a replacement or reason")
        index_text = (root / "records" / "index.md").read_text(encoding="utf-8") if rel.parts[0] == "records" and rel != Path("records/index.md") and (root / "records" / "index.md").is_file() else index.read_text(encoding="utf-8")
        if rel.as_posix() not in index_text and rel.with_suffix("").as_posix() not in index_text:
            errors.append(f"{rel}: unreachable from wiki/index.md")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("lab", type=Path)
    args = parser.parse_args(); errors = lint(args.lab)
    if errors:
        print("Local Wiki lint failed:"); print("\n".join(f"- {item}" for item in errors)); return 1
    print("Local Wiki lint passed."); return 0


if __name__ == "__main__": raise SystemExit(main())
