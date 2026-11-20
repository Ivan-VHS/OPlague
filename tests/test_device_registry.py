from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tools.device_registry import (RegistryError, append_snapshot, create_snapshot, load_registry,
                                   new_registry, save_registry, snapshot_diff, validate_registry)

class DeviceRegistryTests(unittest.TestCase):
    def test_round_trip_and_schema_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            registry = new_registry()
            registry["devices"] = [{"instance_id": "PCI\\A", "name": "Adapter"}]
            save_registry(path, registry)
            loaded = load_registry(path)
            self.assertEqual(loaded["schema_version"], 1)
            self.assertEqual(loaded["devices"][0]["name"], "Adapter")

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema":"oplage.device-registry","schema":"bad"}', encoding="utf-8")
            with self.assertRaisesRegex(RegistryError, "duplicate JSON key"):
                load_registry(path)

    def test_duplicate_devices_and_unsupported_versions_are_rejected(self):
        value = new_registry()
        value["devices"] = [{"instance_id": "PCI\\A"}, {"instance_id": "pci\\a"}]
        with self.assertRaisesRegex(RegistryError, "duplicate"):
            validate_registry(value)
        value = new_registry(); value["schema_version"] = 2
        with self.assertRaisesRegex(RegistryError, "unsupported"):
            validate_registry(value)

    def test_snapshot_identity_is_deterministic_and_append_increments_revision(self):
        snapshot = create_snapshot([{"instance_id": "PCI\\A"}], label="baseline", captured_at="2026-11-20T00:00:00Z")
        again = create_snapshot([{"instance_id": "PCI\\A"}], label="baseline", captured_at="2026-11-20T00:00:00Z")
        self.assertEqual(snapshot["snapshot_id"], again["snapshot_id"])
        registry = append_snapshot(new_registry(), snapshot)
        self.assertEqual(registry["revision"], 1)
        self.assertEqual(registry["devices"][0]["instance_id"], "PCI\\A")
        with self.assertRaisesRegex(RegistryError, "already exists"):
            append_snapshot(registry, snapshot)

    def test_diff_reports_added_removed_changed_and_metric_deltas(self):
        before = create_snapshot([{"instance_id": "PCI\\A", "status": "OK"}, {"instance_id": "USB\\B"}],
                                 [{"sha256": "a" * 64, "version": "1"}], {"health": 0.8}, captured_at="before")
        after = create_snapshot([{"instance_id": "PCI\\A", "status": "Error"}, {"instance_id": "PCI\\C"}],
                                [{"sha256": "a" * 64, "version": "2"}, {"sha256": "b" * 64}],
                                {"health": 0.5}, captured_at="after")
        result = snapshot_diff(before, after)
        self.assertEqual(result["totals"]["devices_added"], 1)
        self.assertEqual(result["totals"]["devices_removed"], 1)
        self.assertEqual(result["totals"]["devices_changed"], 1)
        self.assertEqual(result["totals"]["packages_changed"], 1)
        self.assertAlmostEqual(result["metric_deltas"]["health"]["delta"], -0.3)

    def test_symlink_registry_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "real.json"; target.write_text(json.dumps(new_registry()))
            link = Path(directory) / "link.json"
            try: link.symlink_to(target)
            except (OSError, NotImplementedError): self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(RegistryError, "symbolic link"):
                load_registry(link)

if __name__ == "__main__":
    unittest.main()
