from __future__ import annotations

import unittest

from tools.i18n import LocaleContext, canonical_locale_tag


class LocaleTagTests(unittest.TestCase):
    def test_canonicalizes_language_script_and_region(self) -> None:
        self.assertEqual(canonical_locale_tag("zh-hans-cn"), "zh-Hans-CN")
        self.assertEqual(canonical_locale_tag("sr_latn_rs"), "sr-Latn-RS")

    def test_accepts_extensions_and_private_use(self) -> None:
        self.assertEqual(canonical_locale_tag("en-US-u-ca-gregory"), "en-US-u-ca-gregory")
        self.assertEqual(canonical_locale_tag("x-local-test"), "x-local-test")

    def test_accepts_registered_grandfathered_language_tags(self) -> None:
        cases = {
            "i-klingon": "i-klingon",
            "EN-gb-OED": "en-GB-oed",
            "no-BOK": "no-bok",
            "zh-guoyu": "zh-guoyu",
            "sgn-be-fr": "sgn-BE-FR",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(canonical_locale_tag(value), expected)

    def test_rejects_unknown_irregular_language_tag(self) -> None:
        with self.assertRaises(ValueError):
            canonical_locale_tag("i-unknown")

    def test_rejects_malformed_tags(self) -> None:
        for value in ("", "en--US", "a", "en-u", "en-u-ca-ca"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonical_locale_tag(value)

    def test_catalog_fallback_and_rtl(self) -> None:
        root = LocaleContext.load("ar-EG")
        self.assertEqual(root.resolved_tag, "ar")
        self.assertEqual(root.direction, "rtl")
        self.assertEqual(root.message("common.action.save"), "حفظ")

    def test_direction_ignores_script_like_extension_subtags(self) -> None:
        context = LocaleContext.load("en-u-kn-arab")
        self.assertEqual(context.direction, "ltr")

    def test_explicit_script_controls_text_direction(self) -> None:
        self.assertEqual(LocaleContext.load("ar-Latn").direction, "ltr")
        self.assertEqual(LocaleContext.load("ar-Arab").direction, "rtl")

    def test_unknown_valid_locale_uses_source_messages(self) -> None:
        context = LocaleContext.load("sw-TZ")
        self.assertEqual(context.requested_tag, "sw-TZ")
        self.assertEqual(context.resolved_tag, "en")
        self.assertEqual(context.message("common.action.save"), "Save")


if __name__ == "__main__":
    unittest.main()
