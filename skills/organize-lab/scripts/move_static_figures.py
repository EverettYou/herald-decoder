#!/usr/bin/env python3
"""Move static result images into a lab's figures/ directory and repair references."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXTENSIONS = {".png", ".svg", ".jpg", ".jpeg", ".pdf"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", type=Path); parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(); lab = args.lab.resolve(); results, figures = lab / "results", lab / "figures"
    sources = [path for path in results.iterdir() if path.is_file() and path.suffix.lower() in EXTENSIONS]
    if not args.apply:
        for source in sources: print(f"MOVE results/{source.name} -> figures/{source.name}")
        return 0
    figures.mkdir(exist_ok=True)
    for source in sources:
        destination = figures / source.name
        if destination.exists():
            if hashlib.file_digest(source.open("rb"), "sha256").hexdigest() != hashlib.file_digest(destination.open("rb"), "sha256").hexdigest():
                raise FileExistsError(destination)
            source.unlink()
            continue
        source.rename(destination)
    names = [source.name for source in sources]
    refs = [*lab.rglob("*.md"), lab / "lab.json", * (lab / "manifests").glob("*.json"), * (lab / "scripts").glob("*.py")]
    for path in refs:
        if not path.is_file(): continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for name in names: updated = updated.replace(f"results/{name}", f"figures/{name}")
        if updated != text: path.write_text(updated, encoding="utf-8")
    print(f"Moved {len(sources)} static figures into {figures}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
