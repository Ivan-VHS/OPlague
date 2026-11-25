"""Tests for portable OPlague report exports."""
import csv
import io
import json
import unittest

from tools.report_export import (
    anonymize_report,
    render_report,
    render_report_csv,
    render_report_json,
    render_report_markdown,
)


class ReportExportTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "schema": "oplage.inspection-bundle.v1",
            "packages": [{
                "file_name": "sample.zip",
                "sha256": "a" * 64,
                "pnp_id": "USB\\VID_1234&PID_5678",
                "hardware_ids": ["PCI\\VEN_1234&DEV_5678"],
                "path": "C:/Users/Alice/Downloads/sample.zip",
                "inf_metadata": {"provider": "Example"},
            }],
            "totals": {"packages": 1, "reported_bytes": 512},
        }

    def test_json_round_trip_is_stable(self):
        rendered = render_report_json(self.report)
        self.assertEqual(rendered, render_report_json(self.report))
        self.assertEqual(json.loads(rendered), self.report)

    def test_csv_contains_one_row_per_package(self):
        rendered = render_report_csv(self.report)
        rows = list(csv.DictReader(io.StringIO(rendered)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["file_name"], "sample.zip")
        self.assertEqual(rows[0]["inf_metadata"], '{"provider": "Example"}')

    def test_markdown_explains_evidence_limits(self):
        rendered = render_report_markdown(self.report)
        self.assertIn("not a driver-installation recommendation", rendered)
        self.assertIn("sample.zip", rendered)
        self.assertIn("publisher trust", rendered)

    def test_anonymization_is_stable_and_does_not_mutate_input(self):
        private = anonymize_report(self.report)
        self.assertEqual(private["packages"][0]["pnp_id"],
                         anonymize_report(self.report)["packages"][0]["pnp_id"])
        self.assertNotIn("VID_1234", private["packages"][0]["pnp_id"])
        self.assertNotIn("VEN_1234", private["packages"][0]["hardware_ids"][0])
        self.assertEqual(private["packages"][0]["path"], "<redacted>")
        self.assertEqual(self.report["packages"][0]["pnp_id"], "USB\\VID_1234&PID_5678")
        self.assertEqual(private["packages"][0]["sha256"], self.report["packages"][0]["sha256"])

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(ValueError):
            render_report(self.report, "pdf")


if __name__ == "__main__":
    unittest.main()
