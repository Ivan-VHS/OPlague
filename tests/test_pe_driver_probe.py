# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import struct
import tempfile
import unittest
from pe_driver_probe import PEFormatError, build_inventory_report, inspect_pe, scan_directory

def make_pe(path: Path, machine: int = 0x8664, subsystem: int = 1, section_data: bytes = b"") -> None:
    data = bytearray(0x300)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, machine, 1, 123456, 0, 0, 0x70, 0x2022)
    optional = 0x98
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<H", data, optional + 68, subsystem)
    section = optional + 0x70
    data[section:section + 8] = b".text\0\0\0"
    raw_size = min(len(section_data), 0x80)
    struct.pack_into("<IIII", data, section + 8, raw_size, 0x1000, raw_size, 0x200)
    struct.pack_into("<I", data, section + 36, 0x60000020)
    if raw_size:
        data[0x200:0x200 + raw_size] = section_data[:raw_size]
    path.write_bytes(data)

class PEDriverProbeTests(unittest.TestCase):
    def test_detects_architecture_section_and_unverified_signature_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.sys"
            make_pe(path, section_data=b"A" * 80)
            report = inspect_pe(path)
            self.assertEqual(report["machine"], "x86_64")
            self.assertEqual(report["subsystem"], "native")
            self.assertTrue(report["driver_candidate"])
            self.assertEqual(report["sections"][0]["name"], ".text")
            self.assertTrue(report["sections"][0]["executable"])
            self.assertEqual(report["authenticode"]["trust"], "not_verified")
            self.assertEqual(report["warnings"], ["no_authenticode_certificate_table"])
            self.assertRegex(report["sha256"], r"^[0-9a-f]{64}$")

    def test_rejects_non_pe_files_and_header_offsets_outside_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readme.txt"
            path.write_text("not a binary", encoding="utf-8")
            with self.assertRaises(PEFormatError):
                inspect_pe(path)
            path.write_bytes(b"MZ" + b"\0" * 60)
            with self.assertRaises(PEFormatError):
                inspect_pe(path)

    def test_directory_scan_is_sorted_and_skips_unrelated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_pe(root / "b.dll", machine=0x14C, subsystem=3)
            make_pe(root / "a.sys", machine=0xAA64, subsystem=1)
            (root / "ignore.txt").write_text("ignored", encoding="utf-8")
            reports = scan_directory(root)
            self.assertEqual([item["path"] for item in reports], ["a.sys", "b.dll"])
            self.assertEqual(reports[0]["machine"], "arm64")

    def test_inventory_report_groups_duplicate_hashes_and_architectures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_pe(root / "a.sys", machine=0x8664)
            (root / "b.sys").write_bytes((root / "a.sys").read_bytes())
            report = build_inventory_report(scan_directory(root), str(root))
            self.assertEqual(report["schema"], "oplague.pe-inventory.v1")
            self.assertEqual(report["summary"]["valid_pe_files"], 2)
            self.assertEqual(report["summary"]["driver_candidates"], 2)
            self.assertEqual(report["summary"]["duplicate_groups"], 1)
            self.assertEqual(report["architectures"]["x86_64"], 2)
            self.assertEqual(report["trust_boundary"]["signature_verification"], "not_performed")

    def test_scan_limit_is_validated_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                scan_directory(directory, 0)

if __name__ == "__main__":
    unittest.main()
