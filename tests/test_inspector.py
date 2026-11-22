from __future__ import annotations
import hashlib, stat, tempfile, unittest, zipfile
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

    def test_archive_security_report_flags_metadata_without_extracting(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "driver-bundle.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("driver.sys", b"binary")
                archive.writestr("DRIVER.SYS", b"duplicate on Windows filesystems")
                archive.writestr("install.ps1", b"Write-Host 'review'")
                archive.writestr("nested.cab", b"nested package")
                link = zipfile.ZipInfo("linked.sys")
                link.create_system = 3
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(link, "driver.sys")

            report = inspect_package(path)
            risk = report["archive_security"]
            self.assertEqual(risk["schema"], "oplage.archive-risk.v1")
            self.assertTrue(risk["metadata_only"])
            self.assertEqual(risk["disposition"], "manual_review")
            self.assertEqual(risk["duplicate_paths"], ["DRIVER.SYS"])
            self.assertEqual(risk["symbolic_links"], ["linked.sys"])
            self.assertEqual(risk["script_candidates"], ["install.ps1"])
            self.assertEqual(risk["nested_archives"], ["nested.cab"])
            self.assertGreaterEqual(risk["warning_count"], 3)
            self.assertIn("not malware detection", risk["limitations"])
            self.assertFalse((Path(folder) / "driver.sys").exists())


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
