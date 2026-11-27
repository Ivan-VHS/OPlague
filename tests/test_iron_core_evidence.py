import copy
import json
from pathlib import Path
import unittest

from tools.iron_core_evidence import (
    IronCoreEvidenceError,
    validate_iron_core_ast,
)


FIXTURE = Path(__file__).parent.parent / "examples" / "iron_core" / "inspection.ast.json"


class IronCoreEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_accepts_bounded_structural_evidence(self):
        result = validate_iron_core_ast(self.payload)
        self.assertEqual(result.version, "PYTYLIKI_IRON_CORE_DEMO_V1")
        self.assertEqual(result.block_count, 2)
        self.assertEqual(result.semantic_ids, ("core.context", "selection.filter"))
        self.assertFalse(result.ci_verified)
        self.assertFalse(result.hardware_effects_performed)
        self.assertEqual(result.provenance, "caller-supplied-untrusted-json")

    def test_rejects_source_claim_promoted_to_ci(self):
        payload = copy.deepcopy(self.payload)
        payload["verification_claims_are_ci_evidence"] = True
        with self.assertRaisesRegex(IronCoreEvidenceError, "CI evidence"):
            validate_iron_core_ast(payload)

    def test_rejects_hardware_execution_flags(self):
        payload = copy.deepcopy(self.payload)
        payload["hardware_access_performed"] = True
        with self.assertRaisesRegex(IronCoreEvidenceError, "hardware_access_performed"):
            validate_iron_core_ast(payload)

    def test_rejects_unknown_semantic_id(self):
        payload = copy.deepcopy(self.payload)
        payload["blocks"][0]["semantic_id"] = "privilege.grant"
        with self.assertRaisesRegex(IronCoreEvidenceError, "unknown marker"):
            validate_iron_core_ast(payload)

    def test_rejects_inconsistent_source_range(self):
        payload = copy.deepcopy(self.payload)
        payload["blocks"][1]["body_length"] += 1
        with self.assertRaisesRegex(IronCoreEvidenceError, "body length"):
            validate_iron_core_ast(payload)

    def test_rejects_unclosed_block(self):
        payload = copy.deepcopy(self.payload)
        payload["blocks"][0]["closed"] = False
        with self.assertRaisesRegex(IronCoreEvidenceError, "not closed"):
            validate_iron_core_ast(payload)

    def test_rejects_oversized_source(self):
        payload = copy.deepcopy(self.payload)
        payload["source_bytes"] = 1024 * 1024 + 1
        with self.assertRaisesRegex(IronCoreEvidenceError, "one-megabyte"):
            validate_iron_core_ast(payload)

    def test_rejects_mismatched_catalog_count(self):
        payload = copy.deepcopy(self.payload)
        payload["marker_counts"]["block.end"] = 1
        with self.assertRaisesRegex(IronCoreEvidenceError, "closing marker"):
            validate_iron_core_ast(payload)


if __name__ == "__main__":
    unittest.main()
