import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("lab_report_lint", ROOT / "skills" / "organize-lab" / "scripts" / "lab_report_lint.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_lab(tmp_path: Path, report: str) -> Path:
    lab = tmp_path / "lab-004-example"
    (lab / "results").mkdir(parents=True)
    (lab / "figures").mkdir()
    (lab / "figures" / "curve.png").write_bytes(b"png")
    (lab / "lab.json").write_text(json.dumps({"report_contract": {"max_lines": 80, "max_evidence_links": 3}}))
    (lab / "REPORT.md").write_text(report)
    return lab


def test_report_lint_accepts_contract_compliant_report(tmp_path):
    lab = write_lab(tmp_path, """# Lab 004 — Example

## Overview

### L004.1 Motivation
Why this matters.

### L004.2 Background
Known context.

### L004.3 Question
What happens?

### L004.4 Hypothesis
This is testable.

## Evidence

### L004.5 Facts
The matched comparison supports the stated result.

![Matched curve](figures/curve.png)

*Figure L004.5 — matched curve supports the comparison; data: [evidence.json](results/evidence.json).* 

### L004.6 Evidence map
[L004.5 data](results/evidence.json)

## Analysis

### L004.7 Implications
The mechanism is plausible.

### L004.8 Limitations
This is finite-size evidence.

### L004.9 Next question
Measure the next discriminating condition.
""")
    assert MODULE.lint(lab) == []


def test_report_lint_rejects_raw_run_ids_and_unstructured_evidence(tmp_path):
    lab = write_lab(tmp_path, """# Lab 004 — Example

## Overview

### L004.1 Motivation
Why this matters.

## Evidence

### L004.2 Facts
R6AB was better.

## Analysis

### L004.3 Implications
Maybe useful.
""")
    errors = MODULE.lint(lab)
    assert any("reader-facing internal run IDs" in item for item in errors)
    assert any("report is prose-only" in item for item in errors)
    assert any("missing required numbered subsection" in item for item in errors)


def test_report_lint_accepts_a_table_without_requiring_a_figure(tmp_path):
    lab = write_lab(tmp_path, """# Lab 004 — Example

## Overview

### L004.1 Motivation
Why this matters.

### L004.2 Background
Known context.

### L004.3 Question
What happens?

### L004.4 Hypothesis
This is testable.

## Evidence

### L004.5 Facts
| Policy | Error rate |
| --- | --- |
| A | 0.10 |

### L004.6 Evidence map
[L004.5 data](results/evidence.json)

## Analysis

### L004.7 Implications
The mechanism is plausible.

### L004.8 Limitations
This is finite-size evidence.

### L004.9 Next question
Measure the next discriminating condition.
""")
    assert MODULE.lint(lab) == []


def test_report_lint_rejects_a_static_file_mislabelled_as_artifact(tmp_path):
    lab = write_lab(tmp_path, """# Lab 004 — Example

## Overview

### L004.1 Motivation
Why this matters.

### L004.2 Background
Known context.

### L004.3 Question
What happens?

### L004.4 Hypothesis
This is testable.

## Evidence

### L004.5 Facts
[Interactive artifact](results/curve.png)

### L004.6 Evidence map
[L004.5 data](results/evidence.json)

## Analysis

### L004.7 Implications
The mechanism is plausible.

### L004.8 Limitations
This is finite-size evidence.

### L004.9 Next question
Measure the next discriminating condition.
""")
    assert any("interactive artifact" in item for item in MODULE.lint(lab))


def test_report_lint_rejects_duplicated_prose_and_dashboard_routes(tmp_path):
    repeated = "This is a deliberately repeated explanation of a bounded result and its limitation, written long enough to be a meaningful paragraph-level duplication rather than an ordinary repeated label."
    lab = write_lab(tmp_path, f"""# Lab 004 — Example

{repeated}

{repeated}

![Curve](/lab-assets/lab-004-example/figures/curve.png)
""")
    errors = MODULE.lint(lab)
    assert any("duplicated prose" in item for item in errors)
    assert any("dashboard-only" in item for item in errors)


def test_report_lint_rejects_a_withdrawn_local_wiki_citation(tmp_path):
    lab = write_lab(tmp_path, "# Lab 004 — Example\n\n[Old evidence](wiki/old.md)\n")
    (lab / "wiki").mkdir()
    (lab / "wiki" / "old.md").write_text("---\nstatus: withdrawn\n---\n")
    assert any("non-current Local Wiki" in item for item in MODULE.lint(lab))
