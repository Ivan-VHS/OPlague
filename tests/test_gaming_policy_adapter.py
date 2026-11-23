from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.gaming_policy_adapter import (
    GamingEvidenceError,
    PROVIDER_IDS,
    build_duckos_capability_evidence,
    to_duckos_capabilities,
)


class GamingPolicyAdapterTests(unittest.TestCase):
    def test_missing_providers_stay_unavailable(self):
        evidence = build_duckos_capability_evidence()
        self.assertEqual(set(evidence["providers"]), set(PROVIDER_IDS))
        self.assertEqual(evidence["provided_capabilities"], [])
        self.assertFalse(evidence["system_mutations_performed"])
        self.assertFalse(evidence["execution_performed"])

    def test_provider_catalog_matches_duckos_cpu_telemetry_contract(self):
        self.assertIn("cpu_telemetry", PROVIDER_IDS)
        evidence = build_duckos_capability_evidence()
        self.assertFalse(evidence["providers"]["cpu_telemetry"]["available"])

    def test_maps_only_real_supplied_evidence(self):
        gpu = {
            "provider": "nvidia-smi", "available": True,
            "gpus": [{"name": "GPU", "memory_used_mib": 100, "memory_total_mib": 1000}],
        }
        evidence = build_duckos_capability_evidence(
            devices=[],
            gpu_telemetry=gpu,
            reliability_events={"provider": "Windows System event log", "available": True},
            frame_time={"sample_count": 1000, "p99_frametime_ms": 18.2},
            active_power_plan={"guid": "381b4222-f694-41f0-9685-ff5bb260df2e"},
            snapshot={"snapshot_id": "snap-1", "hardware_fingerprint": "a" * 64},
        )
        caps = to_duckos_capabilities(evidence)
        for name in ("hardware_profile", "gpu_telemetry", "vram_metrics", "reliability_events",
                     "frame_time", "session_snapshot"):
            self.assertTrue(caps[name]["available"], name)
        self.assertFalse(caps["thermal_control"]["available"])
        self.assertFalse(caps["fan_control"]["available"])
        self.assertFalse(caps["scheduler"]["available"])

    def test_windows_power_plan_executor_is_advertised_as_consent_gated(self):
        with patch("tools.gaming_policy_adapter.platform.system", return_value="Windows"):
            evidence = build_duckos_capability_evidence()
        control = evidence["control_adapters"]["windows_power_plan_session"]
        self.assertTrue(control["available"])
        self.assertTrue(control["requires_explicit_user_consent"])
        self.assertTrue(control["captures_baseline_before_change"])
        self.assertTrue(control["restores_only_when_current_plan_is_unchanged"])
        self.assertFalse(control["changes_driver_or_registry_state"])

    def test_power_plan_provider_is_platform_scoped(self):
        with patch("tools.gaming_policy_adapter.platform.system", return_value="Linux"):
            evidence = build_duckos_capability_evidence(
                active_power_plan={"guid": "381b4222-f694-41f0-9685-ff5bb260df2e"}
            )
        self.assertFalse(evidence["providers"]["power_plan"]["available"])

    def test_rejects_bad_gpu_or_benchmark_evidence(self):
        with self.assertRaises(GamingEvidenceError):
            build_duckos_capability_evidence(gpu_telemetry={"provider": "guessed", "available": True})
        with self.assertRaises(GamingEvidenceError):
            build_duckos_capability_evidence(frame_time={"sample_count": 0, "p99_frametime_ms": 0})
        with self.assertRaises(GamingEvidenceError):
            build_duckos_capability_evidence(
                snapshot={"snapshot_id": "snap-1", "hardware_fingerprint": "not-a-hash"}
            )

    def test_accepts_oplague_saved_profile_hardware_fingerprint(self):
        evidence = build_duckos_capability_evidence(
            compatibility_profile={
                "validation": "operator_confirmed",
                "game_id": "game.exe",
                "hardware_fingerprint": "b" * 64,
                "driver_version": "1.0",
            }
        )
        self.assertTrue(evidence["providers"]["compatibility_profiles"]["available"])

    def test_profile_must_be_operator_confirmed(self):
        with self.assertRaises(GamingEvidenceError):
            build_duckos_capability_evidence(
                compatibility_profile={
                    "validation": "automatic",
                    "game_id": "game.exe",
                    "hardware_hash": "a" * 64,
                }
            )

    def test_rejects_incomplete_duckos_payload(self):
        with self.assertRaises(GamingEvidenceError):
            to_duckos_capabilities({"schema": "oplague.duckos-gaming-evidence.v1", "providers": {}})


if __name__ == "__main__":
    unittest.main()
