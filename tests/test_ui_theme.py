import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ui_theme import (
    PALETTES,
    _save_preferred_theme,
    contrast_ratio,
    load_preferred_theme,
    palette_contrast_issues,
    palette_for,
)


class OPlagueThemeTests(unittest.TestCase):
    def test_only_the_duck_palette_is_available(self):
        self.assertEqual(set(PALETTES), {"duck"})
        palette = palette_for("duck")
        self.assertEqual(palette["bg"], "#080808")
        self.assertEqual(palette["surface"], "#151515")
        self.assertEqual(palette["elevated"], "#242424")
        self.assertEqual(palette["fg"], "#FFFFFF")
        self.assertEqual(palette["secondary"], "#E5E5E5")
        self.assertEqual(palette["muted"], "#A6A6A6")
        self.assertEqual(palette["brand"], "#FFD400")
        self.assertEqual(palette["brand_hover"], "#FFE45C")
        self.assertEqual(palette["border"], "#3A3A3A")
        self.assertEqual(palette["selection"], "#3A3100")

    def test_legacy_modes_all_resolve_to_the_same_duck_palette(self):
        expected = palette_for("duck")
        for mode in ("system", "light", "dark", "amber"):
            with self.subTest(mode=mode):
                self.assertEqual(palette_for(mode), expected)
        self.assertEqual(palette_for("system", system_dark=True), expected)
        self.assertEqual(palette_for("system", system_dark=False), expected)

    def test_text_action_and_focus_contrast_are_accessible(self):
        palette = palette_for()
        self.assertGreaterEqual(contrast_ratio(palette["fg"], palette["bg"]), 7.0)
        self.assertGreaterEqual(contrast_ratio(palette["fg"], palette["surface"]), 7.0)
        self.assertGreaterEqual(contrast_ratio(palette["on_brand"], palette["brand"]), 4.5)
        self.assertGreaterEqual(contrast_ratio(palette["focus"], palette["bg"]), 3.0)
        self.assertGreaterEqual(contrast_ratio(palette["muted"], palette["bg"]), 4.5)
        self.assertEqual(palette_contrast_issues(palette), [])

    def test_semantic_statuses_use_distinct_hues_and_explicit_labels(self):
        palette = palette_for()
        for token in ("success", "warning", "error", "info", "brand", "blue", "red"):
            with self.subTest(token=token):
                self.assertEqual(palette[token], "#FFD400")
        self.assertEqual(palette["on_blue"], "#080808")
        self.assertEqual(palette["on_red"], "#080808")

    def test_legacy_user_settings_are_normalized_to_duck(self):
        for old_mode in ("system", "light", "dark", "amber", "duck"):
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "ui-settings.json"
                target.write_text(json.dumps({"version": 1, "mode": old_mode}), encoding="utf-8")
                with patch("ui_theme._settings_path", return_value=target):
                    _save_preferred_theme(old_mode)
                self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["mode"], "duck")
                self.assertEqual(load_preferred_theme(), "duck")
                self.assertEqual(sorted(path.name for path in Path(directory).iterdir()),
                                 ["ui-settings.json"])

    def test_failed_atomic_replace_preserves_previous_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ui-settings.json"
            original = json.dumps({"version": 1, "mode": "light"})
            target.write_text(original, encoding="utf-8")
            with patch("ui_theme._settings_path", return_value=target):
                with patch("ui_theme.os.replace", side_effect=OSError("simulated replace failure")):
                    _save_preferred_theme("dark")
            self.assertEqual(target.read_text(encoding="utf-8"), original)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()),
                             ["ui-settings.json"])

    def test_invalid_color_is_rejected(self):
        with self.assertRaises(ValueError):
            contrast_ratio("blue", "#FFFFFF")

    def test_unknown_theme_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duck"):
            palette_for("neon")


if __name__ == "__main__":
    unittest.main()
