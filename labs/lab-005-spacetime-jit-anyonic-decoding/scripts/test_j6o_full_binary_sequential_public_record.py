"""Public/private and joint-law checks for the fixed full-binary fixture."""

from collections import defaultdict
import unittest

from run_j6o_full_binary_sequential_public_record import run


class FullBinarySequentialRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_three_actions_and_normalized_conditioned_laws(self) -> None:
        rows = self.result["public_law_rows"]
        self.assertEqual(len(rows), 10)
        self.assertEqual({row["action"] for row in rows},
                         {"defer", "partial", "matched"})
        totals = defaultdict(float)
        for row in rows:
            if row["action"] != "defer":
                totals[(row["action"], row["first_public"]["charge"][1])] += \
                    row["second_conditional_probability"]
        self.assertEqual(set(totals.values()), {1.0})

    def test_no_private_fields_inside_public_records(self) -> None:
        for row in self.result["public_law_rows"]:
            for key in ("first_public", "second_public"):
                record = row[key]
                if record is None:
                    self.assertEqual(row["action"], "defer")
                    continue
                self.assertEqual(set(record), {"flux", "charge", "vacuum"})
                self.assertTrue(all(len(bits) == 24 for bits in record.values()))
                self.assertTrue(all(bit in (0, 1) for bits in record.values()
                                    for bit in bits))
                self.assertEqual(record["vacuum"],
                                 [1 - bit for bit in record["charge"]])
                self.assertTrue(all(not (flux and charge) for flux, charge
                                    in zip(record["flux"], record["charge"])))

    def test_source_limits_and_action_binding(self) -> None:
        rows = self.result["public_law_rows"]
        for row in rows:
            self.assertEqual([i for i, bit in enumerate(row["first_public"]["flux"])
                              if bit], [0, 2])
            second = row["second_public"]
            if row["action"] == "defer":
                self.assertIsNone(second)
            elif row["action"] == "partial":
                self.assertEqual(row["public_action_red_edge_ids"], [0])
                self.assertEqual([i for i, bit in enumerate(second["flux"]) if bit], [1, 2])
                self.assertEqual(sum(second["charge"]), second["charge"][0])
            else:
                self.assertEqual(row["public_action_red_edge_ids"], [0, 4])
                self.assertEqual(second["flux"], [0] * 24)
                self.assertEqual(second["charge"][0], second["charge"][2])
                self.assertIn(sum(second["charge"]), (0, 2))
        self.assertEqual(self.result["stochastic_histories"], 0)
        self.assertEqual(self.result["schedule_arm_evaluations"], 0)
        self.assertEqual(self.result["bootstrap_replicates"], 0)


if __name__ == "__main__":
    unittest.main()
