# Herald Decoder

> An evidence-first research workspace for symmetry-enriched quantum-error-correction decoding.

Herald Decoder asks whether **current, locally measurable side information** can improve the decoding of topological quantum codes. The first operational model compares an ordinary endpoint syndrome \(S\) with a simultaneous record \((S,H)\), where \(H\) is an \(SU(2)\)-motivated fusion-remnant herald field. It develops matched decoder baselines, simulations, and evidence needed to test that question.

This repository is a research program, not a claim that an improved threshold has been established. The authoritative scientific framing and claim boundaries live in the [Project Page](wiki/thesis.md).

## The essential boundary

In this project, a **herald** is a current fusion-remnant witness: a local observation correlated with incident error structure. It is **not** a qubit-loss flag, a known erasure location, a fusion history, a worldline, or a pairing oracle. A decoder receives only the current snapshot \((S,H)\); it must not reconstruct or assume access to time-ordered microscopic history.

This distinction determines the comparison protocol: an erasure decoder and a herald-aware decoder condition on different observations and are not interchangeable baselines. See [Side-information-aware decoding](wiki/methods/side-information-aware-decoding.md).

## Research goal

The central question is:

> How does symmetry enrichment of topological excitations change quantum-code decodability, and can the resulting measurable structure support more capable practical decoders?

The immediate research gate is to specify a static joint model \(P(E,S,H)\): the current error configuration, endpoint syndrome, and herald snapshot. Only then can the project make a matched comparison between syndrome-only and herald-aware decoders. The full hypothesis, assumptions, and open questions are maintained in the [Project Page](wiki/thesis.md).

## Start here

| If you want to… | Start with |
| --- | --- |
| Understand the research question and its limits | [Project Page](wiki/thesis.md) |
| Compare MWPM, Union-Find, and belief matching | [Error-correction decoding](wiki/concepts/error-correction-decoding.md) |
| Understand the shared simulator and observation model | [String-herald simulator](wiki/models/string-herald-simulator.md) |
| Review the implemented decoder work | [Lab 001](labs/lab-001-string-herald-visualization/) and [Lab 002](labs/lab-002-herald-belief-matching/) |
| Browse citations and implementation provenance | [References](references/) |
| Find an unresolved research decision | [Discussion](discussion/) |

## Quick start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Node.js 18+ to run the browser-side contract tests

```bash
git clone <your-fork-or-repository-url>
cd herald-decoder
uv sync
./run_server.sh
```

