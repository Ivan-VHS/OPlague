from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.federation import (
    SNAPSHOT_SCHEMA, InventoryError, build_device_snapshot,
    capture_pnp_devices, compare_device_snapshots, export_device_snapshot,
    load_identity_key, main,
)


def reseal_snapshot(snapshot: dict) -> dict:
    payload = dict(snapshot)
    payload.pop("snapshot_sha256", None)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    snapshot["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
    return snapshot


class FederationSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.devices = [
            {"InstanceId": "PCI\\VEN_1234&DEV_5678\\SERIAL-A", "FriendlyName": "Example GPU", "Class": "Display", "Status": "OK", "Problem": 0},
            {"InstanceId": "USB\\VID_1234&PID_5678\\SERIAL-B", "FriendlyName": "Example Device", "Class": "USB", "Status": "Error", "Problem": 28},
        ]

    def test_snapshot_is_versioned_normalized_and_read_only(self) -> None:
        snapshot = build_device_snapshot(self.devices, captured_utc="2026-11-20T00:00:00Z")
        self.assertEqual(snapshot["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(snapshot["source"]["mode"], "read_only")
        self.assertEqual(snapshot["summary"]["total_devices"], 2)
        self.assertEqual(snapshot["summary"]["ok_devices"], 1)
        self.assertEqual(snapshot["summary"]["problem_devices"], 1)
        self.assertAlmostEqual(snapshot["metrics"]["device_ok_ratio"], 0.5)
        self.assertAlmostEqual(snapshot["metrics"]["device_problem_free_ratio"], 0.5)
        self.assertNotIn("SERIAL-A", json.dumps(snapshot))
        self.assertEqual(len(snapshot["devices"][0]["identity_sha256"]), 64)

    def test_identity_ids_use_keyed_pseudonyms_with_export_scoped_defaults(self) -> None:
        first = build_device_snapshot(self.devices, identity_key=b"a" * 32)
        repeated = build_device_snapshot(self.devices, identity_key=b"a" * 32)
        other = build_device_snapshot(self.devices, identity_key=b"b" * 32)
        ephemeral_one = build_device_snapshot(self.devices)
        ephemeral_two = build_device_snapshot(self.devices)
        self.assertEqual(first["devices"][0]["identity_sha256"], repeated["devices"][0]["identity_sha256"])
        self.assertNotEqual(first["devices"][0]["identity_sha256"], other["devices"][0]["identity_sha256"])
        self.assertNotEqual(ephemeral_one["devices"][0]["identity_sha256"], ephemeral_two["devices"][0]["identity_sha256"])
        self.assertEqual(ephemeral_one["identity_protection"]["key_scope"], "snapshot_ephemeral")
        self.assertEqual(first["identity_protection"]["key_scope"], "caller_managed")
        self.assertNotIn("SERIAL-A", json.dumps(first))

    def test_identity_key_file_is_bounded_and_requires_32_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / "identity.key"
            key_path.write_bytes(b"x" * 32)
            self.assertEqual(load_identity_key(key_path), b"x" * 32)
            key_path.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
                load_identity_key(key_path)

    def test_snapshot_export_requires_explicit_confirmation(self) -> None:
        with self.assertRaisesRegex(PermissionError, "explicit user confirmation"):
            export_device_snapshot(self.devices, user_confirmed=False)
        self.assertEqual(
            export_device_snapshot(self.devices, user_confirmed=True)["schema"],
            SNAPSHOT_SCHEMA,
        )

    def test_cli_snapshot_requires_confirmation_before_device_scan(self) -> None:
        with patch("tools.federation.capture_pnp_devices") as capture:
            self.assertEqual(main(["snapshot"]), 1)
        capture.assert_not_called()

    def test_empty_inventory_does_not_claim_perfect_health(self) -> None:
        snapshot = build_device_snapshot([])
        self.assertEqual(snapshot["metrics"]["device_ok_ratio"], 0.0)
        self.assertEqual(snapshot["metrics"]["package_audit_coverage_ratio"], 0.0)

    def test_package_coverage_distinguishes_missing_evidence(self) -> None:
        snapshot = build_device_snapshot([], packages=[{"file_name": "bad.udrv", "valid": False}])
        self.assertEqual(snapshot["metrics"]["package_integrity_ratio"], 0.0)
        self.assertEqual(snapshot["metrics"]["package_audit_coverage_ratio"], 1.0)

    def test_duplicate_device_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate PnP identity"):
            build_device_snapshot([self.devices[0], self.devices[0]])

    def test_comparison_requires_same_snapshot_dimensions(self) -> None:
        reference = build_device_snapshot(self.devices)
        candidate = build_device_snapshot([self.devices[0]])
        result = compare_device_snapshots(reference, candidate)
        self.assertEqual(result["schema"], "oplage.device-audit.v1")
        self.assertIn("euclidean_distance", result["comparison"])
        mismatched = build_device_snapshot([self.devices[0]])
        mismatched["metrics"]["different"] = mismatched["metrics"].pop("device_ok_ratio")
        reseal_snapshot(mismatched)
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            compare_device_snapshots(reference, mismatched)


    def test_snapshot_fingerprint_rejects_metric_tampering(self) -> None:
        snapshot = build_device_snapshot(self.devices)
        snapshot["metrics"]["device_ok_ratio"] = 0.25
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            compare_device_snapshots(snapshot, snapshot)

    def test_native_cross_check_is_opt_in(self) -> None:
        reference = build_device_snapshot(self.devices)
        candidate = build_device_snapshot([self.devices[0]])
        with patch("tools.pytyliki_ffi.euclidean_distance", return_value=0.25) as native:
            result = compare_device_snapshots(reference, candidate, "/trusted/libpytyliki.so")
        self.assertEqual(result["native_cross_check"]["backend"], "pytyliki-c-abi-v1")
        self.assertEqual(result["native_cross_check"]["euclidean_distance"], 0.25)
        native.assert_called_once()

    def test_pnp_provider_is_windows_only(self) -> None:
        with patch("tools.federation.os.name", "posix"):
            with self.assertRaises(InventoryError):
                capture_pnp_devices()

    def test_cli_compare_reads_and_writes_json(self) -> None:
        reference = build_device_snapshot(self.devices)
        candidate = build_device_snapshot([self.devices[0]])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left, right, output = root / "left.json", root / "right.json", root / "report.json"
            left.write_text(json.dumps(reference), encoding="utf-8")
            right.write_text(json.dumps(candidate), encoding="utf-8")
            self.assertEqual(main(["compare", "--reference", str(left), "--candidate", str(right), "--output", str(output)]), 0)
            saved = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(saved["mode"], "read_only")
        self.assertIn("comparison", saved)


if __name__ == "__main__":
    unittest.main()
