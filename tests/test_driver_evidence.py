from __future__ import annotations

import json
import unittest

from tools.driver_evidence import (
    LEDGER_SCHEMA, DriverEvidenceError, build_driver_evidence_ledger,
)


def observation(
    *, instance_id: str = r"PCI\VEN_1234&DEV_5678\SERIAL-A",
    attribute: str = "provider", value: str = "Example Vendor",
    source_sha256: str = "a" * 64, captured: str = "2026-11-20T10:00:00Z",
    locator: str = "INF.Provider",
    source_kind: str = "inf_metadata",
    period_start: str | None = None, period_end: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "instance_id": instance_id, "attribute": attribute, "value": value,
        "source_sha256": source_sha256, "captured_at_utc": captured,
        "locator": locator, "source_kind": source_kind,
    }
    if period_start is not None:
        result["period_start_utc"] = period_start
        result["period_end_utc"] = period_end
    return result


class DriverEvidenceLedgerTests(unittest.TestCase):
    def test_subject_identifier_is_pseudonymized_and_repeatable_with_same_key(self) -> None:
        raw = observation()
        first = build_driver_evidence_ledger([raw], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        again = build_driver_evidence_ledger([raw], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        other = build_driver_evidence_ledger([raw], identity_key=b"x" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        serialized = json.dumps(first, ensure_ascii=False)
        self.assertEqual(first, again)
        self.assertNotEqual(first["evidence"][0]["subject_ref"], other["evidence"][0]["subject_ref"])
        self.assertNotIn("SERIAL-A", serialized)
        self.assertNotIn("PCI\\VEN_1234", serialized)
        self.assertEqual(first["schema"], LEDGER_SCHEMA)
        self.assertFalse(first["identity_protection"]["raw_identifiers_exported"])

    def test_identifier_attributes_are_pseudonymized_too(self) -> None:
        raw = observation(attribute="hardware_id", value=r"PCI\VEN_1234&DEV_5678", locator="INF.Models")
        ledger = build_driver_evidence_ledger([raw], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        serialized = json.dumps(ledger)
        self.assertNotIn("VEN_1234", serialized)
        self.assertTrue(ledger["evidence"][0]["value"]["pseudonym"].startswith("hmac-sha256:"))

    def test_conflicting_values_are_retained_without_automatic_resolution(self) -> None:
        rows = [
            observation(value="Vendor A", source_sha256="a" * 64, locator="INF.Provider"),
            observation(value="Vendor B", source_sha256="b" * 64, locator="manifest#/provider", source_kind="udrv_manifest"),
        ]
        ledger = build_driver_evidence_ledger(rows, identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        group = ledger["groups"][0]
        self.assertEqual(group["state"], "conflicted")
        self.assertEqual(set(group["distinct_values"]), {"Vendor A", "Vendor B"})
        self.assertEqual(ledger["summary"]["conflicted_groups"], 1)
        self.assertIn("no source is selected", ledger["conflicts"][0]["resolution"])

    def test_distinct_source_artifacts_with_same_value_are_not_claimed_as_verified(self) -> None:
        rows = [
            observation(source_sha256="a" * 64, locator="INF.Provider"),
            observation(source_sha256="b" * 64, locator="manifest#/provider", source_kind="udrv_manifest"),
        ]
        ledger = build_driver_evidence_ledger(rows, identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        self.assertEqual(ledger["groups"][0]["state"], "multi_source_consistent")
        self.assertTrue(ledger["semantics"]["multi_source_consistent_is_not_independent_verification"])

    def test_different_time_windows_are_not_merged(self) -> None:
        rows = [
            observation(value="1.0", source_sha256="a" * 64, period_start="2026-11-01T00:00:00Z", period_end="2026-11-02T00:00:00Z"),
            observation(value="2.0", source_sha256="b" * 64, period_start="2026-11-02T00:00:00Z", period_end="2026-11-03T00:00:00Z"),
        ]
        ledger = build_driver_evidence_ledger(rows, identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        self.assertEqual(ledger["summary"]["groups"], 2)
        self.assertEqual(ledger["summary"]["conflicted_groups"], 0)

    def test_identity_key_and_input_bounds_are_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            build_driver_evidence_ledger([observation()], identity_key=b"short", generated_at_utc="2026-11-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "observations must contain"):
            build_driver_evidence_ledger([], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")

    def test_bad_timestamp_digest_source_kind_and_locator_fail_closed(self) -> None:
        base = observation()
        with self.assertRaisesRegex(ValueError, "timezone"):
            build_driver_evidence_ledger([{**base, "captured_at_utc": "2026-11-20T10:00:00"}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            build_driver_evidence_ledger([{**base, "source_sha256": "bad"}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "unsupported source_kind"):
            build_driver_evidence_ledger([{**base, "source_kind": "shell"}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "safe relative"):
            build_driver_evidence_ledger([{**base, "locator": "../../users/name"}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")

    def test_non_scalar_and_non_finite_values_are_rejected(self) -> None:
        base = observation()
        with self.assertRaisesRegex(TypeError, "scalar"):
            build_driver_evidence_ledger([{**base, "value": {"unexpected": "object"}}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "finite"):
            build_driver_evidence_ledger([{**base, "value": float("nan")}], identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")

    def test_generated_digest_is_deterministic_and_versioned(self) -> None:
        rows = [observation()]
        first = build_driver_evidence_ledger(rows, identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        second = build_driver_evidence_ledger(rows, identity_key=b"k" * 32, generated_at_utc="2026-11-20T12:00:00Z")
        self.assertEqual(first["ledger_sha256"], second["ledger_sha256"])
        self.assertEqual(len(first["ledger_sha256"]), 64)
        self.assertEqual(first["mode"], "read_only")


if __name__ == "__main__":
    unittest.main()