Open [http://127.0.0.1:8010](http://127.0.0.1:8010). The local dashboard is the best entry point for the live Wiki, knowledge graph, labs, reference library, and discussion record.

Useful server commands:

```bash
./run_server.sh status
./run_server.sh restart
./run_server.sh logs
./run_server.sh stop
```

### Accelerated research runtime

The dashboard and all decoder benchmarks and Lab sweeps use the same
fail-closed launcher below. It verifies the exact Python, NumPy, Numba, SciPy,
and PyMatching versions listed in `requirements-research.txt` before executing
a command. The dashboard therefore fails at startup rather than silently
serving the Lab 002 artifact through an unaccelerated Python fallback.

```bash
./run_research_python.sh -c 'from herald_decoder import NUMBA_AVAILABLE; print(NUMBA_AVAILABLE)'
```

For a fresh Linux server clone, create the repository-local pinned runtime:

```bash
uv python install 3.13.2
uv venv --python 3.13.2 .venv
uv pip install --python .venv/bin/python -r requirements-research.txt
./run_research_python.sh -c 'import numpy, numba, pymatching, scipy; print("research runtime ready")'
```

The Lab 006 A8 runner uses the validated optimized implementation by default:
Numba-pretabulated full interior `(m,R)` record generation, batched Numba BP,
and posterior-LLR PyMatching. Its LER score depends only on the final
correction clearing the detector syndrome and having trivial residual logical
parity; BP convergence is recorded as a diagnostic and does not gate LER.

Example acquisition of the six registered Lab 006 curves:

```bash
./run_research_python.sh -u labs/lab-006-sun-bp-theory/scripts/dispatch_a8_ler.py --workers 48
```

The dispatcher resumes the six `final-v2` checkpoints without changing their
per-cell RNG streams, keeps inherited originals, and atomically saves each
completed cell. Run only one dispatcher at a time. Each worker uses one CPU
thread; reduce `--workers` on smaller hosts. It refreshes explicitly partial
LER and BP diagnostic panels throughout acquisition. The research scope is
U(1), SU(2), SU(3), square/honeycomb, L=5,7,9,11, 20,000 shots per sampled
cell, with rough-boundary m and R unmeasured; None is deferred.

After the dispatcher finishes, audit all cells and render final plots with:

```bash
./run_research_python.sh labs/lab-006-sun-bp-theory/scripts/finalize_a8_ler.py
```

The original single-curve runner remains available for fresh separately tagged
runs; the expanded current checkpoints are owned by the dispatcher.

## Repository map

```text
├── dashboard/       Local research interface and its API/frontend tests
├── discussion/      Durable questions, decisions, and resolutions
├── labs/            Self-contained exploratory experiments and reports
├── references/      Immutable external-source archive and provenance records
├── skills/          Agent workflows for references, Wiki, labs, and review
├── src/             Promoted reusable code only (not one-off lab code)
├── wiki/            Compiled, cited project knowledge
├── project.json     Live project framing shown by the dashboard
├── pyproject.toml   Python runtime definition
└── run_server.sh    Single launcher for the local dashboard (port 8010)
```

### Where information belongs

- **`references/`** holds papers, repositories, and provenance. It is input material, not a conclusion.
- **`labs/`** holds a proposed or active experiment: its plan, scripts, figures, results, and report. Each lab is self-contained.
- **`wiki/`** holds durable synthesis: cited background and findings supported by completed lab reports. It must not duplicate raw papers or reports.
- **`src/`** receives code only after it has proved reusable across labs and has been validated.
- **`discussion/`** records choices that require researcher judgment; it is the project’s durable decision trail.

## Current architecture

The project deliberately separates evidence from synthesis:

```text
external sources ── provenance ──> references/ ── cited background ──┐
                                                                      ├──> wiki/
experiments ── plans · code · results · reports ──> labs/ ───────────┘
                                      │
                                      └── reusable, validated components ──> src/
```

The dashboard reads these canonical files; it is not a second source of truth. Update the relevant Markdown, JSON, report, or provenance record, then use the dashboard to inspect the result.

## Working with this project as an AI agent

Read this section before modifying research content.

1. **Orient before acting.** Read the [Project Page](wiki/thesis.md), the relevant Wiki method/model page, and the owning lab or reference record. Use the dashboard’s knowledge graph to follow linked material.
2. **Respect the observation model.** Do not treat a herald as an erasure flag or as hidden-history access. Keep comparisons matched in code, noise model, measurement budget, and decoder back end.
3. **Preserve ownership.** Put exploratory code and provisional conclusions in the relevant lab. Promote only cross-lab reusable code to `src/`, and only cited or evidence-backed findings to the Wiki.
4. **Keep evidence separate from synthesis.** Cite the precise paper, repository, lab report, or result artifact behind a claim. State whether it is background, project synthesis, preliminary evidence, or an open question.
5. **Do not manufacture conclusions.** A finite benchmark is not a threshold claim; an implementation reference is not experimental evidence; an unresolved scientific choice belongs in `discussion/` rather than being silently assumed.
6. **Validate the layer you changed.** Run the relevant lab tests for experiment code, the Wiki lint for Wiki edits, and dashboard tests for interface or graph changes.

The project workflows are available as local skills:

| Task | Workflow |
| --- | --- |
| Discover or acquire a source | [`discover-references`](skills/discover-references/SKILL.md), [`fetch-reference`](skills/fetch-reference/SKILL.md) |
| Distill supported knowledge into the Wiki | [`wiki-ingest`](skills/wiki-ingest/SKILL.md), [`wiki-query`](skills/wiki-query/SKILL.md) |
| Audit Wiki structure and knowledge health | [`wiki-lint`](skills/wiki-lint/SKILL.md) |
| Propose and run an experiment or bounded research cycle | [`create-lab`](skills/create-lab/SKILL.md), [`auto-research`](skills/auto-research/SKILL.md) |
| Guide a scientific investigation end to end | [`research-workflow`](skills/research-workflow/SKILL.md) |
| Escalate a substantive decision | [`consult-human`](skills/consult-human/SKILL.md) |

## Verification

Run checks from the repository root after making the corresponding change:

```bash
# Wiki links, provenance, and structure
uv run python skills/wiki-lint/scripts/lint_wiki.py .

# Dashboard server and knowledge-graph contracts
uv run python -m unittest dashboard.tests.test_knowledge_graph
node --test dashboard/tests/*.test.js

# A lab’s own tests (example)
PYTHONPATH=labs/lab-002-herald-belief-matching/scripts \
  uv run python -m unittest discover \
  -s labs/lab-002-herald-belief-matching/scripts \
  -p 'test_*.py'
```

For task-specific commands and expected artifacts, treat the lab’s `PLAN.md`, `REPORT.md`, and `scripts/README.md` as authoritative.

## Contributing research changes

Keep changes narrow and reviewable:

1. Identify the owner layer: reference, lab, Wiki, reusable source, dashboard, or discussion.
2. Change the canonical artifact in that layer.
3. Add or update provenance and links when the relationship changes.
4. Run the relevant checks above.
5. Record scientific limitations and unresolved decisions explicitly.

Before opening a GitHub pull request, avoid bundling generated caches, local virtual environments, or unrelated experimental outputs with the research change.

## Further documentation

- [Wiki overview](wiki/README.md)
- [Labs overview](labs/README.md)
- [Dashboard guide](dashboard/README.md)
- [Reference archive guide](references/README.md)
- [Discussion guide](discussion/README.md)
- [Skills overview](skills/README.md)

[Scientific correction: full prior domain for binary herald decoding](wiki/methods/binary-herald-full-prior-domain.md)
