from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest

from tools.pe_inspector import PEFormatError, inspect_pe, inspect_pe_bytes


def make_pe() -> bytes:
    header = bytearray(0x200 + 40)
    header[:2] = b"MZ"
    struct.pack_into("<I", header, 0x3C, 0x80)
    header[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", header, 0x84, 0x8664, 1, 1234, 0, 0, 0xF0, 0x22)
    optional = 0x98
    struct.pack_into("<H", header, optional, 0x20B)
    struct.pack_into("<I", header, optional + 16, 0x1000)
    struct.pack_into("<Q", header, optional + 24, 0x140000000)
    struct.pack_into("<II", header, optional + 32, 0x1000, 0x200)
    struct.pack_into("<H", header, optional + 68, 3)
    struct.pack_into("<I", header, optional + 108, 16)
    struct.pack_into("<II", header, optional + 112 + 4 * 8, 0x400, 0x100)
    section = optional + 0xF0
    header[section:section + 8] = b".text\0\0\0"
    struct.pack_into("<IIII", header, section + 8, 0x100, 0x1000, 0x100, 0x200)
    struct.pack_into("<I", header, section + 36, 0x60000020)
    return bytes(header) + bytes(0x500 - len(header))


class PEInspectorTests(unittest.TestCase):
    def test_reads_headers_and_sections_without_a_signature_verdict(self):
        report = inspect_pe_bytes(make_pe(), file_size=0x500)
        self.assertEqual(report["machine"], "x64")
        self.assertEqual(report["format"], "PE32+")
        self.assertEqual(report["entry_point_rva"], 0x1000)
        self.assertEqual(report["sections"][0]["name"], ".text")
        self.assertTrue(report["certificate_table"]["present"])
        self.assertFalse(report["certificate_table"]["verified"])
        self.assertEqual(report["signature_verdict"], "not-checked")
        self.assertFalse(report["execution_performed"])

    def test_rejects_bad_signature_and_out_of_file_sections(self):
        with self.assertRaises(PEFormatError):
            inspect_pe_bytes(b"not-pe")
        data = bytearray(make_pe())
        struct.pack_into("<I", data, 0x98 + 0xF0 + 20, 0x9000)
        with self.assertRaises(PEFormatError):
            inspect_pe_bytes(bytes(data), file_size=0x500)

    def test_reads_regular_file_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.exe"
            path.write_bytes(make_pe())
            self.assertEqual(inspect_pe(path)["machine"], "x64")


if __name__ == "__main__":
    unittest.main()
