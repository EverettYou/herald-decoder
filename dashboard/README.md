# Research dashboard

Run `../run_server.sh`, then open `http://127.0.0.1:8010`. The launcher provides `start`, `status`, `restart`, `stop`, and `logs`; automatically takes over an earlier Herald Decoder process on port 8010; and requires explicit `--takeover` before replacing an unrelated process. Port 8010 is fixed for this project. It always starts through `../run_research_python.sh`, so the live Lab 002 artifact uses the same fail-closed accelerated runtime as numerical research runs.

Supervising tools that need to retain the process in their own terminal use `../run_server.sh foreground`; this follows the same ownership checks and remains part of the single launcher interface.

The dashboard is a read-only project map. It reads canonical status from `project.json`, `references/references.json`, `labs/labs.json`, each lab's `lab.json`, and the shared Wiki Markdown. Edit those research artifacts rather than editing the displayed dashboard text.

## Layout

This follows the Mercor-style frontend/backend split while keeping the project launcher stable:

- `server.py` is the single HTTP entry point used by `../run_server.sh`.
- `backend/` contains reusable server-side modules, including the unified search and community-label services.
- `frontend/` contains the browser shell, page controllers, styles, and local rendering dependencies.
- `tests/` contains backend and frontend contract tests.

The project does not use server-rendered templates; pages are assembled by the frontend from the JSON/Markdown research artifacts. Therefore there is intentionally no `templates/` directory.

## Reference resources after a clone or migration

The reference registry's `status: fetched` records historical acquisition; it does
not guarantee that this checkout contains its cached resources. PDF files are
tracked, but `references/**/source.tar` and `source.tar.gz` are intentionally
ignored by Git. Repository viewers need those archives, pinned to the commit in
each reference's `provenance.json`.

Audit or restore the viewer resources from the project root:

```sh
python3 scripts/restore_reference_resources.py --report .tmp/reference-resources.json
python3 scripts/restore_reference_resources.py --restore --report .tmp/reference-resources.json
```

Restoration downloads only missing resources and requires their original SHA-256
checksums. Existing mismatched files and downloads with different checksums are
reported as errors and never overwritten/installed. No repository code is run.
The optional `--include-paper-sources` flag also restores recorded LaTeX archives;
these are not required to read the PDFs. Reference pages retain canonical source
links when local assets are missing. The server reads restored assets live, so
restoring an archive does not require a restart.

## Homepage Lab evolution

The evolution map uses `parents` and `created` from the live Lab catalog. Columns
represent ancestry, with explicit dates on each study; the horizontal distance
is not elapsed time. All registered connections are retained, including dashed
additional parent links. Study titles are primary and Lab numbers are secondary.

Scroll or drag to pan, pinch to zoom, or use the zoom/Overview buttons. With the
map focused, `+`, `-`, and `0` zoom or fit; Tab and Enter open studies. Narrow
screens initially retain readable cards with horizontal panning available.

Layout regressions live in `tests/research-timeline-layout.test.js`. Run the live
browser audit from the project root with a Playwright Chromium installation:

```sh
python dashboard/tests/verify_evolution_browser.py --base-url http://localhost:8010/
```

The redesign and its verification scope are recorded in
`audits/lab-evolution-2026-09-09.md` and the accompanying JSON.
