import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("lab_wiki_lint", ROOT / "skills" / "organize-lab" / "scripts" / "lab_wiki_lint.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_local_wiki_requires_navigable_current_page(tmp_path):
    lab = tmp_path / "lab-004-example"
    (lab / "results").mkdir(parents=True)
    (lab / "results" / "evidence.json").write_text('{"value": 1}')
    (lab / "wiki").mkdir()
    (lab / "wiki" / "index.md").write_text("# Index\n\n- [[method|Method]]\n")
    (lab / "wiki" / "method.md").write_text("""---
title: Method
status: current
updated: 2026-09-01
---

## Summary

Method summary.

## Evidence

[Evidence](../results/evidence.json)

## Status

Current.

## Related pages

[[index|Index]]
""")
    assert MODULE.lint(lab) == []


def test_local_wiki_rejects_unexplained_withdrawal(tmp_path):
    lab = tmp_path / "lab-004-example"
    (lab / "wiki").mkdir(parents=True)
    (lab / "wiki" / "index.md").write_text("# Index\n\n- [[old|Old]]\n")
    (lab / "wiki" / "old.md").write_text("""---
title: Old
status: withdrawn
updated: 2026-09-01
---

## Summary

Old result.

## Evidence

None.

## Status

Withdrawn.

## Related pages

[[index|Index]]
""")
    assert any("replacement or reason" in error for error in MODULE.lint(lab))


def test_local_wiki_rejects_a_run_level_lab_subtitle(tmp_path):
    lab = tmp_path / "lab-004-example"
    (lab / "wiki").mkdir(parents=True)
    (lab / "wiki" / "index.md").write_text("# Index\n")
    (lab / "lab.json").write_text('{"summary": "R6AG finds a local result."}')
    assert any("summary must describe the lab purpose" in error for error in MODULE.lint(lab))


def test_local_wiki_document_cannot_leak_into_result_cards(tmp_path):
    lab = tmp_path / "lab-004-example"
    (lab / "wiki" / "records").mkdir(parents=True)
    (lab / "wiki" / "index.md").write_text("# Index\n\n- [[records/index|Records]]\n")
    (lab / "wiki" / "records" / "index.md").write_text("""---
title: Records
status: current
updated: 2026-09-01
---

## Summary

Record index.

## Evidence

None.

## Status

Current.

## Related pages

[[index|Index]]
""")
    (lab / "lab.json").write_text("""{
      "summary": "Study a durable scientific question.",
      "results": [{
        "id": "internal-audit",
        "kind": "document",
        "format": "markdown",
        "path": "wiki/records/internal-audit.md",
        "presentation": "result"
      }]
    }""")
    errors = MODULE.lint(lab)
    assert any("must not be published as a Result card" in error for error in errors)
