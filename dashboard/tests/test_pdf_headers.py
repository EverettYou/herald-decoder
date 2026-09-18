import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from dashboard.server import Handler, cache_headers_for_content_type, parse_byte_range, prefers_pdf_html_viewer


class PdfCacheHeaderTests(unittest.TestCase):
    def test_pdf_responses_are_revalidatable_not_no_store(self):
        headers = dict(cache_headers_for_content_type("application/pdf"))
        self.assertNotIn("no-store", headers["Cache-Control"])
        self.assertIn("must-revalidate", headers["Cache-Control"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertNotIn("Pragma", headers)

    def test_json_api_responses_remain_uncached(self):
        headers = dict(cache_headers_for_content_type("application/json; charset=utf-8"))
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(headers["Pragma"], "no-cache")


class ByteRangeTests(unittest.TestCase):
    def test_missing_header_means_full_body(self):
        self.assertIsNone(parse_byte_range(100, None))
        self.assertIsNone(parse_byte_range(100, ""))

    def test_open_and_closed_ranges(self):
        self.assertEqual(parse_byte_range(100, "bytes=0-9"), (0, 9))
        self.assertEqual(parse_byte_range(100, "bytes=50-"), (50, 99))
        self.assertEqual(parse_byte_range(100, "bytes=-10"), (90, 99))

    def test_invalid_ranges_raise(self):
        with self.assertRaises(ValueError):
            parse_byte_range(100, "bytes=200-201")
        with self.assertRaises(ValueError):
            parse_byte_range(100, "items=0-1")


class PdfHttpTests(unittest.TestCase):
    paper = "/api/references/jing2026-ilp-topological-decoder/pdf"

    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.httpd.server_address

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _request(self, method, path, headers=None):
        connection = HTTPConnection(self.host, self.port, timeout=10)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        header_map = {key.lower(): value for key, value in response.getheaders()}
        connection.close()
        return response.status, header_map, body

    def test_get_pdf_redirects_to_html_viewer(self):
        status, headers, body = self._request("GET", self.paper)
        self.assertEqual(status, 302)
        self.assertEqual(headers["location"], "/pdf-viewer?id=jing2026-ilp-topological-decoder")
        self.assertEqual(body, b"")

    def test_pdf_viewer_page_loads_the_toolbar_script(self):
        status, headers, body = self._request("GET", "/pdf-viewer?id=jing2026-ilp-topological-decoder")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["content-type"])
        self.assertIn(b"HeraldPdfViewer.mount", body)
        self.assertIn(b"/bytes", body)
        self.assertIn(b"pdf-viewer.js", body)

    def test_head_pdf_matches_raw_bytes(self):
        get_status, get_headers, get_body = self._request("GET", self.paper + "?raw=1")
        head_status, head_headers, head_body = self._request("HEAD", self.paper)
        self.assertEqual(get_status, 200)
        self.assertEqual(head_status, 200)
        self.assertEqual(head_body, b"")
        self.assertEqual(head_headers["content-type"], "application/pdf")
        self.assertEqual(head_headers["content-length"], get_headers["content-length"])
        self.assertEqual(int(get_headers["content-length"]), len(get_body))

    def test_range_request_returns_partial_content(self):
        paper = Path(__file__).resolve().parents[2] / "references/jing2026-ilp-topological-decoder/paper.pdf"
        expected = paper.read_bytes()
        status, headers, body = self._request("GET", self.paper, headers={"Range": "bytes=0-15"})
        self.assertEqual(status, 206)
        self.assertEqual(body, expected[:16])
        self.assertEqual(headers["content-range"], f"bytes 0-15/{len(expected)}")
        self.assertEqual(headers["content-length"], "16")

    def test_raw_query_stays_pdf_bytes(self):
        status, headers, body = self._request("GET", self.paper + "?raw=1")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "application/pdf")
        self.assertTrue(body.startswith(b"%PDF-"))

    def test_all_archived_papers_serve_pdf_bytes(self):
        root = Path(__file__).resolve().parents[2]
        records = json.loads((root / "references" / "references.json").read_text())["references"]
        papers = [item["id"] for item in records if (root / "references" / item["id"] / "paper.pdf").is_file()]
        self.assertGreaterEqual(len(papers), 10)
        for paper_id in papers:
            status, headers, body = self._request("GET", f"/api/references/{paper_id}/bytes")
            self.assertEqual(status, 200, paper_id)
            self.assertEqual(headers["content-type"], "application/pdf", paper_id)
            self.assertTrue(body.startswith(b"%PDF"), paper_id)


class PdfViewerPreferenceTests(unittest.TestCase):
    def test_fetch_and_head_keep_bytes(self):
        self.assertFalse(prefers_pdf_html_viewer("HEAD", {}, {"Accept": "text/html"}))
        self.assertFalse(prefers_pdf_html_viewer("GET", {"raw": ["1"]}, {"Sec-Fetch-Dest": "document"}))
        self.assertFalse(prefers_pdf_html_viewer("GET", {}, {"Range": "bytes=0-1"}))
        self.assertFalse(prefers_pdf_html_viewer("GET", {}, {"Sec-Fetch-Dest": "empty"}))

    def test_plain_get_uses_html(self):
        self.assertTrue(prefers_pdf_html_viewer("GET", {}, {}))
        self.assertTrue(prefers_pdf_html_viewer("GET", {}, {"Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate"}))
        self.assertTrue(prefers_pdf_html_viewer("GET", {}, {"Accept": "text/html,application/xhtml+xml"}))


if __name__ == "__main__":
    unittest.main()
