import os
import unittest
from unittest.mock import patch

from dashboard.backend.search import hybrid_relevance_score, is_complex_query, lexical_score, local_search
from dashboard.server import unified_search_documents, unified_search_payload


class UnifiedSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = unified_search_documents()

    def test_all_three_catalogs_share_one_document_schema(self):
        self.assertEqual(
            {document["entity_type"] for document in self.documents},
            {"reference", "lab", "wiki"},
        )
        self.assertTrue(all(document["target"]["href"].startswith("/") for document in self.documents))

    def test_exact_title_is_protected_as_navigation(self):
        document = next(document for document in self.documents if document["entity_type"] == "lab")
        score, reason = lexical_score(document["title"], document)
        self.assertEqual(score, 20.0)
        self.assertIn("Exact", reason)

    def test_mercor_tuned_blend_allows_conceptual_relevance(self):
        conceptual = hybrid_relevance_score(0.0, 0.90, semantic_floor=0.68, top_similarity=0.90)
        weak_keyword = hybrid_relevance_score(4.5, 0.80, semantic_floor=0.68, top_similarity=0.90)
        self.assertGreater(conceptual, weak_keyword)

    def test_complex_constraints_trigger_bounded_llm_refinement(self):
        self.assertTrue(is_complex_query(
            "Find work with herald information but without fusion history and compare current evidence"
        ))
        self.assertFalse(is_complex_query("herald decoder"))

    def test_local_fallback_respects_scope(self):
        result = local_search("belief matching", scope="labs", documents=self.documents)
        self.assertTrue(result["results"])
        self.assertTrue(all(item["entity_type"] == "lab" for item in result["results"]))

    def test_server_falls_back_without_semantic_opt_in(self):
        with patch.dict(os.environ, {"OPENAI_CATALOG_SEARCH_ENABLED": "0"}):
            result = unified_search_payload("surface code", "references", 10, False)
        self.assertEqual(result["mode"], "local")
        self.assertTrue(all(item["entity_type"] == "reference" for item in result["results"]))


if __name__ == "__main__":
    unittest.main()
