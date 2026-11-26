from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.multisyntax_source_audit import SyntaxAuditError, audit_validation_report


class MultiSyntaxSourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "sample.py"
        self.source.write_text("print(42)\n", encoding="utf-8")
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def report(self, syntax="python"):
        return {
            "schema": "reaper.syntax-validation.v1",
            "syntax": syntax,
            "source_sha256": self.digest,
            "valid": True,
            "execution_performed": False,
            "analysis": {},
        }

    def test_accepts_matching_syntax_validation_evidence(self):
        result = audit_validation_report(self.source, self.report(), ["pure", "console_output"])
        self.assertEqual(result["status"], "reviewed")
        self.assertEqual(result["validated_syntaxes"], ["python"])
        self.assertFalse(result["source_execution_performed"])

    def test_rejects_changed_source_and_execution_evidence(self):
        with self.assertRaisesRegex(SyntaxAuditError, "SHA-256"):
            audit_validation_report(self.source, {**self.report(), "source_sha256": "0" * 64})
        report = self.report()
        report["execution_performed"] = True
        with self.assertRaisesRegex(SyntaxAuditError, "non-executing"):
            audit_validation_report(self.source, report)

    def test_rejects_report_for_a_different_source_extension(self):
        with self.assertRaisesRegex(SyntaxAuditError, "extension does not match"):
            audit_validation_report(self.source, self.report("brainfuck"))

    def test_blocks_capabilities_not_provided_by_safe_python_frontend(self):
        result = audit_validation_report(
            self.source, self.report(), ["pure", "network", "filesystem_io"]
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["unsupported_capabilities"], ["filesystem_io", "network"])

    def test_polyglot_capabilities_use_the_intersection_of_frontends(self):
        polyglot_source = self.root / "project.polyglot"
        polyglot_source.write_text("%% python\\nprint(42)\\n%% brainfuck\\n+.", encoding="utf-8")
        polyglot_digest = hashlib.sha256(polyglot_source.read_bytes()).hexdigest()
        report = {
            "schema": "reaper.polyglot-validation.v1",
            "source_sha256": polyglot_digest,
            "valid": True,
            "execution_performed": False,
            "block_count": 2,
            "blocks": [
                {"syntax": "python", "valid": True, "execution_performed": False, "analysis": {}},
                {"syntax": "brainfuck", "valid": True, "execution_performed": False, "analysis": {}},
            ],
        }
        result = audit_validation_report(polyglot_source, report, ["pure", "filesystem_io"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["validated_syntaxes"], ["python", "brainfuck"])

    def test_surfaces_brainfuck_pointer_diagnostics(self):
        brainfuck_source = self.root / "sample.bf"
        brainfuck_source.write_text("[>+]", encoding="utf-8")
        report = {
            **self.report("brainfuck"),
            "source_sha256": hashlib.sha256(brainfuck_source.read_bytes()).hexdigest(),
        }
        report["analysis"] = {
            "pointer_balance_warnings": [
                {"code": "BF-W001", "message": "loop has non-zero pointer displacement"}
            ]
        }
        result = audit_validation_report(brainfuck_source, report)
        self.assertEqual(result["status"], "attention_required")
        self.assertEqual(result["findings"][0]["code"], "BF-W001")

    def test_rejects_unrecognized_syntax_and_malformed_polyglot_block(self):
        with self.assertRaisesRegex(SyntaxAuditError, "unknown syntax"):
            audit_validation_report(self.source, self.report("powershell"))
        polyglot_source = self.root / "malformed.polyglot"
        polyglot_source.write_text("%% python\\nprint(42)", encoding="utf-8")
        report = {
            "schema": "reaper.polyglot-validation.v1",
            "source_sha256": hashlib.sha256(polyglot_source.read_bytes()).hexdigest(),
            "valid": True,
            "execution_performed": False,
            "block_count": 1,
            "blocks": [{"syntax": "python", "valid": True}],
        }
        with self.assertRaisesRegex(SyntaxAuditError, "non-executing"):
            audit_validation_report(polyglot_source, report)


if __name__ == "__main__":
    unittest.main()
