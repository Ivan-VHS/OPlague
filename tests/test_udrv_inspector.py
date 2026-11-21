from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.udrv_inspector import PackageError, inspect_package


def make_manifest(payload: bytes, path: str = "payload/sample.inf") -> bytes:
    return json.dumps(
        {
            "format": "udrv",
            "format_version": 1,
            "id": "example.vendor.driver",
            "version": "1.2.3",
            "payload": [
                {
                    "path": path,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ],
        }
    ).encode("utf-8")


class UdrvInspectorTests(unittest.TestCase):
    def test_valid_directory_package(self) -> None:
        payload = b"[Version]\nSignature=$Windows NT$\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "payload").mkdir()
            (root / "payload" / "sample.inf").write_bytes(payload)
            (root / "manifest.json").write_bytes(make_manifest(payload))

            report = inspect_package(root)

        self.assertEqual(report.package_id, "example.vendor.driver")
        self.assertEqual(report.version, "1.2.3")
        self.assertEqual(report.files_verified, 1)
        self.assertEqual(report.total_bytes, len(payload))
        self.assertEqual(report.container, "directory")

    def test_oversized_directory_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_bytes(b"x" * (4 * 1024 * 1024 + 1))

            with self.assertRaisesRegex(PackageError, "manifest exceeds the 4 MiB limit"):
                inspect_package(root)

    def test_valid_zip_package(self) -> None:
        payload = b"driver payload"
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "sample.udrv"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", make_manifest(payload))
                archive.writestr("payload/sample.inf", payload)

            report = inspect_package(archive_path)

        self.assertEqual(report.container, "zip")
        self.assertEqual(report.files_verified, 1)

    def test_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "payload").mkdir()
            (root / "payload" / "sample.inf").write_bytes(b"ORIGINAL")
            (root / "manifest.json").write_bytes(make_manifest(b"original"))

            with self.assertRaisesRegex(PackageError, "SHA-256 mismatch"):
                inspect_package(root)

    def test_undeclared_archive_file_is_rejected(self) -> None:
        payload = b"declared"
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "extra.udrv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("manifest.json", make_manifest(payload))
                archive.writestr("payload/sample.inf", payload)
                archive.writestr("payload/extra.sys", b"not declared")

            with self.assertRaisesRegex(PackageError, "undeclared files"):
                inspect_package(archive_path)

    def test_traversal_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "payload").mkdir()
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "format": "udrv",
                        "format_version": 1,
                        "id": "example.driver",
                        "version": "1",
                        "payload": [
                            {
                                "path": "payload/../../outside.sys",
                                "size": 0,
                                "sha256": hashlib.sha256(b"").hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PackageError, "unsafe payload path"):
                inspect_package(root)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                '{"format":"udrv","format":"other"}', encoding="utf-8"
            )
            with self.assertRaisesRegex(PackageError, "duplicate JSON key"):
                inspect_package(root)

    def test_symbolic_link_payload_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "payload").mkdir()
            target = root / "payload" / "target.inf"
            target.write_bytes(b"driver")
            link = root / "payload" / "link.inf"
            try:
                link.symlink_to(target.name)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable on this platform")
            (root / "manifest.json").write_bytes(make_manifest(b"driver", "payload/target.inf"))
            with self.assertRaisesRegex(PackageError, "symbolic links"):
                inspect_package(root)


if __name__ == "__main__":
    unittest.main()
