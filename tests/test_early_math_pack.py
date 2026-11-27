from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_early_math_pack import (
    MAX_PACK_BYTES,
    load_pack,
    validate_early_math_pack,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "early_math_pack.v1.json"


class EarlyMathPackValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_pack(EXAMPLE)

    def test_repository_example_obeys_the_static_content_contract(self) -> None:
        self.assertEqual(validate_early_math_pack(self.pack), [])

    def test_unknown_personal_data_fields_are_rejected(self) -> None:
        payload = copy.deepcopy(self.pack)
        payload["child_id"] = "sample-child"
        errors = validate_early_math_pack(payload)
        self.assertTrue(any("unsupported fields" in item for item in errors))

    def test_timers_scoring_and_remote_collection_are_prohibited(self) -> None:
        for key, value in (
            ("timed", True),
            ("scored", True),
            ("personal_data_collection", True),
            ("network_required", True),
        ):
            with self.subTest(key=key):
                payload = copy.deepcopy(self.pack)
                payload["session_policy"][key] = value
                self.assertTrue(validate_early_math_pack(payload))

    def test_external_links_and_executable_markup_are_rejected(self) -> None:
        payload = copy.deepcopy(self.pack)
        payload["stages"][0]["activities"][0]["adult_prompt"] = "Open https://example.org"
        self.assertTrue(validate_early_math_pack(payload))

        payload["stages"][0]["activities"][0]["adult_prompt"] = "<script>alert(1)</script>"
        self.assertTrue(validate_early_math_pack(payload))

    def test_age_bands_must_fit_the_pack_and_remain_ordered(self) -> None:
        payload = copy.deepcopy(self.pack)
        payload["stages"][1]["age_months"] = {"min": 24, "max": 36}
        errors = validate_early_math_pack(payload)
        self.assertTrue(any("must not overlap" in item for item in errors))

    def test_stage_ids_and_activity_ids_must_be_unique(self) -> None:
        payload = copy.deepcopy(self.pack)
        payload["stages"][1]["id"] = payload["stages"][0]["id"]
        self.assertTrue(validate_early_math_pack(payload))

        payload = copy.deepcopy(self.pack)
        payload["stages"][1]["activities"][0]["id"] = payload["stages"][0]["activities"][0]["id"]
        self.assertTrue(validate_early_math_pack(payload))

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema":"first","schema":"second"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                load_pack(path)

    def test_oversized_files_are_rejected_before_json_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "too-large.json"
            path.write_bytes(b" " * (MAX_PACK_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "exceeds"):
                load_pack(path)

    def test_symbolic_link_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "pack.json"
            target.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
            link = root / "pack-link.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable on this platform")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                load_pack(link)


if __name__ == "__main__":
    unittest.main()
