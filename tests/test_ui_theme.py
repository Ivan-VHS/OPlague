import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ui_theme import PALETTES, _save_preferred_theme, contrast_ratio, load_preferred_theme, palette_contrast_issues, palette_for


class OPlagueThemeTests(unittest.TestCase):
    def test_light_and_dark_palettes_are_distinct_and_complete(self):
        light = palette_for("light")
        dark = palette_for("dark")
        self.assertNotEqual(light["page"], dark["page"])
        self.assertTrue(light["accent"] and dark["accent"])
        self.assertTrue(light["editor_text"] and dark["editor_text"])
        required = {
            "bg", "surface", "elevated", "fg", "secondary", "muted",
            "blue", "blue_hover", "on_blue", "red", "red_hover", "on_red",
            "border", "focus", "selection", "selection_fg", "disabled",
            "success", "warning", "error", "info",
        }
        self.assertTrue(required.issubset(light))
        self.assertTrue(required.issubset(dark))

    def test_system_mode_can_be_resolved_deterministically(self):
        self.assertEqual(palette_for("system", system_dark=True)["mode"], "dark")
        self.assertEqual(palette_for("system", system_dark=False)["mode"], "light")

    def test_white_blue_red_text_and_action_contrast(self):
        for palette in PALETTES.values():
            self.assertGreaterEqual(contrast_ratio(palette["fg"], palette["bg"]), 7.0)
            self.assertGreaterEqual(contrast_ratio(palette["on_blue"], palette["blue"]), 4.5)
            self.assertGreaterEqual(contrast_ratio(palette["on_red"], palette["red"]), 4.5)

    def test_every_palette_meets_ui_ux_40026_text_contrast(self):
        for name, palette in PALETTES.items():
            self.assertEqual(palette_contrast_issues(palette), [], name)
            for token in ("success", "warning", "error", "info"):
                self.assertIn(token, palette)

    def test_invalid_color_is_rejected(self):
        with self.assertRaises(ValueError):
            contrast_ratio("blue", "#FFFFFF")

    def test_unknown_theme_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "system"):
            palette_for("neon")


    def test_theme_settings_are_atomically_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ui-settings.json"
            target.write_text('{"version": 1, "mode": "light"}\\n', encoding="utf-8")
            with patch("ui_theme._settings_path", return_value=target):
                _save_preferred_theme("dark")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["mode"], "dark")
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()),
                             ["ui-settings.json"])

    def test_failed_atomic_replace_preserves_previous_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ui-settings.json"
            original = '{"version": 1, "mode": "light"}\\n'
            target.write_text(original, encoding="utf-8")
            with patch("ui_theme._settings_path", return_value=target):
                with patch("ui_theme.os.replace", side_effect=OSError("simulated replace failure")):
                    _save_preferred_theme("dark")
            self.assertEqual(target.read_text(encoding="utf-8"), original)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()),
                             ["ui-settings.json"])

    def test_theme_saver_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "system"):
            _save_preferred_theme("neon")

    def test_preferred_theme_loader_returns_supported_mode(self):
        self.assertIn(load_preferred_theme(), {"system", "light", "dark"})


if __name__ == "__main__":
    unittest.main()
