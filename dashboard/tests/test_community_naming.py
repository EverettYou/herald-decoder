from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dashboard.backend.community_naming import enrich_community_labels


class FakeResponses:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps({
            "labels": [{"community_id": 0, "label": "error correction decoders"}],
        }))


class CommunityNamingTests(unittest.TestCase):
    def test_title_cased_structured_label_is_cached(self):
        graph = {
            "nodes": [{"id": "methods/example", "label": "Example decoder", "community": 0, "weighted_degree": 2}],
            "communities": [{"id": 0, "label": "Decoding Algorithms"}],
        }
        pages = [{"id": "methods/example", "title": "Example decoder", "page_type": "method", "topics": ["Decoding Algorithms"], "preview": "A decoder."}]
        responses = FakeResponses()
        with tempfile.TemporaryDirectory() as directory:
            stats = enrich_community_labels(
                graph, pages, cache_path=Path(directory) / "labels.json", api_key="test-key", model="test-model",
                client_factory=lambda **_: SimpleNamespace(responses=responses),
            )
        self.assertEqual(stats, {"cached": 0, "generated": 1, "fallback": 0})
        self.assertEqual(graph["communities"][0]["label"], "Error Correction Decoders")
        self.assertFalse(responses.calls[0]["store"])
        self.assertEqual(responses.calls[0]["text"]["format"]["type"], "json_schema")

    def test_all_communities_are_named_in_one_cached_request(self):
        graph = {
            "nodes": [
                {"id": "methods/matching", "label": "Matching decoder", "community": 0, "weighted_degree": 2},
                {"id": "methods/side-info", "label": "Side-information decoder", "community": 1, "weighted_degree": 2},
            ],
            "communities": [{"id": 0, "label": "Quantum Error Correction"}, {"id": 1, "label": "Quantum Error Correction"}],
        }
        pages = [
            {"id": "methods/matching", "title": "Matching decoder", "page_type": "method", "topics": ["Quantum Error Correction"], "preview": "Matching."},
            {"id": "methods/side-info", "title": "Side-information decoder", "page_type": "method", "topics": ["Quantum Error Correction"], "preview": "Side information."},
        ]
        responses = FakeResponses()
        responses.create = lambda **kwargs: (responses.calls.append(kwargs) or SimpleNamespace(output_text=json.dumps({
            "labels": [
                {"community_id": 0, "label": "Matching Decoders"},
                {"community_id": 1, "label": "Side-Information Decoding"},
            ],
        })))
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "labels.json"
            first = enrich_community_labels(graph, pages, cache_path=cache_path, api_key="test-key", model="test-model", client_factory=lambda **_: SimpleNamespace(responses=responses))
            second = enrich_community_labels(graph, pages, cache_path=cache_path, api_key="test-key", model="test-model", client_factory=lambda **_: SimpleNamespace(responses=responses))
        self.assertEqual(first, {"cached": 0, "generated": 2, "fallback": 0})
        self.assertEqual(second, {"cached": 2, "generated": 0, "fallback": 0})
        self.assertEqual(len(responses.calls), 1)
        self.assertIn('<community id="0"', responses.calls[0]["input"])
        self.assertIn('<community id="1"', responses.calls[0]["input"])


if __name__ == "__main__":
    unittest.main()
