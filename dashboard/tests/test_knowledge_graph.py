import json
import re
import unittest
from collections import Counter
from unittest.mock import patch

from dashboard.server import LABS, LAB_STAGES, lab_catalog, knowledge_graph, normalize_community_label, project_payload, wiki_index_payload, wiki_pages


class KnowledgeGraphModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("dashboard.server.enrich_community_labels", return_value={"cached": 0, "generated": 0, "fallback": 0}):
            cls.graph = knowledge_graph(wiki_pages())

    def test_display_edges_have_explicit_semantic_roles(self):
        roles = Counter(edge["display_role"] for edge in self.graph["display_edges"])
        self.assertLessEqual(roles["predicted"], 4)
        self.assertTrue(roles["authored"])
        self.assertTrue(roles["grounded"])
        self.assertEqual(set(roles) - {"authored", "grounded", "predicted"}, set())

    def test_predictions_are_not_keyword_or_source_links(self):
        for edge in self.graph["edges"]:
            self.assertNotIn("keyword_overlap", edge["signals"])
            if edge["display_role"] == "predicted":
                self.assertFalse(edge["signals"]["direct"])
                self.assertFalse(edge["signals"]["citation"])
                self.assertFalse(edge["signals"]["source_overlap"])
                self.assertTrue(edge["signals"]["adamic_adar"])

    def test_explicit_citations_are_grounded_not_predicted(self):
        citation_edges = [edge for edge in self.graph["edges"] if edge["signals"]["citation"]]
        self.assertTrue(citation_edges)
        self.assertTrue(all(edge["display_role"] == "grounded" for edge in citation_edges))
        displayed = {(edge["source"], edge["target"]) for edge in self.graph["display_edges"]}
        self.assertTrue(all((edge["source"], edge["target"]) in displayed for edge in citation_edges))

    def test_dashboard_reference_citations_connect_decoder_implementation_records(self):
        nodes = {node["id"]: node for node in self.graph["nodes"]}
        for reference_id in ("beliefmatching-code", "pymatching-code", "uf-decoder-code"):
            node = nodes[f"reference/{reference_id}"]
            self.assertGreater(node["degree"], 0, reference_id)
            self.assertEqual(node["href"], f"/reference?id={reference_id}")

    def test_local_community_labels_are_human_readable_title_case(self):
        self.assertEqual(normalize_community_label("decoding algorithms"), "Decoding Algorithms")
        self.assertEqual(normalize_community_label("SU(2) herald decoding"), "SU(2) Herald Decoding")

    def test_fallback_community_labels_are_distinct_and_descriptive(self):
        labels = [community["label"] for community in self.graph["communities"]]
        self.assertEqual(len(labels), len({label.casefold() for label in labels}))
        self.assertIn("Decoder Architectures", labels)
        self.assertIn("Non-Abelian Fault-Tolerant Decoding", labels)

    def test_homepage_uses_only_active_labs_and_a_canonical_stage_vocabulary(self):
        self.assertEqual(LAB_STAGES, ("design", "active", "blocked", "complete"))
        payload = project_payload()
        self.assertNotIn("current_lab", payload)
        self.assertTrue(all(lab["stage"] == "active" for lab in payload["active_labs"]))

    def test_lab_index_keeps_compatibility_status_fields(self):
        payload = project_payload()
        labs = {lab["id"]: lab for lab in payload["active_labs"]}
        self.assertEqual(
            set(labs),
            {
                "lab-002-herald-belief-matching",
                "lab-003-herald-threshold-phase-diagram",
                "lab-004-d4-intrinsic-heralded-decoding",
                "lab-005-spacetime-jit-anyonic-decoding",
            },
        )
        for lab in labs.values():
            self.assertTrue(lab["summary"])
            self.assertTrue(lab["current_focus"])
            self.assertTrue(lab["next_action"])

    def test_raw_lab_index_is_complete_for_older_dashboard_instances(self):
        index = json.loads((LABS / "labs.json").read_text(encoding="utf-8"))["labs"]
        for lab in index:
            self.assertIn(lab["stage"], LAB_STAGES)
            self.assertTrue(lab["summary"])
            self.assertTrue(lab["current_focus"])
            self.assertTrue(lab["next_action"])
            self.assertTrue(lab["updated"])

    def test_lab_lineage_is_lab_owned_and_has_only_known_parents(self):
        catalog = lab_catalog()
        known_ids = {lab["id"] for lab in catalog}
        lineage = {lab["id"]: lab["parents"] for lab in catalog}
        self.assertEqual(lineage["lab-001-string-herald-visualization"], [])
        self.assertEqual(lineage["lab-002-herald-belief-matching"], ["lab-001-string-herald-visualization"])
        self.assertEqual(
            {lab["id"]: lab["created"] for lab in catalog},
            {
                "lab-001-string-herald-visualization": "2026-08-26",
                "lab-002-herald-belief-matching": "2026-08-26",
                "lab-003-herald-threshold-phase-diagram": "2026-08-27",
                "lab-004-d4-intrinsic-heralded-decoding": "2026-08-28",
                "lab-005-spacetime-jit-anyonic-decoding": "2026-08-28",
            },
        )
        self.assertEqual(
            lineage["lab-005-spacetime-jit-anyonic-decoding"],
            ["lab-002-herald-belief-matching", "lab-004-d4-intrinsic-heralded-decoding"],
        )
        for lab in catalog:
            self.assertTrue(set(lab["parents"]).issubset(known_ids))
            self.assertNotIn(lab["id"], lab["parents"])
            self.assertRegex(lab["created"], re.compile(r"^\d{4}-\d{2}-\d{2}$"))

    def test_wiki_index_is_a_live_control_plane_not_a_reference_list(self):
        with patch("dashboard.server.wiki_lint_status", return_value={"state": "healthy", "errors": 0, "warnings": 0}):
            index = wiki_index_payload()
        self.assertGreater(index["statistics"]["pages"], 0)
        self.assertIn("decoding_methods", index["sections"])
        self.assertIn("references/lieart", [page["id"] for page in index["sections"]["references"]])
        self.assertIn(
            "references/jing2025-intrinsic-heralding",
            [page["id"] for page in index["sections"]["references"]],
        )
        self.assertIn("paper", index["sources"]["by_kind"])

    def test_reference_pages_have_one_shared_page_type(self):
        pages = {page["id"]: page for page in wiki_pages()}
        self.assertEqual(pages["references/lieart"]["page_type"], "reference")


if __name__ == "__main__":
    unittest.main()
