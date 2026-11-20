from __future__ import annotations
import unittest
from tools.inf_catalog import parse_inf_document
from tools.driver_compatibility import match_device_to_inf, rank_inf_candidates

SAMPLE = r'''[Version]
Signature="$Windows NT$"
Class=Net
Provider=%Vendor%
DriverVer=01/02/2026,1.2.3.4
CatalogFile=net.cat

[Manufacturer]
%Vendor%=Models,NTamd64.10.0

[Models.NTamd64.10.0]
%Device%=Install, PCI\VEN_1234&DEV_5678, PCI\VEN_1234

[Strings]
Vendor="Example"
Device="Example Network Adapter"
'''

class InfCatalogTests(unittest.TestCase):
    def test_parses_version_and_decorated_models(self):
        parsed = parse_inf_document(SAMPLE)
        self.assertEqual(parsed["version"]["class"], "Net")
        self.assertEqual(parsed["version"]["driverver"], "01/02/2026,1.2.3.4")
        self.assertEqual(parsed["model_sections"], ["models", "models.ntamd64.10.0"])
        self.assertEqual(parsed["device_ids"], [r"PCI\VEN_1234&DEV_5678", r"PCI\VEN_1234"])

    def test_continuations_and_comment_stripping(self):
        parsed = parse_inf_document("""[Manufacturer]
%M%=Models ; comment
[Models]
%X%=Install, PCI\\VEN_A \\
  , PCI\\VEN_B ; trailing
""")
        self.assertEqual(parsed["device_ids"], [r"PCI\VEN_A", r"PCI\VEN_B"])

    def test_hardware_ids_outrank_compatible_ids(self):
        parsed = parse_inf_document(SAMPLE)
        device = {"hardware_ids": [r"PCI\VEN_1234&DEV_5678"], "compatible_ids": [r"PCI\VEN_1234"]}
        result = match_device_to_inf(device, parsed)
        self.assertEqual(result["match_type"], "hardware-id")
        self.assertEqual(result["evidence_score"], 100)

    def test_compatible_id_and_candidate_order(self):
        inf = {"device_ids": [r"PCI\VEN_1234"]}
        device = {"hardware_ids": [r"PCI\VEN_9999"], "compatible_ids": [r"PCI\VEN_1234"]}
        match = match_device_to_inf(device, inf)
        self.assertEqual(match["match_type"], "compatible-id")
        ranked = rank_inf_candidates(device, [{"name": "other", "inf_evidence": {"device_ids": []}}, {"name": "yes", "inf_evidence": inf}])
        self.assertEqual(ranked[0]["package"]["name"], "yes")

    def test_no_match_is_explicit_and_missing_models_warn(self):
        parsed = parse_inf_document("[Version]\nClass=Net\n")
        self.assertFalse(match_device_to_inf({"hardware_ids": ["PCI\\VEN_X"]}, parsed)["matched"])
        self.assertTrue(parsed["warnings"])

    def test_rejects_oversized_input(self):
        with self.assertRaisesRegex(ValueError, "limit"):
            parse_inf_document("x" * (2 * 1024 * 1024 + 1))

if __name__ == "__main__":
    unittest.main()
