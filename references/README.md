# References

This is the immutable provenance index for papers, repositories, datasets, and
other external research materials. A reference is registered in
`references.json`; retained PDFs and provenance belong in
`references/<reference-id>/`.

Upstream source archives are intentionally omitted from Git because they are
exactly reproducible from the retrieval URL and SHA-256 recorded in each
`provenance.json`. Downloaded `source.tar` and `source.tar.gz` files are ignored;
verify their checksum against provenance before using them.

Repository `source.tar.gz` snapshots are nevertheless required runtime inputs
for the dashboard repo viewer. Restore missing pinned snapshots with
`python3 scripts/restore_reference_resources.py --restore`. The restore command
verifies each archive against provenance before installing it. Storage cleanup
may remove reproducible paper source archives, but must retain repository
snapshots while the local dashboard is expected to browse them.

References are inputs to the project, not candidates to be scored. Their scientific claims are distilled into the shared Wiki with explicit citations.
