from __future__ import annotations

import contextlib
import io
import json
import unittest

from tools.hardware_id_linter import lint_hardware_id, main


class HardwareIdLinterTests(unittest.TestCase):
    def test_pci_identifier_explains_known_fields(self) -> None:
        report = lint_hardware_id(
            r"PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03"
        )

        self.assertTrue(report["valid"])
        self.assertEqual(report["bus"], "PCI")
        fields = {item["code"]: item["value"] for item in report["fields"]}
        self.assertEqual(fields, {
            "VEN": "8086",
            "DEV": "15F3",
            "SUBSYS": "00008086",
            "REV": "03",
        })
        self.assertIn("does not prove that a device exists", report["limitations"][0])

    def test_normalizes_case_and_forward_slashes(self) -> None:
        report = lint_hardware_id(" pci/ven_8086&dev_15f3 ")
        self.assertTrue(report["valid"])
        self.assertEqual(report["normalized"], r"PCI\VEN_8086&DEV_15F3")

    def test_usb_identifier_checks_vid_pid_and_revision(self) -> None:
        report = lint_hardware_id(r"USB\VID_046D&PID_C52B&REV_1201&MI_00")

        self.assertTrue(report["valid"])
        fields = {item["code"]: item["value"] for item in report["fields"]}
        self.assertEqual(fields["VID"], "046D")
        self.assertEqual(fields["PID"], "C52B")
        self.assertEqual(fields["REV"], "1201")
        self.assertEqual(fields["MI"], "00")

    def test_pci_requires_vendor_and_device_fields(self) -> None:
        report = lint_hardware_id(r"PCI\VEN_8086")
        self.assertFalse(report["valid"])
        self.assertTrue(any("DEV attribute is missing" in item for item in report["errors"]))

    def test_rejects_non_hex_pci_vendor(self) -> None:
        report = lint_hardware_id(r"PCI\VEN_INTL&DEV_15F3")
        self.assertFalse(report["valid"])
        self.assertTrue(any("VEN must contain" in item for item in report["errors"]))

    def test_rejects_duplicate_attributes(self) -> None:
        report = lint_hardware_id(r"PCI\VEN_8086&VEN_1234&DEV_15F3")
        self.assertFalse(report["valid"])
        self.assertTrue(any("Duplicate attribute: VEN" in item for item in report["errors"]))

    def test_accepts_acpi_opaque_identifier_without_guessing(self) -> None:
        report = lint_hardware_id(r"ACPI\PNP0A08")
        self.assertTrue(report["valid"])
        self.assertEqual(report["bus"], "ACPI")
        self.assertIn("does not infer its meaning", " ".join(report["notes"]))

    def test_additional_components_are_not_mislabelled_as_hardware_ids(self) -> None:
        report = lint_hardware_id(r"PCI\VEN_8086&DEV_15F3\3&11583659&0&10")
        self.assertTrue(report["valid"])
        self.assertEqual(report["scope"], "instance-id-like path")
        self.assertEqual(report["additional_path_segments"], ["3&11583659&0&10"])

    def test_rejects_unknown_bus_and_invalid_path(self) -> None:
        self.assertFalse(lint_hardware_id(r"UNKNOWN\DEVICE")["valid"])
        self.assertFalse(lint_hardware_id(r"PCI\..\escape")["valid"])

    def test_rejects_non_string_and_nul_input(self) -> None:
        self.assertFalse(lint_hardware_id(None)["valid"])
        self.assertFalse(lint_hardware_id("PCI\\VEN_8086\x00&DEV_15F3")["valid"])

    def test_cli_json_and_exit_status(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["--json", r"PCI\VEN_8086&DEV_15F3"])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output.getvalue())["valid"])

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["--json", r"PCI\VEN_8086"])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(output.getvalue())["valid"])


if __name__ == "__main__":
    unittest.main()
