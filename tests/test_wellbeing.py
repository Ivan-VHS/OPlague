"""Tests for OPlague's read-only wellbeing reference."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.wellbeing import (
    RESOURCE_PATH,
    WellbeingReferenceError,
    get_topic,
    load_reference,
)


class OPlagueWellbeingTests(unittest.TestCase):
    def test_bundle_preserves_video_provenance(self):
        payload = load_reference()
        self.assertEqual(payload["source"]["video_url"], "https://www.youtube.com/watch?v=brNbnipJ-i8")
        self.assertEqual(payload["source"]["published_at"], "2025-11-23")

    def test_partial_transcript_is_explicit(self):
        coverage = load_reference()["transcript_coverage"]
        self.assertTrue(coverage["missing_middle"])
        self.assertEqual(coverage["available_segments"][0]["end_seconds"], 475)
        self.assertEqual(coverage["available_segments"][1]["start_seconds"], 4636)

    def test_title_only_antidepressant_claim_is_unverified(self):
        topic = get_topic("antidepressant-myths")
        self.assertEqual(topic["evidence_status"], "insufficient_transcript")
        self.assertEqual(topic["timestamps_seconds"], [])

    def test_all_documented_topics_have_unique_ids(self):
        topics = load_reference()["topics"]
        ids = [topic["id"] for topic in topics]
        self.assertEqual(len(ids), len(set(ids)))

    def test_safety_guardrails_reject_diagnostic_repurposing(self):
        payload = load_reference()
        payload["guardrails"] = ["Informational content only."]
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "reference.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(WellbeingReferenceError):
                load_reference(candidate)

    def test_duplicate_topics_are_rejected(self):
        payload = load_reference()
        payload["topics"].append(copy.deepcopy(payload["topics"][0]))
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "reference.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(WellbeingReferenceError):
                load_reference(candidate)

    def test_resource_is_local_and_bounded(self):
        self.assertTrue(RESOURCE_PATH.is_file())
        self.assertLess(RESOURCE_PATH.stat().st_size, 256 * 1024)


if __name__ == "__main__":
    unittest.main()
