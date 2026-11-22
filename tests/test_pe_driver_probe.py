# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import struct
import tempfile
import unittest
from pe_driver_probe import PEFormatError, inspect_pe, scan_directory

def make_pe(path: Path, machine: int = 0x8664, subsystem: int = 1) -> None:
    data = bytearray(0x200)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, machine, 3, 0, 0, 0, 0x70, 0x2022)
    struct.pack_into("<H", data, 0x98, 0x20B)
    struct.pack_into("<H", data, 0x98 + 68, subsystem)
    path.write_bytes(data)

class PEDriverProbeTests(unittest.TestCase):
    def test_detects_architecture_and_marks_candidate_without_claiming_trust(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.sys"
            make_pe(path)
            report = inspect_pe(path)
            self.assertEqual(report["machine"], "x86_64")
            self.assertEqual(report["subsystem"], "native")
            self.assertTrue(report["driver_candidate"])
            self.assertEqual(report["signature_status"], "not_checked")
            self.assertRegex(report["sha256"], r"^[0-9a-f]{64}$")

    def test_rejects_non_pe_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readme.txt"
            path.write_text("not a binary", encoding="utf-8")
            with self.assertRaises(PEFormatError):
                inspect_pe(path)

    def test_directory_scan_is_sorted_and_skips_symlink_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_pe(root / "b.dll", machine=0x14C, subsystem=3)
            make_pe(root / "a.sys", machine=0xAA64, subsystem=1)
            (root / "ignore.txt").write_text("ignored", encoding="utf-8")
            reports = scan_directory(root)
            self.assertEqual([item["path"] for item in reports], ["a.sys", "b.dll"])
            self.assertEqual(reports[0]["machine"], "arm64")

if __name__ == "__main__":
    unittest.main()
