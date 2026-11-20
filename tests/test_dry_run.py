from __future__ import annotations
import hashlib
import json
import unittest
from tools.dry_run import build_dry_run_plan, check_plan_freshness, DryRunError

class DryRunTests(unittest.TestCase):
    def setUp(self):
        self.device = {"instance_id": "PCI\\VEN_1234&DEV_5678", "name": "Network Adapter",
                       "hardware_ids": [r"PCI\VEN_1234&DEV_5678"], "compatible_ids": [r"PCI\VEN_1234"]}
        self.package = {"package_id": "vendor.net", "version": "2.0", "sha256": "a" * 64,
                       "device_ids": [r"PCI\VEN_1234&DEV_5678", r"PCI\VEN_1234"]}
        self.match = {"matched": True, "match_type": "hardware-id",
                      "matched_device_id": r"PCI\VEN_1234&DEV_5678",
                      "matched_inf_id": r"PCI\VEN_1234&DEV_5678"}

    def test_trusted_exact_match_produces_non_applying_plan(self):
        plan = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                  audit_status="passed", signature_status="trusted", inventory_revision=8)
        self.assertEqual(plan["status"], "ready-for-review")
        self.assertFalse(plan["will_modify_system"])
        self.assertFalse(plan["execution_supported"])
        self.assertEqual(len(plan["plan_sha256"]), 64)

    def test_unknown_or_unsigned_signature_is_blocked_by_default(self):
        unknown = build_dry_run_plan(device=self.device, package=self.package, match=self.match, audit_status="passed")
        unsigned = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                      audit_status="passed", signature_status="unsigned")
        self.assertEqual(unknown["status"], "blocked")
        self.assertEqual(unsigned["status"], "blocked")

    def test_compatible_only_match_requires_review(self):
        match = {"matched": True, "match_type": "compatible-id", "matched_device_id": r"PCI\VEN_1234",
                 "matched_inf_id": r"PCI\VEN_1234"}
        plan = build_dry_run_plan(device=self.device, package=self.package, match=match,
                                  audit_status="passed", signature_status="trusted")
        self.assertEqual(plan["status"], "ready-for-review")
        self.assertTrue(any("Compatible ID" in warning for warning in plan["warnings"]))

    def test_failed_audit_invalid_signature_and_mismatched_evidence_block(self):
        failed = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                    audit_status="failed", signature_status="trusted")
        invalid = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                     audit_status="passed", signature_status="invalid")
        self.assertEqual(failed["status"], "blocked")
        self.assertEqual(invalid["status"], "blocked")
        bad_match = {**self.match, "matched_device_id": "PCI\\OTHER"}
        with self.assertRaisesRegex(DryRunError, "does not belong"):
            build_dry_run_plan(device=self.device, package=self.package, match=bad_match,
                               audit_status="passed", signature_status="trusted")
        undeclared = {**self.match, "matched_inf_id": "PCI\\OTHER"}
        with self.assertRaisesRegex(DryRunError, "not declared"):
            build_dry_run_plan(device=self.device, package=self.package, match=undeclared,
                               audit_status="passed", signature_status="trusted")

    def test_plan_freshness_detects_changed_digest_device_revision_and_tampering(self):
        plan = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                  audit_status="passed", signature_status="trusted", inventory_revision=7)
        fresh = check_plan_freshness(plan, current_package_sha256="a" * 64,
                                     current_device_instance_id=self.device["instance_id"], current_inventory_revision=7)
        stale = check_plan_freshness(plan, current_package_sha256="b" * 64,
                                     current_device_instance_id="PCI\\OTHER", current_inventory_revision=8)
        self.assertTrue(fresh["fresh"])
        self.assertFalse(stale["fresh"])
        self.assertEqual(len(stale["reasons"]), 3)
        tampered = dict(plan); tampered["target"] = {**plan["target"], "package_version": "9.9"}
        check = check_plan_freshness(tampered, current_package_sha256="a" * 64,
                                     current_device_instance_id=self.device["instance_id"], current_inventory_revision=7)
        self.assertFalse(check["fresh"])
        self.assertIn("content digest", check["reasons"][0])

    def test_freshness_rejects_blocked_or_executable_plans(self):
        blocked = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                     audit_status="passed", signature_status="unknown", inventory_revision=7)
        result = check_plan_freshness(blocked, current_package_sha256="a" * 64,
                                      current_device_instance_id=self.device["instance_id"], current_inventory_revision=7)
        self.assertFalse(result["fresh"])
        self.assertTrue(any("blocked" in reason for reason in result["reasons"]))
        safe = build_dry_run_plan(device=self.device, package=self.package, match=self.match,
                                  audit_status="passed", signature_status="trusted", inventory_revision=7)
        unsafe = dict(safe)
        unsafe["will_modify_system"] = True
        unsigned = {key: value for key, value in unsafe.items() if key != "plan_sha256"}
        unsafe["plan_sha256"] = hashlib.sha256(json.dumps(
            unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")).hexdigest()
        result = check_plan_freshness(unsafe, current_package_sha256="a" * 64,
                                      current_device_instance_id=self.device["instance_id"], current_inventory_revision=7)
        self.assertFalse(result["fresh"])
        self.assertTrue(any("non-applying" in reason for reason in result["reasons"]))

if __name__ == "__main__":
    unittest.main()
