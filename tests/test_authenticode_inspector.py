"""Tests for the read-only Authenticode inspection helper."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import authenticode_inspector as inspector


class AuthenticodeInspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "sample.sys"
        self.file.write_bytes(b"local test fixture")

    def test_rejects_non_driver_file_types(self):
        other = Path(self.temp.name) / "notes.txt"
        other.write_text("not a driver", encoding="utf-8")
        with self.assertRaises(inspector.AuthenticodeError):
            inspector.inspect_signatures([other])

    @patch.object(inspector.platform, "system", return_value="Linux")
    @patch.object(inspector.os, "name", "posix")
    def test_non_windows_platform_is_explicitly_unsupported(self, *_):
        with self.assertRaises(NotImplementedError):
            inspector.inspect_signatures([self.file])

    @patch.object(inspector.platform, "system", return_value="Windows")
    @patch.object(inspector.os, "name", "nt")
    @patch.object(inspector.subprocess, "run")
    def test_paths_are_sent_as_json_stdin_not_script_text(self, run, *_):
        expected = {
            "path": str(self.file.resolve()),
            "status": "Valid",
            "status_message": "Signature verified.",
            "signer_subject": "CN=Example Publisher",
            "signer_issuer": "CN=Example Root",
            "signer_thumbprint": "0123456789ABCDEF",
            "signer_not_before": None,
            "signer_not_after": None,
            "timestamp_subject": "CN=Timestamp",
        }
        run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps([expected]), stderr=""
        )
        report = inspector.inspect_signatures([self.file])
        args, kwargs = run.call_args
        self.assertEqual(json.loads(kwargs["input"]), [str(self.file.resolve())])
        self.assertNotIn(str(self.file.resolve()), args[0][-1])
        self.assertEqual(report["schema"], inspector.SCHEMA)
        self.assertEqual(report["results"][0]["status"], "Valid")
        self.assertTrue(report["read_only"])

    @patch.object(inspector.platform, "system", return_value="Windows")
    @patch.object(inspector.os, "name", "nt")
    @patch.object(inspector.subprocess, "run")
    def test_timeout_is_reported_without_retry(self, run, *_):
        run.side_effect = subprocess.TimeoutExpired("powershell.exe", 45)
        with self.assertRaises(inspector.AuthenticodeError):
            inspector.inspect_signatures([self.file])
        run.assert_called_once()

    def test_file_count_limit_is_enforced(self):
        with self.assertRaises(inspector.AuthenticodeError):
            inspector.inspect_signatures([self.file] * (inspector.MAX_FILES + 1))


if __name__ == "__main__":
    unittest.main()
