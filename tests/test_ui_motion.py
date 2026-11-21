import os
import tempfile
import unittest

from ui_motion import (
    DURATIONS_MS, MotionPreferences, duration_for, ease_out, ease_paddle_out,
    load_preferences, reduced_motion_enabled, save_preferences,
)


class MotionTests(unittest.TestCase):
    def test_easing_is_clamped_and_monotonic(self):
        self.assertEqual(ease_out(-1), 0.0)
        self.assertEqual(ease_out(0), 0.0)
        self.assertEqual(ease_out(1), 1.0)
        self.assertEqual(ease_out(2), 1.0)
        values = [ease_out(i / 20) for i in range(21)]
        self.assertEqual(values, sorted(values))

    def test_duration_tokens_follow_motion_budget(self):
        self.assertEqual(DURATIONS_MS["instant"], 0)
        self.assertEqual(DURATIONS_MS["micro"], 100)
        self.assertLessEqual(duration_for("spatial", MotionPreferences(reduce_motion=True)), 80)
        self.assertLessEqual(duration_for("emphasis", MotionPreferences(eco_visuals=True)), 80)
        with patch("ui_motion.reduced_motion_enabled", return_value=False):
            normal = duration_for("spatial", MotionPreferences())
            expressive = duration_for("spatial", MotionPreferences(expressive_motion=True))
            reduced = duration_for("spatial", MotionPreferences(True, False, False, True))
            self.assertGreater(expressive, normal)
            self.assertLessEqual(expressive, 380)
            self.assertLessEqual(reduced, 80)

    def test_paddle_easing_is_bounded_at_endpoints_and_has_a_soft_overshoot(self):
        self.assertEqual(ease_paddle_out(0), 0.0)
        self.assertEqual(ease_paddle_out(1), 1.0)
        self.assertGreater(max(ease_paddle_out(i / 100) for i in range(101)), 1.0)

    def test_explicit_reduced_motion_override(self):
        previous = os.environ.get("UI_REDUCED_MOTION")
        try:
            os.environ["UI_REDUCED_MOTION"] = "1"
            self.assertTrue(reduced_motion_enabled())
            os.environ["UI_REDUCED_MOTION"] = "true"
            self.assertTrue(reduced_motion_enabled())
        finally:
            if previous is None:
                os.environ.pop("UI_REDUCED_MOTION", None)
            else:
                os.environ["UI_REDUCED_MOTION"] = previous

    def test_preferences_are_persisted_without_losing_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            old_appdata = os.environ.get("APPDATA")
            os.environ["APPDATA"] = folder
            try:
                expected = MotionPreferences(True, True, False, True)
                save_preferences("motion-tests", expected)
                self.assertEqual(load_preferences("motion-tests"), expected)
            finally:
                if old_appdata is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = old_appdata


if __name__ == "__main__":
    unittest.main()
