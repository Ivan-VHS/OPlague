from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.federation import build_device_snapshot
from tools.snapshot_history import _write_report_atomically, analyze_snapshot_history


class SnapshotHistoryTests(unittest.TestCase):
    def _snapshot(self, captured: str, problem: bool = False):
        devices = [{
            "instance_id": "DEMO\\DEVICE",
            "friendly_name": "Demo device",
            "class": "System",
            "status": "Error" if problem else "OK",
            "problem": 1 if problem else None,
        }]
        return build_device_snapshot(
            devices,
            captured_utc=captured,
            identity_key=b"x" * 32,
        )

    def test_stable_chronological_history(self) -> None:
        snapshots = [
            self._snapshot("2026-11-21T00:00:00Z"),
            self._snapshot("2026-11-21T00:00:10Z"),
            self._snapshot("2026-11-21T00:00:20Z"),
        ]
        report = analyze_snapshot_history(snapshots, expected_interval_seconds=10.0)
        self.assertEqual(report["schema"], "oplage.snapshot-history-analysis.v1")
        self.assertEqual(report["snapshot_count"], 3)
        self.assertEqual(report["capture_cadence"]["cadence_score"], 100.0)
        self.assertEqual(report["overall_descriptive_score"], 100.0)

    def test_metric_change_is_reported_not_interpreted_as_verdict(self) -> None:
        snapshots = [
            self._snapshot("2026-11-21T00:00:00Z"),
            self._snapshot("2026-11-21T00:00:10Z", problem=True),
            self._snapshot("2026-11-21T00:00:20Z", problem=True),
        ]
        report = analyze_snapshot_history(snapshots, expected_interval_seconds=10.0)
        self.assertLess(report["metric_stability"]["device_ok_ratio"]["stability_score"], 100.0)
        self.assertIn("do not establish", report["semantics"])

    def test_rejects_bad_order_and_tampered_snapshot(self) -> None:
        snapshots = [
            self._snapshot("2026-11-21T00:00:00Z"),
            self._snapshot("2026-11-21T00:00:10Z"),
            self._snapshot("2026-11-21T00:00:20Z"),
        ]
        with self.assertRaisesRegex(ValueError, "increasing"):
            analyze_snapshot_history([snapshots[1], snapshots[0], snapshots[2]])
        snapshots[1]["metrics"]["device_ok_ratio"] = 0.25
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            analyze_snapshot_history(snapshots)

    def test_rejects_non_utc_capture_timestamps(self) -> None:
        with self.assertRaisesRegex(ValueError, "normalized to UTC"):
            analyze_snapshot_history([
                self._snapshot("2026-11-21T00:00:00Z"),
                self._snapshot("2026-11-21T02:00:10+02:00"),
                self._snapshot("2026-11-21T00:00:20Z"),
            ])

    def test_rejects_integer_inputs_outside_float64_range(self) -> None:
        snapshots = [
            self._snapshot("2026-11-21T00:00:00Z"),
            self._snapshot("2026-11-21T00:00:10Z"),
            self._snapshot("2026-11-21T00:00:20Z"),
        ]
        with self.assertRaisesRegex(ValueError, "float64 range"):
            analyze_snapshot_history(snapshots, expected_interval_seconds=10 ** 1000)

    def test_report_write_is_atomic_and_rejects_symlink_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "report.json"
            target.write_text("old", encoding="utf-8")
            _write_report_atomically(target, "new\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")
            source = root / "source.json"
            source.write_text("keep", encoding="utf-8")
            link = root / "linked.json"
            try:
                link.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable on this platform")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                _write_report_atomically(link, "overwrite")
            self.assertEqual(source.read_text(encoding="utf-8"), "keep")

    def test_requires_minimum_history_and_valid_tolerance(self) -> None:
        one = self._snapshot("2026-11-21T00:00:00Z")
        with self.assertRaises(ValueError):
            analyze_snapshot_history([one, one])
        snapshots = [
            self._snapshot("2026-11-21T00:00:00Z"),
            self._snapshot("2026-11-21T00:00:10Z"),
            self._snapshot("2026-11-21T00:00:20Z"),
        ]
        with self.assertRaises(ValueError):
            analyze_snapshot_history(snapshots, tolerance_ratio=0.0)


if __name__ == "__main__":
    unittest.main()
