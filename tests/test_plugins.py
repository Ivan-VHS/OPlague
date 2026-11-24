import hashlib
import tempfile
import unittest
from pathlib import Path

from oplague.plugins import (
    PluginError, PluginExecutionPolicy, PluginManager, PLUGIN_SPECS,
)


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
        key_name = "API" + "_KEY"
        sample_value = "example" + "_secret_value_12345"
        (self.root / "settings.py").write_text(f'{key_name} = "{sample_value}"\n', encoding="utf-8")
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

    def test_plugin_execution_policy_bounds_inputs_and_outputs(self):
        with self.assertRaises(PluginError):
            PluginExecutionPolicy(max_input_bytes=True)
        limited_input = PluginManager(policy=PluginExecutionPolicy(max_input_bytes=8))
        with self.assertRaisesRegex(PluginError, "input exceeds"):
            limited_input.run("operandu", value={"many": "characters"})

        limited_output = PluginManager(policy=PluginExecutionPolicy(max_output_bytes=8))
        with self.assertRaisesRegex(PluginError, "output exceeds"):
            limited_output.run("operandu", value=1)

    def test_plugin_health_reports_readiness_and_invocation_metrics(self):
        manager = PluginManager()
        self.assertTrue(manager.health()["ready"])
        result = manager.run("operandu", value={"score": 0.5})
        self.assertEqual(result["type"], "mapping")
        health = manager.health()
        self.assertEqual(health["schema"], "oplage.plugin-health.v1")
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["plugins"]["operandu"]["invocations"], 1)
        self.assertEqual(health["plugins"]["operandu"]["successes"], 1)
        self.assertEqual(health["plugins"]["operandu"]["in_flight"], 0)
        self.assertGreaterEqual(
            health["plugins"]["operandu"]["last_duration_ms"], 0.0
        )

    def test_plugin_dispatch_rejects_concurrency_saturation(self):
        policy = PluginExecutionPolicy(max_concurrent_per_plugin=1)
        manager = PluginManager(policy=policy)
        semaphore = manager._semaphores["operandu"]
        self.assertTrue(semaphore.acquire(blocking=False))
        try:
            with self.assertRaisesRegex(PluginError, "concurrency limit"):
                manager.run("operandu", value=1)
        finally:
            semaphore.release()


if __name__ == "__main__":
    unittest.main()
