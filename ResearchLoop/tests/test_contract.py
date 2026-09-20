import unittest
import tempfile
from pathlib import Path

from ResearchLoop.core.audit import audit_retiming, frame_distortion
from ResearchLoop.core.contract import (atomic_write_json, clean_correct_asr,
                                        deterministic_subset, expand_integer_grid,
                                        sha256_file)
from ResearchLoop.core.projector import strict_project


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.clean = [
            {"event_id": "a", "t": 1, "line": "x+", "value": 1},
            {"event_id": "b", "t": 3, "line": "x+", "value": 1},
            {"event_id": "c", "t": 2, "line": "y-", "value": 1},
        ]

    def test_budget_metrics(self):
        adv = [dict(e) for e in self.clean]
        adv[0]["t"] = 0
        adv[1]["t"] = 4
        result = audit_retiming(self.clean, adv, time_bins=5, budget_type="B1", beta=2)
        self.assertTrue(result.passed)
        self.assertEqual((result.b_inf, result.b1, result.b0), (1, 2, 2))

    def test_detects_count_change(self):
        result = audit_retiming(self.clean, self.clean[:-1], time_bins=5, budget_type="B0", beta=2)
        self.assertFalse(result.passed)
        self.assertFalse(result.count_preserved)

    def test_detects_capacity_violation(self):
        adv = [dict(e) for e in self.clean]
        adv[0]["t"] = 3
        result = audit_retiming(self.clean, adv, time_bins=5, budget_type="B0", beta=1)
        self.assertFalse(result.capacity1_valid)

    def test_projector_preserves_contract(self):
        candidates = [
            {"event_id": "a", "target_t": 0, "probability": 0.9},
            {"event_id": "b", "target_t": 2, "probability": 0.8},
            {"event_id": "c", "target_t": 1, "probability": 0.7},
        ]
        adv = strict_project(self.clean, candidates, time_bins=5, budget_type="B0", beta=2)
        result = audit_retiming(self.clean, adv, time_bins=5, budget_type="B0", beta=2)
        self.assertTrue(result.passed)

    def test_frame_norms(self):
        d = frame_distortion([0, 1, 0], [1, 0, 0])
        self.assertEqual(d["frame_l0"], 2)
        self.assertEqual(d["frame_l1"], 2)

    def test_all_budget_projectors_are_independently_audited(self):
        candidates = [
            {"event_id": "a", "target_t": 0, "probability": 0.9},
            {"event_id": "b", "target_t": 4, "probability": 0.8},
            {"event_id": "c", "target_t": 1, "probability": 0.7},
        ]
        for budget_type, beta in (("B_inf", 1), ("B1", 2), ("B0", 2)):
            with self.subTest(budget_type=budget_type):
                adv = strict_project(self.clean, candidates, time_bins=5,
                                     budget_type=budget_type, beta=beta)
                self.assertTrue(audit_retiming(self.clean, adv, time_bins=5,
                                               budget_type=budget_type, beta=beta).passed)

    def test_line_value_and_timeline_tampering_are_rejected(self):
        for field, value in (("line", "other"), ("value", 2), ("t", 5)):
            with self.subTest(field=field):
                adv = [dict(e) for e in self.clean]
                adv[0][field] = value
                self.assertFalse(audit_retiming(self.clean, adv, time_bins=5,
                                                budget_type="B0", beta=3).passed)

    def test_integer_counts_expand_to_unit_packets(self):
        packets = expand_integer_grid([[0, 2], [1, 0]])
        self.assertEqual(len(packets), 3)
        self.assertEqual({p["value"] for p in packets}, {1})
        self.assertEqual(len({p["event_id"] for p in packets}), 3)
        result = audit_retiming(packets, packets, time_bins=2, budget_type="B0", beta=0)
        self.assertFalse(result.capacity1_valid)

    def test_asr_uses_only_clean_correct_denominator(self):
        result = clean_correct_asr([
            {"clean_correct": True, "attack_success": True},
            {"clean_correct": True, "attack_success": False},
            {"clean_correct": False, "attack_success": True},
        ])
        self.assertEqual(result, {"clean_correct_count": 2, "attack_success_count": 1, "asr": 50.0})

    def test_subset_selection_is_deterministic_and_order_independent(self):
        first = deterministic_subset(range(20), 5, 42)
        second = deterministic_subset(reversed(range(20)), 5, 42)
        self.assertEqual(first, second)
        self.assertNotEqual(first, deterministic_subset(range(20), 5, 123))

    def test_atomic_manifest_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            digest = atomic_write_json(path, {"run_id": "test", "complete": True})
            self.assertEqual(digest, sha256_file(path))
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
