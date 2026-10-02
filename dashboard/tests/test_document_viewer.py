import unittest

from dashboard import server


class ProjectDocumentViewerTests(unittest.TestCase):
    def test_wiki_document_uses_the_wiki_reader(self):
        self.assertEqual(
            server.project_document_href("wiki/methods/herald-aware-belief-matching.md"),
            "/wiki?page=methods%2Fherald-aware-belief-matching",
        )

    def test_lab_markdown_uses_the_generic_document_reader(self):
        href = server.project_document_href(
            "labs/lab-002-herald-belief-matching/notes/bp-convergence-remediation.md"
        )
        self.assertEqual(
            href,
            "/document?path=labs%2Flab-002-herald-belief-matching%2Fnotes%2Fbp-convergence-remediation.md",
        )

    def test_payload_is_scoped_and_readable(self):
        payload = server.project_document_payload(
            "labs/lab-002-herald-belief-matching/REPORT.md"
        )
        self.assertEqual(payload["kind"], "markdown")
        self.assertEqual(payload["path"], "labs/lab-002-herald-belief-matching/REPORT.md")
        self.assertIn("Herald-aware belief matching", payload["content"])

    def test_payload_rejects_paths_outside_the_read_only_roots(self):
        with self.assertRaises(ValueError):
            server.project_document_payload("../.env")
        with self.assertRaises(FileNotFoundError):
            server.project_document_payload("dashboard/server.py")

    def test_integrated_decoder_source_is_readable(self):
        payload = server.project_document_payload("src/herald_decoder/README.md")
        self.assertEqual(payload["kind"], "markdown")
        self.assertIn("make_decoder", payload["content"])
        source = server.project_document_payload("src/herald_decoder/planar_ml.py")
        self.assertEqual(source["kind"], "code")


if __name__ == "__main__":
    unittest.main()
