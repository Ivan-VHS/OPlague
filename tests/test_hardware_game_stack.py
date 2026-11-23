from __future__ import annotations

import unittest

from tools.hardware_game_stack import SCHEMA, SUBSYSTEMS, analyze_benchmark, build_report, redact_report


class HardwareGameStackTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "schema": "oplague.hardware-snapshot.v1",
            "collected_at": "2026-11-23T10:00:00+00:00",
            "host": {"manufacturer": "Example OEM", "model": "Workstation", "os_name": "Windows 11",
                     "version": "10.0.26200", "build_number": "26200", "architecture": "AMD64"},
            "firmware": {"vendor": "Example BIOS", "version": "1.2.3", "release_date": "2026-05-01",
                         "secure_boot": True, "tpm_present": True},
            "cpu": {"name": "Example 16-Core CPU", "cores": 16, "logical_processors": 32,
                    "max_clock_mhz": 5200, "load_percent": 35},
            "memory": {"total_bytes": 32 * 1024**3, "free_bytes": 18 * 1024**3,
                       "modules": [{"capacity_bytes": 16 * 1024**3, "speed_mhz": 6000},
                                   {"capacity_bytes": 16 * 1024**3, "speed_mhz": 6000}]},
            "gpus": [{"name": "NVIDIA GeForce RTX Example", "driver_version": "600.1",
                      "driver_date": "2026-10-01", "status": "OK",
                      "horizontal_resolution": 2560, "vertical_resolution": 1440,
                      "refresh_rate_hz": 165}],
            "devices": [
                {"name": "Example GPU", "class": "Display", "status": "OK",
                 "pnp_id": "PCI\\VEN_10DE&DEV_1234\\INSTANCE_PRIVATE",
                 "hardware_ids": ["PCI\\VEN_10DE&DEV_1234&SUBSYS_00000001"],
                 "compatible_ids": ["PCI\\VEN_10DE&DEV_1234"], "problem_code": 0},
                {"name": "Faulty USB Device", "class": "USB", "status": "Error",
                 "pnp_id": "USB\\VID_1234&PID_0001\\SERIAL_PRIVATE",
                 "hardware_ids": ["USB\\VID_1234&PID_0001"], "compatible_ids": [],
                 "problem_code": 43},
            ],
            "drivers": [
                {"device_name": "Example GPU", "provider": "NVIDIA", "version": "600.1",
                 "inf_name": "oem1.inf", "is_signed": True},
                {"device_name": "Example USB Device", "provider": "Example", "version": "1.0",
                 "inf_name": "oem2.inf", "is_signed": False},
            ],
            "thermal_zones": [{"name": "ACPI Thermal Zone", "current_temperature": 3632}],
            "power": {"active_scheme": "Balanced"},
            "battery": {"present": False, "status": "", "charge_percent": None},
            "processes": [{"name": "Cyberpunk2077", "pid": 4242, "cpu_seconds": 12.5,
                           "working_set_bytes": 2_000_000_000}],
            "driver_updates": [], "driver_update_discovery_status": "not_requested",
        }

    def test_report_has_all_fifteen_subsystems_and_no_mutations(self):
        report = build_report(self.snapshot)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["subsystem_count"], 15)
        self.assertEqual(set(report["subsystems"]), set(SUBSYSTEMS))
        self.assertFalse(any(report["safety"].values()))

    def test_problem_codes_and_signature_metadata_are_not_trust_verdicts(self):
        report = build_report(self.snapshot)
        self.assertEqual(report["subsystems"]["device_health"]["data"]["problem_device_count"], 1)
        signature = report["subsystems"]["signature_evidence"]["data"]
        self.assertEqual(signature["reported_signed"], 1)
        self.assertEqual(signature["reported_unsigned"], 1)
        self.assertEqual(signature["trust_verdict"], "not_performed")

    def test_compatibility_requires_an_exact_identifier(self):
        catalog = [{"driver_id": "gpu", "package_name": "GPU package",
                    "hardware_ids": ["PCI\\VEN_10DE&DEV_1234&SUBSYS_00000001"],
                    "architectures": ["amd64"]}]
        result = build_report(self.snapshot, driver_catalog=catalog)["subsystems"]["driver_compatibility"]["data"]
        self.assertEqual(result["exact_match_edges"], 1)
        self.assertTrue(result["manual_review_required"])

    def test_similar_but_not_equal_ids_do_not_match(self):
        catalog = [{"driver_id": "wrong", "hardware_ids": ["PCI\\VEN_10DE&DEV_1234&SUBSYS_00000002"]}]
        result = build_report(self.snapshot, driver_catalog=catalog)["subsystems"]["driver_compatibility"]["data"]
        self.assertEqual(result["exact_match_edges"], 0)

    def test_windows_update_candidates_enter_the_exact_match_graph(self):
        self.snapshot["driver_updates"] = [{"title": "Candidate", "update_id": "update-1",
                                            "hardware_ids": ["USB\\VID_1234&PID_0001"]}]
        report = build_report(self.snapshot)
        self.assertEqual(report["subsystems"]["windows_update_discovery"]["data"]["candidate_count"], 1)
        self.assertEqual(report["subsystems"]["driver_compatibility"]["data"]["exact_match_edges"], 1)

    def test_benchmark_reports_average_and_one_percent_low(self):
        result = analyze_benchmark({"game": "Test", "frame_times_ms": [10.0] * 99 + [40.0]})
        self.assertEqual(result["status"], "available")
        self.assertAlmostEqual(result["metrics"]["average_fps"], 97.09, places=1)
        self.assertLess(result["metrics"]["one_percent_low_fps"], result["metrics"]["average_fps"])

    def test_benchmark_rejects_invalid_or_empty_samples(self):
        with self.assertRaises(ValueError):
            analyze_benchmark({"frame_times_ms": [10.0, float("nan")]})
        with self.assertRaises(ValueError):
            analyze_benchmark({"fps_samples": []})

    def test_acpi_temperature_is_converted_to_celsius(self):
        self.snapshot["thermal_zones"] = [{"current_temperature": 3682}]
        zone = build_report(self.snapshot)["subsystems"]["thermal_watchdog"]["data"]["zones"][0]
        self.assertEqual(zone["state"], "hot")

    def test_privacy_redaction_removes_device_instance_and_matched_ids(self):
        report = build_report(self.snapshot, driver_catalog=[{
            "driver_id": "gpu", "hardware_ids": ["PCI\\VEN_10DE&DEV_1234&SUBSYS_00000001"]
        }])
        redacted = redact_report(report)
        self.assertNotIn("INSTANCE_PRIVATE", str(redacted))
        self.assertNotIn("SERIAL_PRIVATE", str(redacted))
        self.assertNotIn("matched_ids", str(redacted))
        self.assertFalse(redacted["privacy"]["hardware_ids_included"])

    def test_low_memory_is_advisory_only(self):
        self.snapshot["memory"]["total_bytes"] = 8 * 1024**3
        planner = build_report(self.snapshot)["subsystems"]["game_performance_planner"]["data"]
        self.assertTrue(any(item["area"] == "memory" for item in planner["recommendations"]))
        self.assertEqual(planner["automatic_changes_applied"], 0)


if __name__ == "__main__":
    unittest.main()
