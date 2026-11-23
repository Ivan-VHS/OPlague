from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import game_optimizer as gaming


class GameOptimizerTests(unittest.TestCase):
    def test_normalizes_complete_pci_identity_without_dropping_subsystem(self):
        value = r"pci/ven_10de&dev_2c05&subsys_12345678&rev_a1"
        self.assertEqual(
            gaming.normalize_hardware_id(value),
            r"PCI\VEN_10DE&DEV_2C05&SUBSYS_12345678&REV_A1",
        )

    def test_rejects_unsafe_hardware_ids(self):
        self.assertEqual(gaming.normalize_hardware_id("PCI\\VEN_10DE"), "PCI\\VEN_10DE")
        self.assertEqual(gaming.normalize_hardware_id("PCI\\VEN_10DE*"), "")
        self.assertEqual(gaming.normalize_hardware_id("../escape"), "")
        self.assertEqual(gaming.normalize_hardware_id(""), "")

    def test_preserves_full_pnp_instance_suffix(self):
        device_id = r"PCI\\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03\\4&2A3B4C5D&0&00E0"
        self.assertEqual(gaming.normalize_hardware_id(device_id), device_id.upper())
        identity = gaming.hardware_identity(device_id)
        self.assertEqual(identity["vendor_id"], "8086")
        self.assertEqual(identity["device_code"], "15F3")

    def test_extracts_pci_and_usb_fields(self):
        pci = gaming.hardware_identity(r"PCI\VEN_10DE&DEV_2C05&SUBSYS_12345678&REV_A1")
        self.assertEqual(pci["vendor_id"], "10DE")
        self.assertEqual(pci["device_code"], "2C05")
        self.assertEqual(pci["subsystem_id"], "12345678")
        self.assertEqual(pci["revision"], "A1")
        usb = gaming.hardware_identity(r"USB\VID_046D&PID_C548&REV_1200")
        self.assertEqual(usb["usb_vendor_id"], "046D")
        self.assertEqual(usb["usb_product_id"], "C548")

    def test_fingerprint_is_stable_and_driver_sensitive(self):
        first = [{"pnp_id": r"PCI\VEN_1234&DEV_ABCD", "driver_version": "1.0", "inf_name": "oem1.inf"}]
        second = [{"pnp_id": r"pci\ven_1234&dev_abcd", "driver_version": "1.0", "inf_name": "oem1.inf"}]
        changed = [{"pnp_id": r"PCI\VEN_1234&DEV_ABCD", "driver_version": "2.0", "inf_name": "oem2.inf"}]
        self.assertEqual(gaming.hardware_fingerprint(first), gaming.hardware_fingerprint(second))
        self.assertNotEqual(gaming.hardware_fingerprint(first), gaming.hardware_fingerprint(changed))

    def test_snapshot_is_written_atomically_and_contains_identity(self):
        devices = [{"name": "GPU", "pnp_id": r"PCI\VEN_10DE&DEV_2C05", "driver_version": "1.2"}]
        with tempfile.TemporaryDirectory() as folder:
            result = gaming.create_snapshot(devices=devices, power_scheme=None, directory=Path(folder))
            stored = json.loads(Path(result["snapshot_path"]).read_text(encoding="utf-8"))
        self.assertEqual(stored["schema"], gaming.SCHEMA_VERSION)
        self.assertEqual(stored["devices"][0]["driver_version"], "1.2")
        self.assertEqual(len(stored["hardware_fingerprint"]), 64)

    def test_power_scheme_parser_uses_guid_and_keeps_description(self):
        class Completed:
            returncode = 0
            stdout = "Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)\n"
            stderr = ""
        with patch.object(gaming.os, "name", "nt"):
            result = gaming.active_power_scheme(lambda *args, **kwargs: Completed())
        self.assertEqual(result["guid"], "381b4222-f694-41f0-9685-ff5bb260df2e")
        self.assertIn("Balanced", result["description"])

    def test_power_scheme_rejects_alias_before_running_command(self):
        called = []
        with patch.object(gaming.os, "name", "nt"):
            with self.assertRaises(ValueError):
                gaming.set_active_power_scheme("SCHEME_MIN", lambda *args, **kwargs: called.append(args))
        self.assertEqual(called, [])

    def test_restore_does_not_override_a_power_plan_changed_elsewhere(self):
        previous = "381b4222-f694-41f0-9685-ff5bb260df2e"
        applied = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        external = "a1841308-3541-4fab-bc81-f71556f20b4a"
        with tempfile.TemporaryDirectory() as folder:
            session_path = Path(folder) / "active-session.json"
            session_path.write_text(json.dumps({
                "schema": gaming.SCHEMA_VERSION,
                "status": "active",
                "previous_power_scheme": {"guid": previous},
                "applied_power_scheme_guid": applied,
            }), encoding="utf-8")
            commands = []
            class Completed:
                returncode = 0
                stdout = f"Power Scheme GUID: {external} (User selected)\\n"
                stderr = ""
            def runner(command, **kwargs):
                commands.append(command)
                return Completed()
            with patch.object(gaming.os, "name", "nt"):
                result = gaming.restore_game_session(directory=Path(folder), runner=runner)
        self.assertFalse(result["restored"])
        self.assertEqual(result["reason"], "external_power_plan_change")
        self.assertFalse(any("/setactive" in command for command in commands))

    def test_frametime_csv_reports_average_and_low_percentiles(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "frames.csv"
            source.write_text(
                "Application,MsBetweenPresents\n" + "\n".join(
                    f"game.exe,{value}" for value in [10.0] * 999 + [50.0]
                ),
                encoding="utf-8",
            )
            result = gaming.summarize_frametime_csv(source)
        self.assertEqual(result["sample_count"], 1000)
        self.assertGreater(result["average_fps"], 90)
        self.assertAlmostEqual(result["one_percent_low_fps"], 71.43, places=2)
        self.assertEqual(result["point_one_percent_low_fps"], 20.0)

    def test_0_1_percent_low_is_unavailable_for_short_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "short.csv"
            source.write_text(
                "MsBetweenPresents\n" + "\n".join(["10.0"] * 99 + ["50.0"]),
                encoding="utf-8",
            )
            result = gaming.summarize_frametime_csv(source)
        self.assertIsNone(result["point_one_percent_low_fps"])

    def test_frametime_csv_rejects_unknown_header(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.csv"
            source.write_text("FPS,CPU\n120,40\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                gaming.summarize_frametime_csv(source)

    def test_regression_comparison_uses_low_percentiles_and_p99(self):
        baseline = {
            "one_percent_low_fps": 100.0,
            "point_one_percent_low_fps": 80.0,
            "p99_frametime_ms": 20.0,
        }
        candidate = {
            "one_percent_low_fps": 92.0,
            "point_one_percent_low_fps": 70.0,
            "p99_frametime_ms": 22.0,
        }
        result = gaming.compare_benchmarks(baseline, candidate)
        self.assertTrue(result["regression_detected"])
        self.assertIn("1% low dropped beyond threshold", result["reasons"])
        self.assertFalse(result["automatic_rollback"])

    def test_profile_cache_requires_manual_validation_and_exact_tuple(self):
        devices = [{"pnp_id": r"PCI\VEN_10DE&DEV_2C05", "driver_version": "1.0"}]
        fingerprint = gaming.hardware_fingerprint(devices)
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / "profiles.json"
            with self.assertRaises(ValueError):
                gaming.save_game_profile(
                    game_id="sample.exe", game_name="Sample", hardware_hash=fingerprint,
                    driver_version="1.0", settings={"mode": "competitive"}, path=cache,
                )
            saved = gaming.save_game_profile(
                game_id="sample.exe", game_name="Sample", hardware_hash=fingerprint,
                driver_version="1.0", settings={"mode": "competitive"}, validated=True, path=cache,
            )
            found = gaming.find_game_profile(
                game_id="sample.exe", hardware_hash=fingerprint,
                driver_version="1.0", path=cache,
            )
            missed = gaming.find_game_profile(
                game_id="sample.exe", hardware_hash=fingerprint,
                driver_version="2.0", path=cache,
            )
        self.assertEqual(saved["profile"]["validation"], "operator_confirmed")
        self.assertIsNotNone(found)
        self.assertIsNone(missed)


if __name__ == "__main__":
    unittest.main()
