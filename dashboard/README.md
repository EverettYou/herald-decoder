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
