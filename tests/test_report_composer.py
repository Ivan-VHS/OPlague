from __future__ import annotations

import unittest

from tools.report_composer import compose_inspection_reports


class InspectionReportComposerTests(unittest.TestCase):
    def test_composes_inf_and_zip_reports_with_totals(self) -> None:
        reports = [
            {
                "file_name": "network.inf",
                "format": "INF",
                "size_bytes": 120,
                "sha256": "a" * 64,
                "inf_metadata": {"class": "Net", "provider": "Vendor"},
            },
            {
                "file_name": "driver.zip",
                "format": "ZIP",
                "size_bytes": 800,
                "sha256": "b" * 64,
                "entry_count": 3,
                "expanded_size_bytes": 1500,
                "inf_files": [{"file": "display.inf", "metadata": {"class": "Display"}}],
                "catalog_files": ["display.cat"],
            },
        ]
        bundle = compose_inspection_reports(reports)
        self.assertEqual(bundle["schema"], "oplage.inspection-bundle.v1")
        self.assertEqual([item["file_name"] for item in bundle["packages"]],
                         ["network.inf", "driver.zip"])
        self.assertEqual(bundle["totals"], {
            "packages": 2,
            "reported_bytes": 920,
            "archive_entries": 3,
            "expanded_bytes": 1500,
            "inf_files": 2,
            "catalog_files": 1,
        })
        self.assertEqual(len(bundle["bundle_sha256"]), 64)
        self.assertEqual(reports[0]["inf_metadata"]["class"], "Net")

    def test_digest_is_deterministic_and_order_sensitive(self) -> None:
        first = {"file_name": "a.inf", "format": "INF", "size_bytes": 1, "sha256": "1" * 64}
        second = {"file_name": "b.inf", "format": "INF", "size_bytes": 2, "sha256": "2" * 64}
        one = compose_inspection_reports([first, second])
        again = compose_inspection_reports([first, second])
        reversed_bundle = compose_inspection_reports([second, first])
        self.assertEqual(one["bundle_sha256"], again["bundle_sha256"])
        self.assertNotEqual(one["bundle_sha256"], reversed_bundle["bundle_sha256"])

    def test_rejects_empty_input_and_invalid_shapes(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            compose_inspection_reports([])
        with self.assertRaises(TypeError):
            compose_inspection_reports([None])  # type: ignore[list-item]
        with self.assertRaisesRegex(ValueError, "format"):
            compose_inspection_reports([{
                "file_name": "bad.bin", "format": "BIN",
                "size_bytes": 1, "sha256": "a" * 64,
            }])

    def test_rejects_invalid_or_duplicate_digests(self) -> None:
        valid = {"file_name": "a.inf", "format": "INF", "size_bytes": 1, "sha256": "a" * 64}
        with self.assertRaisesRegex(ValueError, "invalid SHA-256"):
            compose_inspection_reports([{**valid, "sha256": "not-a-digest"}])
        with self.assertRaisesRegex(ValueError, "duplicate package digest"):
            compose_inspection_reports([valid, {**valid, "file_name": "copy.inf"}])

    def test_rejects_negative_or_excessive_counts(self) -> None:
        valid = {"file_name": "a.inf", "format": "INF", "size_bytes": -1, "sha256": "a" * 64}
        with self.assertRaisesRegex(ValueError, "size_bytes"):
            compose_inspection_reports([valid])
        archive = {
            "file_name": "a.zip", "format": "ZIP", "size_bytes": 1,
            "sha256": "b" * 64, "entry_count": 10001,
        }
        with self.assertRaisesRegex(ValueError, "entry_count"):
            compose_inspection_reports([archive])

    def test_rejects_malformed_inf_metadata(self) -> None:
        report = {
            "file_name": "a.inf", "format": "INF", "size_bytes": 1,
            "sha256": "a" * 64, "inf_metadata": {"class": 123},
        }
        with self.assertRaises(TypeError):
            compose_inspection_reports([report])


if __name__ == "__main__":
    unittest.main()
