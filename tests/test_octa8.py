from __future__ import annotations
import unittest
from oplague.octa8 import Octa8Error, octa8_pack, octa8_unpack, octa8_digest, octa8_validate, octa8_assert_kind

class Octa8AdapterTests(unittest.TestCase):
    def test_eight_kind_wire_round_trip(self):
        values = [None, True, -1, 2.5, "report", b"hash", [1, "x"], {"device": "cpu"}]
        for value in values:
            self.assertEqual(octa8_unpack(octa8_pack(value)), value)

    def test_digest_is_stable_for_record_order(self):
        self.assertEqual(octa8_digest(octa8_pack({"a": 1, "b": 2})), octa8_digest(octa8_pack({"b": 2, "a": 1})))

    def test_validation_rejects_wrong_schema_and_nonfinite_values(self):
        self.assertFalse(octa8_validate({"schema": "bad", "kind": "text", "value": "x"}))
        with self.assertRaises(Octa8Error):
            octa8_pack(float("nan"))

    def test_kind_assertion(self):
        self.assertTrue(octa8_assert_kind(octa8_pack({"ok": True}), "record"))
        with self.assertRaises(Octa8Error):
            octa8_assert_kind(octa8_pack(1), "text")

if __name__ == "__main__":
    unittest.main()
