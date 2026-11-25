import unittest

from tools.atomic_quantum import (
    AtomicQuantumEvidenceError, compare_metric_records, known_function,
    load_catalogue, summarize_report, validate_report,
)

class AtomicQuantumEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "schema": "ivan-vhs.atomic-quantum-report.v1",
            "function_id": "telem_system_health_133",
            "quality": "simulated",
            "source_sha256": "a" * 64,
            "window_start_epoch": 100,
            "window_end_epoch": 200,
            "sample_count": 10,
            "metrics": {"coherence": {"value": 0.92, "unit": "ratio", "absolute_uncertainty": 0.01}},
        }

    def test_catalogue_is_133_unique_entries(self):
        rows = load_catalogue()["functions"]
        self.assertEqual(len(rows), 133)
        self.assertEqual(len({row["id"] for row in rows}), 133)
        self.assertTrue(known_function("atom_superpose_basis_01"))
        self.assertFalse(known_function("fake_quantum_operation"))

    def test_report_validation_and_summary(self):
        clean = validate_report(self.report)
        self.assertTrue(clean["read_only"])
        self.assertEqual(clean["evidence_class"], "simulated")
        summary = summarize_report(self.report)
        self.assertEqual(summary["metric_count"], 1)
        self.assertTrue(summary["advisory_only"])

    def test_comparison_requires_same_window_and_quality(self):
        other = dict(self.report)
        other["source_sha256"] = "b" * 64
        other["metrics"] = {"coherence": {"value": 0.90, "unit": "ratio", "absolute_uncertainty": 0.005}}
        result = compare_metric_records(self.report, other, "coherence")
        self.assertAlmostEqual(result["delta"], -0.02)
        self.assertTrue(result["uncertainty_envelopes_disjoint"])
        other["window_end_epoch"] = 201
        with self.assertRaises(AtomicQuantumEvidenceError):
            compare_metric_records(self.report, other, "coherence")

    def test_bad_provenance_and_unknown_id_rejected(self):
        bad = dict(self.report)
        bad["source_sha256"] = "not-a-digest"
        with self.assertRaises(AtomicQuantumEvidenceError):
            validate_report(bad)
        bad = dict(self.report)
        bad["function_id"] = "unknown"
        with self.assertRaises(AtomicQuantumEvidenceError):
            validate_report(bad)

    def test_observed_quality_cannot_skip_provenance(self):
        bad = dict(self.report)
        bad["quality"] = "observed"
        bad["source_sha256"] = "x" * 64
        with self.assertRaises(AtomicQuantumEvidenceError):
            validate_report(bad)

if __name__ == "__main__":
    unittest.main()
