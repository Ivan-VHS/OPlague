from __future__ import annotations

import unittest
from tools.hardware_id_lint import lint_hardware_id, format_report


class HardwareIdLintTests(unittest.TestCase):
    def test_pci_identifier_is_split_into_explained_components(self):
        report = lint_hardware_id(r"PCI\\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03")
        self.assertTrue(report["valid"])
        self.assertEqual(report["bus"], "PCI")
        fields = {item["name"]: item["value"] for item in report["components"]}
        self.assertEqual(fields["ven"], "8086")
        self.assertEqual(fields["dev"], "15F3")
        self.assertEqual(fields["subsys"], "00008086")
        self.assertEqual(fields["rev"], "03")
        self.assertTrue(any("no manufacturer name" in item["meaning"] for item in report["components"]))

    def test_normalization_is_case_and_separator_tolerant(self):
        report = lint_hardware_id(" pci/ven_8086&dev_15f3 ")
        self.assertEqual(report["normalized"], r"PCI\\VEN_8086&DEV_15F3")
        self.assertTrue(report["valid"])

    def test_bad_field_width_is_an_error(self):
        report = lint_hardware_id(r"PCI\\VEN_12&DEV_15F3")
        self.assertFalse(report["valid"])
        self.assertTrue(any(item["code"] == "OPL-E0102" for item in report["findings"]))

    def test_usb_identifier_uses_usb_field_rules(self):
        report = lint_hardware_id(r"USB\\VID_046D&PID_C534&REV_1201")
        self.assertTrue(report["valid"])
        self.assertEqual(report["bus"], "USB")

    def test_unknown_bus_and_path_traversal_fail_closed(self):
        unknown = lint_hardware_id(r"UNKNOWN\\DEVICE_01")
        traversal = lint_hardware_id(r"PCI\\..\\VEN_8086&DEV_15F3")
        self.assertFalse(unknown["valid"])
        self.assertFalse(traversal["valid"])

    def test_unknown_fields_are_reported_without_guessing(self):
        report = lint_hardware_id(r"PCI\\VEN_ABCD&DEV_1234&VENDORNAME_FOO")
        self.assertTrue(report["valid"])
        self.assertTrue(any(item["code"] == "OPL-W0104" for item in report["findings"]))
        self.assertNotIn("manufacturer", str(report).casefold())

    def test_input_bounds_and_non_string_values(self):
        self.assertFalse(lint_hardware_id(42)["valid"])
        self.assertFalse(lint_hardware_id("A" * 513)["valid"])

    def test_formatted_report_states_the_scope(self):
        report = format_report(lint_hardware_id(r"ACPI\\PNP0303"))
        self.assertIn("Syntax inspection only", report)
        self.assertIn("no detailed vendor grammar", report)


if __name__ == "__main__":
    unittest.main()
