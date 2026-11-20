from __future__ import annotations
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from tools.device_registry import create_snapshot
from tools.dry_run import build_dry_run_plan
from tools.oplague_cli import main

class OPlagueCliTests(unittest.TestCase):
    def _write(self, path: Path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_snapshot_diff_command_emits_json(self):
        with tempfile.TemporaryDirectory() as directory:
            left = create_snapshot([{"instance_id": "PCI\\A"}], captured_at="left")
            right = create_snapshot([{"instance_id": "PCI\\A"}, {"instance_id": "USB\\B"}], captured_at="right")
            before, after = Path(directory) / "before.json", Path(directory) / "after.json"
            self._write(before, left); self._write(after, right)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["snapshot", "diff", str(before), str(after)])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["totals"]["devices_added"], 1)

    def test_registry_init_and_snapshot_create_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            source = Path(directory) / "snapshot.json"
            self.assertEqual(main(["registry", "init", str(registry)]), 0)
            self._write(source, {"devices": [{"instance_id": "PCI\\A"}], "packages": [], "metrics": {"health": 0.9}})
            self.assertEqual(main(["snapshot", "create", str(registry), str(source), "--label", "baseline"]), 0)
            payload = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(payload["revision"], 1)
            self.assertEqual(payload["snapshots"][0]["label"], "baseline")

    def test_registry_init_refuses_to_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            registry.write_text("keep me", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["registry", "init", str(registry)])
            self.assertEqual(code, 1)
            self.assertEqual(registry.read_text(encoding="utf-8"), "keep me")

    def test_dry_run_plan_and_freshness_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            device = {"instance_id": "PCI\\A", "hardware_ids": ["PCI\\A"]}
            package = {"package_id": "example", "sha256": "a" * 64, "device_ids": ["PCI\\A"]}
            match = {"matched": True, "match_type": "hardware-id", "matched_device_id": "PCI\\A", "matched_inf_id": "PCI\\A"}
            plan = build_dry_run_plan(device=device, package=package, match=match,
                                      audit_status="passed", signature_status="trusted", inventory_revision=3)
            source = Path(directory) / "plan.json"
            self._write(source, plan)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["dry-run", "freshness", str(source), "--current-digest", "a" * 64,
                             "--current-device", "PCI\\A", "--current-revision", "3"])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(output.getvalue())["fresh"])

    def test_dry_run_plan_returns_blocked_exit_code_for_unknown_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {
                "device": {"instance_id": "PCI\\A", "hardware_ids": ["PCI\\A"]},
                "package": {"package_id": "example", "sha256": "a" * 64, "device_ids": ["PCI\\A"]},
                "match": {"matched": True, "match_type": "hardware-id", "matched_device_id": "PCI\\A", "matched_inf_id": "PCI\\A"},
                "audit_status": "passed",
                "signature_status": "unknown",
            }
            source = Path(directory) / "plan-input.json"; self._write(source, payload)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["dry-run", "plan", str(source)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "blocked")

    def test_compatibility_rank_command(self):
        with tempfile.TemporaryDirectory() as directory:
            device = {"hardware_ids": ["PCI\\A"], "compatible_ids": ["PCI\\B"]}
            packages = [{"package_id": "compatible", "inf_evidence": {"device_ids": ["PCI\\B"]}},
                        {"package_id": "exact", "inf_evidence": {"device_ids": ["PCI\\A"]}}]
            device_path, package_path = Path(directory) / "device.json", Path(directory) / "packages.json"
            self._write(device_path, device); self._write(package_path, packages)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["compatibility", str(device_path), str(package_path)])
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())["results"]
            self.assertEqual(result[0]["package"]["package_id"], "exact")

if __name__ == "__main__":
    unittest.main()
