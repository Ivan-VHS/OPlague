from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.sbom_inventory import SBOMError, build_sbom, write_sbom


class SBOMInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        (self.root / "README.md").write_text("project\n", encoding="utf-8")
        (self.root / "main.c").write_bytes(b"int main(void) { return 0; }")
        hidden = self.root / ".git"
        hidden.mkdir()
        (hidden / "secret").write_text("not inventoried", encoding="utf-8")

    def test_creates_repeatable_spdx_file_inventory_without_license_claims(self):
        first = build_sbom(self.root, created="2026-01-01T00:00:00Z")
        second = build_sbom(self.root, created="2026-01-01T00:00:00Z")
        self.assertEqual(first, second)
        self.assertEqual(first["spdxVersion"], "SPDX-2.3")
        self.assertEqual(len(first["files"]), 2)
        self.assertEqual(first["files"][0]["licenseConcluded"], "NOASSERTION")
        self.assertFalse(first["packages"])

    def test_refuses_invalid_or_symlink_roots_and_file_overwrite(self):
        with self.assertRaises(SBOMError):
            build_sbom(self.root / "missing")
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.json"
            report = build_sbom(self.root)
            write_sbom(report, output)
            with self.assertRaises(SBOMError):
                write_sbom(report, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["spdxVersion"], "SPDX-2.3")

    def test_created_timestamp_requires_timezone(self):
        with self.assertRaises(SBOMError):
            build_sbom(self.root, created="2026-01-01T00:00:00")


if __name__ == "__main__":
    unittest.main()
