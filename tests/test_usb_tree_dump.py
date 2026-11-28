from __future__ import annotations

import unittest

from tools.usb_tree_dump import build_usb_tree


class UsbTreeDumpTests(unittest.TestCase):
    def test_builds_a_deterministic_parent_child_tree(self):
        report = build_usb_tree([
            {
                "instance_id": "USB\\VID_1234&PID_ABCD\\SERIAL-SECRET",
                "parent_instance_id": "USB\\ROOT_HUB30\\1",
                "name": "Input device",
                "status": "OK",
            },
            {
                "instance_id": "USB\\ROOT_HUB30\\1",
                "name": "USB root hub",
                "status": "OK",
            },
        ])
        self.assertEqual(report["device_count"], 2)
        self.assertEqual(report["root_count"], 1)
        root = report["roots"][0]
        self.assertEqual(root["name"], "USB root hub")
        self.assertEqual(root["children"][0]["name"], "Input device")

    def test_raw_instance_ids_are_hidden_by_default(self):
        report = build_usb_tree([
            {"instance_id": "USB\\VID_1234&PID_ABCD\\SERIAL-SECRET", "name": "Device"}
        ])
        rendered = str(report)
        self.assertNotIn("SERIAL-SECRET", rendered)
        self.assertNotIn("instance_id", report["roots"][0])
        self.assertFalse(report["includes_instance_ids"])

    def test_instance_ids_require_explicit_opt_in(self):
        report = build_usb_tree(
            [{"instance_id": "USB\\VID_1234&PID_ABCD\\SERIAL-SECRET"}],
            include_instance_ids=True,
        )
        self.assertEqual(
            report["roots"][0]["instance_id"],
            "USB\\VID_1234&PID_ABCD\\SERIAL-SECRET",
        )

    def test_missing_parent_is_reported_as_orphan(self):
        report = build_usb_tree([
            {
                "instance_id": "USB\\VID_1234&PID_ABCD\\DEVICE",
                "parent_instance_id": "USB\\ROOT_HUB30\\MISSING",
            }
        ])
        self.assertEqual(report["orphan_count"], 1)
        self.assertEqual(report["root_count"], 1)

    def test_parent_cycles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            build_usb_tree([
                {"instance_id": "USB\\A", "parent_instance_id": "USB\\B"},
                {"instance_id": "USB\\B", "parent_instance_id": "USB\\A"},
            ])

    def test_non_usb_ids_and_duplicates_are_rejected(self):
        with self.assertRaises(ValueError):
            build_usb_tree([{"instance_id": "PCI\\VEN_1234&DEV_ABCD"}])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_usb_tree([
                {"instance_id": "USB\\A"},
                {"instance_id": "usb\\a"},
            ])


if __name__ == "__main__":
    unittest.main()
