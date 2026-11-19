from __future__ import annotations
import hashlib, tempfile, unittest, zipfile
from pathlib import Path
from oplague_app import inspect_package, parse_inf_text

SAMPLE = """[Version]
Class=Net
Provider=%Vendor%
DriverVer=11/19/2026,1.2.3.4
CatalogFile=sample.cat

[Manufacturer]
Provider=Wrong
"""

class InspectorTests(unittest.TestCase):
    def test_inf_parser_limits_values_to_version_section(self):
        result = parse_inf_text(SAMPLE)
        self.assertEqual(result["class"], "Net")
        self.assertEqual(result["provider"], "%Vendor%")
        self.assertNotIn("wrong", result.values())

    def test_inf_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.inf"
            path.write_text(SAMPLE, encoding="utf-8")
            result = inspect_package(path)
            self.assertEqual(result["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_zip_metadata_without_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "driver.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("sample.inf", SAMPLE)
                archive.writestr("sample.cat", b"catalog")
            result = inspect_package(path)
            self.assertEqual(result["entry_count"], 2)
            self.assertEqual(result["inf_files"][0]["metadata"]["class"], "Net")
            self.assertEqual(result["catalog_files"], ["sample.cat"])
            self.assertFalse((Path(folder) / "sample.inf").exists())

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../escape.inf", SAMPLE)
            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                inspect_package(path)

    def test_rejects_unknown_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "payload.bin"; path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "Supported package formats"):
                inspect_package(path)

if __name__ == "__main__":
    unittest.main()
