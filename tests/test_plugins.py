import hashlib
import tempfile
import unittest
from pathlib import Path

from oplague.plugins import PluginError, PluginManager, PLUGIN_SPECS


class PluginFederationTests(unittest.TestCase):
    def setUp(self):
        self.manager = PluginManager()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_catalog_has_stable_ids_and_names(self):
        self.assertEqual(len(PLUGIN_SPECS), 18)
        self.assertEqual(self.manager.get_plugin("Keel Koh").plugin_id, "keel-koh")
        self.assertEqual(self.manager.get_plugin("PROFEVO").name, "Profevo")

    def test_workflow_is_deterministic_and_dry_run(self):
        result = self.manager.run("dropaul", steps=[
            {"id": "test", "depends_on": ["build"]},
            {"id": "build", "depends_on": []},
        ])
        self.assertEqual(result["execution_order"], ["build", "test"])
        self.assertTrue(result["dry_run"])

    def test_workflow_cycle_is_rejected(self):
        with self.assertRaises(PluginError):
            self.manager.run("dropaul", steps=[
                {"id": "a", "depends_on": ["b"]},
                {"id": "b", "depends_on": ["a"]},
            ])

    def test_file_catalog_fingerprints_content(self):
        path = self.root / "readme.md"
        path.write_text("hello", encoding="utf-8")
        result = self.manager.run("baplap", path=self.root)
        self.assertEqual(result["entries"][0]["sha256"], hashlib.sha256(b"hello").hexdigest())

    def test_security_scan_is_static_and_bounded(self):
        (self.root / "settings.py").write_text('API_KEY = "example_secret_value_12345"\n', encoding="utf-8")
        result = self.manager.run("kali", path=self.root)
        self.assertGreaterEqual(result["finding_count"], 1)
        self.assertIn("not a complete security audit", result["scope"])

    def test_disabled_plugin_cannot_dispatch(self):
        self.manager.set_enabled("Operandu", False)
        with self.assertRaises(PluginError):
            self.manager.run("operandu", value={"x": 1})

    def test_evidence_paths_cannot_escape_workspace(self):
        result = self.manager.run("vprossee", path=self.root, evidence=[
            {"id": "E1", "claim": "bounded", "source": "../../outside.txt", "verified": True}
        ])
        self.assertFalse(result["rows"][0]["valid"])
        self.assertIn("source escapes workspace root", result["rows"][0]["issues"])

    def test_evolution_plan_does_not_mutate(self):
        result = self.manager.run("profevo", current_version="1.2.3", target_version="2.0.0")
        self.assertEqual(result["change_level"], "major")
        self.assertFalse(result["files_modified"])


if __name__ == "__main__":
    unittest.main()
