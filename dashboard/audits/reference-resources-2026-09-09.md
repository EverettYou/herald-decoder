# Reference resource migration audit — 2026-09-09

The repository-viewer failure was reproduced in the live API: all five pinned
repository archives were absent. Git intentionally excludes `source.tar` and
`source.tar.gz`; registry `status: fetched` is historical acquisition metadata,
not an inventory of the current checkout. The repository frontend requested the
missing archive before rendering its header, turning that absence into a whole
page “Dashboard error” and hiding the canonical source link.

All five snapshots were restored from the original codeload URLs at the recorded
commits: BeliefMatching, uf_decoder, Relay-BP, LieART, and PyMatching. All downloaded
SHA-256 hashes match their existing provenance records. No snapshot was upgraded
and no downloaded repository code was executed. Their live file lists contain
15, 43, 739, 36, and 200 files respectively; all five README endpoints work.

All 27 local PDFs existed before this work and match the original provenance
hashes. Every live PDF GET returns HTTP 200, application/pdf, and matching bytes.
The running service already had a PDF cache-header change and inline disposition
before this audit. This audit did not change that behavior or establish the
older cache policy as the cause of the user's current symptom.

Twenty-one recorded paper-source archives are still missing. They contain the
paper sources rather than the PDFs used by the reader and are not needed for
PDF display. Six papers have no source archive recorded in their provenance.
Use `--include-paper-sources` with the recovery tool if those optional sources
are needed; they were not silently replaced with newer versions.

The frontend now preserves the reference header and canonical source link when
local resources are missing. The recovery command and migration limitations are
documented in `dashboard/README.md`. Archives remain ignored by Git, so future
clones must run `python3 scripts/restore_reference_resources.py --restore`.

Verification is separated by layer in the accompanying JSON: registry/provenance,
local resources, live HTTP, and browser results. Browser screenshots are retained
locally in `.tmp/reference-audit/`. The audit used the live service at
`http://localhost:8010`; it does not certify an unknown forwarded URL, application
webview, or the user's browser. The reported PDF problem remains unlocalized in
that user-specific environment, and must not be represented as fixed there.

Chromium completed PDF loading (100% with nonzero page counts) for all 27
papers and displayed all five repository READMEs. The catalog rendered 32 cards.
Both simulated missing-resource cases (paper and repository) retained their
canonical links and displayed an explanatory message without Dashboard error.
Existing reference identifier tests (3) and PDF cache-header tests (2) passed;
both changed JavaScript modules passed syntax checks.
