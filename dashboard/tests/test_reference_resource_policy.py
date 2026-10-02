import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compact_repository_payloads.py"
SPEC = importlib.util.spec_from_file_location("compact_repository_payloads", SCRIPT)
COMPACTION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(COMPACTION)


class ReferenceResourcePolicyTest(unittest.TestCase):
    def test_repository_snapshots_are_never_selected_for_storage_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references = root / "references"
            fixtures = {
                "repo-code": ("repository", b"repo snapshot"),
                "paper": ("paper", b"paper source"),
            }
            for reference_id, (kind, body) in fixtures.items():
                folder = references / reference_id
                folder.mkdir(parents=True)
                archive = folder / "source.tar.gz"
                archive.write_bytes(body)
                (folder / "provenance.json").write_text(json.dumps({
                    "kind": kind,
                    "urls": {"repository" if kind == "repository" else "source": "https://example.invalid/source"},
                    "sha256": {archive.name: hashlib.sha256(body).hexdigest()},
                }))

            previous_root = COMPACTION.REPO
            COMPACTION.REPO = root
            try:
                selected = COMPACTION.verify_reference_sources()
            finally:
                COMPACTION.REPO = previous_root

            self.assertEqual([item["path"] for item in selected], ["references/paper/source.tar.gz"])


if __name__ == "__main__":
    unittest.main()
