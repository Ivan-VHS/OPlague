"""Tests for the read-only Authenticode inspection boundary."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from tools.authenticode import (
    AuthenticodeAuditError,
    inspect_authenticode_files,
)


class AuthenticodeInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = self.root / "sample.cat"
        self.driver = self.root / "sample.sys"
        self.catalog.write_bytes(b"catalog")
        self.driver.write_bytes(b"driver")

    def tearDown(self):
        self.temp.cleanup()

    def test_uses_fixed_powershell_command_and_json_input(self):
        observed = {}

        def runner(command, **kwargs):
            observed["command"] = command
            observed["input"] = kwargs["input"]
            return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps({
                "schema": "oplage.authenticode-audit.v1",
                "results": [{
                    "path": str(self.catalog.resolve()),
                    "status": "Valid",
                    "status_message": "Signature verified",
                    "signer_subject": "CN=Example",
                    "signer_issuer": "CN=Example Root",
                    "signer_thumbprint": "ABCD",
                    "timestamp_subject": None,
                }],
            }))

        report = inspect_authenticode_files(
            [self.catalog], runner=runner, platform_name="nt"
        )
        self.assertEqual(report["summary"]["statuses"], {"Valid": 1})
        self.assertFalse(report["installation_attempted"])
        self.assertFalse(report["system_modified"])
        self.assertIn("Get-AuthenticodeSignature", observed["command"][-1])
        self.assertNotIn(str(self.catalog), observed["command"][-1])
        self.assertEqual(json.loads(observed["input"])["paths"], [str(self.catalog.resolve())])

    def test_rejects_non_windows_before_invoking_runner(self):
        called = []
        with self.assertRaises(AuthenticodeAuditError):
            inspect_authenticode_files([self.catalog], runner=lambda *a, **k: called.append(True),
                                       platform_name="posix")
        self.assertEqual(called, [])

    def test_preflights_every_file_before_calling_runner(self):
        unknown = self.root / "payload.bin"
        unknown.write_bytes(b"x")
        called = []
        with self.assertRaisesRegex(ValueError, "unsupported"):
            inspect_authenticode_files([self.catalog, unknown],
                                       runner=lambda *a, **k: called.append(True),
                                       platform_name="nt")
        self.assertEqual(called, [])

    def test_rejects_duplicate_and_empty_selection(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect_authenticode_files([self.catalog, self.catalog], platform_name="nt")
        with self.assertRaises(ValueError):
            inspect_authenticode_files([], platform_name="nt")

    def test_rejects_failed_powershell_execution(self):
        runner = lambda *a, **k: SimpleNamespace(returncode=1, stderr="access denied", stdout="")
        with self.assertRaisesRegex(AuthenticodeAuditError, "access denied"):
            inspect_authenticode_files([self.driver], runner=runner, platform_name="nt")

    def test_rejects_incomplete_provider_result(self):
        runner = lambda *a, **k: SimpleNamespace(
            returncode=0, stderr="", stdout='{"schema":"oplage.authenticode-audit.v1","results":[]}'
        )
        with self.assertRaisesRegex(AuthenticodeAuditError, "incomplete"):
            inspect_authenticode_files([self.driver], runner=runner, platform_name="nt")


if __name__ == "__main__":
    unittest.main()
