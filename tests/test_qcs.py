from __future__ import annotations

import unittest

from tools.qcs import DIALECTS, QCSSyntaxError, parse_source, render_report


class QCSParserTests(unittest.TestCase):
    def test_catalogue_has_66_unique_dialects_and_domains(self) -> None:
        self.assertEqual(len(DIALECTS), 66)
        self.assertEqual(len({item["name"] for item in DIALECTS}), 66)
        self.assertEqual(len({item["domain"] for item in DIALECTS}), 66)
        self.assertEqual([item["index"] for item in DIALECTS], list(range(1, 67)))

    def test_parses_swift_like_contour_and_transfer_operators(self) -> None:
        source = """|~ domain:mmio(addr: 0x40021000), invariant:!, arch:arm64, budget:120ns ~|
func togglePin(register: UInt32, bit: UInt8) {
    register ^= 1 << bit
    register ->> writeMMIO(register)
}
|~ end ~|
"""
        result = parse_source(source)
        self.assertEqual(result["schema"], "oplage.qcs-contour.v1")
        self.assertEqual(result["summary"]["contour_count"], 1)
        self.assertEqual(result["contours"][0]["dialect"], "BareSwift")
        self.assertEqual(result["contours"][0]["attributes"]["budget"], "120ns")
        self.assertEqual(result["contours"][0]["transfers"][0]["operator"], "->>")
        self.assertEqual(result["contours"][0]["transfers"][0]["line"], 4)

    def test_nested_commas_and_strings_do_not_split_attributes(self) -> None:
        result = parse_source('''|~ domain:bus(protocol: "axi4", lanes: 4), invariant:~, owner:dma ~|
let value = 1
|~ end ~|
''')
        self.assertEqual(result["contours"][0]["domain"], "bus")
        self.assertEqual(result["contours"][0]["attributes"]["domain"], 'bus(protocol: "axi4", lanes: 4)')

    def test_multiple_contours_and_borrow_release_are_counted(self) -> None:
        result = parse_source('''|~ domain:arena, invariant:? ~|
let page = allocate()
page <-~ pool.release
|~ end ~|
|~ domain:simd(width:128), invariant:! ~|
let sum = add(a, b)
|~ end ~|
''')
        self.assertEqual(result["summary"]["contour_count"], 2)
        self.assertEqual(result["summary"]["transfer_count"], 1)
        self.assertEqual(result["contours"][0]["transfers"][0]["kind"], "borrow-release")

    def test_rejects_unknown_domain_and_bad_invariant(self) -> None:
        with self.assertRaisesRegex(QCSSyntaxError, "unknown domain"):
            parse_source("|~ domain:quantumCPU, invariant:! ~|\nx\n|~ end ~|")
        with self.assertRaisesRegex(QCSSyntaxError, "invariant must"):
            parse_source("|~ domain:mmio, invariant:yes ~|\nx\n|~ end ~|")

    def test_rejects_duplicate_missing_and_invalid_attributes(self) -> None:
        for header, message in (
            ("domain:mmio, domain:heap, invariant:!", "duplicate attribute"),
            ("domain:mmio", "invariant must"),
            ("domain:mmio, invariant:!, budget:soon", "budget must"),
        ):
            with self.subTest(header=header), self.assertRaisesRegex(QCSSyntaxError, message):
                parse_source(f"|~ {header} ~|\nx\n|~ end ~|")

    def test_rejects_malformed_contour_boundaries(self) -> None:
        invalid = (
            "|~ end ~|",
            "|~ domain:mmio, invariant:! ~|\nx",
            "|~ domain:mmio, invariant:! ~|\n|~ domain:heap, invariant:? ~|\nx\n|~ end ~|",
            "outside text\n|~ domain:mmio, invariant:! ~|\nx\n|~ end ~|",
            "|~ domain:mmio, invariant:! ~|\n|~ end ~|",
        )
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(QCSSyntaxError):
                parse_source(source)

    def test_report_is_compact_and_explicit_about_scope(self) -> None:
        result = parse_source("|~ domain:trng, invariant:~ ~|\nlet sample = read()\n|~ end ~|")
        report = render_report(result)
        self.assertIn("QCS validation: PASS", report)
        self.assertIn("RandSwift", report)
        self.assertIn("no compilation", report)

    def test_source_size_is_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds"):
            parse_source("x" * (1_048_577))


if __name__ == "__main__":
    unittest.main()
