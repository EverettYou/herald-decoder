import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_slope_flow_gray_frontier.py")
SPEC = importlib.util.spec_from_file_location("gray_frontier_audit", SCRIPT)
gray_frontier_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gray_frontier_audit)


class GrayFrontierAuditTests(unittest.TestCase):
    def test_completed_registered_matrix(self):
        result = gray_frontier_audit.audit(gray_frontier_audit.DEFAULT_MANIFEST)
        self.assertEqual(result["status"], "data_complete_not_analyzed")
        self.assertEqual(result["jobs_complete"], 10)
        self.assertEqual(result["raw_rows_observed"], 24000)
        self.assertEqual(result["syndrome_faithful_rows"], 24000)
        self.assertFalse(result["scientific_analysis_performed"])


if __name__ == "__main__":
    unittest.main()
