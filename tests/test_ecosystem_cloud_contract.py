import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = json.loads(
    (ROOT / "federation" / "ecosystem-cloud-adapter.v1.json").read_text(encoding="utf-8")
)


class EcosystemCloudAdapterContractTests(unittest.TestCase):
    def test_contract_identity_and_read_only_boundary(self):
        self.assertEqual(ADAPTER["schema"], "ivan-vhs.ecosystem-cloud-adapter.v1")
        self.assertEqual(ADAPTER["version"], 1)
        self.assertEqual(ADAPTER["project"], "oplague")
        self.assertEqual(ADAPTER["project_key"], "oplague")
        self.assertEqual(ADAPTER["shared_contract"], "ivan-vhs.ecosystem-cloud.v1")
        self.assertEqual(ADAPTER["status"], "contract-only")
        self.assertEqual(ADAPTER["security"]["inspection_mode"], "read-only-local-first")
        self.assertFalse(ADAPTER["security"]["automatic_upload"])
        self.assertFalse(ADAPTER["compatibility"]["driver_install_or_execution"])

    def test_cloud_and_payload_execution_are_disabled_by_default(self):
        runtime = ADAPTER["runtime"]
        self.assertEqual(runtime["default_network_mode"], "disabled")
        self.assertTrue(runtime["user_opt_in_required"])
        self.assertFalse(runtime["core_requires_network"])
        self.assertEqual(runtime["supabase_transport"], "not-implemented")
        self.assertEqual(ADAPTER["security"]["payload_execution"], "never")

    def test_driver_payloads_and_raw_identifiers_are_forbidden(self):
        denied = set(ADAPTER["denylist"])
        for value in (
            "driver-binaries",
            "inf-payloads",
            "raw-device-identifiers",
            "serial-numbers",
            "raw-usb-descriptors",
            "private-signing-material",
            "access-tokens",
            "service-role-keys",
        ):
            with self.subTest(value=value):
                self.assertIn(value, denied)
        self.assertEqual(
            ADAPTER["security"]["hash_semantics"],
            "integrity-reference-only-not-authorship-proof",
        )
        self.assertTrue(ADAPTER["synchronization"]["upload_requires_user_action"])


if __name__ == "__main__":
    unittest.main()
