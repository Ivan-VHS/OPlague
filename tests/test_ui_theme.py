import unittest

from ui_theme import PALETTES, contrast_ratio, load_preferred_theme, palette_for


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

    def test_invalid_color_is_rejected(self):
        with self.assertRaises(ValueError):
            contrast_ratio("blue", "#FFFFFF")

    def test_unknown_theme_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "system"):
            palette_for("neon")

    def test_preferred_theme_loader_returns_supported_mode(self):
        self.assertIn(load_preferred_theme(), {"system", "light", "dark"})


if __name__ == "__main__":
    unittest.main()
