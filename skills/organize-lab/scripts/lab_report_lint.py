#!/usr/bin/env python3
"""Deterministic completion checks for a lab's reader-facing report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULTS = {"max_lines": 500, "max_evidence_links": 12}
REQUIRED_SECTIONS = ["Overview", "Evidence", "Analysis"]
REQUIRED_OVERVIEW = ["Motivation", "Background", "Question", "Hypothesis"]
REQUIRED_ANALYSIS = ["Implications", "Limitations", "Next question"]


def visible_markdown(text: str) -> str:
    """Remove destinations so provenance filenames do not count as prose."""
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", text)


def lint(lab: Path) -> list[str]:
    report_path, metadata_path = lab / "REPORT.md", lab / "lab.json"
    if not report_path.is_file():
        return ["REPORT.md is missing"]
    if not metadata_path.is_file():
        return ["lab.json is missing"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    contract = dict(DEFAULTS)
    contract.update(metadata.get("report_contract", {}))
    text = report_path.read_text(encoding="utf-8")
    errors: list[str] = []
    lab_match = re.search(r"lab-(\d+)-", lab.name)
    if not lab_match:
        return ["lab directory must begin with lab-<number>-"]
    prefix = f"L{int(lab_match.group(1)):03d}"

    if re.search(r"\]\(/lab-(?:result|assets)[^)]+\)", text):
        errors.append("report uses dashboard-only asset routes; use portable relative citations")
    wiki_targets = re.findall(r"\[[^]]+\]\((wiki/[^)#]+\.md)(?:#[^)]+)?\)", text)
    if (lab / "wiki").is_dir() and not wiki_targets:
        errors.append("report must cite at least one current Local Wiki page")
    for target in wiki_targets:
        page = lab / target
        if not page.is_file():
            errors.append(f"report cites missing Local Wiki page: {target}")
        elif not re.search(r"^status:\s*current\s*$", page.read_text(encoding="utf-8"), flags=re.M):
            errors.append(f"report cites non-current Local Wiki page: {target}")

    def subsection_blocks(section: str) -> list[tuple[str, str]]:
        return [(match.group(1), match.group(2)) for match in re.finditer(
            r"^###\s+(.+?)\s*$([\s\S]*?)(?=^###\s+|\Z)", section, flags=re.M
        )]

    def has_current_wiki(block: str) -> bool:
        return any(target in wiki_targets for target in re.findall(r"\[[^]]+\]\((wiki/[^)#]+\.md)(?:#[^)]+)?\)", block))
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", visible_markdown(text))]
    repeated = {block for block in paragraphs if len(block) > 120 and paragraphs.count(block) > 1}
    if repeated:
        errors.append("report contains duplicated prose paragraphs")

    if len(text.splitlines()) > int(contract["max_lines"]):
        errors.append(f"report has {len(text.splitlines())} lines; contract limit is {contract['max_lines']}")
    h2 = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.M)
    if h2 != REQUIRED_SECTIONS:
        errors.append("top-level sections must be exactly: Overview, Evidence, Analysis")
    headings = re.findall(r"^#{3,4}\s+(.+?)\s*$", text, flags=re.M)
    for label in REQUIRED_OVERVIEW + REQUIRED_ANALYSIS:
        if not any(re.search(rf"\b{re.escape(label)}\b", heading, flags=re.I) for heading in headings):
            errors.append(f"missing required numbered subsection: {label}")
    for heading in headings:
        if not re.match(rf"{prefix}\.\d+(?:\.\d+)*\s+", heading):
            errors.append(f"heading lacks {prefix} decimal identifier: {heading}")

    images = re.findall(r"!\[([^]]*)\]\(([^)]+)\)", text)
    for alt, target in images:
        if not target.startswith("figures/"):
            errors.append(f"report figure must live under figures/: {target}")
        if not alt.strip():
            errors.append("report figure needs descriptive alt text")
    for match in re.finditer(r"!\[[^]]*\]\([^)]+\)\s*\n\s*\*([^\n*]+)\*", text):
        caption = match.group(1)
        if not re.match(rf"Figure\s+{prefix}\.\d+(?:\.\d+)*\b", caption):
            errors.append(f"figure caption must begin 'Figure {prefix}.n': {caption}")
        if "data:" not in caption.casefold():
            errors.append(f"figure caption must cite supporting data: {caption}")
    if len(re.findall(r"!\[[^]]*\]\([^)]+\)\s*\n\s*\*[^\n*]+\*", text)) != len(images):
        errors.append("every report figure needs an immediate italic caption")

    tables = re.findall(r"^\|[^\n]+\|\n\|\s*:?-{3,}", text, flags=re.M)
    artifacts = re.findall(r"\[([^]]*artifact[^]]*)\]\(([^)]+)\)", text, flags=re.I)
    for label, target in artifacts:
        if not target.startswith("results/") or not target.endswith(".html"):
            errors.append(f"interactive artifact must link to results/*.html: {label}")
    limitations_match = re.search(r"^##\s+Analysis\s*$([\s\S]*)", text, flags=re.M)
    has_exception = bool(limitations_match and re.search(r"no meaningful visual", limitations_match.group(1), flags=re.I))
    if not (images or tables or artifacts or has_exception):
        errors.append("report is prose-only; add a figure, table, or interactive artifact, or explain why no meaningful visual exists")

    evidence_match = re.search(r"^##\s+Evidence\s*$([\s\S]*?)(?=^##\s+Analysis\s*$)", text, flags=re.M)
    if evidence_match:
        if (lab / "wiki").is_dir():
            for heading, block in subsection_blocks(evidence_match.group(1)):
                if not has_current_wiki(block):
                    errors.append(f"evidence subsection lacks a current Local Wiki citation: {heading}")
        links = re.findall(r"(?<!!)\[[^]]+\]\([^)]+\)", evidence_match.group(1))
        if len(links) > int(contract["max_evidence_links"]):
            errors.append(f"evidence map has {len(links)} links; contract limit is {contract['max_evidence_links']}")
    elif re.search(r"^##\s+Evidence\s*$", text, flags=re.M):
        errors.append("Evidence section exists but the required top-level section order is invalid")
    else:
        errors.append("Evidence section is missing")
    analysis_match = re.search(r"^##\s+Analysis\s*$([\s\S]*)", text, flags=re.M)
    if analysis_match and (lab / "wiki").is_dir():
        for heading, block in subsection_blocks(analysis_match.group(1)):
            if re.search(r"\b(Implications|Limitations)\b", heading, flags=re.I) and not has_current_wiki(block):
                errors.append(f"analysis subsection lacks a current Local Wiki citation: {heading}")
    leaked = sorted(set(re.findall(r"\b(?:R|P|M)\d+(?:\.\d+|[A-Z]+)?\b", visible_markdown(text))))
    if leaked:
        errors.append(f"reader-facing internal run IDs are forbidden: {', '.join(leaked)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", type=Path, help="path to labs/<lab-id>")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    errors = lint(args.lab)
    if args.as_json:
        print(json.dumps({"lab": str(args.lab), "ok": not errors, "errors": errors}, indent=2))
    elif errors:
        print("Lab report lint failed:")
        for item in errors:
            print(f"- {item}")
    else:
        print("Lab report lint passed.")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
