from __future__ import annotations

import unittest

from tools.xp_game_compatibility import audit_game_profile


class XpGameCompatibilityTests(unittest.TestCase):
    def profile(self):
        return {
            "schema": "duckos.game-launch-profile.v1",
            "id": "legacy-game", "name": "Legacy Game",
            "compatibility": {
                "windows_version": "windows-xp", "service_pack": 3,
                "graphics": ["direct3d9", "glide"], "audio": ["directsound", "eax"],
                "input": ["directinput"], "network": ["directplay", "ipx_spx"],
                "display": {"width": 1024, "height": 768, "color_depth": 16, "refresh_rate_hz": 85}
            }
        }

    def test_reports_legacy_graphics_audio_display_and_network_findings(self):
        report = audit_game_profile(self.profile())
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(report["schema"], "oplague.xp-sp3-game-compatibility.v1")
        self.assertTrue({
            "XP-GFX-GLIDE", "XP-DISPLAY-COLOR-DEPTH", "XP-DISPLAY-REFRESH",
            "XP-AUDIO-EAX", "XP-NETWORK-LEGACY"
        }.issubset(codes))
        self.assertEqual(report["status"], "attention_required")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["drivers_changed"])

    def test_4_by_3_display_does_not_raise_aspect_warning(self):
        profile = self.profile()
        profile["compatibility"]["display"].update({"width": 1024, "height": 768, "color_depth": 32, "refresh_rate_hz": 60})
        report = audit_game_profile(profile)
        self.assertNotIn("XP-DISPLAY-ASPECT", {item["code"] for item in report["findings"]})

    def test_supplied_hardware_snapshot_reports_gpu_driver_evidence(self):
        report = audit_game_profile(self.profile(), {
            "devices": [{"name": "Example GPU", "driver_version": "1.2", "status": "OK"}]
        })
        self.assertEqual(report["hardware"]["display_adapters"][0]["driver_version"], "1.2")

    def test_rejects_wrong_profile_schema_and_malformed_display(self):
        profile = self.profile()
        profile["schema"] = "wrong"
        with self.assertRaises(ValueError):
            audit_game_profile(profile)
        profile = self.profile()
        profile["compatibility"]["display"]["width"] = True
        with self.assertRaises(ValueError):
            audit_game_profile(profile)


if __name__ == "__main__":
    unittest.main()
