from __future__ import annotations
import hashlib, stat, tempfile, unittest, zipfile
from pathlib import Path
from oplague_app import MAX_INF_BYTES, inspect_package, parse_inf_text

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


    def test_rejects_case_insensitive_duplicate_archive_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("driver.inf", SAMPLE)
                archive.writestr("DRIVER.INF", SAMPLE)
            with self.assertRaisesRegex(ValueError, "Duplicate archive path"):
                inspect_package(path)

    def test_rejects_symlink_entries_without_extracting_them(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "symlink.zip"
            link = zipfile.ZipInfo("payload.inf")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(link, SAMPLE)
            with self.assertRaisesRegex(ValueError, "Non-regular archive entry"):
                inspect_package(path)

    def test_rejects_non_canonical_dot_segments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dot-segment.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("nested/./driver.inf", SAMPLE)
            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                inspect_package(path)

    def test_oversized_direct_inf_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "oversized.inf"
            with path.open("wb") as stream:
                stream.truncate(MAX_INF_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "INF file is too large"):
                inspect_package(path)

    def test_rejects_unknown_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "payload.bin"; path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "Supported package formats"):
                inspect_package(path)

    def test_inf_and_zip_reports_include_model_id_evidence(self):
        model_inf = SAMPLE + """
[Manufacturer]
%Vendor%=Models,NTamd64
[Models.NTamd64]
%Adapter%=Install, PCI\\VEN_1234&DEV_ABCD
"""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inf_path = root / "network.inf"
            inf_path.write_text(model_inf, encoding="utf-8")
            direct = inspect_package(inf_path)
            self.assertEqual(
                direct["compatibility"]["hardware_ids"],
                ["PCI\\VEN_1234&DEV_ABCD"],
            )
            self.assertEqual(direct["compatibility"]["architectures"], ["x64"])

            zip_path = root / "network.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("network.inf", model_inf)
            zipped = inspect_package(zip_path)
            self.assertEqual(
                zipped["inf_files"][0]["compatibility"]["hardware_ids"],
                ["PCI\\VEN_1234&DEV_ABCD"],
            )

if __name__ == "__main__":
    unittest.main()
