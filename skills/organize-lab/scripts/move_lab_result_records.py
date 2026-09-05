#!/usr/bin/env python3
"""Move human-readable result records into a navigable Local Wiki collection."""
from __future__ import annotations

import argparse
import os
import re
from datetime import date
from pathlib import Path


LINK = re.compile(r"(?P<prefix>\]\()(?P<target>[^)#\s]+)(?P<suffix>(?:#[^)]+)?\))")


def rewrite_links(text: str, source: Path, destination: Path, lab: Path, moved: dict[Path, Path]) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        if target.startswith(("http:", "https:", "/")):
            return match.group(0)
        resolved = (source.parent / target).resolve()
        resolved = moved.get(resolved, resolved)
        if not resolved.is_relative_to(lab) or not resolved.exists():
            return match.group(0)
        relative = Path(os.path.relpath(resolved, destination.parent)).as_posix()
        return f"{match.group('prefix')}{relative}{match.group('suffix')}"
    return LINK.sub(replace, text)


def page(title: str, record: str) -> str:
    return f"""---
title: {title!r}
status: current
updated: {date.today().isoformat()}
record: true
---

## Summary

Preserved detailed research record. Its scientific interpretation is maintained in the topical Local Wiki pages.

## Evidence

The original dated audit, method, fixture, or benchmark record follows.

## Status

Current as provenance; it is not by itself a report-level claim.

## Related pages

- [[index|Lab Wiki index]]
- [[records/index|Research-record index]]

## Record

{record.lstrip()}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(); lab = args.lab.resolve()
    results, records = lab / "results", lab / "wiki" / "records"
    sources = sorted(results.glob("*.md"))
    if not args.apply:
        for source in sources: print(f"MOVE {source.relative_to(lab)} -> wiki/records/{source.name}")
        return 0
    records.mkdir(parents=True, exist_ok=True)
    moved = {source.resolve(): (records / source.name).resolve() for source in sources}
    entries = []
    for source in sources:
        destination = moved[source.resolve()]
        text = source.read_text(encoding="utf-8")
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), source.stem.replace("-", " "))
        destination.write_text(page(title, rewrite_links(text, source, destination, lab, moved)), encoding="utf-8")
        source.unlink()
        entries.append(f"- [[records/{source.stem}|{title}]]")
    index = records / "index.md"
    previous = index.read_text(encoding="utf-8") if index.is_file() else ""
    prior_entries = [line for line in previous.splitlines() if line.startswith("- [[records/")]
    all_entries = sorted(set(prior_entries + entries))
    index.write_text("---\ntitle: 'Lab research records'\nstatus: current\nupdated: " + date.today().isoformat() + "\n---\n\n## Summary\n\nDetailed dated research records, grouped here as provenance rather than report content.\n\n## Evidence\n\n" + "\n".join(all_entries) + "\n\n## Status\n\nCurrent as an audit trail.\n\n## Related pages\n\n- [[index|Lab Wiki index]]\n", encoding="utf-8")
    root_index = lab / "wiki" / "index.md"
    if root_index.is_file():
        text = root_index.read_text(encoding="utf-8")
        if "records/index" not in text:
            root_index.write_text(text.rstrip() + "\n- [[records/index|Detailed research records]]\n", encoding="utf-8")
    record_names = {path.name for path in records.glob("*.md")}
    record_stems = {path.stem for path in records.glob("*.md")}
    for record_page in records.glob("*.md"):
        text = record_page.read_text(encoding="utf-8")
        # Research runners may emit their detailed Markdown directly to the
        # record collection.  Normalize that raw output before link repair so
        # it becomes a valid, navigable Local Wiki page at the integration
        # gate rather than a second, unofficial document type.
        if not re.match(r"^---\n.*?\n---\n", text, flags=re.S):
            title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), record_page.stem.replace("-", " "))
            text = page(title, text)
            record_page.write_text(text, encoding="utf-8")
        def normalize_wikilink(match: re.Match[str]) -> str:
            target, label = match.group(1), match.group(2)
            target = target.removeprefix("../")
            if "/" not in target and target in record_stems and target != "index":
                target = f"records/{target}"
            return f"[[{target}{'|' + label if label else ''}]]"
        updated = re.sub(r"\[\[([^]|#]+)(?:\|([^]]+))?\]\]", normalize_wikilink, text)
        if updated != text:
            record_page.write_text(updated, encoding="utf-8")
    for wiki_page in (lab / "wiki").rglob("*.md"):
        if wiki_page.is_relative_to(records):
            continue
        text = wiki_page.read_text(encoding="utf-8")
        def repair(match: re.Match[str]) -> str:
            target = match.group(1)
            name = Path(target).name
            if name not in record_names:
                return match.group(0)
            destination = records / name
            return "(" + Path(os.path.relpath(destination, wiki_page.parent)).as_posix() + ")"
        updated = re.sub(r"\((?:\.\./)?results/([^)#]+\.md)\)", repair, text)
        if updated != text:
            wiki_page.write_text(updated, encoding="utf-8")
    # A moved record must not remain canonicalized under results/ in the lab's
    # durable plan or result index.  Those stale pointers caused later agents
    # to recreate the old layout even after a successful migration.
    canonical_records = {item.name for item in records.glob("*.md")}
    for durable_path in (lab / "lab.json", lab / "PLAN.md"):
        if not durable_path.is_file():
            continue
        text = durable_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?<![\w/])results/([^\s\]\\\")]+\.md)",
            lambda match: f"wiki/records/{match.group(1)}" if match.group(1) in canonical_records else match.group(0),
            text,
        )
        if updated != text:
            durable_path.write_text(updated, encoding="utf-8")
    print(f"Moved {len(sources)} result records into {records}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
