"""OPlague tests for Code Mental Health / Codebase Wellbeing."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.code_wellbeing import CodeWellbeingError, load_charter, scan_project


class CodebaseWellbeingTests(unittest.TestCase):
    def test_charter_is_an_engineering_metaphor_not_a_clinical_model(self):
        concept = load_charter()["concept"]
        self.assertTrue(concept["is_engineering_metaphor"])
        self.assertFalse(concept["clinical_equivalence"])

    def test_detects_source_tests_docs_and_ci(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "README.md").write_text("# Demo", encoding="utf-8")
            (root / "src" / "main.py").write_text("# TODO: review\nprint('ok')\n", encoding="utf-8")
            (root / "tests" / "test_main.py").write_text("def test_ok(): pass\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
            report = scan_project(root)
        self.assertEqual(report["inventory"]["source_files"], 2)
        self.assertEqual(report["inventory"]["test_files"], 1)
        self.assertEqual(report["inventory"]["readme_files"], 1)
        self.assertEqual(report["inventory"]["ci_workflow_files"], 1)
        self.assertEqual(report["inventory"]["maintenance_markers"]["TODO"], 1)

    def test_build_vendor_and_git_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (".git", "build", "vendor", "node_modules"):
                (root / name).mkdir()
                (root / name / "generated.py").write_text("pass\n", encoding="utf-8")
            self.assertEqual(scan_project(root)["inventory"]["total_files"], 0)

    def test_markers_are_review_prompts_not_failure_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("# FIXME: context needed\n", encoding="utf-8")
            report = scan_project(root)
        signal = next(x for x in report["signals"] if x["id"] == "maintainability-review-cues")
        self.assertIn("not automatic defects", signal["note"])

    def test_invalid_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CodeWellbeingError):
                scan_project(Path(directory) / "absent")

    def test_no_aggregate_score_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            report = scan_project(directory)
        self.assertNotIn("score", report)
        self.assertTrue(report["scan"]["read_only"])
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
